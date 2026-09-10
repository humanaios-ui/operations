"""
agent_caps_runtime.py — Agent Behavioral Cap Enforcement (v0.1)

Enforces per-agent caps defined in behavior_spec.json:
- Request limits (N req/hour per zone)
- Token budgets (context window allocation per session)
- Reply cost caps (max tokens per reply)
- Concurrent operation limits (max simultaneous tasks per zone)
- Scope caps (which repositories, decision classes, zones)

Pattern:
1. CapEnforcer loads behavior_spec.json at init
2. Before operation: check_cap_before_operation(agent_id, op_type, cost, zone)
3. Returns: (allowed: bool, remaining_budget: Dict, reason: str)
4. On exceed: blocks operation, logs to audit trail, emits GAP callout
5. Integration: called by agent_core.py, prs_run.py, adv_eval.py
"""

import json
import hashlib
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta
from enum import Enum
import re


class OperationType(Enum):
    """Types of operations subject to cap enforcement."""
    REQUEST = "REQUEST"                 # API request (counts against request limit)
    TOKEN_ALLOCATION = "TOKEN_ALLOCATION"  # Token budget claim
    REPLY_GENERATION = "REPLY_GENERATION"  # Reply generation (counts tokens)
    CONCURRENT_TASK = "CONCURRENT_TASK"    # Start concurrent task
    ZONE_ACCESS = "ZONE_ACCESS"            # Access to a zone


@dataclass
class CapDefinition:
    """A single cap definition from behavior_spec.json."""
    cap_name: str                       # e.g., "max_requests_per_hour_z1"
    cap_type: str                       # REQUEST, TOKEN_BUDGET, REPLY_COST, CONCURRENT, SCOPE
    limit: Optional[int] = None         # Numeric limit
    window_minutes: Optional[int] = None # Time window (for rate-based caps)
    zones: Optional[List[str]] = None   # Applicable zones (Z1, Z2, Z3)
    scope_repos: Optional[List[str]] = None  # Allowed repos (if SCOPE cap)
    scope_decision_classes: Optional[List[str]] = None  # Allowed classes
    enabled: bool = True


