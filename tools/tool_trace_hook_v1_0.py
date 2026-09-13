#!/usr/bin/env python3
"""
tool_trace_hook_v1_0.py
Builder v1.7 compliant
HumanAIOS — Stage 5 of the execution-grounded calibration plan

A Claude Code PostToolUse hook. Wired via .claude/settings.json, this
script is invoked by the harness after every tool call, receives the
call's details as JSON on stdin, and appends one hash-chained TOOL_CALL
event to a per-session ledger under .claude/tool_traces/. Reuses
tools/nf_ledger_v0_1.py's own append()/read()/verify() unchanged — the
same hash-chain primitives Stages 1-4 use for PIN/RESOLVE, applied here
to a plain observation log instead of a prediction.

WHY THIS IS "CLAUDE-SIDE", UNLIKE STAGES 1-4
-------------------------------------------------
Stages 1-4 measure any predictor's declared/observed gap — human, Claude,
Copilot — through a substrate-agnostic ledger schema. This hook measures
one specific thing: what tools the Claude Code harness actually invoked
during a session. It is deliberately narrower and lower in the stack: it
grounds a claim like "the agent used tools X, Y, Z in this session"
against something the model's own generated text cannot edit, because the
hook fires from the harness after the tool call already happened, not
from anything the model wrote.

WHAT THIS DOES AND DOES NOT PROVE ABOUT FORGERY
-----------------------------------------------------
During NORMAL operation, the model does not choose what gets logged or
when: every tool call triggers this hook automatically, and the model has
no code path to suppress a real call from being logged or to fabricate a
call that never happened, because it never invokes this script directly.
The hash chain additionally means an in-place edit to an existing entry
breaks verification (see tools/lifecycle_predict_v1_0.py's identical
property and its documented limitations, which apply here unchanged).

This is NOT a claim that a model with shell access is cryptographically
prevented from forging the file. In this environment the agent can read
this script, read the hashing algorithm, and — if it deliberately chose
to — compute a consistent next hash and append a fabricated entry by
hand, exactly as it could hand-edit any other file it has permission to
write. Closing that gap fully needs a signing key genuinely outside the
agent's own execution environment, which a local, full-filesystem-access
CLI session does not have. What this hook actually buys is: nothing
appears in the trace by the model's own initiative, and no real call goes
unrecorded, under the harness's own operation — not immunity to a
deliberately adversarial actor with shell access to its own trace file.

WHY IT NEVER BLOCKS THE TOOL CALL
---------------------------------------
By the time PostToolUse fires, the tool has already run. A logging bug
here must never surface as a broken session, so every failure path in
this script prints a note to stderr and exits 0 rather than raising —
the one deliberate exception to this codebase's usual fail-loud
discipline, because this script's job is passive observation, not
gatekeeping.

WHAT IS STORED, AND WHY NOT THE FULL TOOL INPUT/OUTPUT
------------------------------------------------------------
Only the tool name, the sorted top-level keys of tool_input, and a SHA256
digest of its canonical JSON are recorded — never the raw input or output.
A Write call's file content, a Bash command's full output, or any other
tool payload can be arbitrarily large or sensitive; a digest is enough to
later confirm two independently-held records agree without ever
committing that payload to the trace ledger itself.

Wiring (.claude/settings.json):
  "hooks": {
    "PostToolUse": [
      {"matcher": "*", "hooks": [
        {"type": "command",
         "command": "python3 \"$CLAUDE_PROJECT_DIR/tools/tool_trace_hook_v1_0.py\""}
      ]}
    ]
  }

Usage:
  echo '{"hook_event_name":"PostToolUse","session_id":"s1",
         "tool_name":"Read","tool_input":{"file_path":"x"}}' \\
      | python3 tools/tool_trace_hook_v1_0.py
  python3 tools/tool_trace_hook_v1_0.py --smoke-test
"""
from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nf_ledger_v0_1 as engine  # noqa: E402  (append/read/verify, unchanged)

