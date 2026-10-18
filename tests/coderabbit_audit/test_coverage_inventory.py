"""Negative controls for the CodeRabbit coverage pilot (#806)."""
import importlib.util
import unittest
from unittest.mock import patch
from pathlib import Path

MODULE = Path(__file__).resolve().parents[2] / "tools/coderabbit_coverage_inventory.py"
spec = importlib.util.spec_from_file_location("coderabbit_coverage_inventory", MODULE)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Cannot load coverage inventory module: {MODULE}")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class CoverageTests(unittest.TestCase):
    def fixture(self):
        return {
            "files": [
                {
                    "path": "a.py",
                    "status": "PENDING",
                    "disposition": "pending",
                    "file_kind": "source_code_and_comments",
                    "classification_basis": "test",
                    "sensitivity": "UNASSESSED",
                    "owner": "UNRESOLVED",
                    "generator": "UNRESOLVED",
                    "document_metadata": {
                        "doc_id": None,
                        "registry_state": "NOT_CROSS_REFERENCED",
                        "approval_state": "UNASSESSED",
                        "fpcp_lifecycle": "UNASSESSED",
                        "references_to": "UNASSESSED",
                        "tests_for": "UNASSESSED",
                        "visibility": "UNASSESSED",
                    },
                    "reason": "no review",
                    "review_receipt": None,
                },
                {
                    "path": "b.pdf",
                    "status": "UNSUPPORTED",
                    "disposition": "metadata_only",
                    "file_kind": "binary_media",
                    "classification_basis": "test",
                    "sensitivity": "UNASSESSED",
                    "owner": "UNRESOLVED",
                    "generator": "UNRESOLVED",
                    "document_metadata": {
                        "doc_id": None,
                        "registry_state": "NOT_CROSS_REFERENCED",
                        "approval_state": "UNASSESSED",
                        "fpcp_lifecycle": "UNASSESSED",
                        "references_to": "UNASSESSED",
                        "tests_for": "UNASSESSED",
                        "visibility": "UNASSESSED",
                    },
                    "reason": "binary",
                    "review_receipt": None,
                },
            ],
            "commit": "a" * 40,
            "checkpoint": {
                "complete": True,
                "page_complete": True,
                "after_path": None,
                "next_after_path": None,
                "total_tree_paths": 2,
                "covered_paths": 2,
            },
        }

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

    def test_pending_forged_receipt_never_promotes(self):
        d = self.fixture()
        d["files"][0]["review_receipt"] = {"bot": "coderabbit", "signed": True}
        self.assertEqual(mod.validate(d)["reviewed_authenticated"], 0)

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
            record("120000", "blob", "f" * 40, "docs/current"),
            record("100644", "blob", "1" * 40, "src/app.py"),
            record("100644", "blob", "2" * 40, "tests/test_app.py"),
            record("100644", "blob", "3" * 40, "TOOLS_MANIFEST.md"),
        ])
        with patch.object(mod, "git", side_effect=[sha.encode(), tree]) as mock:
            report = mod.inventory(sha)
            self.assertEqual(report["generated_by"]["path"], "tools/coderabbit_coverage_inventory.py")
            self.assertRegex(report["generated_by"]["sha256"], r"^[a-f0-9]{64}$")
        self.assertEqual(mock.call_args_list[1].args, ("ls-tree", "-rz", "--full-tree", sha))
        by_path = {row["path"]: row for row in report["files"]}
        self.assertEqual(by_path[".env"]["status"], "NOT_APPLICABLE")
        self.assertEqual(by_path[".env"]["disposition"], "excluded_with_reason")
        self.assertEqual(by_path[".env"]["sensitivity"], "POTENTIALLY_SENSITIVE")
        self.assertEqual(by_path["static/photo.png"]["status"], "UNSUPPORTED")
        self.assertEqual(by_path["static/photo.png"]["disposition"], "metadata_only")
        self.assertEqual(by_path["vendor/dependency"]["status"], "UNSUPPORTED")
        self.assertEqual(by_path["vendor/dependency"]["file_kind"], "submodule")
        self.assertEqual(by_path["docs/current"]["file_kind"], "symlink")
        self.assertEqual(by_path["docs/readme.md"]["status"], "PENDING")
        self.assertEqual(by_path["docs/readme.md"]["document_metadata"]["registry_state"], "NOT_CROSS_REFERENCED")
        self.assertEqual(by_path["src/app.py"]["file_kind"], "source_code_and_comments")
        self.assertEqual(by_path["tests/test_app.py"]["file_kind"], "test_fixture_data")
        self.assertEqual(by_path["TOOLS_MANIFEST.md"]["file_kind"], "generated_rendered")
        self.assertEqual(by_path[".env"]["path_bytes_hex"], b".env".hex())
        self.assertEqual([r["path"] for r in report["files"]], sorted(by_path))
        report["summary"] = mod.validate(report)
        self.assertEqual(report["summary"]["tree_tracked"], 8)
        self.assertEqual(sum(report["summary"]["disposition_counts"].values()), 8)
        self.assertTrue(report["summary"]["census_complete"])

    def test_rejects_moving_or_short_ref(self):
        full = "f" * 40
        for candidate in ("main", full[:12]):
            with self.subTest(candidate=candidate):
                with patch.object(mod, "git", return_value=full.encode()):
                    with self.assertRaisesRegex(ValueError, "40-character"):
                        mod.inventory(candidate)

    def test_checkpoints_resume_after_exact_tree_path(self):
        sha = "a" * 40
        tree = b"".join(
            f"100644 blob {oid * 40}\t{path}".encode() + b"\0"
            for oid, path in zip("bcde", ("a.md", "b.md", "c.md", "d.md"))
        )
        with patch.object(mod, "git", side_effect=[sha.encode(), tree]):
            first = mod.inventory(sha, limit=2)
        self.assertFalse(first["checkpoint"]["complete"])
        self.assertEqual(first["checkpoint"]["next_after_path"], "b.md")
        self.assertEqual([row["path"] for row in first["files"]], ["a.md", "b.md"])

        with patch.object(mod, "git", side_effect=[sha.encode(), tree]):
            second = mod.inventory(sha, after_path=first["checkpoint"]["next_after_path"], limit=2)
        self.assertEqual([row["path"] for row in second["files"]], ["c.md", "d.md"])
        self.assertTrue(second["checkpoint"]["page_complete"])
        self.assertFalse(second["checkpoint"]["complete"])

    def test_checkpoint_cursor_and_limit_fail_closed(self):
        sha = "a" * 40
        tree = b"100644 blob " + b"b" * 40 + b"\ta.md\0"
        with patch.object(mod, "git", side_effect=[sha.encode(), tree]):
            with self.assertRaisesRegex(ValueError, "exactly match"):
                mod.inventory(sha, after_path="missing.md")
        with patch.object(mod, "git", side_effect=[sha.encode()]):
            with self.assertRaisesRegex(ValueError, "at least 1"):
                mod.inventory(sha, limit=0)

    def test_unverified_dispositions_cannot_be_claimed(self):
        report = self.fixture()
        report["files"][0]["disposition"] = "evidence_mapped"
        with self.assertRaisesRegex(ValueError, "cannot assert"):
            mod.validate(report)

    def test_dashboard_lists_each_metadata_only_or_excluded_path(self):
        report = self.fixture()
        report["files"].extend([
            {
                "path": "hidden\\npath.png",
                "status": "UNSUPPORTED",
                "disposition": "metadata_only",
                "file_kind": "binary_media",
                "classification_basis": "test",
                "sensitivity": "UNASSESSED",
                "owner": "UNRESOLVED",
                "generator": "UNRESOLVED",
                "document_metadata": {
                    "doc_id": None,
                    "registry_state": "NOT_CROSS_REFERENCED",
                    "approval_state": "UNASSESSED",
                    "fpcp_lifecycle": "UNASSESSED",
                    "references_to": "UNASSESSED",
                    "tests_for": "UNASSESSED",
                    "visibility": "UNASSESSED",
                },
                "reason": "content not inspected",
            },
            {
                "path": ".env",
                "status": "NOT_APPLICABLE",
                "disposition": "excluded_with_reason",
                "file_kind": "secret_sensitive_candidate",
                "classification_basis": "test",
                "sensitivity": "POTENTIALLY_SENSITIVE",
                "owner": "UNRESOLVED",
                "generator": "UNRESOLVED",
                "document_metadata": {
                    "doc_id": None,
                    "registry_state": "NOT_CROSS_REFERENCED",
                    "approval_state": "UNASSESSED",
                    "fpcp_lifecycle": "UNASSESSED",
                    "references_to": "UNASSESSED",
                    "tests_for": "UNASSESSED",
                    "visibility": "UNASSESSED",
                },
                "reason": "potentially sensitive",
            },
        ])
        report["files"].sort(key=lambda row: row["path"])
        report["checkpoint"] = {
            "complete": True,
            "page_complete": True,
            "after_path": None,
            "next_after_path": None,
            "total_tree_paths": 4,
            "covered_paths": 4,
        }
        report["summary"] = mod.validate(report)
        dashboard = mod.render_dashboard(report)
        self.assertIn("`hidden\\\\npath.png`", dashboard)
        self.assertIn("`.env`", dashboard)
        self.assertEqual(dashboard.count("potentially sensitive"), 1)
        self.assertIn("CodeRabbit is not called or authenticated", dashboard)

    def test_rejects_reviewed_even_if_receipt_is_embedded(self):
        d = self.fixture()
        d["files"][0].update(status="REVIEWED", reason="claimed", review_receipt={"signed": True})
        with self.assertRaisesRegex(ValueError, "forbidden"):
            mod.validate(d)

if __name__ == "__main__":
    unittest.main()
