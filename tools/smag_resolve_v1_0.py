#!/usr/bin/env python3
"""smag_resolve — fix SMAG capture timing by recording CI outcome AFTER checks resolve.

smag-capture fires on PR-close, often BEFORE CI finishes, so `measured` records
`in_progress` (and can even record transient failures that later go green). Round-1
analysis showed this errs BOTH ways: PR #114 looked pending/clean but resolved to a
real FAILURE; PR #104 looked friction but resolved clean. So the capture-time snapshot
is unreliable up and down.

This tool re-queries each ledger row's *terminal* check state (`gh pr view
statusCheckRollup`) and rewrites `measured` to the resolved outcome — preserving the
original capture snapshot as `measured_capture` (the capture-vs-resolved delta is the
instrument-lag signal). Idempotent; rows whose checks are still running are left
pending. Wired into smag-consolidate.yml before analysis, pending rows self-heal each
round; run standalone to backfill history.

Read-only against GitHub (uses `gh`); the only write is the ledger. No credentials.

Usage:
  python3 smag_resolve_v1_0.py [--repo humanaios-ui/operations]
                               [--ledger audits/smag_pilot_ledger.jsonl] [--pending-only]
  python3 smag_resolve_v1_0.py --smoke-test
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Builder v1.7 compliant
# HumanAIOS
TOOL_NAME = "smag_resolve"
TOOL_VERSION = "1.1.0"
DEFAULT_REPO = "humanaios-ui/operations"
DEFAULT_LEDGER = "audits/smag_pilot_ledger.jsonl"

# CI conclusion → gap bucket. Only terminal conclusions count; running states
# (no conclusion / IN_PROGRESS / QUEUED / PENDING / WAITING) mean "not yet resolved".
_FAILURE = {"FAILURE", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED", "STARTUP_FAILURE", "STALE"}
_SUCCESS = {"SUCCESS"}
_NEUTRAL = {"SKIPPED", "NEUTRAL"}
_RUNNING = {"IN_PROGRESS", "QUEUED", "PENDING", "WAITING", "REQUESTED", ""}

# Admission / repository-coordinator checks. They go red on admit timing (a "ready"
# event racing the /coordinator admit command), not on the code the author predicted
# about, so a red one is not counted as `failure` against the author's smag_p.
# They are still recorded, as `routing_red:R` and `routing_failing_checks`, so nothing
# is hidden. Evidence: experiments/bot_review_calibration_e0 (45 of 79 red PRs were red
# only on these). Z2 asked for this on 2026-11-28; the merge of this change ratifies it.
ROUTING_CHECKS = frozenset({
    "Repository admission/backpressure gate",
    "Reconcile active PR admission snapshots",
    "Reconcile terminal PR admission lifecycle",
    "Apply authenticated PR coordinator command",
    "Apply authorized issue coordinator command",
    "Append coordinator state event",
})


# --- pure (testable) ---------------------------------------------------------
def _state(check: dict) -> str:
    """Normalize one statusCheckRollup entry to a conclusion token (uppercase)."""
    return (check.get("conclusion") or check.get("state") or check.get("status") or "").upper()


def _check_name(c: dict) -> str:
    return c.get("name") or c.get("context") or "?"


def resolve_measured(rollup: list, merged: bool) -> tuple:
    """Return (measured_str, all_terminal, failing_names, routing_names). measured matches
    the classifier format: 'merged=<bool>; checks: failure:F, success:S[, skipped:K]
    [, routing_red:R]' when terminal. failing_names lists the checks that concluded
    failure — so the gap can be attributed to a specific (often single, recurring)
    check. Red ROUTING_CHECKS go to routing_names and routing_red, never to failure."""
    fail = succ = skip = running = routing = 0
    failing_names, routing_names = [], []
    for c in rollup or []:
        s = _state(c)
        if s in _RUNNING:
            running += 1
        elif s in _FAILURE and _check_name(c) in ROUTING_CHECKS:
            routing += 1
            routing_names.append(_check_name(c))
        elif s in _FAILURE:
            fail += 1
            failing_names.append(_check_name(c))
        elif s in _SUCCESS:
            succ += 1
        elif s in _NEUTRAL:
            skip += 1
        else:
            running += 1  # unknown / not-yet-terminal → treat as unresolved, stay pending
    if running:
        parts = [f"in_progress:{running}"]
        if fail:
            parts.append(f"failure:{fail}")
        if succ:
            parts.append(f"success:{succ}")
        if routing:
            parts.append(f"routing_red:{routing}")
        return f"merged={merged}; checks: " + ", ".join(parts), False, failing_names, routing_names
    parts = []
    if fail:
        parts.append(f"failure:{fail}")
    if succ:
        parts.append(f"success:{succ}")
    if skip:
        parts.append(f"skipped:{skip}")
    if routing:
        parts.append(f"routing_red:{routing}")
    body = ", ".join(parts) if parts else "no checks"
    return f"merged={merged}; checks: {body}", True, failing_names, routing_names


def apply_resolution(row: dict, resolved: str, terminal: bool, now: str,
                     failing_names: list | None = None, routing_names: list | None = None) -> bool:
    """Update row in place if terminal and changed. Returns True if modified.
    Preserves the first capture snapshot as measured_capture; records failing_checks."""
    if not terminal:
        return False
    # Idempotent, but refresh if the resolved value changed OR failing_checks (a later
    # schema field) is not yet recorded on an already-resolved row.
    desired_failing = failing_names if failing_names is not None else row.get("failing_checks", [])
    desired_routing = routing_names if routing_names is not None else row.get("routing_failing_checks", [])
    if (row.get("measured") == resolved and row.get("resolved") and row.get("failing_checks") == desired_failing
            and row.get("routing_failing_checks", []) == desired_routing):
        return False
    if "measured_capture" not in row:
        row["measured_capture"] = row.get("measured", "")
    row["measured"] = resolved
    row["resolved"] = True
    row["resolved_at"] = now
    row["failing_checks"] = desired_failing or []
    if desired_routing:
        row["routing_failing_checks"] = desired_routing
    else:
        row.pop("routing_failing_checks", None)
    return True


# --- I/O ---------------------------------------------------------------------
def fetch_rollup(repo: str, pr: str) -> tuple:
    out = subprocess.run(
        ["gh", "pr", "view", pr, "--repo", repo, "--json", "mergedAt,statusCheckRollup"],
        capture_output=True, text=True, check=True,
    ).stdout
    d = json.loads(out)
    return (d.get("statusCheckRollup") or []), bool(d.get("mergedAt"))


def _is_pending(measured: str) -> bool:
    return "in_progress" in (measured or "") or "merged=" not in (measured or "")


def run(repo: str, ledger: str, pending_only: bool) -> int:
    path = Path(ledger)
    if not path.exists():
        print(f"{TOOL_NAME}: no ledger at {ledger}")
        return 0
    rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    now = datetime.now(timezone.utc).isoformat()
    changed = 0
    for r in rows:
        if pending_only and not _is_pending(r.get("measured", "")):
            continue
        try:
            rollup, merged = fetch_rollup(repo, str(r["pr"]))
        except (subprocess.CalledProcessError, KeyError):
            continue
        resolved, terminal, failing, routing = resolve_measured(rollup, merged)
        if apply_resolution(r, resolved, terminal, now, failing, routing):
            changed += 1
            culprit = f"  [{', '.join(failing)}]" if failing else ""
            print(f"  ~ PR #{r['pr']}: → {resolved}{culprit}")
    if changed:
        path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    print(f"{TOOL_NAME} v{TOOL_VERSION}: {len(rows)} row(s) scanned; {changed} resolved/updated.")
    return 0


def smoke_test() -> int:
    # terminal: 1 failure + 5 success → friction-shaped, all_terminal True, names captured
    m, term, fn, rn = resolve_measured(
        [{"conclusion": "FAILURE", "name": "claude"}] + [{"conclusion": "SUCCESS"}] * 5, True)
    assert term and "failure:1" in m and "success:5" in m, m
    assert fn == ["claude"] and rn == [], (fn, rn)
    # red admission gate only → no `failure`, recorded as routing_red; classifier sees clean
    m3, term3, fn3, rn3 = resolve_measured(
        [{"conclusion": "FAILURE", "name": "Repository admission/backpressure gate"}, {"conclusion": "SUCCESS"}], True)
    assert term3 and "failure:" not in m3.replace("routing_red", "") and "routing_red:1" in m3, m3
    assert fn3 == [] and rn3 == ["Repository admission/backpressure gate"], (fn3, rn3)
    import re as _re
    assert _re.search(r"failure:\s*(\d+)", m3) is None, "downstream FAIL regexes must not see routing reds"
    # a real failure next to a routing red still counts as one failure
    m4, _, fn4, rn4 = resolve_measured(
        [{"conclusion": "FAILURE", "name": "validate"},
         {"conclusion": "FAILURE", "name": "Reconcile active PR admission snapshots"}], True)
    assert "failure:1" in m4 and "routing_red:1" in m4 and fn4 == ["validate"], m4
    # still running → not terminal, stays pending
    m2, term2, _, _ = resolve_measured([{"status": "IN_PROGRESS"}, {"conclusion": "SUCCESS"}], True)
    assert not term2 and "in_progress:1" in m2, m2
    # apply preserves original + sets resolved + failing_checks
    row = {"pr": "9", "measured": "merged=True; checks: in_progress:5"}
    assert apply_resolution(row, "merged=True; checks: failure:1, success:3", True, "T", ["claude"])
    assert row["measured_capture"] == "merged=True; checks: in_progress:5"
    assert row["measured"] == "merged=True; checks: failure:1, success:3" and row["resolved"]
    assert row["failing_checks"] == ["claude"]
    # idempotent: second apply of same → no change
    assert not apply_resolution(row, "merged=True; checks: failure:1, success:3", True, "T2", ["claude"])
    # routing names recorded beside, not inside, failing_checks
    row2 = {"pr": "10", "measured": "merged=True; checks: in_progress:2"}
    assert apply_resolution(row2, m3, True, "T", fn3, rn3)
    assert row2["failing_checks"] == [] and row2["routing_failing_checks"] == rn3
    # not terminal → no change
    assert not apply_resolution({"measured": "x"}, "y", False, "T")
    print("✓ Smoke test PASSED")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Resolve SMAG rows to final CI outcome.")
    ap.add_argument("--repo", default=DEFAULT_REPO)
    ap.add_argument("--ledger", default=DEFAULT_LEDGER)
    ap.add_argument("--pending-only", action="store_true",
                    help="only re-resolve rows still showing in_progress/unknown")
    ap.add_argument("--smoke-test", action="store_true")
    args = ap.parse_args()
    if args.smoke_test:
        return smoke_test()
    return run(args.repo, args.ledger, args.pending_only)


if __name__ == "__main__":
    sys.exit(main())
