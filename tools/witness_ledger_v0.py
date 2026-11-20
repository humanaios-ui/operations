#!/usr/bin/env python3
"""
Builder v1.7 compliant
witness_ledger_v0.py — local INTENT-OS witness ledger (append-only, hash-chained).

Evidence / attribution substrate only. AUTHORITY_EFFECT is NONE. can_authorize is
false. This tool does not grant merge authority, satisfy required review, sign a
ruling, or replace a Z2 hash. Stop-hook allowlists and HTTP APIs are out of scope.

Usage:
  python3 tools/witness_ledger_v0.py init [--ledger PATH]
  python3 tools/witness_ledger_v0.py append --decision-id ID ... [--ledger PATH]
  python3 tools/witness_ledger_v0.py verify [--ledger PATH]
  python3 tools/witness_ledger_v0.py list [--ledger PATH] [--limit N]
  python3 tools/witness_ledger_v0.py --smoke-test
"""
from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

TOOL_NAME = "witness_ledger"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "governance_tool"
TOOL_ZONE = 1

AUTHORITY_EFFECT = "NONE"
CAN_AUTHORIZE = False
ADVISORY_ONLY = True
SCHEMA_ID = "intentos/witness_ledger_entry_v0"

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LEDGER = ROOT / "ledgers" / "WITNESS_LEDGER.jsonl"
SCHEMA_PATH = ROOT / "schemas" / "intent_os_witness_ledger_entry_v0.schema.json"
ZERO_HASH = "0" * 64

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_TS_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T")

ACTOR_TYPES = ("human", "machine")
ACTOR_ROLES = ("Z1", "Z2", "Z3")
DECISION_CLASSES = ("propose", "approve", "execute", "ratify", "record")
AUTHORITY_LEVELS = ("NONE", "Z1", "Z2", "Z3")

HASHED_FIELDS = (
    "schema",
    "authority_effect",
    "can_authorize",
    "advisory_only",
    "seq",
    "prev_hash",
    "decision_id",
    "timestamp_utc",
    "actor_type",
    "actor_email",
    "actor_role",
    "decision_class",
    "title",
    "context",
    "authority_level",
    "artifacts",
    "rationale",
    "falsifier",
)


class LedgerError(RuntimeError):
    """Raised when a ledger cannot be read or its chain does not validate."""


@contextlib.contextmanager
def ledger_lock(path: Path):
    """Serialize read-build-append on one ledger (same posture as resource_ledger)."""
    lock_path = path.with_suffix(path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "a+", encoding="utf-8") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def canon(obj: Dict[str, Any]) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def refuse(msg: str) -> None:
    raise LedgerError(msg)


