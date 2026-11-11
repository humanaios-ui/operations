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
import ci_predict_rollup_v0_1 as rollup_tool  # noqa: E402
import nf_ledger_v0_1 as engine  # noqa: E402

TOOL_NAME = "test_ci_predict"
TOOL_VERSION = "1.1.0"


def bound_pin(pr="1", sha=None, predictor="Claude Code", checks=None, committed_at="2026-09-12T10:00:00Z"):
    sha = sha or ("a" * 40)
    return {
        "schema": "ci_predict_pin_v2",
        "pr": str(pr),
        "head_sha": sha,
        "predictor": predictor,
        "committed_at": committed_at,
        "declaration_binding": {"declared_pr": str(pr), "changed_from_base": True},
        "checks": checks or {"x": {"conclusion": "success", "p": 0.8}},
    }


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


def test_declaration_requires_explicit_current_pr_binding():
    declaration = {"pr": 42, "checks": {"x": {"conclusion": "success", "p": 0.5}}}
    assert pin_tool.declared_pr_matches(declaration, "42")
    assert not pin_tool.declared_pr_matches({**declaration, "pr": 41}, "42")
    assert not pin_tool.declared_pr_matches({"checks": declaration["checks"]}, "42")


def test_binding_detects_inherited_bytes():
    head = '{"pr":42,"checks":{"x":{"conclusion":"success","p":0.5}}}'
    inherited = pin_tool.declaration_binding("42", "b" * 40, head, head)
    changed = pin_tool.declaration_binding("42", "b" * 40, head, None)
    assert inherited["changed_from_base"] is False
    assert changed["changed_from_base"] is True
    assert inherited["head_content_sha256"] == inherited["base_content_sha256"]


def test_pin_payload_requires_v2_positive_binding():
    declaration = {"pr": 42, "checks": {"x": {"conclusion": "success", "p": 0.5}}}
    binding = pin_tool.declaration_binding("42", "b" * 40, json.dumps(declaration), None)
    payload = pin_tool.build_payload("42", "a" * 40, "KNOWN_AI:ChatGPT", declaration, binding=binding)
    assert pin_tool.pin_payload_is_pr_bound(payload, "42")
    assert not pin_tool.pin_payload_is_pr_bound({**payload, "schema": "ci_predict_pin_v1"}, "42")
    bad = {**payload, "declaration_binding": {"declared_pr": "41", "changed_from_base": True}}
    assert not pin_tool.pin_payload_is_pr_bound(bad, "42")


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


def test_fetch_declaration_via_api_returns_none_on_404(monkeypatch):
    class Fake:
        returncode = 1
        stdout = ""
        stderr = "HTTP 404: Not Found"

    monkeypatch.setattr(pin_tool.subprocess, "run", lambda *a, **k: Fake())
    assert pin_tool.fetch_declaration_via_api("o/r", "sha") is None


def test_fetch_declaration_via_api_fails_closed_on_non_404(monkeypatch):
    class Fake:
        returncode = 1
        stdout = ""
        stderr = "HTTP 500: upstream failure"

    monkeypatch.setattr(pin_tool.subprocess, "run", lambda *a, **k: Fake())
    try:
        pin_tool.fetch_declaration_via_api("o/r", "sha")
        raise AssertionError("expected DeclarationError")
    except pin_tool.DeclarationError:
        pass


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
    binding = {"declared_pr": "1", "changed_from_base": True}
    old_payload = pin_tool.build_payload(
        "1", "b" * 40, "human:x",
        {"pr": 1, "checks": {"q": {"conclusion": "success", "p": 0.5}}},
        binding=binding,
    )
    new_payload = pin_tool.build_payload(
        "1", "a" * 40, "human:x",
        {"pr": 1, "checks": {"q": {"conclusion": "success", "p": 0.9}}},
        binding=binding,
    )
    comments = [
        {"body": pin_tool.render_pin_comment(old_payload), "created_at": "2026-01-01", "user": BOT},
        {"body": pin_tool.render_pin_comment(new_payload), "created_at": "2026-01-02", "user": BOT},
    ]
    selected = resolve_tool.find_latest_pin(comments, "a" * 40, expected_pr="1")
    assert selected is not None
    assert selected["checks"]["q"]["p"] == 0.9
    assert resolve_tool.find_latest_pin(comments, "c" * 40, expected_pr="1") is None


