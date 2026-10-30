"""Regression for tools/workflow_path_validator.py (UnboundLocalError on `paths`)."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "tools"))
from workflow_path_validator import validate_workflow_paths  # noqa: E402


class WorkflowPathValidatorTests(unittest.TestCase):
    def setUp(self):
        self.cwd = os.getcwd()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        os.chdir(self.temp.name)
        self.addCleanup(os.chdir, self.cwd)
        Path("tools").mkdir()
        Path("tools/real.py").write_text("x = 1\n")

    def _workflow(self, trigger_block: str) -> str:
        Path("wf.yml").write_text(f"name: t\non:\n{trigger_block}\njobs: {{}}\n")
        return "wf.yml"

    def test_existing_literal_path_passes(self):
        ok, errors, _ = validate_workflow_paths(self._workflow(
            "  pull_request:\n    paths:\n      - tools/real.py\n"))
        self.assertTrue(ok, errors)

    def test_missing_literal_path_is_an_error(self):
        ok, errors, _ = validate_workflow_paths(self._workflow(
            "  pull_request:\n    paths:\n      - tools/missing.py\n"))
        self.assertFalse(ok)
        self.assertTrue(any("not found" in e for e in errors))

    def test_paths_ignore_is_validated_too(self):
        ok, errors, _ = validate_workflow_paths(self._workflow(
            "  push:\n    paths-ignore:\n      - tools/missing.py\n"))
        self.assertFalse(ok)

    def test_non_list_filter_is_an_error_not_a_crash(self):
        ok, errors, _ = validate_workflow_paths(self._workflow(
            "  push:\n    paths: tools/real.py\n"))
        self.assertFalse(ok)
        self.assertTrue(any("must be a list" in e for e in errors))

    def test_trigger_without_filters_and_inline_glob_do_not_crash(self):
        ok, errors, warnings = validate_workflow_paths(self._workflow(
            "  workflow_dispatch:\n  push:\n    paths:\n      - 'nodir/**/*.py'\n"))
        self.assertTrue(ok, errors)
        self.assertTrue(warnings)


if __name__ == "__main__":
    unittest.main()
