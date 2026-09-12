#!/usr/bin/env python3
"""
ci_predict_resolve_v1_0.py
Builder v1.7 compliant
HumanAIOS — Stage 2 of the execution-grounded calibration plan

RESOLVE half of the PIN → RESOLVE → CONSOLIDATE loop. Reads the pin comment
ci_predict_pin_v1_0.py posted, fetches the PR head SHA's actual check-run
conclusions, and posts a resolve comment recording YES/NO per check plus the
check-run's own URL as `source` — the external, GitHub-owned record a resolution
must point to, mirroring the mandatory `--source` on nf_ledger_v0_1.py's own
`resolve` command.

TERMINAL VS PENDING
--------------------
Only a check whose `status` is `completed` has a meaningful `conclusion`. A check
still `in_progress` or `queued` is left unresolved this run; re-running later
picks it up. This mirrors smag_resolve_v1_0.py's "pending rows self-heal" design
and is why this tool is idempotent: it never guesses at a running check's outcome,
and never re-resolves one it already resolved.

WHY THIS IS NOT auto_scored
-----------------------------
This tool does not judge behaviour — it reads a status GitHub already computed
and compares it to a value declared before the fact. There is no rater, so there
is no inter-rater-agreement question and no validation this could fail short of
"did it read the API correctly," which the tests below check on fixtures.

Usage:
  python3 tools/ci_predict_resolve_v1_0.py resolve --repo OWNER/REPO --pr 123
  python3 tools/ci_predict_resolve_v1_0.py --smoke-test
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from typing import Any, Dict, List, Optional

TOOL_NAME = "ci_predict_resolve"
TOOL_VERSION = "1.0.0"

PIN_MARKER = "<!-- ci-predict:pin -->"
RESOLVE_MARKER = "<!-- ci-predict:resolve -->"
_JSON_BLOCK = re.compile(r"```json\s*(.*?)\s*```", re.DOTALL)


def extract_payload(comment_body: str, marker: str) -> Optional[dict]:
    """Pull the embedded JSON block from a marked comment. None if absent/malformed.

    Unmarked JSON fences (e.g. a SMAG row on the same PR) are ignored: the marker
    is checked first, so this never cross-parses another tool's comment.
    """
    if marker not in (comment_body or ""):
        return None
    match = _JSON_BLOCK.search(comment_body)
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return None


def find_latest_pin(comments: List[dict], head_sha: str) -> Optional[dict]:
    """The most recent pin comment for this exact head SHA, or None.

    Keyed on head_sha, not just presence, so a stale pin from a prior push on the
    same PR can never resolve against a different commit's checks.
    """
    candidates = []
    for comment in comments:
        payload = extract_payload(comment.get("body", ""), PIN_MARKER)
        if payload and payload.get("head_sha") == head_sha:
            candidates.append((comment.get("created_at", ""), payload))
    if not candidates:
        return None
    candidates.sort(key=lambda pair: pair[0])
    return candidates[-1][1]


def already_resolved_checks(comments: List[dict], head_sha: str) -> set:
    """Check names already resolved for this SHA, so a rerun does not duplicate."""
    resolved = set()
    for comment in comments:
        payload = extract_payload(comment.get("body", ""), RESOLVE_MARKER)
        if payload and payload.get("head_sha") == head_sha:
            resolved.update(payload.get("resolutions", {}).keys())
    return resolved


def compute_resolutions(pin_payload: dict, check_runs: List[dict],
                        already_done: Optional[set] = None) -> Dict[str, dict]:
    """Pure: match predicted checks against actual check-run results.

    Returns one entry per predicted check that is both terminal and not already
    resolved. A check with no matching check-run yet, or still running, is
    omitted — not recorded as a miss. Silence here means "ask again later," never
    "predicted correctly."
    """
    already_done = already_done or set()
    by_name: Dict[str, dict] = {}
    for run in check_runs:
        name = run.get("name")
        if name and (name not in by_name or run.get("status") == "completed"):
            by_name[name] = run

    resolutions: Dict[str, dict] = {}
    for check_name, spec in pin_payload.get("checks", {}).items():
        if check_name in already_done:
            continue
        run = by_name.get(check_name)
        if run is None or run.get("status") != "completed":
            continue
        actual = run.get("conclusion")
        resolutions[check_name] = {
            "predicted_conclusion": spec["conclusion"],
            "actual_conclusion": actual,
            "outcome": "YES" if actual == spec["conclusion"] else "NO",
            "source": run.get("html_url", ""),
        }
    return resolutions


def render_resolve_comment(pr: str, head_sha: str, resolutions: Dict[str, dict]) -> str:
    """Render the human-readable + machine-parseable resolve comment."""
    lines = [
        f"- `{name}` → predicted **{r['predicted_conclusion']}**, actual "
        f"**{r['actual_conclusion']}** → {r['outcome']}"
        for name, r in sorted(resolutions.items())
    ]
    payload = {
        "schema": "ci_predict_resolve_v1",
        "pr": str(pr),
        "head_sha": head_sha,
        "resolutions": resolutions,
    }
    return (
        f"{RESOLVE_MARKER}\n"
        f"## CI prediction resolved — PR #{pr} @ `{head_sha[:12]}`\n\n"
        + "\n".join(lines) +
        f"\n\n```json\n{json.dumps(payload, sort_keys=True)}\n```"
    )


def gh_json(path: str):
    """Fetch JSON from the GitHub API via gh. Returns None on failure."""
    proc = subprocess.run(["gh", "api", path], capture_output=True, text=True, timeout=60)
    if proc.returncode != 0:
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None


def gh_json_paginated(path: str, key: str) -> List[dict]:
    """Fetch a paginated GitHub list endpoint via gh --paginate."""
    proc = subprocess.run(["gh", "api", "--paginate", path],
                          capture_output=True, text=True, timeout=60)
    if proc.returncode != 0:
        return []
    items: List[dict] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            page = json.loads(line)
        except json.JSONDecodeError:
            continue
        items.extend(page.get(key, []) if isinstance(page, dict) else page)
    return items


def post_comment(repo: str, pr_number: str, body: str) -> int:
    proc = subprocess.run(
        ["gh", "pr", "comment", str(pr_number), "--repo", repo, "--body", body],
        capture_output=True, text=True,
    )
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    return proc.returncode


def run(repo: str, pr_number: str) -> int:
    pr = gh_json(f"repos/{repo}/pulls/{pr_number}")
    if pr is None:
        print(f"::warning::could not fetch PR {pr_number}; skipping resolve",
              file=sys.stderr)
        return 0
    head_sha = (pr.get("head") or {}).get("sha", "")
    comments = gh_json_paginated(f"repos/{repo}/issues/{pr_number}/comments", "")
    if not comments:
        comments = gh_json(f"repos/{repo}/issues/{pr_number}/comments") or []

    pin_payload = find_latest_pin(comments, head_sha)
    if pin_payload is None:
        print(f"no pin found for {head_sha[:12]}; nothing to resolve")
        return 0

    already_done = already_resolved_checks(comments, head_sha)
    checks_resp = gh_json(f"repos/{repo}/commits/{head_sha}/check-runs")
    check_runs = (checks_resp or {}).get("check_runs", []) if checks_resp else []
    resolutions = compute_resolutions(pin_payload, check_runs, already_done)

    if not resolutions:
        print("no newly-terminal predicted checks; nothing to resolve yet")
        return 0

    comment = render_resolve_comment(pr_number, head_sha, resolutions)
    print(comment)
    return post_comment(repo, pr_number, comment)


def run_smoke_test() -> bool:
    """Pure-logic smoke test against fixture data. No network."""
    ok = True
    pin_payload = {
        "schema": "ci_predict_pin_v1", "pr": "42", "head_sha": "a" * 40,
        "predictor": "Claude Code",
        "checks": {
            "quality": {"conclusion": "success", "p": 0.9},
            "guard": {"conclusion": "success", "p": 0.8},
            "flaky": {"conclusion": "failure", "p": 0.6},
        },
    }
    check_runs = [
        {"name": "quality", "status": "completed", "conclusion": "success",
         "html_url": "https://example/1"},
        {"name": "guard", "status": "completed", "conclusion": "failure",
         "html_url": "https://example/2"},
        {"name": "flaky", "status": "in_progress"},
    ]
    resolutions = compute_resolutions(pin_payload, check_runs)
    ok = ok and resolutions["quality"]["outcome"] == "YES"
    ok = ok and resolutions["guard"]["outcome"] == "NO"
    ok = ok and "flaky" not in resolutions  # still running: not silently scored

    # A check already resolved is not resolved again.
    again = compute_resolutions(pin_payload, check_runs, already_done={"quality"})
    ok = ok and "quality" not in again and "guard" in again

    # Round-trip through the rendered comment and the marker-aware extractor.
    comment = render_resolve_comment("42", "a" * 40, resolutions)
    ok = ok and RESOLVE_MARKER in comment
    round_tripped = extract_payload(comment, RESOLVE_MARKER)
    ok = ok and round_tripped is not None
    ok = ok and round_tripped["resolutions"]["quality"]["outcome"] == "YES"

    # A marker that is not present must not be matched by accident.
    ok = ok and extract_payload("no marker here\n```json\n{}\n```", RESOLVE_MARKER) is None
    # A resolve comment's body must never be readable as a pin, marker mismatch aside:
    # this is the same discrimination find_latest_pin depends on to never cross-parse.
    ok = ok and extract_payload(comment, PIN_MARKER) is None

    # Two pushes to the same PR: an earlier pin for a since-superseded commit must
    # never be selected once a pin for the current head SHA exists.
    from ci_predict_pin_v1_0 import build_payload, render_pin_comment
    stale_pin = render_pin_comment(build_payload("42", "b" * 40, "Claude Code", {
        "checks": {"quality": {"conclusion": "success", "p": 0.5}}}))
    current_pin = render_pin_comment(build_payload("42", "a" * 40, "Claude Code", {
        "checks": {"quality": {"conclusion": "success", "p": 0.9}}}))
    latest = find_latest_pin(
        [{"body": stale_pin, "created_at": "2026-01-01"},
         {"body": current_pin, "created_at": "2026-01-02"}],
        "a" * 40,
    )
    ok = ok and latest is not None and latest["head_sha"] == "a" * 40
    ok = ok and latest["checks"]["quality"]["p"] == 0.9  # the current push's stated p, not the stale one's

    print("✓ Smoke test PASSED" if ok else "✗ Smoke test FAILED")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description=f"{TOOL_NAME} v{TOOL_VERSION}")
    parser.add_argument("--smoke-test", action="store_true")
    sub = parser.add_subparsers(dest="command")

    resolve = sub.add_parser("resolve")
    resolve.add_argument("--repo", required=True)
    resolve.add_argument("--pr", required=True)

    args = parser.parse_args()
    if args.smoke_test:
        return 0 if run_smoke_test() else 1
    if args.command != "resolve":
        parser.print_help()
        return 2
    return run(args.repo, args.pr)


if __name__ == "__main__":
    sys.exit(main())
