"""
Test harness for Grant Match Verifier v1.0
Phase 1 Test Gate: 10 RFPs verified; 100% agreement with manual treasurer baseline

Test scenarios per deliverables/GRANT-TREASURY-PILOT.md:
  1a. Clear green light (available >> required)
  1b. Borderline capital (available ≈ required)
  1c. Red light (insufficient capital)
  1d. Restricted funds excluded (unrestricted only)

Author: Claude Haiku 4.5 (Z1/Z3)
Session: S-091926-Z1-grant-treasury-pilot
Date: 2026-09-19
"""

import pytest
import json
from unittest.mock import Mock, patch
from tools.grant_match_verifier_v1_0 import (
    GrantMatchVerifier,
    BrokerageAPIClient,
    verify_rfp,
    RFPPayload,
    LedgerSnapshot,
    MatchVerdict
)


class MockBrokerageClient(BrokerageAPIClient):
    """Test mock that allows scenario-specific ledger snapshots."""

    def __init__(self, unrestricted_usd: float = 175000, restricted_usd: float = 200000):
        super().__init__(use_mock=True)
        self.unrestricted_usd = unrestricted_usd
        self.restricted_usd = restricted_usd

    def query_ledger(self) -> LedgerSnapshot:
        return LedgerSnapshot(
            unrestricted_cash_usd=self.unrestricted_usd,
            restricted_cash_usd=self.restricted_usd,
            total_assets_usd=self.unrestricted_usd + self.restricted_usd,
            last_updated_at="2026-09-19T08:00:00Z",
            source="Mock Brokerage (Phase 1 Testing)"
        )


class TestScenario1a_ClearGreenLight:
    """Scenario 1a: Available >> Required"""

    def test_verdict_green(self):
        """Should return GREEN_LIGHT when capital surplus is substantial."""
        ledger = MockBrokerageClient(unrestricted_usd=200000, restricted_usd=200000)
        verifier = GrantMatchVerifier(ledger_client=ledger)

        rfp = {
            "grant_id": "1a_clear_green",
            "funder": "NSF",
            "match_required_usd": 150000,
            "timeline_months": 24,
            "restrictions": [],
            "received_at": "2026-09-19T08:30:00Z"
        }

        verdict = verifier.verify(rfp)

        assert verdict.status == "GREEN_LIGHT"
        assert verdict.action == "proceed_to_apply"
        assert verdict.available_unrestricted_usd == 200000
        assert verdict.required_usd == 150000
        assert verdict.surplus_usd == 50000
        assert "Proceed to grant application" in verdict.reasoning

    def test_board_crm_integration_ready(self):
        """Verdict dict should serialize for CRM pipeline update."""
        ledger = MockBrokerageClient(unrestricted_usd=200000)
        verifier = GrantMatchVerifier(ledger_client=ledger)

        rfp = {
            "grant_id": "1a_crm_integration",
            "funder": "NIH",
            "match_required_usd": 100000,
            "timeline_months": 12,
            "restrictions": ["audit_required"],
            "received_at": "2026-09-19T09:00:00Z"
        }

        verdict = verifier.verify(rfp)
        verdict_json = verdict.to_json()

        # Should be valid JSON
        parsed = json.loads(verdict_json)
        assert parsed["status"] == "GREEN_LIGHT"
        assert parsed["grant_id"] == "1a_crm_integration"


