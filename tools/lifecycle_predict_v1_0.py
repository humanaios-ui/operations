#!/usr/bin/env python3
"""
lifecycle_predict_v1_0.py
Builder v1.7 compliant
HumanAIOS — Stage 3 of the execution-grounded calibration plan

PIN/RESOLVE for any lifecycle action with an observable post-state: a service
restart, a redeploy, a health check after a config change — anything where an
operator can state "I expect X to be true within N minutes" before doing the
thing, and then check whether it was. Reuses tools/nf_ledger_v0_1.py's own
event functions unchanged, exactly as ci_predict_*.py does for CI checks;
this is the second, non-CI instance of the same PIN/RESOLVE shape applied to
a different subject.

WHY GENERIC OVER "RESTART", NOT RAILWAY-SPECIFIC
---------------------------------------------------
The predicted-vs-observed shape does not care whether the action was a
Railway restart, a redeploy, a DNS cutover, or a database failover. `action`
and `target` are free-text labels; `expected`/`observed` are field->value
maps. This keeps the tool usable for the next lifecycle prediction without a
rewrite, matching prs_run.py's own "nothing in it is AI-specific" property
one level up: nothing in this is Railway-specific either.

WHY THIS NEVER EXECUTES THE ACTION ITSELF
---------------------------------------------
A service restart is outward-facing and briefly disrupts real traffic. This
tool only records a prediction and later records an observation; it holds no
credentials for Railway, AWS, or anything else, and calls no such API. The
caller (a human, or an agent that has separately confirmed it should proceed)
performs the actual action through whatever system owns it, then supplies
the observed state here. This mirrors the same separation ci_predict_pin
keeps between "declare" and "execute": the declaring code is never the code
with the power to make its own prediction true.

THE ANCHOR HERE IS LEDGER ORDER, NOT A GITHUB COMMENT
---------------------------------------------------------
ci_predict_pin's anchor is a git commit's timestamp, because its predictions
are authored by whoever opens a PR and need a check even the PR author can't
forge. A lifecycle prediction is a first-party operational action: the
operator invoking `pin` is the same party who will invoke `resolve` and the
same party who decides whether to act at all. The append-only, hash-chained
ledger itself is the anchor — a PIN event's position and hash are fixed the
moment it is written, and `resolve` skips any token that already carries a
RESOLVE event (see build_resolve_events below), so a prediction cannot be
quietly rewritten after the fact once it is in the ledger. This is
weaker than ci_predict's model against a malicious operator, and stronger
than nothing: an operator who wanted to cheat would have to edit the ledger
file directly, which verify() catches (this is exactly the property
Stage 1/2 tested against tampering).

EXPECTED / OBSERVED SHAPE
----------------------------
`pin` takes a dict of field -> {"value": <predicted value>, "p": <0..1>}.
`resolve` takes a dict of field -> <observed value>. A field predicted but
not yet observed contributes nothing (VOID by omission, matching
ci_predict's "silence means ask again later, never predicted correctly").
Comparison is exact equality on the value; the caller normalizes upstream
(e.g. "200" vs 200) — this tool does not guess at type coercion.

Usage:
  python3 tools/lifecycle_predict_v1_0.py pin \\
      --ledger ledgers/LIFECYCLE_PREDICT_LEDGER.jsonl \\
      --action restart_service --target "railway:sweet-perfection/operations" \\
      --predictor "Claude Code" --window-minutes 5 \\
      --expect http_health=200:0.85 --expect deploy_status=SUCCESS:0.9
  python3 tools/lifecycle_predict_v1_0.py resolve \\
      --ledger ledgers/LIFECYCLE_PREDICT_LEDGER.jsonl \\
      --episode LC-<id> --source "railway get-status at 2026-09-13T00:00Z" \\
      --observe http_health=200 --observe deploy_status=SUCCESS
  python3 tools/lifecycle_predict_v1_0.py --smoke-test
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nf_ledger_v0_1 as engine  # noqa: E402  (the ledger's own hashing/appending)

TOOL_NAME = "lifecycle_predict"
TOOL_VERSION = "1.0.0"
DEFAULT_LEDGER = "ledgers/LIFECYCLE_PREDICT_LEDGER.jsonl"


class LedgerCorrupt(RuntimeError):
    """Raised when the existing ledger fails verification. Never appended to."""


def slugify(text: str) -> str:
    """A short, readable, non-injective identifier fragment."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "x"


