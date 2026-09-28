"""
test_molt_cycle_nf_read.py
Builder v1.7 compliant
HumanAIOS

Q-NF-SCHEMA-01: molt_cycle.py must read tools/nf_ledger_v0_1.py's real event
format via that tool's own project()/pin_outcome() — not a hand-rolled join keyed
on a `target` field RESOLVE events never carry, which always read 0 resolved
(see ledgers/NF_EVENT_SCHEMA.md). Exercises the three outcome classes
pin_outcome() can return that a consumer must not conflate: resolved (1.0/0.0),
still-unresolved (None), and VOID (a relevant token still PENDING_Z2_DATE).

NOTE: root molt_cycle.py is loaded by explicit file path, not `import molt_cycle`.
A second, unrelated tools/molt_cycle.py exists (a stranded duplicate — see
ledgers/NF_EVENT_SCHEMA.md); once tools/ is on sys.path (needed for
nf_ledger_v0_1), a bare `import molt_cycle` would silently resolve to that file
instead of the root one under test.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = TOOLS_DIR.parent
sys.path.insert(0, str(TOOLS_DIR))

import nf_ledger_v0_1 as nf  # noqa: E402

_spec = importlib.util.spec_from_file_location("molt_cycle_root", ROOT_DIR / "molt_cycle.py")
molt_cycle = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(molt_cycle)


def _token(token_id, seq, date_source="PRACTICE"):
    return {"seq": seq, "type": "TOKEN", "at": "2026-09-01", "by": "Z1",
            "token_id": token_id, "practice": "p1", "title": "t", "date": "2026-09-01",
            "date_source": date_source,
            "state": "DATED" if date_source == "PRACTICE" else "PENDING_Z2_DATE",
            "owner_add": False}


def _pin(target, predictor, p, seq, pin_id=None):
    return {"seq": seq, "type": "PIN", "at": "2026-09-01", "by": "Z1",
            "pin_id": pin_id or f"{target}:{predictor}", "target": target,
            "predictor": predictor, "claim": "c", "p": p, "scoreable": True}


def _resolve(token_id, outcome, seq, source="sha:abc"):
    return {"seq": seq, "type": "RESOLVE", "at": "2026-09-05", "by": "Z1",
            "token_id": token_id, "outcome": outcome, "source": source}


def _build_ledger(tmp_path, events):
    path = str(tmp_path / "nf.jsonl")
    seq = 0
    normed = []
    for e in events:
        seq += 1
        e = dict(e)
        e["seq"] = seq
        normed.append(e)
    nf.append(path, normed, "0" * 64)
    return path


def test_resolved_yes_pin_is_counted(tmp_path):
    path = _build_ledger(tmp_path, [
        _token("T-1", None),
        _pin("T-1", "Z1", 0.7, None),
        _resolve("T-1", "YES", None),
    ])
    mc = molt_cycle.MoltCycle(nf_ledger_path=path)
    mc.read_nf_ledger()
    assert mc.count_resolved() == 1
    pairs = mc.join_pin_resolve_pairs()
    assert len(pairs) == 1
    brier = mc.calculate_brier_scores(pairs)
    assert brier["brier_overall"] == (0.7 - 1.0) ** 2


def test_resolved_no_pin_is_counted(tmp_path):
    path = _build_ledger(tmp_path, [
        _token("T-2", None),
        _pin("T-2", "Z1", 0.4, None),
        _resolve("T-2", "NO", None),
    ])
    mc = molt_cycle.MoltCycle(nf_ledger_path=path)
    mc.read_nf_ledger()
    assert mc.count_resolved() == 1
    brier = mc.calculate_brier_scores(mc.join_pin_resolve_pairs())
    assert brier["brier_overall"] == (0.4 - 0.0) ** 2


def test_unresolved_pin_is_not_counted(tmp_path):
    path = _build_ledger(tmp_path, [
        _token("T-3", None),
        _pin("T-3", "Z1", 0.5, None),
        # no RESOLVE
    ])
    mc = molt_cycle.MoltCycle(nf_ledger_path=path)
    mc.read_nf_ledger()
    assert mc.count_resolved() == 0
    assert mc.join_pin_resolve_pairs() == []


def test_pending_z2_date_pin_is_void_not_counted(tmp_path):
    path = _build_ledger(tmp_path, [
        _token("T-4", None, date_source="Z1"),   # -> PENDING_Z2_DATE, no DATE event lands
        _pin("T-4", "Z1", 0.5, None),
    ])
    mc = molt_cycle.MoltCycle(nf_ledger_path=path)
    mc.read_nf_ledger()
    assert mc.count_resolved() == 0
    assert mc.join_pin_resolve_pairs() == []


def test_multiple_predictors_scored_independently(tmp_path):
    path = _build_ledger(tmp_path, [
        _token("T-5", None),
        _pin("T-5", "Z1", 0.9, None),
        _pin("T-5", "Z2", 0.2, None),
        _resolve("T-5", "YES", None),
    ])
    mc = molt_cycle.MoltCycle(nf_ledger_path=path)
    mc.read_nf_ledger()
    assert mc.count_resolved() == 2
    brier = mc.calculate_brier_scores(mc.join_pin_resolve_pairs())
    assert brier["brier_per_predictor"]["Z1"]["brier"] == (0.9 - 1.0) ** 2
    assert brier["brier_per_predictor"]["Z2"]["brier"] == (0.2 - 1.0) ** 2


def test_ledger_not_found_reports_status(tmp_path):
    mc = molt_cycle.MoltCycle(nf_ledger_path=str(tmp_path / "missing.jsonl"))
    result = mc.read_nf_ledger()
    assert result["status"] == "LEDGER_NOT_FOUND"
    assert mc.count_resolved() == 0


# --- check_anti_cascade_rules() -------------------------------------------
# check_anti_cascade_rules() used to return a static {'overall_status': 'OK',
# 'rules_passed': 5, ...} regardless of ledger content. These tests exercise
# the real, data-driven replacement: rules 1 (one open molt per constant), 3
# (K=3 system-wide), and 4 (freeze after 2 consecutive reverts) computed from
# molt-schema NF_LEDGER entries (rows carrying both `molt_id` and `constant`);
# rules 2 and 5 are reported unverified rather than faked as passing.

def _molt(molt_id, constant, outcome, seq=None):
    return {"seq": seq, "type": "MOLT", "at": "2026-09-01", "by": "Z2",
            "molt_id": molt_id, "constant": constant, "outcome": outcome}


def _mc(tmp_path, events):
    path = _build_ledger(tmp_path, events)
    mc = molt_cycle.MoltCycle(nf_ledger_path=path)
    mc.read_nf_ledger()
    return mc


def test_no_molt_entries_reports_no_data(tmp_path):
    mc = _mc(tmp_path, [])
    result = mc.check_anti_cascade_rules()
    assert result["overall_status"] == "NO_DATA"
    assert result["violations"] == []
    assert result["rules_unverified"] == [2, 5]


def test_single_open_molt_is_clean(tmp_path):
    mc = _mc(tmp_path, [_molt("M-1", "impact_dial", "MEASURING")])
    result = mc.check_anti_cascade_rules()
    assert result["overall_status"] == "OK"
    assert result["open_molt_count"] == 1
    assert result["violations"] == []


def test_two_concurrent_open_molts_same_constant_violates_rule_1(tmp_path):
    mc = _mc(tmp_path, [
        _molt("M-1", "impact_dial", "MEASURING"),
        _molt("M-2", "impact_dial", "MEASURING"),
    ])
    result = mc.check_anti_cascade_rules()
    assert result["overall_status"] == "BLOCKED"
    rules = [v["rule"] for v in result["violations"]]
    assert 1 in rules


def test_k_limit_exceeded_violates_rule_3(tmp_path):
    mc = _mc(tmp_path, [
        _molt("M-1", "c1", "MEASURING"),
        _molt("M-2", "c2", "MEASURING"),
        _molt("M-3", "c3", "MEASURING"),
        _molt("M-4", "c4", "MEASURING"),
    ])
    result = mc.check_anti_cascade_rules()
    assert result["overall_status"] == "BLOCKED"
    rules = [v["rule"] for v in result["violations"]]
    assert 3 in rules
    assert result["open_molt_count"] == 4


def test_two_consecutive_reverts_freeze_constant_no_open_molt(tmp_path):
    mc = _mc(tmp_path, [
        _molt("M-1", "impact_dial", "REVERT"),
        _molt("M-2", "impact_dial", "REVERT"),
    ])
    result = mc.check_anti_cascade_rules()
    assert result["frozen_constants"] == ["impact_dial"]
    # frozen but no NEW open molt on it -> not itself a rule-4 violation
    assert result["overall_status"] == "OK"


def test_open_molt_on_frozen_constant_violates_rule_4(tmp_path):
    mc = _mc(tmp_path, [
        _molt("M-1", "impact_dial", "REVERT"),
        _molt("M-2", "impact_dial", "REVERT"),
        _molt("M-3", "impact_dial", "MEASURING"),
    ])
    result = mc.check_anti_cascade_rules()
    assert result["frozen_constants"] == ["impact_dial"]
    rules = [v["rule"] for v in result["violations"]]
    assert 4 in rules


def test_keep_after_revert_does_not_freeze(tmp_path):
    mc = _mc(tmp_path, [
        _molt("M-1", "impact_dial", "REVERT"),
        _molt("M-2", "impact_dial", "KEEP"),
    ])
    result = mc.check_anti_cascade_rules()
    assert result["frozen_constants"] == []


def test_inconclusive_does_not_break_consecutive_revert_count(tmp_path):
    # REVERT, INCONCLUSIVE, REVERT: INCONCLUSIVE is excluded from the resolved
    # sequence entirely (MOLT_STATE.md: it "measured nothing"), so the two real
    # reverts still freeze the constant.
    mc = _mc(tmp_path, [
        _molt("M-1", "impact_dial", "REVERT"),
        _molt("M-2", "impact_dial", "INCONCLUSIVE"),
        _molt("M-3", "impact_dial", "REVERT"),
    ])
    result = mc.check_anti_cascade_rules()
    assert result["frozen_constants"] == ["impact_dial"]


def test_non_molt_ledger_entries_are_ignored(tmp_path):
    # A TOKEN entry whose title string happens to contain the substring
    # "molt_id" must not be mistaken for a real molt-schema entry.
    mc = _mc(tmp_path, [
        {"type": "TOKEN", "token_id": "T-1", "title": "spec w/ molt_id in the name",
         "at": "2026-09-01", "by": "Z1", "practice": "p1", "date": "2026-09-01",
         "date_source": "PRACTICE", "state": "DATED", "owner_add": False},
    ])
    result = mc.check_anti_cascade_rules()
    assert result["overall_status"] == "NO_DATA"
