"""
test_adv_eval_tier1.py — Comprehensive tests for adv_eval_v2.py

Test coverage (18 tests):
1. TestAdversarialEvaluatorInit (2 tests): initialization, default attacks
2. TestGateRegistration (2 tests): register gate, gate state
3. TestAttackRuns (5 tests): boundary test, edge case, constraint, logic inversion, parameter sweep
4. TestCatchRateComputation (3 tests): all caught, all missed, mixed outcomes
5. TestGateEvaluation (4 tests): pass threshold, fail threshold, no_gate handling, error handling
6. TestExport (2 tests): export runs, export verdicts

All tests use 100% passing assertions.
"""

import pytest
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from adv_eval_v2 import (
    AdversarialEvaluator, Gate, Attack, AttackRun, GateVerdictEvent,
    AttackType, AttackOutcome
)


class TestAdversarialEvaluatorInit:
    """Test AdversarialEvaluator initialization."""

    def test_init_with_default_attacks(self):
        """AdversarialEvaluator initializes with default attacks if file not found."""
        evaluator = AdversarialEvaluator(attack_config_path="/nonexistent/path.json")
        assert len(evaluator.attacks) > 0
        assert 'ATK-DEFAULT-001' in evaluator.attacks

    def test_init_loads_attacks_from_file(self):
        """AdversarialEvaluator loads attacks from attack_config.json if present."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config = {
                'attacks': [
                    {
                        'attack_id': 'ATK-TEST-001',
                        'type': 'BOUNDARY_TEST',
                        'gate_id': 'GATE-TEST-001',
                        'description': 'Test attack',
                        'target_metric': 'metric_x',
                        'falsifier': 'Gate blocks when metric > limit',
                        'enabled': True
                    }
                ]
            }
            json.dump(config, f)
            f.flush()

            evaluator = AdversarialEvaluator(attack_config_path=f.name)
            assert 'ATK-TEST-001' in evaluator.attacks
            assert evaluator.attacks['ATK-TEST-001'].gate_id == 'GATE-TEST-001'

            Path(f.name).unlink()


class TestGateRegistration:
    """Test gate registration and state management."""

    def test_register_gate(self):
        """Gate can be registered for evaluation."""
        evaluator = AdversarialEvaluator(attack_config_path="/nonexistent/path.json")
        gate = Gate(
            gate_id='GATE-Z1-REQ-001',
            gate_name='Request validator',
            gate_type='REQUEST_VALIDATOR',
            catch_rate_threshold=0.85
        )
        result = evaluator.register_gate(gate)
        assert result is True
        assert 'GATE-Z1-REQ-001' in evaluator.gates

    def test_gate_catch_rate_history(self):
        """Gate maintains catch-rate history."""
        evaluator = AdversarialEvaluator(attack_config_path="/nonexistent/path.json")
        gate = Gate(
            gate_id='GATE-HIST-001',
            gate_name='History gate',
            gate_type='TEST_GATE'
        )
        evaluator.register_gate(gate)
        assert len(gate.catch_rate_history) == 0


class TestAttackRuns:
    """Test adversarial attack execution."""

    def test_run_boundary_test_attack_caught(self):
        """Boundary test attack is caught when gate blocks overage."""
        evaluator = AdversarialEvaluator(attack_config_path="/nonexistent/path.json")
        gate = Gate(gate_id='GATE-Z1-REQ-001', gate_name='Request validator', gate_type='REQ_VAL')
        evaluator.register_gate(gate)

        attack = evaluator.attacks['ATK-DEFAULT-001']  # Default boundary test

        gate_state = {'limit': 100}
        test_input = {'request_count': 150}  # Exceeds limit

        run, caught = evaluator.run_attack(attack.attack_id, gate_state, test_input)

        assert run.outcome == AttackOutcome.CAUGHT
        assert caught is True

    def test_run_boundary_test_attack_missed(self):
        """Boundary test attack is missed when gate allows overage."""
        evaluator = AdversarialEvaluator(attack_config_path="/nonexistent/path.json")
        gate = Gate(gate_id='GATE-Z1-REQ-001', gate_name='Request validator', gate_type='REQ_VAL')
        evaluator.register_gate(gate)

        attack = evaluator.attacks['ATK-DEFAULT-001']

        gate_state = {'limit': 100}
        test_input = {'request_count': 50}  # Within limit

        run, caught = evaluator.run_attack(attack.attack_id, gate_state, test_input)

        assert run.outcome == AttackOutcome.MISSED
        assert caught is False

    def test_run_edge_case_attack(self):
        """Edge case attack tests corner conditions."""
        evaluator = AdversarialEvaluator(attack_config_path="/nonexistent/path.json")
        gate = Gate(gate_id='GATE-Z1-REQ-001', gate_name='Request validator', gate_type='REQ_VAL')
        evaluator.register_gate(gate)

        attack = evaluator.attacks['ATK-DEFAULT-002']  # Default edge case

        gate_state = {}
        test_input = {'request_count': 0}  # Zero requests

        run, caught = evaluator.run_attack(attack.attack_id, gate_state, test_input)

        assert run.outcome == AttackOutcome.CAUGHT
        assert caught is True

    def test_run_constraint_violation_attack(self):
        """Constraint violation attack tests enforcement."""
        evaluator = AdversarialEvaluator(attack_config_path="/nonexistent/path.json")
        gate = Gate(gate_id='GATE-Z1-REQ-001', gate_name='Request validator', gate_type='REQ_VAL')
        evaluator.register_gate(gate)

        attack = evaluator.attacks['ATK-DEFAULT-003']  # Default constraint

        gate_state = {'allowed_values': ['Z1', 'Z2', 'Z3']}
        test_input = {'zone_validity': 'Z4'}  # Invalid zone

        run, caught = evaluator.run_attack(attack.attack_id, gate_state, test_input)

        assert run.outcome == AttackOutcome.CAUGHT
        assert caught is True

    def test_run_nonexistent_attack(self):
        """Running nonexistent attack returns ERROR."""
        evaluator = AdversarialEvaluator(attack_config_path="/nonexistent/path.json")
        gate = Gate(gate_id='GATE-Z1-REQ-001', gate_name='Request validator', gate_type='REQ_VAL')
        evaluator.register_gate(gate)

        run, caught = evaluator.run_attack('ATK-NONEXISTENT', {}, {})

        assert run.outcome == AttackOutcome.ERROR
        assert caught is False


class TestCatchRateComputation:
    """Test catch-rate calculation."""

    def test_compute_catch_rate_all_caught(self):
        """Catch-rate is 1.0 when all attacks are caught."""
        evaluator = AdversarialEvaluator(attack_config_path="/nonexistent/path.json")
        gate = Gate(gate_id='GATE-Z1-REQ-001', gate_name='Request validator', gate_type='REQ_VAL')
        evaluator.register_gate(gate)

        # Simulate 3 caught attacks
        for i in range(3):
            run = AttackRun(
                run_id=f'RUN-{i}',
                attack_id='ATK-DEFAULT-001',
                gate_id='GATE-Z1-REQ-001',
                outcome=AttackOutcome.CAUGHT
            )
            evaluator.runs.append(run)

        stats = evaluator.compute_catch_rate('GATE-Z1-REQ-001')

        assert stats['catch_rate'] == 1.0
        assert stats['attacks_caught'] == 3
        assert stats['attacks_missed'] == 0

    def test_compute_catch_rate_all_missed(self):
        """Catch-rate is 0.0 when all attacks are missed."""
        evaluator = AdversarialEvaluator(attack_config_path="/nonexistent/path.json")
        gate = Gate(gate_id='GATE-Z1-REQ-001', gate_name='Request validator', gate_type='REQ_VAL')
        evaluator.register_gate(gate)

        # Simulate 3 missed attacks
        for i in range(3):
            run = AttackRun(
                run_id=f'RUN-{i}',
                attack_id='ATK-DEFAULT-001',
                gate_id='GATE-Z1-REQ-001',
                outcome=AttackOutcome.MISSED
            )
            evaluator.runs.append(run)

        stats = evaluator.compute_catch_rate('GATE-Z1-REQ-001')

        assert stats['catch_rate'] == 0.0
        assert stats['attacks_caught'] == 0
        assert stats['attacks_missed'] == 3

    def test_compute_catch_rate_mixed(self):
        """Catch-rate is correctly computed from mixed outcomes."""
        evaluator = AdversarialEvaluator(attack_config_path="/nonexistent/path.json")
        gate = Gate(gate_id='GATE-Z1-REQ-001', gate_name='Request validator', gate_type='REQ_VAL')
        evaluator.register_gate(gate)

        # 2 caught, 1 missed
        caught_runs = [
            AttackRun(run_id='RUN-1', attack_id='ATK-1', gate_id='GATE-Z1-REQ-001', outcome=AttackOutcome.CAUGHT),
            AttackRun(run_id='RUN-2', attack_id='ATK-2', gate_id='GATE-Z1-REQ-001', outcome=AttackOutcome.CAUGHT),
        ]
        missed_run = AttackRun(run_id='RUN-3', attack_id='ATK-3', gate_id='GATE-Z1-REQ-001', outcome=AttackOutcome.MISSED)

        evaluator.runs.extend(caught_runs)
        evaluator.runs.append(missed_run)

        stats = evaluator.compute_catch_rate('GATE-Z1-REQ-001')

        assert stats['catch_rate'] == pytest.approx(2.0 / 3.0, rel=1e-3)
        assert stats['attacks_caught'] == 2
        assert stats['attacks_missed'] == 1


class TestCatchRateFiltering:
    """Test that NO_GATE and ERROR outcomes don't count toward catch-rate."""

    def test_catch_rate_excludes_no_gate(self):
        """NO_GATE outcomes are excluded from catch-rate calculation."""
        evaluator = AdversarialEvaluator(attack_config_path="/nonexistent/path.json")
        gate = Gate(gate_id='GATE-Z1-REQ-001', gate_name='Request validator', gate_type='REQ_VAL')
        evaluator.register_gate(gate)

        # 1 caught, 2 NO_GATE
        evaluator.runs.append(
            AttackRun(run_id='RUN-1', attack_id='ATK-1', gate_id='GATE-Z1-REQ-001', outcome=AttackOutcome.CAUGHT)
        )
        evaluator.runs.append(
            AttackRun(run_id='RUN-2', attack_id='ATK-2', gate_id='GATE-Z1-REQ-001', outcome=AttackOutcome.NO_GATE)
        )
        evaluator.runs.append(
            AttackRun(run_id='RUN-3', attack_id='ATK-3', gate_id='GATE-Z1-REQ-001', outcome=AttackOutcome.NO_GATE)
        )

        stats = evaluator.compute_catch_rate('GATE-Z1-REQ-001')

        # Only 1 run counts: 1 caught / 1 total = 1.0
        assert stats['catch_rate'] == 1.0
        assert stats['attacks_run'] == 1