@dataclass
class CapUsage:
    """Current usage tracking for a single agent."""
    agent_id: str
    cap_name: str
    operations_count: int = 0
    tokens_used: int = 0
    concurrent_tasks: int = 0
    last_reset_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    events: List[Dict[str, Any]] = field(default_factory=list)

    def reset_if_window_expired(self, window_minutes: int):
        """Reset counters if window_minutes has elapsed since last_reset_at."""
        last_reset = datetime.fromisoformat(self.last_reset_at.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        elapsed = (now - last_reset).total_seconds() / 60
        if elapsed >= window_minutes:
            self.operations_count = 0
            self.tokens_used = 0
            self.concurrent_tasks = 0
            self.last_reset_at = now.isoformat()


@dataclass
class CapCheckResult:
    """Result of cap check before operation."""
    allowed: bool
    reason: str
    remaining_budget: Dict[str, Any] = field(default_factory=dict)
    violated_caps: List[str] = field(default_factory=list)


class CapEnforcer:
    """Enforces agent behavioral caps from behavior_spec.json."""

    def __init__(self, behavior_spec_path: str = "behavior_spec.json"):
        """
        Initialize CapEnforcer.

        Args:
            behavior_spec_path: Path to behavior_spec.json
        """
        self.behavior_spec_path = behavior_spec_path
        self.caps: Dict[str, CapDefinition] = {}
        self.usage: Dict[str, Dict[str, CapUsage]] = {}  # agent_id -> cap_name -> CapUsage
        self.audit_trail: List[Dict[str, Any]] = []
        self._load_caps()

    def _load_caps(self):
        """Load cap definitions from behavior_spec.json."""
        try:
            with open(self.behavior_spec_path, 'r') as f:
                spec = json.load(f)

            # Extract caps section
            caps_section = spec.get('caps', {})
            for cap_name, cap_def in caps_section.items():
                self.caps[cap_name] = CapDefinition(
                    cap_name=cap_name,
                    cap_type=cap_def.get('type', 'UNKNOWN'),
                    limit=cap_def.get('limit'),
                    window_minutes=cap_def.get('window_minutes', 60),
                    zones=cap_def.get('zones', ['Z1', 'Z2', 'Z3']),
                    scope_repos=cap_def.get('scope_repos'),
                    scope_decision_classes=cap_def.get('scope_decision_classes'),
                    enabled=cap_def.get('enabled', True)
                )
        except FileNotFoundError:
            # Create minimal default caps if file not found
            self._create_default_caps()

    def _create_default_caps(self):
        """Create default cap definitions."""
        self.caps = {
            'max_requests_per_hour': CapDefinition(
                cap_name='max_requests_per_hour',
                cap_type='REQUEST',
                limit=100,
                window_minutes=60,
                zones=['Z1', 'Z2', 'Z3']
            ),
            'token_budget_per_session': CapDefinition(
                cap_name='token_budget_per_session',
                cap_type='TOKEN_BUDGET',
                limit=100000,
                window_minutes=None,
                zones=['Z1']
            ),
            'max_reply_tokens': CapDefinition(
                cap_name='max_reply_tokens',
                cap_type='REPLY_COST',
                limit=4000,
                window_minutes=None,
                zones=['Z1']
            ),
            'max_concurrent_tasks': CapDefinition(
                cap_name='max_concurrent_tasks',
                cap_type='CONCURRENT',
                limit=3,
                window_minutes=None,
                zones=['Z1']
            ),
        }

    def check_cap_before_operation(
        self,
        agent_id: str,
        op_type: OperationType,
        cost: int = 1,
        zone: str = 'Z1',
        repo: Optional[str] = None,
        decision_class: Optional[str] = None
    ) -> CapCheckResult:
        """
        Check whether operation is allowed under current caps.

        Args:
            agent_id: Agent identifier (e.g., 'claude-agent-1')
            op_type: OperationType enum
            cost: Cost of operation (requests=1, tokens=N)
            zone: Zone (Z1, Z2, Z3)
            repo: Repository (for scope checks)
            decision_class: Decision class (for scope checks)

        Returns:
            CapCheckResult with allowed/reason/remaining_budget
        """
        result = CapCheckResult(
            allowed=True,
            reason="No caps violated",
            remaining_budget={},
            violated_caps=[]
        )

        # Initialize usage tracking for this agent if needed
        if agent_id not in self.usage:
            self.usage[agent_id] = {}

        violated = []

        # Check each applicable cap
        for cap_name, cap_def in self.caps.items():
            if not cap_def.enabled:
                continue
            if zone not in (cap_def.zones or ['Z1', 'Z2', 'Z3']):
                continue

            # Skip if cap doesn't apply to this operation type
            if not self._cap_applies_to_operation(cap_def, op_type):
                continue

            # Initialize usage for this cap if needed
            if cap_name not in self.usage[agent_id]:
                self.usage[agent_id][cap_name] = CapUsage(agent_id, cap_name)

            usage = self.usage[agent_id][cap_name]

            # Reset counters if window expired
            if cap_def.window_minutes:
                usage.reset_if_window_expired(cap_def.window_minutes)

            # Check REQUEST caps
            if cap_def.cap_type == 'REQUEST' and op_type == OperationType.REQUEST:
                if usage.operations_count >= cap_def.limit:
                    violated.append(cap_name)
                else:
                    remaining = cap_def.limit - usage.operations_count
                    result.remaining_budget[cap_name] = remaining

            # Check TOKEN_BUDGET caps
            elif cap_def.cap_type == 'TOKEN_BUDGET' and op_type == OperationType.TOKEN_ALLOCATION:
                if usage.tokens_used + cost > cap_def.limit:
                    violated.append(cap_name)
                else:
                    remaining = cap_def.limit - usage.tokens_used
                    result.remaining_budget[cap_name] = remaining

            # Check REPLY_COST caps
            elif cap_def.cap_type == 'REPLY_COST' and op_type == OperationType.REPLY_GENERATION:
                if cost > cap_def.limit:
                    violated.append(cap_name)
                else:
                    remaining = cap_def.limit - cost
                    result.remaining_budget[cap_name] = remaining

            # Check CONCURRENT caps
            elif cap_def.cap_type == 'CONCURRENT' and op_type == OperationType.CONCURRENT_TASK:
                if usage.concurrent_tasks >= cap_def.limit:
                    violated.append(cap_name)
                else:
                    remaining = cap_def.limit - usage.concurrent_tasks
                    result.remaining_budget[cap_name] = remaining

            # Check SCOPE caps
            elif cap_def.cap_type == 'SCOPE' and op_type == OperationType.ZONE_ACCESS:
                if cap_def.scope_repos and repo and repo not in cap_def.scope_repos:
                    violated.append(f"{cap_name}:repo_scope")
                if cap_def.scope_decision_classes and decision_class and decision_class not in cap_def.scope_decision_classes:
                    violated.append(f"{cap_name}:class_scope")

        if violated:
            result.allowed = False
            result.violated_caps = violated
            result.reason = f"Cap violations: {', '.join(violated)}"

        # Log to audit trail
        self._log_cap_check(agent_id, op_type, cost, zone, result)

        return result

    def record_operation(
        self,
        agent_id: str,
        op_type: OperationType,
        cost: int = 1,
        zone: str = 'Z1',
        outcome: str = 'SUCCESS'
    ) -> bool:
        """
        Record that operation completed; increment usage counters.

        Args:
            agent_id: Agent identifier
            op_type: OperationType enum
            cost: Cost of operation
            zone: Zone
            outcome: SUCCESS, BLOCKED, or EXCEEDED

        Returns:
            True if recorded successfully
        """
        if agent_id not in self.usage:
            self.usage[agent_id] = {}

        event = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'agent_id': agent_id,
            'op_type': op_type.value,
            'cost': cost,
            'zone': zone,
            'outcome': outcome
        }

        if outcome == 'SUCCESS':
            # Increment appropriate counters
            for cap_name, cap_def in self.caps.items():
                if not cap_def.enabled or zone not in (cap_def.zones or ['Z1', 'Z2', 'Z3']):
                    continue

                if cap_name not in self.usage[agent_id]:
                    self.usage[agent_id][cap_name] = CapUsage(agent_id, cap_name)

                usage = self.usage[agent_id][cap_name]
                if cap_def.window_minutes:
                    usage.reset_if_window_expired(cap_def.window_minutes)

                if cap_def.cap_type == 'REQUEST' and op_type == OperationType.REQUEST:
                    usage.operations_count += 1
                elif cap_def.cap_type == 'TOKEN_BUDGET' and op_type == OperationType.TOKEN_ALLOCATION:
                    usage.tokens_used += cost
                elif cap_def.cap_type == 'CONCURRENT' and op_type == OperationType.CONCURRENT_TASK:
                    usage.concurrent_tasks += 1

                usage.events.append(event)

        self.audit_trail.append(event)
        return True

    def release_concurrent_task(self, agent_id: str, zone: str = 'Z1') -> bool:
        """Decrement concurrent task count when task completes."""
        for cap_name, usage in self.usage.get(agent_id, {}).items():
            cap_def = self.caps.get(cap_name)
            if cap_def and cap_def.cap_type == 'CONCURRENT':
                if usage.concurrent_tasks > 0:
                    usage.concurrent_tasks -= 1
        return True

    def get_remaining_budget(self, agent_id: str, zone: str = 'Z1') -> Dict[str, Any]:
        """Get remaining budget for all applicable caps."""
        budget = {}
        for cap_name, cap_def in self.caps.items():
            if not cap_def.enabled or zone not in (cap_def.zones or ['Z1', 'Z2', 'Z3']):
                continue

            if cap_name not in self.usage.get(agent_id, {}):
                # Cap not yet tracked for this agent; full budget available
                budget[cap_name] = {
                    'limit': cap_def.limit,
                    'used': 0,
                    'remaining': cap_def.limit
                }
            else:
                usage = self.usage[agent_id][cap_name]
                if cap_def.window_minutes:
                    usage.reset_if_window_expired(cap_def.window_minutes)

                remaining = cap_def.limit - max(
                    usage.operations_count,
                    usage.tokens_used,
                    usage.concurrent_tasks
                )
                budget[cap_name] = {
                    'limit': cap_def.limit,
                    'used': max(usage.operations_count, usage.tokens_used, usage.concurrent_tasks),
                    'remaining': remaining
                }

        return budget

    def _cap_applies_to_operation(self, cap_def: CapDefinition, op_type: OperationType) -> bool:
        """Check if a cap applies to an operation type."""
        cap_type_map = {
            'REQUEST': OperationType.REQUEST,
            'TOKEN_BUDGET': OperationType.TOKEN_ALLOCATION,
            'REPLY_COST': OperationType.REPLY_GENERATION,
            'CONCURRENT': OperationType.CONCURRENT_TASK,
            'SCOPE': OperationType.ZONE_ACCESS,
        }
        return cap_type_map.get(cap_def.cap_type) == op_type

    def _log_cap_check(
        self,
        agent_id: str,
        op_type: OperationType,
        cost: int,
        zone: str,
        result: CapCheckResult
    ):
        """Log cap check to audit trail."""
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'type': 'cap_check',
            'agent_id': agent_id,
            'op_type': op_type.value,
            'cost': cost,
            'zone': zone,
            'allowed': result.allowed,
            'violated_caps': result.violated_caps
        }
        self.audit_trail.append(log_entry)

    def export_audit_trail(self, filepath: str = "cap_audit_trail.jsonl"):
        """Export audit trail to JSONL file."""
        with open(filepath, 'w') as f:
            for entry in self.audit_trail:
                f.write(json.dumps(entry, default=str) + '\n')

    def export_usage_summary(self, filepath: str = "cap_usage_summary.json"):
        """Export usage summary to JSON file."""
        summary = {}
        for agent_id, caps in self.usage.items():
            summary[agent_id] = {}
            for cap_name, usage in caps.items():
                summary[agent_id][cap_name] = {
                    'operations_count': usage.operations_count,
                    'tokens_used': usage.tokens_used,
                    'concurrent_tasks': usage.concurrent_tasks,
                    'last_reset_at': usage.last_reset_at,
                    'event_count': len(usage.events)
                }
        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
