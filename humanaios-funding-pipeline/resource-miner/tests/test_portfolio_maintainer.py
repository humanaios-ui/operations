"""Synthetic privacy and drift tests; never use the founder's actual profile."""
import unittest
from pathlib import Path

from resource_miner.mines import load_mines, resolve_mines
from resource_miner.portfolio_maintainer import (
    BUSINESS_SCHEMA, BUSINESS_SOURCE, PROFILE_SCHEMA, observe_portfolio,
)

ROOT = Path(__file__).resolve().parents[1]
SHA_A = "a" * 40
SHA_B = "b" * 40


def fixture():
    personal = {
        "schema": PROFILE_SCHEMA,
        "capability_codes": ["data_quality", "ai_evaluation"],
        "approved_for_local_matching": True,
        "revision": SHA_A,
    }
    business = {
        "schema": BUSINESS_SCHEMA, "source_url": BUSINESS_SOURCE,
        "revision": SHA_B, "stage": "research", "legal_form": "llc",
        "focus": "behavioral_observability",
    }
    consumer = {
        "description": "Open AI behavioral observability research.",
        "fundingStage": "research", "budgetRange": None, "teamSize": "solo",
    }
    return personal, business, consumer


class PortfolioMaintainerTests(unittest.TestCase):
    def test_registered_as_resource_not_external_opportunity(self):
        mines = load_mines(ROOT / "data" / "mines.seed.json")
        match = [m for m in mines if m.name == "Owner-Controlled Portfolio Profile"]
        self.assertEqual(len(match), 1)
        self.assertIn("CONTROLLED_RESOURCE_SOURCE", match[0].roles)
        self.assertNotIn("OPPORTUNITY_SOURCE", match[0].roles)
        candidates, receipts = resolve_mines(match, observed_at="2026-10-25T00:00:00Z")
        self.assertEqual(candidates, [])
        self.assertEqual(receipts[0].state, "ROLE_ONLY")

    def test_clean_snapshot_never_grants_authority(self):
        report = observe_portfolio(*fixture())
        self.assertEqual(report["review_state"], "NO_DRIFT_OBSERVED")
        self.assertIs(report["eligibility_assessed"], False)
        self.assertIs(report["mutation_performed"], False)
        self.assertEqual(report["authority_effect"], "NONE")

    def test_catches_unsubstantiated_commercial_claims(self):
        personal, business, consumer = fixture()
        consumer["description"] = "374K verified workers; physical execution layer"
        consumer["fundingStage"] = "early-stage"
        consumer["budgetRange"] = {"min": 100000, "max": 1000000}
        consumer["teamSize"] = "small"
        report = observe_portfolio(personal, business, consumer)
        self.assertEqual(report["review_state"], "REVIEW_REQUIRED")
        self.assertIn("STAGE_DRIFT", report["issues"])
        self.assertIn("UNSUPPORTED_CLAIM:374K_VERIFIED_WORKERS", report["issues"])
        self.assertIn("UNSUPPORTED_CLAIM:PHYSICAL_EXECUTION_LAYER", report["issues"])
        self.assertIn("UNAPPROVED_BUDGET_RANGE", report["issues"])
        self.assertIn("TEAM_SIZE_RECHECK", report["issues"])
        self.assertEqual(report["next_action"], "HUMAN_REVIEW")

    def test_rejects_sensitive_or_extra_fields_and_unapproved_use(self):
        personal, business, consumer = fixture()
        personal["email"] = "private@example.com"
        with self.assertRaises(ValueError):
            observe_portfolio(personal, business, consumer)
        del personal["email"]
        personal["approved_for_local_matching"] = False
        with self.assertRaises(ValueError):
            observe_portfolio(personal, business, consumer)

    def test_source_changes_are_only_a_review_signal(self):
        personal, business, consumer = fixture()
        report = observe_portfolio(
            personal, business, consumer,
            prior={"personal_revision": SHA_B, "business_revision": SHA_B},
        )
        self.assertIn("PERSONAL_SOURCE_CHANGED", report["issues"])
        self.assertFalse(report["mutation_performed"])


if __name__ == "__main__":
    unittest.main()
