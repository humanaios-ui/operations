"""Synthetic E1 tests for issue #753. No network requests or real data."""
import importlib.util
from pathlib import Path
import unittest

MOD = Path(__file__).resolve().parents[2] / "src" / "resource_miner" / "outlier_public_adapter_v0_1.py"
spec = importlib.util.spec_from_file_location("outlier_public_adapter_v0_1", MOD)
adapter = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = adapter
spec.loader.exec_module(adapter)


def cases():
    P = adapter.PublicCandidate
    return [
        P("OTL-E1-001", "HUMAN_LABOR_INCOME_OPPORTUNITY",
          "https://outlier.ai/faq", "PUBLIC_FIRST_PARTY_METADATA", "public_contributor_faq"),
        P("OTL-E1-002", "HUMAN_NETWORK_REWARD",
          "https://outlier.ai/faq", "PUBLIC_FIRST_PARTY_METADATA", "public_referral_faq"),
        P("OTL-E1-003", "AI_EVALUATION_ENVIRONMENT",
          "https://outlier.ai/legal/terms-of-use", "PUBLIC_FIRST_PARTY_METADATA",
          "public_terms_and_notice"),
    ]


class TestOutlierPublicAdapter(unittest.TestCase):
    def test_three_case_screen(self):
        result = adapter.evaluate_fixture(cases())
        self.assertEqual(len(result), 3)
        self.assertEqual([x["bsa_state"] for x in result], [
            "CONDITIONAL_HUMAN_REVIEW", "INSUFFICIENT_EVIDENCE",
            "RESEARCH_POLICY_HOLD",
        ])
        self.assertEqual([x["expected_value"] for x in result],
                         ["UNKNOWN", "UNKNOWN", "NOT_APPLICABLE"])
        for x in result:
            self.assertEqual(x["authority_effect"], "NONE")
            self.assertEqual(x["execution"], "NOT_AUTHORIZED")
            self.assertEqual(x["bot_state"], "NOT_OBSERVED")

    def test_action_boundary(self):
        self.assertEqual(adapter.authorize_action("REVIEW_SUPPLIED_PUBLIC_METADATA"),
                         "ALLOWED_NON_EXECUTING")
        for action in adapter.FORBIDDEN_ACTIONS | {"UNRECOGNIZED", "REVIEW_DASHBOARD"}:
            for token in (None, True, "Z2", {"approved": True}):
                with self.subTest(action=action, token=str(token)):
                    with self.assertRaises(adapter.PolicyDenied):
                        adapter.authorize_action(action, external_authorization=token)

    def test_source_boundary(self):
        bad = [
            "http://outlier.ai/faq", "https://app.outlier.ai/dashboard",
            "https://app.outlier.ai/referrals",
            "https://outlier.ai.evil.test/faq",
            "https://outlier.ai@evil.test/faq",
            "https://outlier.ai:444/faq",
            "https://outlier.ai/faq?token=secret",
            "https://outlier.ai/legal/model-usage",
            "https://outlier.ai/any-other-page",
            "file:///etc/passwd", "https://outlier.ai/faq#private",
        ]
        for url in bad:
            with self.subTest(url=url):
                with self.assertRaises(adapter.PolicyDenied):
                    adapter.validate_public_url(url)

    def test_missing_provenance_and_categories_fail(self):
        P = adapter.PublicCandidate
        for x in [
            P("OTL-E1-009", "HUMAN_NETWORK_REWARD", "https://outlier.ai/faq",
              "AUTHENTICATED_DASHBOARD", "public_referral_faq"),
            P("OTL-E1-009", "CONTRACTOR_TASK_RECORD", "https://outlier.ai/faq",
              "PUBLIC_FIRST_PARTY_METADATA", "public_referral_faq"),
            P("OTL-E1-009", "HUMAN_NETWORK_REWARD", "https://outlier.ai/faq",
              "PUBLIC_FIRST_PARTY_METADATA", "contractor_project_content"),
        ]:
            with self.assertRaises(adapter.PolicyDenied):
                adapter.screen(x)

    def test_duplicate_or_partial_fixture_fails(self):
        with self.assertRaises(adapter.PolicyDenied):
            adapter.evaluate_fixture(cases()[:2])
        with self.assertRaises(adapter.PolicyDenied):
            adapter.evaluate_fixture([cases()[0]] * 3)


if __name__ == "__main__":
    unittest.main()
