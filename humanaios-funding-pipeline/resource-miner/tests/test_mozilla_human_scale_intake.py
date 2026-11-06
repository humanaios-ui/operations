"""Contract tests for the 2026 Mozilla Human-Scale AI resource intake.

Read-only. No network, applications, provider decisions, or credentials.
"""
import json
import unittest
from datetime import date
from pathlib import Path

from resource_miner.intent_os import evaluate_objective
from resource_miner.miner import enrich
from resource_miner.sources import funding_pipeline

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT.parent / "data" / "sources.json"
NEEDS = ROOT / "data" / "needs.seed.json"
REQUIREMENTS = ROOT / "data" / "resource_requirements.seed.json"
OFFICIAL_URL = (
    "https://www.mozillafoundation.org/en/what-we-do/grantmaking/incubator/human-scale-ai/"
)


class MozillaHumanScaleIntakeTests(unittest.TestCase):
    def test_source_row_has_official_provenance_and_no_eligibility_claim(self):
        rows = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
        found = [r for r in rows if r.get("url") == OFFICIAL_URL]
        self.assertEqual(len(found), 1, "One canonical Mozilla 2026 source identity")
        row = found[0]
        self.assertEqual(row["sponsor"], "Mozilla Foundation")
        self.assertEqual(row["deadline"], "2026-11-20")
        self.assertEqual(row["last_checked"], "2026-11-03")
        self.assertIsNone(row["native_eligible"], "Applicant eligibility not assessed")
        self.assertIn("conditional", row["award_size"].lower())
        self.assertEqual(row["affordances"], ["project_funding"])

    def test_miner_normalizes_distinct_mozilla_programs_without_promoting_success(self):
        discovered = list(funding_pipeline.discover(SOURCE_PATH))
        incubator = [r for r in discovered if r.source_url == OFFICIAL_URL]
        self.assertEqual(len(incubator), 1)
        historical = [r for r in discovered if r.title == "Mozilla Technology Fund"]
        self.assertEqual(len(historical), 1)
        self.assertNotEqual(incubator[0].resource_id, historical[0].resource_id)

        mined = enrich(incubator, NEEDS, REQUIREMENTS)
        self.assertEqual(len(mined), 1)
        record = mined[0]
        self.assertEqual(record.source_name, "HumanAIOS Funding Pipeline")
        self.assertEqual(record.deadline, "2026-11-20")
        self.assertIn("grant", record.resource_types)
        self.assertIn("project_funding", record.resource_affordances)
        self.assertFalse(record.eligibility_assessed)
        self.assertNotEqual(record.eligibility_status, "ELIGIBLE")
        self.assertNotEqual(record.resource_state, "AWARDED")

    def test_intent_os_projection_keeps_source_qualification_distinct(self):
        mined = enrich(
            [r for r in funding_pipeline.discover(SOURCE_PATH)
             if r.source_url == OFFICIAL_URL],
            NEEDS, REQUIREMENTS,
        )
        result = evaluate_objective(
            "Find Mozilla Foundation Human-Scale AI Incubator project funding",
            [m.to_dict() for m in mined],
            source_mode="snapshot",
            source_status="CURATED_FUNDING_NOT_A_LIVE_ELIGIBILITY_CHECK",
        )
        if date.today() <= date(2026, 11, 20):
            self.assertEqual(len(result["candidates"]), 1)
            item = result["candidates"][0]
            self.assertFalse(item["eligibility_assessed"])
            self.assertNotEqual(item["verification_state"], "VERIFIED")
            self.assertEqual(item["source_name"], "HumanAIOS Funding Pipeline")
        else:
            self.assertFalse(result["candidates"], "Expired lead must not be recommended")


if __name__ == "__main__":
    unittest.main()
