"""
Grant Matching Engine v1.0
Phase 1B: Nonprofit Grant Discovery & Matching Service

Matches nonprofit profiles to grant opportunities using keyword fit, geography,
budget, and timeline scoring. Integrates capacity assessment via verify_rfp().

Author: Claude Haiku 4.5 (Z1/Z3)
Session: S-091926-Z1-grant-treasury-pilot
Date: 2026-09-19
"""

import json
import logging
from typing import TypedDict, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict
from collections import Counter

logger = logging.getLogger(__name__)


class NonprofitProfile(TypedDict):
    """Nonprofit organization profile."""
    nonprofit_id: str
    name: str
    ein: str
    annual_revenue_usd: float
    mission_keywords: list[str]
    service_geography: list[str]
    restrictions: list[str]
    recent_grants: Optional[list[dict]]
    unrestricted_capital_usd: Optional[float]


@dataclass
class MatchScore:
    """Scoring breakdown for a grant match."""
    grant_id: str
    funder: str
    amount_usd: float
    match_required_usd: float
    deadline: str
    days_until_deadline: int
    keyword_fit: float
    geography_fit: float
    budget_fit: float
    timeline_fit: float
    combined_score: float
    capacity_verdict: Optional[str]
    capacity_shortfall_usd: Optional[float]

    def to_dict(self):
        return asdict(self)


class GrantMatchVerifierClient:
    """Client to call verify_rfp() for capacity assessment."""

    def __init__(self):
        self.use_mock = True

    def verify_capacity(self, nonprofit_unrestricted_usd: float, grant_match_required_usd: float) -> dict:
        """Check if nonprofit has sufficient capital for grant match."""
        if self.use_mock:
            return self._mock_verify(nonprofit_unrestricted_usd, grant_match_required_usd)
        raise NotImplementedError("Real verify_rfp() API call in Phase 2B")

    def _mock_verify(self, unrestricted_usd: float, match_required_usd: float) -> dict:
        """Mock verify_rfp() response."""
        surplus = unrestricted_usd - match_required_usd
        if surplus >= 0:
            return {
                "status": "GREEN_LIGHT",
                "action": "proceed_to_apply",
                "available_unrestricted_usd": unrestricted_usd,
                "required_usd": match_required_usd,
                "surplus_usd": surplus,
            }
        else:
            return {
                "status": "RED_LIGHT",
                "action": "fundraise_then_apply",
                "available_unrestricted_usd": unrestricted_usd,
                "required_usd": match_required_usd,
                "surplus_usd": surplus,
            }


class GrantMatcher:
    """Core matching engine with scoring algorithm."""

    def __init__(self):
        self.capacity_verifier = GrantMatchVerifierClient()
        self.weights = {
            "keyword_fit": 0.4,
            "geography_fit": 0.3,
            "budget_fit": 0.2,
            "timeline_fit": 0.1,
        }

    def score_match(self, grant, nonprofit_profile: NonprofitProfile) -> MatchScore:
        """Score a single grant-nonprofit match."""
        keyword_score = self._score_keyword_fit(
            nonprofit_profile["mission_keywords"],
            grant.focus_areas,
        )
        geography_score = self._score_geography_fit(
            nonprofit_profile["service_geography"],
            grant.eligible_states,
        )
        budget_score = self._score_budget_fit(
            nonprofit_profile["annual_revenue_usd"],
            grant.amount_usd,
        )
        timeline_score = self._score_timeline_fit(grant.days_until_deadline)

        combined_score = (
            (keyword_score * self.weights["keyword_fit"])
            + (geography_score * self.weights["geography_fit"])
            + (budget_score * self.weights["budget_fit"])
            + (timeline_score * self.weights["timeline_fit"])
        )

        # Capacity check (if unrestricted capital provided)
        capacity_verdict = None
        capacity_shortfall_usd = None
        if nonprofit_profile.get("unrestricted_capital_usd") is not None:
            capacity_check = self.capacity_verifier.verify_capacity(
                nonprofit_profile["unrestricted_capital_usd"],
                grant.match_required_usd,
            )
            capacity_verdict = capacity_check["status"]
            if capacity_check.get("surplus_usd", 0) < 0:
                capacity_shortfall_usd = abs(capacity_check["surplus_usd"])

        return MatchScore(
            grant_id=grant.grant_id,
            funder=grant.funder,
            amount_usd=grant.amount_usd,
            match_required_usd=grant.match_required_usd,
            deadline=grant.deadline,
            days_until_deadline=grant.days_until_deadline,
            keyword_fit=keyword_score,
            geography_fit=geography_score,
            budget_fit=budget_score,
            timeline_fit=timeline_score,
            combined_score=combined_score,
            capacity_verdict=capacity_verdict,
            capacity_shortfall_usd=capacity_shortfall_usd,
        )

    def _score_keyword_fit(self, nonprofit_keywords: list[str], grant_areas: list[str]) -> float:
        """Score keyword overlap between nonprofit mission and grant focus areas."""
        if not nonprofit_keywords or not grant_areas:
            return 0.0

        nonprofit_set = set(k.lower().replace(" ", "_") for k in nonprofit_keywords)
        grant_set = set(a.lower().replace(" ", "_") for a in grant_areas)

        # Count partial matches: if nonprofit keyword is a substring of grant area
        matches = 0
        for np_keyword in nonprofit_set:
            for grant_area in grant_set:
                if np_keyword in grant_area or grant_area in np_keyword:
                    matches += 1
                    break

        if not nonprofit_set and not grant_set:
            return 0.0

        # Score based on proportion of nonprofit keywords that match something in grant
        keyword_match_ratio = matches / len(nonprofit_set) if nonprofit_set else 0.0

        # Boost score if any exact matches exist
        exact_intersection = nonprofit_set & grant_set
        if exact_intersection:
            keyword_match_ratio = min(1.0, keyword_match_ratio + 0.3)

        return min(1.0, keyword_match_ratio)

    def _score_geography_fit(self, nonprofit_states: list[str], grant_states: list[str]) -> float:
        """Score geographic overlap."""
        if not nonprofit_states or not grant_states:
            return 0.0

        if "all" in grant_states:
            return 1.0

        nonprofit_set = set(s.upper() for s in nonprofit_states)
        grant_set = set(s.upper() for s in grant_states)

        overlap = nonprofit_set & grant_set
        if not overlap:
            return 0.0

        if len(overlap) >= len(nonprofit_set):
            return 1.0
        else:
            return len(overlap) / len(nonprofit_set)

    def _score_budget_fit(self, nonprofit_revenue: float, grant_amount: float) -> float:
        """Score budget appropriateness."""
        if nonprofit_revenue <= 0 or grant_amount <= 0:
            return 0.5

        ratio = grant_amount / nonprofit_revenue

        if 0.5 <= ratio <= 2.0:
            return 1.0
        elif 0.25 <= ratio < 0.5:
            return 0.9
        elif 2.0 < ratio <= 4.0:
            return 0.8
        elif 0.1 <= ratio < 0.25:
            return 0.7
        elif 4.0 < ratio <= 10.0:
            return 0.5
        elif ratio >= 10.0:
            return 0.3
        else:
            return 0.4

    def _score_timeline_fit(self, days_until_deadline: int) -> float:
        """Score deadline urgency and feasibility."""
        if days_until_deadline <= 0:
            return 0.0
        elif days_until_deadline >= 90:
            return 1.0
        elif days_until_deadline >= 60:
            return 0.9
        elif days_until_deadline >= 30:
            return 0.7
        elif days_until_deadline >= 15:
            return 0.4
        else:
            return 0.1

    def rank_matches(
        self,
        grants: list,
        nonprofit_profile: NonprofitProfile,
        top_n: Optional[int] = None,
    ) -> List[MatchScore]:
        """Score and rank all grants for a nonprofit."""
        scores = []
        for grant in grants:
            try:
                score = self.score_match(grant, nonprofit_profile)
                scores.append(score)
            except Exception as e:
                logger.error(f"Error scoring grant {grant.grant_id}: {e}")

        scores.sort(key=lambda s: s.combined_score, reverse=True)

        if top_n:
            return scores[:top_n]
        return scores


