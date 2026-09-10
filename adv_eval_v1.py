"""
adv_eval_v1.py — Adversarial Evaluation Engine

Tests gate robustness by running attacks designed to bypass or fail each gate.
Tracks catch rates (what % of attacks were caught). Z2 chooses which attacks
to run; code runs them and emits VERDICT + ATTACK events.

Pattern:
1. READ: Fetch gates to test, attack suite from Z2 spec
2. EXECUTE: Run each attack against target gate
3. MEASURE: Track attack outcome (caught, bypassed, error)
4. EMIT: ATTACK event for each attack, VERDICT summary per gate
5. REPORT: Catch rate and NO_GATE incidents (never count toward catch rate)

Gates tested (from Phase 2 M11-M15):
1. FalsifierLintGate — requires falsifier presence, substantiveness, testability
2. Z2HashVerifyGate — SHA256 signature validation
3. AntiCascadeLintRule — enforces 5 anti-cascade rules
4. MerkleRootGate — tree-based ledger integrity
5. FullCIIntegrationGate — orchestrates all 5 gates in sequence

No auto-approve; Z2 must explicitly authorize new attacks via molt.
"""

import json
import hashlib
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from enum import Enum


class AttackOutcome(Enum):
    """Outcome of an attack against a gate."""
    CAUGHT = "CAUGHT"          # Gate blocked the attack (success)
    BYPASSED = "BYPASSED"      # Attack got through (failure)
    ERROR = "ERROR"            # Gate errored on attack
    NO_GATE = "NO_GATE"        # Gate doesn't exist (never counts as caught)
    TIMEOUT = "TIMEOUT"        # Attack exceeded time limit


class GateType(Enum):
    """Types of gates in the CI pipeline."""
    FALSIFIER_LINT = "FalsifierLintGate"
    Z2_HASH_VERIFY = "Z2HashVerifyGate"
    ANTI_CASCADE = "AntiCascadeLintRule"
    MERKLE_ROOT = "MerkleRootGate"
    FULL_CI = "FullCIIntegrationGate"


@dataclass
class Attack:
    """A single attack against a gate."""
    attack_id: str
    gate: str                  # GateType name
    name: str                  # Human-readable attack name
    description: str
    payload: Dict[str, Any]    # Attack payload
    expected_catch: bool       # Z2 prediction: should this be caught?
    authorized_by_z2: bool = False  # Z2 approved this attack


@dataclass
class AttackEvent:
    """Event emitted after attack execution."""
    event_id: str
    attack_id: str
    gate: str
    outcome: str               # CAUGHT, BYPASSED, ERROR, NO_GATE, TIMEOUT
    payload_hash: str
    gate_response: Optional[Dict[str, Any]]
    expected_catch: bool
    matched_expectation: bool
    timestamp: str


@dataclass
class GateVerdictSummary:
    """Summary of attacks against one gate."""
    gate: str
    total_attacks: int
    attacks_caught: int
    attacks_bypassed: int
    attacks_error: int
    attacks_no_gate: int
    catch_rate: float          # attacks_caught / (total - no_gate)
    matched_expectations: int
    timestamp: str


