"""Domain adapters for the Guiding Light general gradient engine.

Adapters normalize existing Operations artifacts without upgrading their evidence.
They intentionally preserve the authority boundary of each source system.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any


def career_snapshot_to_generic(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Normalize the v0.1 career snapshot into the v0.2 generic target contract."""
    targets: list[dict[str, Any]] = []

    for opportunity in snapshot.get("opportunities") or []:
        target = deepcopy(opportunity)
        target["domain"] = "career"
        target["target_value"] = target.pop(
            "opportunity_value",
            target.get("target_value", 0.5),
        )
        if "gradient_axes" in target and "value_axes" not in target:
            target["value_axes"] = target.pop("gradient_axes")

        for requirement in target.get("requirements") or []:
            if "label" not in requirement and "capability" in requirement:
                requirement["label"] = requirement["capability"]

        targets.append(target)

    return {
        "schema_version": "0.2.0",
        "subject": {
            "id": snapshot.get("profile_id", "career-profile"),
            "type": "person",
        },
        "domain": "career",
        "declared_goal_source": snapshot.get("declared_goal_source", "user"),
        "selected_target": snapshot.get("selected_target"),
        "source_refs": snapshot.get("source_refs", []),
        "omissions": snapshot.get("omissions", []),
        "uncertainty": snapshot.get("uncertainty", []),
        "targets": targets,
    }


def resource_candidate_to_target(candidate: dict[str, Any]) -> dict[str, Any]:
    """Normalize a Resource Miner candidate without claiming applicant eligibility.

    Resource Miner is discovery. Need alignment and source provenance may be carried
    forward, but unassessed eligibility remains a mandatory UNKNOWN.
    """
    refs = []
    for key in ("canonical_url", "primary_source_url", "source_url"):
        value = candidate.get(key)
        if value and value not in refs:
            refs.append(value)

    for evidence in candidate.get("evidence") or []:
        url = evidence.get("url") if isinstance(evidence, dict) else None
        if url and url not in refs:
            refs.append(url)

    need_scores = [
        float(match.get("score", 0.0))
        for match in candidate.get("need_matches") or []
        if isinstance(match, dict)
    ]
    value_axes = {}
    normalized_need_alignment = (
        max(0.0, min(1.0, max(need_scores))) if need_scores else None
    )
    if normalized_need_alignment is not None:
        value_axes["need_alignment"] = normalized_need_alignment

    eligibility_assessed = bool(candidate.get("eligibility_assessed"))
    eligibility_state = "PARTIAL" if eligibility_assessed else "UNKNOWN"

    return {
        "id": str(candidate.get("resource_id", "")),
        "title": str(candidate.get("title", "Untitled resource")),
        "domain": "resource",
        "target_type": "external_resource",
        "target_value": normalized_need_alignment if normalized_need_alignment is not None else 0.5,
        "value_axes": value_axes,
        "requirements": [
            {
                "id": "authoritative-eligibility",
                "label": "Authoritative applicant eligibility",
                "weight": 1.0,
                "mandatory": True,
                "mapping_state": eligibility_state,
                "gap_type": "authority",
                "artifact_target": "verified eligibility determination",
            }
        ],
        "source_refs": refs,
        "source_status": candidate.get("status", "UNKNOWN"),
        "source_route": candidate.get("route", "VERIFY_NOW"),
        "eligibility_status": candidate.get("eligibility_status", "UNASSESSED"),
        "authority_note": (
            "Resource Miner relevance is discovery evidence only; eligibility must be "
            "verified by the appropriate domain authority."
        ),
    }


def funding_source_to_target(source: dict[str, Any]) -> dict[str, Any]:
    """Normalize the legacy funding dataset as discovery-only.

    Existing tags are not silently converted into applicant eligibility.
    """
    refs = [value for value in [source.get("url")] if value]
    return {
        "id": str(source.get("id") or source.get("name") or ""),
        "title": str(source.get("name", "Untitled funding source")),
        "domain": "funding",
        "target_type": str(source.get("category", "funding")),
        "target_value": 0.5,
        "value_axes": {},
        "requirements": [
            {
                "id": "funding-eligibility-verification",
                "label": "Current authoritative funding eligibility",
                "weight": 1.0,
                "mandatory": True,
                "mapping_state": "UNKNOWN",
                "gap_type": "authority",
                "artifact_target": "current eligibility evidence",
            }
        ],
        "source_refs": refs,
        "source_status": source.get("status"),
        "deadline": source.get("deadline"),
        "award_size": source.get("award_size"),
        "authority_note": (
            "Legacy funding tags support discovery/routing only. They do not establish "
            "current applicant eligibility."
        ),
    }


def entitlement_result_to_target(result: dict[str, Any]) -> dict[str, Any]:
    """Normalize an Entitlement Navigator EvaluationResult.

    PASS is mapped to USER_ATTESTED rather than DOCUMENTED because EvaluationResult
    alone does not reveal whether the underlying applicant predicate was supported by
    documentary evidence. The navigator's status and legal note remain authoritative
    metadata and are never replaced by Guiding Light classification.
    """
    requirements: list[dict[str, Any]] = []

    for index, predicate in enumerate(result.get("predicates") or [], 1):
        state = str(predicate.get("state", "UNKNOWN")).upper()
        mapping_state = {
            "PASS": "USER_ATTESTED",
            "FAIL": "BLOCKED",
            "UNKNOWN": "UNKNOWN",
        }.get(state, "UNKNOWN")

        requirements.append(
            {
                "id": str(predicate.get("field") or f"predicate-{index}"),
                "label": str(predicate.get("label") or f"Predicate {index}"),
                "weight": 1.0,
                "mandatory": True,
                "mapping_state": mapping_state,
                "gap_type": "authority" if state == "UNKNOWN" else "evidence",
                "evidence_needed": list(predicate.get("evidence") or []),
                "note": predicate.get("note"),
            }
        )

    refs = []
    for source in result.get("sources") or []:
        if isinstance(source, dict):
            url = source.get("url")
            if url and url not in refs:
                refs.append(url)

    return {
        "id": str(result.get("program_id", "")),
        "title": str(result.get("title", "Untitled entitlement pathway")),
        "domain": "entitlement",
        "target_type": str(result.get("program_type", "benefit")),
        "target_value": 0.5,
        "value_axes": {},
        "requirements": requirements,
        "source_refs": refs,
        "source_status": result.get("status"),
        "required_evidence": list(result.get("required_evidence") or []),
        "next_actions": list(result.get("next_actions") or []),
        "last_verified": result.get("last_verified"),
        "authority_note": result.get("legal_note"),
    }
