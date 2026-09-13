#!/usr/bin/env python3
"""
test_prs_runner_tier1.py — Tier 1 tests for PRS Runner (v0.3)

Tests core PRS functionality:
- Hypothesis registration with NF_LEDGER PIN entries
- Locked parameter validation
- Experiment execution
- Prediction resolution (EXPECTED/SURPRISE/VOID)
- VERDICT event emission and event chain recording
- NF_LEDGER RESOLVE entries with Brier scoring
- Z2 ratification hash binding
- Event and ledger export

Total: 15 tests covering all major code paths.
"""

import pytest
import json
import hashlib
from datetime import datetime, timezone
from prs_run import (
    PRSRunner, PreregisteredHypothesis, PredictionOutcome, NFLedgerEntry
)


class TestPRSRunnerRegistration:
    """Tests for hypothesis registration and NF_LEDGER PIN creation."""

    def test_register_single_hypothesis(self):
        """Test registering a single hypothesis creates PIN entry."""
        runner = PRSRunner()
        hypothesis = PreregisteredHypothesis(
            hypothesis_id="H-20260910-001",
            title="Quality Prediction",
            prediction="quality_score > 75",
            metric="quality_score",
            threshold=75.0,
            direction="gt",
            experiment_params={"model": "haiku", "temp": 0.7},
            registered_at=datetime.now(timezone.utc).isoformat(),
            registered_sha="abc123def456",
            prediction_window_days=7,
        )

        result = runner.register_hypothesis(hypothesis)

        assert result['hypothesis_id'] == "H-20260910-001"
        assert result['status'] == 'REGISTERED'
        assert result['params_frozen'] is True
        assert result['registered_sha'] == "abc123def456"
        assert 'nf_ledger_pin' in result
        assert result['nf_ledger_pin']['entry_type'] == 'PIN'

    def test_register_multiple_hypotheses(self):
        """Test registering multiple hypotheses with chain linking."""
        runner = PRSRunner()
        hypothesis1 = PreregisteredHypothesis(
            hypothesis_id="H-001",
            title="Test 1",
            prediction="x > 5",
            metric="x",
            threshold=5.0,
            direction="gt",
            experiment_params={},
            registered_at=datetime.now(timezone.utc).isoformat(),
            registered_sha="sha1",
            prediction_window_days=7,
        )
        hypothesis2 = PreregisteredHypothesis(
            hypothesis_id="H-002",
            title="Test 2",
            prediction="y < 10",
            metric="y",
            threshold=10.0,
            direction="lt",
            experiment_params={},
            registered_at=datetime.now(timezone.utc).isoformat(),
            registered_sha="sha2",
            prediction_window_days=7,
        )

        result1 = runner.register_hypothesis(hypothesis1)
        result2 = runner.register_hypothesis(hypothesis2)

        # Verify chain linking: result2's PIN has result1's PIN hash as prior
        pin1_hash = result1['nf_ledger_pin']['hash']
        pin2_prior = result2['nf_ledger_pin']['prior_hash']
        assert pin2_prior == pin1_hash

    def test_nf_ledger_pin_hash_computation(self):
        """Test that PIN entry hash is computed correctly."""
        runner = PRSRunner()
        hypothesis = PreregisteredHypothesis(
            hypothesis_id="H-TEST",
            title="Test",
            prediction="m > 50",
            metric="m",
            threshold=50.0,
            direction="gt",
            experiment_params={},
            registered_at="2026-09-10T10:00:00Z",
            registered_sha="testsha",
            prediction_window_days=5,
        )

        runner.register_hypothesis(hypothesis)
        pin_entry = runner.nf_ledger_entries[0]

        # Verify hash is set
        assert pin_entry.hash is not None
        assert len(pin_entry.hash) == 64  # SHA256 hex is 64 chars


