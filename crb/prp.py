"""Portable Review Package integrity helpers.

Defines a non-self-referential package root and append-only run-event verification.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

DIGEST_FILE = "receipts/package.sha256"


def _canonical_json(obj: Any) -> bytes:
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def package_inventory(root: str | Path) -> list[dict[str, Any]]:
    root = Path(root).resolve()
    rows: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"symlink refused: {path}")
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if rel == DIGEST_FILE:
            continue
        data = path.read_bytes()
        rows.append({"path": rel, "size": len(data), "sha256": sha256_bytes(data)})
    return rows


def package_root(root: str | Path) -> str:
    return sha256_bytes(_canonical_json(package_inventory(root)))


def event_hash(event: dict[str, Any]) -> str:
    body = dict(event)
    body.pop("event_hash", None)
    return sha256_bytes(_canonical_json(body))


def verify_event_chain(path: str | Path) -> tuple[bool, str]:
    previous = None
    expected_seq = 1
    for line_no, raw in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        event = json.loads(raw)
        if event.get("seq") != expected_seq:
            return False, f"line {line_no}: expected seq {expected_seq}"
        if event.get("prev_event_hash") != previous:
            return False, f"line {line_no}: predecessor mismatch"
        calculated = event_hash(event)
        if event.get("event_hash") != calculated:
            return False, f"line {line_no}: event hash mismatch"
        previous = calculated
        expected_seq += 1
    return True, "VALID"