def test_untrusted_commenter_cannot_forge_a_pin():
    payload = pin_tool.build_payload(
        "1", "a" * 40, "human:x",
        {"pr": 1, "checks": {"q": {"conclusion": "success", "p": 0.99}}},
        binding={"declared_pr": "1", "changed_from_base": True},
    )
    forged = [{"body": pin_tool.render_pin_comment(payload), "created_at": "2026-01-01",
               "user": {"login": "some-collaborator"}}]
    assert resolve_tool.find_latest_pin(forged, "a" * 40, expected_pr="1") is None


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


def test_later_skipped_job_cannot_replace_executed_success():
    """Issue #870: newer workflow-path skips are separate from completed checks."""
    sha = "e90e4cbd35ea2192d794dc38908a29b8c2cc7140"
    examples = (
        ("Measure molt tier from the diff (ADVISORY)", 116157977703, 116339835553,
         "38653587426", "38710329738"),
        ("Repository admission/backpressure gate", 116162748778, 116339835121,
         "38655061130", "38710328696"),
    )
    for name, executed_id, skipped_id, executed_run, skipped_run in examples:
        pin = bound_pin(sha=sha, checks={
            name: {"conclusion": "success", "p": 0.8},
        })
        success_url = (
            f"https://github.com/humanaios-ui/operations/actions/runs/"
            f"{executed_run}/job/{executed_id}"
        )
        skipped_url = (
            f"https://github.com/humanaios-ui/operations/actions/runs/"
            f"{skipped_run}/job/{skipped_id}"
        )
        executed = {"id": executed_id, "name": name, "status": "completed",
                    "conclusion": "success", "html_url": success_url}
        skipped = {"id": skipped_id, "name": name, "status": "completed",
                   "conclusion": "skipped", "html_url": skipped_url}
        for order in ((executed, skipped), (skipped, executed)):
            outcomes = resolve_tool.compute_resolutions(pin, list(order))
            assert outcomes[name]["outcome"] == "YES"
            assert outcomes[name]["actual_conclusion"] == "success"
            assert outcomes[name]["source"] == success_url
            events = consolidate_tool.build_events(
                pin, outcomes, existing_ids=set(), pushed_at_date="2026-10-14"
            )
            assert [event["type"] for event in events] == [
                "TOKEN", "PIN", "RESOLVE"
            ]
            assert events[-1]["outcome"] == "YES"
            assert events[-1]["source"] == success_url


def test_skipped_only_does_not_create_failed_prediction():
    """Without an executed check, a success/failure forecast is not evaluated."""
    skipped = [{"id": 100, "name": "gate", "status": "completed",
                "conclusion": "skipped", "html_url": "https://example/skip"}]
    for expected in ("success", "failure"):
        pin = bound_pin(checks={"gate": {"conclusion": expected, "p": 0.8}})
        result = resolve_tool.compute_resolutions(pin, skipped)
        assert result == {}
        assert consolidate_tool.build_events(pin, result, set(), "2026-10-15") == []


def test_skipped_is_distinct_valid_forecast_when_declared():
    """A declared skipped outcome retains its original check-conclusion meaning."""
    pin = bound_pin(checks={"gate": {"conclusion": "skipped", "p": 0.8}})
    skipped = {"name": "gate", "status": "completed", "conclusion": "skipped",
               "html_url": "https://example/skip", "id": 2}
    result = resolve_tool.compute_resolutions(pin, [skipped])
    assert result["gate"]["outcome"] == "YES"
    assert result["gate"]["actual_conclusion"] == "skipped"
    executed_later = {"name": "gate", "status": "completed",
                      "conclusion": "success", "html_url": "https://example/success", "id": 3}
    changed = resolve_tool.compute_resolutions(pin, [skipped, executed_later])
    assert changed["gate"]["outcome"] == "NO"
    assert changed["gate"]["source"] == "https://example/success"


def test_earlier_real_failure_stays_a_miss_after_later_skip():
    """An actual failure is scoreable even when a later same-name job skipped."""
    pin = bound_pin(checks={"guard": {"conclusion": "success", "p": 0.8}})
    actual_failure = {"name": "guard", "status": "completed", "conclusion": "failure",
                      "html_url": "https://example/fail", "id": 1}
    skipped = {"name": "guard", "status": "completed", "conclusion": "skipped",
               "html_url": "https://example/skip", "id": 3}
    actual_success = {"name": "guard", "status": "completed", "conclusion": "success",
                      "html_url": "https://example/pass", "id": 2}
    missed = resolve_tool.compute_resolutions(pin, [skipped, actual_failure])
    assert missed["guard"]["outcome"] == "NO"
    assert missed["guard"]["source"] == "https://example/fail"
    latest_executed = resolve_tool.compute_resolutions(
        pin, [actual_failure, skipped, actual_success]
    )
    assert latest_executed["guard"]["outcome"] == "YES"
    assert latest_executed["guard"]["source"] == "https://example/pass"
    assert resolve_tool.compute_resolutions(pin, [actual_success, skipped],
                                            already_done={"guard"}) == {}


