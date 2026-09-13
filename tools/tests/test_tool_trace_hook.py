"""
test_tool_trace_hook.py
Builder v1.7 compliant
HumanAIOS

Covers Stage 5's producer: the PostToolUse hook must never store a raw
tool_input value (only key names and a digest), must never block the real
tool call regardless of internal failure, must refuse to extend a
corrupted existing chain, and must sanitize an untrusted session_id into
a safe, contained filename.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_DIR))

import tool_trace_hook_v1_0 as hook  # noqa: E402
import nf_ledger_v0_1 as engine  # noqa: E402


def test_smoke_test_passes():
    assert hook.run_smoke_test()


def test_run_hook_appends_hash_chained_event(tmp_path):
    reason = hook.run_hook(
        {"hook_event_name": "PostToolUse", "session_id": "s1",
         "tool_name": "Read", "tool_input": {"file_path": "/etc/hosts"}},
        tmp_path,
    )
    assert reason is None
    ledger = tmp_path / hook.DEFAULT_TRACE_DIR / hook.ledger_filename("s1")
    rows = engine.read(str(ledger))
    assert len(rows) == 1
    assert engine.verify(rows) is None
    assert rows[0]["tool_name"] == "Read"
    assert rows[0]["type"] == "TOOL_CALL"


def test_raw_tool_input_value_never_stored(tmp_path):
    hook.run_hook(
        {"hook_event_name": "PostToolUse", "session_id": "s1",
         "tool_name": "Write", "tool_input": {"file_path": "/x", "content": "SECRET-VALUE"}},
        tmp_path,
    )
    ledger = tmp_path / hook.DEFAULT_TRACE_DIR / hook.ledger_filename("s1")
    raw = ledger.read_text()
    assert "SECRET-VALUE" not in raw
    assert "/x" not in raw
    rows = engine.read(str(ledger))
    assert sorted(rows[0]["input_keys"]) == ["content", "file_path"]


def test_second_call_chains_onto_first(tmp_path):
    hook.run_hook(
        {"hook_event_name": "PostToolUse", "session_id": "s1",
         "tool_name": "Read", "tool_input": {}},
        tmp_path,
    )
    hook.run_hook(
        {"hook_event_name": "PostToolUse", "session_id": "s1",
         "tool_name": "Bash", "tool_input": {}},
        tmp_path,
    )
    ledger = tmp_path / hook.DEFAULT_TRACE_DIR / hook.ledger_filename("s1")
    rows = engine.read(str(ledger))
    assert len(rows) == 2
    assert rows[1]["prev_hash"] == rows[0]["hash"]
    assert engine.verify(rows) is None


def test_corrupted_ledger_is_not_extended(tmp_path):
    hook.run_hook(
        {"hook_event_name": "PostToolUse", "session_id": "s1",
         "tool_name": "Read", "tool_input": {}},
        tmp_path,
    )
    ledger = tmp_path / hook.DEFAULT_TRACE_DIR / hook.ledger_filename("s1")
    rows = engine.read(str(ledger))
    rows[0]["tool_name"] = "Tampered"
    with open(ledger, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")

    reason = hook.run_hook(
        {"hook_event_name": "PostToolUse", "session_id": "s1",
         "tool_name": "Edit", "tool_input": {}},
        tmp_path,
    )
    assert reason is not None
    assert "corrupted" in reason
    post_rows = [json.loads(line) for line in ledger.read_text().splitlines()]
    assert len(post_rows) == 1  # not extended


def test_missing_session_id_falls_back_to_safe_placeholder(tmp_path):
    reason = hook.run_hook(
        {"hook_event_name": "PostToolUse", "tool_name": "Read", "tool_input": {}},
        tmp_path,
    )
    assert reason is None
    assert (tmp_path / hook.DEFAULT_TRACE_DIR / hook.ledger_filename("unknown-session")).exists()


def test_path_traversal_session_id_is_contained(tmp_path):
    hook.run_hook(
        {"hook_event_name": "PostToolUse", "session_id": "../../etc/passwd",
         "tool_name": "Read", "tool_input": {}},
        tmp_path,
    )
    assert (tmp_path / hook.DEFAULT_TRACE_DIR / hook.ledger_filename("../../etc/passwd")).exists()
    assert not (tmp_path.parent / "etc" / "passwd.jsonl").exists()


def test_colliding_slugs_get_distinct_ledger_files(tmp_path):
    """slugify("a/b") == slugify("a-b"); ledger_filename() must not
    collapse two distinct session_ids onto one file (Copilot review
    finding on PR #302)."""
    assert hook.slugify("a/b") == hook.slugify("a-b")
    hook.run_hook(
        {"hook_event_name": "PostToolUse", "session_id": "a/b",
         "tool_name": "Read", "tool_input": {}},
        tmp_path,
    )
    hook.run_hook(
        {"hook_event_name": "PostToolUse", "session_id": "a-b",
         "tool_name": "Bash", "tool_input": {}},
        tmp_path,
    )
    ledger_ab_slash = tmp_path / hook.DEFAULT_TRACE_DIR / hook.ledger_filename("a/b")
    ledger_ab_dash = tmp_path / hook.DEFAULT_TRACE_DIR / hook.ledger_filename("a-b")
    assert ledger_ab_slash != ledger_ab_dash
    assert ledger_ab_slash.exists() and ledger_ab_dash.exists()
    rows_slash = engine.read(str(ledger_ab_slash))
    rows_dash = engine.read(str(ledger_ab_dash))
    assert len(rows_slash) == 1 and rows_slash[0]["tool_name"] == "Read"
    assert len(rows_dash) == 1 and rows_dash[0]["tool_name"] == "Bash"


def test_append_tool_call_reports_missing_hash_without_raising(tmp_path):
    """A malformed existing row (missing "hash") must return a reason
    string, not raise — the write path's must-never-block contract
    (Copilot review finding on PR #302)."""
    ledger = tmp_path / hook.DEFAULT_TRACE_DIR / hook.ledger_filename("s1")
    ledger.parent.mkdir(parents=True)
    with open(ledger, "w", encoding="utf-8") as handle:
        handle.write(json.dumps({"seq": 1, "type": "TOOL_CALL", "tool_name": "Read"}) + "\n")
    reason = hook.append_tool_call(ledger, "s1", "Bash", {}, "2026-09-13T00:00:00+00:00")
    assert reason is not None
    assert "not extending" in reason


def test_main_survives_non_string_cwd(monkeypatch, tmp_path):
    """A non-string cwd in the hook payload (e.g. an int) must not crash
    main() — it falls back to the script's own project root rather than
    raising a TypeError out of Path() (Copilot review finding on PR #302)."""
    import io
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    monkeypatch.setattr(
        sys, "stdin",
        io.StringIO(json.dumps({"hook_event_name": "PostToolUse", "session_id": "s1",
                                "tool_name": "Read", "tool_input": {}, "cwd": 12345})),
    )
    assert hook.main([]) == 0


def test_session_start_creates_empty_ledger(tmp_path):
    hook.touch_session_ledger({"session_id": "quiet"}, tmp_path)
    ledger = tmp_path / hook.DEFAULT_TRACE_DIR / hook.ledger_filename("quiet")
    assert ledger.exists()
    assert ledger.stat().st_size == 0


def test_session_start_does_not_clobber_existing_trace(tmp_path):
    hook.run_hook(
        {"hook_event_name": "PostToolUse", "session_id": "quiet",
         "tool_name": "Read", "tool_input": {}},
        tmp_path,
    )
    hook.touch_session_ledger({"session_id": "quiet"}, tmp_path)
    ledger = tmp_path / hook.DEFAULT_TRACE_DIR / hook.ledger_filename("quiet")
    assert len(engine.read(str(ledger))) == 1


def test_main_dispatches_session_start(monkeypatch, tmp_path):
    import io
    monkeypatch.setattr(
        sys, "stdin",
        io.StringIO(json.dumps({"hook_event_name": "SessionStart", "session_id": "s1"})),
    )
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    assert hook.main([]) == 0
    ledger = tmp_path / hook.DEFAULT_TRACE_DIR / hook.ledger_filename("s1")
    assert ledger.exists()
    assert ledger.stat().st_size == 0


def test_non_dict_tool_input_does_not_crash(tmp_path):
    reason = hook.run_hook(
        {"hook_event_name": "PostToolUse", "session_id": "s1",
         "tool_name": "Weird", "tool_input": "not-a-dict"},
        tmp_path,
    )
    assert reason is None


def test_main_never_blocks_on_unparseable_stdin(monkeypatch, capsys):
    import io
    monkeypatch.setattr(sys, "stdin", io.StringIO("not json"))
    assert hook.main([]) == 0
    assert "could not parse stdin" in capsys.readouterr().err


def test_main_ignores_non_posttooluse_events(monkeypatch, tmp_path):
    import io
    monkeypatch.setattr(
        sys, "stdin",
        io.StringIO(json.dumps({"hook_event_name": "PreToolUse", "session_id": "s1",
                                "tool_name": "Read", "tool_input": {}})),
    )
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    assert hook.main([]) == 0
    assert not (tmp_path / hook.DEFAULT_TRACE_DIR).exists()


def test_main_processes_real_posttooluse_stdin(monkeypatch, tmp_path):
    import io
    monkeypatch.setattr(
        sys, "stdin",
        io.StringIO(json.dumps({"hook_event_name": "PostToolUse", "session_id": "s1",
                                "tool_name": "Read", "tool_input": {"file_path": "/a"}})),
    )
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    assert hook.main([]) == 0
    ledger = tmp_path / hook.DEFAULT_TRACE_DIR / hook.ledger_filename("s1")
    assert ledger.exists()
    rows = engine.read(str(ledger))
    assert rows[0]["tool_name"] == "Read"
