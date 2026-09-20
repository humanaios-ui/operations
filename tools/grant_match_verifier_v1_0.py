"""
Grant Pre-Award Match Verifier v1.0
Phase 1 of Q-GRANT-TREASURY-ORCHESTRATION-PILOT-01

Verifies available unrestricted capital against incoming grant RFP requirements.
Provides GREEN_LIGHT (proceed to apply) or RED_LIGHT (escalate to treasurer) verdict.

API Endpoint: POST /api/match-verify
Input: RFP webhook payload
Output: Verdict (GREEN_LIGHT | RED_LIGHT) with capital summary
Test Gate: 10 RFPs verified; 100% agreement with manual treasurer baseline

Author: Claude Haiku 4.5 (Z1/Z3)
Session: S-091926-Z1-grant-treasury-pilot
Date: 2026-09-19
"""

import json
import logging
from typing import TypedDict, Literal
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


class RFPPayload(TypedDict):
    """Incoming RFP webhook payload schema."""
    grant_id: str
    funder: str
    match_required_usd: float
    timeline_months: int
    restrictions: list[str]  # e.g., ["no_overhead", "audit_required"]
    received_at: str  # ISO 8601 timestamp


class LedgerSnapshot(TypedDict):
    """Live brokerage ledger query response."""
    unrestricted_cash_usd: float
    restricted_cash_usd: float  # endowment, emergency reserves
    total_assets_usd: float
    last_updated_at: str  # ISO 8601 timestamp
    source: str  # "Infinite Giving" | "Schwab" | "Local Bank"


@dataclass
class MatchVerdict:
    """Match verification result."""
    grant_id: str
    status: Literal["GREEN_LIGHT", "RED_LIGHT"]
    available_unrestricted_usd: float
    required_usd: float
    surplus_usd: float  # negative if insufficient
    verdict_timestamp: str  # ISO 8601
    action: Literal["proceed_to_apply", "escalate_to_treasurer"]
    reasoning: str

    def to_dict(self):
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class BrokerageAPIClient:
    """Mock/real brokerage API client for ledger queries.

    In production, this would call real APIs (Infinite Giving, Schwab, etc.).
    For Phase 1 testing, uses mock responses.
    """

    def __init__(self, api_url: str = None, api_key: str = None, use_mock: bool = True):
        self.api_url = api_url
        self.api_key = api_key
        self.use_mock = use_mock

    def query_ledger(self) -> LedgerSnapshot:
        """Query live brokerage ledger for current cash position.

        Returns:
            LedgerSnapshot: Current unrestricted/restricted/total balances
        """
        if self.use_mock:
            return self._mock_ledger_response()

        # TODO: Implement real API call
        # response = requests.get(self.api_url, headers={"Authorization": f"Bearer {self.api_key}"})
        # return LedgerSnapshot(**response.json())
        raise NotImplementedError("Real API client not yet implemented")

    def _mock_ledger_response(self) -> LedgerSnapshot:
        """Return mock ledger data for testing."""
        return LedgerSnapshot(
            unrestricted_cash_usd=175000.00,
            restricted_cash_usd=200000.00,
            total_assets_usd=375000.00,
            last_updated_at=datetime.utcnow().isoformat() + "Z",
            source="Mock Brokerage (Phase 1 Testing)"
        )


class GrantMatchVerifier:
    """Core match verification engine.

    Implements the hard gate rule: available_unrestricted >= match_required
    Only unrestricted capital counts. Restricted (endowment, emergency reserves) excluded.
    """

    def __init__(self, ledger_client: BrokerageAPIClient = None):
        self.ledger_client = ledger_client or BrokerageAPIClient(use_mock=True)

    def verify(self, rfp: RFPPayload) -> MatchVerdict:
        """Verify RFP against live capital position.

        Args:
            rfp: Incoming RFP webhook payload

        Returns:
            MatchVerdict: GREEN_LIGHT | RED_LIGHT verdict with capital summary
        """
        # Query current ledger state
        ledger = self.ledger_client.query_ledger()

        # Extract decision variables
        grant_id = rfp["grant_id"]
        match_required = rfp["match_required_usd"]
        available_unrestricted = ledger["unrestricted_cash_usd"]

        # Apply hard gate: unrestricted capital must cover match requirement
        surplus = available_unrestricted - match_required

        if surplus >= 0:
            status = "GREEN_LIGHT"
            action = "proceed_to_apply"
            reasoning = (
                f"Unrestricted capital ${available_unrestricted:,.2f} covers required match ${match_required:,.2f}. "
                f"Surplus: ${surplus:,.2f}. Proceed to grant application."
            )
        else:
            status = "RED_LIGHT"
            action = "escalate_to_treasurer"
            shortfall = abs(surplus)
            reasoning = (
                f"Insufficient unrestricted capital. Required: ${match_required:,.2f}, "
                f"Available: ${available_unrestricted:,.2f}, Shortfall: ${shortfall:,.2f}. "
                f"Escalate to treasurer for override/policy review."
            )

        verdict = MatchVerdict(
            grant_id=grant_id,
            status=status,
            available_unrestricted_usd=available_unrestricted,
            required_usd=match_required,
            surplus_usd=surplus,
            verdict_timestamp=datetime.utcnow().isoformat() + "Z",
            action=action,
            reasoning=reasoning
        )

        logger.info(
            f"Match verdict for {grant_id}: {status} "
            f"(available: ${available_unrestricted:,.2f}, required: ${match_required:,.2f})"
        )

        return verdict


def verify_rfp(rfp_payload: dict) -> dict:
    """Entrypoint for HTTP handler / webhook receiver.

    Args:
        rfp_payload: RFP webhook data (dict or JSON string)

    Returns:
        dict: Verdict as JSON-serializable dict
    """
    if isinstance(rfp_payload, str):
        rfp_payload = json.loads(rfp_payload)

    verifier = GrantMatchVerifier()
    verdict = verifier.verify(rfp_payload)

    return verdict.to_dict()


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    sample_rfp = {
        "grant_id": "rfp_example_2026_0819",
        "funder": "NIH",
        "match_required_usd": 150000,
        "timeline_months": 24,
        "restrictions": ["no_overhead", "audit_required"],
        "received_at": "2026-09-19T08:30:00Z"
    }

    result = verify_rfp(sample_rfp)
    print(json.dumps(result, indent=2))
