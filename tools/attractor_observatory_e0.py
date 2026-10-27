#!/usr/bin/env python3
"""Read-only HumanAIOS convergence and conversion observatory (E0).
Builder v1.7 compliant

Static edges show possible routing, not executed agent decisions.
Outcome rows are unauthenticated assertions even when they carry a reviewer.
No external I/O, persistence, authorization, or automatic learning.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys

TOOL_NAME = "attractor_observatory"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "analytics_tool"
TOOL_ZONE = 1
TOOL_SESSION = "S-20261026-ATTRACTOR-E0"

SCHEMA = "humanaios.attractor_observatory.e0"
STAGES = {
    "OBJECTIVE_DEFINED", "CANDIDATE_IDENTIFIED", "SOURCE_REVIEWED",
    "HUMAN_AUTHORIZED", "RESOURCE_INVENTORIED", "RESOURCE_ACQUIRED",
    "OBJECTIVE_COMPLETED", "RECOVERY_BENEFIT_DELIVERED",
}
OUTCOMES = ("RESOURCE_ACQUIRED", "OBJECTIVE_COMPLETED", "RECOVERY_BENEFIT_DELIVERED")
ID = re.compile(r"^[A-Za-z0-9_.:-]{1,100}$")
HEX40 = re.compile(r"^[a-f0-9]{40}$")
HEX64 = re.compile(r"^[a-f0-9]{64}$")
EVENT_KEYS = {
    "event_id", "objective_id", "event_type", "process_id", "observed_at",
    "source_ref", "source_revision", "evidence_digest", "observer_id",
    "reviewer_id", "review_verdict", "resource_id", "benefit_id",
    "beneficiary_alias",
}
TRAIL_KEYS = {
    "trail_id", "actor_kind", "actor_id", "step", "node_id", "observed_at",
    "source_ref", "source_revision",
}


def _id(value, field):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise ValueError(f"{field}: expected a pseudonymous or namespaced ID")
    return value


def _timestamp(value):
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("observed_at: require UTC ISO8601 ending Z")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("observed_at: invalid UTC timestamp") from exc
    if parsed.utcoffset().total_seconds() != 0:
        raise ValueError("observed_at: not UTC")


def _row_fields(row, allowed, required):
    if not isinstance(row, dict) or set(row) - allowed or set(required) - set(row):
        raise ValueError("invalid record keys: unknown, missing, or non-object")
    for key in required:
        if row[key] is None or row[key] == "":
            raise ValueError(f"required field empty: {key}")


def _read(path, kind):
    if path is None:
        return None, None
    raw = Path(path).read_bytes()
    if len(raw) > 10_000_000:
        raise ValueError(f"{kind}: file too large")
    digest = hashlib.sha256(raw).hexdigest()
    if kind == "graph":
        return json.loads(raw), digest
    records = []
    for i, line in enumerate(raw.splitlines(), 1):
        if not line.strip():
            continue
        if len(line) > 16_384 or len(records) >= 10_000:
            raise ValueError(f"{kind}: record limit exceeded")
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{kind}: malformed JSON at line {i}") from exc
    return records, digest


def _graph(raw):
    if not isinstance(raw, dict):
        raise ValueError("graph must be an object")
    nodes = raw.get("nodes")
    edges = raw.get("edges")
    if isinstance(nodes, dict):
        ids = list(nodes)
        if any(not isinstance(v, dict) or v.get("id", k) != k for k, v in nodes.items()):
            raise ValueError("graph node ID mismatch")
    elif isinstance(nodes, list):
        ids = [v.get("id") for v in nodes if isinstance(v, dict)]
        if len(ids) != len(nodes):
            raise ValueError("bad graph nodes")
    else:
        raise ValueError("bad graph nodes")
    if not isinstance(edges, list) or not ids or len(ids) > 1000 or len(edges) > 10000:
        raise ValueError("bad graph size")
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate graph node")
    for v in ids:
        _id(v, "node ID")
    adjacency = {v: [] for v in ids}
    for e in edges:
        if not isinstance(e, dict):
            raise ValueError("invalid edge")
        source, target = e.get("source", e.get("from")), e.get("target", e.get("to"))
        if source not in adjacency or target not in adjacency:
            raise ValueError("dangling edge")
        if target not in adjacency[source]:
            adjacency[source].append(target)
    return adjacency, len(edges)


def _components(adjacency):
    """Tarjan SCC; ordered deterministic report, edges are directed."""
    count = 0
    index, low, stack, on_stack, result = {}, {}, [], set(), []

    def visit(v):
        nonlocal count
        index[v] = low[v] = count
        count += 1
        stack.append(v)
        on_stack.add(v)
        for w in adjacency[v]:
            if w not in index:
                visit(w)
                low[v] = min(low[v], low[w])
            elif w in on_stack:
                low[v] = min(low[v], index[w])
        if index[v] == low[v]:
            part = []
            while True:
                w = stack.pop()
                on_stack.remove(w)
                part.append(w)
                if w == v:
                    break
            result.append(sorted(part))

    for v in sorted(adjacency):
        if v not in index:
            visit(v)
    return result


def internal(adjacency, edge_count):
    groups = _components(adjacency)
    members = {v: i for i, group in enumerate(groups) for v in group}
    reach = Counter()
    for start in adjacency:
        seen, queue = {start}, [start]
        for v in queue:
            for w in adjacency[v]:
                if w not in seen:
                    seen.add(w)
                    queue.append(w)
        reach.update({members[v] for v in seen})
    summaries = []
    for i, group in enumerate(groups):
        exits = sorted({members[w] for v in group for w in adjacency[v] if members[w] != i})
        cyclic = len(group) > 1 or any(v in adjacency[v] for v in group)
        summaries.append({
            "node_ids": group, "size": len(group),
            "reachable_from_start_count": reach[i],
            "cyclic": cyclic, "exit_component_count": len(exits),
            "terminal": len(exits) == 0,
        })
    summaries.sort(key=lambda item: (-item["size"], -item["reachable_from_start_count"], item["node_ids"]))
    # Stored first outgoing edge is a repeatable test policy, NOT Wikipedia's
    # semantic first link and NOT a claim about live routing frequency.
    loops = 0
    for start in adjacency:
        v, seen = start, set()
        while v not in seen and adjacency[v]:
            seen.add(v)
            v = adjacency[v][0]
        if v in seen:
            loops += 1
    return {
        "mode": "STRUCTURAL_POSSIBILITY_ONLY",
        "node_count": len(adjacency), "edge_count": edge_count,
        "strongly_connected_components": summaries,
        "largest_cyclic_component_size": max((g["size"] for g in summaries if g["cyclic"]), default=0),
        "first_stored_edge_loop_starts": loops,
        "first_stored_edge_policy": "first unique outgoing target in source JSON edge order",
        "caveat": "SCC reachability is not observed runtime repetition or proof of causal influence.",
    }


def observed_returns(records, adjacency):
    if records is None:
        return {"state": "NOT_MEASURED", "trails": None, "repeated_returns": None}
    grouped = defaultdict(list)
    for row in records:
        _row_fields(row, TRAIL_KEYS, TRAIL_KEYS)
        for key in ("trail_id", "actor_id", "node_id"):
            _id(row[key], key)
        if row["actor_kind"] not in ("agent", "decision", "process"):
            raise ValueError("actor_kind must be agent, decision, or process")
        if not isinstance(row["step"], int) or isinstance(row["step"], bool) or row["step"] < 0:
            raise ValueError("step must be a nonnegative integer")
        if row["node_id"] not in adjacency or not isinstance(row["source_ref"], str) or not row["source_ref"]:
            raise ValueError("unknown node or missing source")
        if not HEX40.fullmatch(str(row["source_revision"])):
            raise ValueError("source_revision must be a 40-character commit SHA")
        _timestamp(row["observed_at"])
        grouped[row["trail_id"]].append(row)
    repeat = Counter()
    by_kind = Counter()
    for rows in grouped.values():
        rows.sort(key=lambda r: r["step"])
        if [r["step"] for r in rows] != list(range(len(rows))):
            raise ValueError("trail steps must start at zero without duplicates or gaps")
        if len({(r["actor_id"], r["actor_kind"]) for r in rows}) != 1:
            raise ValueError("trail changes actor identity")
        by_kind[rows[0]["actor_kind"]] += 1
        visits = Counter()
        for prev, row in zip(rows, rows[1:]):
            if row["node_id"] not in adjacency[prev["node_id"]]:
                raise ValueError("trail contains an edge absent from the pinned graph")
        for row in rows:
            visits[row["node_id"]] += 1
        for node, n in visits.items():
            if n > 1:
                repeat[node] += n - 1
    return {
        "state": "OBSERVED_RECORDS_NOT_AUTHENTICATED" if records else "EMPTY_OBSERVATION_WINDOW",
        "trails": len(grouped), "by_actor_kind": dict(sorted(by_kind.items())),
        "repeated_returns": [
            {"node_id": node, "extra_visits_in_trails": n}
            for node, n in sorted(repeat.items(), key=lambda p: (-p[1], p[0]))
        ],
        "caveat": "Source revisions were supplied by the recorder, not independently authenticated.",
    }


def external_conversion(records, adjacency):
    if records is None:
        return {"state": "NOT_MEASURED", "outcomes": None, "by_process": None}
    seen = set()
    groups = defaultdict(lambda: {"RESOURCE_ACQUIRED": 0,
                                  "OBJECTIVE_COMPLETED": 0,
                                  "RECOVERY_BENEFIT_DELIVERED": 0,
                                  "review_attested": 0})
    totals, reviewed, unmapped = Counter(), Counter(), set()
    for row in records:
        required = {
            "event_id", "objective_id", "event_type", "process_id", "observed_at",
            "source_ref", "source_revision", "evidence_digest", "observer_id",
        }
        _row_fields(row, EVENT_KEYS, required)
        for key in ("event_id", "objective_id", "process_id", "observer_id"):
            _id(row[key], key)
        if row["event_id"] in seen:
            raise ValueError("duplicate external event ID")
        seen.add(row["event_id"])
        if row["event_type"] not in STAGES:
            raise ValueError("unknown stage")
        _timestamp(row["observed_at"])
        if not isinstance(row["source_ref"], str) or not row["source_ref"]:
            raise ValueError("source_ref required")
        if not HEX40.fullmatch(str(row["source_revision"])) or not HEX64.fullmatch(str(row["evidence_digest"])):
            raise ValueError("source_revision or evidence_digest invalid")
        for optional_id in ("resource_id", "benefit_id", "beneficiary_alias", "reviewer_id"):
            if optional_id in row:
                _id(row[optional_id], optional_id)
        if row.get("review_verdict") not in (None, "SUPPORTS", "REJECTS", "INDETERMINATE"):
            raise ValueError("bad reviewer verdict")
        stage = row["event_type"]
        if stage in ("RESOURCE_ACQUIRED", "RESOURCE_INVENTORIED") and not row.get("resource_id"):
            raise ValueError("resource outcome requires resource_id")
        if stage == "RECOVERY_BENEFIT_DELIVERED" and (
            not row.get("benefit_id") or not row.get("beneficiary_alias")
        ):
            raise ValueError("benefit requires pseudonymous benefit and beneficiary references")
        if row["process_id"] not in adjacency:
            unmapped.add(row["process_id"])
        if stage in OUTCOMES:
            totals[stage] += 1
            groups[row["process_id"]][stage] += 1
            if row.get("review_verdict") == "SUPPORTS" and row.get("reviewer_id") != row["observer_id"] and row.get("reviewer_id"):
                reviewed[stage] += 1
                groups[row["process_id"]]["review_attested"] += 1
    return {
        "state": "ASSERTIONS_ONLY_NOT_INDEPENDENTLY_AUTHENTICATED" if records else "EMPTY_OBSERVATION_WINDOW",
        "event_count": len(records), "outcomes": dict(sorted(totals.items())),
        "separately_review_attested_outcomes": dict(sorted(reviewed.items())),
        "by_process": [{"process_id": key, **value} for key, value in sorted(groups.items())],
        "unmapped_process_ids": sorted(unmapped),
        "caveat": "Review names and evidence digests are claims in input records. No proof was fetched or authenticated. Process association does not establish causation.",
    }


def build(graph_data, trails=None, outcomes=None, fingerprints=None):
    adjacency, edge_count = _graph(graph_data)
    return {
        "schema": SCHEMA, "authority_effect": "NONE",
        "execution": "DISABLED", "merge_authority": False,
        "inputs": fingerprints or {},
        "graph_generated_at": graph_data.get("generated_at"),
        "source_graph_validation": graph_data.get("validation_status", {"state": "UNREPORTED"}),
        "internal": internal(adjacency, edge_count),
        "observed_returns": observed_returns(trails, adjacency),
        "external_conversion": external_conversion(outcomes, adjacency),
    }


def run_smoke_test():
    """Non-authorizing synthetic smoke-test, no file or network access."""
    synthetic = {
        "nodes": {"X": {"id": "X"}, "Y": {"id": "Y"}},
        "edges": [{"source": "X", "target": "Y"}, {"source": "Y", "target": "X"}],
    }
    report = build(synthetic)
    assert report["authority_effect"] == "NONE"
    assert report["internal"]["largest_cyclic_component_size"] == 2
    assert report["external_conversion"]["state"] == "NOT_MEASURED"
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke-test", action="store_true")
    parser.add_argument("--graph", default="system_graph.json")
    parser.add_argument("--trails", help="explicit read-only observed routing JSONL; optional")
    parser.add_argument("--outcomes", help="explicit receipt claims JSONL; optional")
    parser.add_argument("--output", help="optional local report file; defaults to stdout")
    args = parser.parse_args(argv)
    if args.smoke_test:
        return run_smoke_test()
    try:
        graph, ghash = _read(args.graph, "graph")
        trails, thash = _read(args.trails, "trails")
        outcomes, ohash = _read(args.outcomes, "outcomes")
        report = build(graph, trails, outcomes, {
            "graph_sha256": ghash, "trails_sha256": thash, "outcomes_sha256": ohash,
            "note": "SHA256 fingerprints bytes; does not authenticate the originating Git commit",
        })
    except (OSError, ValueError, TypeError, KeyError, RecursionError, json.JSONDecodeError) as exc:
        parser.exit(2, f"Invalid observation input: {exc}\n")
    output = json.dumps(report, sort_keys=True, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
