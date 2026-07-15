#!/usr/bin/env python3
"""smag_consolidate — drain SMAG rows from the #103 tracking issue into the ledger.

The recursive-learning capture loop has three parts:
  CAPTURE      smag_pr_autocapture posts one predicted-vs-measured row per merged
               PR as a COMMENT on the SMAG pilot ledger issue (#103). (live)
  CONSOLIDATE  *this tool* — drain those comment rows into the durable, analyzable
               ledger file audits/smag_pilot_ledger.jsonl. (was missing → the loop
               captured but never closed; 8 rows sat stranded in issue comments)
  ANALYZE      smag_gap_analysis — compute the predicted-vs-measured gap trend.

Each #103 SMAG comment embeds an exact ```json {...}``` row block; we parse that
(robust — no scraping of the human-readable header), dedup by PR number against the
existing ledger, and append only new rows. Idempotent: safe to re-run.

Read-only against GitHub (uses `gh` to read issue comments); the only write is the
append to the local ledger file. No credentials handled — `gh`/GITHUB_TOKEN auth is
the caller's.

Usage:
  python3 smag_consolidate_v1_0.py [--repo humanaios-ui/operations] [--issue 103]
                                   [--ledger audits/smag_pilot_ledger.jsonl]
  python3 smag_consolidate_v1_0.py --smoke-test
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# Builder v1.7 compliant
# HumanAIOS
TOOL_NAME = "smag_consolidate"
TOOL_VERSION = "1.0.0"
DEFAULT_REPO = "humanaios-ui/operations"
DEFAULT_ISSUE = "103"
DEFAULT_LEDGER = "audits/smag_pilot_ledger.jsonl"

_JSON_BLOCK = re.compile(r"```json\s*(.*?)\s*```", re.DOTALL)


# --- pure helpers (testable, no I/O) -----------------------------------------
def extract_row(comment_body: str, created_at: str | None = None) -> dict | None:
    """Parse the embedded ```json row block from one SMAG comment. None if absent."""
    m = _JSON_BLOCK.search(comment_body or "")
    if not m:
        return None
    try:
        row = json.loads(m.group(1))
    except json.JSONDecodeError:
        return None
    if not row.get("pr"):
        return None
    # The comment json omits timestamp/session; enrich without overwriting.
    if created_at and not row.get("timestamp"):
        row["timestamp"] = created_at
    row.setdefault("session", "")
    return row


def existing_prs(ledger_lines: list[str]) -> set:
    """PR numbers already in the ledger (dedup key)."""
    prs = set()
    for line in ledger_lines:
        line = line.strip()
        if not line:
            continue
        try:
            prs.add(str(json.loads(line).get("pr", "")))
        except json.JSONDecodeError:
            continue
    return prs


def consolidate(comments: list, ledger_lines: list[str]) -> tuple:
    """Return (new_rows, skipped_dup) from comments not already in the ledger.

    comments: list of {"body": str, "createdAt": str}. Deterministic order.
    """
    have = existing_prs(ledger_lines)
    new_rows, skipped, seen = [], 0, set(have)
    for c in comments:
        row = extract_row(c.get("body", ""), c.get("createdAt"))
        if row is None:
            continue
        pr = str(row["pr"])
        if pr in seen:
            skipped += 1
            continue
        seen.add(pr)
        new_rows.append(row)
    return new_rows, skipped


# --- I/O ---------------------------------------------------------------------
def read_ledger(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines() if path.exists() else []


def fetch_comments(repo: str, issue: str) -> list:
    out = subprocess.run(
        ["gh", "issue", "view", issue, "--repo", repo, "--json", "comments"],
        capture_output=True, text=True, check=True,
    ).stdout
    return json.loads(out).get("comments", [])


def append_rows(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")


def run(repo: str, issue: str, ledger: str) -> int:
    path = Path(ledger)
    ledger_lines = read_ledger(path)
    comments = fetch_comments(repo, issue)
    new_rows, skipped = consolidate(comments, ledger_lines)
    if new_rows:
        append_rows(path, new_rows)
    print(f"smag_consolidate v{TOOL_VERSION}: ledger had {len(existing_prs(ledger_lines))} "
          f"row(s); {len(comments)} issue comment(s) scanned; "
          f"{len(new_rows)} new row(s) appended, {skipped} duplicate(s) skipped.")
    for r in new_rows:
        print(f"  + PR #{r['pr']}: {r.get('task','')[:60]}")
    return 0


# --- smoke test --------------------------------------------------------------
def smoke_test() -> int:
    c1 = {"body": "**SMAG row — PR #200**\n\n```json\n" +
          json.dumps({"pr": "200", "task": "t", "substrate": "Copilot",
                      "predicted": "p", "measured": "merged=True", "gap": ""}) +
          "\n```", "createdAt": "2026-07-14T00:00:00Z"}
    c2 = {"body": "no json here", "createdAt": "x"}
    c_dup = {"body": "```json\n" + json.dumps({"pr": "200", "task": "dup"}) + "\n```",
             "createdAt": "y"}
    # parse
    r = extract_row(c1["body"], c1["createdAt"])
    assert r and r["pr"] == "200" and r["timestamp"] == "2026-07-14T00:00:00Z", "parse+enrich"
    assert extract_row(c2["body"]) is None, "no-json → None"
    # consolidate: dedup vs existing ledger + within-batch
    existing = [json.dumps({"pr": "199"})]
    new, skipped = consolidate([c1, c2, c_dup], existing)
    assert len(new) == 1 and new[0]["pr"] == "200", "one new row"
    assert skipped == 1, "within-batch dup skipped"
    # idempotency: re-run with PR 200 now in ledger → nothing new
    new2, _ = consolidate([c1], existing + [json.dumps({"pr": "200"})])
    assert new2 == [], "idempotent re-run"
    print("✓ Smoke test PASSED")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Consolidate SMAG rows from #103 into the ledger.")
    ap.add_argument("--repo", default=DEFAULT_REPO)
    ap.add_argument("--issue", default=DEFAULT_ISSUE)
    ap.add_argument("--ledger", default=DEFAULT_LEDGER)
    ap.add_argument("--smoke-test", action="store_true")
    args = ap.parse_args()
    if args.smoke_test:
        return smoke_test()
    return run(args.repo, args.issue, args.ledger)


if __name__ == "__main__":
    sys.exit(main())
