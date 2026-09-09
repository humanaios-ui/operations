#!/usr/bin/env python3
"""Lint SMAG ledger predictions for pinned `smag_p:` probabilities."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SMAG_P = re.compile(r"(?im)^\s*smag_p\s*:\s*(0(?:\.\d+)?|1(?:\.0+)?)\s*$")
DEFAULT_LEDGER = "audits/smag_pilot_ledger.jsonl"


def load_rows(path: Path) -> list[dict]:
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def find_void_rows(rows: list[dict]) -> list[dict]:
    out = []
    for row in rows:
        predicted = str(row.get("predicted", ""))
        if not SMAG_P.search(predicted):
            out.append(row)
    return out


def smoke_test() -> int:
    rows = [
        {"pr": "1", "predicted": "smag_p:0.40"},
        {"pr": "2", "predicted": "VOID: missing smag_p"},
    ]
    voids = find_void_rows(rows)
    assert len(voids) == 1 and voids[0]["pr"] == "2"
    print("✓ Smoke test PASSED")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Lint SMAG predicted field for pinned probabilities.")
    p.add_argument("--ledger", default=DEFAULT_LEDGER)
    p.add_argument("--enforce", action="store_true", help="exit non-zero if VOID rows exist")
    p.add_argument("--smoke-test", action="store_true")
    args = p.parse_args()

    if args.smoke_test:
        return smoke_test()

    rows = load_rows(Path(args.ledger))
    voids = find_void_rows(rows)
    print(f"rows={len(rows)} with_smag_p={len(rows) - len(voids)} void={len(voids)}")
    if voids:
        sample = ", ".join(str(v.get("pr", "?")) for v in voids[:10])
        print(f"VOID rows (missing smag_p): {sample}")
    if args.enforce and voids:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
