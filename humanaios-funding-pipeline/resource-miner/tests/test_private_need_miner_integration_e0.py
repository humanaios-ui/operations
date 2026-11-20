"""Synthetic integration between private needs bridge and existing Resource Miner."""
from datetime import date
from pathlib import Path
import unittest

from resource_miner.private_need_digest_e0 import project
from resource_miner.models import ResourceCandidate
from resource_miner.needs import load_needs, map_to_needs
from resource_miner.routing import route_candidate

ROOT = Path(__file__).resolve().parents[1]
KEY = b"synthetic-test-hmac-key-not-used-in-actual-mail-001"

class NeedDigestMinerIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.graph = load_needs(ROOT / "data" / "needs.seed.json")

    def _email(self, need_id):
        return dict(message_id="bbbbbbbbbbbbbbbb",need_id=need_id,
            observed_at="2026-11-07T16:00:00Z",priority="MEDIUM",
            source_status="UNVERIFIED",next_action="VERIFY_SOURCE",
            public_url="https://example.org/")

    def _resource(self, title, kinds, tags, deadline=None):
        return ResourceCandidate(
            resource_id="SYNTHETIC-RESOURCE-001",
            title=title, source_name="synthetic official-source fixture",
            source_url="https://example.org/",
            canonical_url="https://example.org/",
            discovery_method="synthetic_fixture",discovered_at="2026-11-07T16:00:00Z",
            description=title, resource_types=kinds, tags=tags, deadline=deadline,
        )

    def test_email_need_id_joins_actual_grant_candidate(self):
        proposed = project([self._email("revenue-capital")], self.graph, KEY)
        candidate = self._resource("Synthetic business grant", ["grant"], ["grant","funding"], "2026-11-20")
        candidate.need_matches = map_to_needs(candidate, self.graph)
        route_candidate(candidate, today=date(2026,11,7))
        self.assertEqual(proposed["records"][0]["need_id"], "revenue-capital")
        self.assertIn("revenue-capital", {x.need_id for x in candidate.need_matches})
        self.assertEqual(candidate.route,"VERIFY_NOW")
        self.assertFalse(candidate.eligibility_assessed)
        self.assertEqual(proposed["authority_effect"],"NONE")

    def test_compute_credit_joins_existing_need(self):
        proposed = project([self._email("compute-infrastructure")], self.graph, KEY)
        candidate = self._resource("Synthetic cloud compute credit",["compute_credit"],["compute","cloud"])
        self.assertEqual(proposed["records"][0]["need_id"],"compute-infrastructure")
        self.assertIn("compute-infrastructure",{x.need_id for x in map_to_needs(candidate,self.graph)})

    def test_unmapped_subscription_does_not_create_graph_node(self):
        proposed=project([self._email("subscription-oversight")],self.graph,KEY)
        self.assertEqual(proposed["need_graph_gaps"],1)
        self.assertNotIn("subscription-oversight",{x["need_id"] for x in self.graph})

    def test_conflicting_gmail_claim_not_upgraded_by_miner_match(self):
        x=self._email("revenue-capital")
        x["source_status"]="SOURCE_CONFLICT"
        proposed=project([x],self.graph,KEY)
        candidate=self._resource("Synthetic grant with conflicting amount",["grant"],["grant"])
        self.assertIn("revenue-capital",{m.need_id for m in map_to_needs(candidate,self.graph)})
        self.assertEqual(proposed["records"][0]["route"],"HOLD_CONFLICT")
        self.assertFalse(proposed["records"][0]["provider_eligibility_verified"])

if __name__ == "__main__":
    unittest.main()
