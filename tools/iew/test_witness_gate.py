import hashlib
import unittest
from tools.iew.witness_gate import classify_evidence, digest

SOURCE = digest(b"source at pinned ref")
INPUT = digest(b"fixed input")
OBSERVED = {"source_sha256": SOURCE, "input_sha256": INPUT,
            "stdout_sha256": digest(b"ACTUAL"), "exit_code": 0}

class WitnessGateAttacks(unittest.TestCase):
    def verify(self, receipt, obs=None, trusted=True):
        return classify_evidence(receipt, observed=obs, trusted_context=trusted,
                                 expected_source_sha256=SOURCE, expected_input_sha256=INPUT)

    def test_read_only_file_access_fake_print_rejected(self):
        self.assertEqual(self.verify({"stdout":"FAKE", "exit_code":0}, OBSERVED)["reason"], "OUTCOME_MISMATCH")

    def test_import_then_print_fake_rejected(self):
        self.assertEqual(self.verify({"stdout":"FAKE", "exit_code":0}, OBSERVED)["result"], "BLOCKED")

    def test_forged_sha256_append_rejected_without_witness(self):
        forged = {"stdout":"FAKE", "exit_code":0, "prev_hash":"0"*64}
        forged["chain_hash"] = digest(str(forged).encode())
        self.assertEqual(self.verify(forged, None)["reason"], "NO_INDEPENDENT_WITNESS")

    def test_self_declared_witness_not_trusted(self):
        claim = {"stdout":"ACTUAL", "exit_code":0, "trusted_context":True}
        self.assertEqual(self.verify(claim, OBSERVED, trusted=False)["result"], "BLOCKED")

    def test_pinned_source_mismatch(self):
        self.assertEqual(self.verify({"stdout":"ACTUAL", "exit_code":0},
                                     {**OBSERVED, "source_sha256":"0"*64})["result"], "BLOCKED")

    def test_pinned_input_mismatch(self):
        self.assertEqual(self.verify({"stdout":"ACTUAL", "exit_code":0},
                                     {**OBSERVED, "input_sha256":"0"*64})["result"], "BLOCKED")

    def test_matching_observed_bytes_still_not_authorization(self):
        got = self.verify({"stdout":"ACTUAL", "exit_code":0}, OBSERVED)
        self.assertEqual(got["result"], "OUTCOME_MATCH")
        self.assertEqual(got["admission_effect"], "NONE")
        self.assertFalse(got["independently_attested"])

    def test_signed_or_verified_labels_are_inert(self):
        self.assertEqual(self.verify({"stdout":"FAKE", "exit_code":0,
                        "status":"VERIFIED_EXECUTED", "signature":"claim"}, OBSERVED)["result"], "BLOCKED")

if __name__ == "__main__":
    unittest.main()
