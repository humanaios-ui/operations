#!/usr/bin/env python3
"""
ci_predict_consolidate_v1_0.py
Builder v1.7 compliant
HumanAIOS — Stage 2 of the execution-grounded calibration plan

CONSOLIDATE half of PIN → RESOLVE → CONSOLIDATE. Drains the pin and resolve
comments ci_predict_pin_v1_0.py and ci_predict_resolve_v1_0.py posted on one PR,
and appends them as TOKEN + PIN + RESOLVE events to a durable, hash-chained ledger
— using tools/nf_ledger_v0_1.py's own event functions (`append`, `check_p`,
`read`, `verify`), unchanged. This tool adds no new hashing or chaining logic of
its own; it only decides which events to build and hands them to that engine.

WHY A SEPARATE LEDGER FILE
---------------------------
ledgers/NF_LEDGER.jsonl is explicitly scoped to "Phase 2 mesh pins" and carries
its own pending Z2 governance debt (dates and priors owed, a ratification hash
owed). Writing CI-check predictions into that file would be scope creep on a
live, ratification-pending artifact — the same failure mode as settling a
pending Z2 decision by side effect, one level removed. This writes to
ledgers/CI_PREDICT_LEDGER.jsonl instead: same engine, same event shapes,
different subject, no collision with anyone else's open governance item.

WHY check_p IS CALLED HERE, NOT ONLY IN THE DECLARATION
---------------------------------------------------------
ci_predict_pin_v1_0.load_declaration already rejects a probability outside
[0,1] before a pin comment is ever posted. This step calls
nf_ledger_v0_1.check_p again at the point the PIN event is actually built, so
the ledger's own tested guarantee — a bad p cannot enter it, from any caller —
holds regardless of what posted the comment.

EVENT ORDER MATTERS
---------------------
nf_ledger_v0_1.project() requires a TOKEN to exist before any PIN or RESOLVE
that references it; this tool always emits TOKEN, then PIN, then RESOLVE, in
that order, per check, matching cmd_build's own ordering.

IDEMPOTENCY
------------
Before appending, this tool reads the existing ledger and skips any check whose
token_id is already present — a PR can be consolidated more than once (e.g. a
follow-up resolve after this ran once) without double-appending.

Usage:
  python3 tools/ci_predict_consolidate_v1_0.py consolidate \\
      --repo OWNER/REPO --pr 123 --ledger ledgers/CI_PREDICT_LEDGER.jsonl
  python3 tools/ci_predict_consolidate_v1_0.py --smoke-test
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nf_ledger_v0_1 as engine  # noqa: E402  (the ledger's own hashing/appending)

TOOL_NAME = "ci_predict_consolidate"
TOOL_VERSION = "1.0.0"
DEFAULT_LEDGER = "ledgers/CI_PREDICT_LEDGER.jsonl"

PIN_MARKER = "<!-- ci-predict:pin -->"
RESOLVE_MARKER = "<!-- ci-predict:resolve -->"
_JSON_BLOCK = re.compile(r"```json\s*(.*?)\s*```", re.DOTALL)


def extract_payload(comment_body: str, marker: str) -> Optional[dict]:
    """Same discrimination as the resolve tool: marker first, then the fence."""
    if marker not in (comment_body or ""):
        return None
    match = _JSON_BLOCK.search(comment_body)
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return None


def collect_pin_and_resolve(comments: List[dict]) -> tuple:
    """Latest pin payload per head_sha, and merged resolutions per head_sha."""
    pins: Dict[str, dict] = {}
    resolves: Dict[str, dict] = {}
    for comment in comments:
        body = comment.get("body", "")
        pin = extract_payload(body, PIN_MARKER)
        if pin and pin.get("head_sha"):
            pins[pin["head_sha"]] = pin  # last write wins: latest push's pin
        resolve = extract_payload(body, RESOLVE_MARKER)
        if resolve and resolve.get("head_sha"):
            resolves.setdefault(resolve["head_sha"], {}).update(
                resolve.get("resolutions", {})
            )
    return pins, resolves


def commit_date_only(committed_at: str) -> str:
    """The YYYY-MM-DD portion of a git commit's ISO 8601 timestamp.

    nf_ledger_v0_1's TOKEN.date is a plain date; a missing/unparseable anchor
    becomes an empty string, never today's date — a token must never claim a
    commit anchor it does not actually have.
    """
    return committed_at[:10] if len(committed_at) >= 10 and committed_at[4] == "-" else ""


def token_id_for(head_sha: str, check_name: str) -> str:
    """Deterministic id, short enough to read, unique per (commit, check)."""
    slug = re.sub(r"[^a-z0-9]+", "-", check_name.lower()).strip("-")
    return f"CI-{head_sha[:12]}-{slug}"


def build_events(pin: dict, resolutions: dict, existing_ids: set,
                 pushed_at_date: str, start_seq: int = 1) -> List[dict]:
    """Pure: TOKEN+PIN+RESOLVE triples for checks that are resolved and new.

    A check present in the pin but with no resolution yet contributes nothing —
    it is neither scored nor recorded as pending; the next consolidate run picks
    it up once ci_predict_resolve_v1_0 has posted its outcome.

    `seq` is assigned here, starting at `start_seq`, because
    nf_ledger_v0_1.verify() requires every event to carry a strictly
    incrementing sequence number and nf_ledger_v0_1.append() does not assign
    one itself — only its own cmd_build closure does, which this tool does not
    call (that closure is spec-file-shaped for the mesh use case).
    """
    head_sha = pin["head_sha"]
    predictor = pin.get("predictor", "unknown")
    events: List[dict] = []
    seq = start_seq
    for check_name, spec in pin.get("checks", {}).items():
        token_id = token_id_for(head_sha, check_name)
        if token_id in existing_ids:
            continue
        resolution = resolutions.get(check_name)
        if resolution is None:
            continue

        events.append({
            "seq": seq, "type": "TOKEN", "at": pushed_at_date, "by": "ci-predict",
            "token_id": token_id, "practice": "ci-predict",
            "title": f"check '{check_name}' on {head_sha[:12]}",
            "date": pushed_at_date, "date_source": "PRACTICE", "owner_add": False,
        })
        seq += 1
        events.append({
            "seq": seq, "type": "PIN", "at": pushed_at_date, "by": "ci-predict",
            "pin_id": f"{token_id}:{predictor}", "target": token_id,
            "predictor": predictor,
            "claim": f"check '{check_name}' on {head_sha[:12]} will conclude "
                     f"'{spec['conclusion']}'",
            "p": engine.check_p(spec["p"], token_id),
            "scoreable": True,
        })
        seq += 1
        events.append({
            "seq": seq, "type": "RESOLVE", "at": pushed_at_date,
            "by": "ci-predict-resolve",
            "token_id": token_id, "outcome": resolution["outcome"],
            "source": resolution["source"],
        })
        seq += 1
    return events


def load_ledger_state(ledger_path: Path) -> tuple:
    """Existing TOKEN ids (for dedup) and the next free seq. Empty/1 if absent."""
    if not ledger_path.exists():
        return set(), 1
    rows = engine.read(str(ledger_path))
    ids = {row["token_id"] for row in rows if row.get("type") == "TOKEN"}
    next_seq = (rows[-1]["seq"] + 1) if rows else 1
    return ids, next_seq


def gh_json_paginated(path: str) -> List[dict]:
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
        items.extend(page if isinstance(page, list) else [])
    return items


def run(repo: str, pr_number: str, ledger_path: Path) -> int:
    comments = gh_json_paginated(f"repos/{repo}/issues/{pr_number}/comments")
    pins, resolves = collect_pin_and_resolve(comments)
    if not pins:
        print(f"no pin comments on PR {pr_number}; nothing to consolidate")
        return 0

    existing_ids, next_seq = load_ledger_state(ledger_path)

    all_events: List[dict] = []
    for head_sha, pin in pins.items():
        built = build_events(
            pin, resolves.get(head_sha, {}), existing_ids,
            pushed_at_date=commit_date_only(pin.get("committed_at", "")),
            start_seq=next_seq,
        )
        all_events.extend(built)
        next_seq += len(built)

    if not all_events:
        print("nothing new to append (all resolved checks already recorded, "
              "or none resolved yet)")
        return 0

    prev = engine.last_hash(str(ledger_path))
    prev = engine.append(str(ledger_path), all_events, prev)
    err = engine.verify(engine.read(str(ledger_path)))
    if err:
        print(f"FAIL post-append verify: {err}", file=sys.stderr)
        return 1
    print(f"appended {len(all_events)} events; head {prev}")
    return 0


def run_smoke_test() -> bool:
    """Full pipeline on fixtures: build → append via the real engine → verify."""
    import tempfile
    ok = True

    pin = {
        "schema": "ci_predict_pin_v1", "pr": "42", "head_sha": "a" * 40,
        "predictor": "Claude Code",
        "checks": {
            "quality": {"conclusion": "success", "p": 0.9},
            "guard": {"conclusion": "success", "p": 0.8},
        },
    }
    resolutions = {
        "quality": {"predicted_conclusion": "success", "actual_conclusion": "success",
                    "outcome": "YES", "source": "https://example/1"},
        "guard": {"predicted_conclusion": "success", "actual_conclusion": "failure",
                  "outcome": "NO", "source": "https://example/2"},
    }

    events = build_events(pin, resolutions, existing_ids=set(), pushed_at_date="2026-09-12")
    ok = ok and len(events) == 6  # 2 checks x (TOKEN, PIN, RESOLVE)
    ok = ok and [e["type"] for e in events[:3]] == ["TOKEN", "PIN", "RESOLVE"]

    ok = ok and commit_date_only("2026-09-12T10:00:00-07:00") == "2026-09-12"
    ok = ok and commit_date_only("") == ""
    ok = ok and commit_date_only("not-a-date") == ""

    with tempfile.TemporaryDirectory() as workdir:
        ledger = Path(workdir) / "smoke.jsonl"
        prev = engine.append(str(ledger), events, "0" * 64)
        rows = engine.read(str(ledger))
        ok = ok and len(rows) == 6
        ok = ok and engine.verify(rows) is None

        # A real Brier score, per predictor, over these two resolved pins:
        # quality hit at p=0.9 -> (0.9-1)^2 = 0.01; guard missed at p=0.8 -> (0.8-0)^2 = 0.64.
        tokens, pins_by_id = engine.project(rows)
        briers = []
        for p in pins_by_id.values():
            outcome = engine.pin_outcome(p, tokens)
            if outcome not in (None, "VOID"):
                briers.append((p["p"] - outcome) ** 2)
        ok = ok and abs(sum(briers) / len(briers) - 0.325) < 1e-9

        # Idempotency: re-running with the same events, now all pre-existing, appends nothing.
        existing_ids, next_seq = load_ledger_state(ledger)
        ok = ok and len(existing_ids) == 2 and next_seq == 7
        rerun_events = build_events(pin, resolutions, existing_ids, "2026-09-12",
                                    start_seq=next_seq)
        ok = ok and rerun_events == []

        # Tamper is still caught through this tool's own read path.
        tampered = engine.read(str(ledger))
        tampered[-1]["outcome"] = "YES"
        ok = ok and engine.verify(tampered) is not None

        # A bad probability is refused by the shared engine, not silently written.
        bad_pin = {**pin, "checks": {"quality": {"conclusion": "success", "p": 7.0}}}
        try:
            build_events(bad_pin, resolutions, set(), "2026-09-12")
            ok = False
        except SystemExit:
            pass

    print("✓ Smoke test PASSED" if ok else "✗ Smoke test FAILED")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description=f"{TOOL_NAME} v{TOOL_VERSION}")
    parser.add_argument("--smoke-test", action="store_true")
    sub = parser.add_subparsers(dest="command")

    consolidate = sub.add_parser("consolidate")
    consolidate.add_argument("--repo", required=True)
    consolidate.add_argument("--pr", required=True)
    consolidate.add_argument("--ledger", default=DEFAULT_LEDGER)

    args = parser.parse_args()
    if args.smoke_test:
        return 0 if run_smoke_test() else 1
    if args.command != "consolidate":
        parser.print_help()
        return 2
    return run(args.repo, args.pr, Path(args.ledger))


if __name__ == "__main__":
    sys.exit(main())
