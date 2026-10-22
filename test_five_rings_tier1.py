"""
test_five_rings_tier1.py — Tests for five_rings.py

Coverage by book:
Earth: capability assignment, tool inventory, rhythm bounds, the nine-principle gate
Water: stance selection, the single strike, paired steps, parries, atomic write, stickiness
Fire:  the three initiatives, boundary validation, the ford gate, collapse, adversarial runs,
       strategy rotation, renewal
Wind:  every school of the audit trips and clears
Void:  the VOID sentinel, falsifiable claims, ledger append, the CLI smoke test
"""

import json
import os
import time

import pytest

from five_rings import (
    CORNERS,
    NINE_PRINCIPLES,
    VOID,
    Claim,
    Collapse,
    Parry,
    Stance,
    as_a_rock,
    assign_by_capability,
    become_the_enemy,
    body_before_sword,
    commander_knows_troops,
    continuous_cut,
    crossing_at_a_ford,
    crush,
    dull_tools,
    fire_and_stones,
    grip,
    hold_down_a_shadow,
    hold_down_the_pillow,
    injure_the_corners,
    ken_no_sen,
    know_the_void,
    let_go_the_hilt,
    main,
    mingle,
    mountain_sea_change,
    move_the_shade,
    nine_principles,
    no_stance,
    one_timing,
    parry,
    penetrate_the_depths,
    persist_or_void,
    rats_head_ox_neck,
    red_leaves,
    release_four_hands,
    renew,
    rhythm,
    stab_at_the_face,
    stick,
    strike_or_touch,
    tai_no_sen,
    tai_tai_no_sen,
    three_shouts,
    two_timing,
    twofold_gaze,
    wind_audit,
    yin_yang_foot,
)

# ── Earth ────────────────────────────────────────────────────────────────────


def test_assign_by_capability_prefers_narrowest_fit():
    assigned = assign_by_capability(
        {"deploy": {"railway"}, "audit": {"python"}},
        {"gen": {"railway", "python"}, "spec": {"railway"}},
    )
    assert assigned == {"deploy": "spec", "audit": "gen"}


def test_assign_by_capability_none_when_no_worker_fits():
    assert assign_by_capability({"x": {"rust"}}, {"gen": {"python"}}) == {"x": None}


def test_tool_inventory():
    assert commander_knows_troops(["python3"])["python3"]
    assert dull_tools(["python3", "no-such-tool-5r"]) == ["no-such-tool-5r"]


def test_rhythm_is_bounded_by_cap():
    assert all(0.0 <= rhythm(n, base=0.5, cap=2.0) <= 2.0 for n in range(10))


def test_nine_principles_names_failures():
    plan = {key: True for key, _ in NINE_PRINCIPLES}
    assert nine_principles(plan) == []
    plan["honest"] = False
    assert nine_principles(plan) == [NINE_PRINCIPLES[0][1]]
    assert len(nine_principles({})) == 9


# ── Water ────────────────────────────────────────────────────────────────────


def test_no_stance_priority():
    assert no_stance({}) is Stance.MIDDLE
    assert no_stance({"verified": True}) is Stance.UPPER
    assert no_stance({"verified": True, "needs_human": True}) is Stance.RIGHT
    assert no_stance({"needs_human": True, "blocked": True}) is Stance.LEFT
    assert no_stance({"blocked": True, "failed": True}) is Stance.LOWER


def test_twofold_gaze_reads_whole_first():
    order = []
    twofold_gaze(lambda: order.append("kan"), lambda: order.append("ken"))
    assert order == ["kan", "ken"]


def test_grip_freezes_only_the_fixed_part():
    fixed, loose = grip({"sha": "abc"}, {"retries": 1})
    with pytest.raises(TypeError):
        fixed["sha"] = "x"
    loose["retries"] = 2
    assert loose["retries"] == 2
    with pytest.raises(TypeError):
        as_a_rock({"k": 1})["k"] = 2


def test_yin_yang_foot_releases_on_error():
    trail = []
    with pytest.raises(ValueError), yin_yang_foot(lambda: "lock", trail.append):
        raise ValueError("cut")
    assert trail == ["lock"]


def test_one_timing_refuses_second_strike():
    strike = one_timing(lambda: "cut")
    assert strike() == "cut"
    with pytest.raises(RuntimeError):
        strike()


def test_two_timing_waits_for_the_opening():
    feinted, state = [], {"tense": True}

    def feint():
        feinted.append(True)
        state["tense"] = False

    assert two_timing(feint, lambda: not state["tense"], lambda: "strike") == "strike"
    assert feinted == [True]
    with pytest.raises(TimeoutError):
        two_timing(lambda: None, lambda: False, lambda: "never", pause=0, limit=3)


