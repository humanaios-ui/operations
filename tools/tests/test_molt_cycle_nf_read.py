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
