#!/usr/bin/env python3
"""
Z2 Queue - v1.1
Builder v1.7 compliant · diagnostic_tool
HumanAIOS · S-071026-01

Supabase-backed Zone 2 queue with local JSONL fallback.

This keeps pm_z2_queue as the canonical store when SUPABASE_URL and
SUPABASE_KEY are available, but never silently drops entries if the REST
write fails. Unsynced local entries can later be retried with
--sync-pending.

Required entry fields:
  - id_slug
  - class
  - synopsis
  - zone2_ratification

Usage:
  python tools/z2_queue_v1_0.py --append entry.json --session-id S-XXX
  python tools/z2_queue_v1_0.py --status --session-id S-XXX
  python tools/z2_queue_v1_0.py --sync-pending
  python tools/z2_queue_v1_0.py --export-ratified --output-dir outputs/
  python tools/z2_queue_v1_0.py --smoke-test
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TOOL_NAME = "z2_queue"
TOOL_VERSION = "1.1.0"
TOOL_CATEGORY = "diagnostic_tool"
TOOL_ZONE = 1

DEFAULT_LOCAL_PATH = "z2_queue_fallback.jsonl"
SUPABASE_TABLE = "pm_z2_queue"
STALE_SESSION_THRESHOLD = 3
VALID_CLASSES = {"F", "IC", "H", "IC-correction"}
REQUIRED_FIELDS = ["id_slug", "class", "synopsis", "zone2_ratification"]


class SpecLoadFailed(Exception):
    """Raised when the requested input cannot be loaded."""


class SupabaseUnreachable(Exception):
    """Raised when Supabase REST access is unavailable."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_supabase_config() -> tuple[str, str]:
    """Return (url, key) from the environment."""
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_KEY", "")
    return url, key


def load_input(source: str) -> dict[str, Any]:
    """
    Load a JSON object from a file path or an inline JSON string.

    Long inline JSON strings should not be treated as filesystem paths.
    """
    path = Path(source) if len(source) < 240 else None
    if path is not None and path.exists():
        try:
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)
        except (json.JSONDecodeError, OSError) as exc:
            raise SpecLoadFailed(f"Cannot load {path}: {exc}") from exc
    else:
        try:
            data = json.loads(source)
        except json.JSONDecodeError as exc:
            raise SpecLoadFailed(
                f"Input is neither a valid path nor valid JSON: {exc}"
            ) from exc

    if not isinstance(data, dict):
        raise SpecLoadFailed("Input JSON must be an object")
    return data


def load_local_fallback(path: str) -> list[dict[str, Any]]:
    """Load JSONL fallback entries, skipping blank or invalid rows."""
    target = Path(path)
    if not target.exists():
        return []

    entries: list[dict[str, Any]] = []
    for line in target.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            entries.append(row)
    return entries


