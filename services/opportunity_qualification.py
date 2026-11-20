"""Synthetic-only, read-only qualification card for one manually reviewed source."""
from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json
import re
from typing import Any
from urllib.parse import urlsplit

from services.career_gradient import learning_priorities, score_opportunity

SCHEMA = "humanaios.opportunity_qualification_card.e0.v1"
SOURCE_URI = (
    "https://careers.molinahealthcare.com/job/united-states/"
    "national-quality-performance-manager-remote/21726/102561038192"
)
_HASH = re.compile(r"^[0-9a-f]{64}$")
_LOCATOR = re.compile(r"^SYNTHETIC-[A-Z0-9_-]{1,60}$")
_ROOT_KEYS = {"schema", "source", "opportunity", "portfolio"}
_SOURCE_KEYS = {
    "issuer", "job_id", "title", "uri", "posting_date", "retrieved_at",
    "rendered_main_text_sha256", "snapshot_kind", "freshness",
    "availability_status", "uncertainty",
}
_EVIDENCE_KEYS = {"locator", "claim", "claim_state", "source_type"}
_REQUIREMENT_KEYS = {
    "label", "kind", "source_predicate", "mapping_state", "gap_type", "evidence_refs"
}
_MAPPING_STATES = {"DOCUMENTED", "PARTIAL", "UNKNOWN", "NOT_HELD", "BLOCKED"}
_CLAIM_STATES = {"SOURCE_SUPPORTED", "HUMAN_ATTESTED", "INFERRED", "UNVERIFIED"}


def _require_object(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"Invalid {label} shape")
    return value


def _require_text(value: Any, label: str, *, maximum: int = 500) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f"Invalid {label}")
    return value


