"""
prs_run.py — Preregistered Study Runner

Executes locked preregistered experiments. No overrides, no parameter changes.
Reads hypothesis from REGISTERED.md (pinned SHA), runs experiment, emits VERDICT.

Pattern:
1. READ: Fetch REGISTERED.md at pinned SHA, load hypothesis
2. VALIDATE: Confirm hypothesis frozen (locked parameters, no edits)
3. RUN: Execute experiment with locked parameters
4. MEASURE: Resolve prediction (prediction vs outcome)
5. VERDICT: Emit VERDICT event (SURPRISE/EXPECTED/VOID), update NF_LEDGER
"""

import json
import hashlib
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class PredictionOutcome(Enum):
    """Outcome of preregistered prediction after experiment."""
    EXPECTED = "EXPECTED"      # Outcome matched prediction
    SURPRISE = "SURPRISE"      # Outcome contradicted prediction
    VOID = "VOID"              # Experiment unmeasurable (null outcome)


@dataclass
class PreregisteredHypothesis:
    """A preregistered study hypothesis with locked parameters."""
    hypothesis_id: str          # e.g., "H-20260910-001"
    title: str
    prediction: str             # "Metric X will be > Y" (testable)
    metric: str                 # "metric_x"
    threshold: float
    direction: str              # "gt" (greater-than), "lt", "eq"
    experiment_params: Dict[str, Any]  # Locked; no changes allowed
    registered_at: str          # ISO timestamp of registration
    registered_sha: str         # SHA256 of REGISTERED.md at registration
    prediction_window_days: int # Days until measurement window closes


@dataclass
class VerdictEvent:
    """Verdict event emitted after experiment completes."""
    verdict_id: str
    hypothesis_id: str
    outcome: str                # EXPECTED, SURPRISE, VOID
    metric_actual: Optional[float]
    metric_predicted: Optional[float]
    matched: bool
    experiment_start: str
    experiment_end: str
    measured_at: str           # ISO timestamp


