"""Fresh-checkout E2/E3 smoke imports and E2 verifier, no live provider calls."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from smoke_e2_macos import verify_e2, wait_for_server
from smoke_e3_macos import verify_snapshot_response


def specimen():
    nonce = "safe_non_secret_nonce_1234"
    manifest = [{"filename": name, "truncated": True, "sha256": "a" * 64}
                for name in ("CURRENT.md", "REGISTERED.md", "GOVERNANCE.md")]
    text = nonce + "\nCURRENT.md REGISTERED.md GOVERNANCE.md: supplied truncated context only; authority NONE."
    return nonce, {"answer": text, "authority": "NONE",
                   "response_may_be_incomplete": False, "source_manifest": manifest}


class E2FreshCloneTests(unittest.TestCase):
    def test_e2_and_e3_imported_from_committed_source(self):
        self.assertTrue(callable(wait_for_server))
        self.assertTrue(callable(verify_snapshot_response))
        nonce, packet = specimen()
        result = verify_e2(packet, nonce)
        self.assertTrue(result["nonce_verified"])
        self.assertEqual(result["authority"], "NONE")
        self.assertEqual(len(result["source_files"]), 3)

    def test_refuses_missing_nonce_or_authority_expansion(self):
        nonce, packet = specimen()
        packet["answer"] = "Context only, no nonce"
        with self.assertRaises(RuntimeError):
            verify_e2(packet, nonce)
        _, packet = specimen()
        packet["authority"] = "AUTO_APPROVE"
        with self.assertRaises(RuntimeError):
            verify_e2(packet, nonce)

    def test_refuses_missing_truncation_disclosure(self):
        nonce, packet = specimen()
        packet["answer"] = nonce + " CURRENT.md REGISTERED.md GOVERNANCE.md"
        with self.assertRaises(RuntimeError):
            verify_e2(packet, nonce)


if __name__ == "__main__":
    unittest.main()
