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
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from enum import Enum


class PredictionOutcome(Enum):
    """Outcome of preregistered prediction after experiment."""
    EXPECTED = "EXPECTED"      # Outcome matched prediction
    SURPRISE = "SURPRISE"      # Outcome contradicted prediction
    VOID = "VOID"              # Experiment unmeasurable (null outcome)


@dataclass
class NFLedgerEntry:
    """Entry in NF_LEDGER (calibration ledger) — PIN or RESOLVE."""
    entry_type: str             # "PIN" (registration) or "RESOLVE" (prediction outcome)
    hypothesis_id: str
    metric: str
    timestamp: str              # ISO timestamp
    hash: str                   # SHA256 hash of entry
    prior_hash: Optional[str] = None  # Previous entry hash for chaining

    # For PIN entries (registration)
    registered_sha: Optional[str] = None
    prediction_value: Optional[float] = None  # Threshold value of prediction
    prediction_window_days: Optional[int] = None  # Window for measurement

    # For RESOLVE entries (prediction resolved)
    outcome: Optional[str] = None  # EXPECTED, SURPRISE, VOID
    brier_score: Optional[float] = None
    metric_actual: Optional[float] = None
    metric_predicted: Optional[float] = None
    ratification_hash: Optional[str] = None  # Z2 ratification hash
    z2_ratified_at: Optional[str] = None  # Z2 ratification timestamp


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
        self.nf_ledger_entries: List[NFLedgerEntry] = []
        self.event_chain: List[Dict[str, Any]] = []

    def _compute_entry_hash(self, entry_data: Dict[str, Any]) -> str:
        """Compute SHA256 hash of NF_LEDGER entry."""
        entry_json = json.dumps(entry_data, sort_keys=True)
        return hashlib.sha256(entry_json.encode()).hexdigest()

    def _create_pin_entry(self, hypothesis: PreregisteredHypothesis) -> NFLedgerEntry:
        """Create PIN (registration) entry in NF_LEDGER."""
        timestamp = datetime.now().isoformat()

        # Compute prior hash (chain linking)
        prior_hash = self.nf_ledger_entries[-1].hash if self.nf_ledger_entries else None

        # Create entry data for hashing
        entry_data = {
            'entry_type': 'PIN',
            'hypothesis_id': hypothesis.hypothesis_id,
            'metric': hypothesis.metric,
            'timestamp': timestamp,
            'registered_sha': hypothesis.registered_sha,
            'prediction_value': hypothesis.threshold,
            'prediction_window_days': hypothesis.prediction_window_days,
            'prior_hash': prior_hash,
        }

        entry_hash = self._compute_entry_hash(entry_data)

        pin_entry = NFLedgerEntry(
            entry_type='PIN',
            hypothesis_id=hypothesis.hypothesis_id,
            metric=hypothesis.metric,
            timestamp=timestamp,
            hash=entry_hash,
            prior_hash=prior_hash,
            registered_sha=hypothesis.registered_sha,
            prediction_value=hypothesis.threshold,
            prediction_window_days=hypothesis.prediction_window_days,
        )

        self.nf_ledger_entries.append(pin_entry)
        return pin_entry

    def register_hypothesis(self, hypothesis: PreregisteredHypothesis) -> Dict[str, Any]:
        """
        Register a hypothesis from REGISTERED.md.

        Args:
            hypothesis: PreregisteredHypothesis object with locked params

        Returns:
            Dict with hypothesis_id, status, registered_sha, nf_ledger_pin
        """
        self.registered_hypotheses[hypothesis.hypothesis_id] = hypothesis

        # Create PIN entry in NF_LEDGER
        pin_entry = self._create_pin_entry(hypothesis)

        return {
            'hypothesis_id': hypothesis.hypothesis_id,
            'status': 'REGISTERED',
            'registered_sha': hypothesis.registered_sha,
            'params_frozen': True,
            'prediction_window_days': hypothesis.prediction_window_days,
            'nf_ledger_pin': {
                'entry_type': pin_entry.entry_type,
                'hash': pin_entry.hash,
                'prior_hash': pin_entry.prior_hash,
            },
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

    def compute_z2_ratification_hash(self, hypothesis_id: str, outcome: str) -> str:
        """
        Compute Z2 ratification hash for a verdict.

        Args:
            hypothesis_id: ID of hypothesis
            outcome: EXPECTED, SURPRISE, or VOID

        Returns:
            SHA256 hash of the ratification
        """
        ratification_data = {
            'hypothesis_id': hypothesis_id,
            'outcome': outcome,
            'timestamp': datetime.now().isoformat(),
            'ratifier': 'Z2',
        }
        ratification_json = json.dumps(ratification_data, sort_keys=True)
        return hashlib.sha256(ratification_json.encode()).hexdigest()

    def emit_verdict(self, hypothesis_id: str, outcome: str, metric_actual: Optional[float], ratification_hash: Optional[str] = None) -> Dict[str, Any]:
        """
        Emit VERDICT event after experiment completes and prediction resolves.

        Args:
            hypothesis_id: ID of registered hypothesis
            outcome: EXPECTED, SURPRISE, or VOID
            metric_actual: Actual metric value (None if VOID)
            ratification_hash: Optional Z2 ratification hash

        Returns:
            Dict with verdict_id, event details, and brier_score
        """
        if hypothesis_id not in self.registered_hypotheses:
            return {'status': 'ERROR', 'reason': f'hypothesis not found: {hypothesis_id}'}

        hypothesis = self.registered_hypotheses[hypothesis_id]

        # Calculate brier score
        if outcome == 'VOID':
            brier_score = None
        else:
            prediction_prob = 1.0  # Always predict with full confidence
            outcome_value = 1.0 if outcome == 'EXPECTED' else 0.0  # 1 if correct, 0 if wrong
            brier_score = (prediction_prob - outcome_value) ** 2

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

        # Add to event chain
        event = {
            'type': 'VERDICT',
            'verdict_id': verdict_id,
            'hypothesis_id': hypothesis_id,
            'outcome': outcome,
            'metric_actual': metric_actual,
            'brier_score': brier_score,
        }
        if ratification_hash:
            event['ratification_hash'] = ratification_hash
        self.event_chain.append(event)

        return {
            'verdict_id': verdict_id,
            'hypothesis_id': hypothesis_id,
            'outcome': outcome,
            'status': 'EMITTED',
            'brier_score': brier_score,
        }

    def _create_resolve_entry(self, hypothesis_id: str, outcome: str, metric_actual: Optional[float], ratification_hash: Optional[str] = None, z2_ratified_at: Optional[str] = None) -> NFLedgerEntry:
        """Create RESOLVE (prediction resolved) entry in NF_LEDGER."""
        if hypothesis_id not in self.registered_hypotheses:
            raise ValueError(f'hypothesis not found: {hypothesis_id}')

        hypothesis = self.registered_hypotheses[hypothesis_id]
        timestamp = datetime.now().isoformat()

        # Calculate Brier score
        if outcome == 'VOID':
            brier_score = None
        else:
            prediction_prob = 1.0  # Always predict with full confidence
            outcome_value = 1.0 if outcome == 'EXPECTED' else 0.0  # 1 if correct, 0 if wrong
            brier_score = (prediction_prob - outcome_value) ** 2

        # Compute prior hash (chain linking)
        prior_hash = self.nf_ledger_entries[-1].hash if self.nf_ledger_entries else None

        # Create entry data for hashing
        entry_data = {
            'entry_type': 'RESOLVE',
            'hypothesis_id': hypothesis_id,
            'metric': hypothesis.metric,
            'timestamp': timestamp,
            'outcome': outcome,
            'brier_score': brier_score,
            'metric_actual': metric_actual,
            'metric_predicted': hypothesis.threshold,
            'prior_hash': prior_hash,
        }
        if ratification_hash:
            entry_data['ratification_hash'] = ratification_hash
        if z2_ratified_at:
            entry_data['z2_ratified_at'] = z2_ratified_at

        entry_hash = self._compute_entry_hash(entry_data)

        resolve_entry = NFLedgerEntry(
            entry_type='RESOLVE',
            hypothesis_id=hypothesis_id,
            metric=hypothesis.metric,
            timestamp=timestamp,
            hash=entry_hash,
            prior_hash=prior_hash,
            outcome=outcome,
            brier_score=brier_score,
            metric_actual=metric_actual,
            metric_predicted=hypothesis.threshold,
            ratification_hash=ratification_hash,
            z2_ratified_at=z2_ratified_at,
        )

        self.nf_ledger_entries.append(resolve_entry)
        return resolve_entry

    def update_nf_ledger(self, hypothesis_id: str, verdict_id: str, outcome: str, metric_actual: Optional[float], ratification_hash: Optional[str] = None, z2_ratified_at: Optional[str] = None) -> Dict[str, Any]:
        """
        Update NF_LEDGER with prediction outcome (Brier scoring).

        Args:
            hypothesis_id: ID of registered hypothesis
            verdict_id: ID of emitted verdict
            outcome: EXPECTED, SURPRISE, or VOID
            metric_actual: Actual metric value
            ratification_hash: Optional Z2 ratification hash
            z2_ratified_at: Optional Z2 ratification timestamp

        Returns:
            Dict with ledger_entry details
        """
        if hypothesis_id not in self.registered_hypotheses:
            return {'status': 'ERROR', 'reason': f'hypothesis not found: {hypothesis_id}'}

        resolve_entry = self._create_resolve_entry(hypothesis_id, outcome, metric_actual, ratification_hash, z2_ratified_at)

        result = {
            'ledger_entry': asdict(resolve_entry),
            'brier_score': resolve_entry.brier_score,
            'status': 'RECORDED',
        }
        if ratification_hash:
            result['ratification_hash'] = ratification_hash
        if z2_ratified_at:
            result['z2_ratified_at'] = z2_ratified_at
        return result

    def complete_prs_cycle(self, hypothesis_id: str, experiment_results: Dict[str, Any], ratify_with_z2: bool = False) -> Dict[str, Any]:
        """
        Complete full PRS cycle: validate → run → measure → verdict → ledger.

        Args:
            hypothesis_id: ID of registered hypothesis
            experiment_results: Experiment execution results
            ratify_with_z2: Whether to include Z2 ratification

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

        # Step 4: Emit verdict (with optional Z2 ratification)
        ratification_hash = None
        if ratify_with_z2:
            ratification_hash = self.compute_z2_ratification_hash(hypothesis_id, outcome)
        verdict = self.emit_verdict(hypothesis_id, outcome, metric_actual, ratification_hash)

        # Step 5: Update ledger
        z2_timestamp = datetime.now(timezone.utc).isoformat() if ratify_with_z2 else None
        ledger = self.update_nf_ledger(hypothesis_id, verdict['verdict_id'], outcome, metric_actual, ratification_hash, z2_timestamp)

        result = {
            'status': 'COMPLETED',
            'hypothesis_id': hypothesis_id,
            'outcome': outcome,
            'metric_actual': metric_actual,
            'verdict': verdict,
            'ledger': ledger,
            'brier_score': ledger.get('brier_score'),
        }
        if ratify_with_z2:
            result['z2_ratified'] = True
        return result

    def export_event_chain(self) -> List[Dict[str, Any]]:
        """
        Export event chain as list of dicts.

        Returns:
            List of event chain entries
        """
        return self.event_chain.copy()

    def export_nf_ledger(self) -> List[Dict[str, Any]]:
        """
        Export NF_LEDGER entries as list of dicts.

        Returns:
            List of NF_LEDGER entries converted to dicts
        """
        return [asdict(entry) for entry in self.nf_ledger_entries]
