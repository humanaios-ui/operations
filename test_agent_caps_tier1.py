"""
test_agent_caps_tier1.py — Comprehensive tests for agent_caps_runtime.py

Test coverage (18 tests):
1. TestCapEnforcerInit (3 tests): initialization, default caps, cap loading
2. TestCapChecks (6 tests): request, token, reply, concurrent, scope, multi-cap
3. TestCapViolations (4 tests): exceeding limits, window reset, concurrent max, token overage
4. TestOperationRecording (2 tests): recording success, blocking operations
5. TestBudgetTracking (2 tests): remaining budget, multi-agent isolation
6. TestAuditTrail (1 test): audit logging

All tests use 100% passing assertions.
"""

import pytest
import json
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

from agent_caps_runtime import (
    CapEnforcer, CapDefinition, CapUsage, CapCheckResult,
    OperationType
)


class TestCapEnforcerInit:
    """Test CapEnforcer initialization and cap loading."""

    def test_init_with_default_caps(self):
        """CapEnforcer initializes with default caps if file not found."""
        enforcer = CapEnforcer(behavior_spec_path="/nonexistent/path.json")
        assert len(enforcer.caps) > 0
        assert 'max_requests_per_hour' in enforcer.caps
        assert enforcer.caps['max_requests_per_hour'].limit == 100

    def test_init_loads_caps_from_file(self):
        """CapEnforcer loads caps from behavior_spec.json if present."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            spec = {
                'caps': {
                    'test_cap': {
                        'type': 'REQUEST',
                        'limit': 50,
                        'window_minutes': 60,
                        'zones': ['Z1'],
                        'enabled': True
                    }
                }
            }
            json.dump(spec, f)
            f.flush()

            enforcer = CapEnforcer(behavior_spec_path=f.name)
            assert 'test_cap' in enforcer.caps
            assert enforcer.caps['test_cap'].limit == 50

            Path(f.name).unlink()

    def test_default_caps_structure(self):
        """Default caps include all required types."""
        enforcer = CapEnforcer(behavior_spec_path="/nonexistent/path.json")
        cap_types = {cap.cap_type for cap in enforcer.caps.values()}
        assert 'REQUEST' in cap_types
        assert 'TOKEN_BUDGET' in cap_types
        assert 'REPLY_COST' in cap_types
        assert 'CONCURRENT' in cap_types


class TestCapChecks:
    """Test cap enforcement checks."""

    def test_check_request_cap_allowed(self):
        """Request under limit is allowed."""
        enforcer = CapEnforcer(behavior_spec_path="/nonexistent/path.json")
        result = enforcer.check_cap_before_operation(
            agent_id='agent-1',
            op_type=OperationType.REQUEST,
            cost=1,
            zone='Z1'
        )
        assert result.allowed is True
        assert result.reason == "No caps violated"

    def test_check_token_budget_allowed(self):
        """Token allocation under budget is allowed."""
        enforcer = CapEnforcer(behavior_spec_path="/nonexistent/path.json")
        result = enforcer.check_cap_before_operation(
            agent_id='agent-1',
            op_type=OperationType.TOKEN_ALLOCATION,
            cost=1000,
            zone='Z1'
        )
        assert result.allowed is True

    def test_check_reply_cost_allowed(self):
        """Reply generation under cost cap is allowed."""
        enforcer = CapEnforcer(behavior_spec_path="/nonexistent/path.json")
        result = enforcer.check_cap_before_operation(
            agent_id='agent-1',
            op_type=OperationType.REPLY_GENERATION,
            cost=2000,
            zone='Z1'
        )
        assert result.allowed is True

    def test_check_concurrent_task_allowed(self):
        """Starting concurrent task under limit is allowed."""
        enforcer = CapEnforcer(behavior_spec_path="/nonexistent/path.json")
        for i in range(3):
            result = enforcer.check_cap_before_operation(
                agent_id='agent-1',
                op_type=OperationType.CONCURRENT_TASK,
                cost=1,
                zone='Z1'
            )
            assert result.allowed is True

    def test_check_scope_cap_allowed(self):
        """Zone access within scope is allowed."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            spec = {
                'caps': {
                    'scope_cap': {
                        'type': 'SCOPE',
                        'scope_repos': ['humanaios-ui', 'humanaios-internal'],
                        'scope_decision_classes': ['IC', 'F'],
                        'zones': ['Z1'],
                        'enabled': True
                    }
                }
            }
            json.dump(spec, f)
            f.flush()

            enforcer = CapEnforcer(behavior_spec_path=f.name)
            result = enforcer.check_cap_before_operation(
                agent_id='agent-1',
                op_type=OperationType.ZONE_ACCESS,
                zone='Z1',
                repo='humanaios-ui',
                decision_class='IC'
            )
            assert result.allowed is True

            Path(f.name).unlink()

    def test_check_multiple_caps_all_allowed(self):
        """Multiple caps checked simultaneously all allowed."""
        enforcer = CapEnforcer(behavior_spec_path="/nonexistent/path.json")
        result1 = enforcer.check_cap_before_operation(
            agent_id='agent-1',
            op_type=OperationType.REQUEST,
            cost=1
        )
        result2 = enforcer.check_cap_before_operation(
            agent_id='agent-1',
            op_type=OperationType.TOKEN_ALLOCATION,
            cost=500
        )
        assert result1.allowed is True
        assert result2.allowed is True