TOOL_NAME = "tool_trace_hook"
TOOL_VERSION = "1.0.0"
DEFAULT_TRACE_DIR = ".claude/tool_traces"


def slugify(text: str) -> str:
    """A safe filename fragment. session_id comes from the harness, not
    the model, but this stays defensive against path traversal regardless."""
    return re.sub(r"[^A-Za-z0-9_-]+", "-", text).strip("-") or "unknown-session"


@contextlib.contextmanager
def _locked(ledger_path: Path):
    """Serializes the read-build-append critical section against a
    concurrent hook invocation for the same session (parallel tool calls
    can fire close together). Same pattern as lifecycle_predict_v1_0.py's
    _locked()."""
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = ledger_path.with_name(ledger_path.name + ".lock")
    with open(lock_path, "w", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)


def build_event(seq: int, session_id: str, tool_name: str, tool_input: dict, at: str) -> dict:
    """Pure: one TOOL_CALL event. Never carries the raw tool_input/output —
    see module docstring."""
    canonical = json.dumps(tool_input, sort_keys=True, default=str)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    keys = sorted(tool_input.keys()) if isinstance(tool_input, dict) else []
    return {
        "seq": seq, "type": "TOOL_CALL", "at": at, "by": "posttooluse-hook",
        "session_id": session_id, "tool_name": tool_name,
        "input_digest": digest, "input_keys": keys,
    }


def append_tool_call(ledger_path: Path, session_id: str, tool_name: str,
                     tool_input: dict, at: str) -> Optional[str]:
    """Appends one TOOL_CALL event under a file lock. Returns None on
    success, or a short reason string if the append was skipped (an
    existing corrupted chain — never extended, only reported) — callers
    that must not block still get to decide what, if anything, to do with
    the reason; this function itself never raises for a corrupted ledger,
    matching the hook's own must-never-block contract.
    """
    with _locked(ledger_path):
        existing: List[dict] = []
        if ledger_path.exists():
            try:
                existing = engine.read(str(ledger_path))
            except (ValueError, OSError) as exc:
                return f"existing ledger unreadable ({exc}) — not extending it"
            err = engine.verify(existing)
            if err:
                return f"existing ledger corrupted ({err}) — not extending it"

        next_seq = (existing[-1]["seq"] + 1) if existing else 1
        prev_hash = existing[-1]["hash"] if existing else "0" * 64
        event = build_event(next_seq, session_id, tool_name, tool_input, at)
        engine.append(str(ledger_path), [event], prev_hash)
    return None


def run_hook(payload: dict, project_dir: Path) -> Optional[str]:
    session_id = payload.get("session_id")
    if not isinstance(session_id, str) or not session_id.strip():
        session_id = "unknown-session"
    tool_name = payload.get("tool_name")
    if not isinstance(tool_name, str) or not tool_name.strip():
        tool_name = "unknown-tool"
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        tool_input = {}

    ledger_path = project_dir / DEFAULT_TRACE_DIR / f"{slugify(session_id)}.jsonl"
    return append_tool_call(ledger_path, session_id, tool_name, tool_input, engine.now())