def load_rows(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            rows.append(json.loads(stripped))
        except json.JSONDecodeError as exc:
            raise LedgerError(f"{path}:{number}: invalid JSON — {exc}") from exc
    return rows


def body_for_hash(row: Dict[str, Any]) -> Dict[str, Any]:
    return {k: row[k] for k in HASHED_FIELDS if k in row}


def compute_hash(row: Dict[str, Any]) -> str:
    return sha256_hex(canon(body_for_hash(row)))


def validate_entry_shape(row: Dict[str, Any], *, require_hash: bool = True) -> None:
    """Stdlib structural checks mirroring the JSON Schema hard constraints."""
    if row.get("schema") != SCHEMA_ID:
        refuse(f"schema must be {SCHEMA_ID!r}, got {row.get('schema')!r}")
    if row.get("authority_effect") != AUTHORITY_EFFECT:
        refuse("authority_effect must be NONE")
    if row.get("can_authorize") is not False:
        refuse("can_authorize must be false")
    if row.get("advisory_only") is not True:
        refuse("advisory_only must be true")

    seq = row.get("seq")
    if not isinstance(seq, int) or isinstance(seq, bool) or seq < 1:
        refuse(f"seq must be a positive integer, got {seq!r}")

    for field in ("prev_hash", "hash") if require_hash else ("prev_hash",):
        value = row.get(field)
        if not isinstance(value, str) or not _SHA256_RE.match(value):
            refuse(f"{field} must be 64 lowercase hex chars")

    for field in (
        "decision_id",
        "title",
        "context",
        "rationale",
        "falsifier",
        "actor_email",
        "timestamp_utc",
    ):
        value = row.get(field)
        if not isinstance(value, str) or not value.strip():
            refuse(f"{field} must be a non-empty string")

    if not _TS_RE.match(row["timestamp_utc"]):
        refuse("timestamp_utc must be an ISO-8601 UTC timestamp starting YYYY-MM-DDT")
    if not _EMAIL_RE.match(row["actor_email"]):
        refuse(f"actor_email {row['actor_email']!r} is not an email-shaped string")
    if row.get("actor_type") not in ACTOR_TYPES:
        refuse(f"actor_type must be one of {ACTOR_TYPES}")
    if row.get("actor_role") not in ACTOR_ROLES:
        refuse(f"actor_role must be one of {ACTOR_ROLES}")
    if row.get("decision_class") not in DECISION_CLASSES:
        refuse(f"decision_class must be one of {DECISION_CLASSES}")
    if row.get("authority_level") not in AUTHORITY_LEVELS:
        refuse(f"authority_level must be one of {AUTHORITY_LEVELS}")

    artifacts = row.get("artifacts")
    if not isinstance(artifacts, dict):
        refuse("artifacts must be an object")
    for key, value in artifacts.items():
        if not isinstance(key, str) or not isinstance(value, str):
            refuse("artifacts values must be strings")


def verify_chain(rows: List[Dict[str, Any]]) -> List[str]:
    """Return a list of break descriptions; empty means OK."""
    breaks: List[str] = []
    prev = ZERO_HASH
    for index, row in enumerate(rows):
        try:
            validate_entry_shape(row, require_hash=True)
        except LedgerError as exc:
            breaks.append(f"seq={row.get('seq', '?')} shape: {exc}")
            continue
        if row["prev_hash"] != prev:
            breaks.append(
                f"seq={row['seq']} prev_hash mismatch "
                f"(expected {prev}, got {row['prev_hash']})"
            )
        expected = compute_hash(row)
        if row["hash"] != expected:
            breaks.append(
                f"seq={row['seq']} hash mismatch "
                f"(expected {expected}, got {row['hash']})"
            )
        if index and row["seq"] != rows[index - 1]["seq"] + 1:
            breaks.append(f"seq={row['seq']} sequence gap")
        prev = row["hash"]
    return breaks


def build_entry(
    *,
    seq: int,
    prev_hash: str,
    decision_id: str,
    timestamp_utc: str,
    actor_type: str,
    actor_email: str,
    actor_role: str,
    decision_class: str,
    title: str,
    context: str,
    authority_level: str,
    artifacts: Dict[str, str],
    rationale: str,
    falsifier: str,
) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "schema": SCHEMA_ID,
        "authority_effect": AUTHORITY_EFFECT,
        "can_authorize": CAN_AUTHORIZE,
        "advisory_only": ADVISORY_ONLY,
        "seq": seq,
        "prev_hash": prev_hash,
        "decision_id": decision_id,
        "timestamp_utc": timestamp_utc,
        "actor_type": actor_type,
        "actor_email": actor_email,
        "actor_role": actor_role,
        "decision_class": decision_class,
        "title": title,
        "context": context,
        "authority_level": authority_level,
        "artifacts": dict(artifacts),
        "rationale": rationale,
        "falsifier": falsifier,
    }
    validate_entry_shape(row, require_hash=False)
    row["hash"] = compute_hash(row)
    return row


def append_entry(path: Path, fields: Dict[str, Any]) -> Dict[str, Any]:
    with ledger_lock(path):
        rows = load_rows(path)
        breaks = verify_chain(rows)
        if breaks:
            refuse("refusing append on broken chain: " + "; ".join(breaks))
        seq = 1 if not rows else int(rows[-1]["seq"]) + 1
        prev = ZERO_HASH if not rows else rows[-1]["hash"]
        row = build_entry(seq=seq, prev_hash=prev, **fields)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
        return row


def parse_artifacts(pairs: Optional[List[str]]) -> Dict[str, str]:
    artifacts: Dict[str, str] = {}
    for item in pairs or []:
        if "=" not in item:
            refuse(f"--artifact must be key=value, got {item!r}")
        key, value = item.split("=", 1)
        if not key:
            refuse(f"--artifact key empty in {item!r}")
        artifacts[key] = value
    return artifacts


