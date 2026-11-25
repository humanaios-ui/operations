"""Offline falsifier tests for issue #1090. Not a live Witness claim."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "experiments/witness-live-proof/prove_existing_witness.py"
spec = importlib.util.spec_from_file_location("existing_witness_proof", SCRIPT)
proof = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proof)
NONCE = "0123456789abcdef0123456789abcdef"


def good_payload():
    answer = "WITNESS_ACK:" + NONCE + " I do not authorize work."
    return {
        "answer": answer, "authority": "NONE",
        "answer_sha256": hashlib.sha256(answer.encode()).hexdigest(),
        "source_manifest": [
            {"filename": name, "sha256": "a" * 64, "truncated": False}
            for name in proof.EXPECTED_CONTEXT
        ],
    }


class ExistingWitnessLiveProofTests(unittest.TestCase):
    def test_nonce_and_manifest(self):
        result = proof.verify_answer(good_payload(), NONCE)
        self.assertTrue(result["nonce_echo_verified"])
        self.assertEqual(result["authority"], "NONE")
        self.assertEqual(len(result["source_manifest"]), 3)

    def test_nonce_absent_refused(self):
        bad = good_payload()
        bad["answer"] = "No nonce"
        with self.assertRaisesRegex(proof.ProofRefused, "NONCE_NOT_ECHOED"):
            proof.verify_answer(bad, NONCE)

    def test_nonce_substring_refused(self):
        bad = good_payload()
        bad["answer"] = "WITNESS_ACK:" + NONCE + "a"
        with self.assertRaisesRegex(proof.ProofRefused, "NONCE_NOT_ECHOED"):
            proof.verify_answer(bad, NONCE)

    def test_authority_escalation_refused(self):
        bad = good_payload()
        bad["authority"] = "APPROVED"
        with self.assertRaisesRegex(proof.ProofRefused, "AUTHORITY_NOT_NONE"):
            proof.verify_answer(bad, NONCE)

    def test_incomplete_refused(self):
        bad = good_payload()
        bad["response_may_be_incomplete"] = True
        with self.assertRaisesRegex(proof.ProofRefused, "INCOMPLETE_RESPONSE"):
            proof.verify_answer(bad, NONCE)

    def test_wrong_source_manifest_refused(self):
        bad = good_payload()
        bad["source_manifest"] = bad["source_manifest"][:1]
        with self.assertRaisesRegex(proof.ProofRefused, "SOURCE_MANIFEST_WRONG_FILES"):
            proof.verify_answer(bad, NONCE)

    def test_source_digest_absent_refused(self):
        bad = good_payload()
        bad["source_manifest"][0]["sha256"] = "not-hash"
        with self.assertRaisesRegex(proof.ProofRefused, "SOURCE_DIGEST_MISSING"):
            proof.verify_answer(bad, NONCE)

    def test_reply_digest_mismatch_refused(self):
        bad = good_payload()
        bad["answer_sha256"] = "f" * 64
        with self.assertRaisesRegex(proof.ProofRefused, "RESPONSE_DIGEST_MISMATCH"):
            proof.verify_answer(bad, NONCE)

    def test_fallback_wrapped_payload(self):
        wrapped = SimpleNamespace(is_error=False,
                                  structured_content={"result": good_payload()})
        self.assertEqual(proof.parse_payload(wrapped), good_payload())

    def test_mcp_error_refused(self):
        with self.assertRaisesRegex(proof.ProofRefused, "MCP_TOOL_ERROR"):
            proof.parse_payload(SimpleNamespace(is_error=True))


if __name__ == "__main__":
    unittest.main()
