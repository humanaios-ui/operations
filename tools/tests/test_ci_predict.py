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


def test_parse_declaration_refuses_non_dict_top_level():
    for bad in ["[1, 2, 3]", "42", '"a string"', "null"]:
        try:
            pin_tool.parse_declaration(bad, "test")
            raise AssertionError(f"expected DeclarationError for {bad!r}")
        except pin_tool.DeclarationError:
            pass


def test_fetch_declaration_via_api_decodes_base64_content(monkeypatch):
    import base64 as b64

    class Fake:
        returncode = 0
        stdout = json.dumps({"content": b64.b64encode(
            b'{"checks": {"x": {"conclusion": "success", "p": 0.5}}}'
        ).decode()})

    monkeypatch.setattr(pin_tool.subprocess, "run", lambda *a, **k: Fake())
    content = pin_tool.fetch_declaration_via_api("o/r", "sha")
    assert content is not None
    assert pin_tool.parse_declaration(content, "x")["checks"]["x"]["p"] == 0.5


def test_fetch_declaration_via_api_returns_none_on_failure(monkeypatch):
    class Fake:
        returncode = 1
        stdout = ""

    monkeypatch.setattr(pin_tool.subprocess, "run", lambda *a, **k: Fake())
    assert pin_tool.fetch_declaration_via_api("o/r", "sha") is None


def test_commit_date_via_api_reads_committer_date(monkeypatch):
    class Fake:
        returncode = 0
        stdout = json.dumps({"commit": {"committer": {"date": "2026-01-01T00:00:00Z"}}})

    monkeypatch.setattr(pin_tool.subprocess, "run", lambda *a, **k: Fake())
    assert pin_tool.commit_date_via_api("o/r", "sha") == "2026-01-01T00:00:00Z"


def test_commit_date_via_api_empty_on_failure(monkeypatch):
    class Fake:
        returncode = 1
        stdout = ""

    monkeypatch.setattr(pin_tool.subprocess, "run", lambda *a, **k: Fake())
    assert pin_tool.commit_date_via_api("o/r", "sha") == ""


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


BOT = {"login": resolve_tool.TRUSTED_LOGIN}


def test_stale_pin_never_selected_over_current_head():
    old_payload = pin_tool.build_payload("1", "b" * 40, "human:x",
                                         {"checks": {"q": {"conclusion": "success", "p": 0.5}}})
    new_payload = pin_tool.build_payload("1", "a" * 40, "human:x",
                                         {"checks": {"q": {"conclusion": "success", "p": 0.9}}})
    comments = [
        {"body": pin_tool.render_pin_comment(old_payload), "created_at": "2026-01-01", "user": BOT},
        {"body": pin_tool.render_pin_comment(new_payload), "created_at": "2026-01-02", "user": BOT},
    ]
    selected = resolve_tool.find_latest_pin(comments, "a" * 40)
    assert selected is not None
    assert selected["checks"]["q"]["p"] == 0.9
    assert resolve_tool.find_latest_pin(comments, "c" * 40) is None


def test_untrusted_commenter_cannot_forge_a_pin():
    payload = pin_tool.build_payload("1", "a" * 40, "human:x",
                                     {"checks": {"q": {"conclusion": "success", "p": 0.99}}})
    forged = [{"body": pin_tool.render_pin_comment(payload), "created_at": "2026-01-01",
               "user": {"login": "some-collaborator"}}]
    assert resolve_tool.find_latest_pin(forged, "a" * 40) is None


def test_untrusted_commenter_cannot_suppress_a_resolution():
    """An attacker cannot pre-empt a real check with a forged 'already resolved'."""
    resolve_comment = resolve_tool.render_resolve_comment(
        "1", "a" * 40, {"q": {"predicted_conclusion": "success",
                              "actual_conclusion": "success", "outcome": "YES", "source": "u"}})
    forged = [{"body": resolve_comment, "user": {"login": "some-collaborator"}}]
    assert resolve_tool.already_resolved_checks(forged, "a" * 40) == set()
    trusted = [{"body": resolve_comment, "user": BOT}]
    assert resolve_tool.already_resolved_checks(trusted, "a" * 40) == {"q"}