def cmd_init(args: argparse.Namespace) -> int:
    path = Path(args.ledger)
    if path.exists() and path.stat().st_size > 0:
        refuse(f"ledger already exists and is non-empty: {path}")
    row = append_entry(
        path,
        {
            "decision_id": "WITNESS-LEDGER-GENESIS",
            "timestamp_utc": args.timestamp or now_utc(),
            "actor_type": "machine",
            "actor_email": "noreply@anthropic.com",
            "actor_role": "Z1",
            "decision_class": "record",
            "title": "Witness ledger v0 genesis",
            "context": (
                "Local INTENT-OS witness ledger substrate. "
                "AUTHORITY_EFFECT=NONE; can_authorize=false. "
                "Not a Z2 ratification and not a stop-hook allowlist."
            ),
            "authority_level": "NONE",
            "artifacts": {
                "schema": str(SCHEMA_PATH.relative_to(ROOT)),
                "tool": f"{TOOL_NAME}@{TOOL_VERSION}",
            },
            "rationale": "Establish an empty hash-chained attribution store for Phase B.",
            "falsifier": "verify fails if genesis is edited, deleted, or reordered.",
        },
    )
    print(json.dumps({"ok": True, "action": "init", "seq": row["seq"], "hash": row["hash"], "ledger": str(path)}))
    return 0


def cmd_append(args: argparse.Namespace) -> int:
    path = Path(args.ledger)
    row = append_entry(
        path,
        {
            "decision_id": args.decision_id,
            "timestamp_utc": args.timestamp or now_utc(),
            "actor_type": args.actor_type,
            "actor_email": args.actor_email,
            "actor_role": args.actor_role,
            "decision_class": args.decision_class,
            "title": args.title,
            "context": args.context,
            "authority_level": args.authority_level,
            "artifacts": parse_artifacts(args.artifact),
            "rationale": args.rationale,
            "falsifier": args.falsifier,
        },
    )
    print(json.dumps({"ok": True, "action": "append", "seq": row["seq"], "hash": row["hash"], "ledger": str(path)}))
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    path = Path(args.ledger)
    rows = load_rows(path)
    breaks = verify_chain(rows)
    tip = rows[-1]["hash"] if rows else None
    payload = {
        "ok": not breaks,
        "action": "verify",
        "ledger": str(path),
        "entries": len(rows),
        "tip": tip,
        "breaks": breaks,
        "authority_effect": AUTHORITY_EFFECT,
        "can_authorize": CAN_AUTHORIZE,
    }
    print(json.dumps(payload, sort_keys=True))
    return 0 if not breaks else 1


def cmd_list(args: argparse.Namespace) -> int:
    path = Path(args.ledger)
    rows = load_rows(path)
    breaks = verify_chain(rows)
    if breaks:
        refuse("refusing list on broken chain: " + "; ".join(breaks))
    limit = args.limit
    selected = rows if limit is None or limit <= 0 else rows[-limit:]
    summary = [
        {
            "seq": row["seq"],
            "decision_id": row["decision_id"],
            "timestamp_utc": row["timestamp_utc"],
            "actor_role": row["actor_role"],
            "decision_class": row["decision_class"],
            "title": row["title"],
            "hash": row["hash"],
        }
        for row in selected
    ]
    print(json.dumps({"ok": True, "action": "list", "entries": len(rows), "shown": len(summary), "rows": summary}, sort_keys=True))
    return 0


