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
import contextlib
import fcntl
import hashlib
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nf_ledger_v0_1 as engine  # noqa: E402  (the ledger's own hashing/appending)

TOOL_NAME = "lifecycle_predict"
TOOL_VERSION = "1.0.0"
DEFAULT_LEDGER = "ledgers/LIFECYCLE_PREDICT_LEDGER.jsonl"


class LedgerCorrupt(RuntimeError):
    """Raised when the existing ledger fails verification. Never appended to."""


@contextlib.contextmanager
def _locked(ledger_path: Path):
    """Serializes the read-build-append critical section against a concurrent
    pin/resolve on the same ledger file. Without this, two invocations can
    each read the same next_seq/last_hash and append events that collide,
    corrupting the hash chain (only caught after the fact by verify())."""
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = ledger_path.with_name(ledger_path.name + ".lock")
    with open(lock_path, "w", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)


def _minutes_between(start_iso: str, end_iso: str) -> float:
    """Elapsed minutes between two engine.now()-style ISO 8601 timestamps."""
    return (datetime.fromisoformat(end_iso) - datetime.fromisoformat(start_iso)).total_seconds() / 60.0


def slugify(text: str) -> str:
    """A short, readable, non-injective identifier fragment."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "x"


def new_episode_id(action: str, target: str) -> str:
    """A fresh identifier for one pin episode. Includes a time-based
    component and a collision-resistant suffix (64 bits, from the current
    monotonic clock) so two pins in the same second for the same
    action/target get distinct episode ids — and therefore distinct token
    ids, since token_id_for derives from episode_id. cmd_pin additionally
    checks the generated token ids against the ledger's existing ones while
    holding the lock, so even the residual chance of a collision here is
    caught rather than silently overwriting an unrelated prediction.
    """
    stamp = time.strftime("%Y%m%dT%H%M%S", time.gmtime())
    suffix = hashlib.sha256(f"{time.monotonic_ns()}".encode()).hexdigest()[:16]
    return f"LC-{stamp}-{slugify(action)}-{slugify(target)}-{suffix}"


def token_id_for(episode_id: str, field: str) -> str:
    """Deterministic id, unique per (episode, field).

    A 64-bit digest suffix guards against two field names slugging to the
    same string, the same collision class fixed in ci_predict_consolidate's
    token_id_for. build_pin_events additionally rejects any duplicate
    token id generated within one batch outright, rather than relying on
    digest length alone to make that collision merely unlikely.
    """
    digest = hashlib.sha256(field.encode("utf-8")).hexdigest()[:16]
    return f"{episode_id}:{slugify(field)}-{digest}"


def _read_ledger_or_corrupt(ledger_path: Path) -> List[dict]:
    """engine.read(), with a truncated/unreadable file folded into
    LedgerCorrupt instead of raising JSONDecodeError/OSError past callers
    that only catch LedgerCorrupt."""
    try:
        return engine.read(str(ledger_path))
    except (ValueError, OSError) as exc:
        raise LedgerCorrupt(f"{ledger_path}: unreadable — {exc}") from exc


def load_ledger_state(ledger_path: Path) -> Tuple[set, int]:
    """Existing TOKEN ids and the next free seq. Raises LedgerCorrupt if the
    existing chain fails verification, or if any row is a well-formed JSON
    value that is nonetheless not a usable event (not an object, or missing
    a field verify()/this function reads) — never build on a chain we
    cannot trust or even fully parse as ledger rows."""
    if not ledger_path.exists():
        return set(), 1
    rows = _read_ledger_or_corrupt(ledger_path)
    try:
        err = engine.verify(rows)
        if err:
            raise LedgerCorrupt(f"{ledger_path}: {err}")
        ids = {row["token_id"] for row in rows if row.get("type") == "TOKEN"}
        next_seq = (rows[-1]["seq"] + 1) if rows else 1
    except LedgerCorrupt:
        raise
    except (KeyError, AttributeError, TypeError) as exc:
        raise LedgerCorrupt(f"{ledger_path}: malformed row — {exc}") from exc
    return ids, next_seq


def build_pin_events(episode_id: str, action: str, target: str, predictor: str,
                     expected: Dict[str, dict], window_minutes: int,
                     pinned_at: str, start_seq: int) -> List[dict]:
    """Pure: TOKEN+PIN pairs, one per expected field, in that order.

    Mirrors ci_predict_consolidate.build_events's TOKEN-before-PIN ordering,
    required by nf_ledger_v0_1.project(). `p` is validated by engine.check_p,
    the same refusal every other caller of this engine goes through.
    window_minutes is validated here too, not only in cmd_pin, so a caller
    using this function directly cannot bypass the CLI's guard and write a
    claim like "within -5 minutes" that could never resolve as YES.
    """
    if window_minutes <= 0:
        raise ValueError(f"window_minutes must be positive, got {window_minutes}")

    events: List[dict] = []
    seq = start_seq
    seen_token_ids: set = set()
    for field, spec in expected.items():
        if spec.get("p") is None:
            raise ValueError(f"missing probability for field {field!r} — p is required in [0,1]")
        token_id = token_id_for(episode_id, field)
        if token_id in seen_token_ids:
            raise ValueError(
                f"token id collision within this pin batch for field {field!r} "
                f"({token_id!r}) — refusing to silently overwrite another field's prediction"
            )
        seen_token_ids.add(token_id)
        events.append({
            "seq": seq, "type": "TOKEN", "at": pinned_at, "by": "lifecycle-predict",
            "token_id": token_id, "practice": "lifecycle-predict",
            "title": f"{action} on {target}: {field}",
            "date": pinned_at[:10], "date_source": "PRACTICE", "owner_add": False,
            "state": "DATED",
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

    The claim is time-bound ("will be X within N minutes"): an observation
    taken after the pin's window has elapsed cannot confirm the claim, even
    if the value now matches, so it scores NO rather than YES. This is the
    same reasoning ci_predict applies to a stale head_sha — an outcome
    observed outside the window the prediction was actually about is not
    evidence the prediction held.
    """
    if not source.strip():
        raise ValueError("--source must not be blank — it is the outcome's provenance")
    if not ledger_path.exists():
        raise ValueError(f"no ledger at {ledger_path} — nothing to resolve against")

    try:
        rows = _read_ledger_or_corrupt(ledger_path)
        already_resolved = {r["token_id"] for r in rows if r.get("type") == "RESOLVE"}
        pins_for_episode = [
            r for r in rows if r.get("type") == "PIN" and r.get("episode_id") == episode_id
        ]
    except LedgerCorrupt:
        raise
    except (KeyError, AttributeError, TypeError) as exc:
        raise LedgerCorrupt(f"{ledger_path}: malformed row — {exc}") from exc

    if not pins_for_episode:
        raise ValueError(f"no PIN events found for episode {episode_id!r}")

    try:
        known_fields = {pin["field"] for pin in pins_for_episode}
    except (KeyError, AttributeError, TypeError) as exc:
        raise LedgerCorrupt(f"{ledger_path}: malformed PIN row — {exc}") from exc
    unknown_fields = set(observed) - known_fields
    if unknown_fields:
        raise ValueError(
            f"observed field(s) {sorted(unknown_fields)} do not match any PIN in "
            f"episode {episode_id!r} (known fields: {sorted(known_fields)})"
        )

    events: List[dict] = []
    seq = start_seq
    try:
        for pin in pins_for_episode:
            field = pin["field"]
            token_id = pin["target"]
            if token_id in already_resolved:
                continue
            if field not in observed:
                continue
            actual = observed[field]
            elapsed_minutes = _minutes_between(pin["at"], resolved_at)
            within_window = 0 <= elapsed_minutes <= pin["window_minutes"]
            outcome = "YES" if (actual == pin["predicted_value"] and within_window) else "NO"
            events.append({
                "seq": seq, "type": "RESOLVE", "at": resolved_at,
                "by": "lifecycle-predict",
                "token_id": token_id, "outcome": outcome, "source": source,
                "elapsed_minutes": round(elapsed_minutes, 3), "within_window": within_window,
            })
            seq += 1
    except (KeyError, AttributeError, TypeError) as exc:
        raise LedgerCorrupt(f"{ledger_path}: malformed PIN row — {exc}") from exc
    return events


