"""
test_ci_predict.py
Builder v1.7 compliant
HumanAIOS

Covers the three-part PIN -> RESOLVE -> CONSOLIDATE loop for execution-grounded
calibration: a declaration is refused if it carries a bad probability or an
unknown conclusion, a still-running check is never scored, a stale push's pin
never resolves against the current head, seq/hash chaining through the real
engine survives, and a bad probability is refused at the point the ledger is
actually built, not only at declaration time.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_DIR))

import ci_predict_pin_v1_0 as pin_tool  # noqa: E402
import ci_predict_resolve_v1_0 as resolve_tool  # noqa: E402
import ci_predict_consolidate_v1_0 as consolidate_tool  # noqa: E402
import nf_ledger_v0_1 as engine  # noqa: E402

TOOL_NAME = "test_ci_predict"
TOOL_VERSION = "1.0.0"


# --- pin ----------------------------------------------------------------
def test_smoke_tests_pass():
    assert pin_tool.run_smoke_test()
    assert resolve_tool.run_smoke_test()
    assert consolidate_tool.run_smoke_test()


def test_declaration_refuses_bad_probability(tmp_path):
    bad = tmp_path / "pr.json"
    bad.write_text(json.dumps({"checks": {"x": {"conclusion": "success", "p": 1.2}}}))
    try:
        pin_tool.load_declaration(bad)
        raise AssertionError("expected DeclarationError")
    except pin_tool.DeclarationError:
        pass


def test_declaration_refuses_unknown_conclusion(tmp_path):
    bad = tmp_path / "pr.json"
    bad.write_text(json.dumps({"checks": {"x": {"conclusion": "maybe", "p": 0.5}}}))
    try:
        pin_tool.load_declaration(bad)
        raise AssertionError("expected DeclarationError")
    except pin_tool.DeclarationError:
        pass


def test_declaration_refuses_empty_checks(tmp_path):
    bad = tmp_path / "pr.json"
    bad.write_text(json.dumps({"checks": {}}))
    try:
        pin_tool.load_declaration(bad)
        raise AssertionError("expected DeclarationError")
    except pin_tool.DeclarationError:
        pass


def test_declaration_accepts_valid_file(tmp_path):
    good = tmp_path / "pr.json"
    good.write_text(json.dumps({"checks": {"quality": {"conclusion": "success", "p": 0.8}}}))
    loaded = pin_tool.load_declaration(good)
    assert loaded["checks"]["quality"]["p"] == 0.8


def test_missing_declaration_is_an_error_not_a_default(tmp_path):
    try:
        pin_tool.load_declaration(tmp_path / "absent.json")
        raise AssertionError("expected DeclarationError")
    except pin_tool.DeclarationError:
        pass


def test_git_commit_date_empty_outside_a_repo(tmp_path):
    """No guessed anchor when git cannot answer."""
    outside = tmp_path / "not_tracked.json"
    outside.write_text("{}")
    assert pin_tool.git_commit_date(outside) == ""


# --- resolve --------------------------------------------------------------
def test_running_check_is_never_scored():
    pin = {"head_sha": "a" * 40, "checks": {"x": {"conclusion": "success", "p": 0.7}}}
    runs = [{"name": "x", "status": "in_progress"}]
    resolutions = resolve_tool.compute_resolutions(pin, runs)
    assert resolutions == {}


def test_missing_check_run_is_never_scored():
    pin = {"head_sha": "a" * 40, "checks": {"x": {"conclusion": "success", "p": 0.7}}}
    resolutions = resolve_tool.compute_resolutions(pin, check_runs=[])
    assert resolutions == {}


def test_hit_and_miss_computed_correctly():
    pin = {"head_sha": "a" * 40, "checks": {
        "x": {"conclusion": "success", "p": 0.7},
        "y": {"conclusion": "failure", "p": 0.6},
    }}
    runs = [
        {"name": "x", "status": "completed", "conclusion": "success", "html_url": "u1"},
        {"name": "y", "status": "completed", "conclusion": "success", "html_url": "u2"},
    ]
    resolutions = resolve_tool.compute_resolutions(pin, runs)
    assert resolutions["x"]["outcome"] == "YES"
    assert resolutions["y"]["outcome"] == "NO"
    assert resolutions["y"]["source"] == "u2"


def test_already_resolved_check_is_skipped():
    pin = {"head_sha": "a" * 40, "checks": {"x": {"conclusion": "success", "p": 0.7}}}
    runs = [{"name": "x", "status": "completed", "conclusion": "success", "html_url": "u"}]
    resolutions = resolve_tool.compute_resolutions(pin, runs, already_done={"x"})
    assert resolutions == {}


def test_stale_pin_never_selected_over_current_head():
    old_payload = pin_tool.build_payload("1", "b" * 40, "human:x",
                                         {"checks": {"q": {"conclusion": "success", "p": 0.5}}})
    new_payload = pin_tool.build_payload("1", "a" * 40, "human:x",
                                         {"checks": {"q": {"conclusion": "success", "p": 0.9}}})
    comments = [
        {"body": pin_tool.render_pin_comment(old_payload), "created_at": "2026-01-01"},
        {"body": pin_tool.render_pin_comment(new_payload), "created_at": "2026-01-02"},
    ]
    selected = resolve_tool.find_latest_pin(comments, "a" * 40)
    assert selected is not None
    assert selected["checks"]["q"]["p"] == 0.9
    assert resolve_tool.find_latest_pin(comments, "c" * 40) is None


def test_extract_payload_ignores_wrong_marker():
    payload = {"head_sha": "x"}
    body = f"{resolve_tool.PIN_MARKER}\n```json\n{json.dumps(payload)}\n```"
    assert resolve_tool.extract_payload(body, resolve_tool.RESOLVE_MARKER) is None
    assert resolve_tool.extract_payload(body, resolve_tool.PIN_MARKER) == payload


# --- consolidate ------------------------------------------------------------
def test_build_events_orders_token_pin_resolve():
    pin = {"head_sha": "a" * 40, "predictor": "Claude Code",
           "checks": {"x": {"conclusion": "success", "p": 0.8}}}
    resolutions = {"x": {"outcome": "YES", "source": "u"}}
    events = consolidate_tool.build_events(pin, resolutions, existing_ids=set(),
                                           pushed_at_date="2026-09-12")
    assert [e["type"] for e in events] == ["TOKEN", "PIN", "RESOLVE"]
    assert events[0]["token_id"] == events[1]["target"] == events[2]["token_id"]


def test_build_events_skips_unresolved_checks():
    pin = {"head_sha": "a" * 40, "predictor": "Claude Code",
           "checks": {"x": {"conclusion": "success", "p": 0.8}}}
    events = consolidate_tool.build_events(pin, resolutions={}, existing_ids=set(),
                                           pushed_at_date="2026-09-12")
    assert events == []


def test_build_events_skips_existing_tokens():
    pin = {"head_sha": "a" * 40, "predictor": "Claude Code",
           "checks": {"x": {"conclusion": "success", "p": 0.8}}}
    resolutions = {"x": {"outcome": "YES", "source": "u"}}
    token_id = consolidate_tool.token_id_for("a" * 40, "x")
    events = consolidate_tool.build_events(pin, resolutions, existing_ids={token_id},
                                           pushed_at_date="2026-09-12")
    assert events == []


def test_build_events_refuses_bad_probability():
    pin = {"head_sha": "a" * 40, "predictor": "Claude Code",
           "checks": {"x": {"conclusion": "success", "p": 3.0}}}
    resolutions = {"x": {"outcome": "YES", "source": "u"}}
    try:
        consolidate_tool.build_events(pin, resolutions, existing_ids=set(),
                                      pushed_at_date="2026-09-12")
        raise AssertionError("expected SystemExit from nf_ledger_v0_1.check_p")
    except SystemExit:
        pass


def test_full_pipeline_verifies_and_scores(tmp_path):
    """Pin -> resolve -> consolidate -> the real engine's own verify and score."""
    ledger = tmp_path / "ci.jsonl"
    pin = {"head_sha": "a" * 40, "predictor": "Claude Code",
           "checks": {"x": {"conclusion": "success", "p": 0.9},
                      "y": {"conclusion": "success", "p": 0.9}}}
    runs = [
        {"name": "x", "status": "completed", "conclusion": "success", "html_url": "u1"},
        {"name": "y", "status": "completed", "conclusion": "failure", "html_url": "u2"},
    ]
    resolutions = resolve_tool.compute_resolutions(pin, runs)
    events = consolidate_tool.build_events(pin, resolutions, existing_ids=set(),
                                           pushed_at_date="2026-09-12")
    engine.append(str(ledger), events, "0" * 64)
    rows = engine.read(str(ledger))
    assert engine.verify(rows) is None

    tokens, pins = engine.project(rows)
    outcomes = {p["pin_id"]: engine.pin_outcome(p, tokens) for p in pins.values()}
    hit_id = f"{consolidate_tool.token_id_for('a'*40, 'x')}:Claude Code"
    miss_id = f"{consolidate_tool.token_id_for('a'*40, 'y')}:Claude Code"
    assert outcomes[hit_id] == 1.0
    assert outcomes[miss_id] == 0.0


def test_tampering_a_consolidated_ledger_is_detected(tmp_path):
    ledger = tmp_path / "ci.jsonl"
    pin = {"head_sha": "a" * 40, "predictor": "Claude Code",
           "checks": {"x": {"conclusion": "success", "p": 0.8}}}
    events = consolidate_tool.build_events(
        pin, {"x": {"outcome": "YES", "source": "u"}}, set(), "2026-09-12"
    )
    engine.append(str(ledger), events, "0" * 64)
    rows = engine.read(str(ledger))
    rows[-1]["outcome"] = "NO"
    assert engine.verify(rows) is not None


def test_token_id_is_deterministic_and_slugged():
    a = consolidate_tool.token_id_for("abc123", "Behavioral compliance (IC-045 gate)")
    b = consolidate_tool.token_id_for("abc123", "Behavioral compliance (IC-045 gate)")
    assert a == b
    assert " " not in a and "(" not in a


def test_commit_date_only_extracts_date_portion():
    assert consolidate_tool.commit_date_only("2026-09-12T10:00:00-07:00") == "2026-09-12"
    assert consolidate_tool.commit_date_only("") == ""
    assert consolidate_tool.commit_date_only("garbage") == ""
