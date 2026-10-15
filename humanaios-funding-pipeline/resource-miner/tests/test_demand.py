import unittest

from resource_miner.demand import (
    attach_snapshot,
    build_snapshot,
    parse_bing_keyword_csv,
    parse_google_trends_csv,
    validate_query_cluster,
)
from resource_miner.models import DemandQuery, ResourceCandidate
from resource_miner.normalize import normalize_generic


class DemandTests(unittest.TestCase):
    def test_google_trends_is_relative_not_user_count(self):
        csv_text = """Category: All categories

Week,azure startup credits: (United States),bug bounty programs: (United States)
2026-09-13,24,72
2026-09-20,30,80
2026-09-27,36,100
"""
        metrics = parse_google_trends_csv(
            csv_text,
            observed_at="2026-10-03T08:00:00-05:00",
            geography="US",
        )
        self.assertTrue(metrics)
        self.assertTrue(all(m.unit == "relative_index_0_100" for m in metrics))
        self.assertFalse(any("user" in m.unit for m in metrics))
        peak = [
            m
            for m in metrics
            if m.query.startswith("bug bounty") and m.metric == "interest_peak"
        ][0]
        self.assertEqual(peak.value, 100)

    def test_google_trends_preserves_censored_low_volume(self):
        csv_text = """Week,niche query: (United States)
2026-09-20,<1
2026-09-27,2
"""
        metrics = parse_google_trends_csv(
            csv_text,
            observed_at="2026-10-03T08:00:00-05:00",
            geography="US",
        )
        censored = [m for m in metrics if m.censored_below is not None]
        self.assertEqual(censored[0].censored_below, 1.0)
        self.assertIsNone(censored[0].value)

    def test_bing_volume_is_search_activity_not_unique_people(self):
        csv_text = """Keyword,Impressions,Week
azure startup credits,1200,2026-09-20
HackerOne bug bounty,3400,2026-09-20
"""
        metrics = parse_bing_keyword_csv(
            csv_text,
            observed_at="2026-10-03T08:00:00-05:00",
            geography="US",
        )
        self.assertEqual(len(metrics), 2)
        self.assertEqual(metrics[0].metric, "impressions")
        self.assertEqual(metrics[0].value, 1200)
        self.assertEqual(metrics[0].unit, "search_events_or_impressions")

    def test_query_cluster_distinguishes_mine_opportunity_resource_and_need(self):
        cluster = validate_query_cluster(
            [
                DemandQuery("Microsoft for Startups", "MINE", "NAME"),
                DemandQuery("Azure startup credits", "OPPORTUNITY", "RESOURCE"),
                DemandQuery("cloud credits for startups", "RESOURCE_CLASS", "RESOURCE"),
                DemandQuery("free cloud credits", "NEED", "PROBLEM"),
            ]
        )
        self.assertEqual(
            [q.subject_kind for q in cluster],
            ["MINE", "OPPORTUNITY", "RESOURCE_CLASS", "NEED"],
        )

    def test_snapshot_rejects_mixed_subject_kinds(self):
        with self.assertRaises(ValueError):
            build_snapshot(
                subject_kind="OPPORTUNITY",
                query_cluster=[
                    DemandQuery("Azure startup credits", "OPPORTUNITY", "RESOURCE"),
                    DemandQuery("Microsoft for Startups", "MINE", "NAME"),
                ],
                provider_metrics=[],
                observed_at="2026-10-03T08:00:00-05:00",
            )

    def test_normalizer_can_bind_mine_to_opportunity(self):
        candidate = normalize_generic(
            title="Azure startup credit offer",
            url="https://example.test/azure-credit",
            source_name="Microsoft",
            discovery_method="test",
            mine_name="Microsoft for Startups",
            mine_url="https://www.microsoft.com/en-us/startups",
            opportunity_kind="startup_cloud_credit",
        )
        self.assertEqual(candidate.mine_name, "Microsoft for Startups")
        self.assertEqual(candidate.opportunity_kind, "startup_cloud_credit")
        self.assertNotEqual(candidate.title, candidate.mine_name)

    def test_demand_attachment_cannot_change_routing_or_eligibility(self):
        candidate = ResourceCandidate(
            resource_id="res-test",
            title="Azure credit opportunity",
            source_name="Microsoft for Startups",
            source_url="https://example.test",
            canonical_url="https://example.test",
            discovery_method="test",
            discovered_at="2026-10-03T08:00:00-05:00",
            route="WATCH",
            eligibility_assessed=False,
        )
        snapshot = build_snapshot(
            subject_kind="OPPORTUNITY",
            query_cluster=[
                DemandQuery("Azure startup credits", "OPPORTUNITY", "RESOURCE")
            ],
            provider_metrics=[],
            observed_at="2026-10-03T08:00:00-05:00",
        )
        updated = attach_snapshot(candidate, snapshot)
        self.assertEqual(updated.route, "WATCH")
        self.assertFalse(updated.eligibility_assessed)
        self.assertEqual(len(updated.demand_snapshots), 1)

    def test_hackerone_ontology_tracks_reward_as_resource_not_mine(self):
        candidate = ResourceCandidate(
            resource_id="h1-test",
            title="Example Bug Bounty — scoped web asset",
            source_name="HackerOne",
            source_url="https://hackerone.com/example",
            canonical_url="https://hackerone.com/example",
            discovery_method="test",
            discovered_at="2026-10-03T08:00:00-05:00",
            mine_name="HackerOne",
            opportunity_kind="bug_bounty_program_asset",
            resource_types=["paid_work"],
            resource_affordances=["earned_income"],
        )
        self.assertEqual(candidate.mine_name, "HackerOne")
        self.assertNotEqual(candidate.title, candidate.mine_name)
        self.assertIn("earned_income", candidate.resource_affordances)


if __name__ == "__main__":
    unittest.main()
