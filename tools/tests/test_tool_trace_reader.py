"""
test_tool_trace_reader.py
Builder v1.7 compliant
HumanAIOS

Covers Stage 5's consumer: a never-captured trace must read as None, an
empty-but-captured trace must read as [] (a distinct claim: "zero tools
called" vs "no trace exists"), a real trace round-trips through the hook's
own append path, and a tampered ledger is refused outright rather than
partially returned.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_DIR))

import tool_trace_reader_v1_0 as reader  # noqa: E402
import tool_trace_hook_v1_0 as hook  # noqa: E402
import nf_ledger_v0_1 as engine  # noqa: E402


def test_smoke_test_passes():
    assert reader.run_smoke_test()


def test_never_captured_session_reads_as_none(tmp_path):
    trace_dir = tmp_path / hook.DEFAULT_TRACE_DIR
    assert reader.load_tool_trace(trace_dir, "never-ran") is None


def test_captured_but_empty_session_reads_as_empty_list(tmp_path):
    trace_dir = tmp_path / hook.DEFAULT_TRACE_DIR
    trace_dir.mkdir(parents=True)
    (trace_dir / hook.ledger_filename("empty")).touch()
    assert reader.load_tool_trace(trace_dir, "empty") == []


def test_real_trace_round_trips_through_the_hook(tmp_path):
    trace_dir = tmp_path / hook.DEFAULT_TRACE_DIR
    hook.run_hook(
        {"hook_event_name": "PostToolUse", "session_id": "real",
         "tool_name": "Read", "tool_input": {"file_path": "/secret"}},
        tmp_path,
    )
    hook.run_hook(
        {"hook_event_name": "PostToolUse", "session_id": "real",
         "tool_name": "Bash", "tool_input": {"command": "rm -rf /"}},
        tmp_path,
    )
    trace = reader.load_tool_trace(trace_dir, "real")
    assert trace is not None
    assert len(trace) == 2
    assert trace[0]["tool_name"] == "Read"
    assert trace[1]["tool_name"] == "Bash"
    assert "/secret" not in json.dumps(trace)
    assert "rm -rf" not in json.dumps(trace)


def test_tampered_trace_refused_not_partially_returned(tmp_path):
    trace_dir = tmp_path / hook.DEFAULT_TRACE_DIR
    hook.run_hook(
        {"hook_event_name": "PostToolUse", "session_id": "real",
         "tool_name": "Read", "tool_input": {}},
        tmp_path,
    )
    ledger = trace_dir / hook.ledger_filename("real")
    rows = engine.read(str(ledger))
    rows[0]["tool_name"] = "Forged"
    with open(ledger, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")

    try:
        reader.load_tool_trace(trace_dir, "real")
        raise AssertionError("expected TraceCorrupt")
    except reader.TraceCorrupt:
        pass


def test_malformed_tool_call_row_raises_traceable_not_keyerror(tmp_path):
    """A TOOL_CALL row missing "seq" must raise TraceCorrupt, not an
    uncaught KeyError — engine.verify() alone doesn't validate which
    application-level fields a row carries, only the hash chain (Copilot
    review finding on PR #302)."""
    trace_dir = tmp_path / hook.DEFAULT_TRACE_DIR
    trace_dir.mkdir(parents=True)
    ledger = trace_dir / hook.ledger_filename("bad")
    row = {"type": "TOOL_CALL", "at": "x", "tool_name": "Read", "prev_hash": "0" * 64}
    row["hash"] = engine.sha(engine.canon(row))
    with open(ledger, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(row) + "\n")

    try:
        reader.load_tool_trace(trace_dir, "bad")
        raise AssertionError("expected TraceCorrupt")
    except reader.TraceCorrupt:
        pass


def test_cli_report_missing_session_prints_note(tmp_path, capsys):
    trace_dir = tmp_path / hook.DEFAULT_TRACE_DIR
    parser = reader.build_parser()
    args = parser.parse_args(["report", "--session-id", "ghost", "--trace-dir", str(trace_dir)])
    assert reader.cmd_report(args) == 0
    assert "no tool_trace captured" in capsys.readouterr().out


def test_cli_report_json_shape(tmp_path, capsys):
    trace_dir = tmp_path / hook.DEFAULT_TRACE_DIR
    hook.run_hook(
        {"hook_event_name": "PostToolUse", "session_id": "real",
         "tool_name": "Read", "tool_input": {}},
        tmp_path,
    )
    parser = reader.build_parser()
    args = parser.parse_args([
        "report", "--session-id", "real", "--trace-dir", str(trace_dir), "--json",
    ])
    assert reader.cmd_report(args) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["session_id"] == "real"
    assert len(out["tool_trace"]) == 1
    assert out["tool_trace"][0]["tool_name"] == "Read"


def test_cli_report_requires_session_id():
    assert reader.main(["report"]) == 2


def test_cli_report_on_corrupted_trace_exits_nonzero(tmp_path, capsys):
    trace_dir = tmp_path / hook.DEFAULT_TRACE_DIR
    hook.run_hook(
        {"hook_event_name": "PostToolUse", "session_id": "real",
         "tool_name": "Read", "tool_input": {}},
        tmp_path,
    )
    ledger = trace_dir / hook.ledger_filename("real")
    rows = engine.read(str(ledger))
    rows[0]["tool_name"] = "Forged"
    with open(ledger, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")

    parser = reader.build_parser()
    args = parser.parse_args(["report", "--session-id", "real", "--trace-dir", str(trace_dir)])
    assert reader.cmd_report(args) == 1
    assert "FAIL" in capsys.readouterr().err
