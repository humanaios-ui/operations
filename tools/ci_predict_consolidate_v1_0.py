#!/usr/bin/env python3
"""
ci_predict_consolidate_v1_0.py
Builder v1.7 compliant
HumanAIOS — Stage 2 of the execution-grounded calibration plan

CONSOLIDATE half of PIN → RESOLVE → CONSOLIDATE. Reads the pin comment(s)
ci_predict_pin_v1_0.py posted on one PR, independently re-fetches each
predicted commit's actual check-run conclusions, and appends the result as
TOKEN + PIN + RESOLVE events to a durable, hash-chained ledger — using
tools/nf_ledger_v0_1.py's own event functions (`append`, `check_p`, `read`,
`verify`), unchanged. This tool adds no new hashing or chaining logic of its
own; it only decides which events to build and hands them to that engine.

WHY THIS RE-DERIVES RESOLUTIONS INSTEAD OF READING A RESOLVE COMMENT
-----------------------------------------------------------------------
An earlier version trusted ci_predict_resolve_v1_0.py's posted comment for
the scored outcome. That comment is just another PR comment: anyone who can
comment on the PR could post a forged one, in the right shape, and have a
fabricated YES/NO scored into the ledger. This version never reads a resolve
comment at all — it calls ci_predict_resolve_v1_0.compute_resolutions()
itself, against a fresh check-runs fetch, using only the trusted PIN as the
predicted side. The forgeable surface is reduced to "what was predicted,"
which cannot be independently re-derived from anywhere else, and which the
PIN's own git-commit anchor already grounds.

WHY A SEPARATE LEDGER FILE
---------------------------
ledgers/NF_LEDGER.jsonl is explicitly scoped to "Phase 2 mesh pins" and
carries its own pending Z2 governance debt (dates and priors owed, a
ratification hash owed). Writing CI-check predictions into that file would
be scope creep on a live, ratification-pending artifact — the same failure
mode as settling a pending Z2 decision by side effect, one level removed.
This writes to ledgers/CI_PREDICT_LEDGER.jsonl instead: same engine, same
event shapes, different subject, no collision with anyone else's open
governance item.

WHY A MISSING ANCHOR REFUSES THE CHECK, NOT JUST THE DATE
-------------------------------------------------------------
A TOKEN with `date_source: PRACTICE` is immediately scoreable in
nf_ledger_v0_1's model. If the git-commit anchor could not be determined
(git_commit_date failed), marking it PRACTICE anyway would let an unanchored
prediction into the ledger as if it were provably-before-the-outcome — the
exact property this whole stage exists to establish. Such a check is
skipped entirely rather than recorded with a fabricated anchor.

WHY check_p IS CALLED HERE, NOT ONLY IN THE DECLARATION
---------------------------------------------------------
ci_predict_pin_v1_0.load_declaration already rejects a probability outside
[0,1] before a pin comment is ever posted. This step calls
nf_ledger_v0_1.check_p again at the point the PIN event is actually built, so
the ledger's own tested guarantee — a bad p cannot enter it, from any caller
— holds regardless of what posted the comment.

EVENT ORDER MATTERS
---------------------
nf_ledger_v0_1.project() requires a TOKEN to exist before any PIN or RESOLVE
that references it; this tool always emits TOKEN, then PIN, then RESOLVE, in
that order, per check, matching cmd_build's own ordering.

IDEMPOTENCY
------------
Before appending, this tool reads the existing ledger and skips any check
whose token_id is already present — a PR can be consolidated more than once
without double-appending. The existing chain is verified before any new
event is built from it, so a corrupt checked-in ledger is refused up front
rather than mutated and only found broken afterward.

Usage:
  python3 tools/ci_predict_consolidate_v1_0.py consolidate \\
      --repo OWNER/REPO --pr 123 --ledger ledgers/CI_PREDICT_LEDGER.jsonl
  python3 tools/ci_predict_consolidate_v1_0.py --smoke-test
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nf_ledger_v0_1 as engine  # noqa: E402  (the ledger's own hashing/appending)
import ci_predict_resolve_v1_0 as resolver  # noqa: E402  (trust filter + resolution logic)

TOOL_NAME = "ci_predict_consolidate"
TOOL_VERSION = "1.0.0"
DEFAULT_LEDGER = "ledgers/CI_PREDICT_LEDGER.jsonl"


class LedgerCorrupt(RuntimeError):
    """Raised when the existing ledger fails verification. Never appended to."""


def collect_trusted_pins(comments: List[dict]) -> Dict[str, dict]:
    """The latest trusted pin per distinct head_sha seen in these comments.

    Several pushes to the same PR each get their own pin; each is kept, keyed
    by its own head_sha, so a check resolved late against an older push is
    still attributable to the prediction actually made for that commit.
    """
    per_sha: Dict[str, list] = {}
    for comment in comments:
        if not resolver.is_trusted(comment):
            continue
        payload = resolver.extract_payload(comment.get("body", ""), resolver.PIN_MARKER)
        if payload and payload.get("head_sha"):
            per_sha.setdefault(payload["head_sha"], []).append(
                (comment.get("created_at", ""), payload)
            )
    latest: Dict[str, dict] = {}
    for head_sha, candidates in per_sha.items():
        candidates.sort(key=lambda pair: pair[0])
        latest[head_sha] = candidates[-1][1]
    return latest


def commit_date_only(committed_at: str) -> str:
    """The YYYY-MM-DD portion of a git commit's ISO 8601 timestamp.

    nf_ledger_v0_1's TOKEN.date is a plain date; a missing/unparseable anchor
    becomes an empty string, never today's date — a token must never claim a
    commit anchor it does not actually have.
    """
    return committed_at[:10] if len(committed_at) >= 10 and committed_at[4] == "-" else ""


def token_id_for(head_sha: str, check_name: str) -> str:
    """Deterministic id, unique per (commit, check).

    A readable slug alone is not injective: "a b" and "a-b" both slug to
    "a-b", and a punctuation-only name slugs to empty. An 8-hex digest of the
    exact original name is appended so two distinct names can never collide,
    while the slug keeps the id readable at a glance.
    """
    slug = re.sub(r"[^a-z0-9]+", "-", check_name.lower()).strip("-") or "check"
    digest = hashlib.sha256(check_name.encode("utf-8")).hexdigest()[:8]
    return f"CI-{head_sha[:12]}-{slug}-{digest}"


def build_events(pin: dict, resolutions: dict, existing_ids: set,
                 pushed_at_date: str, start_seq: int = 1) -> List[dict]:
    """Pure: TOKEN+PIN+RESOLVE triples for checks that are resolved, new, and
    carry a real commit anchor.

    A check present in the pin but with no resolution yet contributes
    nothing — it is neither scored nor recorded as pending; the next
    consolidate run picks it up once a fresh check-runs fetch shows it
    terminal. A check whose anchor could not be determined (empty
    `pushed_at_date`) is skipped outright: see the module docstring on why an
    unanchored prediction must never enter the ledger as PRACTICE-dated.

    `seq` is assigned here, starting at `start_seq`, because
    nf_ledger_v0_1.verify() requires every event to carry a strictly
    incrementing sequence number and nf_ledger_v0_1.append() does not assign
    one itself — only its own cmd_build closure does, which this tool does
    not call (that closure is spec-file-shaped for the mesh use case).
    """
    if not pushed_at_date:
        return []

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
    """Existing TOKEN ids (for dedup) and the next free seq. Empty/1 if absent.

    Raises LedgerCorrupt if the checked-in ledger fails verification — this
    tool must never build new events on top of a chain it cannot trust, and
    must never be the one to silently paper over that by appending anyway.
    """
    if not ledger_path.exists():
        return set(), 1
    rows = engine.read(str(ledger_path))
    err = engine.verify(rows)
    if err:
        raise LedgerCorrupt(f"{ledger_path}: {err}")
    ids = {row["token_id"] for row in rows if row.get("type") == "TOKEN"}
    next_seq = (rows[-1]["seq"] + 1) if rows else 1
    return ids, next_seq


def run(repo: str, pr_number: str, ledger_path: Path) -> int:
    comments = resolver.gh_json_paginated(f"repos/{repo}/issues/{pr_number}/comments")
    pins = collect_trusted_pins(comments)
    if not pins:
        print(f"no trusted pin comments on PR {pr_number}; nothing to consolidate")
        return 0

    try:
        existing_ids, next_seq = load_ledger_state(ledger_path)
    except LedgerCorrupt as exc:
        print(f"FAIL: refusing to append — {exc}", file=sys.stderr)
        return 1

    all_events: List[dict] = []
    for head_sha, pin in pins.items():
        check_runs = resolver.gh_json_paginated(
            f"repos/{repo}/commits/{head_sha}/check-runs", key="check_runs"
        )
        resolutions = resolver.compute_resolutions(pin, check_runs)
        built = build_events(
            pin, resolutions, existing_ids,
            pushed_at_date=commit_date_only(pin.get("committed_at", "")),
            start_seq=next_seq,
        )
        all_events.extend(built)
        next_seq += len(built)
        existing_ids.update(e["token_id"] for e in built if e["type"] == "TOKEN")

    if not all_events:
        print("nothing new to append (all resolved checks already recorded, "
              "none resolved yet, or no anchor available)")
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
        "predictor": "Claude Code", "committed_at": "2026-09-12T10:00:00Z",
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

    # An empty anchor refuses the check entirely, never falls back to PRACTICE.
    ok = ok and build_events(pin, resolutions, set(), pushed_at_date="") == []

    ok = ok and commit_date_only("2026-09-12T10:00:00-07:00") == "2026-09-12"
    ok = ok and commit_date_only("") == ""
    ok = ok and commit_date_only("not-a-date") == ""

    # token_id_for is injective across names that would collide after slugging.
    a = token_id_for("a" * 40, "a b")
    b = token_id_for("a" * 40, "a-b")
    ok = ok and a != b
    ok = ok and token_id_for("a" * 40, "!!!") != token_id_for("a" * 40, "???")

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

        # A corrupted checked-in ledger refuses to accept new events at all.
        corrupt_ledger = Path(workdir) / "corrupt.jsonl"
        engine.append(str(corrupt_ledger), events, "0" * 64)
        corrupt_rows = engine.read(str(corrupt_ledger))
        corrupt_rows[0]["hash"] = "0" * 64
        with open(corrupt_ledger, "w", encoding="utf-8") as handle:
            import json as _json
            for row in corrupt_rows:
                handle.write(_json.dumps(row) + "\n")
        try:
            load_ledger_state(corrupt_ledger)
            ok = False
        except LedgerCorrupt:
            pass

    # An untrusted commenter's pin is never collected, even for a real head_sha.
    forged_body = "not a real pin, just text with the marker below\n" + \
        resolver.PIN_MARKER + '\n```json\n{"head_sha": "' + ("a" * 40) + '"}\n```'
    trusted_pins = collect_trusted_pins(
        [{"body": forged_body, "user": {"login": "some-collaborator"}, "created_at": "x"}]
    )
    ok = ok and trusted_pins == {}

    print("✓ Smoke test PASSED" if ok else "✗ Smoke test FAILED")
    return ok


def main() -> int:
    import argparse
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
