"""Bounded offline Oracle–SMAG–Resource Miner evaluation, with no authority.

The input forecasts are author-controlled PR body assertions, not independently
precommitted predictions. GitHub PR metadata is a separate observational source,
but is not an authenticated witness to forecast origin, full PR quality,
admission, or later reversions. Outputs are DESCRIPTIVE_ONLY.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .document_source_reflex import project_report

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
_SHA = re.compile(r"^[a-f0-9]{40}$")
PROBABILITY_BASELINE = 0.5
MAX_CASES = 30


def _instant(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("invalid observation timestamp")
    try:
        instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid observation timestamp") from exc
    if instant.tzinfo is None:
        raise ValueError("observation timestamps must carry a timezone")
    return instant.astimezone(timezone.utc)


def oracle_module():
    # Fixed path in the versioned checkout, not a caller-supplied import target.
    path = ROOT / "oracles" / "engine" / "forecast_replay_v0_1.py"
    spec = importlib.util.spec_from_file_location("bounded_oracle_replay", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Oracle replay implementation not available")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _indexed(snapshot: dict[str, Any], expected_schema: str) -> dict[int, dict]:
    if not isinstance(snapshot, dict) or snapshot.get("schema") != expected_schema:
        raise ValueError("unexpected snapshot schema")
    rows = snapshot.get("rows")
    if not isinstance(rows, list) or not 1 <= len(rows) <= MAX_CASES:
        raise ValueError("snapshot size outside bound")
    indexed: dict[int, dict] = {}
    for item in rows:
        if not isinstance(item, dict) or type(item.get("pr")) is not int:
            raise ValueError("malformed PR observation")
        pr = item["pr"]
        if pr < 1 or pr in indexed:
            raise ValueError("duplicate or invalid PR")
        indexed[pr] = item
    return indexed


def project_experiment(predictions: dict[str, Any], outcomes: dict[str, Any]) -> dict[str, Any]:
    """Evaluate two separately captured input streams without extra API calls."""
    forecast_rows = _indexed(predictions, "humanaios.oracle_smag_forecasts.offline_v0_1")
    outcome_rows = _indexed(outcomes, "humanaios.oracle_smag_outcomes.offline_v0_1")
    if set(forecast_rows) != set(outcome_rows):
        raise ValueError("prediction and outcome sampling frames disagree")
    snapshot_at = predictions.get("snapshot_at")
    snapshot_instant = _instant(snapshot_at)
    if snapshot_instant != _instant(outcomes.get("snapshot_at")):
        raise ValueError("observation times must match")
    oracle = oracle_module()
    # Semantic target: GitHub merge status by a fixed evaluation snapshot.
    # It does not mean admitted, successful CI, quality, or verified user outcome.
    episodes = []
    miner_prs = []
    for number in sorted(forecast_rows):
        prediction = forecast_rows[number]
        observed = outcome_rows[number]
        probability = prediction.get("smag_p_meta")
        if (type(probability) not in (float, int) or
                not 0 <= probability <= 1):
            raise ValueError("invalid SMAG prediction")
        declared_at = prediction.get("declared_at")
        head = observed.get("head_sha")
        if not isinstance(head, str) or not _SHA.fullmatch(head):
            raise ValueError("invalid observed head OID")
        status = observed.get("status")
        merged_at = observed.get("merged_at")
        if status not in {"MERGED", "OPEN"}:
            raise ValueError("unsupported observation state; closed-unmerged is not scored")
        if (status == "MERGED") != isinstance(merged_at, str):
            raise ValueError("resolved state and merged_at mismatch")
        if status == "MERGED" and _instant(merged_at) > snapshot_instant:
            raise ValueError("future merge cannot be observed at snapshot time")
        locator = f"https://github.com/humanaios-ui/operations/pull/{number}"
        manifest = oracle.build_manifest(
            forecast_id=f"SMAG-RETROSPECTIVE-PR-{number}",
            question_key="smag_github_merged_at_snapshot_v0_1",
            question="Did this consolidation PR merge by the frozen observation time?",
            subject_ref=locator,
            created_at=declared_at,
            closes_at=snapshot_at,
            evidence_cutoff={"kind": "TIMESTAMP", "sequence": 0, "ref": declared_at},
            resolution_rule="YES iff separately captured GitHub metadata records a merge by snapshot_at; OPEN remains unresolved.",
            resolution_sources=["GITHUB_PR_METADATA_NOT_INDEPENDENTLY_ATTESTED"],
            owner="resource-miner-offline-evaluation",
            provenance_kind="PROSPECTIVE_SOURCE_REPLAY",
            provenance_refs=[locator],
            annul_rules=["PR metadata missing or outcome definition ambiguous"],
        )
        episode = oracle.start_episode(
            manifest,
            predictor_id="SMAG_PR_BODY_ASSERTED",
            probability=float(probability),
            recorded_at=declared_at,  # Replay time, not independently proven PR-open pin.
            evidence_refs=[locator],
        )
        if status == "MERGED":
            episode = oracle.resolve_episode(
                episode, outcome=1, resolver_id="GITHUB_METADATA_OBSERVER",
                source_refs=[locator], resolved_at=merged_at,
                witness_role="UNATTESTED_GITHUB_METADATA_CAPTURE",
                verification_status="RECORDED_NOT_REVERIFIED",
            )
        episodes.append(episode)
        miner_prs.append({
            "repo": "humanaios-ui/operations", "number": number, "head_oid": head,
            "merged": status == "MERGED", "ci_status": "UNKNOWN",
            "coderabbit_status": "UNKNOWN", "human_approval": "UNKNOWN",
            "admission_status": "UNKNOWN", "receipt_head": None,
        })
    cohort = oracle.score_cohort(
        episodes, eligible_forecast_ids=[e["manifest"]["forecast_id"] for e in episodes],
        sampling_frame_ref="UNATTESTED_RETROSPECTIVE_FIXTURE",
        sampling_frame_sealed_before_outcomes=False,
        minimum_claim_n=20,
    )
    scored = cohort["receipts"]
    miner = project_report({
        "source_identity": "smag-retrospective-pr-body-20261021",
        "receipt_identity": "github-metadata-unattested-20261021",
        "observed_at": snapshot_at, "sources": [], "bindings": [],
        "pull_requests": miner_prs,
    })
    if cohort["claim_status"] != "DESCRIPTIVE_ONLY" or miner["overall"] != "UNVERIFIED":
        raise AssertionError("pilot must never promote observed author claims to verified outcomes")
    baseline_brier = (
        sum(oracle.brier_score(PROBABILITY_BASELINE, int(r["outcome"])) for r in scored) / len(scored)
        if scored else None
    )
    result = {
        "schema": "humanaios.oracle_smag_miner_experiment.offline_v0_1",
        "sampling_frame": sorted(forecast_rows),
        "frame_count": len(episodes),
        "resolved_count": len(scored),
        "pending_count": len(episodes) - len(scored),
        "oracle_claim_status": cohort["claim_status"],
        "brier_smag_resolved": cohort.get("mean_brier"),
        "brier_constant_0_5_resolved": baseline_brier,
        "miner_candidate_codes": [c["finding_code"] for c in miner["candidates"]],
        "miner_candidate_count": len(miner["candidates"]),
        "oracle_cohort_blockers": cohort["claim_blockers"],
        "f3_challenge_performed": False,
        "retrospective_precommitment_authenticated": False,
        "outcomes_independently_attested": False,
        "calibration_warrant": "UNVERIFIED",
        "limitations": [
            "This is retrospective replay, not an independently precommitted prospective forecast.",
            "SMAG PR-body probability is a declaration; author edits or temporal history are unverified.",
            "Merge metadata does not establish zero rework, admitted governance, or human success.",
            "OPEN episodes remain censored, not failures.",
            "Only two resolved observations: no statistical calibration claim.",
            "No F2 or F3 is generated retrospectively because a synthetic correction would cause leakage.",
            "Resource Miner findings are verification opportunities, not approval or independently sourced receipts.",
        ],
        "authority_effect": "NONE",
        "merge_authority": False,
    }
    result["digest_sha256"] = hashlib.sha256(
        json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return result


def offline_fixture_report() -> dict[str, Any]:
    forecasts = json.loads((FIXTURES / "oracle_smag_predictions_20261021.json").read_text(encoding="utf-8"))
    outcomes = json.loads((FIXTURES / "oracle_smag_outcomes_20261021.json").read_text(encoding="utf-8"))
    return project_experiment(forecasts, outcomes)


if __name__ == "__main__":
    print(json.dumps(offline_fixture_report(), indent=2, sort_keys=True))