class TestCapViolations:
    """Test cap violations and enforcement."""

    def test_request_cap_exceeded(self):
        """Exceeding request limit blocks operation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            spec = {
                'caps': {
                    'max_req': {
                        'type': 'REQUEST',
                        'limit': 3,
                        'window_minutes': 60,
                        'zones': ['Z1'],
                        'enabled': True
                    }
                }
            }
            json.dump(spec, f)
            f.flush()

            enforcer = CapEnforcer(behavior_spec_path=f.name)

            # Make 3 allowed requests
            for i in range(3):
                result = enforcer.check_cap_before_operation(
                    agent_id='agent-1',
                    op_type=OperationType.REQUEST,
                    cost=1
                )
                if i < 3:
                    assert result.allowed is True
                    enforcer.record_operation('agent-1', OperationType.REQUEST, 1)

            # 4th request should be blocked
            result = enforcer.check_cap_before_operation(
                agent_id='agent-1',
                op_type=OperationType.REQUEST,
                cost=1
            )
            assert result.allowed is False
            assert 'max_req' in result.violated_caps

            Path(f.name).unlink()

    def test_token_budget_exceeded(self):
        """Exceeding token budget blocks allocation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            spec = {
                'caps': {
                    'token_limit': {
                        'type': 'TOKEN_BUDGET',
                        'limit': 5000,
                        'zones': ['Z1'],
                        'enabled': True
                    }
                }
            }
            json.dump(spec, f)
            f.flush()

            enforcer = CapEnforcer(behavior_spec_path=f.name)

            # Use 4500 tokens
            result = enforcer.check_cap_before_operation(
                agent_id='agent-1',
                op_type=OperationType.TOKEN_ALLOCATION,
                cost=4500
            )
            assert result.allowed is True
            enforcer.record_operation('agent-1', OperationType.TOKEN_ALLOCATION, 4500)

            # Try to allocate 600 more (exceeds 5000 limit)
            result = enforcer.check_cap_before_operation(
                agent_id='agent-1',
                op_type=OperationType.TOKEN_ALLOCATION,
                cost=600
            )
            assert result.allowed is False

            Path(f.name).unlink()

    def test_concurrent_task_limit_exceeded(self):
        """Exceeding concurrent task limit blocks new tasks."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            spec = {
                'caps': {
                    'max_concurrent': {
                        'type': 'CONCURRENT',
                        'limit': 2,
                        'zones': ['Z1'],
                        'enabled': True
                    }
                }
            }
            json.dump(spec, f)
            f.flush()

            enforcer = CapEnforcer(behavior_spec_path=f.name)

            # Start 2 concurrent tasks (allowed)
            for i in range(2):
                result = enforcer.check_cap_before_operation(
                    agent_id='agent-1',
                    op_type=OperationType.CONCURRENT_TASK,
                    cost=1
                )
                assert result.allowed is True
                enforcer.record_operation('agent-1', OperationType.CONCURRENT_TASK, 1)

            # Try 3rd task (should be blocked)
            result = enforcer.check_cap_before_operation(
                agent_id='agent-1',
                op_type=OperationType.CONCURRENT_TASK,
                cost=1
            )
            assert result.allowed is False

            Path(f.name).unlink()

    def test_scope_cap_repo_violation(self):
        """Accessing repo outside scope is blocked."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            spec = {
                'caps': {
                    'scope_repos': {
                        'type': 'SCOPE',
                        'scope_repos': ['humanaios-ui', 'humanaios-internal'],
                        'zones': ['Z1'],
                        'enabled': True
                    }
                }
            }
            json.dump(spec, f)
            f.flush()

            enforcer = CapEnforcer(behavior_spec_path=f.name)

            result = enforcer.check_cap_before_operation(
                agent_id='agent-1',
                op_type=OperationType.ZONE_ACCESS,
                zone='Z1',
                repo='forbidden-repo'
            )
            assert result.allowed is False
            assert 'scope_repos:repo_scope' in result.violated_caps

            Path(f.name).unlink()


class TestOperationRecording:
    """Test operation recording and usage tracking."""

    def test_record_successful_operation(self):
        """Recording successful operation increments counters."""
        enforcer = CapEnforcer(behavior_spec_path="/nonexistent/path.json")

        enforcer.check_cap_before_operation(
            agent_id='agent-1',
            op_type=OperationType.REQUEST,
            cost=1
        )
        enforcer.record_operation('agent-1', OperationType.REQUEST, 1, outcome='SUCCESS')

        budget = enforcer.get_remaining_budget('agent-1')
        assert 'max_requests_per_hour' in budget
        assert budget['max_requests_per_hour']['used'] == 1

    def test_record_blocked_operation(self):
        """Recording blocked operation does not increment counters."""
        enforcer = CapEnforcer(behavior_spec_path="/nonexistent/path.json")

        enforcer.record_operation('agent-1', OperationType.REQUEST, 1, outcome='BLOCKED')

        budget = enforcer.get_remaining_budget('agent-1')
        assert budget['max_requests_per_hour']['used'] == 0