def run_smoke_test() -> bool:
    """Simulates two hook invocations for one session and a corrupted-
    ledger case, without going through stdin/subprocess."""
    import tempfile
    ok = True

    with tempfile.TemporaryDirectory() as workdir:
        project_dir = Path(workdir)

        reason1 = run_hook(
            {"hook_event_name": "PostToolUse", "session_id": "sess-1",
             "tool_name": "Read", "tool_input": {"file_path": "/a"}},
            project_dir,
        )
        ok = ok and reason1 is None
        reason2 = run_hook(
            {"hook_event_name": "PostToolUse", "session_id": "sess-1",
             "tool_name": "Bash", "tool_input": {"command": "ls"}},
            project_dir,
        )
        ok = ok and reason2 is None

        ledger_path = project_dir / DEFAULT_TRACE_DIR / "sess-1.jsonl"
        rows = engine.read(str(ledger_path))
        ok = ok and len(rows) == 2
        ok = ok and engine.verify(rows) is None
        ok = ok and rows[0]["tool_name"] == "Read"
        ok = ok and rows[1]["tool_name"] == "Bash"
        ok = ok and rows[0]["session_id"] == "sess-1"
        # Raw input value is never stored verbatim, only the key name and a digest.
        ok = ok and "/a" not in json.dumps(rows[0])
        ok = ok and rows[0]["input_keys"] == ["file_path"]

        # A non-dict tool_input (defensive) doesn't crash the hook.
        reason3 = run_hook(
            {"hook_event_name": "PostToolUse", "session_id": "sess-2",
             "tool_name": "Weird", "tool_input": "not-a-dict"},
            project_dir,
        )
        ok = ok and reason3 is None

        # A missing/blank session_id falls back to a safe placeholder
        # rather than crashing or writing an unsafe path.
        reason4 = run_hook(
            {"hook_event_name": "PostToolUse", "tool_name": "Ghost", "tool_input": {}},
            project_dir,
        )
        ok = ok and reason4 is None
        ok = ok and (project_dir / DEFAULT_TRACE_DIR / "unknown-session.jsonl").exists()

        # A corrupted existing ledger is reported, never silently extended.
        corrupt_rows = engine.read(str(ledger_path))
        corrupt_rows[0]["outcome"] = "tampered"
        with open(ledger_path, "w", encoding="utf-8") as handle:
            for row in corrupt_rows:
                handle.write(json.dumps(row) + "\n")
        reason5 = run_hook(
            {"hook_event_name": "PostToolUse", "session_id": "sess-1",
             "tool_name": "Edit", "tool_input": {}},
            project_dir,
        )
        ok = ok and reason5 is not None and "corrupted" in reason5
        # The corrupted ledger was NOT extended — still 2 rows, not 3.
        post_rows = [json.loads(line) for line in ledger_path.read_text().splitlines()]
        ok = ok and len(post_rows) == 2

        # session_id path traversal attempt is neutralized into a safe,
        # contained filename rather than escaping the trace directory.
        run_hook(
            {"hook_event_name": "PostToolUse", "session_id": "../../etc/passwd",
             "tool_name": "X", "tool_input": {}},
            project_dir,
        )
        ok = ok and (project_dir / DEFAULT_TRACE_DIR / "etc-passwd.jsonl").exists()
        ok = ok and not (project_dir.parent.parent / "etc" / "passwd.jsonl").exists()

    print("✓ Smoke test PASSED" if ok else "✗ Smoke test FAILED")
    return ok


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=f"{TOOL_NAME} v{TOOL_VERSION}")
    parser.add_argument("--smoke-test", action="store_true")
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.smoke_test:
        return 0 if run_smoke_test() else 1

    # Everything below this point must never raise: a logging bug must
    # never surface as a broken tool call. See module docstring.
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception as exc:  # noqa: BLE001 - deliberate, see docstring
        print(f"{TOOL_NAME}: could not parse stdin ({exc}); not logging", file=sys.stderr)
        return 0

    if not isinstance(payload, dict):
        return 0
    if payload.get("hook_event_name") not in (None, "PostToolUse"):
        return 0

    project_dir_raw = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd")
    project_dir = Path(project_dir_raw) if project_dir_raw else Path(__file__).resolve().parents[1]

    try:
        reason = run_hook(payload, project_dir)
        if reason:
            print(f"{TOOL_NAME}: {reason}", file=sys.stderr)
    except Exception as exc:  # noqa: BLE001 - deliberate, see docstring
        print(f"{TOOL_NAME}: unexpected error ({exc}); not blocking the tool call", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
