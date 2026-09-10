"""
adv_eval_v2.py — Adversarial Evaluation with Catch-Rate Tracking (v0.2)

Tests gates by attempting attacks. Catch-rate = (attacks_caught / attacks_run).
Gates must achieve threshold catch-rate before molt can KEEP.

Pattern:
1. Gate change triggers adversarial eval (Tier-2 molt on gate)
2. Evaluator loads attack list for the gate
3. For each attack: attempt execution, record catch/miss
4. Compute catch-rate: (caught / total) attacks
5. Report VERDICT: gate passes/fails catch-rate threshold
6. NO_GATE verdict never counts toward catch-rate (blocked before exec)

Integrated with molt_cycle.py: If gate molt predicts improvement,
ADV must run and gate must meet catch-rate threshold before KEEP.
"""

import json
import hashlib
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from enum import Enum


class AttackType(Enum):
    """Types of adversarial attacks."""
    BOUNDARY_TEST = "BOUNDARY_TEST"      # Test boundary conditions
    LOGIC_INVERSION = "LOGIC_INVERSION"  # Invert gate logic
    PARAMETER_SWEEP = "PARAMETER_SWEEP"  # Sweep parameters
    CONSTRAINT_VIOLATION = "CONSTRAINT_VIOLATION"  # Violate constraints
    EDGE_CASE = "EDGE_CASE"              # Test edge cases


class AttackOutcome(Enum):
    """Outcome of an adversarial attack."""
    CAUGHT = "CAUGHT"                    # Gate detected and blocked attack
    MISSED = "MISSED"                    # Gate allowed attack (failed)
    NO_GATE = "NO_GATE"                  # Gate not available (never counts)
    ERROR = "ERROR"                      # Attack execution error (dropped)


@dataclass
class Gate:
    """A gate being tested by adversarial evaluation."""
    gate_id: str                         # e.g., "GATE-Z1-REQ-001"
    gate_name: str                       # e.g., "Request validator"
    gate_type: str                       # e.g., "REQUEST_VALIDATOR"
    molt_id: Optional[str] = None        # Molt that modified this gate
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    catch_rate_threshold: float = 0.85   # Gate must catch 85% of attacks
    catch_rate_history: List[float] = field(default_factory=list)


@dataclass
class Attack:
    """An adversarial attack on a gate."""
    attack_id: str                       # e.g., "ATK-20260910-001"
    attack_type: AttackType
    gate_id: str
    description: str                     # Human-readable attack description
    target_metric: str                   # What metric does this test
    falsifier: str                       # Condition that proves attack succeeded
    enabled: bool = True


