"""
test_molt_cycle_anti_cascade.py
Builder v1.7 compliant
HumanAIOS

check_anti_cascade_rules() used to return a static {'overall_status': 'OK',
'rules_passed': 5, ...} regardless of ledger content. These tests exercise the
real, data-driven replacement: rules 1 (one open molt per constant), 3 (K=3
system-wide), and 4 (freeze after 2 consecutive reverts) computed from
molt-schema NF_LEDGER entries (rows carrying both `molt_id` and `constant`);
rules 2 and 5 reported unverified rather than faked as passing.

NOTE: root molt_cycle.py is loaded by explicit file path, matching
test_molt_cycle_nf_read.py -- see that file's note on the stranded
tools/molt_cycle.py duplicate.
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


def _molt(molt_id, constant, outcome, seq=None):
    return {"seq": seq, "type": "MOLT", "at": "2026-09-01", "by": "Z2",
            "molt_id": molt_id, "constant": constant, "outcome": outcome}


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
