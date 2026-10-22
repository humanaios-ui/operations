"""Offline fixtures for RMO-VERIFY-001. No external requests or side effects."""
import unittest
from resource_miner.verification_opportunities import (
    DASE_SEED, OpportunityObservation, evaluate,
)

BASE = dict(
    identifier="TEST-1", subject="Sample", source_url="https://example.org/post",
    source_kind="synthetic", need_state="EXPLICIT_VERIFICATION_REQUEST",
    claim_summary="Reproduce stated benchmark", required_capability="code_review",
)


class VerificationOpportunityTests(unittest.TestCase):
    def test_seed_is_unverified_and_unauthorized(self):
        result = evaluate(DASE_SEED, {})
        self.assertEqual(result["claim_status"], "UNVERIFIED")
        self.assertEqual(result["authorization_state"], "NOT_AUTHORIZED")
        self.assertFalse(result["can_authorize"])

    def test_explicit_request_only_potential_fit(self):
        r = evaluate(OpportunityObservation(**BASE), {"code_review": "OBSERVED_AVAILABLE"})
        self.assertEqual(r["screening_state"], "CANDIDATE")
        self.assertEqual(r["capability_fit"], "POTENTIAL_ONLY")
        self.assertFalse(r["can_authorize"])

    def test_claim_only_not_opportunity(self):
        r = evaluate(OpportunityObservation(**{**BASE, "need_state": "CLAIM_ONLY"}), {})
        self.assertEqual(r["screening_state"], "CLAIM_ONLY")

    def test_critique_is_not_authorization(self):
        r = evaluate(OpportunityObservation(**{**BASE, "need_state": "THIRD_PARTY_CRITIQUE"}), {})
        self.assertEqual(r["screening_state"], "REVIEW_ONLY_NO_CONSENT")
        self.assertFalse(r["can_authorize"])

    def test_unknown_capability_not_suitable(self):
        r = evaluate(OpportunityObservation(**BASE), {})
        self.assertEqual(r["capability_fit"], "NOT_ESTABLISHED")

    def test_missing_provenance_fails_closed(self):
        with self.assertRaises(ValueError):
            evaluate(OpportunityObservation(**{**BASE, "source_url": ""}), {})

    def test_local_or_http_url_fails_closed(self):
        for url in ("http://example.org", "https://localhost/private", "https://user:pass@example.org"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                evaluate(OpportunityObservation(**{**BASE, "source_url": url}), {})

    def test_external_action_blocked(self):
        r = evaluate(OpportunityObservation(**{**BASE, "external_action_requested": True}), {})
        self.assertEqual(r["screening_state"], "BLOCKED_EXTERNAL_ACTION")
        self.assertFalse(r["can_authorize"])

    def test_commercial_unknown_remains_unknown(self):
        self.assertEqual(evaluate(OpportunityObservation(**BASE), {})["commercial_signal"], "UNKNOWN")

    def test_evidence_urls_checked(self):
        with self.assertRaises(ValueError):
            evaluate(OpportunityObservation(**{**BASE, "evidence_refs": ("file:///private",)}), {})

    def test_github_public_supported_without_fetch(self):
        r = evaluate(OpportunityObservation(**{**BASE, "source_kind": "github_public"}), {})
        self.assertEqual(r["source_kind"], "github_public")

    def test_challenge_public_supported_without_fetch(self):
        r = evaluate(OpportunityObservation(**{**BASE, "source_kind": "challenge_public"}), {})
        self.assertEqual(r["source_kind"], "challenge_public")


if __name__ == "__main__":
    unittest.main()