def new_episode_id(action: str, target: str) -> str:
    """A fresh identifier for one pin episode. Includes a time-based
    component and a short random-ish suffix (from the current monotonic
    clock) so two pins in the same second for the same action/target still
    get distinct episode ids; collision would only merge two unrelated
    predictions' tokens, which token_id_for's digest suffix (below) also
    guards against independently.
    """
    stamp = time.strftime("%Y%m%dT%H%M%S", time.gmtime())
    suffix = hashlib.sha256(f"{time.monotonic_ns()}".encode()).hexdigest()[:6]
    return f"LC-{stamp}-{slugify(action)}-{slugify(target)}-{suffix}"


def token_id_for(episode_id: str, field: str) -> str:
    """Deterministic id, unique per (episode, field).

    Digest suffix guards against two field names slugging to the same
    string, the same collision class fixed in ci_predict_consolidate's
    token_id_for.
    """
    digest = hashlib.sha256(field.encode("utf-8")).hexdigest()[:8]
    return f"{episode_id}:{slugify(field)}-{digest}"


def load_ledger_state(ledger_path: Path) -> Tuple[set, int]:
    """Existing TOKEN ids and the next free seq. Raises LedgerCorrupt if the
    existing chain fails verification — never build on a chain we cannot
    trust."""
    if not ledger_path.exists():
        return set(), 1
    rows = engine.read(str(ledger_path))
    err = engine.verify(rows)
    if err:
        raise LedgerCorrupt(f"{ledger_path}: {err}")
    ids = {row["token_id"] for row in rows if row.get("type") == "TOKEN"}
    next_seq = (rows[-1]["seq"] + 1) if rows else 1
    return ids, next_seq


def build_pin_events(episode_id: str, action: str, target: str, predictor: str,
                     expected: Dict[str, dict], window_minutes: int,
                     pinned_at: str, start_seq: int) -> List[dict]:
    """Pure: TOKEN+PIN pairs, one per expected field, in that order.

    Mirrors ci_predict_consolidate.build_events's TOKEN-before-PIN ordering,
    required by nf_ledger_v0_1.project(). `p` is validated by engine.check_p,
    the same refusal every other caller of this engine goes through.
    """
    events: List[dict] = []
    seq = start_seq
    for field, spec in expected.items():
        token_id = token_id_for(episode_id, field)
        events.append({
            "seq": seq, "type": "TOKEN", "at": pinned_at, "by": "lifecycle-predict",
            "token_id": token_id, "practice": "lifecycle-predict",
            "title": f"{action} on {target}: {field}",
            "date": pinned_at[:10], "date_source": "PRACTICE", "owner_add": False,
        })
        seq += 1
        events.append({
            "seq": seq, "type": "PIN", "at": pinned_at, "by": "lifecycle-predict",
            "pin_id": f"{token_id}:{predictor}", "target": token_id,
            "predictor": predictor,
            "claim": f"{action} on {target}: {field} will be {spec['value']!r} "
                     f"within {window_minutes} minutes",
            "p": engine.check_p(spec["p"], token_id),
            "scoreable": True,
            "episode_id": episode_id, "action": action, "lc_target": target,
            "field": field, "predicted_value": spec["value"],
            "window_minutes": window_minutes,
        })
        seq += 1
    return events


def build_resolve_events(ledger_path: Path, episode_id: str, observed: Dict[str, object],
                         source: str, resolved_at: str, start_seq: int) -> List[dict]:
    """Pure-ish (reads the ledger to find this episode's pins): RESOLVE events
    for observed fields whose token has not already been resolved.

    A predicted field with no corresponding observed value is left alone —
    not scored, not marked missing — so a partial observation never fabricates
    an outcome for a field nobody actually checked.
    """
    rows = engine.read(str(ledger_path))
    already_resolved = {r["token_id"] for r in rows if r.get("type") == "RESOLVE"}
    pins_for_episode = [
        r for r in rows if r.get("type") == "PIN" and r.get("episode_id") == episode_id
    ]
    if not pins_for_episode:
        raise ValueError(f"no PIN events found for episode {episode_id!r}")

    events: List[dict] = []
    seq = start_seq
    for pin in pins_for_episode:
        field = pin["field"]
        token_id = pin["target"]
        if token_id in already_resolved:
            continue
        if field not in observed:
            continue
        actual = observed[field]
        outcome = "YES" if actual == pin["predicted_value"] else "NO"
        events.append({
            "seq": seq, "type": "RESOLVE", "at": resolved_at,
            "by": "lifecycle-predict",
            "token_id": token_id, "outcome": outcome, "source": source,
        })
        seq += 1
    return events