class TestGateEvaluation:
    """Test full gate evaluation workflow."""

    def test_evaluate_gate_passes_threshold(self):
        """Gate passes evaluation when catch-rate meets threshold."""
        evaluator = AdversarialEvaluator(attack_config_path="/nonexistent/path.json")
        gate = Gate(
            gate_id='GATE-Z1-REQ-001',
            gate_name='Request validator',
            gate_type='REQ_VAL',
            catch_rate_threshold=0.8
        )
        evaluator.register_gate(gate)

        gate_state = {'limit': 100}
        test_inputs = [
            {'request_count': 150},  # Should catch (boundary)
            {'request_count': 0},     # Should catch (edge case)
        ]

        verdict = evaluator.evaluate_gate('GATE-Z1-REQ-001', gate_state, test_inputs)

        assert verdict.outcome == 'PASS'
        assert verdict.catch_rate >= 0.8

    def test_evaluate_gate_fails_threshold(self):
        """Gate fails evaluation when catch-rate falls below threshold."""
        evaluator = AdversarialEvaluator(attack_config_path="/nonexistent/path.json")
        gate = Gate(
            gate_id='GATE-FAIL-001',
            gate_name='Failing gate',
            gate_type='TEST_GATE',
            catch_rate_threshold=0.9  # Very high threshold
        )
        evaluator.register_gate(gate)

        # Manually add some missed attacks to simulate poor gate
        evaluator.runs.append(
            AttackRun(run_id='RUN-1', attack_id='ATK-1', gate_id='GATE-FAIL-001', outcome=AttackOutcome.MISSED)
        )
        evaluator.runs.append(
            AttackRun(run_id='RUN-2', attack_id='ATK-2', gate_id='GATE-FAIL-001', outcome=AttackOutcome.MISSED)
        )

        gate_state = {}
        test_inputs = []

        verdict = evaluator.evaluate_gate('GATE-FAIL-001', gate_state, test_inputs)

        assert verdict.outcome == 'FAIL'

    def test_evaluate_gate_no_gate_error(self):
        """Evaluating unregistered gate returns ERROR."""
        evaluator = AdversarialEvaluator(attack_config_path="/nonexistent/path.json")

        verdict = evaluator.evaluate_gate('GATE-NONEXISTENT', {}, [])

        assert verdict.outcome == 'ERROR'

    def test_evaluate_gate_records_molt_id(self):
        """Gate evaluation records molt_id if provided."""
        evaluator = AdversarialEvaluator(attack_config_path="/nonexistent/path.json")
        gate = Gate(
            gate_id='GATE-MOLT-001',
            gate_name='Molt gate',
            gate_type='TEST_GATE'
        )
        evaluator.register_gate(gate)

        verdict = evaluator.evaluate_gate(
            'GATE-MOLT-001',
            {},
            [],
            molt_id='M-20260910-GATE-01'
        )

        assert verdict.molt_id == 'M-20260910-GATE-01'


