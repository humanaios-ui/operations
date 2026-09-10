"""
priority_queue_engine.py — Priority Queue with Score-Based READY Gate

Implements Priority Queue with dynamic scoring:
  score = impact + Σ impact(unblocks)

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
"""

import json
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from enum import Enum


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

    def __init__(self):
        self.items = {}              # molt_id → QueueItem
        self.score_events = []
        self.ready_decisions = []
        self.z2_score_pins = {}      # molt_id → pinned score (Z2 authorized)

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
        # Sort by score (descending)
        sorted_items = sorted(
            self.items.items(),
            key=lambda x: x[1].score,
            reverse=True
        )

        ready_items = []
        blocked_items = []

        for rank, (molt_id, item) in enumerate(sorted_items):
            if item.status == QueueItemStatus.COMPLETED.value:
                continue

            decision = ReadyGateDecision(
                molt_id=molt_id,
                can_start=item.can_start(),
                reason='READY' if item.can_start() else 'BLOCKED',
                current_score=item.score,
                rank_in_queue=rank,
                blockers=item.blocked_by,
            )

            if item.can_start():
                ready_items.append(asdict(decision))
            else:
                blocked_items.append(asdict(decision))

            self.ready_decisions.append(asdict(decision))

        return {
            'ready_items': len(ready_items),
            'blocked_items': len(blocked_items),
            'ready': ready_items,
            'blocked': blocked_items,
            'gate_status': 'APPLIED',
        }

    def get_next_ready(self) -> Optional[Dict[str, Any]]:
        """Get the highest-score READY item (top of queue)."""
        sorted_items = sorted(
            self.items.items(),
            key=lambda x: x[1].score,
            reverse=True
        )

        for molt_id, item in sorted_items:
            if item.can_start():
                return {
                    'molt_id': molt_id,
                    'score': item.score,
                    'impact': item.impact,
                    'description': item.description,
                    'blocks': item.blocks,
                }

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
        sorted_items = sorted(
            self.items.items(),
            key=lambda x: x[1].score,
            reverse=True
        )

        return {
            'total_items': len(self.items),
            'ready_count': sum(1 for item in self.items.values() if item.can_start()),
            'blocked_count': sum(1 for item in self.items.values() if item.status == QueueItemStatus.BLOCKED.value),
            'completed_count': sum(1 for item in self.items.values() if item.status == QueueItemStatus.COMPLETED.value),
            'queue': [
                {
                    'rank': rank,
                    'molt_id': molt_id,
                    'score': item.score,
                    'impact': item.impact,
                    'status': item.status,
                    'blocked_by': item.blocked_by,
                }
                for rank, (molt_id, item) in enumerate(sorted_items)
            ],
        }
