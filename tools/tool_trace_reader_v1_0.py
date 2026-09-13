#!/usr/bin/env python3
"""
tool_trace_reader_v1_0.py
Builder v1.7 compliant
HumanAIOS — Stage 5 of the execution-grounded calibration plan

Reads a session's tool_trace ledger (written by tools/tool_trace_hook_v1_0.py's
PostToolUse hook) and emits the meta.tool_trace array the plan names: an
ordered, hash-chain-verified record of the tools that session actually
invoked. Read-only: never appends to any ledger.

WHY A MISSING TRACE RETURNS None, NOT AN EMPTY LIST
--------------------------------------------------------
An empty list would mean "this session called zero tools" — a real,
meaningful claim. No file at all means something else entirely: hooks
were never wired for this run, the session predates Stage 5, or this is
a non-Claude-Code substrate where no PostToolUse hook exists to fire.
Collapsing those into the same value would let an absent trace read as a
clean one. See the ACAT contract schemas' own description of this field
for the same distinction.

WHY A CORRUPTED LEDGER REFUSES RATHER THAN RETURNING WHAT IT CAN
------------------------------------------------------------------------
A hash-chain break means at least one entry cannot be trusted relative to
its neighbors. Returning the entries before the break and silently
dropping the rest would understate what happened; returning everything
including the broken tail would overstate what can be trusted. Refusing
outright, as every other ledger-reading tool in this codebase does, is
the same choice made consistently.

Usage:
  python3 tools/tool_trace_reader_v1_0.py report --session-id s1
  python3 tools/tool_trace_reader_v1_0.py report --session-id s1 --json
  python3 tools/tool_trace_reader_v1_0.py --smoke-test
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nf_ledger_v0_1 as engine  # noqa: E402  (read/verify, unchanged)
import tool_trace_hook_v1_0 as hook  # noqa: E402  (slugify, build_event, DEFAULT_TRACE_DIR)

TOOL_NAME = "tool_trace_reader"
TOOL_VERSION = "1.0.0"


class TraceCorrupt(RuntimeError):
    """Raised when a session's tool_trace ledger fails hash-chain verification."""


def load_tool_trace(trace_dir: Path, session_id: str) -> Optional[List[dict]]:
    """None if no trace was ever captured for this session; otherwise the
    ordered list of TOOL_CALL records, each {seq, at, tool_name,
    input_digest, input_keys} — never the raw tool input itself, since the
    ledger never stored it. Raises TraceCorrupt if the chain doesn't
    verify; never returns a partial list for a broken chain."""
    ledger_path = trace_dir / hook.ledger_filename(session_id)
    if not ledger_path.exists():
        return None
    try:
        rows = engine.read(str(ledger_path))
    except (ValueError, OSError) as exc:
        raise TraceCorrupt(f"{ledger_path}: unreadable — {exc}") from exc
    try:
        err = engine.verify(rows)
    except Exception as exc:  # noqa: BLE001 - verification failures must normalize to TraceCorrupt
        raise TraceCorrupt(f"{ledger_path}: verification failed — {exc}") from exc
    if err:
        raise TraceCorrupt(f"{ledger_path}: {err}")
    trace = []
    for row in rows:
        if not isinstance(row, dict):
            raise TraceCorrupt(f"{ledger_path}: row is not an object")
        if row.get("type") != "TOOL_CALL":
            raise TraceCorrupt(f"{ledger_path}: unexpected row type {row.get('type')!r}")
        required = ("seq", "at", "tool_name", "input_digest", "input_keys")
        missing = [field for field in required if field not in row]
        if missing:
            raise TraceCorrupt(
                f"{ledger_path}: TOOL_CALL row missing required field(s): {', '.join(missing)}"
            )
        trace.append({
            "seq": row["seq"], "at": row["at"],
            "tool_name": row["tool_name"],
            "input_digest": row["input_digest"],
            "input_keys": row["input_keys"],
        })
    return trace


def cmd_report(args: argparse.Namespace) -> int:
    trace_dir = Path(args.trace_dir)
    try:
        trace = load_tool_trace(trace_dir, args.session_id)
    except TraceCorrupt as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps({"session_id": args.session_id, "tool_trace": trace}, indent=2))
    else:
        if trace is None:
            print(f"{args.session_id}: no tool_trace captured "
                 f"(no hooks wired, pre-Stage-5, or a non-Claude-Code substrate)")
        elif not trace:
            print(f"{args.session_id}: tool_trace present but empty (zero tools called)")
        else:
            print(f"{args.session_id}: {len(trace)} tool call(s)")
            for entry in trace:
                print(f"  [{entry['seq']}] {entry['at']}  {entry['tool_name']}"
                     f"  keys={entry['input_keys']}")
    return 0