class AdversarialEvalEngine:
    """Adversarial Evaluation Engine — tests gate robustness."""

    def __init__(self):
        self.attacks = []
        self.events = []
        self.summaries = []
        self.gate_implementations = {}  # Registry of gate implementations

    def register_gate(self, gate_name: str, gate_fn: Callable) -> Dict[str, Any]:
        """
        Register a gate implementation for testing.

        Args:
            gate_name: Name of gate (e.g., 'FalsifierLintGate')
            gate_fn: Function that implements the gate

        Returns:
            Dict with registration status
        """
        self.gate_implementations[gate_name] = gate_fn
        return {
            'gate': gate_name,
            'status': 'REGISTERED',
            'callable': gate_fn is not None,
        }

    def define_attack(self, attack: Attack) -> Dict[str, Any]:
        """
        Define an attack for Z2 approval.

        Args:
            attack: Attack object with payload

        Returns:
            Dict with attack_id, status, awaiting_z2
        """
        self.attacks.append(attack)

        return {
            'attack_id': attack.attack_id,
            'gate': attack.gate,
            'status': 'AWAITING_Z2_APPROVAL' if not attack.authorized_by_z2 else 'APPROVED',
            'expected_catch': attack.expected_catch,
        }

    def authorize_attack(self, attack_id: str) -> Dict[str, Any]:
        """
        Z2 approves an attack for execution.

        Args:
            attack_id: ID of attack to authorize

        Returns:
            Dict with authorization status
        """
        for attack in self.attacks:
            if attack.attack_id == attack_id:
                attack.authorized_by_z2 = True
                return {
                    'attack_id': attack_id,
                    'status': 'AUTHORIZED',
                    'gate': attack.gate,
                }

        return {
            'attack_id': attack_id,
            'status': 'NOT_FOUND',
            'error': f'Attack {attack_id} not defined',
        }

    def execute_attack(self, attack: Attack) -> Dict[str, Any]:
        """
        Execute a single attack against its target gate.

        Args:
            attack: Attack to execute

        Returns:
            Dict with outcome, gate_response, event
        """
        # Check if gate exists
        if attack.gate not in self.gate_implementations:
            event_id = f'ATK-{datetime.now().isoformat()[:10]}-{len(self.events):05d}'

            event = AttackEvent(
                event_id=event_id,
                attack_id=attack.attack_id,
                gate=attack.gate,
                outcome=AttackOutcome.NO_GATE.value,
                payload_hash=hashlib.sha256(json.dumps(attack.payload, sort_keys=True).encode()).hexdigest(),
                gate_response=None,
                expected_catch=attack.expected_catch,
                matched_expectation=False,  # NO_GATE never counts as caught
                timestamp=datetime.now().isoformat(),
            )

            self.events.append(asdict(event))

            return {
                'attack_id': attack.attack_id,
                'outcome': AttackOutcome.NO_GATE.value,
                'reason': f'Gate {attack.gate} not registered',
                'event_id': event_id,
            }

        # Execute attack against gate
        gate_fn = self.gate_implementations[attack.gate]

        try:
            gate_response = gate_fn(attack.payload)
        except Exception as e:
            event_id = f'ATK-{datetime.now().isoformat()[:10]}-{len(self.events):05d}'

            event = AttackEvent(
                event_id=event_id,
                attack_id=attack.attack_id,
                gate=attack.gate,
                outcome=AttackOutcome.ERROR.value,
                payload_hash=hashlib.sha256(json.dumps(attack.payload, sort_keys=True).encode()).hexdigest(),
                gate_response={'error': str(e)},
                expected_catch=attack.expected_catch,
                matched_expectation=False,
                timestamp=datetime.now().isoformat(),
            )

            self.events.append(asdict(event))

            return {
                'attack_id': attack.attack_id,
                'outcome': AttackOutcome.ERROR.value,
                'error': str(e),
                'event_id': event_id,
            }

        # Determine if attack was caught
        # Gate returns {"valid": True/False} or {"status": "PASS"/"FAIL"}
        caught = not gate_response.get('valid', True) or gate_response.get('status') == 'FAIL'

        outcome = AttackOutcome.CAUGHT if caught else AttackOutcome.BYPASSED
        matched_expectation = (caught == attack.expected_catch)

        event_id = f'ATK-{datetime.now().isoformat()[:10]}-{len(self.events):05d}'

        event = AttackEvent(
            event_id=event_id,
            attack_id=attack.attack_id,
            gate=attack.gate,
            outcome=outcome.value,
            payload_hash=hashlib.sha256(json.dumps(attack.payload, sort_keys=True).encode()).hexdigest(),
            gate_response=gate_response,
            expected_catch=attack.expected_catch,
            matched_expectation=matched_expectation,
            timestamp=datetime.now().isoformat(),
        )

        self.events.append(asdict(event))

        return {
            'attack_id': attack.attack_id,
            'outcome': outcome.value,
            'caught': caught,
            'matched_expectation': matched_expectation,
            'gate_response': gate_response,
            'event_id': event_id,
        }

    def execute_attack_suite(self, gate_name: str, authorized_only: bool = True) -> Dict[str, Any]:
        """
        Execute all attacks against a specific gate.

        Args:
            gate_name: Name of gate to test
            authorized_only: Only run Z2-authorized attacks

        Returns:
            Dict with execution results and summary
        """
        target_attacks = [a for a in self.attacks if a.gate == gate_name]

        if authorized_only:
            target_attacks = [a for a in target_attacks if a.authorized_by_z2]

        results = []
        caught_count = 0
        bypassed_count = 0
        error_count = 0
        no_gate_count = 0
        matched_count = 0

        for attack in target_attacks:
            result = self.execute_attack(attack)
            results.append(result)

            outcome = result['outcome']
            if outcome == AttackOutcome.CAUGHT.value:
                caught_count += 1
            elif outcome == AttackOutcome.BYPASSED.value:
                bypassed_count += 1
            elif outcome == AttackOutcome.ERROR.value:
                error_count += 1
            elif outcome == AttackOutcome.NO_GATE.value:
                no_gate_count += 1

            if result.get('matched_expectation'):
                matched_count += 1

        # Calculate catch rate (excluding NO_GATE incidents)
        evaluable_attacks = caught_count + bypassed_count + error_count
        catch_rate = caught_count / evaluable_attacks if evaluable_attacks > 0 else 0.0

        summary = GateVerdictSummary(
            gate=gate_name,
            total_attacks=len(target_attacks),
            attacks_caught=caught_count,
            attacks_bypassed=bypassed_count,
            attacks_error=error_count,
            attacks_no_gate=no_gate_count,
            catch_rate=catch_rate,
            matched_expectations=matched_count,
            timestamp=datetime.now().isoformat(),
        )

        self.summaries.append(asdict(summary))

        return {
            'gate': gate_name,
            'attack_results': results,
            'summary': asdict(summary),
        }

    def execute_all_gates(self, authorized_only: bool = True) -> Dict[str, Any]:
        """
        Execute attack suite against all gates.

        Args:
            authorized_only: Only run Z2-authorized attacks

        Returns:
            Dict with results per gate and overall summary
        """
        results = {}

        for gate_name in self.gate_implementations.keys():
            results[gate_name] = self.execute_attack_suite(gate_name, authorized_only)

        # Overall summary
        total_attacks = len([a for a in self.attacks if not authorized_only or a.authorized_by_z2])
        total_caught = sum(s['attacks_caught'] for s in [r['summary'] for r in results.values()])
        total_evaluable = sum(s['attacks_caught'] + s['attacks_bypassed'] + s['attacks_error']
                              for s in [r['summary'] for r in results.values()])
        overall_catch_rate = total_caught / total_evaluable if total_evaluable > 0 else 0.0

        return {
            'gates_tested': len(results),
            'total_attacks': total_attacks,
            'total_caught': total_caught,
            'total_evaluable': total_evaluable,
            'overall_catch_rate': overall_catch_rate,
            'per_gate': results,
            'summary': self.summaries[-len(results):],  # Last N summaries
        }

    def report_catch_rates(self) -> Dict[str, Any]:
        """Report catch rates per gate."""
        if not self.summaries:
            return {'error': 'No attacks executed yet'}

        report = {}
        for summary in self.summaries:
            gate = summary['gate']
            report[gate] = {
                'catch_rate': summary['catch_rate'],
                'attacks_caught': summary['attacks_caught'],
                'attacks_bypassed': summary['attacks_bypassed'],
                'total_evaluable': summary['attacks_caught'] + summary['attacks_bypassed'] + summary['attacks_error'],
            }

        return report