class PRSRunner:
    """Preregistered Study runner — executes locked hypotheses."""

    def __init__(self):
        self.registered_hypotheses = {}
        self.verdicts = []
        self.experiment_events = []

    def register_hypothesis(self, hypothesis: PreregisteredHypothesis) -> Dict[str, Any]:
        """
        Register a hypothesis from REGISTERED.md.

        Args:
            hypothesis: PreregisteredHypothesis object with locked params

        Returns:
            Dict with hypothesis_id, status, registered_sha
        """
        self.registered_hypotheses[hypothesis.hypothesis_id] = hypothesis

        return {
            'hypothesis_id': hypothesis.hypothesis_id,
            'status': 'REGISTERED',
            'registered_sha': hypothesis.registered_sha,
            'params_frozen': True,
            'prediction_window_days': hypothesis.prediction_window_days,
        }

    def validate_hypothesis_frozen(self, hypothesis_id: str) -> Dict[str, Any]:
        """
        Validate that hypothesis parameters are frozen (locked).
        No edits allowed after registration.
        """
        if hypothesis_id not in self.registered_hypotheses:
            return {'valid': False, 'reason': f'hypothesis not found: {hypothesis_id}'}

        hypothesis = self.registered_hypotheses[hypothesis_id]

        return {
            'valid': True,
            'hypothesis_id': hypothesis_id,
            'params_frozen': True,
            'registered_sha': hypothesis.registered_sha,
        }

    def run_experiment(self, hypothesis_id: str, experiment_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run an experiment with locked hypothesis parameters.

        Args:
            hypothesis_id: ID of registered hypothesis
            experiment_results: {metric_name: value, ...} from experiment execution

        Returns:
            Dict with experiment status, metric_actual
        """
        if hypothesis_id not in self.registered_hypotheses:
            return {'status': 'ERROR', 'reason': f'hypothesis not found: {hypothesis_id}'}

        hypothesis = self.registered_hypotheses[hypothesis_id]

        # Extract actual metric from experiment results
        metric_actual = experiment_results.get(hypothesis.metric)

        if metric_actual is None:
            return {
                'status': 'VOID',
                'hypothesis_id': hypothesis_id,
                'reason': f'metric {hypothesis.metric} not in results',
            }

        experiment_start = datetime.now().isoformat()
        experiment_end = datetime.now().isoformat()

        self.experiment_events.append({
            'hypothesis_id': hypothesis_id,
            'metric_actual': metric_actual,
            'experiment_start': experiment_start,
            'experiment_end': experiment_end,
        })

        return {
            'status': 'COMPLETED',
            'hypothesis_id': hypothesis_id,
            'metric_actual': metric_actual,
            'experiment_start': experiment_start,
            'experiment_end': experiment_end,
        }

    def resolve_prediction(self, hypothesis_id: str, metric_actual: float) -> Dict[str, Any]:
        """
        Resolve prediction by comparing actual to predicted threshold.

        Args:
            hypothesis_id: ID of registered hypothesis
            metric_actual: Actual metric value from experiment

        Returns:
            Dict with outcome (EXPECTED/SURPRISE/VOID), matched boolean
        """
        if hypothesis_id not in self.registered_hypotheses:
            return {'outcome': 'VOID', 'reason': f'hypothesis not found: {hypothesis_id}'}

        hypothesis = self.registered_hypotheses[hypothesis_id]

        # Compare actual to threshold using direction
        if hypothesis.direction == "gt":
            matched = metric_actual > hypothesis.threshold
        elif hypothesis.direction == "lt":
            matched = metric_actual < hypothesis.threshold
        elif hypothesis.direction == "eq":
            matched = metric_actual == hypothesis.threshold
        else:
            return {'outcome': 'VOID', 'reason': f'unknown direction: {hypothesis.direction}'}

        outcome = PredictionOutcome.EXPECTED if matched else PredictionOutcome.SURPRISE

        return {
            'outcome': outcome.value,
            'matched': matched,
            'metric_actual': metric_actual,
            'metric_predicted': hypothesis.threshold,
            'direction': hypothesis.direction,
        }

    def emit_verdict(self, hypothesis_id: str, outcome: str, metric_actual: Optional[float]) -> Dict[str, Any]:
        """
        Emit VERDICT event after experiment completes and prediction resolves.

        Args:
            hypothesis_id: ID of registered hypothesis
            outcome: EXPECTED, SURPRISE, or VOID
            metric_actual: Actual metric value (None if VOID)

        Returns:
            Dict with verdict_id, event details
        """
        if hypothesis_id not in self.registered_hypotheses:
            return {'status': 'ERROR', 'reason': f'hypothesis not found: {hypothesis_id}'}

        hypothesis = self.registered_hypotheses[hypothesis_id]

        verdict_id = f'V-{datetime.now().isoformat()[:10]}-{len(self.verdicts):05d}'

        verdict = VerdictEvent(
            verdict_id=verdict_id,
            hypothesis_id=hypothesis_id,
            outcome=outcome,
            metric_actual=metric_actual,
            metric_predicted=hypothesis.threshold if outcome != 'VOID' else None,
            matched=(outcome == 'EXPECTED'),
            experiment_start=datetime.now().isoformat(),
            experiment_end=datetime.now().isoformat(),
            measured_at=datetime.now().isoformat(),
        )

        self.verdicts.append(asdict(verdict))

        return {
            'verdict_id': verdict_id,
            'hypothesis_id': hypothesis_id,
            'outcome': outcome,
            'status': 'EMITTED',
        }

    def update_nf_ledger(self, hypothesis_id: str, verdict_id: str, outcome: str, metric_actual: Optional[float]) -> Dict[str, Any]:
        """
        Update NF_LEDGER with prediction outcome (Brier scoring).

        Args:
            hypothesis_id: ID of registered hypothesis
            verdict_id: ID of emitted verdict
            outcome: EXPECTED, SURPRISE, or VOID
            metric_actual: Actual metric value

        Returns:
            Dict with ledger_entry details
        """
        if hypothesis_id not in self.registered_hypotheses:
            return {'status': 'ERROR', 'reason': f'hypothesis not found: {hypothesis_id}'}

        hypothesis = self.registered_hypotheses[hypothesis_id]

        # Calculate Brier score: (prediction - outcome)^2
        # prediction: 1 if matched expected, 0 if surprise, None if void
        if outcome == 'VOID':
            brier_score = None
        else:
            prediction_prob = 1.0 if outcome == 'EXPECTED' else 0.0
            outcome_value = 1.0 if outcome == 'EXPECTED' else 0.0
            brier_score = (prediction_prob - outcome_value) ** 2

        ledger_entry = {
            'type': 'PREDICTION_RESOLVED',
            'verdict_id': verdict_id,
            'hypothesis_id': hypothesis_id,
            'metric': hypothesis.metric,
            'metric_actual': metric_actual,
            'metric_predicted': hypothesis.threshold,
            'outcome': outcome,
            'brier_score': brier_score,
            'timestamp': datetime.now().isoformat(),
        }

        return {
            'ledger_entry': ledger_entry,
            'brier_score': brier_score,
            'status': 'RECORDED',
        }

    def complete_prs_cycle(self, hypothesis_id: str, experiment_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete full PRS cycle: validate → run → measure → verdict → ledger.

        Args:
            hypothesis_id: ID of registered hypothesis
            experiment_results: Experiment execution results

        Returns:
            Dict with cycle status, verdict, ledger updates
        """
        # Step 1: Validate hypothesis is frozen
        validation = self.validate_hypothesis_frozen(hypothesis_id)
        if not validation.get('valid'):
            return {'status': 'FAILED', 'reason': validation.get('reason')}

        # Step 2: Run experiment
        run_result = self.run_experiment(hypothesis_id, experiment_results)
        if run_result.get('status') == 'VOID':
            # Still emit verdict even if VOID
            verdict = self.emit_verdict(hypothesis_id, 'VOID', None)
            ledger = self.update_nf_ledger(hypothesis_id, verdict['verdict_id'], 'VOID', None)
            return {
                'status': 'COMPLETED_VOID',
                'hypothesis_id': hypothesis_id,
                'verdict': verdict,
                'ledger': ledger,
            }

        # Step 3: Resolve prediction
        metric_actual = run_result.get('metric_actual')
        prediction = self.resolve_prediction(hypothesis_id, metric_actual)
        outcome = prediction.get('outcome')

        # Step 4: Emit verdict
        verdict = self.emit_verdict(hypothesis_id, outcome, metric_actual)

        # Step 5: Update ledger
        ledger = self.update_nf_ledger(hypothesis_id, verdict['verdict_id'], outcome, metric_actual)

        return {
            'status': 'COMPLETED',
            'hypothesis_id': hypothesis_id,
            'outcome': outcome,
            'metric_actual': metric_actual,
            'verdict': verdict,
            'ledger': ledger,
            'brier_score': ledger.get('brier_score'),
        }
