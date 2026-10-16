#!/usr/bin/env python3
"""
kg_map_check_v0_1.py — check the repo snapshot of the HumanAIOS knowledge graph.

Reads kg/humanaios_kg_v0_1.json and checks it against this checkout:

  - ids are unique; every edge endpoint names a known node
  - every edge has a rationale and a status from the declared vocabulary
  - every repo_evidence path exists in this checkout
  - repo_status agrees with the evidence: verified_path needs an existing path,
    no_repo_trace needs no evidence paths

It does not query Supabase. Table names in table_ref are only listed; live
table existence was checked by hand on the as_of date and is recorded in the
snapshot's notes, not re-checked here.

Exit 0 when clean, 1 when any check fails.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
DEFAULT_SNAPSHOT = os.path.join(REPO_ROOT, "kg", "humanaios_kg_v0_1.json")

EDGE_STATUSES = {"unratified", "retracted"}
REPO_STATUSES = {"verified_path", "partial", "no_repo_trace"}


def check(snapshot: dict, repo_root: str) -> list:
    """Return a list of human-readable problems. Empty list means clean."""
    problems = []
    nodes = snapshot.get("nodes", [])
    edges = snapshot.get("edges", [])

    node_ids = [n.get("id") for n in nodes]
    if len(node_ids) != len(set(node_ids)):
        problems.append("duplicate node ids")
    known = set(node_ids)

    for node in nodes:
        nid = node.get("id")
        if node.get("kind") == "repo_area":
            status = node.get("repo_status")
            if status not in REPO_STATUSES:
                problems.append(f"{nid}: unknown repo_status {status!r}")
                continue
            evidence = node.get("repo_evidence", [])
            present = [p for p in evidence if os.path.exists(os.path.join(repo_root, p))]
            if status == "verified_path" and not present:
                problems.append(f"{nid}: verified_path but no evidence path exists")
            if status == "no_repo_trace" and evidence:
                problems.append(f"{nid}: no_repo_trace but evidence paths listed")
            for p in evidence:
                if not os.path.exists(os.path.join(repo_root, p)):
                    problems.append(f"{nid}: evidence path missing: {p}")

    edge_ids = [e.get("id") for e in edges]
    if len(edge_ids) != len(set(edge_ids)):
        problems.append("duplicate edge ids")

    for edge in edges:
        eid = edge.get("id")
        for end in ("source", "target"):
            if edge.get(end) not in known:
                problems.append(f"edge {eid}: unknown {end} {edge.get(end)!r}")
        if not edge.get("rationale"):
            problems.append(f"edge {eid}: no rationale")
        if edge.get("status") not in EDGE_STATUSES:
            problems.append(f"edge {eid}: unknown status {edge.get('status')!r}")

    return problems


def main(argv: list | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("snapshot", nargs="?", default=DEFAULT_SNAPSHOT)
    ap.add_argument("--repo-root", default=REPO_ROOT)
    args = ap.parse_args(argv)

    with open(args.snapshot, encoding="utf-8") as fh:
        snapshot = json.load(fh)

    problems = check(snapshot, args.repo_root)
    if problems:
        for p in problems:
            print(f"FAIL {p}")
        print(f"{len(problems)} problem(s)")
        return 1
    areas = sum(1 for n in snapshot.get("nodes", []) if n.get("kind") == "repo_area")
    print(f"OK {len(snapshot.get('nodes', []))} nodes ({areas} repo areas), "
          f"{len(snapshot.get('edges', []))} edges")
    return 0


if __name__ == "__main__":
    sys.exit(main())