def _validate_source(source_value: Any) -> dict[str, Any]:
    source = _require_object(source_value, _SOURCE_KEYS, "source")
    if (
        source["issuer"] != "Molina Healthcare"
        or source["job_id"] != "2040242"
        or source["uri"] != SOURCE_URI
        or source["title"] != "National Quality Performance Manager"
    ):
        raise ValueError("Unrecognized first-party opportunity source")
    parsed_uri = urlsplit(source["uri"])
    if (
        parsed_uri.scheme != "https"
        or parsed_uri.hostname != "careers.molinahealthcare.com"
        or parsed_uri.username is not None
        or parsed_uri.password is not None
        or parsed_uri.query
        or parsed_uri.fragment
    ):
        raise ValueError("Invalid first-party source URI")
    if not isinstance(source["posting_date"], str) or not isinstance(source["retrieved_at"], str):
        raise ValueError("Invalid source posting date")
    try:
        datetime.strptime(source["posting_date"], "%Y-%m-%d")
        retrieved = datetime.fromisoformat(source["retrieved_at"].replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid source observation time") from exc
    if not source["retrieved_at"].endswith("Z") or retrieved.utcoffset().total_seconds() != 0:
        raise ValueError("Source observation time must be UTC")
    if not isinstance(source["rendered_main_text_sha256"], str) or not _HASH.fullmatch(
        source["rendered_main_text_sha256"]
    ):
        raise ValueError("Invalid rendered-source digest")
    if source["snapshot_kind"] != "RENDERED_MAIN_TEXT_SHA256":
        raise ValueError("Unsupported source snapshot kind")
    if not isinstance(source["freshness"], str) or source["freshness"] not in {
        "CURRENT_AS_OBSERVED", "STALE", "UNKNOWN", "CONFLICTING"
    }:
        raise ValueError("Invalid source freshness")
    if source["availability_status"] != "UNKNOWN":
        raise ValueError("Application availability must remain unassessed")
    if (
        not isinstance(source["uncertainty"], list)
        or not source["uncertainty"]
        or len(source["uncertainty"]) > 10
        or any(not isinstance(item, str) or not item.strip() for item in source["uncertainty"])
        or any(len(item) > 300 for item in source["uncertainty"])
    ):
        raise ValueError("Source uncertainty must be explicit")
    return source


def _validate_portfolio(portfolio_value: Any) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    portfolio = _require_object(portfolio_value, {"fixture_class", "evidence"}, "portfolio")
    if portfolio["fixture_class"] != "SYNTHETIC_ONLY":
        raise ValueError("Only a synthetic portfolio fixture is accepted")
    evidence = portfolio["evidence"]
    if not isinstance(evidence, list) or not 1 <= len(evidence) <= 64:
        raise ValueError("Invalid bounded evidence list")
    by_locator: dict[str, dict[str, Any]] = {}
    for item_value in evidence:
        item = _require_object(item_value, _EVIDENCE_KEYS, "evidence item")
        locator = item["locator"]
        if not isinstance(locator, str) or not _LOCATOR.fullmatch(locator) or locator in by_locator:
            raise ValueError("Evidence locators must be unique synthetic references")
        if item["source_type"] != "SYNTHETIC_ARTIFACT":
            raise ValueError("Non-synthetic portfolio source")
        if not isinstance(item["claim_state"], str) or item["claim_state"] not in _CLAIM_STATES:
            raise ValueError("Invalid evidence claim state")
        _require_text(item["claim"], "synthetic evidence claim")
        by_locator[locator] = item
    return by_locator, evidence


def _validate_requirements(
    requirements_value: Any, evidence_by_locator: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    if not isinstance(requirements_value, list) or not 1 <= len(requirements_value) <= 16:
        raise ValueError("Invalid bounded opportunity requirements")
    requirements = []
    seen_labels = set()
    for requirement_value in requirements_value:
        requirement = _require_object(requirement_value, _REQUIREMENT_KEYS, "requirement")
        label = _require_text(requirement["label"], "requirement label", maximum=240)
        if label in seen_labels:
            raise ValueError("Requirement labels must be unique")
        seen_labels.add(label)
        if not isinstance(requirement["kind"], str) or requirement["kind"] not in {
            "DUTY", "REQUIRED", "PREFERRED"
        }:
            raise ValueError("Invalid requirement kind")
        if not isinstance(requirement["source_predicate"], str) or requirement[
            "source_predicate"
        ] not in {
            "DUTY", "REQUIREMENT", "PREFERENCE", "EXPLICIT_EXCLUSION", "UNKNOWN"
        }:
            raise ValueError("Invalid source predicate")
        if not isinstance(requirement["mapping_state"], str) or requirement[
            "mapping_state"
        ] not in _MAPPING_STATES:
            raise ValueError("Invalid requirement mapping state")
        if not isinstance(requirement["gap_type"], str) or requirement["gap_type"] not in {
            "evidence", "skill", "unknown", "blocker"
        }:
            raise ValueError("Invalid requirement gap type")
        refs = requirement["evidence_refs"]
        if not isinstance(refs, list) or any(
            not isinstance(ref, str) or ref not in evidence_by_locator for ref in refs
        ):
            raise ValueError("Requirement references unknown evidence")
        if requirement["mapping_state"] == "DOCUMENTED" and (
            not refs
            or any(evidence_by_locator[ref]["claim_state"] != "SOURCE_SUPPORTED" for ref in refs)
        ):
            raise ValueError("Documented matches require source-supported synthetic evidence")
        if requirement["mapping_state"] == "NOT_HELD" and not refs:
            raise ValueError("A reported missing capability requires synthetic evidence")
        if (
            requirement["mapping_state"] == "BLOCKED"
            and (
                requirement["kind"] != "REQUIRED"
                or requirement["source_predicate"] != "EXPLICIT_EXCLUSION"
            )
        ):
            raise ValueError("Blockers require an explicit source exclusion")
        if (
            requirement["source_predicate"] == "EXPLICIT_EXCLUSION"
            and (
                requirement["kind"] != "REQUIRED"
                or requirement["mapping_state"] != "BLOCKED"
            )
        ):
            raise ValueError("Explicit source exclusions must be represented as blockers")
        if (
            requirement["source_predicate"] == "UNKNOWN"
            and requirement["mapping_state"] == "DOCUMENTED"
        ):
            raise ValueError("Unknown source predicates cannot support a match")
        requirements.append(requirement)
    return requirements


def _requirement_category(requirement: dict[str, Any]) -> str | None:
    if requirement["source_predicate"] == "EXPLICIT_EXCLUSION":
        return "HARD_BLOCKER"
    if requirement["source_predicate"] == "UNKNOWN":
        return "SOURCE_UNKNOWN"
    if requirement["mapping_state"] == "DOCUMENTED":
        return None
    return "SKILL_GAP" if requirement["gap_type"] == "skill" else "EVIDENCE_GAP"


def _canonical_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(encoded.encode("utf-8")).hexdigest()


def project_qualification_card(payload: dict[str, Any]) -> dict[str, Any]:
    """Project a manually annotated source and synthetic portfolio without side effects."""
    data = _require_object(payload, _ROOT_KEYS, "fixture")
    if data["schema"] != SCHEMA:
        raise ValueError("Unsupported qualification fixture schema")
    source = _validate_source(data["source"])
    opportunity = _require_object(data["opportunity"], {"goal", "requirements"}, "opportunity")
    goal = _require_text(opportunity["goal"], "declared goal", maximum=240)
    evidence_by_locator, evidence = _validate_portfolio(data["portfolio"])
    requirements = _validate_requirements(opportunity["requirements"], evidence_by_locator)
    source_current = source["freshness"] == "CURRENT_AS_OBSERVED"

    supported_matches = []
    gaps = []
    for requirement in requirements:
        if not source_current:
            category = "SOURCE_STALE" if source["freshness"] == "STALE" else "SOURCE_UNKNOWN"
            gaps.append({
                "requirement": requirement["label"],
                "kind": requirement["kind"],
                "category": category,
                "mapping_state": requirement["mapping_state"],
            })
        elif requirement["mapping_state"] == "DOCUMENTED":
            supported_matches.append({
                "requirement": requirement["label"],
                "kind": requirement["kind"],
                "evidence_refs": list(requirement["evidence_refs"]),
                "evidence": [
                    {
                        "locator": evidence_by_locator[ref]["locator"],
                        "claim": evidence_by_locator[ref]["claim"],
                        "claim_state": evidence_by_locator[ref]["claim_state"],
                    }
                    for ref in requirement["evidence_refs"]
                ],
                "evidence_class": "SOURCE_SUPPORTED",
                "fixture_class": "SYNTHETIC_ONLY",
            })
        else:
            gaps.append({
                "requirement": requirement["label"],
                "kind": requirement["kind"],
                "category": _requirement_category(requirement),
                "mapping_state": requirement["mapping_state"],
            })

    mapped_opportunity = {
        "id": source["job_id"],
        "title": source["title"],
        "gradient_axes": {"evidence_gain": 0.6},
        "requirements": [
            {
                "label": item["label"],
                "capability": item["label"],
                "mapping_state": item["mapping_state"],
                "mandatory": item["kind"] == "REQUIRED",
                "gap_type": item["gap_type"],
            }
            for item in requirements
        ],
    }
    gradient = score_opportunity(mapped_opportunity)
    priorities = learning_priorities([mapped_opportunity])
    advancement_path = None
    if source_current:
        for requirement in requirements:
            if (
                requirement["kind"] == "PREFERRED"
                and requirement["mapping_state"] != "DOCUMENTED"
                and requirement["gap_type"] in {"evidence", "skill"}
            ):
                priority = next(
                    (row for row in priorities if row["capability"] == requirement["label"]),
                    None,
                )
                if priority is not None:
                    advancement_path = {
                        "requirement": requirement["label"],
                        "action": priority["action"],
                        "steps": [
                            "Search authorized existing evidence first.",
                            "If none is available, optionally create a synthetic practice artifact.",
                        ],
                        "next_decision": (
                            "Check existing evidence; if none is available, choose whether to "
                            "approve optional practice."
                        ),
                        "suggested_proof": [
                            "A query or work sample",
                            "A repeatable check of its expected result",
                        ],
                        "optional": True,
                        "does_not_block_pursuit": True,
                        "human_approval_required": True,
                    }
                    break
    elif source["freshness"] != "CURRENT_AS_OBSERVED":
        advancement_path = {
            "action": "VERIFY_CURRENT_SOURCE",
            "steps": ["Recheck the first-party source before relying on this opportunity."],
            "next_decision": "Choose whether to recheck the first-party posting.",
            "human_approval_required": True,
        }

    result = {
        "schema": SCHEMA,
        "opportunity": {
            "issuer": source["issuer"],
            "job_id": source["job_id"],
            "title": source["title"],
            "uri": source["uri"],
            "posting_date": source["posting_date"],
            "retrieved_at": source["retrieved_at"],
            "source_snapshot": {
                "kind": source["snapshot_kind"],
                "sha256": source["rendered_main_text_sha256"],
            },
            "freshness": source["freshness"],
            "availability_status": "UNKNOWN",
            "uncertainty": list(source["uncertainty"]),
            "goal": goal,
        },
        "portfolio_fixture": "SYNTHETIC_ONLY",
        "portfolio_evidence_count": len(evidence),
        "supported_matches": supported_matches,
        "gaps": gaps,
        "pathway_classification": gradient.classification if source_current else "HOLD",
        "mandatory_unknowns": list(gradient.mandatory_unknowns) if source_current else [],
        "eligibility_status": "UNASSESSED",
        "eligibility_assessed": False,
        "advancement_path": advancement_path,
        "execution_available": False,
        "can_submit_application": False,
        "can_contact_employer": False,
        "can_modify_portfolio": False,
        "authority_effect": "NONE",
    }
    return {**result, "projection_sha256": _canonical_digest(result)}
