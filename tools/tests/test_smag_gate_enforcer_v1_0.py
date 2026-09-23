#!/usr/bin/env python3
"""
Regression tests for SMAG Calibration Gate Enforcer v1.0

Test coverage:
- Profile loading and validation
- Ratification status detection
- Gap rate computation from ledger
- Threshold enforcement logic
- Rolling window boundary conditions
- Malformed timestamp handling
- Missing ledger handling
"""

import json
import sys
import tempfile
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Import the module under test
sys.path.insert(0, str(Path(__file__).parent.parent))
from smag_gate_enforcer_v1_0 import (
    load_profile,
    is_profile_ratified,
    compute_gap_rate,
)


def test_load_profile_valid():
    """Test loading a valid profile."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        profile = {
            "profile_id": "TEST-PROFILE",
            "ratified_by_z2": "Night",
            "ratification_hash": "sha256_abc123...",
            "substrates": {
                "test:substrate": {
                    "confidence_weight": 1.0,
                    "review_bar": "standard",
                    "merge_pause_threshold": 0.25
                }
            }
        }
        json.dump(profile, f)
        f.flush()

        loaded = load_profile(f.name)
        assert loaded["profile_id"] == "TEST-PROFILE"
        assert "test:substrate" in loaded["substrates"]

        Path(f.name).unlink()


def test_load_profile_missing():
    """Test error handling for missing profile."""
    try:
        load_profile("/nonexistent/path/profile.json")
        assert False, "Should have exited on missing profile"
    except SystemExit as e:
        assert e.code == 2


def test_is_profile_ratified_yes():
    """Test detection of ratified profile."""
    profile = {
        "ratified_by_z2": "Night",
        "ratification_hash": "sha256_hash_value"
    }
    assert is_profile_ratified(profile) == True


def test_is_profile_ratified_no():
    """Test detection of unratified profile."""
    profile = {
        "ratified_by_z2": "TBD_AWAITING_Z2_DECISION",
        "ratification_hash": "TBD_AWAITING_Z2_SIGNATURE"
    }
    assert is_profile_ratified(profile) == False


def test_compute_gap_rate_missing_ledger():
    """Test gap_rate with missing ledger (clean slate)."""
    gap_rate = compute_gap_rate("/nonexistent/ledger.jsonl", 30)
    assert gap_rate == 0.0


def test_compute_gap_rate_empty_ledger():
    """Test gap_rate with empty ledger file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write("")  # Empty file
        f.flush()

        gap_rate = compute_gap_rate(f.name, 30)
        assert gap_rate == 0.0

        Path(f.name).unlink()


def test_compute_gap_rate_no_failing_checks():
    """Test gap_rate with ledger containing no failing checks."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        # Write rows with empty failing_checks
        now = datetime.now(timezone.utc).isoformat()
        for i in range(10):
            f.write(json.dumps({"timestamp": now, "failing_checks": []}) + "\n")
        f.flush()

        gap_rate = compute_gap_rate(f.name, 30)
        assert gap_rate == 0.0

        Path(f.name).unlink()


def test_compute_gap_rate_all_passing():
    """Test gap_rate when all checks pass (no failing_checks)."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        now = datetime.now(timezone.utc).isoformat()
        # Write passing rows (empty failing_checks)
        for i in range(10):
            f.write(json.dumps({"timestamp": now, "failing_checks": []}) + "\n")
        f.flush()

        gap_rate = compute_gap_rate(f.name, 30)
        assert gap_rate == 0.0, f"Expected 0.0, got {gap_rate}"

        Path(f.name).unlink()


def test_compute_gap_rate_all_failing():
    """Test gap_rate when all checks fail."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        now = datetime.now(timezone.utc).isoformat()
        # Write failing rows (non-empty failing_checks)
        for i in range(10):
            f.write(json.dumps({"timestamp": now, "failing_checks": ["check1"]}) + "\n")
        f.flush()

        gap_rate = compute_gap_rate(f.name, 30)
        assert gap_rate == 1.0, f"Expected 1.0, got {gap_rate}"

        Path(f.name).unlink()


def test_compute_gap_rate_mixed():
    """Test gap_rate with mix of passing and failing rows."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        now = datetime.now(timezone.utc).isoformat()
        # 7 passing, 3 failing
        for i in range(7):
            f.write(json.dumps({"timestamp": now, "failing_checks": []}) + "\n")
        for i in range(3):
            f.write(json.dumps({"timestamp": now, "failing_checks": ["check1"]}) + "\n")
        f.flush()

        gap_rate = compute_gap_rate(f.name, 30)
        assert abs(gap_rate - 0.3) < 0.01, f"Expected 0.3, got {gap_rate}"

        Path(f.name).unlink()


