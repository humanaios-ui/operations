"""Milestone 2: execute a genuine *local* Resource Miner work product.

This is an evidence-only negative control. Local work is executed against the
checked-in snapshot. It does NOT invoke Azure, Cerebras, or Langfuse. A true
three-provider trial needs separately authorized runtime and measured witness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

from .combinations import evaluate_combinations, load_snapshot


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def verify_source_queue(snapshot: list[dict[str, Any]], selected_ids: list[str]) -> dict[str, Any]:
    """Perform actual deterministic, provenance-preserving screening work.

    Produces bounded follow-up verification questions. No claim is treated as
    independently verified. Never invokes a provider and never grants authority.
    """
    if not selected_ids or len(selected_ids) != len(set(selected_ids)):
        raise ValueError("Selected resource IDs must be nonempty and unique")
    by_id = {row["resource_id"]: row for row in snapshot if row.get("resource_id") in selected_ids}
    if set(by_id) != set(selected_ids):
        raise ValueError("Source record missing")
    items = []
    for rid in sorted(selected_ids):
        row = by_id[rid]
        evidence = row.get("evidence") or []
        urls = sorted({ref["url"] for ref in evidence if isinstance(ref, dict) and isinstance(ref.get("url"), str)})
        if not urls:
            raise ValueError("Missing evidence references")
        items.append({
            "resource_id": rid,
            "source_url": row.get("source_url"),
            "affordances_claimed": sorted(set(row.get("resource_affordances") or [])),
            "evidence_urls": urls,
            "source_currentness": "NOT_INDEPENDENTLY_VERIFIED",
            "actual_access": "NOT_INDEPENDENTLY_VERIFIED",
            "eligibility": "UNASSESSED",
            "next_operation": "VERIFY_PRIMARY_SOURCE_AND_PROVIDER_TERMS",
        })
    return {
        "task": "CREATE_RESOURCE_VERIFICATION_QUEUE",
        "output_kind": "EVIDENCE_REVIEW_QUEUE",
        "items": items,
        "verification_questions_generated": len(items),
        "verified_provider_integrations": 0,
        "verified_task_outcomes": 0,
        "external_calls": 0,
        "authorization_state": "NOT_REQUESTED",
        "authority_effect": "NONE",
        "actionability_state": "NOT_ACTIONABLE",
    }


def runtime_prerequisites(environ: dict[str, str]) -> dict[str, Any]:
    """Preflight only. Presence is not proof of account access or authorization.

    Azure witness requires independently attested execution on owned Azure
    compute. A CI/GitHub host is *not* Azure by virtue of env vars alone.
    """
    required = ("CEREBRAS_API_KEY", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY",
                "LANGFUSE_BASE_URL", "AZURE_EXECUTION_RECEIPT")
    missing = [key for key in required if not environ.get(key, "").strip()]
    return {
        "provider_live_trial": "BLOCKED_MISSING_RUNTIME" if missing else "PREFLIGHT_ONLY_NOT_AUTHORIZED",
        "missing_configuration": missing,
        "azure_compute_witness": "NOT_VERIFIED",
        "provider_interoperability": "NOT_VERIFIED",
        "authorization_state": "NOT_REQUESTED",
        "execution_capability": "NONE",
    }


def run_shadow_trial(snapshot: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    comparison = evaluate_combinations(snapshot, config)
    baseline = comparison["existing_miner_first_feasible"]
    bundle = comparison["best_multi_resource"]
    if baseline is None or bundle is None:
        raise ValueError("No feasible same-budget single vs bundle trial")

    def timed(ids: list[str]) -> tuple[dict[str, Any], int]:
        began = time.perf_counter_ns()
        result = verify_source_queue(snapshot, ids)
        return result, time.perf_counter_ns() - began

    base_artifact, base_ns = timed(baseline["resource_ids"])
    bundle_artifact, bundle_ns = timed(bundle["resource_ids"])
    return {
        "schema": "humanaios.resource-complementarity-outcome-shadow.v0.1",
        "task": "CREATE_RESOURCE_VERIFICATION_QUEUE",
        "source_snapshot_ref": comparison["source_snapshot_ref"],
        "as_of": comparison["as_of"],
        "mode": "LOCAL_REAL_EXECUTION_NO_EXTERNAL_PROVIDERS",
        "comparison": {
            "baseline": {
                "resource_ids": baseline["resource_ids"],
                "assumed_review_minutes": baseline["review_minutes"],
                "actual_local_processing_ns": base_ns,
                "generated_verification_questions": base_artifact["verification_questions_generated"],
                "verified_task_outcomes": base_artifact["verified_task_outcomes"],
                "artifact_sha256": _digest(base_artifact),
            },
            "bundle": {
                "resource_ids": bundle["resource_ids"],
                "assumed_review_minutes": bundle["review_minutes"],
                "actual_local_processing_ns": bundle_ns,
                "generated_verification_questions": bundle_artifact["verification_questions_generated"],
                "verified_task_outcomes": bundle_artifact["verified_task_outcomes"],
                "artifact_sha256": _digest(bundle_artifact),
            },
            "verified_outcome_delta": (bundle_artifact["verified_task_outcomes"]
                                       - base_artifact["verified_task_outcomes"]),
            "reported_affordance_delta": comparison["incremental_reported_coverage"],
        },
        "interpretation": "NO_VERIFIED_PROVIDER_SYNERGY_OR_COMPLETED_VERIFICATION_OUTCOME",
        "elapsed_time_note": "Measured local Python processing only; not provider latency or founder effort",
        "incremental_dollar_cost": "NOT_MEASURED",
        "evidence_limit": "SNAPSHOT_REFERENCES_ARE_NOT_PROVIDER_ACCESS_OR_CURRENTNESS_PROOF",
        "provider_live_preflight": runtime_prerequisites(dict(os.environ)),
        "authority_effect": "NONE",
        "execution_capability": "LOCAL_READ_ONLY_ONLY",
        "verified_synergy": "NOT_ESTABLISHED",
    }


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    p = argparse.ArgumentParser(description="Run Resource Miner local outcome negative-control benchmark")
    p.add_argument("--snapshot", default=str(root / "data/resources.snapshot.jsonl"))
    p.add_argument("--config", default=str(root / "data/experiments/resource_complementarity_pilot.v1.json"))
    args = p.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    print(json.dumps(run_shadow_trial(load_snapshot(args.snapshot), config), indent=2))


if __name__ == "__main__":
    main()