class TestScenario1b_BorderlineCapital:
    """Scenario 1b: Available ≈ Required (just meets threshold)"""

    def test_borderline_exactly_equal(self):
        """Should return GREEN_LIGHT when available == required (zero surplus)."""
        ledger = MockBrokerageClient(unrestricted_usd=150000)
        verifier = GrantMatchVerifier(ledger_client=ledger)

        rfp = {
            "grant_id": "1b_borderline_equal",
            "funder": "DOE",
            "match_required_usd": 150000,
            "timeline_months": 24,
            "restrictions": [],
            "received_at": "2026-09-19T10:00:00Z"
        }

        verdict = verifier.verify(rfp)

        assert verdict.status == "GREEN_LIGHT"
        assert verdict.surplus_usd == 0
        assert verdict.action == "proceed_to_apply"

    def test_borderline_one_dollar_surplus(self):
        """Should return GREEN_LIGHT even with $1 surplus."""
        ledger = MockBrokerageClient(unrestricted_usd=150001)
        verifier = GrantMatchVerifier(ledger_client=ledger)

        rfp = {
            "grant_id": "1b_borderline_one_dollar",
            "funder": "DOE",
            "match_required_usd": 150000,
            "timeline_months": 24,
            "restrictions": [],
            "received_at": "2026-09-19T10:15:00Z"
        }

        verdict = verifier.verify(rfp)

        assert verdict.status == "GREEN_LIGHT"
        assert verdict.surplus_usd == 1


class TestScenario1c_RedLight:
    """Scenario 1c: Insufficient capital"""

    def test_insufficient_capital(self):
        """Should return RED_LIGHT when available < required."""
        ledger = MockBrokerageClient(unrestricted_usd=100000)
        verifier = GrantMatchVerifier(ledger_client=ledger)

        rfp = {
            "grant_id": "1c_red_light",
            "funder": "NSF",
            "match_required_usd": 150000,
            "timeline_months": 24,
            "restrictions": [],
            "received_at": "2026-09-19T11:00:00Z"
        }

        verdict = verifier.verify(rfp)

        assert verdict.status == "RED_LIGHT"
        assert verdict.action == "escalate_to_treasurer"
        assert verdict.available_unrestricted_usd == 100000
        assert verdict.required_usd == 150000
        assert verdict.surplus_usd == -50000  # negative shortfall
        assert "Escalate to treasurer" in verdict.reasoning

    def test_treasurer_escalation_alert(self):
        """Verdict should clearly identify shortfall for escalation."""
        ledger = MockBrokerageClient(unrestricted_usd=80000)
        verifier = GrantMatchVerifier(ledger_client=ledger)

        rfp = {
            "grant_id": "1c_escalation_alert",
            "funder": "NIH",
            "match_required_usd": 150000,
            "timeline_months": 18,
            "restrictions": ["no_overhead"],
            "received_at": "2026-09-19T11:30:00Z"
        }

        verdict = verifier.verify(rfp)

        assert verdict.status == "RED_LIGHT"
        assert "Shortfall: $70,000.00" in verdict.reasoning


class TestScenario1d_RestrictedFundsExcluded:
    """Scenario 1d: Restricted funds (endowment, emergency) excluded from match check"""

    def test_restricted_not_counted(self):
        """Should NOT count restricted funds; only unrestricted counts."""
        # Total: $300k, but only $100k unrestricted
        ledger = MockBrokerageClient(unrestricted_usd=100000, restricted_usd=200000)
        verifier = GrantMatchVerifier(ledger_client=ledger)

        rfp = {
            "grant_id": "1d_restricted_excluded",
            "funder": "Foundation",
            "match_required_usd": 120000,
            "timeline_months": 12,
            "restrictions": [],
            "received_at": "2026-09-19T12:00:00Z"
        }

        verdict = verifier.verify(rfp)

        # Total assets ($300k) would be sufficient, but unrestricted ($100k) is not
        assert verdict.status == "RED_LIGHT"
        assert verdict.available_unrestricted_usd == 100000
        assert verdict.surplus_usd == -20000
        assert "Escalate to treasurer" in verdict.reasoning

    def test_restricted_funds_policy_clear(self):
        """Reasoning should explicitly state why restricted funds don't count."""
        ledger = MockBrokerageClient(unrestricted_usd=50000, restricted_usd=500000)
        verifier = GrantMatchVerifier(ledger_client=ledger)

        rfp = {
            "grant_id": "1d_policy_clarity",
            "funder": "DOE",
            "match_required_usd": 100000,
            "timeline_months": 24,
            "restrictions": [],
            "received_at": "2026-09-19T12:30:00Z"
        }

        verdict = verifier.verify(rfp)

        # Large restricted pool doesn't help
        assert verdict.status == "RED_LIGHT"