def test_compute_gap_rate_window_boundary():
    """Test gap_rate respects rolling window boundary."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        now = datetime.now(timezone.utc)

        # Old row (outside window) - should be ignored
        old_date = (now - timedelta(days=35)).isoformat()
        f.write(json.dumps({"timestamp": old_date, "failing_checks": ["check1"]}) + "\n")

        # Recent rows (inside 30-day window)
        recent_date = (now - timedelta(days=5)).isoformat()
        for i in range(10):
            f.write(json.dumps({"timestamp": recent_date, "failing_checks": []}) + "\n")

        f.flush()

        gap_rate = compute_gap_rate(f.name, 30)
        # Should count only the 10 recent passing rows, not the old failing one
        assert gap_rate == 0.0, f"Expected 0.0 (old row outside window), got {gap_rate}"

        Path(f.name).unlink()


def test_compute_gap_rate_malformed_timestamp():
    """Test gap_rate handling of malformed timestamps."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        now = datetime.now(timezone.utc).isoformat()

        # Malformed timestamp
        f.write(json.dumps({"timestamp": "invalid-date", "failing_checks": ["check1"]}) + "\n")

        # Valid timestamps
        for i in range(5):
            f.write(json.dumps({"timestamp": now, "failing_checks": []}) + "\n")

        f.flush()

        gap_rate = compute_gap_rate(f.name, 30)
        # Should skip the malformed row and count only the 5 valid ones
        assert gap_rate == 0.0, f"Expected 0.0 (malformed skipped), got {gap_rate}"

        Path(f.name).unlink()


def test_compute_gap_rate_missing_timestamp():
    """Test gap_rate handling of rows with missing timestamp."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        now = datetime.now(timezone.utc).isoformat()

        # Row with no timestamp
        f.write(json.dumps({"failing_checks": ["check1"]}) + "\n")

        # Valid rows
        for i in range(5):
            f.write(json.dumps({"timestamp": now, "failing_checks": []}) + "\n")

        f.flush()

        gap_rate = compute_gap_rate(f.name, 30)
        # Should skip the no-timestamp row and count only the 5 valid ones
        assert gap_rate == 0.0, f"Expected 0.0 (no-timestamp skipped), got {gap_rate}"

        Path(f.name).unlink()


def test_compute_gap_rate_malformed_json():
    """Test gap_rate handling of malformed JSON lines."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        now = datetime.now(timezone.utc).isoformat()

        # Malformed JSON
        f.write("{ invalid json }\n")

        # Valid rows
        for i in range(5):
            f.write(json.dumps({"timestamp": now, "failing_checks": []}) + "\n")

        f.flush()

        gap_rate = compute_gap_rate(f.name, 30)
        # Should skip the malformed JSON and count only the 5 valid ones
        assert gap_rate == 0.0, f"Expected 0.0 (malformed JSON skipped), got {gap_rate}"

        Path(f.name).unlink()


def test_compute_gap_rate_threshold_equality():
    """Test that threshold comparison works correctly at equality."""
    # This verifies gap_rate computation returns exactly 0.25
    # The gate uses > (not >=) for threshold check
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        now = datetime.now(timezone.utc).isoformat()

        # Create 25% failing rate (1 failing out of 4 total)
        f.write(json.dumps({"timestamp": now, "failing_checks": ["check1"]}) + "\n")
        for i in range(3):
            f.write(json.dumps({"timestamp": now, "failing_checks": []}) + "\n")

        f.flush()

        gap_rate = compute_gap_rate(f.name, 30)
        # Should be exactly 0.25 (the threshold value)
        assert abs(gap_rate - 0.25) < 0.01, f"Expected 0.25, got {gap_rate}"

        Path(f.name).unlink()


if __name__ == "__main__":
    tests = [
        test_load_profile_valid,
        test_load_profile_missing,
        test_is_profile_ratified_yes,
        test_is_profile_ratified_no,
        test_compute_gap_rate_missing_ledger,
        test_compute_gap_rate_empty_ledger,
        test_compute_gap_rate_no_verdicts,
        test_compute_gap_rate_all_passing,
        test_compute_gap_rate_all_failing,
        test_compute_gap_rate_mixed,
        test_compute_gap_rate_window_boundary,
        test_compute_gap_rate_malformed_timestamp,
        test_compute_gap_rate_missing_timestamp,
        test_compute_gap_rate_malformed_json,
        test_compute_gap_rate_threshold_equality,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            print(f"✓ {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