def run_smoke_test() -> int:
    """Exercise append/verify/list and tamper detection on a temp ledger."""
    with tempfile.TemporaryDirectory() as tmp:
        led = Path(tmp) / "WITNESS_LEDGER.jsonl"
        parser = build_parser()

        def run(argv: List[str], expect_fail: bool = False) -> Tuple[int, str]:
            args = parser.parse_args(argv)
            buf = __import__("io").StringIO()
            with contextlib.redirect_stdout(buf):
                try:
                    code = args.fn(args)
                except LedgerError as exc:
                    if expect_fail:
                        return 1, str(exc)
                    raise
            if expect_fail:
                raise AssertionError(f"expected failure for {argv}, got exit {code}: {buf.getvalue()}")
            assert code == 0, (argv, buf.getvalue())
            return code, buf.getvalue()

        run(["init", "--ledger", str(led), "--timestamp", "2026-11-20T00:00:00Z"])
        run(
            [
                "append",
                "--ledger",
                str(led),
                "--decision-id",
                "Q-SMOKE-01",
                "--actor-type",
                "human",
                "--actor-email",
                "carly.r.anderson@gmail.com",
                "--actor-role",
                "Z2",
                "--decision-class",
                "ratify",
                "--title",
                "Smoke attribution",
                "--context",
                "Temp ledger only",
                "--authority-level",
                "Z2",
                "--rationale",
                "Smoke path",
                "--falsifier",
                "edit breaks verify",
                "--artifact",
                "pr=demo#0",
                "--timestamp",
                "2026-11-20T00:01:00Z",
            ]
        )
        code, out = run(["verify", "--ledger", str(led)])
        payload = json.loads(out)
        assert payload["ok"] is True and payload["entries"] == 2, payload
        code, out = run(["list", "--ledger", str(led), "--limit", "1"])
        listed = json.loads(out)
        assert listed["shown"] == 1 and listed["rows"][0]["decision_id"] == "Q-SMOKE-01"

        # Boundary refusals
        bad = {
            "decision_id": "Q-BAD",
            "timestamp_utc": "2026-11-20T00:02:00Z",
            "actor_type": "human",
            "actor_email": "carly.r.anderson@gmail.com",
            "actor_role": "Z2",
            "decision_class": "ratify",
            "title": "bad",
            "context": "bad",
            "authority_level": "Z2",
            "artifacts": {},
            "rationale": "bad",
            "falsifier": "bad",
        }
        row = build_entry(seq=99, prev_hash=ZERO_HASH, **bad)
        row["can_authorize"] = True
        try:
            validate_entry_shape(row)
            raise AssertionError("can_authorize=true should refuse")
        except LedgerError:
            pass
        row["can_authorize"] = False
        row["authority_effect"] = "GRANT"
        try:
            validate_entry_shape(row)
            raise AssertionError("authority_effect!=NONE should refuse")
        except LedgerError:
            pass

        # Tamper detection
        lines = led.read_text(encoding="utf-8").splitlines()
        obj = json.loads(lines[1])
        obj["title"] = "TAMPERED"
        lines[1] = json.dumps(obj, sort_keys=True)
        led.write_text("\n".join(lines) + "\n", encoding="utf-8")
        args = parser.parse_args(["verify", "--ledger", str(led)])
        with contextlib.redirect_stdout(__import__("io").StringIO()):
            code = args.fn(args)
        assert code == 1, "tampered ledger must fail verify"

        assert AUTHORITY_EFFECT == "NONE" and CAN_AUTHORIZE is False
        assert SCHEMA_PATH.is_file(), f"missing schema at {SCHEMA_PATH}"
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        assert schema["properties"]["authority_effect"]["const"] == "NONE"
        assert schema["properties"]["can_authorize"]["const"] is False

    print("smoke-test OK")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description=(
            "INTENT-OS witness ledger v0 — append-only attribution store "
            "(authority_effect=NONE; can_authorize=false)"
        )
    )
    ap.add_argument("--smoke-test", action="store_true")
    sub = ap.add_subparsers(dest="command")

    p = sub.add_parser("init", help="Write genesis row to an empty ledger")
    p.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    p.add_argument("--timestamp", default=None)
    p.set_defaults(fn=cmd_init)

    p = sub.add_parser("append", help="Append one attribution entry")
    p.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    p.add_argument("--decision-id", required=True)
    p.add_argument("--actor-type", required=True, choices=ACTOR_TYPES)
    p.add_argument("--actor-email", required=True)
    p.add_argument("--actor-role", required=True, choices=ACTOR_ROLES)
    p.add_argument("--decision-class", required=True, choices=DECISION_CLASSES)
    p.add_argument("--title", required=True)
    p.add_argument("--context", required=True)
    p.add_argument("--authority-level", required=True, choices=AUTHORITY_LEVELS)
    p.add_argument("--rationale", required=True)
    p.add_argument("--falsifier", required=True)
    p.add_argument("--artifact", action="append", default=[])
    p.add_argument("--timestamp", default=None)
    p.set_defaults(fn=cmd_append)

    p = sub.add_parser("verify", help="Verify hash-chain integrity")
    p.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    p.set_defaults(fn=cmd_verify)

    p = sub.add_parser("list", help="List recent entries (after verify)")
    p.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(fn=cmd_list)

    return ap


def main(argv: Optional[List[str]] = None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv)
    if args.smoke_test:
        return run_smoke_test()
    if not getattr(args, "fn", None):
        ap.print_help()
        return 2
    try:
        return args.fn(args)
    except LedgerError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
