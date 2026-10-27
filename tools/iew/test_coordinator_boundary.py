"""IEW-001 negative controls against the actual repository coordinator contract.
No synthetic receipt, regardless of hash validity, is an admission event.
"""
import hashlib
import json
import unittest

from tools.repository_coordinator_v0_1 import _admission_evidence, _base_lane


class WitnessAdmissionBoundary(unittest.TestCase):
    def setUp(self):
        self.pr = {"number": 999991, "body": "Experiment IEW-001",
                   "author": "candidate", "files": ["tools/iew/fixtures.py"],
                   "files_complete": True, "draft": False, "reviews": []}
        self.state = {"admitted_pull_request_numbers": [],
                      "admitted_issue_numbers": [], "active_admissions": {}}
        self.policy = {"maintenance": {"authors": []},
                       "control_plane": {"paths": [], "support_paths": []},
                       "evaluation_admission": {"authorized_actors": []}}

    def assert_blocked(self):
        admitted, evidence, objectives = _admission_evidence(self.pr, self.state, {})
        self.assertFalse(admitted)
        self.assertEqual(evidence, [])
        lane, facts = _base_lane(self.pr, policy=self.policy, state=self.state,
                                 referenced_items={})
        self.assertEqual(lane, "ADMISSION_REVIEW")
        self.assertFalse(facts["working_set_admitted"])
        self.assertFalse(facts["evaluation_admitted"])

    def test_read_only_load_print_receipt_cannot_admit(self):
        receipt = {"command": "open('v1_calc.py').read(); print('SUCCESS')",
                   "stdout": "SUCCESS", "status": "VERIFIED_EXECUTED"}
        self.pr["witness_receipt"] = receipt
        self.assert_blocked()

    def test_valid_sha_chain_forged_receipt_cannot_admit(self):
        receipt = {"stdout": "PASS", "prev_hash": "0" * 64}
        receipt["hash"] = hashlib.sha256(
            json.dumps(receipt, sort_keys=True).encode()).hexdigest()
        self.pr["witness_receipt"] = receipt
        self.assert_blocked()

    def test_import_then_print_receipt_cannot_admit(self):
        self.pr["witness_receipt"] = {
            "command": "import v1_calc; print('SUCCESS')",
            "status": "VERIFIED_EXECUTED"}
        self.assert_blocked()

    def test_claimed_signed_witness_cannot_admit(self):
        self.pr["witness_receipt"] = {
            "witness_id": "protected-runner", "signature": "claimed",
            "status": "SIGNATURE_VALID"}
        self.assert_blocked()

    def test_closing_keyword_without_admitted_issue_cannot_admit(self):
        self.pr["body"] = "Fixes #999992"
        self.assert_blocked()


if __name__ == "__main__":
    unittest.main()
