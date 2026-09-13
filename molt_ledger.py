"""
molt_ledger.py — Operational Molt Ledger Schema and Events

Implements molt_events.jsonl: append-only ledger of all molt decisions and outcomes.
Each entry is hash-chained; the ledger chains into the event stream (EV).

Molt cycle (from molt_cycle.py):
1. READ: live-fetch REGISTERED.md, read NF, EV, Q, ST
2. PROPOSE: emit MOLT_CANDIDATE for each constant needing re-evaluation
3. RATIFY: Z2 approves candidate (hash)
4. APPLY: write constant with molt_id
5. MEASURE: at window close, resolve prediction into NF
6. KEEP/REVERT: prediction held → KEEP; falsifier tripped → REVERT

Brier tracking: score predictions and track per-constant learning curve.
Revert tracking: two reverts → constant frozen (Z2 Tier 2 override required to reopen).

Anti-cascade rules enforced in molt_cycle.py:
1. One open molt per constant
2. No self-reference in windows
3. K=3 open molts system-wide
4. Freeze after 2 reverts
5. Ranking by Priority Queue score
"""

import json
import hashlib
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class MoltEventType(Enum):
    """Types of molt events."""
    MOLT_CANDIDATE = "MOLT_CANDIDATE"      # Proposed change
    RATIFY = "RATIFY"                      # Z2 approved
    APPLY = "APPLY"                        # Change written
    MEASURE = "MEASURE"                    # Prediction resolved
    KEEP = "KEEP"                          # Prediction held
    REVERT = "REVERT"                      # Falsifier tripped


class MoltOutcome(Enum):
    """Outcome of a molt."""
    KEEP = "KEEP"              # Prediction held; good
    REVERT = "REVERT"          # Falsifier tripped; bad
    INCONCLUSIVE = "INCONCLUSIVE"  # Measurement window not closed


@dataclass
class MoltCandidate:
    """Proposed constant change (before ratification)."""
    molt_candidate_id: str
    constant: str
    current_value: Any
    proposed_value: Any
    prediction: str            # "metric X will be > Y"
    metric: str
    predicted_value: float     # Expected metric value
    falsifier: str             # "would prove it wrong" sentence
    window_days: int           # Measurement window
    revert_rule: str           # e.g., "falsify on metric < 0.50"
    proposed_at: str           # ISO timestamp
    priority_score: int        # From Priority Queue


@dataclass
class MoltRatify:
    """Z2 ratification of molt candidate."""
    molt_id: str               # e.g., "MOLT-20260910-001"
    molt_candidate_id: str     # Link to candidate
    z2_signature: str          # SHA256 hash signed by Z2
    decision: str              # ACCEPT, EDIT, REJECT
    ratified_at: str           # ISO timestamp


@dataclass
class MoltApply:
    """Application of ratified molt."""
    molt_id: str
    constant: str
    prior_value: Any
    new_value: Any
    prior_molt_id: str         # Previous molt_id that set this
    applied_at: str
    window_close_at: str       # When prediction is measured


@dataclass
class MoltMeasurement:
    """Measurement of molt prediction at window close."""
    molt_id: str
    constant: str
    metric_actual: float
    metric_predicted: float
    brier_score: float         # (predicted - actual)^2
    outcome: str               # KEEP, REVERT, INCONCLUSIVE
    measured_at: str


@dataclass
class MoltEvent:
    """Append-only ledger entry for molt."""
    event_id: str
    molt_id: str
    event_type: str            # MOLT_CANDIDATE, RATIFY, APPLY, MEASURE, KEEP, REVERT
    constant: str
    prior_hash: str            # Hash of previous event (chain)
    hash: str                  # Hash of this event
    timestamp: str
    data: Dict[str, Any]       # Event-specific data


