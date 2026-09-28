#!/usr/bin/env python3
"""
Regression tests for SMAG calibration state evaluator v1.0.
"""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from smag_gate_enforcer_v1_0 import (
    calibration_review_required,
    compute_gap_rate,
    is_profile_ratified,
    load_measurement_state,
    minimum_evidence_state_satisfied,
)


def make_ledger(rows):
    handle = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
    with handle as file_handle:
        for row in rows:
            if isinstance(row, str):
                file_handle.write(row + "\n")
            else:
                file_handle.write(json.dumps(row) + "\n")
    return handle.name


def test_is_profile_ratified_accepts_authorized_identity_and_sha256_form():
    profile = {
        "ratified_by_z2": "carly.r.anderson@gmail.com",
        "ratification_hash": "a" * 64,
    }
    assert is_profile_ratified(profile) is True


def test_is_profile_ratified_rejects_placeholders_and_unknown_identities():
    assert is_profile_ratified(
        {
            "ratified_by_z2": "TBD_AWAITING_Z2_DECISION",
            "ratification_hash": "TBD_AWAITING_Z2_SIGNATURE",
        }
    ) is False
    assert is_profile_ratified(
        {
            "ratified_by_z2": "Night",
            "ratification_hash": "a" * 64,
        }
    ) is False


def test_load_measurement_state_marks_missing_ledger_invalid():
    state = load_measurement_state("/nonexistent/ledger.jsonl", "human:humanaios-ui")
    assert state["contract_valid"] is False
    assert state["row_count"] == 0
    assert "ledger missing" in state["issues"][0]


def test_compute_gap_rate_filters_to_target_substrate():
    ledger_path = make_ledger(
        [
            {
                "substrate": "human:humanaios-ui",
                "timestamp": "2026-09-20T00:00:00Z",
                "failing_checks": [],
            },
            {
                "substrate": "human:humanaios-ui",
                "timestamp": "2026-09-21T00:00:00Z",
                "failing_checks": ["validate"],
            },
            {
                "substrate": "Copilot",
                "timestamp": "2026-09-21T00:00:00Z",
                "failing_checks": ["other-check"],
            },
        ]
    )
    try:
        assert compute_gap_rate(ledger_path, "human:humanaios-ui") == 0.5
        assert compute_gap_rate(ledger_path, "Copilot") == 1.0
    finally:
        Path(ledger_path).unlink()


def test_load_measurement_state_rejects_missing_failing_checks_for_target_substrate():
    ledger_path = make_ledger(
        [
            {
                "substrate": "human:humanaios-ui",
                "timestamp": "2026-09-21T00:00:00Z",
            }
        ]
    )
    try:
        state = load_measurement_state(ledger_path, "human:humanaios-ui")
        assert state["contract_valid"] is False
        assert state["row_count"] == 0
        assert "missing failing_checks" in state["issues"][0]
    finally:
        Path(ledger_path).unlink()


def test_load_measurement_state_rejects_malformed_json():
    ledger_path = make_ledger(
        [
            '{ bad json',
            {
                "substrate": "human:humanaios-ui",
                "timestamp": "2026-09-21T00:00:00Z",
                "failing_checks": [],
            },
        ]
    )
    try:
        state = load_measurement_state(ledger_path, "human:humanaios-ui")
        assert state["contract_valid"] is False
        assert state["row_count"] == 1
        assert "malformed json" in state["issues"][0]
    finally:
        Path(ledger_path).unlink()


def test_minimum_evidence_state_satisfied_uses_calibration_floor():
    state = {"row_count": 4}
    assert minimum_evidence_state_satisfied(state, {"calibration_floor": 5}) is False
    assert minimum_evidence_state_satisfied(state, {"calibration_floor": 4}) is True


def test_calibration_review_required_false_when_profile_is_unratified():
    profile = {
        "ratified_by_z2": "TBD_AWAITING_Z2_DECISION",
        "ratification_hash": "TBD_AWAITING_Z2_SIGNATURE",
    }
    substrate_profile = {
        "calibration_floor": 2,
        "merge_pause_threshold": 0.25,
    }
    measurement_state = {
        "contract_valid": True,
        "row_count": 2,
        "failed_rows": 1,
        "gap_rate": 0.5,
    }
    assert calibration_review_required(profile, substrate_profile, measurement_state) is False


def test_calibration_review_required_true_only_when_all_predicates_hold():
    profile = {
        "ratified_by_z2": "aioshuman@gmail.com",
        "ratification_hash": "sha256(decisions | by=Night | at=timestamp)",
    }
    substrate_profile = {
        "calibration_floor": 2,
        "merge_pause_threshold": 0.25,
    }
    measurement_state = {
        "contract_valid": True,
        "row_count": 2,
        "failed_rows": 1,
        "gap_rate": 0.5,
    }
    assert calibration_review_required(profile, substrate_profile, measurement_state) is True
