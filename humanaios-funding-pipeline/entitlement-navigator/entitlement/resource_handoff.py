from __future__ import annotations

from typing import Any

SCHEMA = "humanaios.resource-entitlement-handoff.v1"


def intake_resource_handoff(handoff: dict[str, Any]) -> dict[str, Any]:
    """Validate a Resource Miner handoff and open an Entitlement investigation."""
    if not isinstance(handoff, dict):
        raise ValueError("handoff must be an object")
    if handoff.get("schema") != SCHEMA:
        raise ValueError("unsupported resource handoff schema")
    if handoff.get("source_system") != "resource-miner":
        raise ValueError("handoff source_system must be resource-miner")
    if handoff.get("target_system") != "entitlement-navigator":
        raise ValueError("handoff target_system must be entitlement-navigator")
    if handoff.get("requested_action") != "VERIFY_ELIGIBILITY":
        raise ValueError("handoff requested_action must be VERIFY_ELIGIBILITY")

    eligibility = handoff.get("eligibility") or {}
    if eligibility.get("assessed") is not False:
        raise ValueError("upstream handoff cannot claim eligibility was assessed")
    if str(eligibility.get("status") or "").upper() != "UNASSESSED":
        raise ValueError("upstream handoff must remain UNASSESSED")
    if eligibility.get("claim") != "NO_ELIGIBILITY_CLAIM":
        raise ValueError("upstream handoff cannot carry an eligibility claim")

    resource = handoff.get("resource") or {}
    resource_id = str(resource.get("resource_id") or "").strip()
    if not resource_id:
        raise ValueError("resource.resource_id is required")

    provenance = handoff.get("provenance") or {}
    evidence = list(provenance.get("evidence") or [])

    return {
        "intake_type": "RESOURCE_INVESTIGATION",
        "resource_id": resource_id,
        "title": resource.get("title"),
        "classification": "INVESTIGATE",
        "eligibility_assessed": False,
        "eligibility_status": "UNASSESSED",
        "authority_effect": "NONE",
        "source_handoff_id": handoff.get("handoff_id"),
        "provenance": {
            "source_system": "resource-miner",
            "source_name": provenance.get("source_name"),
            "discovery_method": provenance.get("discovery_method"),
            "discovered_at": provenance.get("discovered_at"),
            "last_verified_at": provenance.get("last_verified_at"),
            "evidence": evidence,
        },
        "need_alignment": list(handoff.get("need_alignment") or []),
        "resource_miner_route": (handoff.get("routing") or {}).get("resource_miner_route"),
        "required_evidence": [
            "Current authoritative program/resource source",
            "Permitted applicant/entity types",
            "Applicant-specific eligibility predicates",
            "Geography/jurisdiction requirements where applicable",
            "Current availability and submission window",
        ],
        "next_actions": [
            "Verify the current authoritative source.",
            "Resolve applicant/entity predicates independently of Resource Miner scores.",
            "Record contradictory or missing evidence before changing classification.",
        ],
        "note": (
            "Resource Miner discovery and need alignment opened this investigation. "
            "They do not establish eligibility, entitlement, or a recommendation to apply."
        ),
    }
