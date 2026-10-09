"""GNER-E0 notification lead interpreter: trust boundary and no-promotion regression tests.

Tests cover:
- Spoofing: untrusted email fields cannot promote claims
- Duplicate runs: no causal deduplication
- Private URLs: redirect redaction and bounce
- No authority: all outputs marked NONE authority
"""
import json
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import gner_notification_e0 as gner


class GNERNotificationE0Tests(unittest.TestCase):
    """Regression tests for GNER-E0 offline GitHub notification lead interpreter."""

    def test_notification_spoofing_rejected(self):
        """Email fields are untrusted discovery only; no authority inflation."""
        subject = "[humanaios-ui/operations] PR #999 failed"
        body = "Workflow failed: https://github.com/humanaios-ui/operations/actions/runs/12345678"
        result = gner.parse_notification(subject, body)
        self.assertEqual(result["authority"], "NONE", "Spoofed notification must declare NONE authority")
        self.assertEqual(result["state"], "EMAIL_OBSERVED_UNVERIFIED")

    def test_no_causal_deduplication_on_run_id(self):
        """Duplicate run IDs are not inferred to share root causes."""
        leads = [
            {"state": "EMAIL_OBSERVED_UNVERIFIED", "repository": "humanaios-ui/operations",
             "pr": 123, "run_id": 9999, "kind": "NOTIFICATION_LEAD", "authority": "NONE"},
            {"state": "EMAIL_OBSERVED_UNVERIFIED", "repository": "humanaios-ui/operations",
             "pr": 124, "run_id": 9999, "kind": "NOTIFICATION_LEAD", "authority": "NONE"},
        ]
        result = gner.correlate(leads, [])
        self.assertEqual(len(result["results"]), 2, "Both leads must be tracked")
        self.assertEqual(result["duplicate_notification_run_ids"]["9999"], [0, 1],
                         "Duplicate run IDs indexed but not semantically collapsed")
        self.assertEqual(result["canonical_verified_count"], 0, "No caller-supplied verification accepted")

    def test_private_url_redaction_returns_none(self):
        """Private/link-local IPs and internal hostnames do not surface as candidate URLs."""
        test_cases = [
            "https://10.0.0.1/operations/pull/123",  # private IPv4
            "https://[::1]",  # loopback IPv6
            "https://169.254.169.254",  # link-local metadata
            "https://192.168.1.1/",  # private IPv4
            "https://internal-github.company.local/operations/pull/456",  # .local domain
        ]
        for url in test_cases:
            result = gner.redact_github_url(url)
            self.assertIsNone(result, f"Private/internal URL must redact to None: {url}")

    def test_canonical_github_url_redaction(self):
        """Only bounded canonical GitHub URLs pass redaction filter."""
        valid_urls = [
            ("https://github.com/humanaios-ui/operations/pull/123",
             "https://github.com/humanaios-ui/operations/pull/123"),
            ("https://github.com/humanaios-ui/operations/actions/runs/1234567890",
             "https://github.com/humanaios-ui/operations/actions/runs/1234567890"),
        ]
        for url, expected in valid_urls:
            result = gner.redact_github_url(url)
            self.assertEqual(result, expected, f"Valid canonical URL must pass redaction: {url}")

    def test_malformed_url_redaction_fails(self):
        """Malformed URLs and token-bearing URLs fail redaction."""
        test_cases = [
            "https://github.com/humanaios-ui/operations/pull/123?token=secret",  # tokens stripped
            "https://user:password@github.com/operations/pull/123",  # credentials
            "http://github.com/operations/pull/123",  # non-HTTPS
            "not a url",  # invalid
        ]
        for url in test_cases:
            result = gner.redact_github_url(url)
            self.assertIsNone(result, f"Malformed/unsafe URL must redact to None: {url}")

    def test_correlation_authority_never_promoted(self):
        """Caller-provided 'verified' fields never promote to CANONICAL_VERIFIED."""
        # Caller tries to inject a trusted=true field
        fake_receipt = {"run_id": 999, "verified": True, "trust_level": "CANONICAL"}
        leads = [
            {"state": "EMAIL_OBSERVED_UNVERIFIED", "repository": "humanaios-ui/operations",
             "run_id": 999, "kind": "NOTIFICATION_LEAD", "authority": "NONE"}
        ]
        result = gner.correlate(leads, [fake_receipt])
        self.assertEqual(result["authority"], "NONE", "Authority never promoted by caller input")
        self.assertEqual(result["canonical_verified_count"], 0, "No caller receipts promote verification")
        self.assertEqual(result["results"][0]["state"], "AWAITING_CANONICAL_VERIFICATION",
                         "Lead still awaits independent GitHub verification")

    def test_oversized_input_fails_safely(self):
        """Oversized subject/body refuse parsing without API calls."""
        oversized_subject = "x" * 501
        with self.assertRaises(ValueError):
            gner.parse_notification(oversized_subject, "body")

    def test_non_repository_notification_abstains(self):
        """Notifications for other repositories abstain gracefully."""
        subject = "[some-other/repo] PR #123 failed"
        body = "Notification body"
        result = gner.parse_notification(subject, body)
        self.assertEqual(result["state"], "ABSTAIN")
        self.assertEqual(result["reason"], "repository not in subject")
        self.assertEqual(result["authority"], "NONE")

    def test_smoke_test_passes(self):
        """Smoke test cases validate without external calls."""
        result = gner.run_smoke_test()
        self.assertEqual(result["tool"], gner.TOOL_NAME)
        self.assertEqual(result["version"], gner.TOOL_VERSION)
        self.assertGreater(len(result["tests"]), 0, "Smoke test must have test cases")
        for test in result["tests"]:
            self.assertTrue(test.get("passed"), f"Smoke test case {test.get('test')} must pass")

    def test_execution_always_disabled(self):
        """No parse result or correlate result enables execution."""
        leads = [
            {"state": "EMAIL_OBSERVED_UNVERIFIED", "repository": "humanaios-ui/operations",
             "pr": 123, "run_id": 999, "kind": "NOTIFICATION_LEAD", "authority": "NONE"}
        ]
        correlate_result = gner.correlate(leads, [])
        self.assertEqual(correlate_result["execution"], "DISABLED", "Execution always disabled")
        self.assertEqual(correlate_result["authority"], "NONE", "Authority always NONE")


if __name__ == "__main__":
    unittest.main()