def search_grants(
    nonprofit_profile: NonprofitProfile,
    all_grants: list,
    top_n: int = 15,
    min_score: float = 0.0,
) -> dict:
    """
    Search and rank grants for a nonprofit.

    Args:
        nonprofit_profile: Nonprofit organization data
        all_grants: List of Grant objects from data loader
        top_n: Return top N matches
        min_score: Filter out matches below this score

    Returns:
        Search results dict with ranked matches and metadata
    """
    matcher = GrantMatcher()

    matches = matcher.rank_matches(all_grants, nonprofit_profile, top_n=top_n * 2)
    matches = [m for m in matches if m.combined_score >= min_score][:top_n]

    return {
        "nonprofit_id": nonprofit_profile["nonprofit_id"],
        "nonprofit_name": nonprofit_profile["name"],
        "matches": [m.to_dict() for m in matches],
        "total_matches_ranked": len(matches),
        "search_timestamp": datetime.utcnow().isoformat() + "Z",
        "filters_applied": {
            "top_n": top_n,
            "min_score": min_score,
        },
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    from tools.grant_data_loader_v1_0 import MultiSourceGrantSearch

    sample_nonprofit = NonprofitProfile(
        nonprofit_id="org_test_001",
        name="Example Education Nonprofit",
        ein="12-3456789",
        annual_revenue_usd=500000,
        mission_keywords=["education", "STEM", "underserved"],
        service_geography=["CA", "OR"],
        restrictions=["IRS_501c3_only"],
        recent_grants=[{"funder": "NIH", "amount_usd": 250000, "year": 2025}],
        unrestricted_capital_usd=100000,
    )

    search = MultiSourceGrantSearch()
    all_grants = search.search_all(
        focus_areas=["education", "STEM_education"],
        min_amount=50000,
        eligible_states=["CA", "OR", "WA", "TX", "NY"],
    )

    results = search_grants(sample_nonprofit, all_grants, top_n=10, min_score=0.3)

    print("\n=== GRANT SEARCH RESULTS ===\n")
    print(f"Nonprofit: {results['nonprofit_name']}")
    print(f"Total matches: {results['total_matches_ranked']}\n")

    for i, match in enumerate(results["matches"][:5], 1):
        print(f"{i}. {match['funder']} (Score: {match['combined_score']:.2f})")
        print(f"   Amount: ${match['amount_usd']:,.0f} | Match Required: ${match['match_required_usd']:,.0f}")
        print(f"   Deadline: {match['days_until_deadline']} days | Capacity: {match['capacity_verdict']}")
        print()
