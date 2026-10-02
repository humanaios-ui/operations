#!/usr/bin/env python3
"""Build a provenance-bearing longitudinal graph from chat synthesis + evidence overlay."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

INVARIANTS = [
    "GRAPH_IS_NOT_AUTHORITY",
    "CHAT_MEMORY_IS_NOT_INDEPENDENT_EVIDENCE",
    "REFERENCE_IS_NOT_EVIDENCE",
    "SOURCE_BINDING_IS_NOT_CLAIM_PROOF",
    "CLAIM_IS_NOT_IMPLEMENTATION",
    "IMPLEMENTATION_IS_NOT_TEST",
    "TEST_IS_NOT_OBSERVED_OUTCOME",
    "INFERENCE_IS_NOT_OBSERVATION",
    "INFERENCE_IS_NOT_WARRANT",
    "CALIBRATION_IS_NOT_WARRANT",
    "WARRANT_IS_NOT_AUTHORIZATION",
    "AUTHORIZATION_IS_NOT_EXECUTION",
    "CORRECTIONS_APPEND_AND_SUPERSEDE;THEY_DO_NOT_ERASE_HISTORY",
    "NO_AUTONOMOUS_GRAPH_MUTATION",
    "NO_AUTONOMOUS_SELF_AUTHORIZATION",
]

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sid(meta: dict, number: int) -> str:
    return f"source:github:{meta['kind']}:{number}"

def build(source: dict, overlay: dict, predecessor_hash: str) -> dict:
    items = {int(k): v for k, v in overlay["work_items"].items()}
    bindings = {k: [int(x) for x in v] for k, v in overlay["node_bindings"].items()}
    observed_on = overlay["observed_on"]

    sources = [{
        "id": "source:chat-synthesis:predecessor",
        "type": "derived_artifact",
        "locator": "chat_graph/source/humanaios_cross_chat_knowledge_graph.v0.1.json",
        "sha256": predecessor_hash,
        "evidence_class": "CHAT_DERIVED",
        "authority_effect": "NONE",
    }]
    repo = overlay.get("repository_snapshot")
    if repo:
        sources.append({
            "id": "source:repo-main:observation",
            "type": "github_ref_observation",
            "locator": f"https://github.com/{repo['repository']}/tree/{repo['ref']}",
            "evidence_class": "SOURCE_OBSERVED",
            "authority_effect": "NONE",
            "observed": repo,
        })
    for number, meta in sorted(items.items()):
        kind_path = "pull" if meta["kind"] == "pull_request" else "issues"
        sources.append({
            "id": sid(meta, number),
            "type": "github_work_item_observation",
            "locator": f"https://github.com/humanaios-ui/operations/{kind_path}/{number}",
            "evidence_class": "SOURCE_OBSERVED",
            "authority_effect": "NONE",
            "observed": {"number": number, **meta},
        })
    if overlay.get("planning_surface"):
        sources.append({
            "id": "source:planning:issue-677",
            "type": "github_issue",
            "locator": overlay["planning_surface"],
            "evidence_class": "PLANNING_SURFACE",
            "authority_effect": "NONE",
        })

    entities, assertions, events = [], [], []
    for idx, node in enumerate(source["nodes"], 1):
        nums = bindings.get(node["id"], [])
        refs = ["source:chat-synthesis:predecessor"] + [sid(items[n], n) for n in nums]
        entity = {
            "id": node["id"],
            "type": "semantic_entity",
            "semantic_type": node.get("type"),
            "label": node.get("label"),
            "domain": node.get("domain"),
            "hydration_state": "SOURCE_OBSERVED" if nums else "CHAT_DERIVED",
            "source_refs": refs,
            "original": node,
        }
        if nums:
            entity["observed_work_items"] = [{"number": n, **items[n]} for n in nums]
        entities.append(entity)
        assertions.append({
            "id": f"assertion:node:{idx:04d}",
            "subject": node["id"],
            "predicate": "CHAT_SYNTHESIZED_AS",
            "object": {k: node.get(k) for k in ("label","type","domain","status","description")},
            "epistemic_state": "CHAT_DERIVED",
            "source_refs": ["source:chat-synthesis:predecessor"],
            "authority_effect": "NONE",
        })
        for n in nums:
            assertions.append({
                "id": f"assertion:github:{node['id']}:{n}",
                "subject": node["id"],
                "predicate": "HAS_OBSERVED_WORK_ITEM_METADATA",
                "object": {"number": n, **items[n]},
                "epistemic_state": "OBSERVED",
                "source_refs": [sid(items[n], n)],
                "authority_effect": "NONE",
            })
            events.append({
                "id": f"event:hydrate:{node['id']}:{n}:{observed_on}",
                "type": "hydration_observation",
                "entity_ref": node["id"],
                "source_ref": sid(items[n], n),
                "observed_on": observed_on,
                "result": "SOURCE_OBSERVED",
                "authority_effect": "NONE",
            })

    for idx, edge in enumerate(source["edges"], 1):
        assertions.append({
            "id": f"assertion:edge:{idx:04d}",
            "subject": edge["source"],
            "predicate": edge["relation"],
            "object_ref": edge["target"],
            "description": edge.get("description", ""),
            "epistemic_state": "CHAT_DERIVED",
            "source_refs": ["source:chat-synthesis:predecessor"],
            "authority_effect": "NONE",
            "original_status": edge.get("status"),
        })

    for idx, correction in enumerate(overlay.get("corrections", []), 1):
        number = int(correction["work_item"])
        events.append({
            "id": f"event:correction:{idx:03d}:{observed_on}",
            "type": "correction",
            "observed_on": observed_on,
            "authority_effect": "NONE",
            "preserve_prior": True,
            "source_ref": sid(items[number], number),
            **{k: v for k, v in correction.items() if k != "work_item"},
        })
    if overlay.get("planning_surface"):
        events.append({
            "id": f"event:plan:issue-677:{observed_on}",
            "type": "planning_binding",
            "source_ref": "source:planning:issue-677",
            "observed_on": observed_on,
            "result": "BOUND_AS_PLANNING_SURFACE",
            "authority_effect": "NONE",
        })

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "graph_id": "humanaios-cross-chat-longitudinal-evidence-graph",
        "version": "0.2.0",
        "status": "DERIVED_NON_CANONICAL",
        "generated_date": observed_on,
        "predecessor": {
            "graph_name": source.get("graph_name"),
            "sha256": predecessor_hash,
            "nodes": len(source["nodes"]),
            "edges": len(source["edges"]),
            "status": "SYNTHESIZED_SEMANTIC_INDEX",
        },
        "planning_surface": overlay.get("planning_surface"),
        "invariants": INVARIANTS,
        "epistemic_state_enum": ["CHAT_DERIVED","SOURCE_LOCATED","SOURCE_OBSERVED","CROSS_VERIFIED","CONTESTED","SUPERSEDED"],
        "hydration_state_enum": ["CHAT_DERIVED","SOURCE_LOCATED","SOURCE_OBSERVED","CROSS_VERIFIED","CONTESTED"],
        "time_model": {
            "record_time": "when the graph learned/recorded an observation",
            "valid_time": "when the underlying fact was true when known",
            "policy": "Append observations/corrections; never silently overwrite prior state.",
        },
        "sources": sources,
        "entities": entities,
        "assertions": assertions,
        "events": events,
        "views": [
            {"id":"semantic","description":"Original conceptual structure with epistemic state visible."},
            {"id":"provenance","description":"Source bindings, hashes and derivation lineage."},
            {"id":"longitudinal","description":"Append-only observations, corrections and supersession."},
            {"id":"unhydrated","description":"CHAT_DERIVED entities/assertions lacking primary evidence."},
            {"id":"conflict","description":"Corrected or competing claims without forced resolution."},
        ],
    }

def validate(graph: dict) -> list[str]:
    errors = []
    sids = {x["id"] for x in graph["sources"]}
    eids = {x["id"] for x in graph["entities"]}
    aids = {x["id"] for x in graph["assertions"]}
    vids = {x["id"] for x in graph["events"]}
    if len(sids) != len(graph["sources"]): errors.append("duplicate source ids")
    if len(eids) != len(graph["entities"]): errors.append("duplicate entity ids")
    if len(aids) != len(graph["assertions"]): errors.append("duplicate assertion ids")
    if len(vids) != len(graph["events"]): errors.append("duplicate event ids")
    for a in graph["assertions"]:
        if a["subject"] not in eids: errors.append(f"missing subject {a['subject']}")
        if a.get("object_ref") and a["object_ref"] not in eids: errors.append(f"missing object {a['object_ref']}")
        for ref in a.get("source_refs", []):
            if ref not in sids: errors.append(f"missing source {ref}")
    for event in graph["events"]:
        if event.get("entity_ref") and event["entity_ref"] not in eids: errors.append(f"missing event entity {event['entity_ref']}")
        if event.get("source_ref") and event["source_ref"] not in sids: errors.append(f"missing event source {event['source_ref']}")
    return errors

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="chat_graph/source/humanaios_cross_chat_knowledge_graph.v0.1.json")
    ap.add_argument("--evidence", default="chat_graph/evidence/github_hydration_2026-10-02.json")
    ap.add_argument("--out", default="chat_graph/generated/humanaios_chat_longitudinal_graph.v0.2.json")
    ap.add_argument("--receipt", default="chat_graph/generated/humanaios_chat_longitudinal_graph.receipt.json")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    raw = Path(args.source).read_bytes()
    source = json.loads(raw)
    overlay = json.loads(Path(args.evidence).read_text())
    graph = build(source, overlay, sha256(raw))
    errors = validate(graph)
    if errors:
        raise SystemExit("\n".join(errors))
    if args.check:
        print(f"PASS entities={len(graph['entities'])} assertions={len(graph['assertions'])} sources={len(graph['sources'])} events={len(graph['events'])}")
        return 0
    payload = (json.dumps(graph, indent=2) + "\n").encode()
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True); out.write_bytes(payload)
    receipt = {
        "graph_id": graph["graph_id"], "version": graph["version"],
        "source_sha256": graph["predecessor"]["sha256"], "output_sha256": sha256(payload),
        "entity_count": len(graph["entities"]), "assertion_count": len(graph["assertions"]),
        "source_count": len(graph["sources"]), "event_count": len(graph["events"]),
        "hydrated_entity_count": sum(x["hydration_state"] != "CHAT_DERIVED" for x in graph["entities"]),
        "validation": "PASS",
    }
    rp = Path(args.receipt); rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