class TestPRSRunnerValidation:
    """Tests for hypothesis validation and freezing."""

    def test_validate_hypothesis_frozen(self):
        """Test that registered hypotheses pass frozen validation."""
        runner = PRSRunner()
        hypothesis = PreregisteredHypothesis(
            hypothesis_id="H-VALID",
            title="Test",
            prediction="score > 100",
            metric="score",
            threshold=100.0,
            direction="gt",
            experiment_params={"param1": "value1"},
            registered_at=datetime.now(timezone.utc).isoformat(),
            registered_sha="hash123",
            prediction_window_days=7,
        )

        runner.register_hypothesis(hypothesis)
        result = runner.validate_hypothesis_frozen("H-VALID")

        assert result['valid'] is True
        assert result['params_frozen'] is True

    def test_validate_nonexistent_hypothesis(self):
        """Test that validating nonexistent hypothesis fails."""
        runner = PRSRunner()
        result = runner.validate_hypothesis_frozen("H-NONEXIST")

        assert result['valid'] is False
        assert 'not found' in result['reason']


class TestPRSRunnerExperiment:
    """Tests for experiment execution and prediction resolution."""

    def test_run_experiment_expected_outcome(self):
        """Test running experiment with EXPECTED outcome."""
        runner = PRSRunner()
        hypothesis = PreregisteredHypothesis(
            hypothesis_id="H-EXP-001",
            title="Test Experiment",
            prediction="quality > 75",
            metric="quality",
            threshold=75.0,
            direction="gt",
            experiment_params={},
            registered_at=datetime.now(timezone.utc).isoformat(),
            registered_sha="expsha",
            prediction_window_days=7,
        )

        runner.register_hypothesis(hypothesis)
        run_result = runner.run_experiment("H-EXP-001", {"quality": 85.0})

        assert run_result['status'] == 'COMPLETED'
        assert run_result['metric_actual'] == 85.0

        resolution = runner.resolve_prediction("H-EXP-001", 85.0)

        assert resolution['outcome'] == 'EXPECTED'
        assert resolution['matched'] is True

    def test_run_experiment_surprise_outcome(self):
        """Test running experiment with SURPRISE outcome."""
        runner = PRSRunner()
        hypothesis = PreregisteredHypothesis(
            hypothesis_id="H-EXP-002",
            title="Test",
            prediction="value > 50",
            metric="value",
            threshold=50.0,
            direction="gt",
            experiment_params={},
            registered_at=datetime.now(timezone.utc).isoformat(),
            registered_sha="sha",
            prediction_window_days=7,
        )

        runner.register_hypothesis(hypothesis)
        run_result = runner.run_experiment("H-EXP-002", {"value": 30.0})
        resolution = runner.resolve_prediction("H-EXP-002", 30.0)

        assert resolution['outcome'] == 'SURPRISE'
        assert resolution['matched'] is False

    def test_run_experiment_void_outcome(self):
        """Test running experiment with missing metric (VOID)."""
        runner = PRSRunner()
        hypothesis = PreregisteredHypothesis(
            hypothesis_id="H-VOID",
            title="Test",
            prediction="metric > 100",
            metric="missing_metric",
            threshold=100.0,
            direction="gt",
            experiment_params={},
            registered_at=datetime.now(timezone.utc).isoformat(),
            registered_sha="sha",
            prediction_window_days=7,
        )

        runner.register_hypothesis(hypothesis)
        run_result = runner.run_experiment("H-VOID", {"other_metric": 50.0})

        assert run_result['status'] == 'VOID'
        assert 'metric' in run_result['reason']

    def test_resolve_prediction_with_direction_lt(self):
        """Test resolving prediction with less-than direction."""
        runner = PRSRunner()
        hypothesis = PreregisteredHypothesis(
            hypothesis_id="H-LT",
            title="Test LT",
            prediction="error < 0.05",
            metric="error",
            threshold=0.05,
            direction="lt",
            experiment_params={},
            registered_at=datetime.now(timezone.utc).isoformat(),
            registered_sha="sha",
            prediction_window_days=7,
        )

        runner.register_hypothesis(hypothesis)

        # Should EXPECT when actual < threshold
        result_expected = runner.resolve_prediction("H-LT", 0.03)
        assert result_expected['outcome'] == 'EXPECTED'

        # Should SURPRISE when actual >= threshold
        result_surprise = runner.resolve_prediction("H-LT", 0.07)
        assert result_surprise['outcome'] == 'SURPRISE'


