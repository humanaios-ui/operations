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
            "crb_nodes": len(node_ids),
            "workflows": len(wf_ids),
        },
    }


def build_projection() -> dict[str, Any]:
    capability = load_json("crb/capability_graph.json")
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
