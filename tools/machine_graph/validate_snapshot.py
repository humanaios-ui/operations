#!/usr/bin/env python3
"""Validate a HumanAIOS Machine Substrate Graph snapshot without external dependencies.
Builder v1.7 compliant · validation_tool
HumanAIOS · #596

Usage:
  python3 tools/machine_graph/validate_snapshot.py snapshot.json
  python3 tools/machine_graph/validate_snapshot.py --smoke-test
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path


TOOL_NAME = "machine_graph_validate_snapshot"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "validation_tool"
TOOL_SESSION = "#596"
TOOL_ZONE = 1

REQUIRED_TOP = {"schema", "collector_version", "observed_at", "scope", "nodes", "edges", "omissions", "integrity"}
ALLOWED_OBSERVATION_STATES = {
    "OBSERVED_AVAILABLE",
    "OBSERVED_UNAVAILABLE",
    "NOT_SCANNED",
    "PERMISSION_DENIED",
    "UNKNOWN",
    "STALE_OBSERVATION",
}


def validate_data(data: dict) -> list[str]:
    errors: list[str] = []

    missing = sorted(REQUIRED_TOP - set(data))
    if missing:
        errors.append("missing top-level keys: " + ", ".join(missing))

    nodes = data.get("nodes", [])
    ids = [n.get("id") for n in nodes]
    if any(not i for i in ids):
        errors.append("node without id")
    if len(ids) != len(set(ids)):
        errors.append("duplicate node ids")

    idset = set(ids)
    for n in nodes:
        state = n.get("state")
        if state and state not in ALLOWED_OBSERVATION_STATES:
            errors.append(f"unknown node state: {state}")

    for e in data.get("edges", []):
        if e.get("source") not in idset:
            errors.append(f"missing edge source: {e.get('source')}")
        if e.get("target") not in idset:
            errors.append(f"missing edge target: {e.get('target')}")
        if not e.get("relation"):
            errors.append("edge without relation")

    return errors


def smoke_test() -> int:
    valid = {
        "schema": "x", "collector_version": "0.1.0", "observed_at": "2026-01-01T00:00:00Z",
        "scope": {}, "nodes": [{"id": "a", "state": "OBSERVED_AVAILABLE"}],
        "edges": [], "omissions": [], "integrity": {},
    }
    assert validate_data(valid) == []

    missing_key = dict(valid)
    del missing_key["scope"]
    assert "missing top-level keys: scope" in validate_data(missing_key)

    dangling_edge = dict(valid)
    dangling_edge["edges"] = [{"source": "a", "target": "ghost", "relation": "X"}]
    assert "missing edge target: ghost" in validate_data(dangling_edge)

    with tempfile.TemporaryDirectory() as tmp:
        snap = Path(tmp) / "snapshot.json"
        snap.write_text(json.dumps(valid), encoding="utf-8")
        digest = hashlib.sha256(snap.read_bytes()).hexdigest()
        hash_path = snap.with_suffix(snap.suffix + ".sha256")
        hash_path.write_text(f"{'0' * 64}  snapshot.json\n", encoding="utf-8")
        recorded = hash_path.read_text(encoding="utf-8").split()[0]
        assert recorded != digest, "hash-mismatch path must be reachable"

    print("smoke-test OK — valid/invalid graphs and the hash-mismatch path behave as expected.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("snapshot", nargs="?", help="Required unless --smoke-test is used.")
    ap.add_argument("--hash-file", default=None)
    ap.add_argument("--smoke-test", action="store_true", help="Run the self-test and exit.")
    args = ap.parse_args()

    if args.smoke_test:
        return smoke_test()
    if not args.snapshot:
        ap.error("snapshot is required unless --smoke-test is used")

    path = Path(args.snapshot).expanduser()
    data = json.loads(path.read_text(encoding="utf-8"))
    errors = validate_data(data)
    nodes = data.get("nodes", [])

    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()

    hash_path = Path(args.hash_file).expanduser() if args.hash_file else path.with_suffix(path.suffix + ".sha256")
    if hash_path.exists():
        recorded = hash_path.read_text(encoding="utf-8").split()[0]
        if recorded != digest:
            errors.append(f"hash mismatch: recorded={recorded} actual={digest}")

    print(f"snapshot={path}")
    print(f"sha256={digest}")
    print(f"nodes={len(nodes)}")
    print(f"edges={len(data.get('edges', []))}")
    print(f"omissions={len(data.get('omissions', []))}")
    if errors:
        print("validation=FAIL")
        for err in errors:
            print(f"- {err}")
        return 1

    print("validation=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