def cmd_pin(args: argparse.Namespace) -> int:
    ledger_path = Path(args.ledger)

    if args.window_minutes <= 0:
        print(f"FAIL: --window-minutes must be positive, got {args.window_minutes}",
              file=sys.stderr)
        return 2

    expected: Dict[str, dict] = {}
    try:
        for spec in args.expect:
            field, rest = spec.split("=", 1)
            value, p = rest.rsplit(":", 1)
            expected[field] = {"value": value, "p": float(p)}
    except ValueError:
        print(f"FAIL: --expect must be FIELD=VALUE:P, got {spec!r}", file=sys.stderr)
        return 2
    if not expected:
        print("FAIL: at least one --expect is required", file=sys.stderr)
        return 2

    with _locked(ledger_path):
        try:
            existing_ids, next_seq = load_ledger_state(ledger_path)
        except LedgerCorrupt as exc:
            print(f"FAIL: refusing to pin — {exc}", file=sys.stderr)
            return 1

        episode_id = new_episode_id(args.action, args.target)
        try:
            events = build_pin_events(
                episode_id, args.action, args.target, args.predictor, expected,
                args.window_minutes, engine.now(), next_seq,
            )
        except ValueError as exc:
            print(f"FAIL: {exc}", file=sys.stderr)
            return 2

        new_token_ids = {e["token_id"] for e in events if e["type"] == "TOKEN"}
        colliding = new_token_ids & existing_ids
        if colliding:
            print(f"FAIL: token id collision {sorted(colliding)} — refusing to overwrite "
                  f"an existing prediction", file=sys.stderr)
            return 1

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

    if not args.observe:
        print("FAIL: at least one --observe is required", file=sys.stderr)
        return 2

    observed = {}
    try:
        for spec in args.observe:
            field, value = spec.split("=", 1)
            observed[field] = value
    except ValueError:
        print(f"FAIL: --observe must be FIELD=VALUE, got {spec!r}", file=sys.stderr)
        return 2

    with _locked(ledger_path):
        try:
            _, next_seq = load_ledger_state(ledger_path)
        except LedgerCorrupt as exc:
            print(f"FAIL: refusing to resolve — {exc}", file=sys.stderr)
            return 1

        try:
            events = build_resolve_events(
                ledger_path, args.episode, observed, args.source, engine.now(), next_seq
            )
        except LedgerCorrupt as exc:
            print(f"FAIL: refusing to resolve — {exc}", file=sys.stderr)
            return 1
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

        # A value that arrives correct but after the pin's own window has
        # elapsed does not confirm a time-bound claim — it must score NO,
        # not YES, even though the observed value matches exactly.
        deadline_episode = new_episode_id("restart_service", "svc-late")
        deadline_pin = build_pin_events(
            deadline_episode, "restart_service", "svc-late", "Claude Code",
            {"http_health": {"value": "200", "p": 0.9}},
            window_minutes=5, pinned_at="2026-09-13T00:00:00+00:00", start_seq=1,
        )
        deadline_ledger = Path(workdir) / "deadline.jsonl"
        engine.append(str(deadline_ledger), deadline_pin, "0" * 64)
        late = build_resolve_events(
            deadline_ledger, deadline_episode, {"http_health": "200"}, "manual check",
            "2026-09-13T00:11:00+00:00", 3,  # 11 minutes later, window was 5
        )
        ok = ok and len(late) == 1 and late[0]["outcome"] == "NO"
        ok = ok and late[0]["within_window"] is False

        # The builder itself refuses a non-positive window, not only cmd_pin
        # — a direct caller cannot bypass the CLI's guard.
        try:
            build_pin_events(
                new_episode_id("a", "b"), "a", "b", "Claude Code",
                {"x": {"value": "1", "p": 0.5}}, -5, "2026-09-13T00:00:00+00:00", 1,
            )
            ok = False
        except ValueError:
            pass

        # A blank source is refused — it is the outcome's provenance.
        try:
            build_resolve_events(ledger, episode_id, {"http_health": "200"}, "   ",
                                 "2026-09-13T00:06:00+00:00", seq2)
            ok = False
        except ValueError:
            pass

        # Resolving against a ledger that does not exist is refused, not an
        # uncaught FileNotFoundError.
        try:
            build_resolve_events(Path(workdir) / "never-created.jsonl", "LC-x",
                                 {"x": "y"}, "manual check",
                                 "2026-09-13T00:06:00+00:00", 1)
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

        # An unresolved pin must still be scoreable by the shared engine's own
        # projection/outcome path — pin_outcome() indexes tk["state"] before
        # any RESOLVE event exists, so a PRACTICE-dated TOKEN must carry
        # state="DATED" from the start, the same as the engine's own builder.
        unresolved_tokens, unresolved_pins = engine.project(pin_events)
        for unresolved_pin in unresolved_pins.values():
            ok = ok and engine.pin_outcome(unresolved_pin, unresolved_tokens) is None

        # A missing probability is refused too — check_p's own None passthrough
        # would otherwise let an unscoreable PIN through silently.
        try:
            build_pin_events(
                new_episode_id("a", "b"), "a", "b", "Claude Code",
                {"x": {"value": "1", "p": None}}, 5, "2026-09-13T00:00:00+00:00", 1,
            )
            ok = False
        except ValueError:
            pass

        # An observed field that matches no PIN in the episode (a typo) is
        # refused, distinctly from the legitimate already-resolved no-op.
        try:
            build_resolve_events(ledger, episode_id, {"no_such_field": "x"},
                                 "manual check", "2026-09-13T00:06:00+00:00", seq2)
            ok = False
        except ValueError:
            pass

        # A resolution timestamped before its own pin (clock skew, or a
        # backdated call) must not count as within-window just because the
        # gap is small in magnitude.
        skew_episode = new_episode_id("restart_service", "svc-skew")
        skew_pin = build_pin_events(
            skew_episode, "restart_service", "svc-skew", "Claude Code",
            {"http_health": {"value": "200", "p": 0.9}},
            window_minutes=5, pinned_at="2026-09-13T00:10:00+00:00", start_seq=1,
        )
        skew_ledger = Path(workdir) / "skew.jsonl"
        engine.append(str(skew_ledger), skew_pin, "0" * 64)
        skewed = build_resolve_events(
            skew_ledger, skew_episode, {"http_health": "200"}, "manual check",
            "2026-09-13T00:05:00+00:00", 3,  # 5 minutes BEFORE the pin
        )
        ok = ok and len(skewed) == 1 and skewed[0]["outcome"] == "NO"
        ok = ok and skewed[0]["within_window"] is False

        # Tamper is still caught.
        tampered = engine.read(str(ledger))
        tampered[-1]["outcome"] = "YES"
        ok = ok and engine.verify(tampered) is not None

        # A truncated/malformed ledger file is folded into LedgerCorrupt, not
        # a raw JSONDecodeError past callers that only catch LedgerCorrupt.
        truncated = Path(workdir) / "truncated.jsonl"
        truncated.write_text("{not valid json}\n", encoding="utf-8")
        try:
            load_ledger_state(truncated)
            ok = False
        except LedgerCorrupt:
            pass

        # A syntactically valid JSON row that is nonetheless missing a field
        # verify()/this module reads (here: "hash") must also fold into
        # LedgerCorrupt, not a raw KeyError.
        import json as _json2
        missing_field = Path(workdir) / "missing_field.jsonl"
        missing_field.write_text(
            _json2.dumps({"seq": 1, "type": "TOKEN", "token_id": "x", "prev_hash": "0" * 64}) + "\n",
            encoding="utf-8",
        )
        try:
            load_ledger_state(missing_field)
            ok = False
        except LedgerCorrupt:
            pass

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