def test_duplicate_check_runs_prefer_highest_id():
    """A rerun's newer completed run wins over a stale completed duplicate,
    regardless of which order the API happens to return them in."""
    pin = {"head_sha": "a" * 40, "checks": {"x": {"conclusion": "success", "p": 0.7}}}
    runs = [
        {"name": "x", "status": "completed", "conclusion": "failure", "html_url": "old", "id": 1},
        {"name": "x", "status": "completed", "conclusion": "success", "html_url": "new", "id": 2},
    ]
    resolutions = resolve_tool.compute_resolutions(pin, runs)
    assert resolutions["x"]["outcome"] == "YES"
    assert resolutions["x"]["source"] == "new"

    # Order reversed: the higher id still wins, not "last one in the list".
    resolutions_reversed = resolve_tool.compute_resolutions(pin, list(reversed(runs)))
    assert resolutions_reversed["x"]["source"] == "new"


def test_gh_json_paginated_flattens_wrapped_pages():
    """Simulates gh api --paginate --slurp output shape without a network call."""
    import ci_predict_resolve_v1_0 as rt

    class FakeCompleted:
        returncode = 0
        stdout = json.dumps([
            {"check_runs": [{"name": "a"}]},
            {"check_runs": [{"name": "b"}]},
        ])

    orig = rt.subprocess.run
    rt.subprocess.run = lambda *a, **k: FakeCompleted()
    try:
        items = rt.gh_json_paginated("fake/path", key="check_runs")
    finally:
        rt.subprocess.run = orig
    assert [i["name"] for i in items] == ["a", "b"]


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


def test_build_events_refuses_empty_anchor():
    """An unanchored prediction never enters the ledger, not even as PRACTICE."""
    pin = {"head_sha": "a" * 40, "predictor": "Claude Code",
           "checks": {"x": {"conclusion": "success", "p": 0.8}}}
    resolutions = {"x": {"outcome": "YES", "source": "u"}}
    events = consolidate_tool.build_events(pin, resolutions, existing_ids=set(),
                                           pushed_at_date="")
    assert events == []


def test_token_id_for_is_injective_across_slug_collisions():
    """Names that slug to the same string must not produce the same token id."""
    a = consolidate_tool.token_id_for("a" * 40, "a b")
    b = consolidate_tool.token_id_for("a" * 40, "a-b")
    assert a != b
    punct1 = consolidate_tool.token_id_for("a" * 40, "!!!")
    punct2 = consolidate_tool.token_id_for("a" * 40, "???")
    assert punct1 != punct2


def test_collect_trusted_pins_ignores_untrusted_commenters():
    forged_body = (
        f"{resolve_tool.PIN_MARKER}\n"
        '```json\n{"head_sha": "' + "a" * 40 + '", "checks": {}}\n```'
    )
    comments = [{"body": forged_body, "user": {"login": "some-collaborator"},
                "created_at": "2026-01-01"}]
    assert consolidate_tool.collect_trusted_pins(comments) == {}


def test_collect_trusted_pins_keeps_latest_per_head_sha():
    old = pin_tool.render_pin_comment(pin_tool.build_payload(
        "1", "a" * 40, "Claude Code", {"checks": {"x": {"conclusion": "success", "p": 0.5}}}))
    new = pin_tool.render_pin_comment(pin_tool.build_payload(
        "1", "a" * 40, "Claude Code", {"checks": {"x": {"conclusion": "success", "p": 0.9}}}))
    bot = {"login": resolve_tool.TRUSTED_LOGIN}
    comments = [{"body": old, "user": bot, "created_at": "2026-01-01"},
                {"body": new, "user": bot, "created_at": "2026-01-02"}]
    pins = consolidate_tool.collect_trusted_pins(comments)
    assert pins["a" * 40]["checks"]["x"]["p"] == 0.9


def test_load_ledger_state_refuses_a_corrupt_ledger(tmp_path):
    ledger = tmp_path / "corrupt.jsonl"
    pin = {"head_sha": "a" * 40, "predictor": "Claude Code",
           "checks": {"x": {"conclusion": "success", "p": 0.8}}}
    events = consolidate_tool.build_events(
        pin, {"x": {"outcome": "YES", "source": "u"}}, set(), "2026-09-12"
    )
    engine.append(str(ledger), events, "0" * 64)
    rows = engine.read(str(ledger))
    rows[0]["hash"] = "0" * 64  # tamper
    ledger.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    try:
        consolidate_tool.load_ledger_state(ledger)
        raise AssertionError("expected LedgerCorrupt")
    except consolidate_tool.LedgerCorrupt:
        pass


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