def test_completed_check_without_conclusion_is_pending():
    pin = bound_pin(checks={"guard": {"conclusion": "success", "p": 0.8}})
    result = resolve_tool.compute_resolutions(pin, [
        {"name": "guard", "status": "completed", "conclusion": None, "id": 10}
    ])
    assert result == {}


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
    pin = bound_pin(checks={"x": {"conclusion": "success", "p": 0.8}})
    resolutions = {"x": {"outcome": "YES", "source": "u"}}
    events = consolidate_tool.build_events(pin, resolutions, existing_ids=set(),
                                           pushed_at_date="2026-09-12")
    assert [e["type"] for e in events] == ["TOKEN", "PIN", "RESOLVE"]
    assert events[0]["token_id"] == events[1]["target"] == events[2]["token_id"]


def test_build_events_skips_unresolved_checks():
    pin = bound_pin(checks={"x": {"conclusion": "success", "p": 0.8}})
    events = consolidate_tool.build_events(pin, resolutions={}, existing_ids=set(),
                                           pushed_at_date="2026-09-12")
    assert events == []


def test_build_events_skips_existing_tokens():
    pin = bound_pin(checks={"x": {"conclusion": "success", "p": 0.8}})
    resolutions = {"x": {"outcome": "YES", "source": "u"}}
    token_id = consolidate_tool.token_id_for("a" * 40, "x")
    events = consolidate_tool.build_events(pin, resolutions, existing_ids={token_id},
                                           pushed_at_date="2026-09-12")
    assert events == []


def test_build_events_refuses_empty_anchor():
    """An unanchored prediction never enters the ledger, not even as PRACTICE."""
    pin = bound_pin(checks={"x": {"conclusion": "success", "p": 0.8}})
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
    binding = {"declared_pr": "1", "changed_from_base": True}
    old = pin_tool.render_pin_comment(pin_tool.build_payload(
        "1", "a" * 40, "Claude Code",
        {"pr": 1, "checks": {"x": {"conclusion": "success", "p": 0.5}}},
        binding=binding))
    new = pin_tool.render_pin_comment(pin_tool.build_payload(
        "1", "a" * 40, "Claude Code",
        {"pr": 1, "checks": {"x": {"conclusion": "success", "p": 0.9}}},
        binding=binding))
    bot = {"login": resolve_tool.TRUSTED_LOGIN}
    comments = [{"body": old, "user": bot, "created_at": "2026-01-01"},
                {"body": new, "user": bot, "created_at": "2026-01-02"}]
    pins = consolidate_tool.collect_trusted_pins(comments, expected_pr="1")
    assert pins["a" * 40]["checks"]["x"]["p"] == 0.9


def test_resolver_rejects_legacy_and_wrong_pr_pins():
    good = bound_pin(pr="42")
    bot = {"login": resolve_tool.TRUSTED_LOGIN}

    legacy = {**good, "schema": "ci_predict_pin_v1"}
    legacy_body = f"{resolve_tool.PIN_MARKER}\n```json\n{json.dumps(legacy)}\n```"
    assert resolve_tool.find_latest_pin(
        [{"body": legacy_body, "created_at": "2026-01-01", "user": bot}],
        "a" * 40, expected_pr="42",
    ) is None

    wrong = {**good, "declaration_binding": {"declared_pr": "41", "changed_from_base": True}}
    wrong_body = f"{resolve_tool.PIN_MARKER}\n```json\n{json.dumps(wrong)}\n```"
    assert resolve_tool.find_latest_pin(
        [{"body": wrong_body, "created_at": "2026-01-01", "user": bot}],
        "a" * 40, expected_pr="42",
    ) is None


def test_consolidator_refuses_unbound_pin_even_with_resolution():
    pin = bound_pin()
    resolution = {"x": {"outcome": "YES", "source": "u"}}
    inherited = {**pin, "declaration_binding": {"declared_pr": "1", "changed_from_base": False}}
    assert consolidate_tool.build_events(
        inherited, resolution, set(), "2026-09-12"
    ) == []