def cmd_pin(args: argparse.Namespace) -> int:
    ledger_path = Path(args.ledger)
    try:
        existing_ids, next_seq = load_ledger_state(ledger_path)
    except LedgerCorrupt as exc:
        print(f"FAIL: refusing to pin — {exc}", file=sys.stderr)
        return 1

    expected: Dict[str, dict] = {}
    for spec in args.expect:
        field, rest = spec.split("=", 1)
        value, p = rest.rsplit(":", 1)
        expected[field] = {"value": value, "p": float(p)}
    if not expected:
        print("FAIL: at least one --expect is required", file=sys.stderr)
        return 2

    episode_id = new_episode_id(args.action, args.target)
    events = build_pin_events(
        episode_id, args.action, args.target, args.predictor, expected,
        args.window_minutes, engine.now(), next_seq,
    )
    engine.append(str(ledger_path), events, engine.last_hash(str(ledger_path)))
    err = engine.verify(engine.read(str(ledger_path)))
    if err:
        print(f"FAIL post-pin verify: {err}", file=sys.stderr)
        return 1
    print(f"episode {episode_id}")
    for field, spec in expected.items():
        print(f"  {field} -> {spec['value']!r} (p={spec['p']})")
    return 0


def cmd_resolve(args: argparse.Namespace) -> int:
    ledger_path = Path(args.ledger)
    try:
        _, next_seq = load_ledger_state(ledger_path)
    except LedgerCorrupt as exc:
        print(f"FAIL: refusing to resolve — {exc}", file=sys.stderr)
        return 1

    observed = {}
    for spec in args.observe:
        field, value = spec.split("=", 1)
        observed[field] = value

    try:
        events = build_resolve_events(
            ledger_path, args.episode, observed, args.source, engine.now(), next_seq
        )
    except ValueError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    if not events:
        print("nothing to resolve (already resolved, or no matching observed field)")
        return 0

    engine.append(str(ledger_path), events, engine.last_hash(str(ledger_path)))
    err = engine.verify(engine.read(str(ledger_path)))
    if err:
        print(f"FAIL post-resolve verify: {err}", file=sys.stderr)
        return 1
    for event in events:
        print(f"  {event['token_id']} -> {event['outcome']}")
    return 0


