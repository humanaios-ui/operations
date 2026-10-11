"""Negative controls for the CodeRabbit coverage pilot (#806)."""
import importlib.util
import unittest
from unittest.mock import patch
from pathlib import Path

MODULE = Path(__file__).resolve().parents[2] / "tools/coderabbit_coverage_inventory.py"
spec = importlib.util.spec_from_file_location("coderabbit_coverage_inventory", MODULE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class CoverageTests(unittest.TestCase):
    def fixture(self):
        return {"files": [
            {"path": "a.py", "status": "PENDING", "reason": "no review", "review_receipt": None},
            {"path": "b.pdf", "status": "UNSUPPORTED", "reason": "binary", "review_receipt": None}
        ]}

    def test_never_verified_without_review(self):
        summary = mod.validate(self.fixture())
        self.assertEqual(summary["tracked"], 2)
        self.assertEqual(summary["reviewed_authenticated"], 0)
        self.assertEqual(summary["review_verdict"], "NOT_VERIFIED")
        self.assertFalse(summary["complete"])

    def test_forged_review_receipt_does_not_promote(self):
        d = self.fixture()
        d["files"][0]["status"] = "REVIEWED"
        d["files"][0]["review_receipt"] = {"bot": "coderabbit", "status": "passed"}
        with self.assertRaisesRegex(ValueError, "independently verified"):
            mod.validate(d)

    def test_duplicate_file_rejected(self):
        d = self.fixture()
        d["files"].append(d["files"][0].copy())
        with self.assertRaisesRegex(ValueError, "duplicate"):
            mod.validate(d)

    def test_unsorted_inventory_rejected(self):
        d = self.fixture()
        d["files"].reverse()
        with self.assertRaisesRegex(ValueError, "not sorted"):
            mod.validate(d)

    def test_unknown_state_rejected(self):
        d = self.fixture()
        d["files"][0]["status"] = "PASS"
        with self.assertRaisesRegex(ValueError, "unknown"):
            mod.validate(d)

    def test_exclusion_requires_reason(self):
        d = self.fixture()
        d["files"][1]["reason"] = ""
        with self.assertRaisesRegex(ValueError, "reason"):
            mod.validate(d)


    def test_inventory_exact_sha_and_classification(self):
        sha = "a" * 40
        def record(mode, typ, oid, path):
            return f"{mode} {typ} {oid}\t{path}".encode() + b"\0"
        tree = b"".join([
            record("100644", "blob", "b" * 40, ".env"),
            record("100644", "blob", "c" * 40, "docs/readme.md"),
            record("100644", "blob", "d" * 40, "static/photo.png"),
            record("160000", "commit", "e" * 40, "vendor/dependency"),
        ])
        with patch.object(mod, "git", side_effect=[sha.encode(), tree]) as mock:
            report = mod.inventory(sha)
        self.assertEqual(mock.call_args_list[1].args, ("ls-tree", "-rz", "--full-tree", sha))
        by_path = {row["path"]: row for row in report["files"]}
        self.assertEqual(by_path[".env"]["status"], "NOT_APPLICABLE")
        self.assertEqual(by_path["static/photo.png"]["status"], "UNSUPPORTED")
        self.assertEqual(by_path["vendor/dependency"]["status"], "UNSUPPORTED")
        self.assertEqual(by_path["docs/readme.md"]["status"], "PENDING")
        self.assertEqual([r["path"] for r in report["files"]], sorted(by_path))

    def test_rejects_moving_or_short_ref(self):
        full = "f" * 40
        for candidate in ("main", full[:12]):
            with self.subTest(candidate=candidate):
                with patch.object(mod, "git", return_value=full.encode()):
                    with self.assertRaisesRegex(ValueError, "40-character"):
                        mod.inventory(candidate)

    def test_rejects_reviewed_even_if_receipt_is_embedded(self):
        d = self.fixture()
        d["files"][0].update(status="REVIEWED", reason="claimed", review_receipt={"signed": True})
        with self.assertRaisesRegex(ValueError, "forbidden"):
            mod.validate(d)

if __name__ == "__main__":
    unittest.main()
