#!/usr/bin/env python3
"""
graph_lookup_v0_1.py — read-only, citation-bearing lookup over a repository graph.

Builder v1.7 compliant - diagnostic_tool
HumanAIOS - Q-REPO-GRAPH-LOOKUP-01

Reads a graph.json emitted by tools/repository_knowledge_graph_v0_1.py (PR #630
lineage) and answers a search or node query for the §A session-open step. Every
answer cites the node, its incident edges, and each edge's provenance
(source_ref, locator, source_hash). Every answer is labelled with the commit the
graph was compiled from and whether that commit is the repository's current HEAD.

Guarantees:
  - read-only: the graph file and the repository are never written
  - git is consulted only through `rev-parse HEAD` and `status --porcelain`
  - stdlib only; no network; no import of the compiler module, so it works
    whether or not PR #630 has merged
  - a graph whose integrity digest does not verify yields no answers
  - authority_effect is NONE: an answer is a lookup, never a decision

Usage:
  python3 tools/graph_lookup_v0_1.py --smoke-test
  python3 tools/graph_lookup_v0_1.py --graph PATH --search TEXT [--repo PATH]
  python3 tools/graph_lookup_v0_1.py --graph PATH --node NODE_ID [--repo PATH]
  python3 tools/graph_lookup_v0_1.py --graph PATH --search TEXT --require-fresh

Exit codes:
  0  answered; graph is FRESH (compiled at current HEAD, clean worktree)
  2  refused: graph unreadable, malformed, or integrity digest does not verify
  3  answered but not FRESH (STALE, DIRTY or UNKNOWN); with --require-fresh, no answers printed
  4  bad arguments or unknown node id
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

TOOL_NAME = "graph_lookup"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "diagnostic_tool"
TOOL_SESSION = "Q-REPO-GRAPH-LOOKUP-01"

EXIT_OK = 0
EXIT_REFUSED = 2
EXIT_NOT_FRESH = 3
EXIT_BAD_ARGS = 4

MAX_EDGES_PER_NODE = 10


class LookupRefused(Exception):
    """The graph cannot be trusted enough to answer from."""


def _canonical_bytes(value: Any) -> bytes:
    # Mirrors repository_knowledge_graph_v0_1._canonical_bytes so the digest check
    # agrees with the compiler's own integrity field.
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def verify_integrity(graph: dict[str, Any]) -> str:
    """Return the recomputed digest, or raise if it does not match the graph's claim."""
    claimed = (graph.get("integrity") or {}).get("sha256")
    if not isinstance(claimed, str) or len(claimed) != 64:
        raise LookupRefused("graph carries no integrity.sha256")
    candidate = copy.deepcopy(graph)
    candidate["integrity"]["sha256"] = None
    actual = hashlib.sha256(_canonical_bytes(candidate)).hexdigest()
    if actual != claimed:
        raise LookupRefused(f"integrity mismatch: claimed {claimed}, calculated {actual}")
    return actual


def load_graph(path: Path) -> dict[str, Any]:
    try:
        graph = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise LookupRefused(f"cannot read graph {path}: {exc}") from exc
    if not isinstance(graph, dict):
        raise LookupRefused("graph must be a JSON object")
    if graph.get("authority_effect") != "NONE":
        raise LookupRefused("graph does not declare authority_effect NONE; refusing to answer")
    verify_integrity(graph)
    return graph


def _git(repo: Path, *args: str) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True, text=True, timeout=30, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout


def freshness(graph: dict[str, Any], repo: Path) -> dict[str, Any]:
    """Compare the graph's pinned commit with the repository as it is now."""
    pinned = (graph.get("source") or {}).get("head_commit")
    head = _git(repo, "rev-parse", "HEAD")
    status = _git(repo, "status", "--porcelain")
    current = head.strip() if head else None
    dirty = bool(status and status.strip()) if status is not None else None

    if current is None or dirty is None:
        state = "UNKNOWN"
        reason = "repository HEAD or worktree could not be read"
    elif dirty:
        state = "DIRTY"
        reason = "worktree has uncommitted changes; graph reflects the pinned commit only"
    elif current != pinned:
        state = "STALE"
        reason = "graph was compiled from a different commit than current HEAD"
    else:
        state = "FRESH"
        reason = "graph pinned to current clean HEAD"

    return {
        "state": state,
        "reason": reason,
        "pinned_head_commit": pinned,
        "current_head_commit": current,
        "worktree_dirty": dirty,
    }


def _citations(edge: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "source_ref": p.get("source_ref"),
            "locator": p.get("locator"),
            "source_hash": p.get("source_hash"),
            "method": p.get("method"),
            "confidence": p.get("confidence"),
        }
        for p in edge.get("provenance") or []
    ]


def _answer_for(node: dict[str, Any], edges: list[dict[str, Any]]) -> dict[str, Any]:
    incident = [e for e in edges if e.get("from") == node["id"] or e.get("to") == node["id"]]
    incident.sort(key=lambda e: e.get("id", ""))
    cited = []
    for edge in incident[:MAX_EDGES_PER_NODE]:
        cited.append({
            "edge_id": edge.get("id"),
            "relation": edge.get("relation"),
            "direction": "OUT" if edge.get("from") == node["id"] else "IN",
            "other_end": edge.get("to") if edge.get("from") == node["id"] else edge.get("from"),
            "evidence_state": edge.get("evidence_state"),
            "citations": _citations(edge),
        })
    return {
        "node": {
            "id": node.get("id"),
            "type": node.get("type"),
            "label": node.get("label"),
            "provenance": node.get("provenance") or [],
        },
        "incident_edges": cited,
        "incident_edge_total": len(incident),
        "incident_edges_truncated": len(incident) > MAX_EDGES_PER_NODE,
    }


