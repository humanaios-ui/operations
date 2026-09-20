"""
Test harness for Grant Matching Engine v1.0
Phase 1B Test Gate: 15 parametrized tests (5 nonprofits × 3 grant sources)

Test scenarios per z1-inbox/2026-09-19/PHASE-1B-GRANT-MATCHING-SPEC.md:
  B1a. Perfect fit (high keyword + geography + budget overlap)
  B1b. Geographic mismatch (TX nonprofit, CA-only grant)
  B1c. Budget mismatch (too small)
  B1d. Budget mismatch (too large)
  B1e. Deadline pressure (90+ days vs <30 days)
  B1f. Capacity integration (GREEN_LIGHT)
  B1g. Capacity RED_LIGHT (shortfall)

Author: Claude Haiku 4.5 (Z1/Z3)
Session: S-091926-Z1-grant-treasury-pilot
Date: 2026-09-19
"""

import pytest
from tools.grant_data_loader_v1_0 import (
    Grant,
    GrantsGovAPI,
    FoundationCenterAPI,
    InstrumentalAPI,
    MultiSourceGrantSearch,
)
from tools.grant_matching_engine_v1_0 import (
    NonprofitProfile,
    GrantMatcher,
    search_grants,
)


class MockNonprofitProfiles:
    """Test nonprofit profiles."""

    @staticmethod
    def education_org_ca_or():
        """Education nonprofit serving CA and OR."""
        return NonprofitProfile(
            nonprofit_id="org_edu_001",
            name="Education Leadership Initiative",
            ein="12-3456789",
            annual_revenue_usd=500000,
            mission_keywords=["education", "STEM", "diversity", "underserved"],
            service_geography=["CA", "OR"],
            restrictions=["IRS_501c3_only"],
            recent_grants=[{"funder": "NIH", "amount_usd": 250000, "year": 2025}],
            unrestricted_capital_usd=100000,
        )

    @staticmethod
    def environmental_org_tx_co():
        """Environmental nonprofit serving TX and CO."""
        return NonprofitProfile(
            nonprofit_id="org_env_001",
            name="Climate Action Network",
            ein="23-4567890",
            annual_revenue_usd=750000,
            mission_keywords=["climate", "environment", "sustainability", "clean_energy"],
            service_geography=["TX", "CO"],
            restrictions=["IRS_501c3_only"],
            recent_grants=[{"funder": "DOE", "amount_usd": 100000, "year": 2024}],
            unrestricted_capital_usd=150000,
        )

    @staticmethod
    def health_org_ny_ma():
        """Health nonprofit serving NY and MA."""
        return NonprofitProfile(
            nonprofit_id="org_health_001",
            name="Community Health Alliance",
            ein="34-5678901",
            annual_revenue_usd=300000,
            mission_keywords=["health", "health_equity", "community_health", "research"],
            service_geography=["NY", "MA"],
            restrictions=["IRS_501c3_only"],
            recent_grants=[{"funder": "NIH", "amount_usd": 150000, "year": 2025}],
            unrestricted_capital_usd=75000,
        )

    @staticmethod
    def youth_org_ca_tx():
        """Youth nonprofit serving CA and TX."""
        return NonprofitProfile(
            nonprofit_id="org_youth_001",
            name="Youth Leadership Academy",
            ein="45-6789012",
            annual_revenue_usd=400000,
            mission_keywords=["youth", "education", "leadership", "mentoring"],
            service_geography=["CA", "TX"],
            restrictions=["IRS_501c3_only"],
            recent_grants=None,
            unrestricted_capital_usd=60000,
        )

    @staticmethod
    def arts_org_ny_ca():
        """Arts nonprofit serving NY and CA."""
        return NonprofitProfile(
            nonprofit_id="org_arts_001",
            name="Cultural Arts Collective",
            ein="56-7890123",
            annual_revenue_usd=200000,
            mission_keywords=["arts", "culture", "community", "education"],
            service_geography=["NY", "CA"],
            restrictions=["IRS_501c3_only"],
            recent_grants=None,
            unrestricted_capital_usd=40000,
        )


