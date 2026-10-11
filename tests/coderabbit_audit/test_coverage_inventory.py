"""Negative controls for the CodeRabbit coverage pilot (#806)."""
import importlib.util
import unittest
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


if __name__ == "__main__":
    unittest.main()
