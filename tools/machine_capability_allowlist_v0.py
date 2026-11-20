#!/usr/bin/env python3
"""
Builder v1.7 compliant
machine_capability_allowlist_v0.py — local INTENT-OS machine-capability allowlist.
HumanAIOS — Q-INTENT-OS-WITNESS-LEDGER-01 Phase C (local stop-hook allowlist)

Offline registry a stop-hook can query. AUTHORITY_EFFECT is NONE. can_authorize is
false. This tool does not grant merge authority, satisfy required review, sign a
ruling, or replace a Z2 hash. HTTP /api/z2-authorized-machine-identities is out of
scope (Phase D) and is not consulted by this tool.

Fail-closed: missing/invalid allowlist, missing/broken witness ledger, missing or
unbound machine capability_digest, revoked/unknown identity → DENY.

Usage:
  python3 tools/machine_capability_allowlist_v0.py verify [--allowlist PATH] [--ledger PATH]
  python3 tools/machine_capability_allowlist_v0.py list [--allowlist PATH]
  python3 tools/machine_capability_allowlist_v0.py check --identity EMAIL [--enforce]
  python3 tools/machine_capability_allowlist_v0.py stop-hook [--identity EMAIL] [--enforce]
  python3 tools/machine_capability_allowlist_v0.py --smoke-test
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

TOOL_NAME = "machine_capability_allowlist"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "governance_tool"
TOOL_ZONE = 1
TOOL_SESSION = "S-112026-intent-os-capability-allowlist"

AUTHORITY_EFFECT = "NONE"
CAN_AUTHORIZE = False
ADVISORY_ONLY = True
SCHEMA_ID = "intentos/machine_capability_allowlist_v0"

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ALLOWLIST = ROOT / "ledgers" / "MACHINE_CAPABILITY_ALLOWLIST.json"
DEFAULT_LEDGER = ROOT / "ledgers" / "WITNESS_LEDGER.jsonl"
SCHEMA_PATH = ROOT / "schemas" / "intent_os_machine_capability_allowlist_v0.schema.json"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_TS_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T")

ACTOR_TYPES = ("human", "machine")
ROLES = ("Z1", "Z2", "Z3")
STATUSES = ("active", "pending_capability_binding", "revoked")

HASHED_FIELDS = (
    "schema",
    "authority_effect",
    "can_authorize",
    "advisory_only",
    "updated_utc",
    "source_decision_ids",
    "witness_ledger",
    "require_ledger_verify",
    "http_api",
    "entries",
)


class SpecLoadFailed(Exception):
    """Raised when an allowlist or ledger file cannot be loaded or parsed."""


class AllowlistError(RuntimeError):
    """Raised when the allowlist cannot be loaded or verified."""


def canon(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compute_content_hash(doc: Dict[str, Any]) -> str:
    payload = {key: doc[key] for key in HASHED_FIELDS}
    return sha256_hex(canon(payload))


def refuse(msg: str) -> None:
    raise AllowlistError(msg)


def _import_witness_ledger():
    tools_dir = Path(__file__).resolve().parent
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))
    import witness_ledger_v0 as wl  # noqa: WPS433

    return wl


def validate_allowlist_shape(doc: Dict[str, Any]) -> None:
    if doc.get("schema") != SCHEMA_ID:
        refuse(f"schema must be {SCHEMA_ID!r}")
    if doc.get("authority_effect") != "NONE":
        refuse("authority_effect must be NONE")
    if doc.get("can_authorize") is not False:
        refuse("can_authorize must be false")
    if doc.get("advisory_only") is not True:
        refuse("advisory_only must be true")
    if not isinstance(doc.get("updated_utc"), str) or not _TS_RE.match(doc["updated_utc"]):
        refuse("updated_utc must be an ISO-8601-ish UTC timestamp")
    ids = doc.get("source_decision_ids")
    if not isinstance(ids, list) or not ids or not all(isinstance(x, str) and x for x in ids):
        refuse("source_decision_ids must be a non-empty list of strings")
    if not isinstance(doc.get("witness_ledger"), str) or not doc["witness_ledger"]:
        refuse("witness_ledger path required")
    if doc.get("require_ledger_verify") is not True:
        refuse("require_ledger_verify must be true (v0 fail-closed)")
    http = doc.get("http_api")
    if not isinstance(http, dict):
        refuse("http_api object required")
    if http.get("enabled") is not False:
        refuse("http_api.enabled must be false (Phase D not landed)")
    if http.get("path") != "/api/z2-authorized-machine-identities":
        refuse("http_api.path must be /api/z2-authorized-machine-identities")
    if not isinstance(http.get("note"), str) or not http["note"]:
        refuse("http_api.note required")
    entries = doc.get("entries")
    if not isinstance(entries, list) or not entries:
        refuse("entries must be a non-empty list")
    seen = set()
    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            refuse(f"entries[{idx}] must be an object")
        identity = entry.get("identity")
        if not isinstance(identity, str) or not _EMAIL_RE.match(identity):
            refuse(f"entries[{idx}].identity must be an email")
        key = identity.lower()
        if key in seen:
            refuse(f"duplicate identity: {identity}")
        seen.add(key)
        if entry.get("actor_type") not in ACTOR_TYPES:
            refuse(f"entries[{idx}].actor_type invalid")
        if entry.get("role") not in ROLES:
            refuse(f"entries[{idx}].role invalid")
        if entry.get("status") not in STATUSES:
            refuse(f"entries[{idx}].status invalid")
        digest = entry.get("capability_digest")
        if digest is not None and (not isinstance(digest, str) or not _SHA256_RE.match(digest)):
            refuse(f"entries[{idx}].capability_digest must be null or 64 hex")
        if not isinstance(entry.get("notes"), str) or not entry["notes"]:
            refuse(f"entries[{idx}].notes required")
    ch = doc.get("content_hash")
    if not isinstance(ch, str) or not _SHA256_RE.match(ch):
        refuse("content_hash must be 64 hex")
    expected = compute_content_hash(doc)
    if ch != expected:
        refuse(f"content_hash mismatch: file={ch} recomputed={expected}")


def write_report(output: Dict[str, Any], output_dir: str) -> str:
    """Write a JSON report under output_dir. Returns the file path."""
    dest = Path(output_dir)
    dest.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = dest / f"{TOOL_NAME}_{ts}.json"
    path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(path)


def load_allowlist(path: Path) -> Dict[str, Any]:
    if not path.exists():
        refuse(f"allowlist missing (fail-closed): {path}")
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SpecLoadFailed(f"Cannot load {path}: {exc}") from exc
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SpecLoadFailed(f"allowlist unreadable/unverifiable (fail-closed): {exc}") from exc
    if not isinstance(doc, dict):
        refuse("allowlist root must be an object")
    validate_allowlist_shape(doc)
    return doc


def resolve_ledger_path(doc: Dict[str, Any], override: Optional[Path] = None) -> Path:
    if override is not None:
        return override
    rel = doc["witness_ledger"]
    path = Path(rel)
    if not path.is_absolute():
        path = ROOT / path
    return path


def verify_witness_ledger(ledger_path: Path) -> Dict[str, Any]:
    if not ledger_path.exists():
        refuse(f"witness ledger missing (fail-closed): {ledger_path}")
    wl = _import_witness_ledger()
    try:
        rows = wl.load_rows(ledger_path)
    except Exception as exc:  # noqa: BLE001 — surface as fail-closed
        refuse(f"witness ledger unreadable (fail-closed): {exc}")
    breaks = wl.verify_chain(rows)
    if breaks:
        refuse("witness ledger chain broken (fail-closed): " + "; ".join(breaks))
    if not rows:
        refuse("witness ledger empty (fail-closed)")
    return {
        "ok": True,
        "entries": len(rows),
        "tip": rows[-1]["hash"],
        "path": str(ledger_path),
    }


def find_entry(doc: Dict[str, Any], identity: str) -> Optional[Dict[str, Any]]:
    needle = identity.strip().lower()
    for entry in doc["entries"]:
        if entry["identity"].lower() == needle:
            return entry
    return None


def decide(doc: Dict[str, Any], identity: str, *, ledger_info: Dict[str, Any]) -> Dict[str, Any]:
    """Return a structured ALLOW/DENY decision. Does not consult HTTP."""
    base = {
        "schema": SCHEMA_ID,
        "authority_effect": AUTHORITY_EFFECT,
        "can_authorize": CAN_AUTHORIZE,
        "advisory_only": ADVISORY_ONLY,
        "identity": identity,
        "http_consulted": False,
        "ledger": ledger_info,
        "allowlist_content_hash": doc["content_hash"],
    }
    if not identity or not _EMAIL_RE.match(identity):
        return {**base, "decision": "DENY", "reason": "identity missing or not an email (fail-closed)"}
    entry = find_entry(doc, identity)
    if entry is None:
        return {**base, "decision": "DENY", "reason": "identity not on local allowlist (fail-closed)"}
    if entry["status"] == "revoked":
        return {
            **base,
            "decision": "DENY",
            "reason": "identity revoked on local allowlist (fail-closed)",
            "entry": entry,
        }
    if entry["actor_type"] == "human" and entry["role"] == "Z2" and entry["status"] == "active":
        # Explicit authenticated Z2 path already ratified in dual-authority doctrine.
        return {
            **base,
            "decision": "ALLOW",
            "reason": "active human Z2 identity on local allowlist (Q-Z2-DUAL-AUTHORITY)",
            "entry": entry,
        }
    if entry["actor_type"] == "machine":
        if entry["status"] != "active":
            return {
                **base,
                "decision": "DENY",
                "reason": (
                    f"machine identity status={entry['status']!r}; "
                    "capability binding required (fail-closed)"
                ),
                "entry": entry,
            }
        digest = entry.get("capability_digest")
        if not digest:
            return {
                **base,
                "decision": "DENY",
                "reason": "machine identity active but capability_digest unbound (fail-closed)",
                "entry": entry,
            }
        return {
            **base,
            "decision": "ALLOW",
            "reason": "active machine identity with capability_digest on local allowlist",
            "entry": entry,
        }
    return {
        **base,
        "decision": "DENY",
        "reason": (
            f"no allow rule for actor_type={entry['actor_type']!r} "
            f"role={entry['role']!r} status={entry['status']!r} (fail-closed)"
        ),
        "entry": entry,
    }


def verify_bundle(
    allowlist_path: Path, ledger_path: Optional[Path] = None
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    doc = load_allowlist(allowlist_path)
    led = resolve_ledger_path(doc, ledger_path)
    ledger_info = verify_witness_ledger(led)
    return doc, ledger_info


def cmd_verify(args: argparse.Namespace) -> int:
    try:
        doc, ledger_info = verify_bundle(Path(args.allowlist), Path(args.ledger) if args.ledger else None)
    except AllowlistError as exc:
        print(json.dumps({"ok": False, "action": "verify", "error": str(exc)}, sort_keys=True))
        return 1
    print(
        json.dumps(
            {
                "ok": True,
                "action": "verify",
                "allowlist": str(args.allowlist),
                "content_hash": doc["content_hash"],
                "entries": len(doc["entries"]),
                "ledger": ledger_info,
                "authority_effect": AUTHORITY_EFFECT,
                "can_authorize": CAN_AUTHORIZE,
                "http_api_enabled": doc["http_api"]["enabled"],
            },
            sort_keys=True,
        )
    )
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    try:
        doc, ledger_info = verify_bundle(Path(args.allowlist), Path(args.ledger) if args.ledger else None)
    except AllowlistError as exc:
        print(json.dumps({"ok": False, "action": "list", "error": str(exc)}, sort_keys=True))
        return 1
    rows = [
        {
            "identity": e["identity"],
            "actor_type": e["actor_type"],
            "role": e["role"],
            "status": e["status"],
            "capability_digest": e["capability_digest"],
        }
        for e in doc["entries"]
    ]
    print(
        json.dumps(
            {
                "ok": True,
                "action": "list",
                "entries": rows,
                "ledger": ledger_info,
                "content_hash": doc["content_hash"],
            },
            sort_keys=True,
        )
    )
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    identity = args.identity
    try:
        doc, ledger_info = verify_bundle(Path(args.allowlist), Path(args.ledger) if args.ledger else None)
        result = decide(doc, identity, ledger_info=ledger_info)
    except AllowlistError as exc:
        result = {
            "decision": "DENY",
            "reason": str(exc),
            "identity": identity,
            "http_consulted": False,
            "authority_effect": AUTHORITY_EFFECT,
            "can_authorize": CAN_AUTHORIZE,
        }
        print(json.dumps({"ok": False, "action": "check", **result}, sort_keys=True))
        return 1
    allowed = result["decision"] == "ALLOW"
    payload = {"ok": allowed, "action": "check", **result}
    print(json.dumps(payload, sort_keys=True))
    if args.enforce:
        return 0 if allowed else 1
    # Non-enforce: still report, but exit 0 so callers that only want JSON can parse.
    return 0


def resolve_stop_hook_identity(explicit: Optional[str]) -> str:
    if explicit:
        return explicit.strip()
    for key in (
        "INTENTOS_ACTOR_EMAIL",
        "GIT_AUTHOR_EMAIL",
        "GIT_COMMITTER_EMAIL",
        "GITHUB_ACTOR_EMAIL",
    ):
        val = os.environ.get(key, "").strip()
        if val:
            return val
    return ""


def cmd_stop_hook(args: argparse.Namespace) -> int:
    """Stop-hook integration entrypoint.

    Default is report-only (exit 0) so Claude Code Stop events still complete.
    Set --enforce or INTENTOS_STOP_HOOK_ENFORCE=1 for fail-closed exit codes.
    """
    enforce = bool(args.enforce) or os.environ.get("INTENTOS_STOP_HOOK_ENFORCE", "") == "1"
    identity = resolve_stop_hook_identity(args.identity)
    try:
        doc, ledger_info = verify_bundle(Path(args.allowlist), Path(args.ledger) if args.ledger else None)
        result = decide(doc, identity, ledger_info=ledger_info)
        ok_load = True
        error = None
    except AllowlistError as exc:
        ok_load = False
        error = str(exc)
        result = {
            "decision": "DENY",
            "reason": error,
            "identity": identity or None,
            "http_consulted": False,
            "authority_effect": AUTHORITY_EFFECT,
            "can_authorize": CAN_AUTHORIZE,
        }
    payload = {
        "ok": ok_load and result["decision"] == "ALLOW",
        "action": "stop-hook",
        "enforce": enforce,
        "integration": {
            "claude_code_stop": ".claude/settings.json hooks.Stop",
            "ci_hardcoded_z2": ".github/workflows/z2_ratification_gate.yml (advisory authorship check)",
            "local_query": "tools/machine_capability_allowlist_v0.py check|stop-hook",
            "http_api": "not consulted (Phase D)",
        },
        **result,
    }
    if error:
        payload["error"] = error
    print(json.dumps(payload, sort_keys=True))
    if enforce:
        return 0 if payload["ok"] else 1
    return 0


def build_seed_doc() -> Dict[str, Any]:
    doc: Dict[str, Any] = {
        "schema": SCHEMA_ID,
        "authority_effect": "NONE",
        "can_authorize": False,
        "advisory_only": True,
        "updated_utc": "2026-11-20T19:45:00Z",
        "source_decision_ids": [
            "Q-Z2-DUAL-AUTHORITY-GOVERNANCE-01",
            "Q-INTENT-OS-WITNESS-LEDGER-01",
        ],
        "witness_ledger": "ledgers/WITNESS_LEDGER.jsonl",
        "require_ledger_verify": True,
        "http_api": {
            "enabled": False,
            "path": "/api/z2-authorized-machine-identities",
            "note": "Phase D — local stop-hook must not depend on HTTP; fail closed offline.",
        },
        "entries": [
            {
                "identity": "carly.r.anderson@gmail.com",
                "actor_type": "human",
                "role": "Z2",
                "status": "active",
                "capability_digest": None,
                "notes": "Canonical Z2 identity per Q-Z2-DUAL-AUTHORITY-GOVERNANCE-01 / CLAUDE.md",
            },
            {
                "identity": "aioshuman@gmail.com",
                "actor_type": "human",
                "role": "Z2",
                "status": "active",
                "capability_digest": None,
                "notes": "Authorized business Z2 identity per Q-Z2-DUAL-AUTHORITY-GOVERNANCE-01",
            },
            {
                "identity": "noreply@anthropic.com",
                "actor_type": "machine",
                "role": "Z3",
                "status": "pending_capability_binding",
                "capability_digest": None,
                "notes": (
                    "CLAUDE.md lists this machine identity as pending INTENT-OS Phase 1 "
                    "binding. Stop-hook DENY until status=active and capability_digest set."
                ),
            },
        ],
    }
    doc["content_hash"] = compute_content_hash(doc)
    return doc


def run_smoke_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        allowlist = tmp_path / "MACHINE_CAPABILITY_ALLOWLIST.json"
        ledger = tmp_path / "WITNESS_LEDGER.jsonl"

        wl = _import_witness_ledger()
        parser_wl = wl.build_parser()
        assert (
            wl.cmd_init(
                parser_wl.parse_args(
                    ["init", "--ledger", str(ledger), "--timestamp", "2026-11-20T12:00:00Z"]
                )
            )
            == 0
        )

        doc = build_seed_doc()
        doc["witness_ledger"] = str(ledger)
        doc["content_hash"] = compute_content_hash(doc)
        allowlist.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        loaded, ledger_info = verify_bundle(allowlist, ledger)
        assert ledger_info["ok"] is True

        z2 = decide(loaded, "carly.r.anderson@gmail.com", ledger_info=ledger_info)
        assert z2["decision"] == "ALLOW", z2

        machine = decide(loaded, "noreply@anthropic.com", ledger_info=ledger_info)
        assert machine["decision"] == "DENY", machine
        assert "capability" in machine["reason"].lower() or "pending" in machine["reason"].lower()

        unknown = decide(loaded, "stranger@example.com", ledger_info=ledger_info)
        assert unknown["decision"] == "DENY", unknown

        # Missing allowlist → fail closed
        try:
            load_allowlist(tmp_path / "missing.json")
            raise AssertionError("missing allowlist must refuse")
        except AllowlistError:
            pass

        # Tampered content_hash → fail closed
        bad = json.loads(allowlist.read_text(encoding="utf-8"))
        bad["content_hash"] = "0" * 64
        allowlist.write_text(json.dumps(bad, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        try:
            load_allowlist(allowlist)
            raise AssertionError("tampered allowlist must refuse")
        except AllowlistError:
            pass

        # Broken ledger → fail closed
        allowlist.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        lines = ledger.read_text(encoding="utf-8").splitlines()
        obj = json.loads(lines[0])
        obj["title"] = "TAMPERED"
        ledger.write_text(json.dumps(obj, sort_keys=True) + "\n", encoding="utf-8")
        try:
            verify_bundle(allowlist, ledger)
            raise AssertionError("broken ledger must refuse")
        except AllowlistError:
            pass

        # Bound machine ALLOW path
        allowlist.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        # rebuild clean ledger
        ledger.write_text("", encoding="utf-8")
        assert (
            wl.cmd_init(
                parser_wl.parse_args(
                    ["init", "--ledger", str(ledger), "--timestamp", "2026-11-20T12:00:00Z"]
                )
            )
            == 0
        )
        bound = json.loads(json.dumps(doc))
        for entry in bound["entries"]:
            if entry["identity"] == "noreply@anthropic.com":
                entry["status"] = "active"
                entry["capability_digest"] = "a" * 64
        bound["content_hash"] = compute_content_hash(bound)
        allowlist.write_text(json.dumps(bound, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        loaded2, info2 = verify_bundle(allowlist, ledger)
        assert decide(loaded2, "noreply@anthropic.com", ledger_info=info2)["decision"] == "ALLOW"

        assert AUTHORITY_EFFECT == "NONE" and CAN_AUTHORIZE is False
        assert SCHEMA_PATH.is_file(), f"missing schema at {SCHEMA_PATH}"
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        assert schema["properties"]["authority_effect"]["const"] == "NONE"
        assert schema["properties"]["can_authorize"]["const"] is False
        assert schema["properties"]["http_api"]["properties"]["enabled"]["const"] is False

    print("smoke-test OK")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description=(
            "INTENT-OS machine capability allowlist v0 — local offline stop-hook "
            "registry (authority_effect=NONE; can_authorize=false; fail-closed)"
        )
    )
    ap.add_argument("--smoke-test", action="store_true")
    sub = ap.add_subparsers(dest="command")

    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--allowlist", default=str(DEFAULT_ALLOWLIST))
        p.add_argument(
            "--ledger",
            default=None,
            help="Override witness ledger path (default: path recorded in allowlist)",
        )

    p = sub.add_parser("verify", help="Verify allowlist content_hash + witness ledger chain")
    add_common(p)
    p.set_defaults(fn=cmd_verify)

    p = sub.add_parser("list", help="List allowlist entries after verify")
    add_common(p)
    p.set_defaults(fn=cmd_list)

    p = sub.add_parser("check", help="Decide ALLOW/DENY for one identity (fail-closed)")
    add_common(p)
    p.add_argument("--identity", required=True)
    p.add_argument(
        "--enforce",
        action="store_true",
        help="Exit 1 on DENY (default: print JSON and exit 0)",
    )
    p.set_defaults(fn=cmd_check)

    p = sub.add_parser(
        "stop-hook",
        help="Stop-hook entrypoint (report-only unless --enforce or INTENTOS_STOP_HOOK_ENFORCE=1)",
    )
    add_common(p)
    p.add_argument(
        "--identity",
        default=None,
        help="Override identity; else INTENTOS_ACTOR_EMAIL / GIT_AUTHOR_EMAIL / …",
    )
    p.add_argument("--enforce", action="store_true")
    p.set_defaults(fn=cmd_stop_hook)

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
    except SpecLoadFailed as exc:
        print(json.dumps({"ok": False, "error": f"SPEC_LOAD_FAILED: {exc}"}), file=sys.stderr)
        return 2
    except AllowlistError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
