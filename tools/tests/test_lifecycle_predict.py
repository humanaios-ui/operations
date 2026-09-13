"""
test_lifecycle_predict.py
Builder v1.7 compliant
HumanAIOS

Covers the PIN -> RESOLVE loop for lifecycle actions (restarts, redeploys,
and anything else with an observable post-state): a bad probability is
refused at the shared engine, a partial observation scores only the fields
actually checked, an already-resolved field is never double-scored, an
unknown episode is refused rather than silently ignored, and tampering or a
corrupted existing ledger is caught before any new event is appended.
"""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_DIR))

import lifecycle_predict_v1_0 as lc  # noqa: E402
import nf_ledger_v0_1 as engine  # noqa: E402


def test_smoke_test_passes():
    assert lc.run_smoke_test()


def test_pin_writes_token_and_pin_per_field(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    episode_id = lc.new_episode_id("restart_service", "svc-x")
    events = lc.build_pin_events(
        episode_id, "restart_service", "svc-x", "Claude Code",
        {"http_health": {"value": "200", "p": 0.85}},
        window_minutes=5, pinned_at="2026-09-13T00:00:00+00:00", start_seq=1,
    )
    assert len(events) == 2
    assert events[0]["type"] == "TOKEN"
    assert events[1]["type"] == "PIN"
    engine.append(str(ledger), events, "0" * 64)
    assert engine.verify(engine.read(str(ledger))) is None


def test_bad_probability_refused():
    try:
        lc.build_pin_events(
            lc.new_episode_id("a", "b"), "a", "b", "Claude Code",
            {"x": {"value": "1", "p": 1.5}}, 5, "2026-09-13T00:00:00+00:00", 1,
        )
        raise AssertionError("expected SystemExit from engine.check_p")
    except SystemExit:
        pass


def test_partial_observation_scores_only_checked_field(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    episode_id = lc.new_episode_id("restart_service", "svc-x")
    pin_events = lc.build_pin_events(
        episode_id, "restart_service", "svc-x", "Claude Code",
        {"http_health": {"value": "200", "p": 0.9},
         "deploy_status": {"value": "SUCCESS", "p": 0.7}},
        window_minutes=5, pinned_at="2026-09-13T00:00:00+00:00", start_seq=1,
    )
    engine.append(str(ledger), pin_events, "0" * 64)

    resolve_events = lc.build_resolve_events(
        ledger, episode_id, {"http_health": "200"}, "manual check",
        "2026-09-13T00:03:00+00:00", 5,
    )
    assert len(resolve_events) == 1
    assert resolve_events[0]["outcome"] == "YES"


def test_missed_field_resolves_no(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    episode_id = lc.new_episode_id("restart_service", "svc-x")
    pin_events = lc.build_pin_events(
        episode_id, "restart_service", "svc-x", "Claude Code",
        {"deploy_status": {"value": "SUCCESS", "p": 0.7}},
        window_minutes=5, pinned_at="2026-09-13T00:00:00+00:00", start_seq=1,
    )
    engine.append(str(ledger), pin_events, "0" * 64)

    resolve_events = lc.build_resolve_events(
        ledger, episode_id, {"deploy_status": "CRASHED"}, "manual check",
        "2026-09-13T00:03:00+00:00", 3,
    )
    assert len(resolve_events) == 1
    assert resolve_events[0]["outcome"] == "NO"


def test_already_resolved_field_is_not_double_scored(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    episode_id = lc.new_episode_id("restart_service", "svc-x")
    pin_events = lc.build_pin_events(
        episode_id, "restart_service", "svc-x", "Claude Code",
        {"http_health": {"value": "200", "p": 0.9}},
        window_minutes=5, pinned_at="2026-09-13T00:00:00+00:00", start_seq=1,
    )
    engine.append(str(ledger), pin_events, "0" * 64)
    first = lc.build_resolve_events(
        ledger, episode_id, {"http_health": "200"}, "manual check",
        "2026-09-13T00:03:00+00:00", 3,
    )
    engine.append(str(ledger), first, engine.last_hash(str(ledger)))

    again = lc.build_resolve_events(
        ledger, episode_id, {"http_health": "200"}, "manual check",
        "2026-09-13T00:05:00+00:00", 4,
    )
    assert again == []


def test_unknown_episode_refused(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    episode_id = lc.new_episode_id("restart_service", "svc-x")
    pin_events = lc.build_pin_events(
        episode_id, "restart_service", "svc-x", "Claude Code",
        {"http_health": {"value": "200", "p": 0.9}},
        window_minutes=5, pinned_at="2026-09-13T00:00:00+00:00", start_seq=1,
    )
    engine.append(str(ledger), pin_events, "0" * 64)
    try:
        lc.build_resolve_events(
            ledger, "LC-does-not-exist", {"http_health": "200"}, "manual check",
            "2026-09-13T00:03:00+00:00", 3,
        )
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


def test_token_id_is_injective_over_field_names():
    episode_id = "LC-fixed-episode"
    assert lc.token_id_for(episode_id, "a b") != lc.token_id_for(episode_id, "a-b")


def test_real_brier_over_resolved_episode(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    episode_id = lc.new_episode_id("restart_service", "svc-x")
    pin_events = lc.build_pin_events(
        episode_id, "restart_service", "svc-x", "Claude Code",
        {"http_health": {"value": "200", "p": 0.9},
         "deploy_status": {"value": "SUCCESS", "p": 0.7}},
        window_minutes=5, pinned_at="2026-09-13T00:00:00+00:00", start_seq=1,
    )
    engine.append(str(ledger), pin_events, "0" * 64)
    resolve_events = lc.build_resolve_events(
        ledger, episode_id, {"http_health": "200", "deploy_status": "CRASHED"},
        "manual check", "2026-09-13T00:03:00+00:00", 5,
    )
    engine.append(str(ledger), resolve_events, engine.last_hash(str(ledger)))

    rows = engine.read(str(ledger))
    tokens, pins = engine.project(rows)
    briers = []
    for pin in pins.values():
        outcome = engine.pin_outcome(pin, tokens)
        if outcome not in (None, "VOID"):
            briers.append((pin["p"] - outcome) ** 2)
    # http_health hit at p=0.9 -> 0.01; deploy_status missed at p=0.7 -> 0.49
    assert abs(sum(briers) / len(briers) - 0.25) < 1e-9


def test_tamper_detected(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    episode_id = lc.new_episode_id("restart_service", "svc-x")
    pin_events = lc.build_pin_events(
        episode_id, "restart_service", "svc-x", "Claude Code",
        {"http_health": {"value": "200", "p": 0.9}},
        window_minutes=5, pinned_at="2026-09-13T00:00:00+00:00", start_seq=1,
    )
    engine.append(str(ledger), pin_events, "0" * 64)
    resolve_events = lc.build_resolve_events(
        ledger, episode_id, {"http_health": "200"}, "manual check",
        "2026-09-13T00:03:00+00:00", 3,
    )
    engine.append(str(ledger), resolve_events, engine.last_hash(str(ledger)))

    rows = engine.read(str(ledger))
    rows[-1]["outcome"] = "NO"
    assert engine.verify(rows) is not None


def test_corrupted_ledger_refuses_further_writes(tmp_path):
    ledger = tmp_path / "corrupt.jsonl"
    episode_id = lc.new_episode_id("restart_service", "svc-x")
    pin_events = lc.build_pin_events(
        episode_id, "restart_service", "svc-x", "Claude Code",
        {"http_health": {"value": "200", "p": 0.9}},
        window_minutes=5, pinned_at="2026-09-13T00:00:00+00:00", start_seq=1,
    )
    engine.append(str(ledger), pin_events, "0" * 64)
    rows = engine.read(str(ledger))
    rows[0]["hash"] = "0" * 64
    import json
    with open(ledger, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")

    try:
        lc.load_ledger_state(ledger)
        raise AssertionError("expected LedgerCorrupt")
    except lc.LedgerCorrupt:
        pass


def test_missing_ledger_starts_fresh(tmp_path):
    ids, next_seq = lc.load_ledger_state(tmp_path / "does-not-exist-lc-ledger.jsonl")
    assert ids == set()
    assert next_seq == 1


def test_late_observation_scores_no_even_if_value_matches(tmp_path):
    """A value that arrives correct but after the window elapsed cannot
    confirm a time-bound claim: 'within N minutes' failed on time, however
    the value later reads."""
    ledger = tmp_path / "ledger.jsonl"
    episode_id = lc.new_episode_id("restart_service", "svc-x")
    pin_events = lc.build_pin_events(
        episode_id, "restart_service", "svc-x", "Claude Code",
        {"http_health": {"value": "200", "p": 0.9}},
        window_minutes=5, pinned_at="2026-09-13T00:00:00+00:00", start_seq=1,
    )
    engine.append(str(ledger), pin_events, "0" * 64)

    late = lc.build_resolve_events(
        ledger, episode_id, {"http_health": "200"}, "manual check",
        "2026-09-13T00:11:00+00:00", 3,
    )
    assert len(late) == 1
    assert late[0]["outcome"] == "NO"
    assert late[0]["within_window"] is False


def test_blank_source_refused(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    episode_id = lc.new_episode_id("restart_service", "svc-x")
    pin_events = lc.build_pin_events(
        episode_id, "restart_service", "svc-x", "Claude Code",
        {"http_health": {"value": "200", "p": 0.9}},
        window_minutes=5, pinned_at="2026-09-13T00:00:00+00:00", start_seq=1,
    )
    engine.append(str(ledger), pin_events, "0" * 64)
    try:
        lc.build_resolve_events(ledger, episode_id, {"http_health": "200"}, "   ",
                                "2026-09-13T00:03:00+00:00", 3)
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


def test_resolve_against_missing_ledger_refused(tmp_path):
    try:
        lc.build_resolve_events(tmp_path / "never-created.jsonl", "LC-x", {"x": "y"},
                                "manual check", "2026-09-13T00:03:00+00:00", 1)
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


def test_cli_negative_window_refused(tmp_path):
    ledger = tmp_path / "cli.jsonl"
    parser = lc.build_parser()
    args = parser.parse_args([
        "pin", "--ledger", str(ledger),
        "--action", "restart_service", "--target", "svc-x",
        "--predictor", "Claude Code", "--window-minutes", "-5",
        "--expect", "http_health=200:0.85",
    ])
    assert lc.cmd_pin(args) == 2


def test_cli_malformed_expect_refused(tmp_path, capsys):
    ledger = tmp_path / "cli.jsonl"
    parser = lc.build_parser()
    args = parser.parse_args([
        "pin", "--ledger", str(ledger),
        "--action", "restart_service", "--target", "svc-x",
        "--predictor", "Claude Code", "--window-minutes", "5",
        "--expect", "not-a-valid-spec",
    ])
    assert lc.cmd_pin(args) == 2
    assert "FAIL" in capsys.readouterr().err


def test_cli_malformed_observe_refused(tmp_path, capsys):
    ledger = tmp_path / "cli.jsonl"
    parser = lc.build_parser()
    args = parser.parse_args([
        "resolve", "--ledger", str(ledger), "--episode", "LC-x",
        "--source", "manual check", "--observe", "not-a-valid-spec",
    ])
    assert lc.cmd_resolve(args) == 2
    assert "FAIL" in capsys.readouterr().err


def test_cli_resolve_against_missing_ledger_is_controlled(tmp_path, capsys):
    parser = lc.build_parser()
    args = parser.parse_args([
        "resolve", "--ledger", str(tmp_path / "never-created.jsonl"),
        "--episode", "LC-x", "--source", "manual check", "--observe", "x=y",
    ])
    assert lc.cmd_resolve(args) == 2
    assert "FAIL" in capsys.readouterr().err


def test_concurrent_pins_serialize_without_corrupting_chain(tmp_path):
    """Two pins fired at the same ledger from separate threads must not
    interleave their read-build-append critical sections: the lock in
    _locked() is what prevents seq/prev_hash collisions here."""
    import threading

    ledger = tmp_path / "concurrent.jsonl"
    parser = lc.build_parser()
    results = []

    def do_pin(target):
        args = parser.parse_args([
            "pin", "--ledger", str(ledger),
            "--action", "restart_service", "--target", target,
            "--predictor", "Claude Code", "--window-minutes", "5",
            "--expect", "http_health=200:0.9",
        ])
        results.append(lc.cmd_pin(args))

    threads = [threading.Thread(target=do_pin, args=(f"svc-{i}",)) for i in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert results == [0, 0]
    rows = engine.read(str(ledger))
    assert engine.verify(rows) is None
    assert len(rows) == 4  # 2 pins x (TOKEN, PIN)
    seqs = [r["seq"] for r in rows]
    assert seqs == [1, 2, 3, 4]


def test_cli_pin_then_resolve_round_trip(tmp_path, capsys):
    ledger = tmp_path / "cli.jsonl"
    parser = lc.build_parser()

    pin_args = parser.parse_args([
        "pin", "--ledger", str(ledger),
        "--action", "restart_service", "--target", "svc-x",
        "--predictor", "Claude Code", "--window-minutes", "5",
        "--expect", "http_health=200:0.85",
    ])
    assert lc.cmd_pin(pin_args) == 0
    printed = capsys.readouterr().out
    assert "episode LC-" in printed

    episode_id = printed.splitlines()[0].split("episode ", 1)[1]
    resolve_args = parser.parse_args([
        "resolve", "--ledger", str(ledger), "--episode", episode_id,
        "--source", "manual check", "--observe", "http_health=200",
    ])
    assert lc.cmd_resolve(resolve_args) == 0
    rows = engine.read(str(ledger))
    resolves = [r for r in rows if r.get("type") == "RESOLVE"]
    assert len(resolves) == 1
    assert resolves[0]["outcome"] == "YES"


def test_cli_pin_requires_at_least_one_expect(tmp_path):
    ledger = tmp_path / "cli.jsonl"
    parser = lc.build_parser()
    args = parser.parse_args([
        "pin", "--ledger", str(ledger),
        "--action", "restart_service", "--target", "svc-x",
        "--predictor", "Claude Code", "--window-minutes", "5",
    ])
    assert lc.cmd_pin(args) == 2


def test_missing_probability_refused():
    try:
        lc.build_pin_events(
            lc.new_episode_id("a", "b"), "a", "b", "Claude Code",
            {"x": {"value": "1", "p": None}}, 5, "2026-09-13T00:00:00+00:00", 1,
        )
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


def test_unknown_observed_field_refused_distinctly_from_already_resolved(tmp_path):
    """A typo'd field name is a real error, not the same silent no-op as
    re-observing an already-resolved field."""
    ledger = tmp_path / "ledger.jsonl"
    episode_id = lc.new_episode_id("restart_service", "svc-x")
    pin_events = lc.build_pin_events(
        episode_id, "restart_service", "svc-x", "Claude Code",
        {"http_health": {"value": "200", "p": 0.9}},
        window_minutes=5, pinned_at="2026-09-13T00:00:00+00:00", start_seq=1,
    )
    engine.append(str(ledger), pin_events, "0" * 64)

    try:
        lc.build_resolve_events(ledger, episode_id, {"no_such_field": "x"},
                                "manual check", "2026-09-13T00:03:00+00:00", 3)
        raise AssertionError("expected ValueError")
    except ValueError:
        pass

    # Meanwhile a real already-resolved field stays a legitimate no-op.
    resolved = lc.build_resolve_events(ledger, episode_id, {"http_health": "200"},
                                       "manual check", "2026-09-13T00:03:00+00:00", 3)
    engine.append(str(ledger), resolved, engine.last_hash(str(ledger)))
    again = lc.build_resolve_events(ledger, episode_id, {"http_health": "200"},
                                    "manual check", "2026-09-13T00:04:00+00:00", 4)
    assert again == []


def test_cli_unknown_observed_field_is_controlled(tmp_path, capsys):
    ledger = tmp_path / "cli.jsonl"
    parser = lc.build_parser()
    pin_args = parser.parse_args([
        "pin", "--ledger", str(ledger),
        "--action", "restart_service", "--target", "svc-x",
        "--predictor", "Claude Code", "--window-minutes", "5",
        "--expect", "http_health=200:0.9",
    ])
    lc.cmd_pin(pin_args)
    episode_id = capsys.readouterr().out.splitlines()[0].split("episode ", 1)[1]

    resolve_args = parser.parse_args([
        "resolve", "--ledger", str(ledger), "--episode", episode_id,
        "--source", "manual check", "--observe", "typo_field=x",
    ])
    assert lc.cmd_resolve(resolve_args) == 2
    assert "FAIL" in capsys.readouterr().err


def test_resolution_before_pin_is_not_within_window(tmp_path):
    """Clock skew or a backdated resolve must not be treated as fast just
    because the gap is small in magnitude."""
    ledger = tmp_path / "ledger.jsonl"
    episode_id = lc.new_episode_id("restart_service", "svc-x")
    pin_events = lc.build_pin_events(
        episode_id, "restart_service", "svc-x", "Claude Code",
        {"http_health": {"value": "200", "p": 0.9}},
        window_minutes=5, pinned_at="2026-09-13T00:10:00+00:00", start_seq=1,
    )
    engine.append(str(ledger), pin_events, "0" * 64)

    skewed = lc.build_resolve_events(
        ledger, episode_id, {"http_health": "200"}, "manual check",
        "2026-09-13T00:05:00+00:00", 3,
    )
    assert len(skewed) == 1
    assert skewed[0]["outcome"] == "NO"
    assert skewed[0]["within_window"] is False


def test_malformed_ledger_raises_ledger_corrupt_not_json_error(tmp_path):
    """A truncated/unparseable ledger must surface as the documented
    LedgerCorrupt refusal, not a raw JSONDecodeError past callers that only
    catch LedgerCorrupt."""
    ledger = tmp_path / "truncated.jsonl"
    ledger.write_text("{not valid json}\n", encoding="utf-8")
    try:
        lc.load_ledger_state(ledger)
        raise AssertionError("expected LedgerCorrupt")
    except lc.LedgerCorrupt:
        pass


def test_unresolved_pin_is_scoreable_by_shared_engine():
    """pin_outcome() indexes tk["state"] before any RESOLVE event exists, so
    a PRACTICE-dated TOKEN must carry state="DATED" from the start — the
    same as the shared engine's own builder — or every unresolved pin
    crashes with KeyError the moment anything projects the ledger."""
    episode_id = lc.new_episode_id("restart_service", "svc-x")
    pin_events = lc.build_pin_events(
        episode_id, "restart_service", "svc-x", "Claude Code",
        {"http_health": {"value": "200", "p": 0.9}},
        window_minutes=5, pinned_at="2026-09-13T00:00:00+00:00", start_seq=1,
    )
    tokens, pins = engine.project(pin_events)
    for pin in pins.values():
        assert engine.pin_outcome(pin, tokens) is None  # unresolved, not a crash


def test_malformed_row_missing_field_raises_ledger_corrupt(tmp_path):
    """A syntactically valid JSON row that is nonetheless missing a field
    verify() or this module reads (here: 'hash') must fold into
    LedgerCorrupt too, not a raw KeyError."""
    import json

    ledger = tmp_path / "missing_field.jsonl"
    ledger.write_text(
        json.dumps({"seq": 1, "type": "TOKEN", "token_id": "x", "prev_hash": "0" * 64}) + "\n",
        encoding="utf-8",
    )
    try:
        lc.load_ledger_state(ledger)
        raise AssertionError("expected LedgerCorrupt")
    except lc.LedgerCorrupt:
        pass


def test_cli_resolve_requires_at_least_one_observe(tmp_path, capsys):
    """A resolve call with no --observe must not look like a successful,
    silent no-op — the operator forgot the flag, not resolved nothing on
    purpose."""
    ledger = tmp_path / "cli.jsonl"
    parser = lc.build_parser()
    pin_args = parser.parse_args([
        "pin", "--ledger", str(ledger),
        "--action", "restart_service", "--target", "svc-x",
        "--predictor", "Claude Code", "--window-minutes", "5",
        "--expect", "http_health=200:0.9",
    ])
    lc.cmd_pin(pin_args)
    episode_id = capsys.readouterr().out.splitlines()[0].split("episode ", 1)[1]

    resolve_args = parser.parse_args([
        "resolve", "--ledger", str(ledger), "--episode", episode_id,
        "--source", "manual check",
    ])
    assert lc.cmd_resolve(resolve_args) == 2
    assert "FAIL" in capsys.readouterr().err


def test_pin_refuses_token_id_collision_with_existing_ledger(tmp_path, monkeypatch):
    """cmd_pin must check newly generated token ids against the ledger's
    existing ones rather than discarding load_ledger_state's id set — a
    forced episode-id collision must be refused, not silently overwrite an
    existing prediction."""
    ledger = tmp_path / "ledger.jsonl"
    parser = lc.build_parser()

    fixed_episode = "LC-fixed-for-collision-test"
    monkeypatch.setattr(lc, "new_episode_id", lambda action, target: fixed_episode)

    args = parser.parse_args([
        "pin", "--ledger", str(ledger),
        "--action", "restart_service", "--target", "svc-x",
        "--predictor", "Claude Code", "--window-minutes", "5",
        "--expect", "http_health=200:0.9",
    ])
    assert lc.cmd_pin(args) == 0  # first pin with this episode id succeeds

    assert lc.cmd_pin(args) == 1  # same fixed episode id again must be refused
    rows = engine.read(str(ledger))
    assert engine.verify(rows) is None
    token_ids = [r["token_id"] for r in rows if r.get("type") == "TOKEN"]
    assert len(token_ids) == len(set(token_ids))  # no duplicate token ever landed