def test_continuous_cut_counts_landed_steps():
    assert continuous_cut([lambda: True, lambda: False, lambda: True]) == 1
    assert continuous_cut([lambda: True, lambda: True]) == 2


def test_fire_and_stones_is_atomic_and_leaves_no_temp(tmp_path):
    target = tmp_path / "state.txt"
    fire_and_stones(str(target), "one")
    fire_and_stones(str(target), "two")
    assert target.read_text(encoding="utf-8") == "two"
    assert os.listdir(tmp_path) == ["state.txt"]


def test_red_leaves_and_body_before_sword():
    assert red_leaves({"read", "write"}, "write") == {"read"}
    assert body_before_sword(lambda: 2, lambda n: n * 21) == 42


def test_strike_or_touch():
    assert strike_or_touch(lambda: "hit", dry_run=False) == "hit"
    assert strike_or_touch(lambda: "hit", dry_run=True).startswith("touch:")


def test_parry_three_modes():
    def boom():
        return 1 / 0

    assert parry(boom, ZeroDivisionError, Parry.DEFLECT, lambda: "fallback") == "fallback"
    assert parry(boom, ZeroDivisionError, Parry.ABSORB) is None
    with pytest.raises(RuntimeError) as info:
        parry(boom, ZeroDivisionError, Parry.COUNTER)
    assert isinstance(info.value.__cause__, ZeroDivisionError)
    with pytest.raises(ZeroDivisionError):
        parry(boom, KeyError, Parry.ABSORB)


def test_stab_at_the_face_fails_on_first_false():
    stab_at_the_face({"a": True})
    with pytest.raises(RuntimeError, match="ci_green"):
        stab_at_the_face({"repo_clean": True, "ci_green": False, "later": False})


def test_stick_acts_on_changes_only():
    feed = iter([1, 1, 2, 2, 3])
    seen = []
    assert stick(lambda: next(feed), seen.append, ticks=5) == 3
    assert seen == [1, 2, 3]


def test_mingle_is_lazy():
    handled = []
    gen = mingle(iter([1, 2, 3]), lambda x: handled.append(x) or x)
    assert handled == []
    assert next(gen) == 1
    assert handled == [1]


# ── Fire ─────────────────────────────────────────────────────────────────────


def test_ken_no_sen():
    assert ken_no_sen(lambda: True, lambda: "ran") == "ran"
    with pytest.raises(RuntimeError):
        ken_no_sen(lambda: False, lambda: "ran")


def test_tai_no_sen():
    ticks = iter([False, False, True])
    assert tai_no_sen(lambda: next(ticks), lambda: "countered", pause=0) == "countered"
    with pytest.raises(TimeoutError):
        tai_no_sen(lambda: False, lambda: None, pause=0, limit=2)


def test_tai_tai_no_sen_first_success_wins():
    def slow():
        time.sleep(0.2)
        return "slow"

    def boom():
        raise ValueError("miss")

    assert tai_tai_no_sen(slow, lambda: "fast") == "fast"
    assert tai_tai_no_sen(boom, slow) == "slow"
    with pytest.raises(RuntimeError):
        tai_tai_no_sen(boom, boom)


def test_hold_down_the_pillow_names_refusals():
    validators = {"nonempty": bool, "short": lambda v: len(v) < 5}
    assert hold_down_the_pillow(validators, "") == ["nonempty"]
    assert hold_down_the_pillow(validators, "toolong") == ["short"]
    assert hold_down_the_pillow(validators, "ok") == []


def test_crossing_at_a_ford():
    assert crossing_at_a_ford({"ci": True, "mergeable": True})
    assert not crossing_at_a_ford({"ci": True, "mergeable": False})
    assert not crossing_at_a_ford({})


def test_collapse_opens_after_threshold_and_resets_on_success():
    breaker = Collapse(threshold=2)
    assert not breaker.record(False)
    assert not breaker.record(True)
    assert not breaker.record(False)
    assert breaker.record(False) and breaker.is_open


def test_become_the_enemy_and_corners():
    assert become_the_enemy(lambda x: 1 / x, [1, 0]) == [(0, "ZeroDivisionError: division by zero")]
    broken = injure_the_corners(len)
    assert {item for item, _ in broken} >= {0, -1, None}
    assert injure_the_corners(lambda x: x) == []
    assert len(CORNERS) >= 10


def test_release_four_hands_abandons_stalled_strategy():
    def stalled():
        time.sleep(0.3)
        return "stalled"

    assert release_four_hands([stalled, lambda: "won"], budget=0.05) == "won"
    with pytest.raises(TimeoutError):
        release_four_hands([stalled], budget=0.05)


