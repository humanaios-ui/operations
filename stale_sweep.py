"""
stale_sweep.py — Stale Constant Detection with Decay (v0.1)

Identifies constants that haven't been read/measured recently.
Staleness = (now - last_read) / half_life.
When staleness ≥ 1.0, constant is STALE and either re-read or retired.

Pattern:
1. READ: Load all constants with last_read timestamps and half_life values
2. COMPUTE: For each constant, calculate staleness = (now - last_read) / half_life
3. IDENTIFY: Emit STALE gap to Priority Queue for staleness >= 1.0
4. DECIDE: Z2 re-reads (reset last_read) or retires (no more molts)
5. RETIRE: Mark constant as retired; no new molt candidates generated

Runs nightly or on session open (scheduled job).
Mechanical calculation, no opinion.
"""

import json
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta
from enum import Enum


class ConstantStatus(Enum):
    """Status of a constant."""
    ACTIVE = "ACTIVE"                   # Normal operation
    STALE = "STALE"                     # Not read in >half_life
    RETIRED = "RETIRED"                 # No longer used; no new molts


@dataclass
class Constant:
    """A system constant that can decay (become stale)."""
    constant_id: str                    # e.g., "CONST-IMPACT-DIAL-001"
    constant_name: str                  # Human-readable name
    constant_type: str                  # e.g., "BEHAVIOR_DIAL", "INTEGRITY_MODE"
    half_life_days: float               # Days until staleness = 1.0
    last_read_at: str                   # ISO timestamp of last read/measurement
    status: ConstantStatus = ConstantStatus.ACTIVE
    molt_id: Optional[str] = None       # Molt that last modified this constant
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    retired_at: Optional[str] = None    # When constant was retired (if retired)


@dataclass
class StalenessMetric:
    """Staleness measurement for a single constant."""
    constant_id: str
    staleness: float                    # (now - last_read) / half_life
    days_since_read: float              # Absolute days
    status: ConstantStatus              # ACTIVE, STALE, or RETIRED
    is_stale: bool                      # staleness >= 1.0


