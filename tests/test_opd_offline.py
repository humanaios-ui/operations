"""OPD must stay unable to authorize, execute or learn from untrusted traces."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("opd", ROOT / "tools/opd/offline_distiller.py")
opd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(opd)

def trace(i, head=None):
    return {"schema": opd.SCHEMA, "trace_id": str(i),
            "repository": "humanaios-ui/operations",
            "head_sha": head or ("%040x" % (i + 1)), "state": {"ci": "failure"},
            "proposed_action": {"kind": "diagnose_ci", "category": "permission_error"},
            "corrected_action": {"kind": "prepare_evidence", "category": "permission_error"},
            "outcome": {"status": "verified"},
            "evidence": {"source": "protected_ci",
                         "url": "https://github.com/humanaios-ui/operations/actions/runs/123"},
            "authority_effect": "NONE"}

class OfflineDistillerTests(unittest.TestCase):
    def test_candidate_requires_two_distinct_heads(self):
        self.assertEqual(opd.compile_rules([trace(1)])["rules"], [])
        policy = opd.compile_rules([trace(1), trace(2)])
        self.assertEqual(len(policy["rules"]), 1)
        self.assertEqual(opd.replay([trace(3)], policy)["correct"], 1)

    def test_admission_actions_rejected(self):
        for kind in ("admit", "approve", "merge", "dispatch", "publish_receipt"):
            t = trace(1)
            t["corrected_action"]["kind"] = kind
            self.assertFalse(opd.validate(t)[0])
            self.assertEqual(opd.compile_rules([t])["rules"], [])

    def test_comments_are_not_evidence(self):
        t = trace(1)
        t["evidence"]["source"] = "issue_comment"
        self.assertFalse(opd.validate(t)[0])

    def test_exact_sha_required(self):
        t = trace(1)
        t["head_sha"] = "main"
        self.assertFalse(opd.validate(t)[0])

    def test_outcome_and_authority_fail_closed(self):
        for field, value in (("outcome", {"status": "claimed"}),
                             ("authority_effect", "ADMITTED")):
            t = trace(1)
            t[field] = value
            self.assertFalse(opd.validate(t)[0])

    def test_payload_cannot_contain_commands(self):
        t = trace(1)
        t["corrected_action"]["command"] = "gh pr merge 1"
        self.assertFalse(opd.validate(t)[0])

    def test_no_train_holdout_leakage_and_baseline(self):
        policy = opd.compile_rules([trace(1), trace(2)])
        result = opd.replay([trace(3), trace(4)], policy)
        self.assertEqual(result["coverage"], 1.0)
        self.assertEqual(result["authority_bypasses"], 0)
        self.assertTrue(result["safety_preserved"])

    def test_duplicate_does_not_establish_independence(self):
        policy = opd.compile_rules([trace(1), trace(1)])
        self.assertFalse(policy["rules"])

    def test_untrusted_trace_not_counted(self):
        t = trace(3)
        t["evidence"]["url"] = "https://example.com/fake"
        self.assertEqual(opd.replay([t], opd.compile_rules([trace(1), trace(2)]))["eligible"], 0)

if __name__ == "__main__":
    unittest.main()
