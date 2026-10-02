import json
import unittest
from datetime import date
from pathlib import Path

from resource_miner.miner import enrich
from resource_miner.entitlement_handoff import build_entitlement_handoff
from resource_miner.needs import load_needs, load_requirements, map_to_needs, map_to_requirements
from resource_miner.normalize import canonicalize_url, cash_mentions, normalize_generic, stable_resource_id
from resource_miner.routing import route_candidate
from resource_miner.sources import funding_pipeline
from resource_miner.sources.rss import FeedRejected, MAX_FEED_BYTES, _parse_feed
from resource_miner.store import dedupe

ROOT = Path(__file__).resolve().parents[1]


class ResourceMinerTests(unittest.TestCase):
    def test_cash_extraction(self):
        self.assertEqual(cash_mentions("$2,500 pool; five at $500 each"), [2500.0, 500.0])

    def test_kaggle_maps_to_validation_and_revenue(self):
        fixture = json.loads((ROOT / "fixtures" / "devto_kaggle_article.json").read_text())
        candidate = normalize_generic(
            title=fixture["title"], url=fixture["url"], source_name="DEV Community",
            discovery_method="fixture", description=fixture["description"],
            sponsor=fixture["organization"]["name"], tags=fixture["tag_list"],
            body_text=fixture["body_markdown"],
        )
        needs = load_needs(ROOT / "data" / "needs.seed.json")
        candidate.need_matches = map_to_needs(candidate, needs)
        ids = {x.need_id for x in candidate.need_matches}
        self.assertIn("external-validation", ids)
        self.assertIn("revenue-capital", ids)
        self.assertIn("competition", candidate.resource_types)
        self.assertIn(2500.0, candidate.cash_mentions_usd)
        self.assertEqual(candidate.deadline, "2026-10-11")

    def test_source_category_maps_to_canonical_resource_type(self):
        compute = normalize_generic(
            title="Startup cloud benefit",
            url="https://example.com/compute",
            source_name="Example",
            discovery_method="test",
            source_category="compute_credit",
        )
        api = normalize_generic(
            title="Free inference tier",
            url="https://example.com/api",
            source_name="Example",
            discovery_method="test",
            source_category="free_api",
        )
        infra = normalize_generic(
            title="Free database",
            url="https://example.com/infra",
            source_name="Example",
            discovery_method="test",
            source_category="free_infra",
        )
        self.assertIn("compute_credit", compute.resource_types)
        self.assertIn("api_access", api.resource_types)
        self.assertIn("free_infrastructure", infra.resource_types)

    def test_canonical_funding_pipeline_preserves_resource_mechanism(self):
        resources = list(funding_pipeline.discover(ROOT.parent / "data" / "sources.json"))
        by_title = {resource.title: resource for resource in resources}
        self.assertIn("compute_credit", by_title["Microsoft for Startups Founders Hub"].resource_types)
        self.assertIn("free_infrastructure", by_title["Kaggle Notebooks"].resource_types)
        self.assertIn("api_access", by_title["Cerebras Free API"].resource_types)

    def test_confirmed_requirement_can_route_verify_now(self):
        candidate = normalize_generic(
            title="Independent replication review",
            url="https://example.com/review",
            source_name="Example",
            discovery_method="test",
            description="Independent research replication and evaluation support.",
            source_category="research_grant",
        )
        requirements = load_requirements(ROOT / "data" / "resource_requirements.seed.json")
        candidate.requirement_matches = map_to_requirements(candidate, requirements)
        ids = {match.requirement_id for match in candidate.requirement_matches}
        self.assertIn("RR-INDEPENDENT-VALIDATION-001", ids)
        route_candidate(candidate, today=date(2026, 10, 2))
        self.assertEqual(candidate.route, "VERIFY_NOW")
        self.assertFalse(candidate.eligibility_assessed)

    def test_conditional_requirement_does_not_create_work(self):
        candidate = normalize_generic(
            title="Dedicated local GPU resource",
            url="https://example.com/gpu",
            source_name="Example",
            discovery_method="test",
            description="Local compute GPU edge hardware access.",
            source_category="compute_credit",
        )
        requirements = load_requirements(ROOT / "data" / "resource_requirements.seed.json")
        candidate.requirement_matches = map_to_requirements(candidate, requirements)
        local = next(
            match for match in candidate.requirement_matches
            if match.requirement_id == "RR-LOCAL-COMPUTE-001"
        )
        self.assertGreaterEqual(local.score, 0.55)
        self.assertEqual(local.gap_status, "CONDITIONAL")
        route_candidate(candidate, today=date(2026, 10, 2))
        self.assertEqual(candidate.route, "WATCH")

    def test_enrich_records_requirement_matches(self):
        candidate = normalize_generic(
            title="Independent AI evaluation grant",
            url="https://example.com/independent-eval",
            source_name="Example",
            discovery_method="test",
            description="Funding for independent benchmark evaluation and replication research.",
            source_category="research_grant",
        )
        rows = enrich(
            [candidate],
            ROOT / "data" / "needs.seed.json",
            ROOT / "data" / "resource_requirements.seed.json",
        )
        ids = {match.requirement_id for match in rows[0].requirement_matches}
        self.assertIn("RR-INDEPENDENT-VALIDATION-001", ids)

    def test_winner_announcement_date_is_not_deadline(self):
        candidate = normalize_generic(
            title="Challenge", url="https://example.com/dates", source_name="Example",
            discovery_method="test",
            body_text="Entries close October 11, 2026. Winners announced November 5, 2026.",
        )
        self.assertEqual(candidate.deadline, "2026-10-11")

    def test_unassessed_candidate_routes_verify_now(self):
        candidate = normalize_generic(
            title="AI Benchmark Challenge $500 prize", url="https://example.com/challenge",
            source_name="Example", discovery_method="test",
            description="Benchmark models and publish results. Deadline October 11, 2026.",
            tags=["benchmark", "challenge"],
        )
        needs = load_needs(ROOT / "data" / "needs.seed.json")
        candidate.need_matches = map_to_needs(candidate, needs)
        route_candidate(candidate, today=date(2026, 9, 24))
        self.assertEqual(candidate.route, "VERIFY_NOW")
        self.assertFalse(candidate.eligibility_assessed)

    def test_entitlement_handoff_preserves_unassessed_boundary(self):
        candidate = normalize_generic(
            title="Native business support program",
            url="https://example.gov/support",
            source_name="Example Authority",
            discovery_method="test",
            description="Support for eligible applicants.",
        )
        needs = load_needs(ROOT / "data" / "needs.seed.json")
        candidate.need_matches = map_to_needs(candidate, needs)
        route_candidate(candidate, today=date(2026, 9, 24))
        handoff = build_entitlement_handoff(candidate)
        self.assertEqual(handoff["requested_action"], "VERIFY_ELIGIBILITY")
        self.assertEqual(handoff["eligibility"]["status"], "UNASSESSED")
        self.assertFalse(handoff["eligibility"]["assessed"])
        self.assertEqual(handoff["authority_effect"], "NONE")
        self.assertEqual(handoff["resource"]["resource_id"], candidate.resource_id)

    def test_entitlement_handoff_rejects_upstream_eligibility_claim(self):
        candidate = normalize_generic(
            title="Program", url="https://example.gov/program",
            source_name="Example", discovery_method="test",
        )
        candidate.eligibility_assessed = True
        candidate.eligibility_status = "ELIGIBLE"
        with self.assertRaises(ValueError):
            build_entitlement_handoff(candidate)

    def test_closed_candidate_archives(self):
        candidate = normalize_generic(
            title="Old Challenge", url="https://example.com/old",
            source_name="Example", discovery_method="test"
        )
        candidate.deadline = "2026-01-01"
        route_candidate(candidate, today=date(2026, 9, 24))
        self.assertEqual(candidate.route, "ARCHIVE")

    def test_dedupe_drops_tracking_only_query(self):
        a = normalize_generic(
            title="A", url="https://example.com/x?tracking=1&utm_source=test",
            source_name="one", discovery_method="one"
        )
        b = normalize_generic(
            title="A richer", url="https://EXAMPLE.com/x",
            source_name="two", discovery_method="two", description="more context"
        )
        rows = dedupe([a, b])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].canonical_url, "https://example.com/x")

    def test_semantic_query_identity_is_preserved(self):
        a = "https://example.com/opportunity?id=1&utm_source=mail"
        b = "https://example.com/opportunity?id=2&utm_source=mail"
        self.assertEqual(canonicalize_url(a), "https://example.com/opportunity?id=1")
        self.assertNotEqual(stable_resource_id(a), stable_resource_id(b))

    def test_query_order_is_canonical(self):
        self.assertEqual(
            canonicalize_url("https://example.com/x?b=2&a=1#frag"),
            "https://example.com/x?a=1&b=2",
        )

    def test_rss_rejects_dtd_and_entities(self):
        payload = (
            b'<?xml version="1.0"?><!DOCTYPE rss [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
            b'<rss><channel><item><title>&xxe;</title></item></channel></rss>'
        )
        with self.assertRaises(FeedRejected):
            _parse_feed(payload)

    def test_rss_rejects_oversized_feed(self):
        with self.assertRaises(FeedRejected):
            _parse_feed(b"x" * (MAX_FEED_BYTES + 1))

    def test_rss_parses_normal_feed(self):
        root = _parse_feed(
            b"<rss><channel><item><title>A</title>"
            b"<link>https://example.com/a</link></item></channel></rss>"
        )
        self.assertEqual(root.tag, "rss")

    def test_enrich_sorts_high_relevance_first(self):
        high = normalize_generic(
            title="Benchmark Challenge $500 prize", url="https://example.com/high",
            source_name="x", discovery_method="test", description="AI evaluation benchmark challenge"
        )
        low = normalize_generic(
            title="Gardening newsletter", url="https://example.com/low",
            source_name="x", discovery_method="test"
        )
        rows = enrich([low, high], ROOT / "data" / "needs.seed.json")
        self.assertEqual(rows[0].canonical_url, "https://example.com/high")
        self.assertEqual(rows[0].route, "VERIFY_NOW")


if __name__ == "__main__":
    unittest.main()
