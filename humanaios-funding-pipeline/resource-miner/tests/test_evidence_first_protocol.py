import unittest
from resource_miner.evidence_first_protocol import WitnessFeedback, project_feedback

class EvidenceFirstTests(unittest.TestCase):
    def test_convergent_source_failure(self):
        item = WitnessFeedback("convergent-historical", "SOURCE_CORRECTION",
                               "OBSERVED", "public-lever-listing-check",
                               "No role listed; closure not established")
        output = project_feedback(item)
        self.assertTrue(output["has_correction"])
        self.assertNotIn("correction", output)
        self.assertEqual(output["authority"], "NONE")
        self.assertEqual(output["execution"], "DISABLED")

    def test_intent_corrections_do_not_authorize(self):
        for kind in ("QUESTION", "CONDITIONAL_WILLINGNESS", "INTENT_CORRECTION"):
            item = WitnessFeedback("fixture", kind, "UNVERIFIED", "public-ref",
                                   "private words", "private intent")
            output = project_feedback(item)
            self.assertTrue(output["requires_human_review"])
            self.assertNotIn("private words", str(output))
            self.assertNotIn("private intent", str(output))

    def test_rejects_unsupported_kind_and_source_state(self):
        for kind in ("APPROVAL", "PRIVATE HUMAN TEXT", "", None):
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                WitnessFeedback("fixture", kind, "OBSERVED", "public-ref", "private correction")
        for state in ("VERIFIED_LIVE", "PRIVATE HUMAN TEXT", "", None):
            with self.subTest(state=state), self.assertRaises(ValueError):
                WitnessFeedback("fixture", "QUESTION", state, "public-ref", "private correction")

    def test_no_authority_escalation(self):
        with self.assertRaises(ValueError):
            WitnessFeedback("fixture", "QUESTION", "UNVERIFIED", "ref",
                            "text", authority="APPROVED")

if __name__ == "__main__":
    unittest.main()
