#!/usr/bin/env python3
"""
HAIOS Notify Dispatcher — v1.0
Builder v1.7 compliant · Step 11 dispatcher / Step 12 outreach gate
HumanAIOS · S-052026-01

The notify dispatcher is the final stage in every HAIOS pipeline.
It surfaces system outputs to human operators via two channels:

  Slack (#acat-monitor) — for pipeline results, corpus health, drift signals
  GitHub Issues          — for external research outreach (Tier 1 targets)

GOVERNANCE HARD GATES:
  1. GitHub Issues are NEVER sent autonomously. Every outreach dispatch
     produces a DRAFT and requires Z2_OUTREACH_RATIFY (Night send).
     This enforces Tradition 12 (anonymity / ego deflation) and
     Tradition 11 (attraction not promotion).

  2. Slack posts to #acat-monitor go directly (monitor channel only).
     Posts to #wgs-sync require draft-then-operator-send per WGS protocol.

  3. DAILY_WILL_QUERY: the one-bit daily conscience check, dispatched
     at 07:00 CDT. If unanswered for 3 days, system auto-halts (Step 1
     enforced on human).

Usage:
    python haios_notify_dispatcher_v1_0.py --channel acat-monitor --input <json>
    python haios_notify_dispatcher_v1_0.py --github-draft --repo <url> --input <json>
    python haios_notify_dispatcher_v1_0.py --daily-will-query --input <json>
    python haios_notify_dispatcher_v1_0.py --smoke-test
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import urllib.request
import urllib.error

TOOL_NAME = "haios_notify_dispatcher"
TOOL_VERSION = "1.0.0"
SESSION_ID = "S-052026-01"

# Channel ID registry (confirmed Apr 3, 2026)
CHANNEL_REGISTRY = {
    "acat-monitor":     "C0APHCJ5WUE",
    "wgs-sync":         "C0AND66PT7U",
    "ai-contributions": "C0AP9MUKQ7K",
}

# Workspace
WORKSPACE_ID = "T0AHCDYQU92"

# Tradition 11 linter: issue bodies must not contain these promotion signals
PROMOTION_SIGNALS = [
    "you should use",
    "we are better",
    "our tool is",
    "sign up",
    "subscribe",
    "pricing",
    "commercial license",
    "download now",
    "get started today",
    "testimonials",
]

# ---------------------------------------------------------------------------
# Tradition 11 linter
# ---------------------------------------------------------------------------

def tradition_11_lint(text: str) -> List[str]:
    """Check issue body for promotion signals. Returns list of violations."""
    violations = []
    lower = text.lower()
    for signal in PROMOTION_SIGNALS:
        if signal in lower:
            violations.append(f"Promotion signal detected: '{signal}'")
    return violations


# ---------------------------------------------------------------------------
# Dispatch log entry
# ---------------------------------------------------------------------------

def make_log_entry(
    channel: str,
    message: str,
    status: str,
    session_id: str,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "channel": channel,
        "message_preview": message[:120],
        "status": status,
        "session_id": session_id,
        "error": error,
    }


# ---------------------------------------------------------------------------
# Slack dispatcher
# ---------------------------------------------------------------------------

def dispatch_slack(
    channel: str,
    message: str,
    session_id: str,
    webhook_url: Optional[str] = None,
    draft_only: bool = False,
) -> Dict[str, Any]:
    """Post a message to a Slack channel.

    If draft_only=True (or channel == 'wgs-sync'), produce a draft
    for operator send rather than posting directly.

    Uses SLACK_WEBHOOK_URL env var or explicit webhook_url.
    Falls back to logging if no webhook available.
    """
    # wgs-sync always requires draft-then-operator-send per WGS protocol
    if channel == "wgs-sync":
        draft_only = True

    channel_id = CHANNEL_REGISTRY.get(channel, channel)

    if draft_only:
        draft_path = f"/tmp/haios_slack_draft_{session_id}_{channel}.txt"
        try:
            Path(draft_path).write_text(message, encoding="utf-8")
        except Exception:
            draft_path = None
        return {
            "dispatched": False,
            "draft": True,
            "draft_path": draft_path,
            "channel": channel,
            "channel_id": channel_id,
            "message_preview": message[:200],
            "dispatch_log": [make_log_entry(
                channel, message, "DRAFT", session_id
            )],
            "note": (
                f"Draft saved for operator send to #{channel}. "
                "Per WGS protocol: draft-then-operator-send."
            ),
        }

    # Attempt webhook post
    url = webhook_url or os.environ.get("SLACK_WEBHOOK_URL")
    if url:
        try:
            payload = json.dumps({"text": message}).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                resp_body = resp.read().decode("utf-8")
            return {
                "dispatched": True,
                "channel": channel,
                "channel_id": channel_id,
                "dispatch_log": [make_log_entry(
                    channel, message, "SENT", session_id
                )],
                "response": resp_body[:200],
            }
        except urllib.error.URLError as exc:
            return {
                "dispatched": False,
                "channel": channel,
                "channel_id": channel_id,
                "error": f"Webhook error: {exc}",
                "dispatch_log": [make_log_entry(
                    channel, message, "FAILED", session_id, str(exc)
                )],
            }

    # No webhook: write to local log and return structured result
    log_path = f"/tmp/haios_notify_{session_id}.log"
    try:
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(f"\n--- {datetime.now(timezone.utc).isoformat()} ---\n")
            fh.write(f"CHANNEL: #{channel} ({channel_id})\n")
            fh.write(message)
            fh.write("\n")
    except Exception:
        log_path = None

    return {
        "dispatched": False,
        "simulated": True,
        "channel": channel,
        "channel_id": channel_id,
        "log_path": log_path,
        "dispatch_log": [make_log_entry(
            channel, message, "LOGGED_LOCAL", session_id
        )],
        "note": (
            "No SLACK_WEBHOOK_URL set — message logged locally. "
            "Set SLACK_WEBHOOK_URL env var or use Slack MCP for live dispatch."
        ),
    }


# ---------------------------------------------------------------------------
# GitHub Issue draft creator
# ---------------------------------------------------------------------------

def create_github_draft(
    repo_url: str,
    issue_title: str,
    issue_body: str,
    session_id: str,
    labels: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Produce a GitHub Issue DRAFT for Z2 review.

    NEVER posts autonomously. Produces:
      - Tradition 11 lint result
      - Draft file at /tmp/haios_github_draft_<session>_<slug>.md
      - Structured result for Z2_OUTREACH_RATIFY

    GitHub API posting requires Z2_OUTREACH_RATIFY (Zone 2 decision).
    """
    # Tradition 11 lint
    violations = tradition_11_lint(issue_body)

    # Extract owner/repo from URL
    slug = repo_url.rstrip("/").split("github.com/")[-1].replace("/", "_")

    draft_content = (
        f"# GitHub Issue Draft\n"
        f"**Repo:** {repo_url}\n"
        f"**Title:** {issue_title}\n"
        f"**Session:** {session_id}\n"
        f"**Tradition 11 lint:** "
        f"{'PASS' if not violations else 'VIOLATIONS: ' + '; '.join(violations)}\n"
        f"**Labels:** {', '.join(labels or [])}\n"
        f"\n---\n\n"
        f"{issue_body}\n"
        f"\n---\n"
        f"*This draft requires Z2_OUTREACH_RATIFY before sending.*\n"
        f"*Per governance: 24hr window, Night send, no autonomous dispatch.*\n"
    )

    draft_path = f"/tmp/haios_github_draft_{session_id}_{slug}.md"
    try:
        Path(draft_path).write_text(draft_content, encoding="utf-8")
    except Exception as exc:
        return {
            "dispatched": False,
            "draft": True,
            "draft_path": None,
            "tradition_11_violations": violations,
            "z2_required": True,
            "z2_reason": "Z2_OUTREACH_RATIFY required before GitHub Issue dispatch.",
            "error": f"Failed to write draft: {exc}",
        }

    return {
        "dispatched": False,
        "draft": True,
        "draft_path": draft_path,
        "repo_url": repo_url,
        "issue_title": issue_title,
        "tradition_11_violations": violations,
        "tradition_11_pass": len(violations) == 0,
        "z2_required": True,
        "z2_reason": "Z2_OUTREACH_RATIFY required before GitHub Issue dispatch.",
        "dispatch_log": [make_log_entry(
            f"github:{slug}", issue_body, "DRAFT", session_id
        )],
        "note": (
            "Draft ready for Z2 review. Night reviews, sits 24hr, then "
            "hits send or kill. No personal handles in body. "
            "Monthly rotating chair when Zone 2 expands."
        ),
    }


