from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

ALLOWED_ACTIVATION_STATES = {"ACTIVE", "CONDITIONAL", "INACTIVE"}
ALLOWED_RESOLUTION_MODES = {"COMPOSE_INTERNAL", "ACQUIRE_EXTERNAL", "HYBRID"}
ALLOWED_SUBSTITUTION_STATES = {"ADEQUATE", "PARTIAL", "INADEQUATE", "UNKNOWN"}
PLAN_SCHEMA = "humanaios.resource-plan.v1"
ALLOWED_COMBINATION_MODES = {"ALTERNATIVES", "ALL_REQUIRED"}


def _records(value: Any, label: str) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise ValueError(f"{label} must be a list of objects")
    return value


def _no_authority(record: dict[str, Any]) -> None:
    if "authority_effect" in record and record["authority_effect"] != "NONE":
        raise ValueError("Resource planning cannot grant authority")


def _combination(requirement: dict[str, Any]) -> str:
    return requirement.get("combination_mode", "ALTERNATIVES")


def load_resource_plan(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Resource plan must be a JSON object")
    validate_resource_plan(data)
    return data


def _index(records: list[dict[str, Any]], id_key: str, label: str) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for record in records:
        node_id = record.get(id_key)
        if not isinstance(node_id, str) or not node_id or node_id != node_id.strip():
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
        refs = record.get(field, [])
        if not isinstance(refs, list) or any(not isinstance(ref, str) for ref in refs):
            raise ValueError(f"{record_id} requires a list of {field}")
        if len(refs) != len(set(refs)):
            raise ValueError(f"{record_id} has duplicate {field}")
        for ref in refs:
            if str(ref) not in target_ids:
                raise ValueError(f"{record_id} references unknown {field}: {ref}")


def validate_resource_plan(plan: dict[str, Any]) -> None:
    if not isinstance(plan, dict):
        raise ValueError("Resource plan must be a JSON object")
    plan_id = str(plan.get("plan_id") or "").strip()
    if not plan_id:
        raise ValueError("Resource plan missing plan_id")
    _no_authority(plan)
    if "schema" in plan and plan["schema"] != PLAN_SCHEMA:
        raise ValueError("Unsupported resource plan schema")
    if plan.get("schema") == PLAN_SCHEMA:
        if not isinstance(plan.get("resource_requirements"), list):
            raise ValueError("Versioned plan requires resource_requirements")
        for field in ("needs", "capabilities", "work_packages", "controlled_resources", "substitution_assessments"):
            if field in plan and not isinstance(plan[field], list):
                raise ValueError(f"{field} must be a list")

    needs = _records(plan.get("needs"), "needs")
    capabilities = _records(plan.get("capabilities"), "capabilities")
    work_packages = _records(plan.get("work_packages"), "work_packages")
    resources = _records(plan.get("controlled_resources"), "controlled_resources")
    requirements = _records(plan.get("resource_requirements"), "resource_requirements")
    substitutions = _records(plan.get("substitution_assessments"), "substitution_assessments")
    for record in [*needs, *capabilities, *work_packages, *resources, *requirements, *substitutions]:
        _no_authority(record)

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

    components: dict[str, str] = {}
    for requirement in requirements:
        activation = str(requirement.get("activation_state") or "ACTIVE").upper()
        resolution = str(requirement.get("resolution_mode") or "").upper()
        if activation not in ALLOWED_ACTIVATION_STATES:
            raise ValueError(f"Unsupported activation_state: {activation}")
        if resolution not in ALLOWED_RESOLUTION_MODES:
            raise ValueError(f"Unsupported resolution_mode: {resolution}")
        if not requirement.get("resource_types"):
            raise ValueError(f"{requirement['requirement_id']} requires resource_types")
        if plan.get("schema") == PLAN_SCHEMA:
            if (requirement.get("resolution_mode") not in ("COMPOSE_INTERNAL", "ACQUIRE_EXTERNAL", "HYBRID")
                    or requirement.get("activation_state", "ACTIVE") not in ("ACTIVE", "CONDITIONAL", "INACTIVE")):
                raise ValueError("Versioned planning states must use canonical enums")
            if "mine_external" in requirement and type(requirement["mine_external"]) is not bool:
                raise ValueError("mine_external must be a boolean")
        types = requirement["resource_types"]
        if not isinstance(types, list) or any(not isinstance(t, str) or not t.strip() for t in types):
            raise ValueError("resource_types must be a non-empty list of strings")
        if ("combination_mode" in requirement or "required_components" in requirement) and plan.get("schema") != PLAN_SCHEMA:
            raise ValueError("Combination semantics require an explicit versioned plan schema")
        mode = _combination(requirement)
        if mode not in ("ALTERNATIVES", "ALL_REQUIRED"):
            raise ValueError("Unsupported combination_mode")
        if mode == "ALTERNATIVES":
            if "required_components" in requirement:
                raise ValueError("ALTERNATIVES cannot declare required_components")
            continue
        required = _records(requirement.get("required_components"), "required_components")
        if not required:
            raise ValueError("ALL_REQUIRED needs non-empty required_components")
        for component in required:
            _no_authority(component)
            if set(component) - {"component_id", "label", "authority_effect"}:
                raise ValueError("Unsupported required component fields")
            if "label" in component and not isinstance(component["label"], str):
                raise ValueError("Component label must be a string")
            cid = component.get("component_id")
            if not isinstance(cid, str) or not cid or cid != cid.strip():
                raise ValueError("Required component missing canonical component_id")
            if cid in components or cid in all_node_ids:
                raise ValueError("Duplicate or conflicting component_id")
            components[cid] = requirement["requirement_id"]

    seen_pairs: set[tuple[str, str, str | None]] = set()
    for assessment in substitutions:
        requirement_id = assessment.get("requirement_id")
        resource_id = assessment.get("controlled_resource_id")
        if not isinstance(requirement_id, str) or not isinstance(resource_id, str):
            raise ValueError("Substitution requires string requirement/resource references")
        state = str(assessment.get("status") or "").upper()
        if requirement_id not in requirement_idx:
            raise ValueError(f"Substitution references unknown requirement: {requirement_id}")
        if resource_id not in resource_idx:
            raise ValueError(f"Substitution references unknown controlled resource: {resource_id}")
        if state not in ALLOWED_SUBSTITUTION_STATES:
            raise ValueError(f"Unsupported substitution status: {state}")
        if plan.get("schema") == PLAN_SCHEMA and assessment["status"] != state:
            raise ValueError("Versioned substitution status must use canonical enum")
        cid = assessment.get("component_id")
        if _combination(requirement_idx[requirement_id]) == "ALL_REQUIRED":
            if not isinstance(cid, str) or components.get(cid) != requirement_id:
                raise ValueError("Missing, unknown or conflicting required component reference")
        elif "component_id" in assessment:
            raise ValueError("ALTERNATIVES assessment cannot reference a component")
        pair = (requirement_id, resource_id, cid)
        if pair in seen_pairs:
            raise ValueError(f"Duplicate substitution assessment: {pair}")
        seen_pairs.add(pair)


def derive_requirement_status(plan: dict[str, Any], requirement: dict[str, Any]) -> str:
    # This public entry point must not bypass version/reference validation.
    validate_resource_plan(plan)
    if requirement not in plan.get("resource_requirements", []):
        raise ValueError("Requirement does not belong to resource plan")
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
    if _combination(requirement) == "ALL_REQUIRED":
        # Resources within one component are alternatives; components are cumulative.
        component_states = []
        for component in requirement["required_components"]:
            states = {str(a["status"]).upper() for a in assessments
                      if a["component_id"] == component["component_id"]}
            component_states.append(_alternative_status(states))
        if "INADEQUATE" in component_states:
            return _gap_status(requirement)
        if "UNKNOWN" in component_states:
            return "UNKNOWN"
        if "PARTIAL" in component_states:
            return "PARTIAL"
        return "SATISFIED"
    state = _alternative_status({str(a["status"]).upper() for a in assessments})
    if state == "INADEQUATE":
        return _gap_status(requirement)
    return "SATISFIED" if state == "ADEQUATE" else state


def _alternative_status(states: set[str]) -> str:

    if "ADEQUATE" in states:
        return "ADEQUATE"
    if "PARTIAL" in states:
        return "PARTIAL"
    if "UNKNOWN" in states or not states:
        return "UNKNOWN"

    return "INADEQUATE"


def _gap_status(requirement: dict[str, Any]) -> str:
    resolution = str(requirement["resolution_mode"]).upper()
    return "INTERNAL_COMPOSITION_GAP" if resolution == "COMPOSE_INTERNAL" else "CONFIRMED"


def resolve_resource_plan(plan: dict[str, Any]) -> dict[str, Any]:
    validate_resource_plan(plan)
    requirements = []
    counts: dict[str, int] = {}
    for requirement in plan.get("resource_requirements", []) or []:
        row = deepcopy(requirement)
        row["gap_status"] = derive_requirement_status(plan, requirement)
        counts[row["gap_status"]] = counts.get(row["gap_status"], 0) + 1
        requirements.append(row)

    return deepcopy({
        "plan_id": plan["plan_id"],
        "authority_effect": "NONE",
        "needs": plan.get("needs", []),
        "capabilities": plan.get("capabilities", []),
        "work_packages": plan.get("work_packages", []),
        "controlled_resources": plan.get("controlled_resources", []),
        "resource_requirements": requirements,
        "substitution_assessments": plan.get("substitution_assessments", []),
        "gap_counts": counts,
        **({"schema": plan["schema"]} if "schema" in plan else {}),
    })


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
