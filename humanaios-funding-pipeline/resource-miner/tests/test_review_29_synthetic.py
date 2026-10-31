"""Synthetic review-packet history, status contradictions, and private export."""
from __future__ import annotations
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent / "fixtures"))
from review_29_synthetic import specimen_29, DEEPGRAM
from resource_miner.source_review import (
    project_source_reviews, public_review_packet, review_flags,
)


class Review29Cases(unittest.TestCase):
    def test_29_observations_have_22_latest_views_with_history_retained(self):
        packet = specimen_29()
        result = project_source_reviews(packet)
        self.assertEqual(result["count"], 29)
        self.assertEqual(len(result["reports"]), 29)
        self.assertEqual(result["latest_count"], 22)
        self.assertEqual(len(result["latest_by_source"]), 22)
        packet["records"].reverse()
        self.assertEqual(project_source_reviews(packet), result)
        alpha = next(x for x in result["latest_by_source"] if x["resource_title"] == "Synthetic alpha")
        self.assertEqual(alpha["report_id"], "SYNTHETIC-1")

    def test_deepgram_user_report_requires_recheck_not_employer_closure(self):
        result = project_source_reviews(specimen_29())
        held = next(x for x in result["latest_by_source"] if x["source_url"] == DEEPGRAM)
        self.assertEqual(held["review_gate"], "RECHECK_REQUIRED")
        self.assertTrue(held["source_hold_recommended"])
        self.assertFalse(held["source_availability_verified"])
        self.assertFalse(held["opportunity_closed_verified"])

    def test_policy_and_setup_observations_do_not_pretend_source_missing(self):
        result = project_source_reviews(specimen_29())
        policy = next(x for x in result["reports"] if x["resource_title"] == "Synthetic single-1")
        setup = next(x for x in result["reports"] if x["resource_title"] == "Synthetic single-2")
        self.assertEqual(policy["review_gate"], "HUMAN_REVIEW_ONLY")
        self.assertIn("SUBMISSION_OR_AI_POLICY_RESTRICTION_UNVERIFIED", policy["review_flags"])
        self.assertEqual(setup["review_gate"], "HUMAN_REVIEW_ONLY")
        self.assertIn("RESOURCE_SETUP_DIFFICULTY_USER_REPORTED", setup["review_flags"])

    def test_failed_url_is_not_its_own_replacement(self):
        result = project_source_reviews(specimen_29())
        gov = next(x for x in result["reports"] if x["resource_title"] == "Synthetic single-3")
        self.assertIsNone(gov["replacement_url_user_claim"])

    def test_exports_exclude_raw_notes_query_tokens_and_opaque_path_ids(self):
        packet = public_review_packet(specimen_29())
        self.assertEqual(len(packet["records"]), 29)
        rendered = json.dumps(packet)
        for token in ("SUPER_PRIVATE_DO_NOT_EXPORT", "PRIVATE_TOKEN", "PRIVATE_VALUE",
                      "org_SYNTHETIC_ACCOUNT", "prj_SYNTHETIC_PROJECT"):
            self.assertNotIn(token, rendered)
        self.assertIn("SOURCE_STATUS_NOTE_CONFLICT_RECHECK_REQUIRED", rendered)
        self.assertEqual(project_source_reviews(packet)["latest_count"], 22)


if __name__ == "__main__":
    unittest.main()
