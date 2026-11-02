"""Read-only, source-bound correction proposals over Resource Miner candidates.

Existing ResourceCandidate and INTENT-OS are reused. No network, account access,
authorization, persistence, eligibility determination, calendar mutation or
financial execution. Source feedback is data, never an instruction.
"""
from __future__ import annotations

import hashlib
import ipaddress
import json
import re
from datetime import datetime
from urllib.parse import urlsplit

from .models import ResourceCandidate

SCHEMA = "humanaios.resource-correction-proposal.v0.1"
PROJECTION = "humanaios.resource-correction-projection.v0.1"
FINDINGS = {
    "LINK_FAILED_404", "ROLE_NOT_LISTED", "DEADLINE_CONFLICT",
    "TAX_CREDIT_AS_REBATE", "TAXABLE_GRANT_AS_EXCLUDED",
    "SOURCE_UNAVAILABLE", "OFFICIAL_SOURCE_RECHECKED",
}
HOLD = FINDINGS - {"OFFICIAL_SOURCE_RECHECKED"}
TAX_MECHANISM = {
    "TAX_CREDIT_AS_REBATE": "CREDIT",
    "TAXABLE_GRANT_AS_EXCLUDED": "GENERALLY_TAXABLE",
}
IDENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,95}\Z")


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _time(value: object) -> str:
    if type(value) is not str or len(value) > 48:
        raise ValueError("bounded observation time required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.utcoffset() is None:
            raise ValueError("timezone required")
    except ValueError as exc:
        raise ValueError("ISO8601 timezone-aware time required") from exc
    return value


def _public_url(value: object) -> str:
    if type(value) is not str or not 1 <= len(value) <= 1000:
        raise ValueError("bounded public HTTPS source required")
    parsed = urlsplit(value)
    host = parsed.hostname or ""
    if (parsed.scheme != "https" or not host or "." not in host
            or parsed.username or parsed.password or parsed.port not in (None, 443)
            or any(c.isspace() or ord(c) < 32 for c in value)
            or host.lower() in {"localhost"} or host.endswith((".local", ".internal"))
            or parsed.fragment):
        raise ValueError("source must be public HTTPS with no credentials or fragment")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return value
    raise ValueError("literal IP address not permitted")


def propose(candidate: ResourceCandidate, observation: dict) -> dict:
    """Freeze one disputed claim without mutating an original candidate.

    An observation is NOT authenticated or accepted as a legal/source finding.
    Any proposed tax category is provisional and orthogonal to resource_types.
    """
    if not isinstance(candidate, ResourceCandidate):
        raise ValueError("existing ResourceCandidate required")
    if type(observation) is not dict or set(observation) != {
        "resource_id", "source_url", "observed_at", "finding", "evidence_url",
    }:
        raise ValueError("expected exact non-private correction observation fields")
    resource_id = candidate.resource_id
    if type(resource_id) is not str or not IDENT.fullmatch(resource_id):
        raise ValueError("invalid resource ID")
    if observation["resource_id"] != resource_id:
        raise ValueError("resource identity mismatch")
    source = _public_url(observation["source_url"])
    permitted_sources = {
        candidate.source_url, candidate.canonical_url, candidate.primary_source_url,
    }
    if source not in permitted_sources:
        raise ValueError("observation not bound to this candidate source")
    finding = observation["finding"]
    if finding not in FINDINGS:
        raise ValueError("unsupported correction finding")
    evidence = _public_url(observation["evidence_url"])
    observed_at = _time(observation["observed_at"])
    candidate_sha = _digest(candidate.to_dict(include_raw=False))
    observation_sha = _digest(observation)
    proposal_id = "CORR-" + _digest([resource_id, candidate_sha, observation_sha])[:20].upper()
    return {
        "schema": SCHEMA,
        "proposal_id": proposal_id,
        "resource_id": resource_id,
        "candidate_sha256": candidate_sha,
        "source_url": source,
        "evidence_url": evidence,
        "observed_at": observed_at,
        "finding": finding,
        "provisional_tax_mechanism": TAX_MECHANISM.get(finding, "UNKNOWN"),
        "source_verification_status": ("RECHECK_REQUIRED" if finding in HOLD
                                       else "UNVERIFIED_RECHECK"),
        "proposed_control": ("HOLD_FOR_SOURCE_REVIEW" if finding in HOLD
                             else "DO_NOT_RELEASE_WITHOUT_HUMAN_REVIEW"),
        "verification": "UNVERIFIED_SOURCE_OBSERVATION",
        "eligibility": "UNASSESSED",
        "outcome": "NOT_OBSERVED",
        "financial_roi": "NOT_MEASURED",
        "human_decision": "PENDING",
        "authority_effect": "NONE",
        "execution": "DISABLED",
    }


def project(candidates: list[ResourceCandidate], proposals: list[dict]) -> dict:
    """Overlay source holds on COPIES for INTENT-OS; original rows are untouched.

    Proposed revisions never become evidence of eligibility, closure, finance or
    positive source availability. Any mismatched/forged/stale proposal fails closed.
    """
    if type(candidates) is not list or type(proposals) is not list:
        raise ValueError("bounded candidate/proposal lists required")
    if len(candidates) > 500 or len(proposals) > 500:
        raise ValueError("too many candidates or corrections")
    by_id = {}
    for c in candidates:
        if not isinstance(c, ResourceCandidate) or c.resource_id in by_id:
            raise ValueError("invalid or duplicate original resource")
        by_id[c.resource_id] = c
    applied = {}
    for p in proposals:
        if type(p) is not dict or set(p) != {
            "schema", "proposal_id", "resource_id", "candidate_sha256", "source_url",
            "evidence_url", "observed_at", "finding", "provisional_tax_mechanism",
            "source_verification_status", "proposed_control", "verification",
            "eligibility", "outcome", "financial_roi", "human_decision",
            "authority_effect", "execution",
        }:
            raise ValueError("invalid/extra proposal fields")
        c = by_id.get(p["resource_id"])
        if c is None or p["resource_id"] in applied:
            raise ValueError("unmatched/duplicate correction")
        observation = {key: p[key] for key in (
            "resource_id", "source_url", "observed_at", "finding", "evidence_url")}
        if propose(c, observation) != p:
            raise ValueError("stale, forged or modified correction")
        applied[c.resource_id] = p
    rows = []
    for c in candidates:
        row = c.to_dict(include_raw=False)
        if c.resource_id in applied:
            p = applied[c.resource_id]
            row["source_verification_status"] = p["source_verification_status"]
            row["source_review_state"] = p["proposed_control"]
            # Provisional tax mechanism is a research annotation, not resource
            # taxonomy, verified tax treatment, applicant-specific eligibility,
            # or a positive cash/refund claim.
            row["tax_mechanism_proposed"] = p["provisional_tax_mechanism"]
        rows.append(row)
    return {
        "schema": PROJECTION,
        "rows": rows,
        "held_count": sum(row.get("source_verification_status") == "RECHECK_REQUIRED" for row in rows),
        "correction_ids": sorted(p["proposal_id"] for p in applied.values()),
        "next_human_action": "Verify official source, review correction, authorize any separate branch repair.",
        "provenance": "CALLER_SUPPLIED_NOT_INDEPENDENTLY_AUTHENTICATED",
        "authority_effect": "NONE",
        "execution": "DISABLED",
        "realized_benefit": "NOT_VERIFIED",
        "financial_roi": "NOT_MEASURED",
    }