# ---------------------------------------------------------------------------
# Daily will query
# ---------------------------------------------------------------------------

def dispatch_daily_will_query(
    system_state: Dict[str, Any],
    session_id: str,
    channel: str = "acat-monitor",
) -> Dict[str, Any]:
    """Produce the DAILY_WILL_QUERY — one-bit conscience check.

    Sent to Zone 2 at 07:00 CDT.
    Contains:
      - One sentence: what the system did yesterday
      - One sentence: what it proposes to do today
      - One question: PROCEED / HOLD / REDIRECT?

    If unanswered for 3 consecutive days: system auto-halts.
    """
    yesterday = system_state.get("yesterday_summary",
                                  "Pipeline ran; no anomalies detected.")
    today_proposal = system_state.get("today_proposal",
                                       "Continue current pipeline cadence.")
    pending_z2 = system_state.get("pending_z2_items", [])
    consecutive_unanswered = system_state.get("consecutive_unanswered_days", 0)

    # Auto-halt check
    if consecutive_unanswered >= 3:
        halt_message = (
            "🔴 *SYSTEM AUTO-HALT*\n"
            f"DAILY_WILL_QUERY unanswered for {consecutive_unanswered} "
            "consecutive days.\n"
            "Per Step 1 enforcement: system halted until Zone 2 responds.\n"
            "Pipeline paused. No autonomous actions.\n"
            f"Session: {session_id}"
        )
        return {
            "dispatched": False,
            "auto_halt": True,
            "halt_reason": f"DAILY_WILL_QUERY unanswered {consecutive_unanswered} days",
            "message": halt_message,
            "dispatch_log": [make_log_entry(
                channel, halt_message, "AUTO_HALT", session_id
            )],
        }

    # Build the query (140 chars max on the question part)
    z2_items_str = ""
    if pending_z2:
        z2_items_str = "\n*Pending Z2:* " + " · ".join(
            str(i) for i in pending_z2[:3]
        )

    message = (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🧭 *DAILY_WILL_QUERY · {session_id}*\n"
        f"*Yesterday:* {yesterday[:100]}\n"
        f"*Proposed today:* {today_proposal[:100]}\n"
        f"{z2_items_str}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "*Direction?* Reply: PROCEED | HOLD | REDIRECT + 1 sentence intent\n"
        "_No response in 24hr → auto-halt after 3 consecutive misses_"
    )

    result = dispatch_slack(channel, message, session_id)
    result["query_type"] = "DAILY_WILL_QUERY"
    result["consecutive_unanswered"] = consecutive_unanswered
    return result


