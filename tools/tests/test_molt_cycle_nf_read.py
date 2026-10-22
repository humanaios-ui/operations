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

Also covers MoltCycle.check_anti_cascade_rules() (kept in this same file,
not a separate one, so it runs under the already-enumerated CI suite entry
for this file rather than needing its own new line in quality-baseline.yml —
a .github/workflows/ edit is a Tier 2 gate change per
tools/molting_protocol_diff_v1_0.py's own rule, and this fix doesn't need
one): rules 1/3/4 computed from constants.json's per-constant
molt_id/molt_history fields, rules 2/5 explicitly NOT_MECHANICALLY_CHECKED.

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


# ── check_anti_cascade_rules() ──────────────────────────────────────────────
# See module docstring: kept here rather than in a new file so it runs under
# this file's existing quality-baseline.yml suite entry, not a new one.

import json  # noqa: E402


def _constant(name, molt_id=None, history=None):
    return {"name": name, "molt_id": molt_id, "molt_history": history or []}


def _write_constants(tmp_path, constants):
    path = tmp_path / "constants.json"
    path.write_text(json.dumps({"constants": constants}))
    return str(path)


def _mc_constants(tmp_path, constants):
    return molt_cycle.MoltCycle(constants_path=_write_constants(tmp_path, constants))


def test_no_constants_is_clean(tmp_path):
    mc = _mc_constants(tmp_path, [])
    result = mc.check_anti_cascade_rules()
    assert result["overall_status"] == "OK"
    assert result["open_molt_count"] == 0
    assert result["frozen_constants"] == []
    assert result["at_risk_constants"] == []


def test_ratified_but_unmeasured_molt_counts_as_open(tmp_path):
    # Mirrors the real, current shape in constants.json: a molt_id is set and
    # the only history entry is MOLT_RATIFIED — RATIFIED is a non-terminal
    # state in MOLT_STATE.md's own diagram (RATIFIED -> APPLIED -> MEASURED
    # -> KEPT/REVERTED), so this must read as still open, not resolved.
    mc = _mc_constants(tmp_path, [_constant(
        "QUEUE_SCORING_MODE", molt_id="abc123",
        history=[{"event": "MOLT_RATIFIED", "by": "Z2 (Night)"}],
    )])
    result = mc.check_anti_cascade_rules()
    assert result["open_molt_count"] == 1
    assert result["open_constants"] == ["QUEUE_SCORING_MODE"]
    assert result["rules"][3]["status"] == "PASS"  # 1 open, K=3 default


def test_kept_molt_is_not_open(tmp_path):
    mc = _mc_constants(tmp_path, [_constant(
        "SHRINK", molt_id="abc123", history=[{"event": "KEEP"}],
    )])
    result = mc.check_anti_cascade_rules()
    assert result["open_molt_count"] == 0
    assert result["open_constants"] == []


def test_two_consecutive_reverts_freezes(tmp_path):
    mc = _mc_constants(tmp_path, [_constant(
        "PRIOR_QUALITY", molt_id="m3",
        history=[{"event": "REVERT"}, {"event": "REVERT"}],
    )])
    result = mc.check_anti_cascade_rules()
    assert result["frozen_constants"] == ["PRIOR_QUALITY"]
    assert result["rules"][4]["status"] == "PASS"  # rule 4 *checks correctly*, not "nothing is frozen"


def test_one_revert_is_at_risk_not_frozen(tmp_path):
    mc = _mc_constants(tmp_path, [_constant(
        "SHADOW_PRICE_MIN_N", molt_id="m4", history=[{"event": "REVERT"}],
    )])
    result = mc.check_anti_cascade_rules()
    assert result["frozen_constants"] == []
    assert result["at_risk_constants"] == ["SHADOW_PRICE_MIN_N"]
    assert result["rules_warnings"] == 1


def test_a_keep_after_a_revert_resets_the_streak(tmp_path):
    mc = _mc_constants(tmp_path, [_constant(
        "CONSTRAINT_UNIT", molt_id="m5",
        history=[{"event": "REVERT"}, {"event": "KEEP"}, {"event": "REVERT"}],
    )])
    result = mc.check_anti_cascade_rules()
    assert result["frozen_constants"] == []
    assert result["at_risk_constants"] == ["CONSTRAINT_UNIT"]


def test_k_limit_blocks_when_exceeded(tmp_path):
    constants = [
        _constant(f"C{i}", molt_id=f"m{i}", history=[{"event": "MOLT_RATIFIED"}])
        for i in range(4)
    ]
    mc = _mc_constants(tmp_path, constants)
    mc.k_limit = 3
    result = mc.check_anti_cascade_rules()
    assert result["overall_status"] == "BLOCKED"
    assert result["rules"][3]["status"] == "BLOCKED"
    assert result["rules_blocked"] == 1


def test_rules_2_and_5_are_never_claimed_as_passing(tmp_path):
    mc = _mc_constants(tmp_path, [])
    result = mc.check_anti_cascade_rules()
    assert result["rules"][2]["status"] == "NOT_MECHANICALLY_CHECKED"
    assert result["rules"][5]["status"] == "NOT_MECHANICALLY_CHECKED"
    assert result["rules_not_mechanically_checked"] == 2


def test_check_loads_constants_itself_if_not_already_read(tmp_path):
    # complete_cycle() calls check_anti_cascade_rules() without ever calling
    # read_constants() first — regression guard for that real call path.
    mc = _mc_constants(tmp_path, [_constant("SHRINK", molt_id="m", history=[{"event": "REVERT"}, {"event": "REVERT"}])])
    assert mc.constants == []
    result = mc.check_anti_cascade_rules()
    assert result["frozen_constants"] == ["SHRINK"]


def test_against_real_repo_constants_json_does_not_error():
    """Regression guard against schema drift in the real constants.json."""
    mc = molt_cycle.MoltCycle(constants_path=str(ROOT_DIR / "constants.json"))
    result = mc.check_anti_cascade_rules()
    assert result["overall_status"] in ("OK", "BLOCKED")
    assert isinstance(result["open_constants"], list)
    assert isinstance(result["frozen_constants"], list)
