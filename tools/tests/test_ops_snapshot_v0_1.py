#!/usr/bin/env python3
"""Regression tests for tools/ops_snapshot_v0_1.py (pure layer only; no network)."""
from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import ops_snapshot_v0_1 as ops

NOW = datetime(2026, 10, 24, tzinfo=UTC)


def snap(raw=None):
    return ops.build_snapshot(raw or ops._fixture(), NOW)


def test_smoke_test_passes():
    assert ops.run_smoke_test()


def test_same_input_same_output():
    assert json.dumps(snap(), sort_keys=True) == json.dumps(snap(), sort_keys=True)


def test_main_failure_is_blocker():
    items = [b for b in snap()["blockers"]["items"] if b["rule"] == "MAIN_CHECK_FAILED"]
    assert [b["detail"] for b in items] == ["security-gates"]
    assert items[0]["ref"] == "main@m1"


def test_draft_prs_never_produce_blockers():
    assert not [b for b in snap()["blockers"]["items"] if b["ref"].startswith("#3")]


def test_stale_threshold():
    stale = [b["ref"] for b in snap()["blockers"]["items"] if b["rule"] == "PR_STALE"]
    assert stale == ["#1"]


def test_duplicate_blocker_issues_counted_once():
    raw = ops._fixture()
    raw["blocker_issues"] = raw["blocker_issues"] * 2
    assert snap(raw)["blockers"]["by_rule"]["ISSUE_LABELED_BLOCKER"] == 1


def test_api_errors_downgrade_tag():
    raw = ops._fixture()
    raw["api_errors"] = [{"path": "/x", "status": 403}]
    s = snap(raw)
    assert s["epistemic_tag"] == "OBSERVED_PARTIAL"
    assert s["coverage"]["api_errors"] == [{"path": "/x", "status": 403}]


def test_missing_main_sha_does_not_crash():
    raw = ops._fixture()
    raw["main_sha"] = None
    s = snap(raw)
    assert s["main"]["checks"]["total"] == 0
    assert not [b for b in s["blockers"]["items"] if b["rule"] == "MAIN_CHECK_FAILED"]


def test_authority_boundary_and_not_collected_are_explicit():
    s = snap()
    assert s["authority_effect"] == "NONE"
    assert "unresolved_review_threads" in s["coverage"]["not_collected"]


def test_failed_fetch_reads_unknown_not_zero():
    raw = ops._fixture()
    raw["pulls"] = []
    raw["observed"] = {"main": False, "pulls": False}
    s = snap(raw)
    assert s["epistemic_tag"] == "UNOBSERVED"
    assert s["pull_requests"]["open_count"] is None


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
