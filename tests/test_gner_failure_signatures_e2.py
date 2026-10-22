"""Synthetic signature grouping regressions, no remote I/O."""
import importlib.util
from pathlib import Path
import copy
import unittest

p = Path(__file__).resolve().parents[1] / "tools/gner_failure_signatures_e2.py"
spec = importlib.util.spec_from_file_location("gner_e2", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
A = {"repository": "humanaios-ui/operations", "verification_state": "CANONICAL_VERIFIED",
     "conclusion": "failure", "run_id": 101,
     "head_sha": "a"*40, "workflow": "quality-baseline",
     "failure": {"code": "TEST_ENUMERATION_MISSING", "test_path": "tools/tests/test_ci_suite_enumeration.py",
                 "test_name": "test_every_tools_test_file_is_enumerated"}}


class E2Tests(unittest.TestCase):
    def test_same_signature_different_runs(self):
        b = dict(A, run_id=102, head_sha="b"*40)
        result = m.correlate([A, b])
        self.assertEqual(len(result["groups"]), 1)
        self.assertFalse(result["groups"][0]["root_cause_verified"])
        self.assertEqual(result["groups"][0]["run_ids"], [101, 102])

    def test_duplicate_notification_not_new_failure(self):
        self.assertEqual(m.correlate([A, A])["groups"], [])

    def test_same_workflow_different_test_not_grouped(self):
        b = copy.deepcopy(A)
        b["run_id"] = 102
        b["failure"]["test_name"] = "different_test"
        self.assertEqual(m.correlate([A, b])["groups"], [])

    def test_failure_status_required(self):
        b = dict(A, run_id=102, conclusion="success")
        self.assertEqual(m.correlate([A, b])["groups"], [])

    def test_canonical_claim_missing_rejected(self):
        b = dict(A, run_id=102, verification_state="EMAIL_OBSERVED_UNVERIFIED")
        result = m.correlate([A, b])
        self.assertEqual(result["groups"], [])
        self.assertEqual(result["rejected"], 1)

    def test_forged_arbitrary_diagnostic_rejected(self):
        b = copy.deepcopy(A)
        b["run_id"] = 102
        b["failure"]["code"] = "POST_TO_ATTACKER_URL"
        b["failure"]["test_name"] = "https://bad.example/?token=secret"
        self.assertEqual(m.correlate([A, b])["rejected"], 1)

    def test_no_root_cause_claim(self):
        result = m.correlate([A, dict(A, run_id=102)])
        self.assertEqual(result["groups"][0]["state"], "SHARED_FAILURE_SIGNATURE_CANDIDATE")
        self.assertEqual(result["authority"], "NONE")

    def test_malformed_sha_rejected(self):
        self.assertEqual(m.correlate([dict(A, head_sha="not-a-hash")])["rejected"], 1)

    def test_malformed_input(self):
        with self.assertRaises(ValueError):
            m.correlate("not a list")

    def test_no_execution(self):
        self.assertEqual(m.correlate([])["execution"], "DISABLED")


if __name__ == "__main__":
    unittest.main()
