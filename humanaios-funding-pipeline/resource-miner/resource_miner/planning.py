from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ALLOWED_ACTIVATION_STATES = {"ACTIVE", "CONDITIONAL", "INACTIVE"}
ALLOWED_RESOLUTION_MODES = {"COMPOSE_INTERNAL", "ACQUIRE_EXTERNAL", "HYBRID"}
ALLOWED_SUBSTITUTION_STATES = {"ADEQUATE", "PARTIAL", "INADEQUATE", "UNKNOWN"}


def load_resource_plan(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Resource plan must be a JSON object")
    validate_resource_plan(data)
    return data


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