def run_smoke_test() -> bool:
    """Round-trips through the real hook's own append path, then verifies
    the reader's None/empty/populated/tamper distinctions."""
    import tempfile
    ok = True

    with tempfile.TemporaryDirectory() as workdir:
        project_dir = Path(workdir)
        trace_dir = project_dir / hook.DEFAULT_TRACE_DIR

        # No trace captured yet for this session.
        ok = ok and load_tool_trace(trace_dir, "never-ran") is None

        # A session with zero tool calls but an explicit (empty) ledger
        # is distinguishable from "never ran" — build one directly since
        # the hook itself only ever appends on an actual call.
        empty_ledger = trace_dir / hook.ledger_filename("empty-session")
        empty_ledger.parent.mkdir(parents=True, exist_ok=True)
        empty_ledger.touch()
        ok = ok and load_tool_trace(trace_dir, "empty-session") == []

        hook.run_hook(
            {"hook_event_name": "PostToolUse", "session_id": "real",
             "tool_name": "Read", "tool_input": {"file_path": "/x"}},
            project_dir,
        )
        hook.run_hook(
            {"hook_event_name": "PostToolUse", "session_id": "real",
             "tool_name": "Bash", "tool_input": {"command": "ls -la"}},
            project_dir,
        )
        trace = load_tool_trace(trace_dir, "real")
        ok = ok and trace is not None and len(trace) == 2
        ok = ok and trace[0]["tool_name"] == "Read"
        ok = ok and trace[1]["tool_name"] == "Bash"
        ok = ok and "/x" not in json.dumps(trace)  # raw value never stored, only the key name

        # A tampered ledger is refused outright, not partially returned.
        real_ledger = trace_dir / hook.ledger_filename("real")
        rows = engine.read(str(real_ledger))
        rows[0]["tool_name"] = "Forged"
        with open(real_ledger, "w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row) + "\n")
        try:
            load_tool_trace(trace_dir, "real")
            ok = False
        except TraceCorrupt:
            pass

        # A structurally malformed TOOL_CALL row (missing "seq") is refused
        # via TraceCorrupt, not an uncaught KeyError — engine.verify() alone
        # doesn't catch this since it only checks hash/prev_hash/sequence,
        # not which application-level fields a row carries.
        malformed_dir = project_dir / "malformed"
        malformed_ledger = malformed_dir / hook.ledger_filename("bad")
        malformed_ledger.parent.mkdir(parents=True, exist_ok=True)
        bad_row = {"type": "TOOL_CALL", "at": "x", "tool_name": "Read", "prev_hash": "0" * 64}
        bad_row["hash"] = engine.sha(engine.canon(bad_row))
        with open(malformed_ledger, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(bad_row) + "\n")
        try:
            load_tool_trace(malformed_dir, "bad")
            ok = False
        except TraceCorrupt:
            pass
        except KeyError:
            ok = False

        # A non-TOOL_CALL but otherwise hash-valid row is refused rather than
        # silently dropped into an empty/partial trace.
        unrelated_dir = project_dir / "unrelated"
        unrelated_ledger = unrelated_dir / hook.ledger_filename("odd")
        unrelated_ledger.parent.mkdir(parents=True, exist_ok=True)
        other_row = {"seq": 1, "type": "OPEN", "at": "x", "by": "Z1", "prev_hash": "0" * 64}
        other_row["hash"] = engine.sha(engine.canon(other_row))
        with open(unrelated_ledger, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(other_row) + "\n")
        try:
            load_tool_trace(unrelated_dir, "odd")
            ok = False
        except TraceCorrupt:
            pass

        # Verification exceptions are normalized to TraceCorrupt.
        original_verify = engine.verify
        try:
            engine.verify = lambda _rows: (_ for _ in ()).throw(KeyError("seq"))  # type: ignore[assignment]
            load_tool_trace(trace_dir, "empty-session")
            ok = False
        except TraceCorrupt:
            pass
        finally:
            engine.verify = original_verify

        # CLI round trip.
        parser = build_parser()
        args = parser.parse_args([
            "report", "--session-id", "empty-session", "--trace-dir", str(trace_dir), "--json",
        ])
        ok = ok and cmd_report(args) == 0

        args2 = parser.parse_args([
            "report", "--session-id", "real", "--trace-dir", str(trace_dir),
        ])
        ok = ok and cmd_report(args2) == 1  # still tampered from above

    print("✓ Smoke test PASSED" if ok else "✗ Smoke test FAILED")
    return ok


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=f"{TOOL_NAME} v{TOOL_VERSION}")
    parser.add_argument("--smoke-test", action="store_true")
    sub = parser.add_subparsers(dest="command")

    report = sub.add_parser("report")
    report.add_argument("--session-id", required=False)
    report.add_argument("--trace-dir", default=hook.DEFAULT_TRACE_DIR)
    report.add_argument("--json", action="store_true")

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.smoke_test:
        return 0 if run_smoke_test() else 1
    if args.command == "report":
        if not args.session_id:
            print("FAIL: --session-id is required", file=sys.stderr)
            return 2
        return cmd_report(args)
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
