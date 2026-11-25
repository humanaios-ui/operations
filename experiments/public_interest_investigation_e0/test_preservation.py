"""Regression tests for the preservation gate; never alter the frozen baseline."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from verify_preservation import verify

ROOT = Path(__file__).resolve().parent


class PreservationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        shutil.copytree(ROOT / "baseline", self.root / "baseline")
        shutil.copy2(ROOT / "baseline_receipt.json", self.root)
        self.extracted = self.root / "baseline" / "public_evidence_e0"
        self.archive = self.root / "baseline" / "public_evidence_e0.zip"

    def test_valid_baseline(self):
        result = verify(self.root)
        self.assertEqual(result["local_byte_integrity"], "PASS")
        self.assertEqual(result["manifest_entries"], 14)
        self.assertEqual(result["extracted_files"], 15)
        self.assertEqual(result["repository_readback"], "REQUIRED_SEPARATELY")

    def test_missing_archive(self):
        self.archive.unlink()
        with self.assertRaises(OSError):
            verify(self.root)

    def test_changed_archive(self):
        with self.archive.open("ab") as f:
            f.write(b"changed")
        with self.assertRaises(ValueError):
            verify(self.root)

    def test_missing_extracted_file(self):
        (self.extracted / "README.md").unlink()
        with self.assertRaises(ValueError):
            verify(self.root)

    def test_changed_extracted_file(self):
        (self.extracted / "README.md").write_bytes(b"changed")
        with self.assertRaises(ValueError):
            verify(self.root)

    def test_extra_extracted_file(self):
        (self.extracted / "unlisted.txt").write_text("extra")
        with self.assertRaises(ValueError):
            verify(self.root)

    def test_authority_promotion(self):
        p = self.root / "baseline_receipt.json"
        r = json.loads(p.read_text())
        r["authority_effect"] = "ADMITTED"
        p.write_text(json.dumps(r))
        with self.assertRaises(ValueError):
            verify(self.root)

    def test_missing_digest(self):
        p = self.root / "baseline_receipt.json"
        r = json.loads(p.read_text())
        del r["archive_sha256"]
        p.write_text(json.dumps(r))
        with self.assertRaises(KeyError):
            verify(self.root)


if __name__ == "__main__":
    unittest.main()
