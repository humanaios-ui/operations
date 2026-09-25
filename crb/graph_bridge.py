"""CRB graph bridge.

Builds a read-only projection across capability, workflow, and selected existing
HumanAIOS system nodes. It does not mutate canonical graphs.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: str) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _resolve_existing_ref(ref: str, system: dict[str, Any]) -> tuple[bool, str]:
    if ":" not in ref:
        return (ROOT / ref).exists(), ref
    file_name, node_id = ref.split(":", 1)
    if file_name != "system_graph.json":
        return False, ref
    return node_id in (system.get("nodes") or {}), ref


def validate() -> dict[str, Any]:
    capability = load_json("crb/capability_graph.json")
    morphogenesis = load_json("crb/morphogenesis.json")
    workflows = load_json("crb/workflows.json")
    system = load_json("system_graph.json")

    errors: list[str] = []
    warnings: list[str] = []

    stages = capability.get("stages") or []
    stage_ids = [s.get("id") for s in stages]
    if stage_ids != [f"CAP-{n:02d}" for n in range(1, 12)]:
        errors.append("capability stages must be exactly CAP-01..CAP-11 in order")

    crb_nodes = capability.get("crb_nodes") or []
    node_ids = {n.get("id") for n in crb_nodes}
    if len(node_ids) != len(crb_nodes):
        errors.append("duplicate CRB node id")

    for edge in capability.get("edges") or []:
        if edge.get("from") not in node_ids or edge.get("to") not in node_ids:
            errors.append(f"dangling CRB edge: {edge}")

    for stage in stages:
        for ref in stage.get("existing_refs") or []:
            ok, label = _resolve_existing_ref(ref, system)
            if not ok:
                warnings.append(f"unresolved existing_ref: {label}")

    change_hierarchy = morphogenesis.get("change_hierarchy") or []
    hierarchy_by_id = {entry.get("id"): entry.get("level") for entry in change_hierarchy}
    expected_hierarchy = [(f"CHANGE-L{level}", level) for level in range(5)]
    if any(hierarchy_by_id.get(entry_id) != level for entry_id, level in expected_hierarchy):
        errors.append("change hierarchy must include CHANGE-L0..CHANGE-L4 with matching levels")
    hierarchy_positions = {
        entry.get("id"): index for index, entry in enumerate(change_hierarchy)
    }
    if any(
        hierarchy_positions.get(left_id, -1) >= hierarchy_positions.get(right_id, -1)
        for (left_id, _), (right_id, _) in zip(expected_hierarchy, expected_hierarchy[1:])
    ):
        errors.append("change hierarchy baseline must remain ordered from CHANGE-L0 to CHANGE-L4")

    expected_event_ids = [
        "MORPHOGENIC_SIGNAL",
        "GRAPH_DELTA_CANDIDATE",
        "GRAPH_DELTA_REVIEW",
        "GRAPH_DELTA_AUTHORIZATION",
        "GRAPH_DELTA_APPLIED",
        "GRAPH_DELTA_REVERTED",
    ]
    event_types = morphogenesis.get("event_types") or []
    event_ids = [entry.get("id") for entry in event_types]
    if any(event_id not in event_ids for event_id in expected_event_ids):
        errors.append("graph delta event types must include the governed review lifecycle")
    else:
        event_positions = {event_id: event_ids.index(event_id) for event_id in expected_event_ids}
        if any(
            event_positions[left_id] >= event_positions[right_id]
            for left_id, right_id in zip(expected_event_ids, expected_event_ids[1:])
        ):
            errors.append("graph delta event types must preserve the governed review lifecycle order")

    projection_types = morphogenesis.get("projection_types") or []
    projection_ids = {entry.get("id") for entry in projection_types}
    for entry in projection_types:
        specializes = entry.get("specializes")
        if specializes and specializes not in projection_ids:
            errors.append(f"unknown projection specialization: {specializes}")

    required_review_fields = {
        "delta_id",
        "target_layers",
        "current_path",
        "proposed_delta",
        "evidence_refs",
        "authority_path",
        "capability_reachability_diff",
        "rollback_plan",
        "falsifier",
    }
    review_fields = set(morphogenesis.get("review_requirements") or [])
    if review_fields != required_review_fields:
        errors.append("graph delta review requirements must match the expected contract")

    change_level_ids = {entry_id for entry_id, _ in expected_hierarchy}
    morph_node_ids = node_ids | change_level_ids | set(event_ids) | projection_ids
    for edge in morphogenesis.get("edges") or []:
        if edge.get("from") not in morph_node_ids or edge.get("to") not in morph_node_ids:
            errors.append(f"dangling morphogenesis edge: {edge}")

    wf_ids: set[str] = set()
    for workflow in workflows.get("workflows") or []:
        wid = workflow.get("id")
        if wid in wf_ids:
            errors.append(f"duplicate workflow id: {wid}")
        wf_ids.add(wid)
        caps = workflow.get("capability_stages") or []
        if not caps:
            errors.append(f"{wid}: no capability_stages")
        for cap in caps:
            if cap not in stage_ids:
                errors.append(f"{wid}: unknown capability stage {cap}")

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "counts": {
            "capability_stages": len(stage_ids),
            "change_levels": len(change_hierarchy),
            "crb_nodes": len(node_ids),
            "graph_delta_events": len(event_ids),
            "projection_types": len(projection_ids),
            "workflows": len(wf_ids),
        },
    }


def build_projection() -> dict[str, Any]:
    capability = load_json("crb/capability_graph.json")
    morphogenesis = load_json("crb/morphogenesis.json")
    workflows = load_json("crb/workflows.json")
    system = load_json("system_graph.json")

    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, str]] = []

    for stage in capability["stages"]:
        nodes[stage["id"]] = {
            "id": stage["id"], "type": "capability_stage", "label": stage["label"]
        }
        for ref in stage.get("existing_refs") or []:
            if ref.startswith("system_graph.json:"):
                sid = ref.split(":", 1)[1]
                if sid in system.get("nodes", {}):
                    nid = f"SYS-{sid}"
                    nodes[nid] = {
                        "id": nid,
                        "type": "existing_system_node",
                        "label": system["nodes"][sid].get("name", sid),
                        "source": ref,
                    }
                    edges.append({
                        "from": stage["id"], "to": nid, "rel": "realized_or_observed_by"
                    })

    for node in capability["crb_nodes"]:
        nodes[node["id"]] = dict(node)

    for edge in capability["edges"]:
        edges.append(dict(edge))

    previous_level_id = None
    for entry in morphogenesis.get("change_hierarchy") or []:
        nodes[entry["id"]] = {
            "id": entry["id"],
            "type": "change_level",
            "label": entry["label"],
            "level": entry["level"],
            "name": entry["name"],
            "example": entry["example"],
        }
        if previous_level_id is not None:
            edges.append(
                {"from": previous_level_id, "to": entry["id"], "rel": "escalates_to"}
            )
        previous_level_id = entry["id"]

    for entry in morphogenesis.get("event_types") or []:
        nodes[entry["id"]] = {
            "id": entry["id"],
            "type": entry["type"],
            "label": entry["label"],
            "description": entry["description"],
        }

    for entry in morphogenesis.get("projection_types") or []:
        node = {
            "id": entry["id"],
            "type": entry["type"],
            "label": entry["label"],
        }
        if "definition" in entry:
            node["definition"] = entry["definition"]
        if "specializes" in entry:
            node["specializes"] = entry["specializes"]
        if "minimum_fields" in entry:
            node["minimum_fields"] = entry["minimum_fields"]
        nodes[entry["id"]] = node

    for edge in morphogenesis.get("edges") or []:
        edges.append(dict(edge))

    for workflow in workflows["workflows"]:
        wid = workflow["id"]
        nodes[wid] = {"id": wid, "type": "workflow", "label": workflow["name"]}
        for cap in workflow.get("capability_stages") or []:
            edges.append({"from": cap, "to": wid, "rel": "required_by"})

    return {
        "graph_id": "CRB-MULTIPLEX-PROJECTION-0.1",
        "status": "DERIVED_NON_CANONICAL",
        "nodes": list(nodes.values()),
        "edges": edges,
        "validation": validate(),
    }


def main() -> int:
    result = build_projection()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["validation"]["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
