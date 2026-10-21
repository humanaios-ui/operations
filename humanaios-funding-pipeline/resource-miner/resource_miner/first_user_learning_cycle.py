"""HumanAIOS offline learning cycle: bridge existing Oracle-SMAG-Miner to first-user preflight.

Read-only projection of the existing retrospective experiment plus a *fixed
synthetic* user-question/correction/decision trace. It cannot authenticate a
real user, witness outcomes, approve work, or change the platform.
"""
from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

from .oracle_smag_experiment import offline_fixture_report

SCHEMA = "humanaios.first_user_learning_cycle.offline_v0_1"
SYNTHETIC_INTENT = (
    {"seq": 1, "kind": "QUESTION", "actor": "SYNTHETIC_FIRST_USER",
     "text": "Can HumanAIOS explain the evidence gaps without changing a repository?",
     "authority_effect": "NONE"},
    {"seq": 2, "kind": "CORRECTION", "actor": "SYNTHETIC_FIRST_USER",
     "text": "Show only sources and uncertainty; no submission or approval.",
     "supersedes_seq": 1, "authority_effect": "NONE"},
    {"seq": 3, "kind": "DECISION", "actor": "SYNTHETIC_FIRST_USER",
     "text": "I choose review only, not execution.", "choice": "REVIEW_ONLY",
     "authority_effect": "NONE"},
)
LIVE_GATES = (
    "TRUSTED_DEPLOY_SHA_AND_ORIGIN_VERIFIED",
    "ACCESS_IDENTITY_AND_ALLOWLIST_VERIFIED",
    "CONSENT_AND_NO_DELEGATED_MANDATE_VERIFIED",
    "HUMAN_INTENT_CORRECTION_CONFIRMED_BY_USER",
    "MINER_READ_ONLY_RESULT_AND_LIMITS_OBSERVED",
    "HUMAN_DECISION_RECORDED_WITHOUT_EXECUTION",
    "INDEPENDENT_RESULT_REVIEW_WITH_SOURCE_AND_TIME",
)


def _digest(value: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()


def project_first_user_preflight(
    *, events: tuple[dict, ...] | list[dict] | None = None,
    replay: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Fail closed if synthetic replay is misrepresented as real human qualification."""
    if events is None:
        events = SYNTHETIC_INTENT
    if not isinstance(events, (list, tuple)) or list(events) != list(SYNTHETIC_INTENT):
        raise ValueError("Only the checked-in synthetic onboarding script is permitted")
    script = copy.deepcopy(list(events))
    source = offline_fixture_report() if replay is None else copy.deepcopy(replay)
    if not isinstance(source, dict) or source.get("schema") != "humanaios.oracle_smag_miner_experiment.offline_v0_1":
        raise ValueError("An existing offline Oracle-SMAG-Miner replay is required")
    expected = {
        "authority_effect": "NONE",
        "merge_authority": False,
        "oracle_claim_status": "DESCRIPTIVE_ONLY",
        "calibration_warrant": "UNVERIFIED",
        "retrospective_precommitment_authenticated": False,
        "outcomes_independently_attested": False,
        "f3_challenge_performed": False,
    }
    if any(type(source.get(k)) is not type(v) or source.get(k) != v for k, v in expected.items()):
        raise ValueError("Upstream replay cannot claim independent calibration or authority")
    if (_digest({k: v for k, v in source.items() if k != "digest_sha256"})
            != source.get("digest_sha256")):
        raise ValueError("Upstream report digest mismatch")
    frame, count, resolved, pending = (
        source.get("sampling_frame"), source.get("frame_count"),
        source.get("resolved_count"), source.get("pending_count")
    )
    if (not isinstance(frame, list) or not all(type(n) is int and n > 0 for n in frame)
            or len(frame) != len(set(frame)) or type(count) is not int
            or type(resolved) is not int or type(pending) is not int
            or min(count, resolved, pending) < 0 or count != len(frame)
            or count != resolved + pending):
        raise ValueError("Incomplete or inconsistent sampling frame")
    gaps = source.get("miner_candidate_codes")
    allowed_gaps = {
        "MISSING_VERIFICATION", "STALE_RECEIPT", "SOURCE_CHANGED_REVERIFY",
        "SOURCE_CHANGE_UNMAPPED", "CONFLICTING_CLAIM_BINDINGS",
        "MERGED_WITH_FAILED_ADMISSION",
    }
    if (not isinstance(gaps, list) or source.get("miner_candidate_count") != len(gaps)
            or not all(type(code) is str and code in allowed_gaps for code in gaps)):
        raise ValueError("Resource Miner output is not bounded evidence-only")
    report = {
        "schema": SCHEMA,
        "scope": "OFFLINE_SYNTHETIC_PREFLIGHT",
        "intent_events": script,  # preserved in original order; not parsed into permissions
        "question_preserved": script[0]["text"],
        "correction_preserved": script[1]["text"],
        "human_choice": "SIMULATED_REVIEW_ONLY",
        "observation_frame": sorted(frame),
        "resolved_count": resolved,
        "pending_count": pending,
        "forecast": {
            "status": "DESCRIPTIVE_ONLY",
            "smag_brier": source.get("brier_smag_resolved"),
            "baseline_brier": source.get("brier_constant_0_5_resolved"),
            "independent_attestation": "MISSING",
        },
        "verification_frontier": {
            "candidate_count": len(gaps),
            "candidate_codes": sorted(gaps),
            "transport_provenance": "UNVERIFIED_CALLER_SUPPLIED",
            "action_authorized": False,
        },
        "cycle": [
            {"stage": "OBSERVE", "state": "HISTORICAL_SNAPSHOT_ONLY"},
            {"stage": "PREDICT", "state": "RETROSPECTIVE_REPLAY_ONLY"},
            {"stage": "CHALLENGE", "state": "NOT_PERFORMED"},
            {"stage": "VERIFY", "state": "NOT_INDEPENDENTLY_ATTESTED"},
            {"stage": "CALIBRATE", "state": "DESCRIPTIVE_ONLY"},
            {"stage": "IDENTIFY_GAPS", "state": "ADVISORY_CANDIDATES"},
            {"stage": "HUMAN_DECIDE", "state": "SYNTHETIC_REVIEW_ONLY"},
            {"stage": "IMPROVE", "state": "WAIT_FOR_PROSPECTIVE_EVIDENCE"},
        ],
        "qualification": {
            "preflight": "REPRODUCIBLE_OFFLINE_HARNESS",
            "first_user": "NOT_QUALIFIED_LIVE",
            "missing_live_evidence": list(LIVE_GATES),
        },
        "authority_effect": "NONE",
        "execution": "DISABLED",
        "on_track": "PREFLIGHT_ONLY",
    }
    report["digest_sha256"] = _digest(report)
    return report


if __name__ == "__main__":
    print(json.dumps(project_first_user_preflight(), indent=2, sort_keys=True))
