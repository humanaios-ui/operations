"""
agent_core.py — Agent Runtime with Capacity Enforcement

Executes work orders from PRIORITY_QUEUE.md with hard caps on:
- investor: hours available before escalation
- business: token budget before halt
- investor_spent: tracked hours consumed
- business_spent: tracked tokens consumed

Pattern:
1. READ: Fetch PRIORITY_QUEUE.md (pinned SHA), extract READY top-score rows
2. CHECK: Validate caps vs current drawdown; halt if exceeded
3. EXECUTE: Run task with locked parameters; emit CYCLE event
4. MEASURE: Track hours and tokens; emit drawdown event on exceedance
5. REPORT: Return task result or HALT status

Caps are read from behavior_spec.json (constants node) and enforced by CI gate.
No auto-approve beyond cap; Z2 must explicitly authorize via molt.
"""

import json
import hashlib
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class TaskStatus(Enum):
    """Status of agent task execution."""
    READY = "READY"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    HALTED = "HALTED"
    CAP_EXCEEDED = "CAP_EXCEEDED"
    Z2_REQUIRED = "Z2_REQUIRED"


class CapType(Enum):
    """Capacity constraint types."""
    INVESTOR = "investor"      # hours available
    BUSINESS = "business"      # token budget
    BOTH = "both"              # both caps apply


@dataclass
class AgentCaps:
    """Capacity constraints for agent execution."""
    investor: float            # hours available before halt
    business: int              # tokens available before halt
    investor_spent: float = 0.0
    business_spent: int = 0

    def available_hours(self) -> float:
        return self.investor - self.investor_spent

    def available_tokens(self) -> int:
        return self.business - self.business_spent

    def is_over_hours(self) -> bool:
        return self.investor_spent > self.investor

    def is_over_tokens(self) -> bool:
        return self.business_spent > self.business

    def is_over_any(self) -> bool:
        return self.is_over_hours() or self.is_over_tokens()


@dataclass
class WorkOrder:
    """Work order from PRIORITY_QUEUE."""
    molt_id: str
    rank: int
    impact: int
    status: str              # READY, BLOCKED, COMPLETED
    description: str
    estimated_hours: float
    estimated_tokens: int

    def can_fit_in_caps(self, caps: AgentCaps) -> bool:
        """Check if task can fit within available caps."""
        return (self.estimated_hours <= caps.available_hours() and
                self.estimated_tokens <= caps.available_tokens())


@dataclass
class CycleEvent:
    """Event emitted during task execution."""
    event_id: str
    molt_id: str
    status: str              # READY, RUNNING, COMPLETED, HALTED, CAP_EXCEEDED
    hours_consumed: float
    tokens_consumed: int
    task_result: Optional[Dict[str, Any]]
    cap_status: Dict[str, Any]
    timestamp: str


