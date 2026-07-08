#!/usr/bin/env python3
"""
smag_pr_autocapture_v1_0 — auto-capture a SMAG pilot row from a merged PR
TYPE: tool
Builder v1.7 compliant · smag_autocapture
HumanAIOS · S-070726

The MECHANICAL tier of SMAG capture: no LLM, no human notification. On PR close,
derive the deterministic fields from PR metadata and append a row via
smag_pilot_capture_v1_0.py. The qualitative "gap" (was it gamed?) is left blank for
the optional LLM-review tier to enrich later.

  predicted — linked-issue acceptance (best-effort) / PR title
  measured  — merged? + required-check conclusions
  substrate — derived from PR author login (Copilot / Claude Code / human:<login>)

Usage (in CI, GH_TOKEN in env):
  python3 smag_pr_autocapture_v1_0.py --pr 99 --repo humanaios-ui/operations \
      --capture-tool tools/smag_pilot_capture_v1_0.py --output outputs/
  python3 smag_pr_autocapture_v1_0.py --smoke-test
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys

TOOL_NAME = "smag_pr_autocapture"
TOOL_VERSION = "1.0.0"


def derive_substrate(login: str) -> str:
    """Map a PR author login to a substrate label."""
    low = (login or "").lower()
    if "copilot" in low:
        return "Copilot"
    if "claude" in low:
        return "Claude Code"
    return f"human:{login}" if login else "unknown"


def summarize_checks(check_runs: list) -> str:
    """One-line summary of check-run conclusions."""
    if not check_runs:
        return "no checks"
    counts: dict[str, int] = {}
    for c in check_runs:
        concl = c.get("conclusion") or c.get("status") or "unknown"
        counts[concl] = counts.get(concl, 0) + 1
    return ", ".join(f"{k}:{v}" for k, v in sorted(counts.items()))


def build_fields(pr: dict, checks: list) -> dict:
    """Build the SMAG row fields from PR metadata. Pure function (testable)."""
    login = (pr.get("user") or {}).get("login", "")
    merged = bool(pr.get("merged") or pr.get("merged_at"))
    predicted = (pr.get("body") or "").strip()
    predicted = predicted[:180] if predicted else f"(auto) PR: {pr.get('title', '')[:120]}"
    measured = f"merged={merged}; checks: {summarize_checks(checks)}"
    return {
        "pr": str(pr.get("number", "")),
        "task": (pr.get("title") or "").strip()[:160],
        "substrate": derive_substrate(login),
        "predicted": predicted,
        "measured": measured,
        "gap": "",  # left for the optional LLM-review tier
    }


def gh_json(path: str):
    """Fetch JSON from the GitHub API via gh. Returns None on failure."""
    proc = subprocess.run(["gh", "api", path], capture_output=True, text=True, timeout=60)
    if proc.returncode != 0:
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None


def capture(fields: dict, capture_tool: str, output_dir: str) -> int:
    """Append the row via the existing smag_pilot_capture tool (writes its
    default ledger under output_dir)."""
    ledger = f"{output_dir.rstrip('/')}/smag_pilot_ledger.jsonl"
    argv = [
        sys.executable, capture_tool,
        "--pr", fields["pr"], "--task", fields["task"],
        "--substrate", fields["substrate"], "--predicted", fields["predicted"],
        "--measured", fields["measured"], "--gap", fields["gap"],
        "--ledger", ledger,
        "--output", output_dir,
    ]
    proc = subprocess.run(argv, capture_output=True, text=True)
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    return proc.returncode


def format_comment(fields: dict) -> str:
    """Render a SMAG row as a tracking-issue comment (append-only sink)."""
    return (
        f"**SMAG row — PR #{fields['pr']}** · substrate: `{fields['substrate']}`\n\n"
        f"- **task:** {fields['task']}\n"
        f"- **predicted:** {fields['predicted']}\n"
        f"- **measured:** {fields['measured']}\n"
        f"- **gap:** {fields['gap'] or '_(pending LLM-review tier)_'}\n\n"
        f"```json\n{json.dumps(fields)}\n```"
    )


def post_to_issue(fields: dict, repo: str, issue_number: str) -> int:
    """Post the row as a comment on the tracking issue (conflict-free sink)."""
    proc = subprocess.run(
        ["gh", "issue", "comment", str(issue_number), "--repo", repo,
         "--body", format_comment(fields)],
        capture_output=True, text=True,
    )
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    return proc.returncode


def run(pr_num: str, repo: str, capture_tool: str, output_dir: str,
        tracking_issue: str) -> int:
    pr = gh_json(f"repos/{repo}/pulls/{pr_num}")
    if pr is None:
        print(f"::warning::could not fetch PR {pr_num}; skipping capture")
        return 0  # never fail the workflow over a capture miss
    sha = pr.get("merge_commit_sha") or (pr.get("head") or {}).get("sha")
    checks_resp = gh_json(f"repos/{repo}/commits/{sha}/check-runs") if sha else None
    checks = (checks_resp or {}).get("check_runs", []) if checks_resp else []
    fields = build_fields(pr, checks)
    print(f"SMAG row: {json.dumps(fields)}")
    if tracking_issue:
        return post_to_issue(fields, repo, tracking_issue)
    return capture(fields, capture_tool, output_dir)


def run_smoke_test() -> bool:
    """Smoke test the pure derivation logic (no network)."""
    ok = True
    ok = ok and derive_substrate("Copilot") == "Copilot"
    ok = ok and derive_substrate("claude-code[bot]") == "Claude Code"
    ok = ok and derive_substrate("nightowl").startswith("human:")
    f = build_fields(
        {"number": 7, "title": "t", "body": "b", "user": {"login": "Copilot"}, "merged": True},
        [{"conclusion": "success"}, {"conclusion": "success"}],
    )
    ok = ok and f["substrate"] == "Copilot" and "merged=True" in f["measured"] and "success:2" in f["measured"]
    c = format_comment(f)
    ok = ok and "SMAG row" in c and "predicted:" in c and "```json" in c
    print("✓ Smoke test PASSED" if ok else "✗ Smoke test FAILED")
    return ok


def main() -> int:
    p = argparse.ArgumentParser(description=f"{TOOL_NAME} v{TOOL_VERSION}")
    p.add_argument("--pr")
    p.add_argument("--repo", default="humanaios-ui/operations")
    p.add_argument("--capture-tool", default="tools/smag_pilot_capture_v1_0.py")
    p.add_argument("--output", default="outputs", help="Output dir for the file ledger")
    p.add_argument("--tracking-issue", default="",
                   help="If set, post the row as a comment on this issue "
                        "(conflict-free CI sink) instead of appending the file ledger")
    p.add_argument("--smoke-test", action="store_true")
    args = p.parse_args()
    if args.smoke_test:
        return 0 if run_smoke_test() else 1
    if not args.pr:
        p.error("--pr is required unless --smoke-test")
    return run(args.pr, args.repo, args.capture_tool, args.output, args.tracking_issue)


if __name__ == "__main__":
    sys.exit(main())