# ---------------------------------------------------------------------------
# run() interface (pipeline stage entry point)
# ---------------------------------------------------------------------------

def run(input_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Pipeline stage interface.

    Dispatches based on dispatch_type in input_dict:
      slack         → dispatch to Slack channel
      github_draft  → produce GitHub Issue draft for Z2
      daily_will    → dispatch DAILY_WILL_QUERY
      auto          → infer from input shape (default)
    """
    dispatch_type = input_dict.get("dispatch_type", "auto")
    session_id = input_dict.get("session_id", "UNKNOWN")
    channel = input_dict.get("channel", "acat-monitor")

    # Z2 queue item — always surface, never suppress
    z2_queue_item = input_dict.get("z2_queue_item", False)
    z2_reason = input_dict.get("z2_reason", "")

    if dispatch_type == "daily_will" or input_dict.get("daily_will_query"):
        return dispatch_daily_will_query(
            input_dict.get("system_state", {}),
            session_id,
            channel,
        )

    if dispatch_type == "github_draft" or input_dict.get("repo_url"):
        return create_github_draft(
            repo_url=input_dict.get("repo_url", ""),
            issue_title=input_dict.get("issue_title",
                                        "ACAT Integration Opportunity"),
            issue_body=input_dict.get("issue_body",
                                       input_dict.get("report_text", "")),
            session_id=session_id,
            labels=input_dict.get("labels", ["acat", "behavioral-observability"]),
        )

    # Default: Slack dispatch
    report_text = input_dict.get("report_text", "")
    if not report_text:
        # Construct minimal message from pipeline status
        overall = input_dict.get("overall_status", "UNKNOWN")
        report_text = (
            f"Pipeline result: {overall} · Session: {session_id}"
        )
        if z2_queue_item:
            report_text += f"\n🔴 Z2 REQUIRED: {z2_reason}"

    draft_only = input_dict.get("draft_only", False)
    return dispatch_slack(channel, report_text, session_id,
                          draft_only=draft_only)


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

def run_smoke_test() -> bool:
    print(f"[SMOKE] {TOOL_NAME} v{TOOL_VERSION}")

    # Positive: Slack dispatch (no webhook — logged locally)
    result = dispatch_slack(
        "acat-monitor",
        "Smoke test message",
        "S-SMOKE-01",
    )
    assert "dispatch_log" in result
    assert result["channel"] == "acat-monitor"
    print("[SMOKE] Slack dispatch (local log) OK.")

    # Positive: wgs-sync always produces draft
    result_wgs = dispatch_slack(
        "wgs-sync",
        "WGS post content",
        "S-SMOKE-01",
    )
    assert result_wgs["draft"] is True
    assert result_wgs["dispatched"] is False
    print("[SMOKE] wgs-sync produces draft (not sent).")

    # Positive: GitHub draft — never sends, always z2_required
    gh_result = create_github_draft(
        "https://github.com/test/repo",
        "Test Issue",
        "This is a test. We found calibration opportunities.",
        "S-SMOKE-01",
    )
    assert gh_result["z2_required"] is True
    assert gh_result["dispatched"] is False
    assert gh_result["draft"] is True
    print("[SMOKE] GitHub draft produced (not sent, z2_required).")

    # Tradition 11 linter catches promotion
    violations = tradition_11_lint(
        "You should use our tool. Sign up today for pricing info."
    )
    assert len(violations) >= 2
    print(f"[SMOKE] Tradition 11 linter caught {len(violations)} violations.")

    # Clean copy passes
    clean = tradition_11_lint(
        "We measured calibration drift. Here is the data. "
        "Would you like to run this on your system?"
    )
    assert len(clean) == 0
    print("[SMOKE] Tradition 11 linter passed clean copy.")

    # Daily will query
    dw = dispatch_daily_will_query(
        {"yesterday_summary": "All pipelines PASS.",
         "today_proposal": "Run corpus integrity check."},
        "S-SMOKE-01",
    )
    assert dw["query_type"] == "DAILY_WILL_QUERY"
    print("[SMOKE] DAILY_WILL_QUERY generated.")

    # Auto-halt fires at 3 unanswered days
    halt = dispatch_daily_will_query(
        {"consecutive_unanswered_days": 3},
        "S-SMOKE-01",
    )
    assert halt["auto_halt"] is True
    print("[SMOKE] Auto-halt fires at 3 unanswered days.")

    # run() interface
    run_result = run({
        "session_id": "S-SMOKE-01",
        "channel": "acat-monitor",
        "report_text": "Test pipeline report.",
    })
    assert "dispatch_log" in run_result
    print("[SMOKE] run() interface OK.")

    # Negative: missing report_text uses fallback
    fallback = run({
        "session_id": "S-SMOKE-01",
        "overall_status": "WARN",
    })
    assert "dispatch_log" in fallback
    print("[SMOKE] Missing report_text fallback OK.")

    print("[SMOKE] All assertions passed.")
    return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=f"HAIOS Notify Dispatcher {TOOL_VERSION}"
    )
    parser.add_argument("--channel", "-c",
                        default="acat-monitor",
                        help="Slack channel name (acat-monitor, wgs-sync)")
    parser.add_argument("--input", "-i",
                        help="JSON file path or JSON string")
    parser.add_argument("--github-draft", action="store_true",
                        help="Produce a GitHub Issue draft (Z2 required to send)")
    parser.add_argument("--repo", help="GitHub repo URL for draft")
    parser.add_argument("--daily-will-query", action="store_true",
                        help="Dispatch the DAILY_WILL_QUERY")
    parser.add_argument("--draft-only", action="store_true",
                        help="Produce draft, do not post")
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()

    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)

    input_dict: Dict[str, Any] = {}
    if args.input:
        p = Path(args.input)
        if p.exists():
            input_dict = json.loads(p.read_text(encoding="utf-8"))
        else:
            input_dict = json.loads(args.input)

    input_dict["channel"] = args.channel
    if args.draft_only:
        input_dict["draft_only"] = True
    if args.github_draft:
        input_dict["dispatch_type"] = "github_draft"
        if args.repo:
            input_dict["repo_url"] = args.repo
    if args.daily_will_query:
        input_dict["dispatch_type"] = "daily_will"

    result = run(input_dict)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