def test_move_the_shade_appends_dry_run():
    assert move_the_shade(["echo", "probe"]).stdout.strip() == "probe --dry-run"


def test_hold_down_a_shadow():
    assert hold_down_a_shadow([1, -1, 2], lambda e: e < 0) == ([1, 2], [-1])


def test_three_shouts_records_failure_and_reraises():
    ledger = []

    def fails(during):
        during("half")
        raise ValueError("cut")

    with pytest.raises(ValueError):
        three_shouts(fails, ledger, "op")
    assert [s["shout"] for s in ledger] == ["before", "during", "after"]
    assert ledger[-1]["ok"] is False and "ValueError" in ledger[-1]["error"]
    assert three_shouts(lambda during: "done", ledger, "op2") == "done"
    assert ledger[-1]["ok"] is True and ledger[-1]["op"] == "op2"


def test_crush_runs_every_step():
    ran = []
    failures = crush([lambda: ran.append(1), lambda: 1 / 0, lambda: ran.append(3)])
    assert failures == 1
    assert ran == [1, 3]


def test_mountain_sea_change_two_tries_then_change():
    calls = {"a": 0, "b": 0}

    def a():
        calls["a"] += 1
        raise ValueError("a")

    def b():
        calls["b"] += 1
        return "b"

    assert mountain_sea_change([a, b]) == "b"
    assert calls == {"a": 2, "b": 1}
    with pytest.raises(RuntimeError):
        mountain_sea_change([a])
    assert calls["a"] == 4


def test_penetrate_the_depths_requires_no_reproduction():
    state = {"broken": True}
    assert penetrate_the_depths(lambda: state.update(broken=False), lambda: state["broken"])
    assert not penetrate_the_depths(lambda: None, lambda: True)


def test_renew_rats_head_and_let_go():
    assert renew(True, "tangled", lambda: "fresh") == "fresh"
    assert renew(False, "kept", lambda: "fresh") == "kept"
    assert rats_head_ox_neck(lambda: None, lambda: "macro", lambda d: d is None) == "macro"
    assert rats_head_ox_neck(lambda: "detail", lambda: "macro", lambda d: d is None) == "detail"
    acted = []
    assert let_go_the_hilt(lambda: True, lambda: acted.append(1)) is None
    assert acted == []
    let_go_the_hilt(lambda: False, lambda: acted.append(1))
    assert acted == [1]


# ── Wind ─────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "school,op",
    [
        ("long_sword", {"dependencies": ["a", "b", "c", "d"]}),
        ("strong_stroke", {"flags": ["--force"]}),
        ("short_sword", {"suppresses_errors": True}),
        ("many_techniques", {"strategies": [1, 2, 3, 4]}),
        ("fixed_stance", {"hardcoded": ["/tmp/x"]}),
        ("fixed_gaze", {"metrics": ["latency"]}),
        ("fancy_footwork", {"no_effect_steps": ["step"]}),
        ("speed", {"sleeps_as_sync": True}),
        ("speed", {"verified": False}),
        ("secret_teaching", {"hidden_state": ["ENV_ONLY"]}),
    ],
)
def test_wind_audit_trips_each_school(school, op):
    findings = wind_audit(op)
    assert len(findings) == 1
    assert findings[0].startswith(school + ":")


def test_wind_audit_clears_a_clean_operation():
    assert wind_audit({}) == []
    assert wind_audit({"flags": ["--force"], "force_reason": "Z2-ratified rewrite", "metrics": ["a", "b"]}) == []


# ── Void ─────────────────────────────────────────────────────────────────────


def test_void_and_claims():
    assert know_the_void(lambda: 42) == 42
    assert know_the_void(lambda: 1 / 0) is VOID
    assert not VOID
    assert VOID is not None
    assert repr(VOID) == "VOID"
    assert Claim("ledger chained", lambda: False).stands()
    assert not Claim("ledger chained", lambda: True).stands()


def test_persist_or_void_appends_sorted_json(tmp_path):
    ledger = tmp_path / "receipts.jsonl"
    line = persist_or_void({"b": 1, "a": 2}, str(ledger))
    persist_or_void({"event": "two"}, str(ledger))
    assert line == '{"a": 2, "b": 1}'
    rows = [json.loads(row) for row in ledger.read_text(encoding="utf-8").splitlines()]
    assert rows == [{"a": 2, "b": 1}, {"event": "two"}]


def test_cli_smoke_test_passes(capsys):
    assert main(["--smoke-test"]) == 0
    assert "checks OK" in capsys.readouterr().out
    assert main(["--bogus"]) == 2