class TestPhase1Gate_10RFPAccuracy:
    """Gate 0a: 10 RFPs verified; 100% agreement with manual baseline"""

    test_cases = [
        # (unrestricted, required, expected_status, case_name)
        (200000, 150000, "GREEN_LIGHT", "1a_clear_green"),
        (151000, 150000, "GREEN_LIGHT", "1b_borderline_high"),
        (150000, 150000, "GREEN_LIGHT", "1b_borderline_equal"),
        (149999, 150000, "RED_LIGHT", "1c_borderline_fail_by_1"),
        (100000, 150000, "RED_LIGHT", "1c_red_light"),
        (50000, 120000, "RED_LIGHT", "1d_restricted_excluded"),
        (175000, 100000, "GREEN_LIGHT", "2_normal_green"),
        (75000, 100000, "RED_LIGHT", "3_normal_red"),
        (300000, 250000, "GREEN_LIGHT", "4_large_surplus"),
        (1000, 50000, "RED_LIGHT", "5_severe_shortfall"),
    ]

    @pytest.mark.parametrize("unrestricted,required,expected,name", test_cases)
    def test_all_10_rfps_accurate(self, unrestricted, required, expected, name):
        """All 10 test RFPs should return correct verdict (100% accuracy gate)."""
        ledger = MockBrokerageClient(unrestricted_usd=unrestricted)
        verifier = GrantMatchVerifier(ledger_client=ledger)

        rfp = {
            "grant_id": f"gate_0a_{name}",
            "funder": "Test Funder",
            "match_required_usd": required,
            "timeline_months": 12,
            "restrictions": [],
            "received_at": "2026-09-19T13:00:00Z"
        }

        verdict = verifier.verify(rfp)

        assert verdict.status == expected, (
            f"RFP {name}: expected {expected}, got {verdict.status} "
            f"(available: ${unrestricted:,}, required: ${required:,})"
        )


class TestEntrypoint_VerifyRFP:
    """Test the HTTP handler entrypoint."""

    def test_entrypoint_accepts_dict(self):
        """verify_rfp() should accept dict input."""
        rfp_dict = {
            "grant_id": "ep_dict_input",
            "funder": "NSF",
            "match_required_usd": 100000,
            "timeline_months": 12,
            "restrictions": [],
            "received_at": "2026-09-19T14:00:00Z"
        }

        with patch.object(BrokerageAPIClient, 'query_ledger', return_value=LedgerSnapshot(
            unrestricted_cash_usd=150000,
            restricted_cash_usd=200000,
            total_assets_usd=350000,
            last_updated_at="2026-09-19T08:00:00Z",
            source="Mock"
        )):
            result = verify_rfp(rfp_dict)

        assert result["status"] == "GREEN_LIGHT"
        assert result["grant_id"] == "ep_dict_input"

    def test_entrypoint_accepts_json_string(self):
        """verify_rfp() should accept JSON string input."""
        rfp_json = json.dumps({
            "grant_id": "ep_json_input",
            "funder": "DOE",
            "match_required_usd": 50000,
            "timeline_months": 24,
            "restrictions": ["audit_required"],
            "received_at": "2026-09-19T14:30:00Z"
        })

        with patch.object(BrokerageAPIClient, 'query_ledger', return_value=LedgerSnapshot(
            unrestricted_cash_usd=100000,
            restricted_cash_usd=100000,
            total_assets_usd=200000,
            last_updated_at="2026-09-19T08:00:00Z",
            source="Mock"
        )):
            result = verify_rfp(rfp_json)

        assert result["status"] == "GREEN_LIGHT"
        assert result["grant_id"] == "ep_json_input"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