def test_load_ledger_state_refuses_a_corrupt_ledger(tmp_path):
    ledger = tmp_path / "corrupt.jsonl"
    pin = bound_pin(checks={"x": {"conclusion": "success", "p": 0.8}})
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
    pin = bound_pin(checks={"x": {"conclusion": "success", "p": 3.0}})
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
    pin = bound_pin(checks={
        "x": {"conclusion": "success", "p": 0.9},
        "y": {"conclusion": "success", "p": 0.9},
    })
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
    pin = bound_pin(checks={"x": {"conclusion": "success", "p": 0.8}})
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

# --- Single rolling writer and historical ledger boundaries ---------------
def _sample_rollup_ledger(path, count=1, prev=None):
    events = [{"seq": i + 1, "type": "OPEN", "at": "2026-10-15",
               "by": "ci-predict", "label": str(i)} for i in range(count)]
    engine.append(str(path), events, prev or ("0" * 64))
    return path


def test_rollup_accepts_valid_append_only_extension(tmp_path):
    base = _sample_rollup_ledger(tmp_path / "main.jsonl")
    proposal = tmp_path / "proposal.jsonl"
    proposal.write_bytes(base.read_bytes())
    _sample_rollup_ledger(proposal, 0)
    engine.append(str(proposal), [
        {"seq": 2, "type": "OPEN", "at": "2026-10-15",
         "by": "ci-predict", "label": "new"}], engine.last_hash(str(proposal)))
    assert rollup_tool.require_append_only(base, proposal) == 1
    assert rollup_tool.require_append_only(base, base) == 0


def test_rollup_refuses_branch_divergence_even_if_chains_valid(tmp_path):
    base = _sample_rollup_ledger(tmp_path / "main.jsonl")
    other = tmp_path / "other.jsonl"
    engine.append(str(other), [{"seq": 1, "type": "OPEN",
        "at": "2026-10-15", "by": "ci-predict", "label": "different"}], "0" * 64)
    import pytest
    with pytest.raises(rollup_tool.RollupBlocked, match="DIVERGED_LEDGER"):
        rollup_tool.require_append_only(base, other)


def test_rollup_refuses_forged_hash_and_duplicate_tokens(tmp_path):
    import pytest
    base = _sample_rollup_ledger(tmp_path / "base.jsonl")
    other = tmp_path / "altered.jsonl"
    other.write_bytes(base.read_bytes().replace(b'"label": "0"', b'"label": "X"'))
    with pytest.raises(rollup_tool.RollupBlocked, match="hash"):
        rollup_tool.require_append_only(base, other)
    dup = tmp_path / "duplicate.jsonl"
    engine.append(str(dup), [
        {"seq": 1, "type": "TOKEN", "token_id": "SAME"},
        {"seq": 2, "type": "TOKEN", "token_id": "SAME"}], "0" * 64)
    with pytest.raises(rollup_tool.RollupBlocked, match="duplicate TOKEN"):
        rollup_tool.validate_rows(dup)


def test_single_writer_rejects_legacy_pr_backlog_and_duplicate_rolling():
    import pytest
    old = {"number": 842, "title": rollup_tool.CONSOLIDATE_TITLE,
           "headRefName": "ci-predict-consolidate/20261015-004422"}
    stable = {"number": 899, "title": rollup_tool.CONSOLIDATE_TITLE,
              "headRefName": rollup_tool.ROLLING_BRANCH}
    with pytest.raises(rollup_tool.RollupBlocked, match="LEGACY_BACKLOG"):
        rollup_tool.select_writer([old])
    with pytest.raises(rollup_tool.RollupBlocked, match="LEGACY_BACKLOG"):
        rollup_tool.select_writer([old, stable])
    with pytest.raises(rollup_tool.RollupBlocked, match="multiple rolling"):
        rollup_tool.select_writer([stable, stable])
    assert rollup_tool.select_writer([stable]) == stable
    assert rollup_tool.select_writer([]) is None


def test_rollup_workflow_is_daily_strict_and_has_no_closed_pr_trigger():
    workflow = (TOOLS_DIR.parent / ".github/workflows/ci-predict-consolidate.yml").read_text()
    assert 'cron: "37 4 * * *"' in workflow
    assert "types: [closed]" not in workflow
    assert 'BRANCH="ci-predict-consolidate/rolling"' in workflow
    assert "LEGACY_BACKLOG" not in workflow  # enforced by imported guard
    assert "consolidation failed; refusing to publish partial ledger" in workflow
    assert "git push --set-upstream origin" in workflow
    assert "git push --force" not in workflow
    assert "tools/ci_predict_rollup_v0_1.py verify-prefix" in workflow