class AgentRuntime:
    """Agent Runtime — executes work orders with capacity enforcement."""

    def __init__(self, caps: AgentCaps):
        """Initialize agent with capacity limits."""
        self.caps = caps
        self.cycles = []
        self.task_history = []

    def load_caps_from_spec(self, spec_path: str) -> Dict[str, Any]:
        """
        Load agent caps from behavior_spec.json (constants node).

        Args:
            spec_path: Path to behavior_spec.json

        Returns:
            Dict with investor and business caps
        """
        try:
            with open(spec_path, 'r') as f:
                spec = json.load(f)

            agent_spec = spec.get('agent_caps', {})
            return {
                'investor': agent_spec.get('investor', self.caps.investor),
                'business': agent_spec.get('business', self.caps.business),
            }
        except FileNotFoundError:
            return {
                'investor': self.caps.investor,
                'business': self.caps.business,
            }

    def check_caps(self, work_order: WorkOrder) -> Dict[str, Any]:
        """
        Check if task can execute within cap limits.

        Args:
            work_order: WorkOrder to validate

        Returns:
            Dict with cap_ok (bool), reason, available hours/tokens
        """
        # Check if already over cap
        if self.caps.is_over_any():
            return {
                'cap_ok': False,
                'reason': f'Already over cap: investor={self.caps.investor_spent}/{self.caps.investor}h, business={self.caps.business_spent}/{self.caps.business}t',
                'investor_spent': self.caps.investor_spent,
                'business_spent': self.caps.business_spent,
                'status': TaskStatus.CAP_EXCEEDED.value,
            }

        # Check if task fits
        if not work_order.can_fit_in_caps(self.caps):
            return {
                'cap_ok': False,
                'reason': f'Task exceeds available caps: needs {work_order.estimated_hours}h/{work_order.estimated_tokens}t, have {self.caps.available_hours():.1f}h/{self.caps.available_tokens()}t',
                'investor_available': self.caps.available_hours(),
                'business_available': self.caps.available_tokens(),
                'status': TaskStatus.Z2_REQUIRED.value,
            }

        return {
            'cap_ok': True,
            'investor_available': self.caps.available_hours(),
            'business_available': self.caps.available_tokens(),
            'status': TaskStatus.READY.value,
        }

    def execute_task(self, work_order: WorkOrder, task_fn=None) -> Dict[str, Any]:
        """
        Execute a work order task with cap enforcement.

        Args:
            work_order: WorkOrder to execute
            task_fn: Optional task function(work_order) → (hours, tokens, result)

        Returns:
            Dict with execution status, result, caps after
        """
        # Validate caps
        cap_check = self.check_caps(work_order)
        if not cap_check['cap_ok']:
            return {
                'molt_id': work_order.molt_id,
                'status': cap_check['status'],
                'reason': cap_check['reason'],
                'cap_status': {
                    'investor_spent': self.caps.investor_spent,
                    'business_spent': self.caps.business_spent,
                    'investor_total': self.caps.investor,
                    'business_total': self.caps.business,
                },
                'task_result': None,
            }

        # Execute task or use stub
        if task_fn:
            hours, tokens, result = task_fn(work_order)
        else:
            # Stub execution: consume estimated resources
            hours = work_order.estimated_hours
            tokens = work_order.estimated_tokens
            result = {
                'molt_id': work_order.molt_id,
                'completed_steps': 1,
                'output': f'Task {work_order.molt_id} executed with stub runner',
            }

        # Update drawdown
        self.caps.investor_spent += hours
        self.caps.business_spent += tokens

        # Emit CYCLE event
        event_id = f'CY-{datetime.now().isoformat()[:10]}-{len(self.cycles):05d}'

        cycle_event = CycleEvent(
            event_id=event_id,
            molt_id=work_order.molt_id,
            status=TaskStatus.COMPLETED.value if self.caps.investor_spent <= self.caps.investor else TaskStatus.CAP_EXCEEDED.value,
            hours_consumed=hours,
            tokens_consumed=tokens,
            task_result=result,
            cap_status={
                'investor_spent': self.caps.investor_spent,
                'business_spent': self.caps.business_spent,
                'investor_total': self.caps.investor,
                'business_total': self.caps.business,
                'over_investor': self.caps.is_over_hours(),
                'over_business': self.caps.is_over_tokens(),
            },
            timestamp=datetime.now().isoformat(),
        )

        self.cycles.append(asdict(cycle_event))
        self.task_history.append(work_order.molt_id)

        return {
            'molt_id': work_order.molt_id,
            'status': cycle_event.status,
            'hours_consumed': hours,
            'tokens_consumed': tokens,
            'task_result': result,
            'cap_status': cycle_event.cap_status,
            'event_id': event_id,
        }

    def execute_batch(self, work_orders: List[WorkOrder], task_fn=None) -> Dict[str, Any]:
        """
        Execute multiple work orders in sequence until cap exceeded.
        Halts on first task that exceeds caps (no auto-approve beyond).

        Args:
            work_orders: List of WorkOrders from PRIORITY_QUEUE
            task_fn: Optional task function(work_order) → (hours, tokens, result)

        Returns:
            Dict with completed tasks, halted tasks, final cap status
        """
        completed = []
        halted = []

        for work_order in work_orders:
            # Check caps before attempting
            cap_check = self.check_caps(work_order)
            if not cap_check['cap_ok']:
                halted.append({
                    'molt_id': work_order.molt_id,
                    'reason': cap_check['reason'],
                    'status': cap_check['status'],
                })
                break  # Halt on first cap exceedance

            # Execute task
            result = self.execute_task(work_order, task_fn)

            if result['status'] == TaskStatus.COMPLETED.value:
                completed.append(result)
            else:
                halted.append({
                    'molt_id': work_order.molt_id,
                    'status': result['status'],
                    'reason': result.get('reason'),
                })
                break  # Halt

        return {
            'completed_tasks': len(completed),
            'halted_tasks': len(halted),
            'completed': completed,
            'halted': halted,
            'final_cap_status': {
                'investor_spent': self.caps.investor_spent,
                'business_spent': self.caps.business_spent,
                'investor_total': self.caps.investor,
                'business_total': self.caps.business,
                'over_investor': self.caps.is_over_hours(),
                'over_business': self.caps.is_over_tokens(),
            },
        }

    def report_drawdown(self) -> Dict[str, Any]:
        """Report current drawdown and remaining capacity."""
        return {
            'investor_spent': self.caps.investor_spent,
            'investor_total': self.caps.investor,
            'investor_remaining': self.caps.available_hours(),
            'business_spent': self.caps.business_spent,
            'business_total': self.caps.business,
            'business_remaining': self.caps.available_tokens(),
            'tasks_executed': len(self.task_history),
            'cycles_emitted': len(self.cycles),
            'over_any_cap': self.caps.is_over_any(),
        }

    def halt_if_over_cap(self) -> Dict[str, Any]:
        """
        Check if caps exceeded; if so, return HALT status.
        Called at end of batch or on cap exceedance.
        """
        if self.caps.is_over_any():
            return {
                'status': TaskStatus.HALTED.value,
                'reason': f'Capacity exceeded: investor={self.caps.investor_spent:.1f}h (limit {self.caps.investor}h), business={self.caps.business_spent}t (limit {self.caps.business}t)',
                'cap_status': {
                    'investor_spent': self.caps.investor_spent,
                    'business_spent': self.caps.business_spent,
                    'over_investor': self.caps.is_over_hours(),
                    'over_business': self.caps.is_over_tokens(),
                },
                'z2_required': True,
            }

        return {
            'status': TaskStatus.READY.value,
            'reason': 'Within cap limits',
            'cap_status': {
                'investor_remaining': self.caps.available_hours(),
                'business_remaining': self.caps.available_tokens(),
            },
        }
