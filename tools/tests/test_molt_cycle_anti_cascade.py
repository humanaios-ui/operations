"""
test_molt_cycle_anti_cascade.py
Builder v1.7 compliant
HumanAIOS

MoltCycle.check_anti_cascade_rules() was a stub that returned a hardcoded
{'overall_status': 'OK', 'rules_passed': 5, ...} regardless of actual state —
flagged as PARTIAL in AUTHORIZATION_EVIDENCE_MAPPING.md §3 ("the rule text is
real and lives in MOLT_STATE.md and CI, but the function named to enforce it
in code does not yet do the check itself"). This exercises the real
implementation: rules 1/3/4 computed from constants.json's per-constant
molt_id/molt_history fields (the data read_constants() already loads), and
rules 2/5 explicitly reported NOT_MECHANICALLY_CHECKED rather than assumed
to pass.

NOTE: root molt_cycle.py is loaded by explicit file path, matching
test_molt_cycle_nf_read.py's own pattern — see that file's docstring for why
a bare `import molt_cycle` is unsafe once tools/ is on sys.path.

Run: pytest tools/tests/test_molt_cycle_anti_cascade.py -v
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = TOOLS_DIR.parent

_spec = importlib.util.spec_from_file_location("molt_cycle_root", ROOT_DIR / "molt_cycle.py")
molt_cycle = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(molt_cycle)


def _constant(name, molt_id=None, history=None):
    return {"name": name, "molt_id": molt_id, "molt_history": history or []}


def _write_constants(tmp_path, constants):
    path = tmp_path / "constants.json"
    path.write_text(json.dumps({"constants": constants}))
    return str(path)


def _mc(tmp_path, constants):
    return molt_cycle.MoltCycle(constants_path=_write_constants(tmp_path, constants))


def test_no_constants_is_clean(tmp_path):
    mc = _mc(tmp_path, [])
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
    mc = _mc(tmp_path, [_constant(
        "QUEUE_SCORING_MODE", molt_id="abc123",
        history=[{"event": "MOLT_RATIFIED", "by": "Z2 (Night)"}],
    )])
    result = mc.check_anti_cascade_rules()
    assert result["open_molt_count"] == 1
    assert result["open_constants"] == ["QUEUE_SCORING_MODE"]
    assert result["rules"][3]["status"] == "PASS"  # 1 open, K=3 default


def test_kept_molt_is_not_open(tmp_path):
    mc = _mc(tmp_path, [_constant(
        "SHRINK", molt_id="abc123", history=[{"event": "KEEP"}],
    )])
    result = mc.check_anti_cascade_rules()
    assert result["open_molt_count"] == 0
    assert result["open_constants"] == []


def test_two_consecutive_reverts_freezes(tmp_path):
    mc = _mc(tmp_path, [_constant(
        "PRIOR_QUALITY", molt_id="m3",
        history=[{"event": "REVERT"}, {"event": "REVERT"}],
    )])
    result = mc.check_anti_cascade_rules()
    assert result["frozen_constants"] == ["PRIOR_QUALITY"]
    assert result["rules"][4]["status"] == "PASS"  # rule 4 *checks correctly*, not "nothing is frozen"


def test_one_revert_is_at_risk_not_frozen(tmp_path):
    mc = _mc(tmp_path, [_constant(
        "SHADOW_PRICE_MIN_N", molt_id="m4", history=[{"event": "REVERT"}],
    )])
    result = mc.check_anti_cascade_rules()
    assert result["frozen_constants"] == []
    assert result["at_risk_constants"] == ["SHADOW_PRICE_MIN_N"]
    assert result["rules_warnings"] == 1


def test_a_keep_after_a_revert_resets_the_streak(tmp_path):
    mc = _mc(tmp_path, [_constant(
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
    mc = _mc(tmp_path, constants)
    mc.k_limit = 3
    result = mc.check_anti_cascade_rules()
    assert result["overall_status"] == "BLOCKED"
    assert result["rules"][3]["status"] == "BLOCKED"
    assert result["rules_blocked"] == 1


def test_rules_2_and_5_are_never_claimed_as_passing(tmp_path):
    mc = _mc(tmp_path, [])
    result = mc.check_anti_cascade_rules()
    assert result["rules"][2]["status"] == "NOT_MECHANICALLY_CHECKED"
    assert result["rules"][5]["status"] == "NOT_MECHANICALLY_CHECKED"
    assert result["rules_not_mechanically_checked"] == 2


def test_check_loads_constants_itself_if_not_already_read(tmp_path):
    # complete_cycle() calls check_anti_cascade_rules() without ever calling
    # read_constants() first — regression guard for that real call path.
    mc = _mc(tmp_path, [_constant("SHRINK", molt_id="m", history=[{"event": "REVERT"}, {"event": "REVERT"}])])
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
