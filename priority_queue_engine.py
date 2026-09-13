"""
priority_queue_engine.py — Priority Queue with Score-Based READY Gate

Two scoring modes. The incumbent is the default; the resource mode is inert
until Z2 ratifies it.

  mode="impact"   (INCUMBENT)  score = impact + Σ impact(unblocks)
  mode="resource" (Q-RBE-01)   the same numerator divided by what the row costs
                               at the binding constraint, in two bands:
                                 Band A  cost(constraint) == 0  → rank by score
                                 Band B  cost(constraint)  > 0  → rank by density
                                 unpriced rows are not schedulable at all

Band A before Band B is constraint discipline, not preference: work that does
not touch the bottleneck never competes with work that does. See
docs/RESOURCE_BASED_ECONOMICS.md §7 and RESOURCE_UNITS.yaml.

Only top-score READY rows may begin work. Blocked rows enter queue but cannot
start until their unblock actions are complete. Z2 ratifies impact pins and
score changes via hash.

Pattern:
1. READ: Fetch PRIORITY_QUEUE.md (IC-030), parse all work orders
2. SCORE: Calculate score for each item (base impact + unblock impacts)
3. GATE: Filter READY items; block items with unsolved dependencies
4. RANK: Sort by score; emit READY (start approved)
5. REPORT: Summary of queue state, next READY item

Impacts are constant-like (in behavior_spec.json weights) and are updated
via molt. No auto-prioritization; Z2 approves score changes via hash.

The mode switch is itself governed: `PriorityQueueEngine.from_constants()`
reads constants.json and selects resource mode ONLY when QUEUE_SCORING_MODE
carries a non-null molt_id. Code does not flip its own gate.
"""

import json
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from enum import Enum

# Scoring modes. "impact" is the incumbent and stays the default everywhere.
MODE_IMPACT = "impact"
MODE_RESOURCE = "resource"

# The unit every work order must price itself in under resource mode. Mirrors
# RESOURCE_UNITS.yaml → constraint.unit; kept as a plain string so this module
# has no yaml dependency.
DEFAULT_CONSTRAINT_UNIT = "RAT-min"


class QueueItemStatus(Enum):
    """Status of work order in queue."""
    READY = "READY"            # Can start (score sufficient, no blockers)
    BLOCKED = "BLOCKED"        # Has unresolved blockers
    COMPLETED = "COMPLETED"
    IN_PROGRESS = "IN_PROGRESS"


@dataclass
class QueueItem:
    """Work order in priority queue."""
    molt_id: str
    status: str                # READY, BLOCKED, COMPLETED, IN_PROGRESS
    impact: int                # Base impact (from spec)
    blocks: List[str] = field(default_factory=list)  # Molts this unblocks
    blocked_by: List[str] = field(default_factory=list)  # Molts blocking this
    score: int = 0
    completed_at: Optional[str] = None
    description: str = ""
    # Resource cost vector, e.g. {"RAT-min": 15, "Z1-ktok": 40, "Z3-hr": 2}.
    # Empty means UNPRICED: ignored in impact mode, refused in resource mode.
    cost: Dict[str, float] = field(default_factory=dict)

    def calculate_score(self, all_items: Dict[str, 'QueueItem']) -> int:
        """
        Calculate score: base_impact + Σ impact(unblocks).

        Args:
            all_items: Dict of molt_id → QueueItem (for lookup)

        Returns:
            Calculated score
        """
        unblock_impact = 0

        for unblocked_molt_id in self.blocks:
            if unblocked_molt_id in all_items:
                unblocked_item = all_items[unblocked_molt_id]
                # Only count impact of items that are currently blocked
                if unblocked_item.status == QueueItemStatus.BLOCKED.value:
                    unblock_impact += unblocked_item.impact

        return self.impact + unblock_impact

    def can_start(self) -> bool:
        """Check if item is unblocked and ready."""
        return len(self.blocked_by) == 0 and self.status == QueueItemStatus.READY.value

    # ---------------------------------------------------------------- resource
    def is_priced(self, constraint_unit: str = DEFAULT_CONSTRAINT_UNIT) -> bool:
        """A row is priced when it states its draw on the constraint — including
        an explicit zero. A missing key is 'nobody costed this', which is not the
        same claim as 'this costs nothing'."""
        return constraint_unit in self.cost

    def constraint_cost(self, constraint_unit: str = DEFAULT_CONSTRAINT_UNIT) -> Optional[float]:
        """Draw on the binding constraint, or None if the row is unpriced."""
        if not self.is_priced(constraint_unit):
            return None
        return float(self.cost[constraint_unit])

    def band(self, constraint_unit: str = DEFAULT_CONSTRAINT_UNIT) -> str:
        """A (no constraint draw) · B (draws on the constraint) · UNPRICED."""
        c = self.constraint_cost(constraint_unit)
        if c is None:
            return 'UNPRICED'
        return 'A' if c == 0 else 'B'

    def density(self, all_items: Dict[str, 'QueueItem'],
                constraint_unit: str = DEFAULT_CONSTRAINT_UNIT) -> Optional[float]:
        """Yield per constraint unit: score / cost(constraint).

        None for Band A (no denominator — those rows do not compete for the
        constraint) and for unpriced rows (no denominator can be computed).
        """
        c = self.constraint_cost(constraint_unit)
        if not c:          # None or 0.0
            return None
        return self.calculate_score(all_items) / c


