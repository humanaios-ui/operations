from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlsplit

ALLOWED_ACTIVATION_STATES = {"ACTIVE", "CONDITIONAL", "INACTIVE"}
ALLOWED_RESOLUTION_MODES = {"COMPOSE_INTERNAL", "ACQUIRE_EXTERNAL", "HYBRID"}
ALLOWED_SUBSTITUTION_STATES = {"ADEQUATE", "PARTIAL", "INADEQUATE", "UNKNOWN"}
ALLOWED_PRIVACY_CLASSES = {"PRIVATE", "PUBLIC_SAFE"}
ALLOWED_IMPLEMENTATION_STATES = {"NOT_STARTED", "PROPOSED", "MERGED"}
ALLOWED_DEPLOYMENT_STATES = {"UNVERIFIED", "OBSERVED_NOT_LIVE", "OBSERVED_LIVE"}
THREE_SOURCE_CLAIM = "CAPABILITY_NOT_STARTED"
SHA40 = re.compile(r"^[0-9a-f]{40}$")


def load_resource_plan(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Resource plan must be a JSON object")
    validate_resource_plan(data)
    return data


def load_three_source_pilot(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Three-source pilot must be a JSON object")
    validate_three_source_pilot(data)
    return data


def _exact_fields(record: dict[str, Any], expected: set[str], label: str) -> None:
    if not isinstance(record, dict) or set(record) != expected:
        raise ValueError(f"{label} fields do not match the contract")


def _timestamp(value: object, label: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{label} requires a timezone-aware timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} requires a timezone-aware timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{label} requires a timezone-aware timestamp")


def _github_https(value: object) -> None:
    if not isinstance(value, str) or len(value) > 500:
        raise ValueError("repository source_url must be a bounded GitHub HTTPS URL")
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "github.com"
        or parsed.username
        or parsed.password
        or parsed.port not in (None, 443)
    ):
        raise ValueError("repository source_url must be a bounded GitHub HTTPS URL")


def validate_three_source_pilot(pilot: dict[str, Any]) -> None:
    """Validate one Drive source, one Empirica finding, and one repo capability.

    Source text is input-only. A private source locator and its content never appear
    in the returned projection. This is advisory comparison, not authorization.
    """
    _exact_fields(
        pilot,
        {
            "pilot_id", "authority_effect", "drive_document", "empirica_finding",
            "repository_capability", "next_test",
        },
        "pilot",
    )
    if not isinstance(pilot["pilot_id"], str) or not pilot["pilot_id"].strip():
        raise ValueError("pilot_id is required")
    if pilot["authority_effect"] != "NONE":
        raise ValueError("Three-source context cannot grant authority")

    drive = pilot["drive_document"]
    _exact_fields(
        drive,
        {"source_id", "source_locator", "source_revision", "observed_at", "privacy_class"},
        "drive_document",
    )
    if not all(isinstance(drive[key], str) and drive[key].strip() for key in drive):
        raise ValueError("drive_document fields must be nonempty strings")
    if drive["privacy_class"] not in ALLOWED_PRIVACY_CLASSES:
        raise ValueError("Unsupported Drive privacy_class")
    _timestamp(drive["observed_at"], "drive_document.observed_at")

    finding = pilot["empirica_finding"]
    _exact_fields(
        finding,
        {"finding_id", "source_id", "claim_kind", "statement", "as_of", "epistemic_state"},
        "empirica_finding",
    )
    if finding["source_id"] != drive["source_id"]:
        raise ValueError("Empirica finding must reference the selected Drive source")
    if finding["claim_kind"] != THREE_SOURCE_CLAIM:
        raise ValueError("Unsupported Empirica claim_kind")
    if finding["epistemic_state"] != "OBSERVED":
        raise ValueError("Input finding must remain an OBSERVED historical claim")
    if not isinstance(finding["statement"], str) or not 1 <= len(finding["statement"]) <= 1000:
        raise ValueError("Empirica finding statement must be bounded")
    _timestamp(finding["as_of"], "empirica_finding.as_of")

    capability = pilot["repository_capability"]
    _exact_fields(
        capability,
        {
            "capability_id", "label", "source_url", "source_revision", "observed_at",
            "implementation_state", "deployment_state",
        },
        "repository_capability",
    )
    _github_https(capability["source_url"])
    if not SHA40.fullmatch(str(capability["source_revision"])):
        raise ValueError("repository source_revision must be a full commit SHA")
    _timestamp(capability["observed_at"], "repository_capability.observed_at")
    if capability["implementation_state"] not in ALLOWED_IMPLEMENTATION_STATES:
        raise ValueError("Unsupported implementation_state")
    if capability["deployment_state"] not in ALLOWED_DEPLOYMENT_STATES:
        raise ValueError("Unsupported deployment_state")
    for key in ("capability_id", "label"):
        if not isinstance(capability[key], str) or not capability[key].strip():
            raise ValueError(f"repository_capability.{key} is required")

    next_test = pilot["next_test"]
    _exact_fields(
        next_test,
        {"objective", "steps", "success_conditions", "side_effects"},
        "next_test",
    )
    if next_test["side_effects"] != "NONE":
        raise ValueError("First pilot test must be read-only")
    if not isinstance(next_test["objective"], str) or not next_test["objective"].strip():
        raise ValueError("next_test.objective is required")
    for key in ("steps", "success_conditions"):
        values = next_test[key]
        if (
            not isinstance(values, list)
            or not values
            or len(values) > 12
            or any(not isinstance(value, str) or not value.strip() for value in values)
        ):
            raise ValueError(f"next_test.{key} must be a bounded nonempty string list")


def resolve_three_source_pilot(pilot: dict[str, Any]) -> dict[str, Any]:
    """Build the three INTENT-OS context views without exposing private source text."""
    validate_three_source_pilot(pilot)
    drive = pilot["drive_document"]
    finding = pilot["empirica_finding"]
    capability = pilot["repository_capability"]

    implementation = capability["implementation_state"]
    deployment = capability["deployment_state"]
    if implementation == "MERGED" and deployment == "OBSERVED_LIVE":
        resolution = "CONTRADICTED"
    elif implementation == "MERGED":
        resolution = "SUPERSEDED_IN_PART"
    elif implementation == "NOT_STARTED":
        resolution = "SUPPORTED"
    else:
        resolution = "UNRESOLVED"

    public_source = drive["privacy_class"] == "PUBLIC_SAFE"
    private_ref = hashlib.sha256(
        f"{drive['source_id']}|{drive['source_revision']}".encode("utf-8")
    ).hexdigest()
    source_projection = {
        "source_ref": drive["source_id"] if public_source else f"PRIVATE-SOURCE-SHA256:{private_ref}",
        "source_revision": drive["source_revision"],
        "privacy_class": drive["privacy_class"],
        "source_locator": drive["source_locator"] if public_source else "REDACTED_PRIVATE_SOURCE",
        "source_content_included": False,
    }
    what_needs_proof = []
    if deployment == "UNVERIFIED":
        what_needs_proof.append({
            "claim": "Public deployment and successful human use",
            "epistemic_state": "UNVERIFIED",
        })
    elif deployment == "OBSERVED_NOT_LIVE":
        what_needs_proof.append({
            "claim": "A successful public deployment and human use",
            "epistemic_state": "CONTRADICTED",
        })

    result = {
        "pilot_id": pilot["pilot_id"],
        "resolution": resolution,
        "selected_source": source_projection,
        "empirica_finding": {
            "finding_id": finding["finding_id"],
            "claim_kind": finding["claim_kind"],
            "historical_state": finding["epistemic_state"],
            "current_state": resolution,
            "as_of": finding["as_of"],
            "statement_included": False,
        },
        "what_we_already_have": [{
            "capability_id": capability["capability_id"],
            "label": capability["label"],
            "epistemic_state": "OBSERVED",
            "implementation_state": implementation,
            "source_ref": f"{capability['source_url']}@{capability['source_revision']}",
        }],
        "what_needs_proof": what_needs_proof,
        "smallest_next_test": dict(pilot["next_test"]),
        "authority_effect": "NONE",
        "execution": "DISABLED",
    }
    canonical = json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    result["receipt_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    result["receipt_kind"] = "UNSIGNED_CONTEXT_PROJECTION_NOT_AN_ATTESTATION"
    return result


def _index(records: list[dict[str, Any]], id_key: str, label: str) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for record in records:
        node_id = str(record.get(id_key) or "").strip()
        if not node_id:
            raise ValueError(f"{label} record missing {id_key}")
        if node_id in index:
            raise ValueError(f"Duplicate {label} id: {node_id}")
        index[node_id] = record
    return index


def _require_refs(
    records: list[dict[str, Any]],
    field: str,
    target_ids: set[str],
    label: str,
) -> None:
    for record in records:
        record_id = next(
            (str(value) for key, value in record.items() if key.endswith("_id") and value),
            label,
        )
        for ref in record.get(field, []) or []:
            if str(ref) not in target_ids:
                raise ValueError(f"{record_id} references unknown {field}: {ref}")


def validate_resource_plan(plan: dict[str, Any]) -> None:
    plan_id = str(plan.get("plan_id") or "").strip()
    if not plan_id:
        raise ValueError("Resource plan missing plan_id")
    if str(plan.get("authority_effect") or "NONE").upper() != "NONE":
        raise ValueError("Resource planning cannot grant authority")

    needs = list(plan.get("needs") or [])
    capabilities = list(plan.get("capabilities") or [])
    work_packages = list(plan.get("work_packages") or [])
    resources = list(plan.get("controlled_resources") or [])
    requirements = list(plan.get("resource_requirements") or [])
    substitutions = list(plan.get("substitution_assessments") or [])

    need_idx = _index(needs, "need_id", "need")
    capability_idx = _index(capabilities, "capability_id", "capability")
    work_idx = _index(work_packages, "work_package_id", "work_package")
    resource_idx = _index(resources, "resource_id", "controlled_resource")
    requirement_idx = _index(requirements, "requirement_id", "resource_requirement")

    all_node_ids: list[str] = [
        *need_idx,
        *capability_idx,
        *work_idx,
        *resource_idx,
        *requirement_idx,
    ]
    if len(all_node_ids) != len(set(all_node_ids)):
        raise ValueError("Resource plan node IDs must be globally unique")

    _require_refs(capabilities, "satisfies_need_ids", set(need_idx), "capability")
    _require_refs(work_packages, "enables_capability_ids", set(capability_idx), "work_package")
    _require_refs(requirements, "work_package_ids", set(work_idx), "resource_requirement")
    _require_refs(requirements, "capability_ids", set(capability_idx), "resource_requirement")

    for requirement in requirements:
        activation = str(requirement.get("activation_state") or "ACTIVE").upper()
        resolution = str(requirement.get("resolution_mode") or "").upper()
        if activation not in ALLOWED_ACTIVATION_STATES:
            raise ValueError(f"Unsupported activation_state: {activation}")
        if resolution not in ALLOWED_RESOLUTION_MODES:
            raise ValueError(f"Unsupported resolution_mode: {resolution}")
        if not requirement.get("resource_types"):
            raise ValueError(f"{requirement['requirement_id']} requires resource_types")

    seen_pairs: set[tuple[str, str]] = set()
    for assessment in substitutions:
        requirement_id = str(assessment.get("requirement_id") or "")
        resource_id = str(assessment.get("controlled_resource_id") or "")
        state = str(assessment.get("status") or "").upper()
        if requirement_id not in requirement_idx:
            raise ValueError(f"Substitution references unknown requirement: {requirement_id}")
        if resource_id not in resource_idx:
            raise ValueError(f"Substitution references unknown controlled resource: {resource_id}")
        if state not in ALLOWED_SUBSTITUTION_STATES:
            raise ValueError(f"Unsupported substitution status: {state}")
        pair = (requirement_id, resource_id)
        if pair in seen_pairs:
            raise ValueError(f"Duplicate substitution assessment: {pair}")
        seen_pairs.add(pair)


def derive_requirement_status(plan: dict[str, Any], requirement: dict[str, Any]) -> str:
    activation = str(requirement.get("activation_state") or "ACTIVE").upper()
    if activation == "INACTIVE":
        return "INACTIVE"
    if activation == "CONDITIONAL":
        return "CONDITIONAL"

    requirement_id = str(requirement["requirement_id"])
    assessments = [
        assessment
        for assessment in plan.get("substitution_assessments", []) or []
        if str(assessment.get("requirement_id") or "") == requirement_id
    ]
    states = {str(assessment.get("status") or "").upper() for assessment in assessments}

    if "ADEQUATE" in states:
        return "SATISFIED"
    if "PARTIAL" in states:
        return "PARTIAL"
    if "UNKNOWN" in states or not states:
        return "UNKNOWN"

    resolution = str(requirement.get("resolution_mode") or "").upper()
    if states == {"INADEQUATE"}:
        if resolution in {"ACQUIRE_EXTERNAL", "HYBRID"}:
            return "CONFIRMED"
        if resolution == "COMPOSE_INTERNAL":
            return "INTERNAL_COMPOSITION_GAP"

    return "UNKNOWN"


def resolve_resource_plan(plan: dict[str, Any]) -> dict[str, Any]:
    validate_resource_plan(plan)
    requirements = []
    counts: dict[str, int] = {}
    for requirement in plan.get("resource_requirements", []) or []:
        row = dict(requirement)
        row["gap_status"] = derive_requirement_status(plan, requirement)
        counts[row["gap_status"]] = counts.get(row["gap_status"], 0) + 1
        requirements.append(row)

    return {
        "plan_id": plan["plan_id"],
        "authority_effect": "NONE",
        "needs": plan.get("needs", []),
        "capabilities": plan.get("capabilities", []),
        "work_packages": plan.get("work_packages", []),
        "controlled_resources": plan.get("controlled_resources", []),
        "resource_requirements": requirements,
        "substitution_assessments": plan.get("substitution_assessments", []),
        "gap_counts": counts,
    }


def miner_requirements_from_plan(plan: dict[str, Any]) -> list[dict[str, Any]]:
    resolved = resolve_resource_plan(plan)
    out: list[dict[str, Any]] = []
    for requirement in resolved["resource_requirements"]:
        if not bool(requirement.get("mine_external", False)):
            continue
        gap_status = str(requirement["gap_status"])
        if gap_status in {"SATISFIED", "INACTIVE", "INTERNAL_COMPOSITION_GAP"}:
            continue
        out.append(
            {
                "requirement_id": requirement["requirement_id"],
                "gap_status": gap_status,
                "label": requirement.get("label") or requirement["requirement_id"],
                "objective": requirement.get("objective", ""),
                "resource_types": requirement.get("resource_types", []),
                "affordances": requirement.get("affordances", []),
                "signals": requirement.get("signals", []),
                "satisfied_when": requirement.get("satisfied_when", ""),
                "authority_effect": "NONE",
                "source_plan_id": plan["plan_id"],
            }
        )
    return out