def test_calibration_workflows_exclude_self_generated_rollup_activity():
    root = TOOLS_DIR.parent / ".github/workflows"
    pin = (root / "ci-predict-pin.yml").read_text()
    resolve = (root / "ci-predict-resolve.yml").read_text()
    assert "startsWith(github.event.pull_request.head.ref, 'ci-predict-consolidate/')" in pin
    assert 'if not str(((pr.get("head") or {}).get("ref")) or "").startswith(' in resolve
    assert 'subprocess.run(cmd, check=True)' in resolve



def test_rolling_branch_switch_restores_proposed_ledger():
    """A dirty main ledger must be reset before checking out rolling head."""
    script = (TOOLS_DIR.parent / ".github/workflows/ci-predict-consolidate.yml").read_text()
    save = script.index('cp "$LEDGER" /tmp/ci-predict-proposed-ledger.jsonl')
    reset = script.index('git restore -- "$LEDGER"')
    switch = script.index('git switch -c "$BRANCH" FETCH_HEAD')
    restore = script.index('cp /tmp/ci-predict-proposed-ledger.jsonl "$LEDGER"')
    assert save < reset < switch < restore
    assert 'if [ "$rc" -ne 2 ]; then' in script
    assert 'Cannot establish rolling branch absence' in script


def test_strict_ci_api_rejects_failed_and_malformed_responses(monkeypatch):
    import pytest
    from types import SimpleNamespace

    for status, output in [(1, "[]"), (0, "{broken"), (0, '[{"check_runs":{}}]')]:
        monkeypatch.setattr(resolve_tool.subprocess, "run",
                            lambda *args, **kwargs: SimpleNamespace(returncode=status, stdout=output))
        with pytest.raises(resolve_tool.GitHubApiFailure):
            resolve_tool.gh_json_paginated("repos/o/r/commits/a/check-runs",
                                           key="check_runs", strict=True)


def test_partial_success_then_ci_api_failure_never_publishes(monkeypatch, tmp_path):
    """The second source fails after the first was usable; leave ledger unchanged."""
    first_sha, second_sha = "a" * 40, "b" * 40
    pins = {
        first_sha: bound_pin(pr="123", sha=first_sha),
        second_sha: bound_pin(pr="123", sha=second_sha)
    }
    monkeypatch.setattr(consolidate_tool, "collect_trusted_pins",
                        lambda comments, expected_pr: pins)

    def fetch(path, key=None, strict=False):
        assert strict, "expected fail-closed API mode for the collector"
        if "/issues/" in path:
            return [{"body": "trusted source fixture"}]
        if first_sha in path:
            return [{"name": "x", "status": "completed",
                     "conclusion": "success", "id": 42,
                     "html_url": "https://github.com/example/actions/runs/42"}]
        raise resolve_tool.GitHubApiFailure("synthetic GitHub API failure")

    monkeypatch.setattr(resolve_tool, "gh_json_paginated", fetch)
    target = tmp_path / "calibration.jsonl"
    assert consolidate_tool.run("o/r", "123", target) == 1
    assert not target.exists(), "partially verified events must not be published"


def test_rollup_cli_exposes_documented_input_alias():
    import subprocess
    assert rollup_tool.TOOL_SESSION == "issue-870"
    for command in ("select", "verify-prefix"):
        result = subprocess.run(
            [sys.executable, str(TOOLS_DIR / "ci_predict_rollup_v0_1.py"),
             command, "--help"],
            text=True, capture_output=True, check=False)
        assert result.returncode == 0
        assert "--input" in result.stdout



def test_writer_inventory_limit_matches_cli_bound():
    import pytest
    ordinary = {"number": 1, "title": "unrelated", "headRefName": "fix/example"}
    with pytest.raises(rollup_tool.RollupBlocked, match="inventory incomplete"):
        rollup_tool.select_writer([ordinary, ordinary], inventory_limit=2)
    assert rollup_tool.select_writer([ordinary, ordinary], inventory_limit=3) is None
    with pytest.raises(rollup_tool.RollupBlocked, match="invalid PR inventory limit"):
        rollup_tool.select_writer([], inventory_limit=0)
    workflow = (TOOLS_DIR.parent / ".github/workflows/ci-predict-consolidate.yml").read_text()
    assert 'gh pr list --repo "$REPO" --state open --limit 200' in workflow
    assert "--limit 200 \\" in workflow