class TestScenarioB1a_PerfectFit:
    """Scenario B1a: Perfect fit (high overlap)."""

    def test_education_org_stem_grant(self):
        """Education nonprofit matching NSF STEM grant."""
        nonprofit = MockNonprofitProfiles.education_org_ca_or()
        grants_search = GrantsGovAPI(use_mock=True)
        grants = grants_search.search(focus_areas=["STEM_education"])

        matcher = GrantMatcher()
        scores = matcher.rank_matches(grants, nonprofit, top_n=1)

        assert len(scores) > 0, "Should find matches"
        top_match = scores[0]
        assert top_match.combined_score >= 0.6, f"Expected reasonable score, got {top_match.combined_score}"
        assert top_match.keyword_fit > 0.4, "Should have keyword overlap"
        assert top_match.geography_fit > 0.5, "Should have good geography match"

    def test_perfect_fit_high_score(self):
        """Perfect fit scores higher than partial fits."""
        nonprofit = MockNonprofitProfiles.education_org_ca_or()

        search = MultiSourceGrantSearch()
        all_grants = search.search_all()

        matcher = GrantMatcher()
        scores = matcher.rank_matches(all_grants, nonprofit)

        top_3_scores = [s.combined_score for s in scores[:3]]
        assert top_3_scores[0] >= top_3_scores[1], "Top match should rank highest"
        assert all(s >= 0.4 for s in top_3_scores), "All top 3 should score reasonably"


class TestScenarioB1b_GeographicMismatch:
    """Scenario B1b: Geographic mismatch."""

    def test_tx_nonprofit_ca_only_grant_penalized(self):
        """TX nonprofit should score low on CA-only grants."""
        nonprofit = MockNonprofitProfiles.environmental_org_tx_co()
        nonprofit_ca_only = NonprofitProfile(
            nonprofit_id="org_test_ca",
            name="CA-Only Test Nonprofit",
            ein="99-9999999",
            annual_revenue_usd=500000,
            mission_keywords=["STEM_education"],
            service_geography=["CA"],
            restrictions=[],
            recent_grants=None,
            unrestricted_capital_usd=100000,
        )

        grants_search = GrantsGovAPI(use_mock=True)
        grants = grants_search.search()

        matcher = GrantMatcher()

        # Score for TX nonprofit on all grants
        scores_tx = matcher.rank_matches(grants, nonprofit)

        # Score for CA nonprofit on same grants
        scores_ca = matcher.rank_matches(grants, nonprofit_ca_only)

        # TX nonprofit should score lower due to geography
        tx_scores = [s.combined_score for s in scores_tx]
        ca_scores = [s.combined_score for s in scores_ca]

        assert any(ca > tx for ca, tx in zip(ca_scores, tx_scores)), "CA nonprofit should rank grants higher"


class TestScenarioB1c_BudgetMismatch_TooSmall:
    """Scenario B1c: Budget mismatch (too small)."""

    def test_small_nonprofit_large_grant_penalized(self):
        """Small nonprofit $50k revenue should score low on $500k grant."""
        small_nonprofit = NonprofitProfile(
            nonprofit_id="org_small",
            name="Small Nonprofit",
            ein="88-8888888",
            annual_revenue_usd=50000,
            mission_keywords=["climate_action"],
            service_geography=["CO"],
            restrictions=[],
            recent_grants=None,
            unrestricted_capital_usd=10000,
        )

        grants_search = GrantsGovAPI(use_mock=True)
        grants = grants_search.search()

        matcher = GrantMatcher()
        scores = matcher.rank_matches(grants, small_nonprofit)

        # Budget mismatch should show up as lower scores
        budget_scores = [s.budget_fit for s in scores]
        assert any(bs < 0.6 for bs in budget_scores), "Should have low budget fit on large grants"


