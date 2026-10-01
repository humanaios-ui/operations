#!/usr/bin/env python3
"""Validate a HumanAIOS Machine Substrate Graph snapshot without external dependencies."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


REQUIRED_TOP = {"schema", "collector_version", "observed_at", "scope", "nodes", "edges", "omissions", "integrity"}
ALLOWED_OBSERVATION_STATES = {
    "OBSERVED_AVAILABLE",
    "OBSERVED_UNAVAILABLE",
    "NOT_SCANNED",
    "PERMISSION_DENIED",
    "UNKNOWN",
    "STALE_OBSERVATION",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("snapshot")
    ap.add_argument("--hash-file", default=None)
    args = ap.parse_args()

    path = Path(args.snapshot).expanduser()
    data = json.loads(path.read_text(encoding="utf-8"))
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