@dataclass
class ScoreChangeEvent:
    """Event emitted when score changes."""
    event_id: str
    molt_id: str
    old_score: int
    new_score: int
    reason: str                # IMPACT_CHANGE, UNBLOCK, NEW_BLOCKER, etc.
    timestamp: str


@dataclass
class ReadyGateDecision:
    """Decision from READY gate."""
    molt_id: str
    can_start: bool
    reason: str
    current_score: int
    rank_in_queue: int
    blockers: List[str]


class PriorityQueueEngine:
    """Priority Queue — score-based work ordering with READY gate."""

    def __init__(self, mode: str = MODE_IMPACT,
                 constraint_unit: str = DEFAULT_CONSTRAINT_UNIT,
                 mode_molt_id: Optional[str] = None):
        self.items = {}              # molt_id → QueueItem
        self.score_events = []
        self.ready_decisions = []
        self.z2_score_pins = {}      # molt_id → pinned score (Z2 authorized)
        if mode not in (MODE_IMPACT, MODE_RESOURCE):
            raise ValueError(f"unknown scoring mode {mode!r}")
        self.mode = mode
        self.constraint_unit = constraint_unit
        self.mode_molt_id = mode_molt_id   # the ratification that authorised the mode

    # ------------------------------------------------------------------ mode
    @classmethod
    def from_constants(cls, constants_path: str = 'constants.json',
                       **kwargs) -> 'PriorityQueueEngine':
        """Build an engine whose mode is set by a RATIFIED constant.

        Resource mode activates only when constants.json carries
        QUEUE_SCORING_MODE with current_value 'resource' AND a non-null molt_id.
        A constant with molt_id null is a proposal, not a decision (constants
        node rule), so the engine stays on the incumbent formula — the code does
        not flip its own gate.
        """
        mode, molt_id, unit = MODE_IMPACT, None, DEFAULT_CONSTRAINT_UNIT
        try:
            with open(constants_path, encoding='utf-8') as f:
                consts = json.load(f).get('constants', [])
        except (OSError, json.JSONDecodeError):
            consts = []
        by_name = {c.get('name'): c for c in consts}
        row = by_name.get('QUEUE_SCORING_MODE')
        if row and row.get('molt_id') and row.get('current_value') == MODE_RESOURCE:
            mode, molt_id = MODE_RESOURCE, row['molt_id']
        unit_row = by_name.get('CONSTRAINT_UNIT')
        if unit_row and unit_row.get('current_value'):
            unit = unit_row['current_value']
        return cls(mode=mode, constraint_unit=unit, mode_molt_id=molt_id, **kwargs)

    # ------------------------------------------------------------- ordering
    def _sort_key(self, item: 'QueueItem'):
        """Ordering key, descending.

        impact mode:   (score,)
        resource mode: (band A first, then density, then score as tiebreak);
                       unpriced rows sort last and are refused by the gate.
        """
        if self.mode == MODE_IMPACT:
            return (item.score,)
        band = item.band(self.constraint_unit)
        if band == 'A':
            return (2, item.score, 0.0)
        if band == 'B':
            return (1, item.density(self.items, self.constraint_unit) or 0.0, item.score)
        return (0, 0.0, item.score)

    def _sorted_items(self):
        return sorted(self.items.items(), key=lambda kv: self._sort_key(kv[1]), reverse=True)

    def _gate_reason(self, item: 'QueueItem') -> Optional[str]:
        """Why this row may not start, or None if it may.

        Resource mode adds exactly one rule to the incumbent gate: a row that
        has not priced itself in the constraint unit is not schedulable. Unbounded
        demand on the constraint is what a benefit-only queue produces (F-RBE-02).
        """
        if not item.can_start():
            return 'BLOCKED'
        if self.mode == MODE_RESOURCE and not item.is_priced(self.constraint_unit):
            return f'UNPRICED — no {self.constraint_unit} cost declared'
        return None

    def add_item(self, item: QueueItem) -> Dict[str, Any]:
        """
        Add work order to queue.

        Args:
            item: QueueItem to add

        Returns:
            Dict with item status and initial score
        """
        self.items[item.molt_id] = item

        # Calculate initial score
        item.score = item.calculate_score(self.items)

        return {
            'molt_id': item.molt_id,
            'status': 'ADDED',
            'initial_score': item.score,
            'impact': item.impact,
        }

    def update_item_status(self, molt_id: str, new_status: str) -> Dict[str, Any]:
        """
        Update work order status and recalculate affected scores.

        Args:
            molt_id: ID of item to update
            new_status: New status (READY, BLOCKED, COMPLETED, IN_PROGRESS)

        Returns:
            Dict with status update and score changes
        """
        if molt_id not in self.items:
            return {'error': f'Item {molt_id} not found'}

        item = self.items[molt_id]
        old_status = item.status
        item.status = new_status

        # If completing, update any items that were blocked by this
        score_changes = []
        if new_status == QueueItemStatus.COMPLETED.value:
            item.completed_at = datetime.now().isoformat()

            # Remove this item from blockers of other items
            for other_id, other_item in self.items.items():
                if molt_id in other_item.blocked_by:
                    other_item.blocked_by.remove(molt_id)

                    # Recalculate score for unblocked item
                    old_score = other_item.score
                    new_score = other_item.calculate_score(self.items)

                    if new_score != old_score:
                        event = ScoreChangeEvent(
                            event_id=f'SCE-{datetime.now().isoformat()[:10]}-{len(self.score_events):05d}',
                            molt_id=other_id,
                            old_score=old_score,
                            new_score=new_score,
                            reason='UNBLOCK',
                            timestamp=datetime.now().isoformat(),
                        )
                        self.score_events.append(asdict(event))
                        score_changes.append({
                            'molt_id': other_id,
                            'reason': 'UNBLOCK',
                            'old_score': old_score,
                            'new_score': new_score,
                        })

                    other_item.score = new_score

        return {
            'molt_id': molt_id,
            'old_status': old_status,
            'new_status': new_status,
            'score_changes': score_changes,
            'status': 'UPDATED',
        }

    def resolve_blocker(self, blocked_molt_id: str, blocker_molt_id: str) -> Dict[str, Any]:
        """
        Record that a blocker is resolved (unblock action completed).

        Args:
            blocked_molt_id: ID of blocked item
            blocker_molt_id: ID of blocker that's now resolved

        Returns:
            Dict with unblock status and score changes
        """
        if blocked_molt_id not in self.items:
            return {'error': f'Blocked item {blocked_molt_id} not found'}

        blocked_item = self.items[blocked_molt_id]

        if blocker_molt_id not in blocked_item.blocked_by:
            return {
                'blocked_molt_id': blocked_molt_id,
                'blocker_molt_id': blocker_molt_id,
                'status': 'NOT_A_BLOCKER',
            }

        # Remove blocker
        blocked_item.blocked_by.remove(blocker_molt_id)

        # Recalculate score
        old_score = blocked_item.score
        new_score = blocked_item.calculate_score(self.items)
        blocked_item.score = new_score

        # Update status if fully unblocked
        if len(blocked_item.blocked_by) == 0:
            blocked_item.status = QueueItemStatus.READY.value

        event = ScoreChangeEvent(
            event_id=f'SCE-{datetime.now().isoformat()[:10]}-{len(self.score_events):05d}',
            molt_id=blocked_molt_id,
            old_score=old_score,
            new_score=new_score,
            reason='BLOCKER_RESOLVED',
            timestamp=datetime.now().isoformat(),
        )

        self.score_events.append(asdict(event))

        return {
            'blocked_molt_id': blocked_molt_id,
            'blocker_molt_id': blocker_molt_id,
            'status': 'RESOLVED',
            'old_score': old_score,
            'new_score': new_score,
            'now_ready': len(blocked_item.blocked_by) == 0,
        }

    def apply_ready_gate(self) -> Dict[str, Any]:
        """
        Apply READY gate: determine which items can start.

        Only items with:
        - status = READY
        - blocked_by is empty
        - top-score ranking

        Returns:
            Dict with ready items, blocked items, gate decision
        """
        sorted_items = self._sorted_items()

        ready_items = []
        blocked_items = []

        for rank, (molt_id, item) in enumerate(sorted_items):
            if item.status == QueueItemStatus.COMPLETED.value:
                continue

            reason = self._gate_reason(item)
            decision = ReadyGateDecision(
                molt_id=molt_id,
                can_start=reason is None,
                reason=reason or 'READY',
                current_score=item.score,
                rank_in_queue=rank,
                blockers=item.blocked_by,
            )

            if reason is None:
                ready_items.append(asdict(decision))
            else:
                blocked_items.append(asdict(decision))

            self.ready_decisions.append(asdict(decision))

        return {
            'mode': self.mode,
            'constraint_unit': self.constraint_unit if self.mode == MODE_RESOURCE else None,
            'ready_items': len(ready_items),
            'blocked_items': len(blocked_items),
            'ready': ready_items,
            'blocked': blocked_items,
            'gate_status': 'APPLIED',
        }

    def get_next_ready(self) -> Optional[Dict[str, Any]]:
        """Top of queue: highest score (impact mode) or highest band/density
        (resource mode), among rows the gate lets start."""
        for molt_id, item in self._sorted_items():
            if self._gate_reason(item) is None:
                out = {
                    'molt_id': molt_id,
                    'score': item.score,
                    'impact': item.impact,
                    'description': item.description,
                    'blocks': item.blocks,
                }
                if self.mode == MODE_RESOURCE:
                    out.update({
                        'band': item.band(self.constraint_unit),
                        'cost': item.cost,
                        'density': item.density(self.items, self.constraint_unit),
                    })
                return out

        return None

    def pin_score_z2(self, molt_id: str, z2_authorized: bool) -> Dict[str, Any]:
        """
        Record Z2 authorization of item's score.

        Args:
            molt_id: ID of item
            z2_authorized: Z2 approves this score

        Returns:
            Dict with pin status
        """
        if molt_id not in self.items:
            return {'error': f'Item {molt_id} not found'}

        self.z2_score_pins[molt_id] = z2_authorized

        return {
            'molt_id': molt_id,
            'z2_authorized': z2_authorized,
            'score': self.items[molt_id].score,
            'status': 'PINNED',
        }

    def report_queue(self) -> Dict[str, Any]:
        """Report full queue state."""
        sorted_items = self._sorted_items()

        def row(rank, molt_id, item):
            r = {
                'rank': rank,
                'molt_id': molt_id,
                'score': item.score,
                'impact': item.impact,
                'status': item.status,
                'blocked_by': item.blocked_by,
            }
            if self.mode == MODE_RESOURCE:
                r.update({
                    'band': item.band(self.constraint_unit),
                    'cost': item.cost,
                    'constraint_cost': item.constraint_cost(self.constraint_unit),
                    'density': item.density(self.items, self.constraint_unit),
                })
            return r

        report = {
            'mode': self.mode,
            'total_items': len(self.items),
            'ready_count': sum(1 for item in self.items.values() if self._gate_reason(item) is None),
            'blocked_count': sum(1 for item in self.items.values() if item.status == QueueItemStatus.BLOCKED.value),
            'completed_count': sum(1 for item in self.items.values() if item.status == QueueItemStatus.COMPLETED.value),
            'queue': [row(rank, molt_id, item) for rank, (molt_id, item) in enumerate(sorted_items)],
        }
        if self.mode == MODE_RESOURCE:
            priced = [i for i in self.items.values() if i.is_priced(self.constraint_unit)]
            report.update({
                'constraint_unit': self.constraint_unit,
                'mode_molt_id': self.mode_molt_id,
                'unpriced_count': len(self.items) - len(priced),
                'constraint_demand': sum(i.constraint_cost(self.constraint_unit) or 0 for i in priced),
                'constraint_demand_note': 'excludes unpriced rows; they are refused, not costed at zero',
            })
        return report
