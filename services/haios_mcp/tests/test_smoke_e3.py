"""Deterministic E3 verifier tests; no MCP SDK, network, or local Mac needed."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from smoke_e3_macos import verify_snapshot_response, find_miner_checkout


def sample():
    return {
        "status": "PARTIAL_CANDIDATES_FOR_HUMAN_REVIEW",
        "source_mode": "snapshot", "source_status": "CURATED_SNAPSHOT_NOT_LIVE",
        "source_warning": "two source rows not examined",
        "matched_count": 3, "shown_count": 1, "unshown_match_count": 2,
        "unexamined_count": 2,
        "authority": "NONE", "execution": "DISABLED", "eligibility": "NOT_ASSESSED",
        "receipt_sha256": hashlib.sha256(b"e3").hexdigest(),
        "candidates": [{"resource_id": "SYNTH-E3", "title": "Compute Credits",
                        "source_name": "DEV Community", "source_url": "https://example.org/credits",
                        "route": "WATCH", "eligibility_assessed": False,
                        "source_verification": "UPSTREAM_SNAPSHOT_NOT_INDEPENDENTLY_VERIFIED"}],
    }


class E3Tests(unittest.TestCase):
    def test_preserves_partial_status_source_provenance_and_zero_authority(self):
        r = verify_snapshot_response(sample())
        self.assertEqual(r["unexamined_count"], 2)
        self.assertEqual(r["status"], "PARTIAL_CANDIDATES_FOR_HUMAN_REVIEW")
        self.assertIn("not examined", r["source_warning"])
        self.assertEqual(r["candidates"][0]["source_name"], "DEV Community")
        self.assertEqual(r["eligibility"], "NOT_ASSESSED")
        self.assertEqual(r["execution"], "DISABLED")

    def test_refuses_status_laundering(self):
        p = sample(); p["status"] = "CANDIDATES_FOR_HUMAN_REVIEW"
        with self.assertRaisesRegex(RuntimeError, "Partial status"):
            verify_snapshot_response(p)

    def test_refuses_private_source_or_eligibility_claim(self):
        p = sample(); p["candidates"][0]["source_name"] = "HackerOne private program"
        with self.assertRaisesRegex(RuntimeError, "Non-public"):
            verify_snapshot_response(p)
        p = sample(); p["candidates"][0]["eligibility_assessed"] = True
        with self.assertRaisesRegex(RuntimeError, "asserts eligibility"):
            verify_snapshot_response(p)

    def test_local_miner_discovery_requires_stored_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "resource-miner"
            (root / "resource_miner").mkdir(parents=True)
            (root / "data").mkdir()
            (root / "app.py").write_text("# test stub")
            (root / "resource_miner/intent_os.py").write_text("# test stub")
            with patch.dict("os.environ", {"HAIOS_E3_MINER_ROOT": str(root)}):
                # The user's own custom root is checked first. Other known Mac
                # locations may not exist in this hermetic unit-test environment.
                selected, state = find_miner_checkout()
                self.assertNotEqual(state, "FOUND_LOCAL_STORED_SNAPSHOT")
                (root / "data/resources.snapshot.jsonl").write_text("{}\n")
                selected, state = find_miner_checkout()
                self.assertEqual(selected, root.resolve())
                self.assertEqual(state, "FOUND_LOCAL_STORED_SNAPSHOT")

if __name__ == "__main__":
    unittest.main()