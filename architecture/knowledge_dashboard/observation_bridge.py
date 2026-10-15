#!/usr/bin/env python3
"""Read-only dashboard bridge: RKG #630 + Codebase Atlas #835 + timeline #841.

Builder v1.7 compliant - diagnostic_tool
HumanAIOS - REPOSITORY-KNOWLEDGE-DASHBOARD-PROJECTION-01
Every source keeps its own namespace, head pin and evidence status.
No imported source can create approval, admission, or merge authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

TOOL_NAME = "knowledge_dashboard_projection"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "diagnostic_tool"
TOOL_ZONE = 1
REPO = "humanaios-ui/operations"
_SHA = re.compile(r"^[a-f0-9]{40}$")

def _read(path: str) -> dict:
    p = Path(path)
    if not p.is_file() or p.stat().st_size > 55_000_000:
        raise ValueError("missing or oversized source")
    obj = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("source root must be object")
    return obj

def project(rkg: dict, atlas: dict, timeline: dict) -> dict:
    """Create review-only edges; never promote inferred or historical claims."""
    src = rkg.get("source") or {}
    a_head, r_head = atlas.get("head_sha"), src.get("head_commit")
    if (rkg.get("authority_effect") != "NONE"
            or rkg.get("graph_kind") != "DERIVED_READ_MODEL"
            or rkg.get("validation", {}).get("valid") is not True
            or src.get("repository") != REPO or not _SHA.fullmatch(str(r_head))):
        raise ValueError("RKG source is not a validated pinned read model")
    if (atlas.get("authority_effect") != "NONE"
            or atlas.get("merge_authority") is not False
            or atlas.get("repository") != REPO
            or not _SHA.fullmatch(str(a_head))):
        raise ValueError("Atlas source violates repository or authority boundary")
    if not isinstance(timeline.get("nodes"), list) or not isinstance(timeline.get("edges"), list):
        raise ValueError("timeline schema invalid")
    nodes, edges, ids, path_nodes = [], [], set(), {}
    def node(id_, kind, name, provenance):
        if id_ in ids:
            raise ValueError("duplicate node")
        ids.add(id_)
        nodes.append({"id": id_, "kind": kind, "label": str(name)[:256],
                      "authority_effect": "NONE", "provenance": provenance})
    def link(start, end, relation, source, standing="SOURCE_DECLARED"):
        if start not in ids or end not in ids:
            raise ValueError("dangling source edge")
        edges.append({"from": start, "to": end, "relation": relation,
                      "source": source, "standing": standing, "authority_effect": "NONE"})
    for x in rkg.get("nodes", []):
        key = "rkg:" + x["id"]
        node(key, "RKG_" + x.get("type", "node"), x.get("label", x["id"]),
             {"source": "#630", "records": x.get("provenance", [])[:3], "head": r_head})
        if x["id"].startswith("artifact:"):
            path_nodes[x["id"][9:]] = key
    for x in rkg.get("edges", []):
        link("rkg:" + x["from"], "rkg:" + x["to"], x.get("relation", "SOURCE_EDGE"),
             "#630", x.get("evidence_state", "CLAIMED"))
    atlas_ids = set()
    for x in atlas.get("nodes", []):
        aid = x["id"]
        atlas_ids.add(aid)
        node("atlas:" + aid, "ATLAS_COMPONENT", x.get("label", aid),
             {"source": "#835", "head": a_head, "file_count": x.get("file_count", 0)})
    for x in atlas.get("edges", []):
        link("atlas:" + x["source"], "atlas:" + x["target"],
             "ATLAS_" + x.get("kind", "REFERENCE"), "#835", "STATIC_SOURCE_ASSOCIATION")
        for witness in x.get("evidence", []):
            path = witness.get("source")
            # Never match by similar labels, guessed filenames, or PR comments.
            if path in path_nodes:
                link("atlas:" + x["source"], path_nodes[path], "EXACT_PATH_WITNESS",
                     "#835", "STATIC_SOURCE_ASSOCIATION")
    for x in timeline["nodes"]:
        nid = "time:" + x["id"]
        status = x.get("date_source", "unknown")
        node(nid, "TIMELINE_OBSERVATION", x.get("name", x["id"]),
             {"source": "#841", "source_head_abbrev": timeline.get("head"),
              "first_seen": x.get("first_seen"), "last_changed": x.get("last_changed"),
              "date_source": status, "files": x.get("files", [])})
        for path in x.get("files", []):
            if path in path_nodes:
                link(nid, path_nodes[path], "HISTORICAL_EXACT_PATH_REFERENCE",
                     "#841", "GIT_DATE_OBSERVATION" if status == "git" else "FALLBACK_DATE")
    for x in timeline["edges"]:
        link("time:" + x["source"], "time:" + x["target"],
             "TIMELINE_" + x.get("edge_type", "SOURCE_EDGE"),
             "#841", "HISTORICAL_DECLARATION")
    nodes.sort(key=lambda x: x["id"])
    edges.sort(key=lambda x: (x["from"], x["to"], x["relation"], x["source"]))
    result = {"schema": "humanaios.dashboard-projection.v0.1",
              "graph_kind": "DERIVED_NON_AUTHORITATIVE_PROJECTION",
              "authority_effect": "NONE", "can_authorize": False,
              "can_execute": False, "merge_authority": False,
              "sources": {"rkg": {"head": r_head, "status": "VALIDATED_READ_MODEL"},
                          "atlas": {"head": a_head,
                                    "status": "EXACT_HEAD" if r_head == a_head
                                    else "DIFFERENT_HEAD_NO_CONVERGENCE_CLAIM"},
                          "timeline": {"head_abbrev": timeline.get("head"),
                                       "status": "HISTORICAL_DRAFT_NOT_AUTHORITY"}},
              "nodes": nodes, "edges": edges}
    return result

def smoke_test() -> None:
    sha = "a" * 40
    rkg = {"authority_effect": "NONE", "graph_kind": "DERIVED_READ_MODEL",
           "source": {"repository": REPO, "head_commit": sha},
           "validation": {"valid": True},
           "nodes": [{"id": "artifact:test.py", "type": "artifact", "label": "test.py"}],
           "edges": []}
    atlas = {"authority_effect": "NONE", "merge_authority": False,
             "repository": REPO, "head_sha": sha,
             "nodes": [{"id": "a", "label": "A"}, {"id": "b", "label": "B"}],
             "edges": [{"source": "a", "target": "b", "kind": "python_import",
                        "evidence": [{"source": "test.py", "target": "test.py", "line": 1}]}]}
    timeline = {"head": sha[:8], "nodes": [{"id": "T", "name": "T",
                 "first_seen": "2026-09-01", "files": ["test.py"],
                 "date_source": "fallback"}], "edges": []}
    out = project(rkg, atlas, timeline)
    assert out["authority_effect"] == "NONE" and out["merge_authority"] is False
    assert any(e["relation"] == "EXACT_PATH_WITNESS" for e in out["edges"])
    assert any(e["standing"] == "FALLBACK_DATE" for e in out["edges"])
    atlas["authority_effect"] = "Z2"
    try:
        project(rkg, atlas, timeline)
    except ValueError:
        pass
    else:
        raise AssertionError("untrusted Atlas incorrectly accepted")

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rkg")
    p.add_argument("--atlas")
    p.add_argument("--timeline")
    p.add_argument("--output")
    p.add_argument("--smoke-test", action="store_true")
    args = p.parse_args()
    if args.smoke_test:
        smoke_test()
        print("PASS")
        return
    if not all((args.rkg, args.atlas, args.timeline, args.output)):
        p.error("--rkg, --atlas, --timeline and --output are required")
    combined = project(_read(args.rkg), _read(args.atlas), _read(args.timeline))
    Path(args.output).write_text(json.dumps(combined, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("Derived projection:", len(combined["nodes"]), "nodes,",
          len(combined["edges"]), "links; authority_effect=NONE")

if __name__ == "__main__":
    main()
