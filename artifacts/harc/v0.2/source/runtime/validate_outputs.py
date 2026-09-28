#!/usr/bin/env python3
"""Validate HARC trial deliverable completeness."""
from __future__ import annotations

import argparse
from pathlib import Path

BASE_REQUIRED = (
    "replication_receipt.json",
    "conformance_result.json",
    "engineering_change_proposals.jsonl",
    "humility_receipt.md",
    "agent_summary.md",
)


def missing_outputs(directory: Path, target_result: str | None = None) -> list[str]:
    required = list(BASE_REQUIRED)
    if target_result:
        required.append(target_result)
    missing = []
    for name in required:
        p = directory / name
        if not p.is_file() or p.stat().st_size == 0:
            missing.append(name)
    return missing


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("directory", type=Path)
    ap.add_argument("--target-result")
    args = ap.parse_args()
    missing = missing_outputs(args.directory, args.target_result)
    if missing:
        print("missing: " + ", ".join(missing))
        return 1
    print("complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
