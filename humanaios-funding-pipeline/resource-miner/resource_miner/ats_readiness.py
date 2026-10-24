"""Read-only ATS application readiness projection for a public historical specimen.

No private candidate record, parser oracle, account access, submissions or network I/O.
This is not a job-availability verification service. The report is a public-redacted
experiment anchored to a reported failed source and issue #992.
"""
from __future__ import annotations

from hashlib import sha256
import json
from typing import Any, Mapping

SPECIMEN_ID = "CONVERGENT-PROGRAM-LAUNCH-MANAGER-20261022"
PUBLIC_CASE: dict[str, Any] = {
    "specimen_id": SPECIMEN_ID,
    "employer": "Convergent Research",
    "position": "Program Launch Manager",
    "ats": "Lever",
    "source_url": "https://jobs.lever.co/convergentresearch/7b0506c1-caf2-4e92-9a44-d062c7a9b988",
    "source_observations": [
        {
            "kind": "REPOSITORY_RECORDED_USER_OBSERVATION",
            "observation": "HTTP_404_ON_DIRECT_JOB_LINK",
            "date": "2026-10-22",
            "source": "https://github.com/humanaios-ui/operations/issues/992",
        },
        {
            "kind": "USER_CORRECTION",
            "observation": "ROLE_NOT_LISTED_AT_LEVER_ENDPOINT",
            "date": "2026-10-22",
            "source": "USER_CONVERSATION_NOT_PUBLIC_LINK",
        },
    ],
    "historical_form": [
        "Resume/CV upload",
        "Name and email",
        "Current location",
        "Complex-project example",
        "Stakeholder trust example",
        "Motivation for scientific program launches",
        "Eastern-time collaboration",
        "City and state",
        "US work authorization declaration",
    ],
}
FAILED_OBSERVATIONS = frozenset({
    "HTTP_404_ON_DIRECT_JOB_LINK", "ROLE_NOT_LISTED_AT_LEVER_ENDPOINT",
    "SOURCE_UNAVAILABLE", "APPLICATION_LINK_FAILED",
})
ALLOWED_KINDS = frozenset({
    "REPOSITORY_RECORDED_USER_OBSERVATION", "USER_CORRECTION",
    "OFFICIAL_SITE_OBSERVATION",
})


def project_application_readiness(case: Mapping[str, Any]) -> dict[str, Any]:
    """Return only allowlisted public fields; never echo arbitrary user data.

    A negative observation makes the source inactionable, but NEVER proves closure.
    The function cannot assert that a role is open, even if a listing once existed.
    """
    if not isinstance(case, Mapping):
        raise ValueError("Case must be an object.")
    if case.get("specimen_id") != SPECIMEN_ID:
        raise ValueError("Unknown specimen.")
    observations = case.get("source_observations")
    if not isinstance(observations, list) or not 0 < len(observations) <= 16:
        raise ValueError("Source observations are required and bounded.")
    seen: list[dict[str, str]] = []
    for row in observations:
        if not isinstance(row, Mapping) or row.get("kind") not in ALLOWED_KINDS:
            raise ValueError("Unsupported source observation.")
        if row.get("observation") not in FAILED_OBSERVATIONS:
            raise ValueError("Only recorded source-failure observations are supported in E0.")
        # Strictly output predefined values; do not echo private notes/URLs.
        seen.append({
            "kind": str(row["kind"]),
            "observation": str(row["observation"]),
        })
    issue = "https://github.com/humanaios-ui/operations/issues/992"
    report: dict[str, Any] = {
        "specimen_id": SPECIMEN_ID,
        "report_type": "PUBLIC_REDACTED_HISTORICAL_ATS_READINESS",
        "employer": "Convergent Research",
        "position": "Program Launch Manager",
        "ats_platform": "Lever",
        "source_status": "REPORTED_UNAVAILABLE_AT_ORIGINAL_ENDPOINT",
        "role_closed": "NOT_ESTABLISHED",
        "actionable": False,
        "reason": (
            "Recorded source-failure observation(s): "
            + ", ".join(sorted({row["observation"] for row in seen}))
            + ". These observations do not establish employer closure or current availability."
        ),
        "source_observations": seen,
        "source_issue": issue,
        "source_freshness": "HISTORICAL_NOT_LIVE_RECHECKED",
        "historical_form_requirements": list(PUBLIC_CASE["historical_form"]),
        "form_standing": "INDEXED_HISTORICAL_NOT_CURRENTLY_VERIFIED",
        "applicant_qualification": "NOT_ASSESSED",
        "private_resume_evidence": "NOT_LOADED_IN_PUBLIC_SERVICE",
        "ats_resume_parser": "NOT_TESTED",
        "application_completeness": "NOT_ASSESSED",
        "submission": "NOT_SUBMITTED_BY_THIS_SERVICE",
        "decision": "HOLD_FOR_OFFICIAL_SOURCE_RECHECK",
        "models": {
            "intent_os": "Preserve investigation intent; never turn a question into an application.",
            "resource_miner": "Source failure does not imply role closure or applicant ineligibility.",
            "evidence_graph": "Separate human report, indexed page, and live verified source.",
            "witness": "Show uncertainty and corrections, without assigning authority.",
            "coordinator": "Read only; zero external action, PII disclosure, or submission.",
            "acat": "Use falsifiers and explicit evidence grades; no unmeasured ATS score.",
        },
        "authority": "NONE",
        "execution": "DISABLED",
    }
    raw = json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    report["receipt_sha256"] = sha256(raw.encode("utf-8")).hexdigest()
    report["receipt_kind"] = "UNSIGNED_PROJECTION_DIGEST_NOT_ATTESTATION"
    return report


def public_specimen_readiness() -> dict[str, Any]:
    """Stable read-only public test record. No private candidate content."""
    return project_application_readiness(PUBLIC_CASE)
