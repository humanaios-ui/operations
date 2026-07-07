"""
HumanAIOS — Supabase Logger (Zone 1)
Builder v1.7 compliant

Logs notifications to Supabase with idempotent upsert (claim-then-act pattern).
Uses stdlib urllib to POST/UPSERT into Supabase REST API. No supabase-py needed.

CLI:
  python supabase_logger.py --input fixture.json --report out.json
  python supabase_logger.py --smoke
MCP:
  fastmcp run supabase_logger.py --serve
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Builder v1.7 constants
# ---------------------------------------------------------------------------
TOOL_NAME = "supabase_logger"
TOOL_VERSION = "1.1.0"
TOOL_CATEGORY = "dispatch"
TOOL_SESSION = "S-052326-03"

# ---------------------------------------------------------------------------
# Configuration (override via env)
# ---------------------------------------------------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")  # service_role key
SUPABASE_TABLE = os.getenv("SUPABASE_TABLE", "notification_log")
POST_TIMEOUT = int(os.getenv("POST_TIMEOUT", "15"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
BACKOFF_BASE = float(os.getenv("BACKOFF_BASE", "2.0"))

# ---------------------------------------------------------------------------
# Required env vars for live Supabase calls
# ---------------------------------------------------------------------------
_REQUIRED_ENV_LIVE = ["SUPABASE_URL", "SUPABASE_KEY"]


# ---------------------------------------------------------------------------
# Security helpers
# ---------------------------------------------------------------------------
def redact_for_log(s: str) -> str:
    """Replace sensitive credential patterns with ***REDACTED*** before logging."""
    # Supabase service_role / anon keys (JWT eyJ… or sb_… prefix)
    s = re.sub(r"eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+", "***REDACTED***", s)
    s = re.sub(r"sb_[A-Za-z0-9_\-]{20,}", "***REDACTED***", s)
    # Slack webhook URL path tokens
    s = re.sub(
        r"hooks\.slack\.com/services/[A-Za-z0-9/]+",
        "hooks.slack.com/services/***REDACTED***",
        s,
    )
    # Supabase project URL tokens (strip key param if embedded)
    s = re.sub(r"(apikey=)[A-Za-z0-9_\-\.]+", r"\1***REDACTED***", s)
    return s


# ---------------------------------------------------------------------------
# Startup env validation (warns only — never raises, never exits)
# ---------------------------------------------------------------------------
def validate_env() -> None:
    """
    Check required env vars. Print WARNING to stderr if any are missing.
    Values are never printed. Safe to call at import time.
    """
    missing = [v for v in _REQUIRED_ENV_LIVE if not os.getenv(v)]
    if missing:
        print(
            f"[{TOOL_NAME}] WARNING: missing env vars: {', '.join(missing)}. "
            "Live Supabase upsert will fail; use dry_run=True for testing.",
            file=sys.stderr,
        )


validate_env()


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------
class SpecLoadFailed(Exception):
    """Raised when input spec cannot be loaded or validated."""


class SupabaseInsertFailed(Exception):
    """Raised when Supabase upsert fails permanently."""


# ---------------------------------------------------------------------------
# Input / output helpers
# ---------------------------------------------------------------------------
def load_input(path: str | None) -> dict:
    """Load input spec from JSON file or stdin."""
    if path is None or path == "-":
        raw = sys.stdin.read()
    else:
        if not os.path.isfile(path):
            raise SpecLoadFailed(f"Input file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()
    if not raw.strip():
        raise SpecLoadFailed("Empty input")
    try:
        spec = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SpecLoadFailed(f"Invalid JSON: {exc}") from exc
    if not isinstance(spec, dict):
        raise SpecLoadFailed("Input JSON must be an object")
    return spec


def write_report(out: dict, path: str) -> None:
    """Write report JSON atomically."""
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, default=str)
        f.write("\n")
    os.replace(tmp, path)


def print_summary(out: dict) -> None:
    """Human-readable summary to stderr (safe for MCP stdio)."""
    status = out.get("status", "UNKNOWN")
    action = out.get("action", "?")
    dedup_key = out.get("dedup_key", "?")
    short_key = dedup_key[:16] + "…" if len(str(dedup_key)) > 16 else dedup_key
    print(f"[{TOOL_NAME} v{TOOL_VERSION}] status={status} action={action} key={short_key}",
          file=sys.stderr)


# ---------------------------------------------------------------------------
# Idempotency key generation
# ---------------------------------------------------------------------------
def make_dedup_key(
    tool_name: str,
    session_id: str,
    event_type: str,
    payload_fields: str,
    day_bucket: str | None = None,
) -> str:
    """
    Generate a stable dedup key.

    Args:
        tool_name: Source tool name.
        session_id: Session identifier.
        event_type: Event classification.
        payload_fields: Canonicalized string of key payload fields.
        day_bucket: Date bucket (YYYYMMDD) for daily granularity.

    Returns:
        hex-encoded SHA-256 hash.
    """
    if day_bucket is None:
        day_bucket = datetime.now(timezone.utc).strftime("%Y%m%d")
    raw = f"{tool_name}|{session_id}|{event_type}|{payload_fields}|{day_bucket}"
    return hashlib.sha256(raw.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Supabase REST helpers (stdlib urllib, no supabase-py)
# ---------------------------------------------------------------------------
def _supabase_headers() -> dict[str, str]:
    """Build required Supabase REST headers."""
    key = SUPABASE_KEY
    if not key:
        raise SupabaseInsertFailed("SUPABASE_KEY not configured")
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=representation",
    }


def _request_with_retry(
    req: urllib.request.Request,
    max_retries: int = MAX_RETRIES,
) -> dict:
    """
    Execute urllib request with bounded exponential backoff.

    Returns:
        Parsed JSON response.

    Raises:
        SupabaseInsertFailed on permanent failure.
    """
    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=POST_TIMEOUT) as resp:
                body = resp.read().decode("utf-8")
                if not body:
                    return {}
                return json.loads(body)
        except urllib.error.HTTPError as exc:
            last_error = exc
            body = ""
            try:
                body = exc.read().decode("utf-8", errors="replace")[:1000]
            except Exception:  # noqa: BLE001
                pass

            # 429 -> rate limited
            if exc.code == 429:
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
                sleep_time = (
                    int(retry_after)
                    if retry_after
                    else min(60, BACKOFF_BASE ** attempt + random.random())
                )
                print(f"[supabase] Rate limited, retrying after {sleep_time}s", file=sys.stderr)
                time.sleep(sleep_time)
                continue

            # 5xx -> server error, retry
            if exc.code in (500, 502, 503, 504):
                sleep_time = min(60, BACKOFF_BASE ** attempt + random.random())
                print(
                    f"[supabase] Server error {exc.code}, attempt {attempt + 1}/{max_retries}",
                    file=sys.stderr,
                )
                time.sleep(sleep_time)
                continue

            # Other 4xx are permanent — redact before logging
            safe_body = redact_for_log(body)
            raise SupabaseInsertFailed(f"Supabase HTTP {exc.code}: {safe_body}") from exc

        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            sleep_time = min(60, BACKOFF_BASE ** attempt + random.random())
            print(
                f"[supabase] Request failed ({exc}), attempt {attempt + 1}/{max_retries}",
                file=sys.stderr,
            )
            time.sleep(sleep_time)

    raise SupabaseInsertFailed(
        f"Failed after {max_retries} attempts: {last_error}"
    ) from last_error


def upsert_notification(row: dict) -> dict:
    """
    Upsert a notification row using claim-then-act pattern.

    POST with on_conflict=dedup_key + Prefer: resolution=merge-duplicates.
    Returns the row (existing or new) so caller can detect first-time insert.
    """
    if not SUPABASE_URL:
        raise SupabaseInsertFailed("SUPABASE_URL not configured")

    url = (
        f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}"
        f"?on_conflict=dedup_key"
    )
    headers = _supabase_headers()
    data = json.dumps([row]).encode("utf-8")  # Body is a JSON array

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    result = _request_with_retry(req)

    # Result is a list of rows
    if isinstance(result, list) and len(result) > 0:
        return result[0]
    return result  # type: ignore[return-value]


def patch_notification_status(
    row_id: str,
    slack_status: str,
    slack_ts: str | None = None,
    slack_response: str | None = None,
) -> dict:
    """
    PATCH notification row with Slack delivery status.
    """
    if not SUPABASE_URL:
        raise SupabaseInsertFailed("SUPABASE_URL not configured")

    url = f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}?id=eq.{row_id}"
    # Build headers manually to avoid including key in error messages
    key = SUPABASE_KEY
    if not key:
        raise SupabaseInsertFailed("SUPABASE_KEY not configured")
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    patch_body: dict[str, Any] = {"slack_status": slack_status}
    if slack_ts is not None:
        patch_body["slack_ts"] = slack_ts
    if slack_response is not None:
        patch_body["slack_response"] = slack_response

    data = json.dumps(patch_body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="PATCH")
    return _request_with_retry(req)


# ---------------------------------------------------------------------------
# Core business logic — claim-then-act pattern
# ---------------------------------------------------------------------------
def run(spec: dict) -> dict:
    """
    Log notification to Supabase with idempotent upsert.

    Args:
        spec: Input spec with keys:
            - tool_name, session_id, event_type, payload
            - slack_status: initial status ('pending', 'sent', 'failed')
            - dry_run: if true, compute dedup_key without inserting
            - skip_slack: if true, only upsert log row, don't call Slack

    Returns:
        Result dict with status, action (inserted/cached), dedup_key, row.
    """
    started = datetime.now(timezone.utc).isoformat()
    dry_run = spec.get("dry_run", False)

    # Build payload and dedup key
    tool_name = spec.get("tool_name", "unknown")
    session_id = spec.get("session_id", "default")
    event_type = spec.get("event_type", "notification")
    payload = spec.get("payload", {})
    payload_fields = json.dumps(payload, sort_keys=True, default=str)

    dedup_key = make_dedup_key(
        tool_name=tool_name,
        session_id=session_id,
        event_type=event_type,
        payload_fields=payload_fields,
    )

    if dry_run:
        return {
            "tool_name": TOOL_NAME,
            "tool_version": TOOL_VERSION,
            "status": "ok",
            "action": "dry_run",
            "dedup_key": dedup_key,
            "started_at": started,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "row": None,
        }

    # Build row for upsert
    row = {
        "dedup_key": dedup_key,
        "tool_name": tool_name,
        "session_id": session_id,
        "payload": payload,
        "slack_status": spec.get("slack_status", "pending"),
    }

    try:
        # Step 1: Claim the dedup_key (upsert)
        returned = upsert_notification(row)
        created_at = returned.get("created_at", "")
        updated_at = returned.get("updated_at", "")

        # Step 2: Determine if this was first insert or duplicate
        is_new = True
        if created_at and updated_at and created_at != updated_at:
            is_new = False

        action = "inserted" if is_new else "cached"

        return {
            "tool_name": TOOL_NAME,
            "tool_version": TOOL_VERSION,
            "status": "ok",
            "action": action,
            "dedup_key": dedup_key,
            "row_id": returned.get("id"),
            "started_at": started,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "row": returned,
        }

    except SupabaseInsertFailed as exc:
        return {
            "tool_name": TOOL_NAME,
            "tool_version": TOOL_VERSION,
            "status": "failed",
            "action": "error",
            "dedup_key": dedup_key,
            "error": redact_for_log(str(exc)),
            "started_at": started,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "row": None,
        }


def aggregate(results: list[dict]) -> dict:
    """Aggregate multiple run results."""
    statuses = [r.get("status") for r in results]
    ok_count = statuses.count("ok")
    actions = [r.get("action") for r in results]
    inserted = actions.count("inserted")
    cached = actions.count("cached")
    return {
        "tool_name": TOOL_NAME,
        "tool_version": TOOL_VERSION,
        "aggregate": True,
        "total": len(results),
        "ok": ok_count,
        "failed": len(results) - ok_count,
        "inserted": inserted,
        "cached": cached,
        "results": results,
    }


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------
def run_smoke_test() -> bool:
    """Validate dedup key generation and row building without network."""
    try:
        # Test 1: dedup key stability
        key1 = make_dedup_key("test_tool", "s1", "evt", json.dumps({"a": 1}))
        key2 = make_dedup_key("test_tool", "s1", "evt", json.dumps({"a": 1}))
        assert key1 == key2, f"Dedup key not stable: {key1} != {key2}"

        # Test 2: different inputs -> different keys
        key3 = make_dedup_key("test_tool", "s2", "evt", json.dumps({"a": 1}))
        assert key1 != key3, "Dedup key should differ for different session"

        # Test 3: dry_run mode
        sample = {
            "tool_name": "backup_check",
            "session_id": "2026-05-24-night",
            "event_type": "failure",
            "payload": {"exit_code": 1, "stderr": "disk full"},
            "slack_status": "pending",
            "dry_run": True,
        }
        out = run(sample)
        assert out.get("status") == "ok", f"Unexpected status: {out.get('status')}"
        assert out.get("action") == "dry_run", f"Unexpected action: {out.get('action')}"
        assert len(out["dedup_key"]) == 64, "SHA-256 should be 64 hex chars"

        # Test 4: redact_for_log doesn't expose keys
        sample_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        redacted = redact_for_log(f"apikey={sample_key}")
        assert sample_key not in redacted, "JWT key not redacted"

        print("[smoke] PASSED", file=sys.stderr)
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"[smoke] FAILED: {exc}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# MCP surface
# ---------------------------------------------------------------------------
from fastmcp import FastMCP  # noqa: E402

mcp = FastMCP(TOOL_NAME)


@mcp.tool(
    name=TOOL_NAME,
    description=(
        "Log a notification to Supabase with idempotent upsert. "
        "Returns 'inserted' on first write, 'cached' on duplicate. "
        "Use dedup_key in spec to control idempotency."
    ),
)
def supabase_logger(spec: dict) -> dict:
    """MCP tool wrapper around run()."""
    return run(spec)


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------
def main() -> None:
    p = argparse.ArgumentParser(description=f"{TOOL_NAME} v{TOOL_VERSION}")
    p.add_argument("--input", required=False, help="Path to input JSON (default: stdin)")
    p.add_argument("--smoke", action="store_true", help="Run smoke test and exit")
    p.add_argument("--serve", action="store_true", help="Run as MCP server over stdio")
    p.add_argument("--report", default=f"reports/{TOOL_NAME}.json", help="Report output path")
    args = p.parse_args()

    if args.serve:
        mcp.run()
        return

    if args.smoke:
        sys.exit(0 if run_smoke_test() else 1)

    spec = load_input(args.input)
    out = run(spec)
    write_report(out, args.report)
    print_summary(out)


if __name__ == "__main__":
    main()
