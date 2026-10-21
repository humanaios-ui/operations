"""GNER-E0 bounded offline tests."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("gner", ROOT / "tools/gner_notification_e0.py")
gner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gner)

SUBJECT = "[humanaios-ui/operations] PR run failed: quality-baseline - E1 (2fca23f)"
BODY = "View workflow run https://github.com/humanaios-ui/operations/actions/runs/37992199793?email_token=PRIVATE"


class RelayTests(unittest.TestCase):
    def test_failure_lead(self):
        r = gner.parse_notification(SUBJECT, BODY)
        self.assertEqual(r["run_id"], 37992199793)
        self.assertEqual(r["workflow"], "quality-baseline")
        self.assertEqual(r["sha_prefix"], "2fca23f")
        self.assertEqual(r["state"], "EMAIL_OBSERVED_UNVERIFIED")

    def test_other_repository_abstains(self):
        self.assertEqual(gner.parse_notification("[outsider/repo] Failed", BODY)["state"], "ABSTAIN")

    def test_review_notification(self):
        r = gner.parse_notification(
            "Re: [humanaios-ui/operations] Review (PR #765)",
            "Copilot commented on this pull request. Changes recommended")
        self.assertEqual(r["kind"], "REVIEW_LEAD")
        self.assertEqual(r["pr"], 765)

    def test_forged_confirmation_never_promotes(self):
        lead = gner.parse_notification(SUBJECT, BODY)
        lead["verified"] = True
        r = gner.correlate([lead], [{"verified": True, "run_id": 37992199793}])
        self.assertEqual(r["canonical_verified_count"], 0)
        self.assertEqual(r["results"][0]["state"], "AWAITING_CANONICAL_VERIFICATION")

    def test_duplicate_same_run_only(self):
        lead = gner.parse_notification(SUBJECT, BODY)
        result = gner.correlate([lead, lead], [])
        self.assertEqual(result["duplicate_notification_run_ids"]["37992199793"], [0, 1])

    def test_distinct_runs_not_root_cause(self):
        a = gner.parse_notification(SUBJECT, BODY)
        b = dict(a, run_id=37992199583)
        self.assertEqual(gner.correlate([a, b], [])["duplicate_notification_run_ids"], {})

    def test_url_token_stripped(self):
        url = "https://github.com/humanaios-ui/operations/actions/runs/37992199793?email_token=SECRET"
        self.assertEqual(gner.redact_github_url(url),
                         "https://github.com/humanaios-ui/operations/actions/runs/37992199793")

    def test_external_url_abstains(self):
        self.assertIsNone(gner.redact_github_url("https://evil.example/humanaios-ui/operations/pull/765"))

    def test_no_authority(self):
        r = gner.correlate([gner.parse_notification(SUBJECT, BODY)], [])
        self.assertEqual(r["authority"], "NONE")
        self.assertEqual(r["execution"], "DISABLED")

    def test_oversize_denied(self):
        with self.assertRaises(ValueError):
            gner.parse_notification(SUBJECT, "x" * 25001)

    def test_smoke_test_and_cli_contract(self):
        expected_names = [
            "parse_notification_valid",
            "parse_notification_oversized",
            "correlate_valid",
            "redact_canonical_url",
            "redact_private_ip",
        ]
        result = gner.run_smoke_test()
        self.assertEqual([item["test"] for item in result["tests"]], expected_names)
        self.assertTrue(all(item["passed"] for item in result["tests"]))
        self.assertEqual(result["summary"], "5/5 tests passed")

        command = [sys.executable, str(ROOT / "tools/gner_notification_e0.py")]
        completed = subprocess.run(
            command + ["--smoke-test"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(json.loads(completed.stdout)["summary"], "5/5 tests passed")

        missing_flag = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(missing_flag.returncode, 0)
        self.assertIn("--smoke-test is required", missing_flag.stderr)


if __name__ == "__main__":
    unittest.main()