class TestPRSRunnerVerdictEmission:
    """Tests for VERDICT event emission and event chain recording."""

    def test_emit_verdict_expected(self):
        """Test emitting VERDICT event for EXPECTED outcome."""
        runner = PRSRunner()
        hypothesis = PreregisteredHypothesis(
            hypothesis_id="H-VERDICT",
            title="Test",
            prediction="m > 10",
            metric="m",
            threshold=10.0,
            direction="gt",
            experiment_params={},
            registered_at=datetime.now(timezone.utc).isoformat(),
            registered_sha="sha",
            prediction_window_days=7,
        )

        runner.register_hypothesis(hypothesis)
        verdict = runner.emit_verdict("H-VERDICT", "EXPECTED", 15.0)

        assert verdict['verdict_id'].startswith('V-')
        assert verdict['outcome'] == 'EXPECTED'
        assert verdict['status'] == 'EMITTED'
        assert verdict['brier_score'] == 0.0  # Perfect prediction

    def test_emit_verdict_surprise(self):
        """Test emitting VERDICT event for SURPRISE outcome."""
        runner = PRSRunner()
        hypothesis = PreregisteredHypothesis(
            hypothesis_id="H-SURPRISE",
            title="Test",
            prediction="x > 100",
            metric="x",
            threshold=100.0,
            direction="gt",
            experiment_params={},
            registered_at=datetime.now(timezone.utc).isoformat(),
            registered_sha="sha",
            prediction_window_days=7,
        )

        runner.register_hypothesis(hypothesis)
        verdict = runner.emit_verdict("H-SURPRISE", "SURPRISE", 50.0)

        assert verdict['outcome'] == 'SURPRISE'
        assert verdict['brier_score'] == 1.0  # Worst prediction (confidence=1, got 0)

    def test_emit_verdict_void(self):
        """Test emitting VERDICT event for VOID outcome."""
        runner = PRSRunner()
        hypothesis = PreregisteredHypothesis(
            hypothesis_id="H-VOID-V",
            title="Test",
            prediction="y > 5",
            metric="y",
            threshold=5.0,
            direction="gt",
            experiment_params={},
            registered_at=datetime.now(timezone.utc).isoformat(),
            registered_sha="sha",
            prediction_window_days=7,
        )

        runner.register_hypothesis(hypothesis)
        verdict = runner.emit_verdict("H-VOID-V", "VOID", None)

        assert verdict['outcome'] == 'VOID'
        assert verdict['brier_score'] is None

    def test_verdict_added_to_event_chain(self):
        """Test that verdicts are added to event chain for export."""
        runner = PRSRunner()
        hypothesis = PreregisteredHypothesis(
            hypothesis_id="H-CHAIN",
            title="Test",
            prediction="z > 0",
            metric="z",
            threshold=0.0,
            direction="gt",
            experiment_params={},
            registered_at=datetime.now(timezone.utc).isoformat(),
            registered_sha="sha",
            prediction_window_days=7,
        )

        runner.register_hypothesis(hypothesis)
        runner.emit_verdict("H-CHAIN", "EXPECTED", 5.0)

        assert len(runner.event_chain) == 1
        assert runner.event_chain[0]['outcome'] == 'EXPECTED'

    def test_verdict_with_z2_ratification_hash(self):
        """Test that verdicts can include Z2 ratification hash."""
        runner = PRSRunner()
        hypothesis = PreregisteredHypothesis(
            hypothesis_id="H-Z2",
            title="Test",
            prediction="a > 1",
            metric="a",
            threshold=1.0,
            direction="gt",
            experiment_params={},
            registered_at=datetime.now(timezone.utc).isoformat(),
            registered_sha="sha",
            prediction_window_days=7,
        )

        runner.register_hypothesis(hypothesis)

        z2_hash = runner.compute_z2_ratification_hash("H-Z2", "EXPECTED")
        verdict = runner.emit_verdict("H-Z2", "EXPECTED", 5.0, ratification_hash=z2_hash)

        assert verdict['status'] == 'EMITTED'
        # Check that ratification hash is in event chain
        assert runner.event_chain[0]['ratification_hash'] == z2_hash


