#!/usr/bin/env python3
"""Read-only resource measurements for *existing* HumanAIOS JSON graph views.

This is an observational sidecar, not a graph compiler, admission gate, or
execution router. No graph, repository file, or credential is modified.

Builder v1.7 compliant - diagnostic_tool
HumanAIOS
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import statistics
import sys
import time
import tracemalloc

TOOL_NAME = "graph_resource_observer"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "diagnostic_tool"
TOOL_ZONE = 1

VERSION = TOOL_VERSION
MAX_BYTES = 16 * 1024 * 1024
MAX_TRIALS = 15
SYSTEMS = (
    "system_graph", "evidence_graph", "codebase_atlas", "repository_graph",
    "temporal_graph", "machine_substrate_graph", "session_graph",
)
SAFE_CONTEXT = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._:-]{0,63}$")


class ObservationRefused(ValueError):
    """Unsafe input or unsupported graph structure; no valid measurement."""


def graph_path(repo: Path, name: str) -> Path:
    relative = PurePosixPath(name)
    if (not name or relative.is_absolute() or "\\" in name or
            any(part in ("..", ".") for part in name.split("/")) or
            relative.suffix != ".json"):
        raise ObservationRefused("graph must be a safe relative .json path")
    root = repo.resolve(strict=True)
    path = root
    for part in relative.parts:
        path = path / part
        if path.is_symlink():
            raise ObservationRefused("symlink in graph path refused")
    try:
        candidate = path.resolve(strict=True)
        candidate.relative_to(root)
    except (OSError, ValueError) as exc:
        raise ObservationRefused("graph must exist inside repository") from exc
    if not candidate.is_file():
        raise ObservationRefused("graph must be a regular file")
    return candidate


def _nodes(graph: dict) -> dict[str, object]:
    raw = graph.get("nodes")
    if isinstance(raw, dict):
        if not all(isinstance(key, str) for key in raw):
            raise ObservationRefused("node keys must be strings")
        return raw
    if isinstance(raw, list):
        result: dict[str, object] = {}
        for node in raw:
            if not isinstance(node, dict) or not isinstance(node.get("id"), str):
                raise ObservationRefused("nodes must have string ids")
            if node["id"] in result:
                raise ObservationRefused("duplicate node id")
            result[node["id"]] = node
        return result
    raise ObservationRefused("expected nodes list or object")


def _edges(graph: dict) -> list[dict]:
    edges = graph.get("edges")
    if not isinstance(edges, list) or not all(isinstance(e, dict) for e in edges):
        raise ObservationRefused("expected edges list of objects")
    return edges


def _incident(edges: list[dict], node_id: str) -> int:
    total = 0
    for edge in edges:
        if "from" in edge and "to" in edge:
            left, right = edge["from"], edge["to"]
        elif "source" in edge and "target" in edge:
            left, right = edge["source"], edge["target"]
        else:
            raise ObservationRefused("node scan requires from/to or source/target edges")
        if not isinstance(left, str) or not isinstance(right, str):
            raise ObservationRefused("edge endpoints must be strings")
        total += left == node_id or right == node_id
    return total


def measure_once(path: Path, node_id: str | None) -> tuple[dict, dict]:
    # All measured activity is reading/parsing/hash/counting or an optional node scan.
    tracemalloc.start()
    wall_start = time.perf_counter_ns()
    cpu_start = time.process_time_ns()
    try:
        try:
            with path.open("rb") as handle:
                payload = handle.read(MAX_BYTES + 1)
        except OSError as exc:
            raise ObservationRefused("graph read failed") from exc
        if len(payload) > MAX_BYTES:
            raise ObservationRefused("graph exceeds fixed 16 MiB safety bound")
        try:
            graph = json.loads(payload)
        except (UnicodeError, ValueError) as exc:
            raise ObservationRefused("graph is not valid JSON") from exc
        if not isinstance(graph, dict):
            raise ObservationRefused("graph must be an object")
        nodes, edges = _nodes(graph), _edges(graph)
        incident = None
        if node_id is not None:
            if node_id not in nodes:
                raise ObservationRefused("node not present; count is not zero")
            incident = _incident(edges, node_id)
        digest = hashlib.sha256(payload).hexdigest()
        cpu_ns = time.process_time_ns() - cpu_start
        wall_ns = time.perf_counter_ns() - wall_start
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return (
        {"bytes_read": len(payload), "sha256": digest,
         "nodes_count": len(nodes), "edges_count": len(edges),
         "incident_edges_count": incident},
        {"wall_ns": wall_ns, "cpu_ns": cpu_ns,
         "peak_python_alloc_bytes": peak},
    )


def observe(repo: Path, filename: str, system: str, *, trials: int = 3,
            node_id: str | None = None, context_id: str = "UNSPECIFIED") -> dict:
    if system not in SYSTEMS:
        raise ObservationRefused("unrecognized source system")
    if type(trials) is not int or not 1 <= trials <= MAX_TRIALS:
        raise ObservationRefused("trials must be between 1 and 15")
    if context_id != "UNSPECIFIED" and not SAFE_CONTEXT.fullmatch(context_id):
        raise ObservationRefused("context_id must be short and pseudonymous")
    path = graph_path(repo, filename)
    samples = []
    source = None
    for _ in range(trials):
        identity, cost = measure_once(path, node_id)
        if source is not None and source != identity:
            raise ObservationRefused("source changed between trials; no result")
        source = identity
        samples.append(cost)
    assert source is not None
    return {
        "schema_version": "humanaios.graph.resource_cost_observation.v0",
        "authority_effect": "NONE",
        "read_only": True,
        "source": {
            "system": system, "source_ref": filename,
            "revision": "sha256:" + source["sha256"],
            "revision_kind": "content_hash_not_git_commit",
        },
        "observation": {
            "state": "OBSERVED", "observed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "execution_context_id": context_id,
            "operation": "read_parse_node_scan" if node_id is not None else "read_parse_count",
            "node_id": node_id, "bytes_read": source["bytes_read"],
            "nodes_count": source["nodes_count"], "edges_count": source["edges_count"],
            "incident_edges_count": source["incident_edges_count"],
            "tool_version": VERSION,
            "trials": samples,
            "median_wall_ns": statistics.median(s["wall_ns"] for s in samples),
            "median_cpu_ns": statistics.median(s["cpu_ns"] for s in samples),
            "max_python_alloc_bytes": max(s["peak_python_alloc_bytes"] for s in samples),
            "limitations": [
                "Python allocation tracing is not process RSS or total system RAM",
                "CPU time includes local Python processing; no GPU, disk IOPS, or cloud pricing measured",
                "Warm-cache state and tracing overhead are uncontrolled",
                "Cost is descriptive, not evidence of graph correctness or authorization",
            ],
        },
    }


def run_smoke_test() -> bool:
    """In-memory integrity check: count and node scan without filesystem writes."""
    fixture = {"nodes": {"A": {"id": "A"}},
               "edges": [{"source": "A", "target": "A"}]}
    passed = len(_nodes(fixture)) == 1 and _incident(_edges(fixture), "A") == 1
    print(json.dumps({"smoke_test": "PASS" if passed else "FAIL",
                      "authority_effect": "NONE"}))
    return passed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="read-only root of the existing repository")
    parser.add_argument("--graph", help="relative existing JSON graph path")
    parser.add_argument("--system", choices=SYSTEMS)
    parser.add_argument("--smoke-test", action="store_true", help="run in-memory self-check")
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--node-id", help="optional measured incident-edge scan")
    parser.add_argument("--context-id", default="UNSPECIFIED", help="optional pseudonymous host/context tag")
    args = parser.parse_args(argv)
    if args.smoke_test:
        return 0 if run_smoke_test() else 2
    if not args.graph or not args.system:
        parser.error("--graph and --system are required unless --smoke-test is used")
    try:
        result = observe(Path(args.repo), args.graph, args.system,
                         trials=args.trials, node_id=args.node_id,
                         context_id=args.context_id)
    except (ObservationRefused, OSError) as exc:
        print(json.dumps({"observation_state": "REFUSED", "authority_effect": "NONE",
                          "reason": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