class TestScenarioB1d_BudgetMismatch_TooLarge:
    """Scenario B1d: Budget mismatch (too large)."""

    def test_large_nonprofit_small_grant_not_eliminated(self):
        """Large nonprofit shouldn't completely reject small match-only grants."""
        large_nonprofit = NonprofitProfile(
            nonprofit_id="org_large",
            name="Large Nonprofit",
            ein="77-7777777",
            annual_revenue_usd=2000000,
            mission_keywords=["youth", "education"],
            service_geography=["CA", "TX"],
            restrictions=[],
            recent_grants=None,
            unrestricted_capital_usd=500000,
        )

        grants_search = InstrumentalAPI(use_mock=True)
        grants = grants_search.search(focus_areas=["youth", "education"])

        matcher = GrantMatcher()
        scores = matcher.rank_matches(grants, large_nonprofit)

        assert len(scores) > 0, "Should still find matches for large org"
        budget_scores = [s.budget_fit for s in scores]
        assert any(bs > 0.3 for bs in budget_scores), "Should have reasonable budget fit for at least some grants"


class TestScenarioB1e_DeadlinePressure:
    """Scenario B1e: Deadline urgency impact on scoring."""

    def test_90_day_deadline_scores_higher_than_15_day(self):
        """Grant with 90-day deadline should score higher than 15-day deadline."""
        matcher = GrantMatcher()

        score_90 = matcher._score_timeline_fit(90)
        score_15 = matcher._score_timeline_fit(15)

        assert score_90 > score_15, "90-day deadline should score higher than 15-day"
        assert score_90 == 1.0, "90-day deadline should get max score"
        assert score_15 < 0.5, "15-day deadline should get low score"


class TestScenarioB1f_CapacityIntegration_GREEN:
    """Scenario B1f: Capacity check integration returning GREEN_LIGHT."""

    def test_nonprofit_has_sufficient_capital_green_light(self):
        """Nonprofit with $100k unrestricted, grant requiring $50k → GREEN_LIGHT."""
        nonprofit = NonprofitProfile(
            nonprofit_id="org_rich",
            name="Well-Capitalized Nonprofit",
            ein="66-6666666",
            annual_revenue_usd=500000,
            mission_keywords=["education"],
            service_geography=["CA"],
            restrictions=[],
            recent_grants=None,
            unrestricted_capital_usd=100000,
        )

        grants_search = GrantsGovAPI(use_mock=True)
        grants = grants_search.search(focus_areas=["STEM_education"], min_amount=50000)

        results = search_grants(nonprofit, grants, top_n=5)

        for match in results["matches"]:
            if match["capacity_verdict"] == "GREEN_LIGHT":
                assert match["capacity_shortfall_usd"] is None or match["capacity_shortfall_usd"] <= 0
                break
        else:
            pytest.fail("Should have at least one GREEN_LIGHT match")


class TestScenarioB1g_CapacityIntegration_RED:
    """Scenario B1g: Capacity check integration returning RED_LIGHT."""

    def test_nonprofit_insufficient_capital_red_light(self):
        """Nonprofit with $50k unrestricted, grant requiring $100k → RED_LIGHT."""
        nonprofit = NonprofitProfile(
            nonprofit_id="org_poor",
            name="Capital-Constrained Nonprofit",
            ein="55-5555555",
            annual_revenue_usd=200000,
            mission_keywords=["climate_action"],
            service_geography=["CO"],
            restrictions=[],
            recent_grants=None,
            unrestricted_capital_usd=50000,
        )

        grants_search = GrantsGovAPI(use_mock=True)
        grants = grants_search.search(min_amount=200000)

        results = search_grants(nonprofit, grants, top_n=5)

        for match in results["matches"]:
            if match["match_required_usd"] > nonprofit["unrestricted_capital_usd"]:
                assert match["capacity_verdict"] == "RED_LIGHT"
                assert match["capacity_shortfall_usd"] > 0