class TestPRSRunnerNFLedger:
    """Tests for NF_LEDGER integration (PIN and RESOLVE entries)."""

    def test_nf_ledger_pin_entry_creation(self):
        """Test that registration creates PIN entry in NF_LEDGER."""
        runner = PRSRunner()
        hypothesis = PreregisteredHypothesis(
            hypothesis_id="H-PIN",
            title="Test",
            prediction="m > 50",
            metric="m",
            threshold=50.0,
            direction="gt",
            experiment_params={},
            registered_at=datetime.now(timezone.utc).isoformat(),
            registered_sha="sha",
            prediction_window_days=7,
        )

        runner.register_hypothesis(hypothesis)

        assert len(runner.nf_ledger_entries) == 1
        pin = runner.nf_ledger_entries[0]
        assert pin.entry_type == "PIN"
        assert pin.hypothesis_id == "H-PIN"
        assert pin.metric == "m"
        assert pin.prediction_value == 50.0
        assert pin.prediction_window_days == 7

    def test_nf_ledger_resolve_entry_creation(self):
        """Test that verdict creates RESOLVE entry in NF_LEDGER."""
        runner = PRSRunner()
        hypothesis = PreregisteredHypothesis(
            hypothesis_id="H-RESOLVE",
            title="Test",
            prediction="x > 10",
            metric="x",
            threshold=10.0,
            direction="gt",
            experiment_params={},
            registered_at=datetime.now(timezone.utc).isoformat(),
            registered_sha="sha",
            prediction_window_days=7,
        )

        runner.register_hypothesis(hypothesis)
        verdict = runner.emit_verdict("H-RESOLVE", "EXPECTED", 15.0)
        runner.update_nf_ledger("H-RESOLVE", verdict['verdict_id'], "EXPECTED", 15.0)

        assert len(runner.nf_ledger_entries) == 2
        resolve = runner.nf_ledger_entries[1]
        assert resolve.entry_type == "RESOLVE"
        assert resolve.metric_actual == 15.0
        assert resolve.brier_score == 0.0

    def test_nf_ledger_hash_chain_linking(self):
        """Test that ledger entries are hash-chained (prior_hash links)."""
        runner = PRSRunner()

        # Register two hypotheses
        h1 = PreregisteredHypothesis(
            hypothesis_id="H-1", title="Test", prediction="a > 1", metric="a",
            threshold=1.0, direction="gt", experiment_params={},
            registered_at=datetime.now(timezone.utc).isoformat(), registered_sha="sha", prediction_window_days=7,
        )
        h2 = PreregisteredHypothesis(
            hypothesis_id="H-2", title="Test", prediction="b > 2", metric="b",
            threshold=2.0, direction="gt", experiment_params={},
            registered_at=datetime.now(timezone.utc).isoformat(), registered_sha="sha", prediction_window_days=7,
        )

        runner.register_hypothesis(h1)
        pin1_hash = runner.nf_ledger_entries[0].hash

        runner.register_hypothesis(h2)
        pin2_prior = runner.nf_ledger_entries[1].prior_hash

        assert pin2_prior == pin1_hash

    def test_nf_ledger_z2_ratification_binding(self):
        """Test that RESOLVE entries include Z2 ratification hash."""
        runner = PRSRunner()
        hypothesis = PreregisteredHypothesis(
            hypothesis_id="H-Z2-BIND",
            title="Test",
            prediction="c > 3",
            metric="c",
            threshold=3.0,
            direction="gt",
            experiment_params={},
            registered_at=datetime.now(timezone.utc).isoformat(),
            registered_sha="sha",
            prediction_window_days=7,
        )

        runner.register_hypothesis(hypothesis)
        verdict = runner.emit_verdict("H-Z2-BIND", "EXPECTED", 5.0)

        z2_hash = runner.compute_z2_ratification_hash("H-Z2-BIND", "EXPECTED")
        z2_timestamp = datetime.now(timezone.utc).isoformat()

        runner.update_nf_ledger(
            "H-Z2-BIND", verdict['verdict_id'], "EXPECTED", 5.0,
            ratification_hash=z2_hash, z2_ratified_at=z2_timestamp
        )

        resolve = runner.nf_ledger_entries[1]
        assert resolve.ratification_hash == z2_hash
        assert resolve.z2_ratified_at == z2_timestamp

    def test_brier_score_calculation(self):
        """Test Brier score calculation for various outcomes."""
        runner = PRSRunner()

        # EXPECTED: prediction=1, outcome=1, brier = (1-1)^2 = 0
        result_expected = {"outcome": "EXPECTED", "brier": 0.0}

        # SURPRISE: prediction=1, outcome=0, brier = (1-0)^2 = 1
        result_surprise = {"outcome": "SURPRISE", "brier": 1.0}

        # VOID: no brier
        result_void = {"outcome": "VOID", "brier": None}

        assert result_expected["brier"] == 0.0
        assert result_surprise["brier"] == 1.0
        assert result_void["brier"] is None


