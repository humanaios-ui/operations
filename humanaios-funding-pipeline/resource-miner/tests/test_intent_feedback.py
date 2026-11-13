"""First-user feedback projection regression: three hits, three different states."""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from resource_miner.intent_feedback import project_feedback

ROOT = Path(__file__).resolve().parents[1]
SPECIMEN = ROOT / "fixtures" / "intent_os_first_user_feedback_e0.json"


class IntentFeedbackE0Tests(unittest.TestCase):
    def fixture(self):
        return json.loads(SPECIMEN.read_text(encoding="utf-8"))

    def test_first_user_three_results_preserve_distinct_standing(self):
        p = project_feedback(self.fixture())
        self.assertEqual(p["count"], 3)
        self.assertEqual(p["statuses"]["SETUP_INCOMPLETE"], 1)
        self.assertEqual(p["statuses"]["INTERESTED"], 1)
        self.assertEqual(p["statuses"]["ALREADY_IN_USE"], 1)
        by_name = {x["title"]: x for x in p["records"]}
        self.assertEqual(by_name["GitHub Sponsors"]["next_review"], "COMPLETE_EXISTING_SETUP")
        self.assertEqual(by_name["Apart Lab Fellowship"]["next_review"], "VERIFY_DETAILS_AND_DEADLINE")
        self.assertIn("/sprints/ai-collusion-research-sprint-2026-10-23",
                      by_name["Apart Lab Fellowship"]["related_source_url"])
        self.assertEqual(by_name["Microsoft for Startups Founders Hub"]["next_review"],
                         "RECONCILE_EXISTING_RESOURCE")
        self.assertTrue(all(x["eligibility"] == "NOT_ASSESSED" and
                            not x["ownership_verified"] and
                            not x["registration_verified"] for x in p["records"]))
        self.assertEqual(p["authority_effect"], "NONE")
        self.assertFalse(p["can_auto_publish_seo"])
        self.assertFalse(p["can_auto_apply_or_enroll"])
        self.assertFalse(p["can_auto_retrain_ranker"])

    def test_deterministic_and_order_invariant(self):
        data = self.fixture()
        a = project_feedback(data)
        data["entries"].reverse()
        b = project_feedback(data)
        self.assertEqual(a, b)
        self.assertEqual(a["digest_sha256"], b["digest_sha256"])

    def test_status_is_human_report_not_verified_benefit(self):
        p = project_feedback(self.fixture())
        for record in p["records"]:
            self.assertEqual(record["provenance"], "UNVERIFIED_FIRST_PARTY_HUMAN_REPORT")
            self.assertFalse(record["publication_authorized"])
        self.assertIn("UNSIGNED_LOCAL", p["receipt_kind"])

    def test_unknown_status_cannot_grant_authority(self):
        for status in ("FUNDED", "ELIGIBLE", "SUBMITTED", "AUTHORIZED", "", None, []):
            with self.subTest(status=str(status)):
                data = self.fixture()
                data["entries"][0]["status"] = status
                with self.assertRaises(ValueError):
                    project_feedback(data)

    def test_rejects_private_fields_and_invalid_related_sources(self):
        data = self.fixture()
        data["entries"][0]["private_note"] = "dashboard details"
        with self.assertRaises(ValueError):
            project_feedback(data)
        for url in ("http://localhost:8766", "https://127.0.0.1/data",
                    "https://dev.internal/foo", "javascript:alert(1)",
                    "https://person:secret@example.com/foo"):
            with self.subTest(url=url):
                data = self.fixture()
                data["entries"][0]["related_url"] = url
                with self.assertRaises(ValueError):
                    project_feedback(data)

    def test_no_duplicate_as_two_confirmations(self):
        data = self.fixture()
        data["entries"].append(copy.deepcopy(data["entries"][0]))
        with self.assertRaises(ValueError):
            project_feedback(data)

    def test_bounds_and_no_unexpected_data(self):
        for payload in (
            {"schema": "evil", "entries": []},
            {"schema": "humanaios.intent_os_feedback.v0.1", "entries": [{}]},
            {"schema": "humanaios.intent_os_feedback.v0.1", "entries": [],
             "auth_token": "would-never-accept"},
        ):
            with self.assertRaises(ValueError):
                project_feedback(payload)
        data = self.fixture()
        data["entries"] *= 20
        with self.assertRaises(ValueError):
            project_feedback(data)


if __name__ == "__main__":
    unittest.main()
