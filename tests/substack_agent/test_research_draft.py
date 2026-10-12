"""Offline regression coverage for the legacy forecasting agent HPRA boundary."""
import unittest
from tools.substack_agent.research_draft import verified_research_draft, EvidenceUnavailable

GOOD = {"question_url": "https://example.org/question/1",
        "p4_resolved_at": "2026-10-01T12:00:00+00:00",
        "p4_brier_score": 0.0, "p4_brier_skill_score": 0.0}

class TestResearchDraft(unittest.TestCase):
    def test_missing_data_fails_closed(self):
        with self.assertRaises(EvidenceUnavailable):
            verified_research_draft([])

    def test_synthetic_rejected(self):
        with self.assertRaises(EvidenceUnavailable):
            verified_research_draft([{**GOOD, "evidence_status": "SYNTHETIC_TEST_ONLY"}])

    def test_partial_data_rejected(self):
        with self.assertRaises(EvidenceUnavailable):
            verified_research_draft([{k:v for k,v in GOOD.items() if k != "p4_brier_skill_score"}])

    def test_zero_is_valid_and_no_publish(self):
        p = verified_research_draft([GOOD])
        self.assertEqual(p["status"], "DRAFT_ONLY")
        self.assertEqual(p["authorization"], "NONE")
        self.assertIsNone(p["publication"])
        self.assertIn("n=1", p["content"]["body"])
        self.assertIn("0.000", p["content"]["body"])
        self.assertNotIn("**Published:**", p["content"]["body"])

    def test_draft_mutation_changes_digest(self):
        first = verified_research_draft([GOOD])
        second = verified_research_draft([{**GOOD,"p4_brier_score":0.25}])
        self.assertNotEqual(first["content_sha256"],second["content_sha256"])

    def test_url_and_timestamp_fail_closed(self):
        for data in ({**GOOD,"question_url":"http://example.org/a"},
                     {**GOOD,"p4_resolved_at":"not a date"},
                     {**GOOD,"p4_brier_score":float("nan")}):
            with self.subTest(data=data), self.assertRaises(EvidenceUnavailable):
                verified_research_draft([data])

if __name__ == "__main__":
    unittest.main()