def run_smoke_test() -> bool:
    """Full pipeline on a temp ledger: pin -> resolve -> verify -> real Brier."""
    import tempfile
    ok = True

    with tempfile.TemporaryDirectory() as workdir:
        ledger = Path(workdir) / "smoke.jsonl"

        expected = {
            "http_health": {"value": "200", "p": 0.9},
            "deploy_status": {"value": "SUCCESS", "p": 0.7},
        }
        episode_id = new_episode_id("restart_service", "svc-x")
        pin_events = build_pin_events(
            episode_id, "restart_service", "svc-x", "Claude Code", expected,
            window_minutes=5, pinned_at="2026-09-13T00:00:00+00:00", start_seq=1,
        )
        ok = ok and len(pin_events) == 4  # 2 fields x (TOKEN, PIN)
        engine.append(str(ledger), pin_events, "0" * 64)
        ok = ok and engine.verify(engine.read(str(ledger))) is None

        # Two distinct field names must never collide (same digest-suffix fix
        # as ci_predict_consolidate.token_id_for).
        ok = ok and (token_id_for(episode_id, "a b") != token_id_for(episode_id, "a-b"))

        # A resolve with only a partial observation scores only what was
        # actually checked, not the whole episode.
        _, seq_after_pin = load_ledger_state(ledger)
        partial_events = build_resolve_events(
            ledger, episode_id, {"http_health": "200"}, "manual check",
            "2026-09-13T00:03:00+00:00", seq_after_pin,
        )
        ok = ok and len(partial_events) == 1
        ok = ok and partial_events[0]["outcome"] == "YES"
        engine.append(str(ledger), partial_events, engine.last_hash(str(ledger)))
        ok = ok and engine.verify(engine.read(str(ledger))) is None

        # The still-unobserved field resolves later, correctly as a miss.
        _, seq2 = load_ledger_state(ledger)
        rest_events = build_resolve_events(
            ledger, episode_id, {"deploy_status": "CRASHED"}, "manual check",
            "2026-09-13T00:04:00+00:00", seq2,
        )
        ok = ok and len(rest_events) == 1 and rest_events[0]["outcome"] == "NO"
        engine.append(str(ledger), rest_events, engine.last_hash(str(ledger)))
        rows = engine.read(str(ledger))
        ok = ok and engine.verify(rows) is None

        # A real Brier score over this episode's two resolved pins:
        # http_health hit at p=0.9 -> 0.01; deploy_status missed at p=0.7 -> 0.49.
        tokens, pins = engine.project(rows)
        briers = []
        for pin in pins.values():
            outcome = engine.pin_outcome(pin, tokens)
            if outcome not in (None, "VOID"):
                briers.append((pin["p"] - outcome) ** 2)
        ok = ok and abs(sum(briers) / len(briers) - 0.25) < 1e-9

        # Re-resolving an already-resolved field is a no-op, not a duplicate.
        again = build_resolve_events(
            ledger, episode_id, {"http_health": "200"}, "manual check",
            "2026-09-13T00:05:00+00:00", seq2,
        )
        ok = ok and again == []

        # Unknown episode is refused, not silently ignored.
        try:
            build_resolve_events(ledger, "LC-does-not-exist", {"x": "y"}, "s",
                                 "2026-09-13T00:06:00+00:00", seq2)
            ok = False
        except ValueError:
            pass

        # A bad probability is refused by the shared engine.
        try:
            build_pin_events(
                new_episode_id("a", "b"), "a", "b", "Claude Code",
                {"x": {"value": "1", "p": 3.0}}, 5, "2026-09-13T00:00:00+00:00", 1,
            )
            ok = False
        except SystemExit:
            pass

        # Tamper is still caught.
        tampered = engine.read(str(ledger))
        tampered[-1]["outcome"] = "YES"
        ok = ok and engine.verify(tampered) is not None

        # A corrupted checked-in ledger refuses further pins/resolves.
        corrupt = Path(workdir) / "corrupt.jsonl"
        engine.append(str(corrupt), pin_events, "0" * 64)
        corrupt_rows = engine.read(str(corrupt))
        corrupt_rows[0]["hash"] = "0" * 64
        with open(corrupt, "w", encoding="utf-8") as handle:
            import json as _json
            for row in corrupt_rows:
                handle.write(_json.dumps(row) + "\n")
        try:
            load_ledger_state(corrupt)
            ok = False
        except LedgerCorrupt:
            pass

    print("✓ Smoke test PASSED" if ok else "✗ Smoke test FAILED")
    return ok


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=f"{TOOL_NAME} v{TOOL_VERSION}")
    parser.add_argument("--smoke-test", action="store_true")
    sub = parser.add_subparsers(dest="command")

    pin = sub.add_parser("pin")
    pin.add_argument("--ledger", default=DEFAULT_LEDGER)
    pin.add_argument("--action", required=True)
    pin.add_argument("--target", required=True)
    pin.add_argument("--predictor", required=True)
    pin.add_argument("--window-minutes", type=int, required=True)
    pin.add_argument("--expect", action="append", default=[],
                     metavar="FIELD=VALUE:P",
                     help="repeatable, e.g. --expect http_health=200:0.85")

    resolve = sub.add_parser("resolve")
    resolve.add_argument("--ledger", default=DEFAULT_LEDGER)
    resolve.add_argument("--episode", required=True)
    resolve.add_argument("--source", required=True,
                         help="what was checked to get these values (a log query, "
                              "a URL, a dashboard) — the external anchor for the outcome")
    resolve.add_argument("--observe", action="append", default=[],
                         metavar="FIELD=VALUE",
                         help="repeatable, e.g. --observe http_health=200")

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.smoke_test:
        return 0 if run_smoke_test() else 1
    if args.command == "pin":
        return cmd_pin(args)
    if args.command == "resolve":
        return cmd_resolve(args)
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
