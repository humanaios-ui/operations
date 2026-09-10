"""
stale_sweep.py — Stale Constant Sweep

Detects constants that haven't been re-evaluated within their half-life window.
Emits STALE gaps to Priority Queue for Z2 to decide: re-read (neue molt) or retire.

Pattern:
1. READ: Fetch constants from CONST registry with molt_id and last_updated
2. MEASURE: Calculate time_since_read vs half_life for each constant
3. DETECT: Identify stale constants (time_since_read > half_life)
4. EMIT: STALE gap to Priority Queue per stale constant
5. REPORT: Summary of stale count, Z2 pending decisions

Half-life is a constant itself (decay math, not opinion). Typical values:
- behavior_spec.json: 30 days
- integrity_modes.json: 60 days
- priority_weights.json: 14 days
- agent_caps.json: 21 days

Z2 reviews each STALE gap and decides:
- RE_READ: Propose molt to re-evaluate constant
- RETIRE: Retire constant from use
- EXTEND: Extend half-life (rare; requires molt)

No auto-retire; Z2 must explicitly authorize.
"""

import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum


class StaleStatus(Enum):
    """Status of a constant's staleness."""
    FRESH = "FRESH"            # time_since_read < 50% half_life
    AGING = "AGING"            # 50% <= time_since_read < half_life
    STALE = "STALE"            # time_since_read >= half_life
    CRITICAL = "CRITICAL"      # time_since_read > 2 * half_life


class Z2Decision(Enum):
    """Z2 decision on stale constant."""
    PENDING = "PENDING"        # Awaiting Z2 review
    RE_READ = "RE_READ"        # Propose molt to re-evaluate
    RETIRE = "RETIRE"          # Retire constant from use
    EXTEND = "EXTEND"          # Extend half-life via molt


@dataclass
class Constant:
    """A system constant with versioning and half-life."""
    name: str                  # e.g., "behavior_spec.json"
    molt_id: str               # ID of molt that last set this constant
    last_updated: str          # ISO timestamp of last molt
    half_life_days: int        # Half-life window in days
    current_value: Dict[str, Any]
    retired: bool = False


@dataclass
class StaleGap:
    """Gap emitted when constant becomes stale."""
    gap_id: str
    constant_name: str
    days_since_update: float
    half_life_days: int
    stale_status: str          # FRESH, AGING, STALE, CRITICAL
    molt_id_at_update: str
    time_to_criticality_days: float
    z2_decision: str = "PENDING"
    decision_explanation: str = ""
    timestamp: str = ""


@dataclass
class StaleEvent:
    """Event emitted when STALE gap is created."""
    event_id: str
    constant_name: str
    stale_status: str
    gap_id: str
    z2_decision_needed: bool
    timestamp: str


