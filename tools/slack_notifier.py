"""
HumanAIOS — Slack Notifier (Zone 1)

Dispatches Slack notifications via incoming webhook using stdlib urllib.
Uses Block Kit for structured messages. Exposed as MCP tool.

CLI:
  python slack_notifier.py --input fixture.json --report out.json
  python slack_notifier.py --smoke
MCP:
  fastmcp run slack_notifier.py --serve
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Builder v1.7 constants
# ---------------------------------------------------------------------------
TOOL_NAME = "slack_notifier"
TOOL_VERSION = "1.1.0"
TOOL_CATEGORY = "dispatch"
TOOL_SESSION = "S-052326-03"

# ---------------------------------------------------------------------------
# Configuration (override via env)
# ---------------------------------------------------------------------------
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
POST_TIMEOUT = int(os.getenv("POST_TIMEOUT", "10"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
BACKOFF_BASE = float(os.getenv("BACKOFF_BASE", "2.0"))

# ---------------------------------------------------------------------------
# Required env vars for live dispatch
# ---------------------------------------------------------------------------
_REQUIRED_ENV_LIVE = ["SLACK_WEBHOOK_URL"]


# ---------------------------------------------------------------------------
# Security helpers
# ---------------------------------------------------------------------------
def redact_for_log(s: str) -> str:
    """Replace sensitive credential patterns with ***REDACTED*** before logging."""
    # Slack webhook URL path tokens
    s = re.sub(
        r"hooks\.slack\.com/services/[A-Za-z0-9/]+",
        "hooks.slack.com/services/***REDACTED***",
        s,
    )
    # Supabase keys (JWT eyJ… or sb_… prefix)
    s = re.sub(r"eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+", "***REDACTED***", s)
    s = re.sub(r"sb_[A-Za-z0-9_\-]{20,}", "***REDACTED***", s)
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
            "Live Slack dispatch will fail; use dry_run=True for testing.",
            file=sys.stderr,
        )


validate_env()


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------
class SpecLoadFailed(Exception):
    """Raised when input spec cannot be loaded or validated."""


class SlackDispatchFailed(Exception):
    """Raised when Slack webhook returns non-200 or non-'ok'."""


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
    slack_status = out.get("slack_status", "?")
    print(f"[{TOOL_NAME} v{TOOL_VERSION}] status={status} slack={slack_status}",
          file=sys.stderr)


# ---------------------------------------------------------------------------
# Slack payload builders
# ---------------------------------------------------------------------------
def build_blocks(spec: dict) -> dict:
    """Build Slack Block Kit payload from spec."""
    tool_name = spec.get("tool_name", TOOL_NAME)
    tool_version = spec.get("tool_version", "?")
    session = spec.get("session_id", "unknown")
    status = spec.get("event_status", "INFO")
    title = spec.get("title", f"{tool_name} notification")
    message = spec.get("message", "")
    fields = spec.get("fields", [])
    dedup_key = spec.get("dedup_key", "")
    run_url = spec.get("run_url", "")

    # Emoji mapping for status
    emoji_map = {
        "ERROR": "🔴",
        "WARN": "🟡",
        "OK": "🟢",
        "INFO": "🔵",
    }
    emoji = emoji_map.get(status.upper(), "⚪")

    blocks: list[dict] = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{emoji} {title}",
            },
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Tool:*\n{tool_name} v{tool_version}"},
                {"type": "mrkdwn", "text": f"*Session:*\n{session}"},
                {"type": "mrkdwn", "text": f"*Status:*\n{status.upper()}"},
            ],
        },
    ]

    # Add custom fields
    for field in fields:
        if blocks[-1].get("type") == "section" and "fields" in blocks[-1]:
            blocks[-1]["fields"].append({
                "type": "mrkdwn",
                "text": f"*{field.get('title', 'Field')}:*\n{field.get('value', '')}",
            })

    # Add message body if present
    if message:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": message},
        })

    # Add context footer
    footer_text = ""
    if dedup_key:
        short_key = dedup_key[:16] + "…" if len(dedup_key) > 16 else dedup_key
        footer_text += f"dedup_key: `{short_key}`"
    if run_url:
        footer_text += f" · <{run_url}|Open run>" if footer_text else f"<{run_url}|Open run>"

    if footer_text:
        blocks.append({
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": footer_text}],
        })

    # Fallback text (for notifications / accessibility)
    fallback_text = f"{TOOL_SESSION}: {tool_name} {status}"

    return {"text": fallback_text, "blocks": blocks}


# ---------------------------------------------------------------------------
# Slack dispatch (stdlib urllib, no SDK)
# ---------------------------------------------------------------------------
def post_slack(payload: dict, webhook_url: str | None = None) -> dict:
    """
    POST payload to Slack incoming webhook.

    Returns:
        {"slack_status": "sent", "slack_response": "ok"} on success.

    Raises:
        SlackDispatchFailed on non-200 or non-'ok' response.
    """
    url = webhook_url or SLACK_WEBHOOK_URL
    if not url:
        raise SlackDispatchFailed("SLACK_WEBHOOK_URL not configured")

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
    )

    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=POST_TIMEOUT) as resp:
                body = resp.read().decode("utf-8")
                if resp.status == 200 and body == "ok":
                    return {"slack_status": "sent", "slack_response": body}
                raise SlackDispatchFailed(
                    f"Slack returned {resp.status}: {body}"
                )
        except urllib.error.HTTPError as exc:
            last_error = exc
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            if retry_after:
                sleep_time = int(retry_after)
            else:
                sleep_time = min(60, BACKOFF_BASE ** attempt + random.random())

            body = ""
            try:
                body = exc.read().decode("utf-8", errors="replace")[:500]
            except Exception:  # noqa: BLE001
                pass
            error_msg = redact_for_log(f"Slack HTTP {exc.code}: {body}")

            if exc.code == 429:
                print(f"[slack] Rate limited, retrying after {sleep_time}s", file=sys.stderr)
            elif exc.code in (500, 502, 503, 504):
                print(
                    f"[slack] Server error {exc.code}, attempt {attempt + 1}/{MAX_RETRIES}",
                    file=sys.stderr,
                )
            else:
                raise SlackDispatchFailed(error_msg) from exc

            time.sleep(sleep_time)

        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            sleep_time = min(60, BACKOFF_BASE ** attempt + random.random())
            print(
                f"[slack] Request failed ({exc}), attempt {attempt + 1}/{MAX_RETRIES}",
                file=sys.stderr,
            )
            time.sleep(sleep_time)

    raise SlackDispatchFailed(
        f"Failed after {MAX_RETRIES} attempts: {last_error}"
    ) from last_error


# ---------------------------------------------------------------------------
# Core business logic
# ---------------------------------------------------------------------------
def run(spec: dict) -> dict:
    """
    Dispatch Slack notification.

    Args:
        spec: Input spec with keys:
            - webhook_url: override SLACK_WEBHOOK_URL
            - title, message, tool_name, tool_version, session_id
            - event_status: ERROR | WARN | OK | INFO
            - fields: list of {title, value} for Block Kit sections
            - dedup_key, run_url
            - dry_run: if true, return payload without posting

    Returns:
        Result dict with status, slack_status, payload.
    """
    started = datetime.now(timezone.utc).isoformat()
    dry_run = spec.get("dry_run", False)

    try:
        payload = build_blocks(spec)

        if dry_run:
            result = {
                "slack_status": "dry_run",
                "slack_response": None,
                "payload": payload,
            }
        else:
            webhook = spec.get("webhook_url") or SLACK_WEBHOOK_URL
            slack_result = post_slack(payload, webhook_url=webhook)
            result = {
                "slack_status": slack_result["slack_status"],
                "slack_response": slack_result["slack_response"],
                "payload": payload,
            }

        finished = datetime.now(timezone.utc).isoformat()
        return {
            "tool_name": TOOL_NAME,
            "tool_version": TOOL_VERSION,
            "status": "ok",
            "started_at": started,
            "finished_at": finished,
            **result,
        }

    except SlackDispatchFailed as exc:
        finished = datetime.now(timezone.utc).isoformat()
        return {
            "tool_name": TOOL_NAME,
            "tool_version": TOOL_VERSION,
            "status": "failed",
            "started_at": started,
            "finished_at": finished,
            "error": redact_for_log(str(exc)),
            "slack_status": "failed",
        }


def aggregate(results: list[dict]) -> dict:
    """Aggregate multiple run results."""
    statuses = [r.get("status") for r in results]
    ok_count = statuses.count("ok")
    return {
        "tool_name": TOOL_NAME,
        "tool_version": TOOL_VERSION,
        "aggregate": True,
        "total": len(results),
        "ok": ok_count,
        "failed": len(results) - ok_count,
        "results": results,
    }


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------
def run_smoke_test() -> bool:
    """Validate payload building without network."""
    try:
        sample = {
            "title": "smoke_test",
            "message": "Smoke test notification from HumanAIOS.",
            "tool_name": "test_tool",
            "tool_version": "0.0.0",
            "session_id": "test-session",
            "event_status": "INFO",
            "fields": [{"title": "Duration", "value": "0.1s"}],
            "dedup_key": "smoke123",
            "dry_run": True,
        }
        out = run(sample)
        assert out.get("status") == "ok", f"Unexpected status: {out.get('status')}"
        assert out.get("slack_status") == "dry_run", (
            f"Unexpected slack_status: {out.get('slack_status')}"
        )
        assert "payload" in out, "Missing payload"
        assert "blocks" in out["payload"], "Missing blocks in payload"

        # Verify redact_for_log doesn't expose secrets
        sample_url = "https://hooks.slack.com/services/T12345/B67890/ABCDEF123456"
        redacted = redact_for_log(sample_url)
        assert "ABCDEF123456" not in redacted, "Webhook token not redacted"
        assert "***REDACTED***" in redacted

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


@mcp.tool(name=TOOL_NAME, description="Dispatch a Slack notification via incoming webhook.")
def slack_notifier(spec: dict) -> dict:
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
