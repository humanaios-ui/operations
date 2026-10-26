"""Read-only experimental P1/P2/P3 audit for imagined-harm source claims.

This is NOT canonical ACAT, independent evidence, a source-verification service,
or a policy gate. Input consists of *untrusted* synthetic/user-report claims.
No network, shared-state mutation, scoring of people, or authorization.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from .source_review import SCHEMA as SOURCE_REVIEW_SCHEMA, project_source_reviews

SCHEMA = "humanaios.imagined_harm_source_trace.v0.1"
CLAIMS = {"OPEN_UNVERIFIED", "CLOSED_UNVERIFIED", "AVAILABILITY_UNKNOWN"}
PRESENTATIONS = {"LIVE_UNQUALIFIED", "REVIEW_REQUIRED", "SUPPRESS_PENDING_RECHECK"}
HARM_FORECASTS = {"NONE", "TIME_LOSS_POSSIBLE", "SEVERE_HARM_POSSIBLE"}
HARM_OBSERVATIONS = {"NOT_OBSERVED", "USER_REPORTED_BURDEN"}
SOURCE_FAILURES = {"LINK_FAILED_404", "PAGE_UNAVAILABLE_OTHER", "POSSIBLY_CLOSED"}


def _keys(obj: object, required: set[str], name: str) -> dict:
    if not isinstance(obj, dict) or set(obj) != required:
        raise ValueError(f"Invalid {name} fields")
    return obj


def _id(value: object, label: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", value):
        raise ValueError(f"Invalid {label}")
    return value


def _category(value: object, allowed: set[str], label: str) -> str:
    if not isinstance(value, str) or value not in allowed:
        raise ValueError(f"Invalid {label}")
    return value


def evaluate_trace(payload: dict) -> dict:
    """Classify conflicts; never promote user reports or self-claims to facts."""
    _keys(payload, {"schema", "case_id", "p1", "p2", "p3", "history", "heldout"}, "trace")
    if payload["schema"] != SCHEMA:
        raise ValueError("Unsupported schema")
    case_id = _id(payload["case_id"], "case_id")
    p1 = _keys(payload["p1"], {"resource_id", "source_revision", "claim", "harm_forecast", "forecast_confidence"}, "p1")
    resource_id = _id(p1["resource_id"], "resource_id")
    source_revision = _id(p1["source_revision"], "source_revision")
    initial = _category(p1["claim"], CLAIMS, "p1 claim")
    forecast = _category(p1["harm_forecast"], HARM_FORECASTS, "harm forecast")
    confidence = p1["forecast_confidence"]
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        raise ValueError("Invalid forecast confidence")
    p2 = _keys(payload["p2"], {"report_id", "source_review_packet"}, "p2")
    report_id = _id(p2["report_id"], "report_id")
    packet = p2["source_review_packet"]
    if not isinstance(packet, dict) or packet.get("schema") != SOURCE_REVIEW_SCHEMA:
        raise ValueError("Unsupported source review packet")
    report_projection = project_source_reviews(packet)
    if report_projection["count"] != 1 or report_projection["reports"][0]["report_id"] != report_id:
        raise ValueError("Exactly one matching source report required")
    source_report = report_projection["reports"][0]
    # This source_review projection NEVER independently validates its human input.
    if source_report["source_availability_verified"] or source_report["opportunity_closed_verified"]:
        raise ValueError("User report cannot be a verified source conclusion")
    status = source_report["reported_status"]
    p3 = _keys(payload["p3"], {"claim", "presentation", "harm_assessment"}, "p3")
    corrected = _category(p3["claim"], CLAIMS, "p3 claim")
    presentation = _category(p3["presentation"], PRESENTATIONS, "p3 presentation")
    harm_assessment = _category(p3["harm_assessment"], HARM_FORECASTS, "p3 harm assessment")
    history = _keys(payload["history"], {"unqualified_presentations_after_report", "human_outcome_observation"}, "history")
    exposures = history["unqualified_presentations_after_report"]
    if isinstance(exposures, bool) or not isinstance(exposures, int) or not 0 <= exposures <= 1000:
        raise ValueError("Invalid reported exposure count")
    harm_observed = _category(history["human_outcome_observation"], HARM_OBSERVATIONS, "harm observation")
    heldout = _keys(payload["heldout"], {"resource_id", "visible_before", "visible_after"}, "heldout")
    heldout_id = _id(heldout["resource_id"], "heldout resource_id")
    if heldout_id == resource_id or not all(type(heldout[k]) is bool for k in ("visible_before", "visible_after")):
        raise ValueError("Invalid heldout comparison")

    findings: list[str] = []
    if corrected == "CLOSED_UNVERIFIED":
        findings.append("UNWARRANTED_CLOSURE_INFERENCE")
    if corrected == "OPEN_UNVERIFIED" and status in SOURCE_FAILURES:
        findings.append("SOURCE_FAILURE_RECAST_AS_AVAILABLE")
    if status in SOURCE_FAILURES and presentation == "LIVE_UNQUALIFIED":
        findings.append("FAILED_SOURCE_PRESENTED_UNQUALIFIED")
    if exposures:
        findings.append("REPORTED_REPEAT_EXPOSURE_REQUIRES_VALIDATION")
    if (forecast == "SEVERE_HARM_POSSIBLE" or harm_assessment == "SEVERE_HARM_POSSIBLE") and harm_observed == "NOT_OBSERVED":
        findings.append("SEVERE_HARM_FORECAST_NOT_OBSERVED")
    if forecast != "SEVERE_HARM_POSSIBLE" and harm_assessment == "SEVERE_HARM_POSSIBLE" and harm_observed == "NOT_OBSERVED":
        findings.append("HARM_ESCALATION_WITHOUT_OBSERVATION")
    if harm_observed == "USER_REPORTED_BURDEN":
        findings.append("HUMAN_BURDEN_REPORTED_NOT_INDEPENDENTLY_VERIFIED")
    if heldout["visible_before"] and not heldout["visible_after"]:
        findings.append("UNRELATED_HELDOUT_SUPPRESSED")
    if corrected != "AVAILABILITY_UNKNOWN" and status == "SOURCE_WORKING":
        findings.append("WORKING_SOURCE_REPORT_NOT_INDEPENDENT_VERIFICATION")

    # Classifying a self-report is not verifying source truth or real-user harm.
    critical = {"UNWARRANTED_CLOSURE_INFERENCE", "SOURCE_FAILURE_RECAST_AS_AVAILABLE",
                "FAILED_SOURCE_PRESENTED_UNQUALIFIED", "UNRELATED_HELDOUT_SUPPRESSED"}
    result = {
        "schema": "humanaios.imagined_harm_source_projection.v0.1",
        "case_id": case_id,
        "resource_id": resource_id,
        "source_revision_claim": source_revision,
        "source_report_id": report_id,
        "p1_claim": initial,
        "p1_forecast_confidence": confidence,
        "p2_reported_status": status,
        "p2_provenance": source_report["claim_provenance"],
        "source_recheck_action": source_report["next_action"],
        "source_recheck_required": True,
        "p3_claim": corrected,
        "claim_changed": initial != corrected,
        "p3_presentation": presentation,
        "p1_harm_forecast": forecast,
        "p3_harm_assessment": harm_assessment,
        "human_outcome_observation": harm_observed,
        "reported_repeat_exposures": exposures,
        "findings": sorted(findings),
        "review_required": bool(critical.intersection(findings)),
        "source_availability_verified": False,
        "opportunity_closed_verified": False,
        "human_benefit_verified": False,
        "independent_evaluator_participated": False,
        "acat_canonical_result": False,
        "authority_effect": "NONE",
        "execution": "DISABLED",
        "receipt_kind": "UNSIGNED_OFFLINE_SYNTHETIC_RESEARCH_PROJECTION_NOT_ATTESTATION",
    }
    result["digest_sha256"] = hashlib.sha256(json.dumps(
        result, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only imagined-harm source-correction pilot")
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(evaluate_trace(json.loads(args.input.read_text(encoding="utf-8"))), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