class StaleSweep:
    """Stale Constant Sweep — detects and reports aging constants."""

    def __init__(self):
        self.constants = {}          # name → Constant
        self.gaps = []               # List of StaleGap
        self.events = []             # List of StaleEvent
        self.z2_decisions = {}       # gap_id → Z2Decision

    def register_constant(self, constant: Constant) -> Dict[str, Any]:
        """
        Register a constant with half-life tracking.

        Args:
            constant: Constant object with molt_id and last_updated

        Returns:
            Dict with registration status
        """
        self.constants[constant.name] = constant

        return {
            'constant': constant.name,
            'status': 'REGISTERED',
            'half_life_days': constant.half_life_days,
            'molt_id': constant.molt_id,
        }

    def calculate_staleness(self, constant: Constant, now: datetime) -> Dict[str, Any]:
        """
        Calculate staleness of a constant.

        Args:
            constant: Constant to evaluate
            now: Current datetime

        Returns:
            Dict with days_since_update, stale_status, time_to_criticality
        """
        if constant.retired:
            return {
                'stale_status': 'RETIRED',
                'days_since_update': None,
                'time_to_criticality_days': None,
            }

        # Parse last_updated
        last_updated = datetime.fromisoformat(constant.last_updated.replace('Z', '+00:00'))
        days_since_update = (now - last_updated).days

        # Determine stale status
        if days_since_update < constant.half_life_days * 0.5:
            stale_status = StaleStatus.FRESH.value
        elif days_since_update < constant.half_life_days:
            stale_status = StaleStatus.AGING.value
        elif days_since_update < constant.half_life_days * 2:
            stale_status = StaleStatus.STALE.value
        else:
            stale_status = StaleStatus.CRITICAL.value

        # Time to criticality (when 2x half_life is reached)
        criticality_date = last_updated + timedelta(days=constant.half_life_days * 2)
        time_to_criticality = (criticality_date - now).days

        return {
            'stale_status': stale_status,
            'days_since_update': days_since_update,
            'time_to_criticality_days': time_to_criticality,
        }

    def sweep_constants(self, now: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Sweep all constants and detect stale ones.

        Args:
            now: Current datetime (defaults to now)

        Returns:
            Dict with stale count, gaps, events
        """
        if now is None:
            now = datetime.utcnow()

        stale_count = 0
        aging_count = 0
        critical_count = 0
        fresh_count = 0
        new_gaps = []

        for name, constant in self.constants.items():
            staleness = self.calculate_staleness(constant, now)
            status = staleness['stale_status']

            if status == 'RETIRED':
                continue

            # Emit gap if STALE or CRITICAL
            if status in [StaleStatus.STALE.value, StaleStatus.CRITICAL.value]:
                gap_id = f'GAP-STALE-{datetime.now().isoformat()[:10]}-{len(self.gaps):05d}'

                gap = StaleGap(
                    gap_id=gap_id,
                    constant_name=name,
                    days_since_update=staleness['days_since_update'],
                    half_life_days=constant.half_life_days,
                    stale_status=status,
                    molt_id_at_update=constant.molt_id,
                    time_to_criticality_days=staleness['time_to_criticality_days'],
                    timestamp=datetime.now().isoformat(),
                )

                self.gaps.append(gap)
                new_gaps.append(asdict(gap))

                # Emit STALE event
                event_id = f'STA-{datetime.now().isoformat()[:10]}-{len(self.events):05d}'

                event = StaleEvent(
                    event_id=event_id,
                    constant_name=name,
                    stale_status=status,
                    gap_id=gap_id,
                    z2_decision_needed=(status == StaleStatus.CRITICAL.value),
                    timestamp=datetime.now().isoformat(),
                )

                self.events.append(asdict(event))

                if status == StaleStatus.STALE.value:
                    stale_count += 1
                else:
                    critical_count += 1

            elif status == StaleStatus.AGING.value:
                aging_count += 1
            else:
                fresh_count += 1

        return {
            'swept_constants': len(self.constants),
            'fresh': fresh_count,
            'aging': aging_count,
            'stale': stale_count,
            'critical': critical_count,
            'new_gaps': len(new_gaps),
            'gaps': new_gaps,
        }

    def process_z2_decision(self, gap_id: str, decision: str, explanation: str = "") -> Dict[str, Any]:
        """
        Record Z2 decision on stale constant.

        Args:
            gap_id: ID of stale gap
            decision: RE_READ, RETIRE, or EXTEND
            explanation: Z2's reasoning

        Returns:
            Dict with decision status
        """
        # Find the gap
        target_gap = None
        for gap in self.gaps:
            if gap.gap_id == gap_id:
                target_gap = gap
                break

        if not target_gap:
            return {
                'gap_id': gap_id,
                'status': 'NOT_FOUND',
                'error': f'Gap {gap_id} not found',
            }

        # Record decision
        target_gap.z2_decision = decision
        target_gap.decision_explanation = explanation
        self.z2_decisions[gap_id] = decision

        # If RETIRE, mark constant as retired
        if decision == Z2Decision.RETIRE.value:
            if target_gap.constant_name in self.constants:
                self.constants[target_gap.constant_name].retired = True

        return {
            'gap_id': gap_id,
            'constant_name': target_gap.constant_name,
            'decision': decision,
            'status': 'RECORDED',
            'explanation': explanation,
        }

    def get_pending_decisions(self) -> Dict[str, Any]:
        """Report gaps awaiting Z2 decision."""
        pending = [g for g in self.gaps if g.z2_decision == Z2Decision.PENDING.value]

        return {
            'pending_gaps': len(pending),
            'gaps': [asdict(g) for g in pending],
        }

    def get_stale_report(self) -> Dict[str, Any]:
        """Report current staleness status."""
        stale = [g for g in self.gaps if g.stale_status == StaleStatus.STALE.value]
        critical = [g for g in self.gaps if g.stale_status == StaleStatus.CRITICAL.value]
        pending = [g for g in self.gaps if g.z2_decision == Z2Decision.PENDING.value]

        return {
            'stale_constants': len(stale),
            'critical_constants': len(critical),
            'pending_z2_decisions': len(pending),
            'stale': [asdict(g) for g in stale],
            'critical': [asdict(g) for g in critical],
            'pending': [asdict(g) for g in pending],
        }

    def retire_constant(self, constant_name: str) -> Dict[str, Any]:
        """
        Retire a constant from use (after Z2 decision).

        Args:
            constant_name: Name of constant to retire

        Returns:
            Dict with retirement status
        """
        if constant_name not in self.constants:
            return {
                'constant': constant_name,
                'status': 'NOT_FOUND',
                'error': f'Constant {constant_name} not registered',
            }

        self.constants[constant_name].retired = True

        return {
            'constant': constant_name,
            'status': 'RETIRED',
            'timestamp': datetime.now().isoformat(),
        }

    def propose_molt_for_reread(self, constant_name: str) -> Dict[str, Any]:
        """
        Propose a molt to re-evaluate a stale constant.
        This is a signal to MOLT cycle to create a MOLT_CANDIDATE.

        Args:
            constant_name: Name of constant to re-read

        Returns:
            Dict with molt proposal (sent to Priority Queue)
        """
        if constant_name not in self.constants:
            return {
                'constant': constant_name,
                'status': 'NOT_FOUND',
            }

        constant = self.constants[constant_name]

        return {
            'molt_proposal': {
                'constant': constant_name,
                'reason': 'STALE_CONSTANT_RE_READ',
                'prior_molt_id': constant.molt_id,
                'action': 'PROPOSE_RE_EVALUATION',
                'priority': 'HIGH',  # Stale constants get high priority
            },
            'status': 'PROPOSED',
            'target_queue': 'PRIORITY_QUEUE.md',
        }