def lookup(graph: dict[str, Any], *, search: str | None, node_id: str | None, limit: int) -> list[dict[str, Any]]:
    nodes = graph.get("nodes") or []
    edges = graph.get("edges") or []
    if node_id is not None:
        match = [n for n in nodes if n.get("id") == node_id]
        if not match:
            raise KeyError(node_id)
        return [_answer_for(match[0], edges)]
    needle = (search or "").lower()
    hits = [
        n for n in nodes
        if needle in str(n.get("id", "")).lower() or needle in str(n.get("label", "")).lower()
    ]
    hits.sort(key=lambda n: n.get("id", ""))
    return [_answer_for(n, edges) for n in hits[:limit]]


def build_report(graph_path: Path, repo: Path, graph: dict[str, Any], fresh: dict[str, Any],
                 results: list[dict[str, Any]] | None, query: dict[str, Any]) -> dict[str, Any]:
    return {
        "tool": {"name": TOOL_NAME, "version": TOOL_VERSION, "session": TOOL_SESSION},
        "authority_effect": "NONE",
        "read_only": True,
        "graph": {
            "path": str(graph_path),
            "graph_id": graph.get("graph_id"),
            "integrity_sha256": (graph.get("integrity") or {}).get("sha256"),
            "pinned_head_commit": fresh["pinned_head_commit"],
            "repository": (graph.get("source") or {}).get("repository"),
        },
        "repository": {"path": str(repo), "current_head_commit": fresh["current_head_commit"]},
        "freshness": fresh,
        "query": query,
        "results": results,
    }


def run_smoke_test() -> int:
    """In-memory check: digest verifies, tampering is refused, answers carry citations."""
    graph = {
        "graph_id": "smoke",
        "graph_kind": "DERIVED_READ_MODEL",
        "authority_effect": "NONE",
        "source": {"repository": "smoke", "head_commit": "0" * 40, "worktree_state": "CLEAN"},
        "nodes": [{"id": "n:a", "type": "artifact", "label": "alpha", "provenance": []}],
        "edges": [{"id": "e:1", "from": "n:a", "to": "n:b", "relation": "REFERENCES",
                   "evidence_state": "OBSERVED", "provenance": [
                       {"source_ref": "a.md", "locator": "line:1", "source_hash": "c" * 64,
                        "method": "smoke", "confidence": 1.0}]}],
        "integrity": {"algorithm": "sha256", "canonicalization": "json-sort-keys-utf8", "sha256": None},
    }
    graph["integrity"]["sha256"] = hashlib.sha256(
        _canonical_bytes({**graph, "integrity": {**graph["integrity"], "sha256": None}})).hexdigest()
    checks = {}
    checks["digest_verifies"] = verify_integrity(graph) == graph["integrity"]["sha256"]
    tampered = copy.deepcopy(graph)
    tampered["nodes"][0]["label"] = "beta"
    try:
        verify_integrity(tampered)
        checks["tamper_refused"] = False
    except LookupRefused:
        checks["tamper_refused"] = True
    answer = lookup(graph, search="alpha", node_id=None, limit=5)
    checks["answer_cites_edge"] = bool(answer) and answer[0]["incident_edges"][0]["citations"][0]["locator"] == "line:1"
    ok = all(checks.values())
    print(json.dumps({"smoke_test": "PASS" if ok else "FAIL", "checks": checks}, sort_keys=True))
    return EXIT_OK if ok else EXIT_REFUSED


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only, citation-bearing graph lookup (§A).")
    parser.add_argument("--smoke-test", action="store_true", help="run the in-memory self-check and exit")
    parser.add_argument("--graph", help="graph.json from the repository graph compiler")
    parser.add_argument("--repo", default=".", help="repository the graph describes (default: cwd)")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--search", help="case-insensitive substring over node id and label")
    group.add_argument("--node", help="exact node id")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--require-fresh", action="store_true",
                        help="print no answers unless the graph is FRESH")
    args = parser.parse_args(argv)

    if args.smoke_test:
        return run_smoke_test()
    if not args.graph or not (args.search or args.node):
        parser.error("--graph and one of --search / --node are required")
    if args.limit < 1:
        print(json.dumps({"error": "limit must be at least 1"}), file=sys.stderr)
        return EXIT_BAD_ARGS

    graph_path = Path(args.graph)
    repo = Path(args.repo).resolve()
    try:
        graph = load_graph(graph_path)
    except LookupRefused as exc:
        print(json.dumps({"refused": str(exc), "authority_effect": "NONE"}, indent=2), file=sys.stdout)
        return EXIT_REFUSED

    fresh = freshness(graph, repo)
    query = {"search": args.search, "node": args.node, "limit": args.limit}
    try:
        results = lookup(graph, search=args.search, node_id=args.node, limit=args.limit)
    except KeyError as exc:
        print(json.dumps({"error": f"node not found: {exc.args[0]}"}), file=sys.stderr)
        return EXIT_BAD_ARGS

    if args.require_fresh and fresh["state"] != "FRESH":
        results = None

    report = build_report(graph_path, repo, graph, fresh, results, query)
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    return EXIT_OK if fresh["state"] == "FRESH" else EXIT_NOT_FRESH


if __name__ == "__main__":
    raise SystemExit(main())