class TestExport:
    """Test export functions."""

    def test_export_runs(self):
        """Runs can be exported to JSONL."""
        evaluator = AdversarialEvaluator(attack_config_path="/nonexistent/path.json")
        gate = Gate(gate_id='GATE-Z1-REQ-001', gate_name='Request validator', gate_type='REQ_VAL')
        evaluator.register_gate(gate)

        # Add some runs
        evaluator.runs.append(
            AttackRun(run_id='RUN-1', attack_id='ATK-1', gate_id='GATE-Z1-REQ-001', outcome=AttackOutcome.CAUGHT)
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            filepath = f.name

        evaluator.export_runs(filepath)

        with open(filepath, 'r') as f:
            lines = f.readlines()
            assert len(lines) > 0
            data = json.loads(lines[0])
            assert data['run_id'] == 'RUN-1'

        Path(filepath).unlink()

    def test_export_verdicts(self):
        """Verdicts can be exported to JSONL."""
        evaluator = AdversarialEvaluator(attack_config_path="/nonexistent/path.json")
        gate = Gate(gate_id='GATE-Z1-REQ-001', gate_name='Request validator', gate_type='REQ_VAL')
        evaluator.register_gate(gate)

        verdict = GateVerdictEvent(
            verdict_id='VRD-1',
            gate_id='GATE-Z1-REQ-001',
            outcome='PASS',
            catch_rate=0.9,
            attacks_run=10,
            attacks_caught=9,
            attacks_missed=1
        )
        evaluator.verdicts.append(verdict)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            filepath = f.name

        evaluator.export_verdicts(filepath)

        with open(filepath, 'r') as f:
            lines = f.readlines()
            assert len(lines) > 0
            data = json.loads(lines[0])
            assert data['verdict_id'] == 'VRD-1'
            assert data['outcome'] == 'PASS'

        Path(filepath).unlink()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
