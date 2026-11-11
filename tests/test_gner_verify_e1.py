"""GNER-E1 pure contract verification tests; no live requests."""
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1] / "tools"
for name in ("gner_notification_e0", "gner_verify_e1"):
    spec = importlib.util.spec_from_file_location(name, ROOT / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)

from gner_notification_e0 import parse_notification
from gner_verify_e1 import reconcile, verify_lead, VerificationDenied

SUBJECT = "[humanaios-ui/operations] PR run failed: quality-baseline - E1 (2fca23f)"
LEAD = parse_notification(
    SUBJECT, "https://github.com/humanaios-ui/operations/actions/runs/37992199793"
)
CANONICAL = {
    "id": 37992199793, "repository": {"full_name": "humanaios-ui/operations"},
    "head_sha": "2fca23f68145f1193033c8f4702e7f4344a19e04",
    "name": "quality-baseline", "status": "completed", "conclusion": "failure",
    "event": "pull_request", "pull_requests": [{"number": 765}],
}


class ReconciliationTests(unittest.TestCase):
    def test_matching_canonical_metadata(self):
        r = reconcile(LEAD, CANONICAL)
        self.assertEqual(r["state"], "CANONICAL_VERIFIED")
        self.assertEqual(r["authority"], "NONE")
        self.assertEqual(r["execution"], "DISABLED")

    def test_false_sha_conflicts(self):
        self.assertEqual(reconcile(dict(LEAD, sha_prefix="deadbee"), CANONICAL)["state"], "CONFLICT")

    def test_other_repo_conflicts(self):
        self.assertEqual(reconcile(LEAD, dict(CANONICAL, repository={"full_name": "attacker/repo"}))["state"], "CONFLICT")

    def test_other_run_conflicts(self):
        self.assertEqual(reconcile(LEAD, dict(CANONICAL, id=1))["state"], "CONFLICT")

    def test_false_failure_claim_conflicts(self):
        self.assertEqual(reconcile(LEAD, dict(CANONICAL, conclusion="success"))["state"], "CONFLICT")

    def test_nonterminal_abstains(self):
        self.assertEqual(reconcile(LEAD, dict(CANONICAL, status="in_progress", conclusion=None))["state"], "ABSTAIN")

    def test_pr_association_abstains(self):
        self.assertEqual(reconcile(dict(LEAD, pr=765), dict(CANONICAL, pull_requests=[]))["state"], "ABSTAIN")

    def test_no_email_authorization(self):
        self.assertEqual(reconcile(dict(LEAD, authority="GRANTED"), CANONICAL)["authority"], "NONE")

    def test_no_token_fails_closed(self):
        with self.assertRaises(VerificationDenied):
            verify_lead(LEAD, github_token="")

    def test_invalid_run_id_prevents_network(self):
        with patch("urllib.request.urlopen") as network:
            with self.assertRaises(VerificationDenied):
                verify_lead(dict(LEAD, run_id=-1), github_token="example")
            network.assert_not_called()


if __name__ == "__main__":
    unittest.main()