class MoltLedger:
    """Operational Molt Ledger — append-only event store."""

    def __init__(self):
        self.entries = []              # List of MoltEvent
        self.constants_molt_history = {}  # constant → list of molt_ids
        self.revert_count = {}         # constant → count of reverts

    def append_event(self, event: MoltEvent) -> Dict[str, Any]:
        """
        Append event to ledger (append-only).

        Args:
            event: MoltEvent to append

        Returns:
            Dict with event_id, hash, status
        """
        self.entries.append(event)

        # Track reverts per constant
        if event.event_type == MoltEventType.REVERT.value:
            self.revert_count[event.constant] = self.revert_count.get(event.constant, 0) + 1

        # Track molt history per constant
        if event.molt_id not in self.constants_molt_history.get(event.constant, []):
            if event.constant not in self.constants_molt_history:
                self.constants_molt_history[event.constant] = []
            self.constants_molt_history[event.constant].append(event.molt_id)

        return {
            'event_id': event.event_id,
            'molt_id': event.molt_id,
            'hash': event.hash,
            'status': 'APPENDED',
        }

    def create_molt_candidate_event(self, candidate: MoltCandidate) -> MoltEvent:
        """
        Create MOLT_CANDIDATE event.

        Args:
            candidate: MoltCandidate proposal

        Returns:
            MoltEvent ready to append
        """
        prior_hash = self.entries[-1].hash if self.entries else "genesis"

        event_id = f'EV-{datetime.now().isoformat()[:10]}-{len(self.entries):05d}'

        event_data = {
            'candidate_id': candidate.molt_candidate_id,
            'constant': candidate.constant,
            'proposed_value': candidate.proposed_value,
            'prediction': candidate.prediction,
            'falsifier': candidate.falsifier,
            'window_days': candidate.window_days,
            'priority_score': candidate.priority_score,
        }

        event_hash = hashlib.sha256(
            json.dumps({'candidate': event_data, 'timestamp': datetime.now().isoformat()}, sort_keys=True).encode()
        ).hexdigest()

        return MoltEvent(
            event_id=event_id,
            molt_id=candidate.molt_candidate_id,
            event_type=MoltEventType.MOLT_CANDIDATE.value,
            constant=candidate.constant,
            prior_hash=prior_hash,
            hash=event_hash,
            timestamp=datetime.now().isoformat(),
            data=event_data,
        )

    def create_ratify_event(self, molt_id: str, z2_signature: str, decision: str) -> MoltEvent:
        """
        Create RATIFY event (Z2 approval).

        Args:
            molt_id: ID of molt being ratified
            z2_signature: Z2's hash signature
            decision: ACCEPT, EDIT, or REJECT

        Returns:
            MoltEvent ready to append
        """
        prior_hash = self.entries[-1].hash if self.entries else "genesis"

        event_id = f'EV-{datetime.now().isoformat()[:10]}-{len(self.entries):05d}'

        event_data = {
            'molt_id': molt_id,
            'z2_signature': z2_signature,
            'decision': decision,
        }

        event_hash = hashlib.sha256(
            json.dumps({'ratify': event_data, 'timestamp': datetime.now().isoformat()}, sort_keys=True).encode()
        ).hexdigest()

        return MoltEvent(
            event_id=event_id,
            molt_id=molt_id,
            event_type=MoltEventType.RATIFY.value,
            constant="",  # Ratification is not specific to one constant
            prior_hash=prior_hash,
            hash=event_hash,
            timestamp=datetime.now().isoformat(),
            data=event_data,
        )

    def create_apply_event(self, molt_id: str, constant: str, new_value: Any, prior_molt_id: str) -> MoltEvent:
        """
        Create APPLY event (ratified molt written).

        Args:
            molt_id: ID of molt
            constant: Constant being changed
            new_value: New value being applied
            prior_molt_id: Previous molt_id for this constant

        Returns:
            MoltEvent ready to append
        """
        prior_hash = self.entries[-1].hash if self.entries else "genesis"

        event_id = f'EV-{datetime.now().isoformat()[:10]}-{len(self.entries):05d}'

        window_close_at = (datetime.now() + datetime.timedelta(days=30)).isoformat()  # Stub: 30-day window

        event_data = {
            'molt_id': molt_id,
            'constant': constant,
            'new_value': new_value,
            'prior_molt_id': prior_molt_id,
            'window_close_at': window_close_at,
        }

        event_hash = hashlib.sha256(
            json.dumps({'apply': event_data, 'timestamp': datetime.now().isoformat()}, sort_keys=True).encode()
        ).hexdigest()

        return MoltEvent(
            event_id=event_id,
            molt_id=molt_id,
            event_type=MoltEventType.APPLY.value,
            constant=constant,
            prior_hash=prior_hash,
            hash=event_hash,
            timestamp=datetime.now().isoformat(),
            data=event_data,
        )

    def create_measurement_event(self, molt_id: str, constant: str, metric_actual: float,
                                 metric_predicted: float) -> MoltEvent:
        """
        Create MEASURE event (prediction resolved at window close).

        Args:
            molt_id: ID of molt
            constant: Constant being measured
            metric_actual: Actual metric value
            metric_predicted: Predicted value

        Returns:
            MoltEvent ready to append
        """
        prior_hash = self.entries[-1].hash if self.entries else "genesis"

        event_id = f'EV-{datetime.now().isoformat()[:10]}-{len(self.entries):05d}'

        # Calculate Brier score
        brier_score = (metric_predicted - metric_actual) ** 2

        event_data = {
            'molt_id': molt_id,
            'constant': constant,
            'metric_actual': metric_actual,
            'metric_predicted': metric_predicted,
            'brier_score': brier_score,
        }

        event_hash = hashlib.sha256(
            json.dumps({'measurement': event_data, 'timestamp': datetime.now().isoformat()}, sort_keys=True).encode()
        ).hexdigest()

        return MoltEvent(
            event_id=event_id,
            molt_id=molt_id,
            event_type=MoltEventType.MEASURE.value,
            constant=constant,
            prior_hash=prior_hash,
            hash=event_hash,
            timestamp=datetime.now().isoformat(),
            data=event_data,
        )

    def create_outcome_event(self, molt_id: str, constant: str, outcome: str, brier_score: float) -> MoltEvent:
        """
        Create KEEP or REVERT event (final outcome).

        Args:
            molt_id: ID of molt
            constant: Constant affected
            outcome: KEEP or REVERT
            brier_score: Brier score from measurement

        Returns:
            MoltEvent ready to append
        """
        prior_hash = self.entries[-1].hash if self.entries else "genesis"

        event_id = f'EV-{datetime.now().isoformat()[:10]}-{len(self.entries):05d}'

        event_data = {
            'molt_id': molt_id,
            'constant': constant,
            'outcome': outcome,
            'brier_score': brier_score,
        }

        event_hash = hashlib.sha256(
            json.dumps({'outcome': event_data, 'timestamp': datetime.now().isoformat()}, sort_keys=True).encode()
        ).hexdigest()

        event_type = MoltEventType.KEEP.value if outcome == "KEEP" else MoltEventType.REVERT.value

        return MoltEvent(
            event_id=event_id,
            molt_id=molt_id,
            event_type=event_type,
            constant=constant,
            prior_hash=prior_hash,
            hash=event_hash,
            timestamp=datetime.now().isoformat(),
            data=event_data,
        )

    def is_frozen(self, constant: str) -> bool:
        """
        Check if constant is frozen (two reverts).

        Args:
            constant: Constant to check

        Returns:
            True if frozen, False otherwise
        """
        return self.revert_count.get(constant, 0) >= 2

    def get_revert_count(self, constant: str) -> int:
        """Get revert count for constant."""
        return self.revert_count.get(constant, 0)

    def get_molt_history(self, constant: str) -> List[str]:
        """Get list of molt_ids that touched this constant."""
        return self.constants_molt_history.get(constant, [])

    def report_brier_trend(self) -> Dict[str, Any]:
        """
        Report Brier score trend per constant and predictor.

        Returns:
            Dict with brier trends
        """
        constant_brier = {}

        for entry in self.entries:
            if entry.event_type == MoltEventType.MEASURE.value:
                constant = entry.constant
                brier = entry.data.get('brier_score', 0)

                if constant not in constant_brier:
                    constant_brier[constant] = []

                constant_brier[constant].append({
                    'molt_id': entry.molt_id,
                    'brier_score': brier,
                    'timestamp': entry.timestamp,
                })

        return {
            'constants': len(constant_brier),
            'per_constant': constant_brier,
        }

    def report_revert_status(self) -> Dict[str, Any]:
        """Report revert status and frozen constants."""
        frozen = [c for c, count in self.revert_count.items() if count >= 2]
        at_risk = [c for c, count in self.revert_count.items() if count == 1]

        return {
            'frozen_count': len(frozen),
            'at_risk_count': len(at_risk),
            'frozen': frozen,
            'at_risk': at_risk,
            'revert_counts': self.revert_count,
        }

    def to_jsonl(self) -> str:
        """Serialize ledger to JSONL format."""
        lines = []

        for entry in self.entries:
            lines.append(json.dumps(asdict(entry)))

        return "\n".join(lines)

    def write_ledger(self, filepath: str) -> Dict[str, Any]:
        """Write ledger to JSONL file."""
        with open(filepath, 'w') as f:
            f.write(self.to_jsonl())

        return {
            'filepath': filepath,
            'entries': len(self.entries),
            'status': 'WRITTEN',
        }

    def validate_chain(self) -> Dict[str, Any]:
        """Validate hash chain integrity."""
        errors = []

        for i, entry in enumerate(self.entries):
            if i == 0:
                if entry.prior_hash != "genesis":
                    errors.append(f'Entry 0: prior_hash should be "genesis", got {entry.prior_hash}')
            else:
                expected_prior = self.entries[i - 1].hash
                if entry.prior_hash != expected_prior:
                    errors.append(f'Entry {i}: prior_hash mismatch (expected {expected_prior}, got {entry.prior_hash})')

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'chain_length': len(self.entries),
        }
