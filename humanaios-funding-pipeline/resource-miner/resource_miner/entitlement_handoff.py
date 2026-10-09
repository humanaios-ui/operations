from __future__ import annotations

from typing import Any

SCHEMA = "humanaios.resource-entitlement-handoff.v1"


def _as_dict(candidate: Any) -> dict[str, Any]:
    if hasattr(candidate, "to_dict"):
        return dict(candidate.to_dict())
    if isinstance(candidate, dict):
        return dict(candidate)
    raise TypeError("candidate must be a ResourceCandidate or mapping")


def build_entitlement_handoff(candidate: Any, opportunity_claim: Any | None = None) -> dict[str, Any]:
    """Build a provenance-preserving, non-authoritative Entitlement handoff.\n\n    When an Opportunity Claim is supplied, carry its epistemic state forward\n    without treating that claim as eligibility, warrant, or authorization.\n    """
    data = _as_dict(candidate)
    resource_id = str(data.get("resource_id") or "").strip()
    if not resource_id:
        raise ValueError("resource_id is required")
    if data.get("eligibility_assessed") is not False:
        raise ValueError("Resource Miner handoff must remain eligibility_assessed=false")
    if str(data.get("eligibility_status") or "UNASSESSED").upper() != "UNASSESSED":
        raise ValueError("Resource Miner handoff cannot assert an eligibility result")

    claim_data: dict[str, Any] | None = None
    if opportunity_claim is not None:
        claim_data = _as_dict(opportunity_claim)
        claim_opportunity_id = str(claim_data.get("opportunity_id") or "").strip()
        candidate_opportunity_id = str(data.get("opportunity_id") or "").strip()
        if not claim_opportunity_id or claim_opportunity_id != candidate_opportunity_id:
            raise ValueError("Opportunity Claim must reference the candidate opportunity_id")
        facets = {
            str(row.get("name") or ""): str(row.get("state") or "")
            for row in claim_data.get("facets") or []
            if isinstance(row, dict)
        }
        if facets.get("ELIGIBILITY") != "UNASSESSED":
            raise ValueError("Resource Miner Opportunity Claim cannot pre-resolve eligibility")
        if str(claim_data.get("authorization_state") or "") != "NOT_REQUESTED":
            raise ValueError("Resource Miner Opportunity Claim cannot carry authorization")
        if str(claim_data.get("authority_effect") or "") != "NONE":
            raise ValueError("Resource Miner Opportunity Claim cannot grant authority")

    handoff = {
        "schema": SCHEMA,
        "handoff_id": f"rm:{resource_id}",
        "source_system": "resource-miner",
        "target_system": "entitlement-navigator",
        "requested_action": "VERIFY_ELIGIBILITY",
        "authority_effect": "NONE",
        "resource": {
            "resource_id": resource_id,
            "title": data.get("title"),
            "sponsor": data.get("sponsor"),
            "canonical_url": data.get("canonical_url"),
            "source_url": data.get("source_url"),
            "primary_source_url": data.get("primary_source_url"),
            "resource_types": list(data.get("resource_types") or []),
            "applicant_types": list(data.get("applicant_types") or []),
            "geography": list(data.get("geography") or []),
            "tags": list(data.get("tags") or []),
            "deadline": data.get("deadline"),
            "status": data.get("status"),
        },
        "provenance": {
            "source_name": data.get("source_name"),
            "discovery_method": data.get("discovery_method"),
            "discovered_at": data.get("discovered_at"),
            "last_verified_at": data.get("last_verified_at"),
            "evidence": list(data.get("evidence") or []),
        },
        "need_alignment": list(data.get("need_matches") or []),
        "routing": {
            "resource_miner_route": data.get("route"),
            "note": "Need alignment and Resource Miner routing are discovery signals only.",
        },
        "eligibility": {
            "assessed": False,
            "status": "UNASSESSED",
            "claim": "NO_ELIGIBILITY_CLAIM",
        },
    }

    if claim_data is not None:
        handoff["opportunity_claim"] = {
            "claim_id": claim_data.get("claim_id"),
            "claim_token": claim_data.get("claim_token"),
            "opportunity_id": claim_data.get("opportunity_id"),
            "opportunity_token": claim_data.get("opportunity_token"),
            "overall_state": claim_data.get("overall_state"),
            "facets": list(claim_data.get("facets") or []),
            "falsifiers": list(claim_data.get("falsifiers") or []),
            "unknowns": list(claim_data.get("unknowns") or []),
            "constraints": list(claim_data.get("constraints") or []),
            "warrant_state": claim_data.get("warrant_state"),
            "authorization_state": claim_data.get("authorization_state"),
            "actionability_state": claim_data.get("actionability_state"),
            "authority_effect": claim_data.get("authority_effect"),
        }
    return handoff