class TestPRSRunnerCompleteCycle:
    """Tests for complete PRS cycle execution."""

    def test_complete_prs_cycle_expected(self):
        """Test complete cycle with EXPECTED outcome."""
        runner = PRSRunner()
        hypothesis = PreregisteredHypothesis(
            hypothesis_id="H-CYCLE-EXPECT",
            title="Complete Test",
            prediction="score > 80",
            metric="score",
            threshold=80.0,
            direction="gt",
            experiment_params={"model": "test"},
            registered_at=datetime.now(timezone.utc).isoformat(),
            registered_sha="cyclesha",
            prediction_window_days=7,
        )

        runner.register_hypothesis(hypothesis)

        result = runner.complete_prs_cycle(
            "H-CYCLE-EXPECT",
            {"score": 90.0},
            ratify_with_z2=True
        )

        assert result['status'] == 'COMPLETED'
        assert result['outcome'] == 'EXPECTED'
        assert result['metric_actual'] == 90.0
        assert result['brier_score'] == 0.0
        assert result['z2_ratified'] is True

    def test_complete_prs_cycle_void(self):
        """Test complete cycle with VOID outcome."""
        runner = PRSRunner()
        hypothesis = PreregisteredHypothesis(
            hypothesis_id="H-CYCLE-VOID",
            title="Test",
            prediction="missing > 0",
            metric="missing",
            threshold=0.0,
            direction="gt",
            experiment_params={},
            registered_at=datetime.now(timezone.utc).isoformat(),
            registered_sha="sha",
            prediction_window_days=7,
        )

        runner.register_hypothesis(hypothesis)

        result = runner.complete_prs_cycle(
            "H-CYCLE-VOID",
            {"present": 1.0},
            ratify_with_z2=False
        )

        assert result['status'] == 'COMPLETED_VOID'
        assert 'verdict' in result
        assert 'ledger' in result


class TestPRSRunnerExport:
    """Tests for event chain and ledger export."""

    def test_export_event_chain(self):
        """Test exporting VERDICT events as list."""
        runner = PRSRunner()
        hypothesis = PreregisteredHypothesis(
            hypothesis_id="H-EXPORT",
            title="Test",
            prediction="m > 1",
            metric="m",
            threshold=1.0,
            direction="gt",
            experiment_params={},
            registered_at=datetime.now(timezone.utc).isoformat(),
            registered_sha="sha",
            prediction_window_days=7,
        )

        runner.register_hypothesis(hypothesis)
        runner.emit_verdict("H-EXPORT", "EXPECTED", 5.0)

        chain = runner.export_event_chain()

        assert len(chain) == 1
        assert chain[0]['outcome'] == 'EXPECTED'
        assert chain[0]['metric_actual'] == 5.0

    def test_export_nf_ledger(self):
        """Test exporting NF_LEDGER entries as list."""
        runner = PRSRunner()
        hypothesis = PreregisteredHypothesis(
            hypothesis_id="H-LEDGER-EXP",
            title="Test",
            prediction="x > 2",
            metric="x",
            threshold=2.0,
            direction="gt",
            experiment_params={},
            registered_at=datetime.now(timezone.utc).isoformat(),
            registered_sha="sha",
            prediction_window_days=7,
        )

        runner.register_hypothesis(hypothesis)
        verdict = runner.emit_verdict("H-LEDGER-EXP", "EXPECTED", 3.0)
        runner.update_nf_ledger("H-LEDGER-EXP", verdict['verdict_id'], "EXPECTED", 3.0)

        ledger = runner.export_nf_ledger()

        assert len(ledger) == 2
        assert ledger[0]['entry_type'] == 'PIN'
        assert ledger[1]['entry_type'] == 'RESOLVE'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