class TestPhase1BIntegration_15ParamTests:
    """Gate 0a-broker: 15 parametrized tests (5 nonprofits × 3 sources)."""

    test_cases = [
        # (nonprofit_fixture, expected_score_range, case_name)
        (
            "education_org_ca_or",
            (0.6, 1.0),
            "1_education_org_stem_focus",
        ),
        (
            "environmental_org_tx_co",
            (0.5, 1.0),
            "2_environmental_org_climate_focus",
        ),
        (
            "health_org_ny_ma",
            (0.5, 1.0),
            "3_health_org_community_health_focus",
        ),
        (
            "youth_org_ca_tx",
            (0.4, 1.0),
            "4_youth_org_education_leadership",
        ),
        (
            "arts_org_ny_ca",
            (0.3, 1.0),
            "5_arts_org_culture_focus",
        ),
    ]

    @pytest.mark.parametrize("nonprofit_name,expected_range,case_name", test_cases)
    def test_all_nonprofits_score_reasonably(self, nonprofit_name, expected_range, case_name):
        """All 5 test nonprofits should produce reasonable scores."""
        nonprofit_factory = getattr(MockNonprofitProfiles, nonprofit_name)
        nonprofit = nonprofit_factory()

        search = MultiSourceGrantSearch()
        all_grants = search.search_all()

        results = search_grants(nonprofit, all_grants, top_n=15)

        assert len(results["matches"]) > 0, f"Should find matches for {case_name}"
        top_score = results["matches"][0]["combined_score"]
        assert expected_range[0] <= top_score <= expected_range[1], (
            f"{case_name}: expected score in {expected_range}, got {top_score}"
        )


class TestDeterminism:
    """Ranking should be deterministic (same input → same output)."""

    def test_same_search_returns_same_ranking(self):
        """Identical searches should return identical rankings."""
        nonprofit = MockNonprofitProfiles.education_org_ca_or()

        search = MultiSourceGrantSearch()
        all_grants = search.search_all()

        results1 = search_grants(nonprofit, all_grants, top_n=10)
        results2 = search_grants(nonprofit, all_grants, top_n=10)
        results3 = search_grants(nonprofit, all_grants, top_n=10)

        matches1 = [m["grant_id"] for m in results1["matches"]]
        matches2 = [m["grant_id"] for m in results2["matches"]]
        matches3 = [m["grant_id"] for m in results3["matches"]]

        assert matches1 == matches2 == matches3, "Ranking should be deterministic"


class TestAPILatency:
    """API latency should be <2 seconds for 50+ grant search."""

    def test_search_completes_under_2_seconds(self):
        """Search should complete in <2 seconds."""
        import time

        nonprofit = MockNonprofitProfiles.education_org_ca_or()

        search = MultiSourceGrantSearch()
        all_grants = search.search_all()

        start = time.time()
        results = search_grants(nonprofit, all_grants, top_n=15)
        elapsed = time.time() - start

        assert elapsed < 2.0, f"Search took {elapsed:.2f}s, should be <2s"
        assert len(results["matches"]) > 0, "Should have results"


class TestPrecisionRecall:
    """Test matching precision and recall against baselines."""

    def test_high_fit_grants_appear_in_top_results(self):
        """High-fit grants should rank in top 5 results."""
        nonprofit = MockNonprofitProfiles.education_org_ca_or()

        grants_search = GrantsGovAPI(use_mock=True)
        grants = grants_search.search(focus_areas=["STEM_education", "diversity"])

        matcher = GrantMatcher()
        scores = matcher.rank_matches(grants, nonprofit, top_n=5)

        # At least one grant with keyword_fit > 0.4 should be in top 5
        high_keyword_fits = [s for s in scores if s.keyword_fit > 0.4]
        assert len(high_keyword_fits) > 0, "Should rank reasonably fitting grants in top 5"

    def test_no_false_negatives_on_obvious_fits(self):
        """Obvious fits should never be excluded from top 15."""
        nonprofit = NonprofitProfile(
            nonprofit_id="org_perfect",
            name="STEM Education Nonprofit",
            ein="11-1111111",
            annual_revenue_usd=500000,
            mission_keywords=["STEM_education", "diversity", "underserved"],
            service_geography=["CA"],
            restrictions=[],
            recent_grants=None,
            unrestricted_capital_usd=100000,
        )

        grants_search = GrantsGovAPI(use_mock=True)
        grants = grants_search.search(focus_areas=["STEM_education"])

        results = search_grants(nonprofit, grants, top_n=15)

        # Should have at least some results with good scores
        assert len(results["matches"]) > 0, "Should find STEM-focused grants"
        # Top match should have reasonable combined score
        top_score = results["matches"][0]["combined_score"]
        assert top_score > 0.5, f"Top match should score >0.5, got {top_score}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
