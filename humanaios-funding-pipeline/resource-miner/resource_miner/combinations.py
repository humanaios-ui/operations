"""Bounded, observational Resource Miner capability-complementarity experiment.

Counts distinct *reported* affordances. It does not establish interoperability,
verified value, eligibility, permission, or authority to act.
"""
from __future__ import annotations

import argparse
import itertools
import json
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit
from typing import Any

from .miner import _ranking_score
from .models import NeedMatch, RequirementMatch, ResourceCandidate

MAX_CANDIDATES = 8  # exhaustive, deterministic; never an open-ended solver
MAX_BUNDLE_SIZE = 3


def load_snapshot(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def _check_config(config: dict[str, Any]) -> tuple[date, list[str], dict[str, int], int]:
    as_of = date.fromisoformat(config["as_of"])
    targets = config["target_affordances"]
    ids = config["candidate_ids"]
    costs = config["assumed_review_minutes"]
    budget = config["review_budget_minutes"]
    if not isinstance(ids, list) or not 1 <= len(ids) <= MAX_CANDIDATES:
        raise ValueError("Supply 1..8 explicit candidate IDs")
    if any(not isinstance(x, str) or not x for x in ids) or len(set(ids)) != len(ids):
        raise ValueError("Candidate IDs must be unique, non-empty strings")
    if not isinstance(targets, list) or not targets or len(set(targets)) != len(targets) or any(not isinstance(t, str) or not t for t in targets):
        raise ValueError("Target affordances must be unique non-empty strings")
    if type(budget) is not int or budget < 0:
        raise ValueError("Review budget must be a non-negative integer")
    if not isinstance(costs, dict) or set(costs) != set(ids):
        raise ValueError("Every selected resource needs an explicit review cost")
    if any(type(costs[x]) is not int or costs[x] < 0 for x in ids):
        raise ValueError("Review costs must be non-negative integers")
    return as_of, targets, costs, budget


def _exclusion(row: dict[str, Any], as_of: date) -> str | None:
    if row.get("authority_effect", "NONE") != "NONE":
        return "CLAIMED_AUTHORITY"
    if row.get("user_disposition") in {"PASS", "REJECT", "DECLINED"}:
        return "USER_EXCLUDED"
    if row.get("route") == "ARCHIVE" or row.get("status") == "CLOSED_OR_STALE":
        return "ARCHIVED"
    if row.get("deadline") and date.fromisoformat(row["deadline"]) < as_of:
        return "DEADLINE_PASSED"
    if row.get("resource_state") not in {"CANDIDATE", "ALREADY_ACQUIRED"}:
        return "UNSUPPORTED_RESOURCE_STATE"
    url = row.get("source_url") or row.get("canonical_url") or ""
    if urlsplit(url).scheme != "https" or not urlsplit(url).hostname:
        return "MISSING_PUBLIC_SOURCE"
    evidence = row.get("evidence")
    if not isinstance(evidence, list) or not evidence or not any(
        isinstance(ref, dict) and isinstance(ref.get("url"), str)
        and urlsplit(ref["url"]).hostname == urlsplit(url).hostname
        for ref in evidence
    ):
        return "NO_BOUND_SOURCE_EVIDENCE"
    return None

def _legacy_sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    """Use the existing individual Resource Miner ranking against saved matches."""
    resource = ResourceCandidate(
        resource_id=row["resource_id"], title=row.get("title", ""),
        source_name=row.get("source_name", ""), source_url=row.get("source_url", ""),
        canonical_url=row.get("canonical_url", ""),
        discovery_method=row.get("discovery_method", ""), discovered_at=row.get("discovered_at", ""),
        need_matches=[NeedMatch(**m) for m in row.get("need_matches", [])],
        requirement_matches=[RequirementMatch(**m) for m in row.get("requirement_matches", [])],
    )
    route = row.get("route", "WATCH")
    return (0 if route == "VERIFY_NOW" else 1 if route == "WATCH" else 2,
            -_ranking_score(resource), row.get("deadline") or "9999-12-31", resource.title.lower())


def evaluate_combinations(snapshot: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    """Evaluate declared review cost vs prospective resource-affordance coverage."""
    as_of, targets, costs, budget = _check_config(config)
    ids = config["candidate_ids"]
    observed: dict[str, dict[str, Any]] = {}
    for row in snapshot:
        rid = row.get("resource_id")
        if rid in ids:
            if rid in observed:
                raise ValueError(f"Duplicate candidate identity: {rid}")
            observed[rid] = row
    missing = set(ids) - set(observed)
    if missing:
        raise ValueError(f"Missing snapshot candidates: {sorted(missing)}")

    rejected: dict[str, str] = {}
    eligible: list[dict[str, Any]] = []
    for rid in ids:
        row = observed[rid]
        reason = _exclusion(row, as_of)
        if reason:
            rejected[rid] = reason
        else:
            eligible.append(row)

    def candidate(bundle: tuple[dict[str, Any], ...]) -> dict[str, Any]:
        chosen_ids = sorted(row["resource_id"] for row in bundle)
        covered = sorted({aff for row in bundle for aff in row.get("resource_affordances", []) if aff in targets})
        hosts = sorted({urlsplit(row.get("source_url") or row.get("canonical_url") or "").hostname for row in bundle})
        pending = sorted(row["resource_id"] for row in bundle if not row.get("eligibility_assessed", False))
        return {
            "resource_ids": chosen_ids,
            "source_hosts": hosts,
            "review_minutes": sum(costs[rid] for rid in chosen_ids),
            "covered_affordances": covered,
            "coverage_count": len(covered),
            "needs_eligibility_verification": pending,
            "compatibility": "NOT_EVALUATED" if len(bundle) > 1 else "NOT_APPLICABLE",
        }

    feasible: list[dict[str, Any]] = []
    for size in range(1, min(len(eligible), MAX_BUNDLE_SIZE) + 1):
        for bundle in itertools.combinations(eligible, size):
            item = candidate(bundle)
            if item["review_minutes"] <= budget:
                feasible.append(item)
    # Maximize reported coverage, then unverified eligibility count, then effort;
    # stable tie-break ensures deterministic receipts for CI and audit.
    feasible.sort(key=lambda x: (-x["coverage_count"], len(x["needs_eligibility_verification"]), x["review_minutes"], x["resource_ids"]))
    singles = [row for row in feasible if len(row["resource_ids"]) == 1]
    bundles = [row for row in feasible if len(row["resource_ids"]) > 1]
    baseline = singles[0] if singles else None
    legacy_pool = [row for row in eligible if costs[row["resource_id"]] <= budget]
    legacy_first = candidate((sorted(legacy_pool, key=_legacy_sort_key)[0],)) if legacy_pool else None
    best = bundles[0] if bundles else None
    delta = (best["coverage_count"] - baseline["coverage_count"]) if best and baseline else None
    return {
        "schema": "humanaios.resource-complementarity-observation.v0.1",
        "as_of": as_of.isoformat(),
        "source_snapshot_ref": config.get("source_snapshot_ref", "UNPINNED"),
        "metric": "count_of_distinct_reported_target_affordances_NOT_value_or_outcome",
        "target_affordances": targets,
        "review_budget_minutes": budget,
        "review_cost_basis": "EXPLICIT_SCENARIO_ASSUMPTIONS_NOT_OBSERVED_COSTS",
        "observed_count": len(observed),
        "admissible_for_comparison_count": len(eligible),
        "rejected": rejected,
        "baseline_single": baseline,
        "existing_miner_first_feasible": legacy_first,
        "best_multi_resource": best,
        "incremental_reported_coverage": delta,
        "delta_vs_existing_miner_first": (best["coverage_count"] - legacy_first["coverage_count"])
        if best and legacy_first else None,
        "positive_complementarity_hypothesis": delta is not None and delta > 0,
        "verified_synergy": "NOT_ESTABLISHED",
        "verified_interoperability": "NOT_ESTABLISHED",
        "eligibility_status": "NOT_EVALUATED_FOR_BUNDLE",
        "authorization_state": "NOT_REQUESTED",
        "actionability_state": "NOT_ACTIONABLE",
        "authority_effect": "NONE",
        "execution_capability": "NONE",
        "action_requests": [],
    }


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Resource Miner observational combination pilot")
    parser.add_argument("--snapshot", default=str(root / "data/resources.snapshot.jsonl"))
    parser.add_argument("--config", default=str(root / "data/experiments/resource_complementarity_pilot.v1.json"))
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    print(json.dumps(evaluate_combinations(load_snapshot(args.snapshot), config), indent=2))


if __name__ == "__main__":
    main()