def append_local_fallback(path: str, record: dict[str, Any]) -> None:
    """Append one entry to the JSONL fallback log."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def validate_entry(entry: dict[str, Any]) -> list[str]:
    """Return missing or invalid entry fields."""
    missing = [field for field in REQUIRED_FIELDS if not entry.get(field)]
    if entry.get("class") not in VALID_CLASSES:
        missing.append("class (invalid value)")
    return missing


def supabase_upsert(entry: dict[str, Any], timeout: int = 10) -> list[Any]:
    """Upsert a queue entry into Supabase."""
    url, key = get_supabase_config()
    if not url or not key:
        raise SupabaseUnreachable("SUPABASE_URL/SUPABASE_KEY not set in environment")

    endpoint = f"{url}/rest/v1/{SUPABASE_TABLE}"
    body = json.dumps([entry], ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        method="POST",
        headers={
            "apikey": key,
            "Authorization": f"******",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=representation",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as exc:
        raise SupabaseUnreachable(str(exc)) from exc


def supabase_select(filters: str = "", timeout: int = 10) -> list[dict[str, Any]]:
    """Fetch queue entries from Supabase."""
    url, key = get_supabase_config()
    if not url or not key:
        raise SupabaseUnreachable("SUPABASE_URL/SUPABASE_KEY not set in environment")

    endpoint = f"{url}/rest/v1/{SUPABASE_TABLE}?select=*{filters}"
    request = urllib.request.Request(
        endpoint,
        headers={
            "apikey": key,
            "Authorization": f"******",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as exc:
        raise SupabaseUnreachable(str(exc)) from exc

    if not isinstance(payload, list):
        raise SupabaseUnreachable("Unexpected Supabase response payload")
    return [row for row in payload if isinstance(row, dict)]


def append_entry(
    entry: dict[str, Any],
    session_id: str,
    local_path: str = DEFAULT_LOCAL_PATH,
) -> dict[str, Any]:
    """Append one entry, preferring Supabase and falling back to local JSONL."""
    missing = validate_entry(entry)
    if missing:
        return {
            "written": False,
            "id_slug": entry.get("id_slug"),
            "reason": "missing_required_fields",
            "missing": missing,
        }

    record = {
        **entry,
        "session_first_seen": session_id,
        "compiled": bool(entry.get("compiled", False)),
    }

    try:
        supabase_upsert(record)
        append_local_fallback(
            local_path,
            {
                **record,
                "synced": True,
                "pending_sync": False,
                "logged_at": _utc_now(),
            },
        )
        return {"written": True, "target": "supabase", "id_slug": entry["id_slug"]}
    except SupabaseUnreachable as exc:
        append_local_fallback(
            local_path,
            {
                **record,
                "synced": False,
                "pending_sync": True,
                "sync_error": str(exc),
                "logged_at": _utc_now(),
            },
        )
        return {
            "written": True,
            "target": "local_fallback",
            "id_slug": entry["id_slug"],
            "warning": f"Supabase unreachable, logged locally only: {exc}",
        }


def sync_pending(local_path: str = DEFAULT_LOCAL_PATH) -> dict[str, int]:
    """Retry pending local fallback entries against Supabase."""
    entries = load_local_fallback(local_path)
    updated: list[dict[str, Any]] = []
    synced_count = 0
    failed_count = 0

    for entry in entries:
        if entry.get("synced"):
            updated.append(entry)
            continue

        clean = {
            key: value
            for key, value in entry.items()
            if key not in {"synced", "pending_sync", "sync_error", "logged_at", "resynced_at"}
        }
        try:
            supabase_upsert(clean)
            updated.append(
                {
                    **entry,
                    "synced": True,
                    "pending_sync": False,
                    "sync_error": "",
                    "resynced_at": _utc_now(),
                }
            )
            synced_count += 1
        except SupabaseUnreachable as exc:
            updated.append(
                {
                    **entry,
                    "synced": False,
                    "pending_sync": True,
                    "sync_error": str(exc),
                }
            )
            failed_count += 1

    target = Path(local_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = "\n".join(json.dumps(entry, ensure_ascii=False) for entry in updated)
    target.write_text(payload + ("\n" if updated else ""), encoding="utf-8")
    return {"synced": synced_count, "still_pending": failed_count}


def compute_status(
    entries: list[dict[str, Any]],
    current_session: str,
    source: str,
) -> dict[str, Any]:
    """Summarize queue health for the current session."""
    uncompiled = [entry for entry in entries if not entry.get("compiled")]
    sessions_seen = sorted(
        {entry.get("session_first_seen", "UNKNOWN") for entry in entries}
    )
    session_age = {session_id: index for index, session_id in enumerate(sessions_seen)}
    current_age = session_age.get(current_session, len(sessions_seen))

    stale = []
    for entry in uncompiled:
        first_seen = entry.get("session_first_seen", "UNKNOWN")
        age = current_age - session_age.get(first_seen, current_age)
        if age >= STALE_SESSION_THRESHOLD:
            stale.append(
                {
                    "id_slug": entry.get("id_slug", "UNKNOWN"),
                    "sessions_unresolved": age,
                }
            )

    return {
        "source": source,
        "total_logged": len(entries),
        "uncompiled_count": len(uncompiled),
        "compiled_count": len(entries) - len(uncompiled),
        "oldest_first": [
            entry.get("id_slug", "UNKNOWN")
            for entry in sorted(uncompiled, key=lambda item: item.get("logged_at", ""))
        ],
        "stale_flagged": stale,
    }


def get_current_queue(
    local_path: str = DEFAULT_LOCAL_PATH,
) -> tuple[list[dict[str, Any]], str]:
    """Return the best available queue view and its source label."""
    local_entries = load_local_fallback(local_path)
    try:
        remote_entries = supabase_select()
        pending_local = [entry for entry in local_entries if not entry.get("synced")]
        return remote_entries + pending_local, "supabase (+ local pending_sync entries)"
    except SupabaseUnreachable:
        return (
            local_entries,
            "LOCAL FALLBACK ONLY - Supabase unreachable, view may be incomplete",
        )


def export_ratified(local_path: str = DEFAULT_LOCAL_PATH) -> list[dict[str, Any]]:
    """Export only the ratified/publicly useful queue fields."""
    entries, _ = get_current_queue(local_path)
    keep = set(REQUIRED_FIELDS) | {
        "evidence",
        "fix_principle",
        "related_finding",
        "principles_triggered",
        "status",
    }
    return [
        {key: value for key, value in entry.items() if key in keep}
        for entry in entries
    ]


def write_report(output: Any, output_dir: str, prefix: str = "z2_queue") -> str:
    """Write JSON output to the requested directory."""
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = target_dir / f"{prefix}_{timestamp}.json"
    path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(path)


def print_summary(status: dict[str, Any]) -> None:
    """Print a concise queue summary."""
    print(f"\nSource: {status['source']}")
    print(
        f"Total logged: {status['total_logged']}  "
        f"Uncompiled: {status['uncompiled_count']}  "
        f"Compiled: {status['compiled_count']}"
    )
    if status["oldest_first"]:
        print("Oldest unresolved: " + ", ".join(status["oldest_first"]))
    for stale in status["stale_flagged"]:
        print(
            f"  WARN stale: {stale['id_slug']} unresolved "
            f"{stale['sessions_unresolved']} sessions"
        )


def run_smoke_test() -> bool:
    """Exercise local fallback and validation behavior without live credentials."""
    local_path = tempfile.mktemp(suffix=".jsonl")
    old_url = os.environ.get("SUPABASE_URL")
    old_key = os.environ.get("SUPABASE_KEY")

    try:
        os.environ.pop("SUPABASE_URL", None)
        os.environ.pop("SUPABASE_KEY", None)

        good = {
            "id_slug": "IC-CAND-SMOKE-GOOD",
            "class": "IC",
            "status": "REGISTERED",
            "synopsis": "smoke test entry",
            "zone2_ratification": "Night - S-TEST",
        }
        result_ok = append_entry(good, "S-TEST-1", local_path)
        assert result_ok["written"] is True
        assert result_ok["target"] == "local_fallback"

        bad = {
            "id_slug": "IC-CAND-SMOKE-BAD",
            "class": "IC",
            "status": "CANDIDATE",
            "synopsis": "unratified",
        }
        result_bad = append_entry(bad, "S-TEST-1", local_path)
        assert result_bad["written"] is False
        assert "zone2_ratification" in result_bad["missing"]

        local_after = load_local_fallback(local_path)
        assert any(entry["id_slug"] == "IC-CAND-SMOKE-GOOD" for entry in local_after)
        assert not any(entry["id_slug"] == "IC-CAND-SMOKE-BAD" for entry in local_after)

        exported = export_ratified(local_path)
        assert any(entry["id_slug"] == "IC-CAND-SMOKE-GOOD" for entry in exported)
        print("✓ Smoke test PASSED")
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"✗ Smoke test FAILED: {exc}")
        return False
    finally:
        if old_url is None:
            os.environ.pop("SUPABASE_URL", None)
        else:
            os.environ["SUPABASE_URL"] = old_url
        if old_key is None:
            os.environ.pop("SUPABASE_KEY", None)
        else:
            os.environ["SUPABASE_KEY"] = old_key
        if os.path.exists(local_path):
            os.remove(local_path)


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description=f"{TOOL_NAME} v{TOOL_VERSION}")
    parser.add_argument("--local-path", default=DEFAULT_LOCAL_PATH)
    parser.add_argument("--append", help="Path to entry JSON or inline JSON object")
    parser.add_argument("--session-id", default="S-UNKNOWN")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--sync-pending", action="store_true")
    parser.add_argument("--export-ratified", action="store_true")
    parser.add_argument("--output-dir", "-o", default="outputs/")
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()

    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)

    if args.append:
        try:
            entry = load_input(args.append)
        except SpecLoadFailed as exc:
            print(f"SPEC_LOAD_FAILED: {exc}", file=sys.stderr)
            sys.exit(2)

        result = append_entry(entry, args.session_id, args.local_path)
        if result["written"]:
            print(f"LOGGED [{result['target']}]: {result['id_slug']}")
            if result.get("warning"):
                print(f"WARN: {result['warning']}", file=sys.stderr)
            sys.exit(0)

        print(
            f"REJECTED: {result.get('id_slug', entry.get('id_slug', '?'))} "
            f"- {result['reason']} {result.get('missing', '')}",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.sync_pending:
        result = sync_pending(args.local_path)
        print(f"Synced: {result['synced']}  Still pending: {result['still_pending']}")
        sys.exit(0)

    if args.export_ratified:
        exported = export_ratified(args.local_path)
        out_path = write_report(exported, args.output_dir, prefix="z2_queue_export")
        print(f"Exported {len(exported)} entries -> {out_path}")
        sys.exit(0)

    if args.status:
        entries, source = get_current_queue(args.local_path)
        status = compute_status(entries, args.session_id, source)
        print_summary(status)
        sys.exit(0)

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
