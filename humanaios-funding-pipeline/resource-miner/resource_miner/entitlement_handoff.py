from __future__ import annotations

from typing import Any

SCHEMA = "humanaios.resource-entitlement-handoff.v1"


def _as_dict(candidate: Any) -> dict[str, Any]:
    if hasattr(candidate, "to_dict"):
        return dict(candidate.to_dict())
    if isinstance(candidate, dict):
        return dict(candidate)
    raise TypeError("candidate must be a ResourceCandidate or mapping")


def build_entitlement_handoff(candidate: Any) -> dict[str, Any]:
    """Build a provenance-preserving, non-authoritative Entitlement handoff."""
    data = _as_dict(candidate)
    resource_id = str(data.get("resource_id") or "").strip()
    if not resource_id:
        raise ValueError("resource_id is required")
    if data.get("eligibility_assessed") is not False:
        raise ValueError("Resource Miner handoff must remain eligibility_assessed=false")
    if str(data.get("eligibility_status") or "UNASSESSED").upper() != "UNASSESSED":
        raise ValueError("Resource Miner handoff cannot assert an eligibility result")

    return {
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
