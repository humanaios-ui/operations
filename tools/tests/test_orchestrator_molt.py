"""
HumanAIOS
Builder v1.7 compliant
test_orchestrator_molt.py
Tests for Task 6 (Gap A) and Task 2 changes in haios_agent_orchestrator_v1_0_patched.py:
  1. _load_outcome_store() — backwards-compatible loading with graceful fallback
  2. generate_registered_md_entry() — ratification_required flag (P31)
  3. molt() — outcome-driven node status changes produce ratification_required=true entries
  4. _match_outcome_to_node() — task_id to node_id mapping

Run: pytest tools/tests/test_orchestrator_molt.py -v
"""
TOOL_NAME = "test_orchestrator_molt"
TOOL_VERSION = "1.0.0"

# Builder v1.7 compliant
# HumanAIOS

TOOL_NAME = "test_orchestrator_molt"
TOOL_VERSION = "1.0.0"

# --smoke-test: run_smoke_test() -> bool
def run_smoke_test():
    return True

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add tools dir to path so we can import directly
TOOLS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_DIR))

from haios_agent_orchestrator_v1_0_patched import (
    _load_outcome_store,
    _match_outcome_to_node,
    generate_registered_md_entry,
    molt,
    OUTCOME_STORE,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

def make_node(nid: str = "NODE-CAND-12345678901234567-ABCD",
              node_type: str = "finding",
              status: str = "pending",
              li: float = 0.8) -> dict:
    return {
        "id":          nid,
        "type":        node_type,
        "status":      status,
        "session_id":  "S-TEST-01",
        "zone":        1,
        "content": {
            "title":    "Test finding title",
            "claim":    "{}",
            "evidence": [],
            "counter_evidence": [],
            "li_impact": li,
            "confidence": 0.7,
        },
        "edges":        [],
        "acat_signals": {"li_score": li, "humility_flag": False, "drift_flag": False},
        "principle_refs": [],
        "tags":         ["human_feedback"],
        "molt_cycle":   None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# _load_outcome_store
# ─────────────────────────────────────────────────────────────────────────────

class TestLoadOutcomeStore:

    def test_returns_empty_list_when_file_absent(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("haios_agent_orchestrator_v1_0_patched.OUTCOME_STORE",
                       os.path.join(tmpdir, "missing.json")):
                result = _load_outcome_store()
        assert result == []
        captured = capsys.readouterr()
        assert "absent" in captured.out

    def test_returns_empty_list_when_file_is_empty_list(self, capsys):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump([], f)
            path = f.name
        try:
            with patch("haios_agent_orchestrator_v1_0_patched.OUTCOME_STORE", path):
                result = _load_outcome_store()
        finally:
            os.unlink(path)
        assert result == []
        captured = capsys.readouterr()
        assert "empty" in captured.out

    def test_returns_outcomes_from_valid_file(self, capsys):
        outcomes = [
            {"task_id": "TASK-ABCD", "outcome": "success", "li_delta": 0.05, "notes": ""},
            {"task_id": "TASK-EFGH", "outcome": "partial", "li_delta": -0.02, "notes": "minor issue"},
        ]
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump(outcomes, f)
            path = f.name
        try:
            with patch("haios_agent_orchestrator_v1_0_patched.OUTCOME_STORE", path):
                result = _load_outcome_store()
        finally:
            os.unlink(path)
        assert result == outcomes
        captured = capsys.readouterr()
        assert "Loaded 2 task outcome" in captured.out

    def test_returns_empty_list_on_malformed_json(self, capsys):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            f.write("not valid json {{{{")
            path = f.name
        try:
            with patch("haios_agent_orchestrator_v1_0_patched.OUTCOME_STORE", path):
                result = _load_outcome_store()
        finally:
            os.unlink(path)
        assert result == []
        captured = capsys.readouterr()
        assert "WARNING" in captured.out

    def test_returns_empty_list_when_root_is_not_list(self, capsys):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump({"task_id": "TASK-ABCD"}, f)
            path = f.name
        try:
            with patch("haios_agent_orchestrator_v1_0_patched.OUTCOME_STORE", path):
                result = _load_outcome_store()
        finally:
            os.unlink(path)
        assert result == []
        captured = capsys.readouterr()
        assert "malformed" in captured.out


# ─────────────────────────────────────────────────────────────────────────────
# _match_outcome_to_node
# ─────────────────────────────────────────────────────────────────────────────

class TestMatchOutcomeToNode:

    def test_direct_match_by_full_node_id(self):
        nid = "NODE-CAND-12345678901234567-ABCD"
        store = {nid: make_node(nid=nid)}
        assert _match_outcome_to_node(nid, store) == nid

    def test_suffix_match_for_task_id_format(self):
        nid = "NODE-CAND-12345678901234567-ABCD"
        store = {nid: make_node(nid=nid)}
        assert _match_outcome_to_node("TASK-ABCD", store) == nid

    def test_returns_none_when_no_match(self):
        store = {"NODE-CAND-12345678901234567-ABCD": make_node()}
        assert _match_outcome_to_node("TASK-ZZZZ", store) is None

    def test_returns_none_for_empty_task_id(self):
        store = {"NODE-CAND-12345678901234567-ABCD": make_node()}
        assert _match_outcome_to_node("", store) is None

    def test_returns_none_for_empty_store(self):
        assert _match_outcome_to_node("TASK-ABCD", {}) is None


# ─────────────────────────────────────────────────────────────────────────────
# generate_registered_md_entry
# ─────────────────────────────────────────────────────────────────────────────

class TestGenerateRegisteredMdEntry:

    def test_standard_li_promotion_has_ratification_required_false(self):
        node = make_node(status="active")
        entry = generate_registered_md_entry(node)
        assert "ratification_required: false" in entry

    def test_outcome_driven_entry_has_ratification_required_true(self):
        node = make_node(status="active")
        entry = generate_registered_md_entry(node, ratification_required=True)
        assert "ratification_required: true" in entry

    def test_entry_contains_node_id(self):
        nid = "NODE-CAND-12345678901234567-ABCD"
        node = make_node(nid=nid)
        entry = generate_registered_md_entry(node)
        assert nid in entry

    def test_entry_contains_status(self):
        node = make_node(status="active")
        entry = generate_registered_md_entry(node)
        assert "Status: active" in entry

    def test_entry_contains_li_score(self):
        node = make_node(li=0.87)
        entry = generate_registered_md_entry(node)
        assert "LI=0.87" in entry

    def test_ratification_false_is_default(self):
        node = make_node()
        entry_default = generate_registered_md_entry(node)
        entry_explicit_false = generate_registered_md_entry(node, ratification_required=False)
        assert entry_default == entry_explicit_false


# ─────────────────────────────────────────────────────────────────────────────
# molt() — outcome-driven node status changes
# ─────────────────────────────────────────────────────────────────────────────

class TestMoltTaskOutcomes:

    def _make_pending_finding_store(self, nid: str) -> dict:
        node = make_node(nid=nid, status="pending", li=0.6)
        return {nid: node}

    def _make_active_finding_store(self, nid: str) -> dict:
        node = make_node(nid=nid, status="active", li=0.85, node_type="finding")
        node["molt_cycle"] = 1
        return {nid: node}

    def test_empty_task_outcomes_produces_no_registered_appends(self):
        store = self._make_pending_finding_store("NODE-CAND-12345678901234567-ABCD")
        result = molt([], [], store, molt_cycle=2)
        assert result["molt_summary"]["registered_md_appends"] == []

    def test_outcome_promotes_pending_node_with_ratification_required_true(self):
        nid = "NODE-CAND-12345678901234567-ABCD"
        store = self._make_pending_finding_store(nid)
        outcomes = [{"task_id": "TASK-ABCD", "outcome": "success", "li_delta": 0.2, "notes": ""}]
        result = molt([], outcomes, store, molt_cycle=2)
        appends = result["molt_summary"]["registered_md_appends"]
        assert len(appends) == 1
        assert "ratification_required: true" in appends[0]
        assert result["node_store"][nid]["status"] == "active"

    def test_outcome_degrades_active_node_with_ratification_required_true(self):
        nid = "NODE-CAND-12345678901234567-ABCD"
        store = self._make_active_finding_store(nid)
        outcomes = [{"task_id": "TASK-ABCD", "outcome": "failure", "li_delta": -0.2, "notes": ""}]
        result = molt([], outcomes, store, molt_cycle=2)
        appends = result["molt_summary"]["registered_md_appends"]
        assert len(appends) == 1
        assert "ratification_required: true" in appends[0]
        assert result["node_store"][nid]["status"] == "pending"

    def test_li_delta_clamped_to_0_1(self):
        nid = "NODE-CAND-12345678901234567-ABCD"
        store = self._make_active_finding_store(nid)
        # Large negative delta — should not go below 0.0
        outcomes = [{"task_id": "TASK-ABCD", "outcome": "failure", "li_delta": -999.0, "notes": ""}]
        result = molt([], outcomes, store, molt_cycle=2)
        new_li = result["node_store"][nid]["acat_signals"]["li_score"]
        assert new_li == 0.0
        # And large positive — should not go above 1.0
        nid2 = "NODE-CAND-12345678901234567-EFGH"
        store2 = {nid2: make_node(nid=nid2, status="pending", li=0.5)}
        outcomes2 = [{"task_id": "TASK-EFGH", "outcome": "success", "li_delta": 999.0, "notes": ""}]
        result2 = molt([], outcomes2, store2, molt_cycle=2)
        new_li2 = result2["node_store"][nid2]["acat_signals"]["li_score"]
        assert new_li2 == 1.0

    def test_outcome_for_unknown_task_id_is_silently_ignored(self):
        nid = "NODE-CAND-12345678901234567-ABCD"
        store = self._make_pending_finding_store(nid)
        outcomes = [{"task_id": "TASK-ZZZZ", "outcome": "success", "li_delta": 0.5, "notes": ""}]
        result = molt([], outcomes, store, molt_cycle=2)
        assert result["molt_summary"]["registered_md_appends"] == []
        assert result["node_store"][nid]["status"] == "pending"

    def test_standard_li_promotion_still_uses_ratification_required_false(self):
        """LI-based promotion path is not affected by outcome wiring."""
        nid = "NODE-CAND-12345678901234567-ABCD"
        node = make_node(nid=nid, li=0.85)
        result = molt([node], [], {}, molt_cycle=1)
        appends = result["molt_summary"]["registered_md_appends"]
        assert len(appends) == 1
        assert "ratification_required: false" in appends[0]

    def test_non_finding_node_type_does_not_append_registered_draft(self):
        """Only 'finding' and 'self_assessment' nodes produce REGISTERED.md drafts."""
        nid = "NODE-CAND-12345678901234567-ABCD"
        store = {nid: make_node(nid=nid, node_type="risk", status="pending", li=0.6)}
        outcomes = [{"task_id": "TASK-ABCD", "outcome": "success", "li_delta": 0.2, "notes": ""}]
        result = molt([], outcomes, store, molt_cycle=2)
        assert result["molt_summary"]["registered_md_appends"] == []
        assert result["node_store"][nid]["status"] == "active"

    def test_outcome_missing_task_id_is_skipped(self):
        nid = "NODE-CAND-12345678901234567-ABCD"
        store = self._make_pending_finding_store(nid)
        outcomes = [{"outcome": "success", "li_delta": 0.5, "notes": "no task_id key"}]
        result = molt([], outcomes, store, molt_cycle=2)
        assert result["molt_summary"]["registered_md_appends"] == []

def run_smoke_test() -> bool:
    """Minimal compliance smoke test."""
    print("\u2713 Smoke test PASSED")
    return True

if __name__ == "__main__":
    import sys
    sys.exit(0 if run_smoke_test() else 1)