@dataclass
class AttackRun:
    """Record of one attack execution attempt."""
    run_id: str                          # e.g., "RUN-20260910-001"
    attack_id: str
    gate_id: str
    outcome: AttackOutcome
    metric_value: Optional[float] = None
    notes: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class GateVerdictEvent:
    """Verdict event from adversarial evaluation."""
    verdict_id: str
    gate_id: str
    outcome: str                         # PASS, FAIL, NO_GATE, ERROR
    catch_rate: Optional[float]
    attacks_run: int
    attacks_caught: int
    attacks_missed: int
    molt_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AdversarialEvaluator:
    """Orchestrates adversarial evaluation of gates."""

    def __init__(self, attack_config_path: str = "attack_config.json"):
        """
        Initialize AdversarialEvaluator.

        Args:
            attack_config_path: Path to attack configuration JSON
        """
        self.attack_config_path = attack_config_path
        self.attacks: Dict[str, Attack] = {}
        self.gates: Dict[str, Gate] = {}
        self.runs: List[AttackRun] = []
        self.verdicts: List[GateVerdictEvent] = []
        self._load_attack_config()

    def _load_attack_config(self):
        """Load attack definitions from attack_config.json."""
        try:
            with open(self.attack_config_path, 'r') as f:
                config = json.load(f)

            for attack_def in config.get('attacks', []):
                attack = Attack(
                    attack_id=attack_def.get('attack_id'),
                    attack_type=AttackType[attack_def.get('type', 'EDGE_CASE')],
                    gate_id=attack_def.get('gate_id'),
                    description=attack_def.get('description', ''),
                    target_metric=attack_def.get('target_metric', ''),
                    falsifier=attack_def.get('falsifier', ''),
                    enabled=attack_def.get('enabled', True)
                )
                self.attacks[attack.attack_id] = attack
        except FileNotFoundError:
            self._create_default_attacks()

    def _create_default_attacks(self):
        """Create default attack set for testing."""
        default_attacks = [
            Attack(
                attack_id='ATK-DEFAULT-001',
                attack_type=AttackType.BOUNDARY_TEST,
                gate_id='GATE-Z1-REQ-001',
                description='Test boundary condition: max requests',
                target_metric='request_count',
                falsifier='Gate blocks when request_count > limit'
            ),
            Attack(
                attack_id='ATK-DEFAULT-002',
                attack_type=AttackType.EDGE_CASE,
                gate_id='GATE-Z1-REQ-001',
                description='Test edge case: zero requests',
                target_metric='request_count',
                falsifier='Gate allows when request_count == 0'
            ),
            Attack(
                attack_id='ATK-DEFAULT-003',
                attack_type=AttackType.CONSTRAINT_VIOLATION,
                gate_id='GATE-Z1-REQ-001',
                description='Test constraint: invalid zone',
                target_metric='zone_validity',
                falsifier='Gate blocks when zone not in allowed set'
            ),
        ]
        for attack in default_attacks:
            self.attacks[attack.attack_id] = attack

    def register_gate(self, gate: Gate) -> bool:
        """Register a gate for evaluation."""
        self.gates[gate.gate_id] = gate
        return True

    def run_attack(
        self,
        attack_id: str,
        gate_state: Dict[str, Any],
        test_input: Dict[str, Any]
    ) -> Tuple[AttackRun, bool]:
        """
        Execute one adversarial attack.

        Args:
            attack_id: ID of attack to run
            gate_state: Current gate state (parameters, config)
            test_input: Input parameters for the attack

        Returns:
            (AttackRun record, caught: bool)
        """
        if attack_id not in self.attacks:
            run = AttackRun(
                run_id=f"RUN-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-ERR",
                attack_id=attack_id,
                gate_id='UNKNOWN',
                outcome=AttackOutcome.ERROR,
                notes="Attack not found"
            )
            self.runs.append(run)
            return run, False

        attack = self.attacks[attack_id]
        if not attack.enabled:
            run = AttackRun(
                run_id=f"RUN-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-SKIP",
                attack_id=attack_id,
                gate_id=attack.gate_id,
                outcome=AttackOutcome.NO_GATE,
                notes="Attack disabled"
            )
            self.runs.append(run)
            return run, False

        # Check if gate is available
        if attack.gate_id not in self.gates:
            run = AttackRun(
                run_id=f"RUN-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-NOGATE",
                attack_id=attack_id,
                gate_id=attack.gate_id,
                outcome=AttackOutcome.NO_GATE,
                notes="Gate not found or not available"
            )
            self.runs.append(run)
            return run, False

        # Simulate attack execution: check if falsifier was triggered
        caught = self._simulate_attack(attack, gate_state, test_input)

        outcome = AttackOutcome.CAUGHT if caught else AttackOutcome.MISSED
        run = AttackRun(
            run_id=f"RUN-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{attack.attack_type.value[:3]}",
            attack_id=attack_id,
            gate_id=attack.gate_id,
            outcome=outcome,
            metric_value=test_input.get(attack.target_metric),
            notes=f"Falsifier: {attack.falsifier}"
        )
        self.runs.append(run)
        return run, caught

    def _simulate_attack(
        self,
        attack: Attack,
        gate_state: Dict[str, Any],
        test_input: Dict[str, Any]
    ) -> bool:
        """
        Simulate attack execution and determine if gate caught it.

        Returns:
            True if gate caught the attack (CAUGHT), False if gate missed (MISSED)
        """
        # Boundary test: check if gate respects limits
        if attack.attack_type == AttackType.BOUNDARY_TEST:
            limit = gate_state.get('limit', 100)
            metric_val = test_input.get(attack.target_metric, 0)
            return metric_val > limit

        # Edge case: check corner cases
        if attack.attack_type == AttackType.EDGE_CASE:
            metric_val = test_input.get(attack.target_metric, 0)
            return metric_val == 0 or metric_val is None

        # Logic inversion: check if gate inverts correctly
        if attack.attack_type == AttackType.LOGIC_INVERSION:
            expected = gate_state.get('expected_result', True)
            actual = test_input.get('actual_result', False)
            return expected != actual

        # Constraint violation: check if gate enforces constraints
        if attack.attack_type == AttackType.CONSTRAINT_VIOLATION:
            allowed_values = gate_state.get('allowed_values', [])
            metric_val = test_input.get(attack.target_metric)
            return metric_val not in allowed_values

        # Default: parameter sweep (probabilistic)
        return test_input.get('should_trigger', False)

    def compute_catch_rate(self, gate_id: str) -> Dict[str, Any]:
        """
        Compute catch-rate for a gate from run history.

        Args:
            gate_id: Gate to compute catch-rate for

        Returns:
            {catch_rate, attacks_run, attacks_caught, attacks_missed}
        """
        gate_runs = [r for r in self.runs if r.gate_id == gate_id]

        # Filter out NO_GATE and ERROR outcomes (they don't count)
        countable_runs = [r for r in gate_runs if r.outcome in [AttackOutcome.CAUGHT, AttackOutcome.MISSED]]

        if len(countable_runs) == 0:
            return {
                'catch_rate': 0.0,
                'attacks_run': 0,
                'attacks_caught': 0,
                'attacks_missed': 0
            }

        caught = len([r for r in countable_runs if r.outcome == AttackOutcome.CAUGHT])
        total = len(countable_runs)

        return {
            'catch_rate': caught / total if total > 0 else 0.0,
            'attacks_run': total,
            'attacks_caught': caught,
            'attacks_missed': total - caught
        }

    def evaluate_gate(
        self,
        gate_id: str,
        gate_state: Dict[str, Any],
        test_inputs: List[Dict[str, Any]],
        molt_id: Optional[str] = None
    ) -> GateVerdictEvent:
        """
        Run full evaluation of a gate against all applicable attacks.

        Args:
            gate_id: Gate to evaluate
            gate_state: Current gate state/config
            test_inputs: List of test input sets (one per attack)
            molt_id: Optional molt ID (if gate was just changed by molt)

        Returns:
            GateVerdictEvent with verdict and catch-rate
        """
        if gate_id not in self.gates:
            verdict = GateVerdictEvent(
                verdict_id=f"VRD-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-ERR",
                gate_id=gate_id,
                outcome="ERROR",
                catch_rate=None,
                attacks_run=0,
                attacks_caught=0,
                attacks_missed=0,
                molt_id=molt_id
            )
            self.verdicts.append(verdict)
            return verdict

        gate = self.gates[gate_id]

        # Run attacks for this gate
        gate_attacks = [a for a in self.attacks.values() if a.gate_id == gate_id and a.enabled]

        for i, attack in enumerate(gate_attacks):
            test_input = test_inputs[i] if i < len(test_inputs) else {}
            self.run_attack(attack.attack_id, gate_state, test_input)

        # Compute catch-rate
        stats = self.compute_catch_rate(gate_id)

        # Determine verdict: PASS if catch_rate >= threshold, else FAIL
        passes_threshold = stats['catch_rate'] >= gate.catch_rate_threshold
        outcome = "PASS" if passes_threshold else "FAIL"

        # Record to history
        gate.catch_rate_history.append(stats['catch_rate'])

        verdict = GateVerdictEvent(
            verdict_id=f"VRD-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{outcome[:3]}",
            gate_id=gate_id,
            outcome=outcome,
            catch_rate=stats['catch_rate'],
            attacks_run=stats['attacks_run'],
            attacks_caught=stats['attacks_caught'],
            attacks_missed=stats['attacks_missed'],
            molt_id=molt_id
        )
        self.verdicts.append(verdict)
        return verdict

    def export_runs(self, filepath: str = "adv_eval_runs.jsonl"):
        """Export attack runs to JSONL file."""
        with open(filepath, 'w') as f:
            for run in self.runs:
                f.write(json.dumps(asdict(run), default=str) + '\n')

    def export_verdicts(self, filepath: str = "adv_eval_verdicts.jsonl"):
        """Export verdicts to JSONL file."""
        with open(filepath, 'w') as f:
            for verdict in self.verdicts:
                f.write(json.dumps(asdict(verdict), default=str) + '\n')

    def export_gate_summary(self, filepath: str = "adv_eval_gates.json"):
        """Export gate summary including catch-rate history."""
        summary = {}
        for gate_id, gate in self.gates.items():
            summary[gate_id] = {
                'gate_name': gate.gate_name,
                'gate_type': gate.gate_type,
                'catch_rate_threshold': gate.catch_rate_threshold,
                'catch_rate_history': gate.catch_rate_history,
                'current_catch_rate': gate.catch_rate_history[-1] if gate.catch_rate_history else None,
                'attacks_run_count': len([r for r in self.runs if r.gate_id == gate_id])
            }
        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2)
