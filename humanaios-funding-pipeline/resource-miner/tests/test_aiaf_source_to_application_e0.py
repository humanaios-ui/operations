"""Read-only, existing Resource Miner source -> local application case crosswalk.

This verifies the program already exists once in the public catalog; it does not
read applicant data, submit a proposal, authenticate a provider receipt or write
to live INTENT-OS. Source observations and private application events stay apart.
"""
import json
import unittest
from pathlib import Path

from resource_miner.miner import enrich
from resource_miner.normalize import stable_resource_id
from resource_miner.sources.funding_pipeline import discover
from resource_miner.intent_os import evaluate_objective

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT.parent / "data" / "sources.json"
NEEDS = ROOT / "data" / "needs.seed.json"
REQUIREMENTS = ROOT / "data" / "resource_requirements.seed.json"
URL = "https://www.aialignmentfoundation.org/approach/apply"


class AIAFSourceToApplicationE0(unittest.TestCase):
    def test_official_program_is_single_current_canonical_source(self):
        rows = json.loads(CATALOG.read_text(encoding="utf-8"))
        matching = [x for x in rows if x.get("url") == URL]
        self.assertEqual(len(matching), 1)
        row = matching[0]
        self.assertEqual(row["source"], "aialignmentfoundation.org")
        self.assertEqual(row["last_checked"], "2026-11-04")
        self.assertEqual(row["category"], "research_grant")
        self.assertIsNone(row["native_eligible"])
        self.assertIsNone(row["deadline"])
        self.assertEqual(row["deadline_cadence"], "not_stated")
        self.assertNotIn("fiscal sponsorship", row["notes"].lower())

    def test_real_miner_discovery_and_need_matching_do_not_claim_award(self):
        rows = [r for r in discover(CATALOG) if r.source_url == URL]
        self.assertEqual(len(rows), 1)
        candidate = enrich(rows, NEEDS, REQUIREMENTS)[0]
        self.assertEqual(candidate.resource_id, stable_resource_id(URL))
        self.assertEqual(candidate.resource_types, ["grant"])
        self.assertIn("project_funding", candidate.resource_affordances)
        self.assertFalse(candidate.eligibility_assessed)
        self.assertEqual(candidate.eligibility_status, "UNASSESSED")
        self.assertIsNone(candidate.deadline)
        self.assertEqual(candidate.cash_mentions_usd, [])
        self.assertEqual(candidate.resource_state, "CANDIDATE")
        self.assertIn(candidate.route, ("VERIFY_NOW", "WATCH", "ARCHIVE"))

    def test_local_application_parent_matches_canonical_miner_identity(self):
        html = (ROOT / "my-opportunities.html").read_text(encoding="utf-8")
        self.assertIn('parent_resource_id:"' + stable_resource_id(URL) + '"', html)
        self.assertIn('workflow:"RESEARCH_SUPPORT_APPLICATION"', html)
        self.assertNotIn('parent_resource_id:"aiaf-program-local"', html)

    def test_public_discovery_does_not_expose_private_application_status(self):
        candidates = [r for r in discover(CATALOG) if r.source_url == URL]
        row = enrich(candidates, NEEDS, REQUIREMENTS)[0].to_dict()
        projection = evaluate_objective(
            "AI Alignment Foundation research support for human controlled AI",
            [row], source_mode="snapshot", source_status="CURATED_NOT_LIVE_PROVIDER_CHECK",
        )
        self.assertEqual(projection["authority"], "NONE")
        self.assertEqual(projection["execution"], "DISABLED")
        self.assertEqual(projection["eligibility"], "NOT_ASSESSED")
        self.assertNotIn("APPLICATION_SUBMITTED_HUMAN", json.dumps(projection))
        self.assertNotIn("personal_email", json.dumps(projection))


if __name__ == "__main__":
    unittest.main()