@dataclass
class StaleGapCallout:
    """Gap callout emitted for a stale constant."""
    callout_id: str
    constant_id: str
    constant_name: str
    staleness: float
    days_since_read: float
    recommendation: str                 # "re_read" or "retire"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class StaleSweep:
    """Detects and reports stale constants."""

    def __init__(self, constants_config_path: str = "constants_config.json"):
        """
        Initialize StaleSweep.

        Args:
            constants_config_path: Path to constants configuration JSON
        """
        self.constants_config_path = constants_config_path
        self.constants: Dict[str, Constant] = {}
        self.staleness_history: List[StalenessMetric] = []
        self.callouts: List[StaleGapCallout] = []
        self._load_constants()

    def _load_constants(self):
        """Load constant definitions from constants_config.json."""
        try:
            with open(self.constants_config_path, 'r') as f:
                config = json.load(f)

            for const_def in config.get('constants', []):
                constant = Constant(
                    constant_id=const_def.get('constant_id'),
                    constant_name=const_def.get('name', ''),
                    constant_type=const_def.get('type', 'UNKNOWN'),
                    half_life_days=const_def.get('half_life_days', 30),
                    last_read_at=const_def.get('last_read_at', datetime.now(timezone.utc).isoformat()),
                    status=ConstantStatus[const_def.get('status', 'ACTIVE')],
                    molt_id=const_def.get('molt_id'),
                    retired_at=const_def.get('retired_at')
                )
                self.constants[constant.constant_id] = constant
        except FileNotFoundError:
            self._create_default_constants()

    def _create_default_constants(self):
        """Create default constants for testing."""
        default_constants = [
            Constant(
                constant_id='CONST-IMPACT-DIAL-001',
                constant_name='Impact dial for blocker removal',
                constant_type='BEHAVIOR_DIAL',
                half_life_days=30,
                last_read_at=(datetime.now(timezone.utc) - timedelta(days=15)).isoformat(),
                molt_id='M-20260901-001'
            ),
            Constant(
                constant_id='CONST-TOKEN-BUDGET-001',
                constant_name='Token budget per session',
                constant_type='GATE_PARAM',
                half_life_days=14,
                last_read_at=(datetime.now(timezone.utc) - timedelta(days=7)).isoformat(),
                molt_id='M-20260905-001'
            ),
            Constant(
                constant_id='CONST-CATCH-THRESHOLD-001',
                constant_name='Adversarial catch-rate threshold',
                constant_type='GATE_PARAM',
                half_life_days=60,
                last_read_at=(datetime.now(timezone.utc) - timedelta(days=90)).isoformat(),
                molt_id='M-20260815-001'
            ),
        ]
        for const in default_constants:
            self.constants[const.constant_id] = const

    def compute_staleness(self, constant_id: str) -> StalenessMetric:
        """
        Compute staleness for a single constant.

        Args:
            constant_id: ID of constant to measure

        Returns:
            StalenessMetric with staleness value and status
        """
        if constant_id not in self.constants:
            return StalenessMetric(
                constant_id=constant_id,
                staleness=float('inf'),
                days_since_read=float('inf'),
                status=ConstantStatus.RETIRED,
                is_stale=True
            )

        const = self.constants[constant_id]

        if const.status == ConstantStatus.RETIRED:
            return StalenessMetric(
                constant_id=constant_id,
                staleness=float('inf'),
                days_since_read=float('inf'),
                status=ConstantStatus.RETIRED,
                is_stale=True
            )

        # Calculate days since last read
        last_read = datetime.fromisoformat(const.last_read_at.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        days_since_read = (now - last_read).total_seconds() / (24 * 3600)

        # Calculate staleness ratio
        staleness = days_since_read / const.half_life_days

        # Determine status
        is_stale = staleness >= 1.0
        status = ConstantStatus.STALE if is_stale else ConstantStatus.ACTIVE

        metric = StalenessMetric(
            constant_id=constant_id,
            staleness=staleness,
            days_since_read=days_since_read,
            status=status,
            is_stale=is_stale
        )

        self.staleness_history.append(metric)
        return metric

    def sweep(self) -> List[StaleGapCallout]:
        """
        Run full staleness sweep across all constants.

        Returns:
            List of StaleGapCallout for stale constants
        """
        callouts = []

        for constant_id in self.constants:
            metric = self.compute_staleness(constant_id)

            if metric.is_stale:
                const = self.constants[constant_id]

                # Determine recommendation based on staleness severity
                if metric.staleness >= 2.0:
                    recommendation = "retire"
                    reason_detail = "Very stale (>2x half-life)"
                else:
                    recommendation = "re_read"
                    reason_detail = "Stale (≥1x half-life)"

                callout = StaleGapCallout(
                    callout_id=f"STALE-{constant_id}-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
                    constant_id=constant_id,
                    constant_name=const.constant_name,
                    staleness=metric.staleness,
                    days_since_read=metric.days_since_read,
                    recommendation=recommendation
                )
                callouts.append(callout)
                self.callouts.append(callout)

        return callouts

    def re_read_constant(self, constant_id: str, read_timestamp: Optional[str] = None) -> bool:
        """
        Mark constant as re-read, resetting its staleness.

        Args:
            constant_id: ID of constant to re-read
            read_timestamp: Timestamp of re-read (default: now)

        Returns:
            True if successful
        """
        if constant_id not in self.constants:
            return False

        const = self.constants[constant_id]
        if const.status == ConstantStatus.RETIRED:
            return False

        const.last_read_at = read_timestamp or datetime.now(timezone.utc).isoformat()
        const.status = ConstantStatus.ACTIVE

        return True

    def retire_constant(self, constant_id: str, retire_timestamp: Optional[str] = None) -> bool:
        """
        Retire a constant: mark as retired, no new molts generated.

        Args:
            constant_id: ID of constant to retire
            retire_timestamp: Timestamp of retirement (default: now)

        Returns:
            True if successful
        """
        if constant_id not in self.constants:
            return False

        const = self.constants[constant_id]
        const.status = ConstantStatus.RETIRED
        const.retired_at = retire_timestamp or datetime.now(timezone.utc).isoformat()

        return True

    def get_stale_constants(self) -> List[Constant]:
        """Get list of currently stale constants."""
        stale = []
        for constant_id in self.constants:
            metric = self.compute_staleness(constant_id)
            if metric.is_stale:
                stale.append(self.constants[constant_id])
        return stale

    def get_active_constants(self) -> List[Constant]:
        """Get list of currently active (non-stale) constants."""
        active = []
        for constant_id in self.constants:
            const = self.constants[constant_id]
            if const.status == ConstantStatus.ACTIVE:
                metric = self.compute_staleness(constant_id)
                if not metric.is_stale:
                    active.append(const)
        return active

    def export_staleness_report(self, filepath: str = "staleness_report.json"):
        """Export staleness report for all constants."""
        report = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'total_constants': len(self.constants),
            'active_constants': len(self.get_active_constants()),
            'stale_constants': len(self.get_stale_constants()),
            'constants': {}
        }

        for constant_id, const in self.constants.items():
            metric = self.compute_staleness(constant_id)
            report['constants'][constant_id] = {
                'name': const.constant_name,
                'type': const.constant_type,
                'status': const.status.value,
                'staleness': metric.staleness,
                'days_since_read': metric.days_since_read,
                'half_life_days': const.half_life_days,
                'is_stale': metric.is_stale
            }

        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)

    def export_callouts(self, filepath: str = "stale_callouts.jsonl"):
        """Export stale gap callouts to JSONL file."""
        with open(filepath, 'w') as f:
            for callout in self.callouts:
                f.write(json.dumps(asdict(callout), default=str) + '\n')