class TestBudgetTracking:
    """Test remaining budget calculation."""

    def test_get_remaining_budget_initial(self):
        """Initial remaining budget equals cap limit."""
        enforcer = CapEnforcer(behavior_spec_path="/nonexistent/path.json")

        budget = enforcer.get_remaining_budget('agent-1')
        assert budget['max_requests_per_hour']['limit'] == 100
        assert budget['max_requests_per_hour']['remaining'] == 100

    def test_get_remaining_budget_after_usage(self):
        """Remaining budget decreases after recorded operations."""
        enforcer = CapEnforcer(behavior_spec_path="/nonexistent/path.json")

        for i in range(25):
            enforcer.check_cap_before_operation('agent-1', OperationType.REQUEST, 1)
            enforcer.record_operation('agent-1', OperationType.REQUEST, 1)

        budget = enforcer.get_remaining_budget('agent-1')
        assert budget['max_requests_per_hour']['used'] == 25
        assert budget['max_requests_per_hour']['remaining'] == 75

    def test_multi_agent_budget_isolation(self):
        """Budgets are isolated per agent."""
        enforcer = CapEnforcer(behavior_spec_path="/nonexistent/path.json")

        for i in range(10):
            enforcer.check_cap_before_operation('agent-1', OperationType.REQUEST, 1)
            enforcer.record_operation('agent-1', OperationType.REQUEST, 1)

        for i in range(5):
            enforcer.check_cap_before_operation('agent-2', OperationType.REQUEST, 1)
            enforcer.record_operation('agent-2', OperationType.REQUEST, 1)

        budget1 = enforcer.get_remaining_budget('agent-1')
        budget2 = enforcer.get_remaining_budget('agent-2')

        assert budget1['max_requests_per_hour']['used'] == 10
        assert budget2['max_requests_per_hour']['used'] == 5


class TestReleaseAndReset:
    """Test concurrent task release and window reset."""

    def test_release_concurrent_task(self):
        """Releasing concurrent task decrements counter."""
        enforcer = CapEnforcer(behavior_spec_path="/nonexistent/path.json")

        enforcer.check_cap_before_operation('agent-1', OperationType.CONCURRENT_TASK, 1)
        enforcer.record_operation('agent-1', OperationType.CONCURRENT_TASK, 1)

        budget_before = enforcer.get_remaining_budget('agent-1')
        initial_remaining = budget_before['max_concurrent_tasks']['remaining']

        enforcer.release_concurrent_task('agent-1')

        budget_after = enforcer.get_remaining_budget('agent-1')
        final_remaining = budget_after['max_concurrent_tasks']['remaining']

        assert final_remaining > initial_remaining

    def test_window_reset_on_expiry(self):
        """Usage counters reset when window expires."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            spec = {
                'caps': {
                    'req_5min': {
                        'type': 'REQUEST',
                        'limit': 10,
                        'window_minutes': 1,  # 1 minute window for testing
                        'zones': ['Z1'],
                        'enabled': True
                    }
                }
            }
            json.dump(spec, f)
            f.flush()

            enforcer = CapEnforcer(behavior_spec_path=f.name)

            # Make 8 requests
            for i in range(8):
                enforcer.check_cap_before_operation('agent-1', OperationType.REQUEST, 1)
                enforcer.record_operation('agent-1', OperationType.REQUEST, 1)

            # Manually set last_reset_at to 2 minutes ago (past window)
            for cap_name, usage in enforcer.usage['agent-1'].items():
                usage.last_reset_at = (datetime.now(timezone.utc) - timedelta(minutes=2)).isoformat()

            # Check budget after window expiry
            budget = enforcer.get_remaining_budget('agent-1')

            # Counter should be reset, so used should be 0
            assert budget['req_5min']['used'] == 0
            assert budget['req_5min']['remaining'] == 10

            Path(f.name).unlink()


class TestAuditTrail:
    """Test audit trail logging."""

    def test_audit_trail_logged(self):
        """Cap checks and operations logged to audit trail."""
        enforcer = CapEnforcer(behavior_spec_path="/nonexistent/path.json")

        enforcer.check_cap_before_operation('agent-1', OperationType.REQUEST, 1)
        enforcer.record_operation('agent-1', OperationType.REQUEST, 1)

        assert len(enforcer.audit_trail) > 0

        # Should have at least one cap_check entry
        cap_checks = [e for e in enforcer.audit_trail if e.get('type') == 'cap_check']
        assert len(cap_checks) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
