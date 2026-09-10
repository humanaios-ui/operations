"""
test_builder_compliance_scanner.py
Builder v1.7 compliant - builder_compliance_scanner_tests
HumanAIOS - S-090926-builder-compliance-fix
Focused tests for directory-scan target selection in builder_compliance_scanner_v1.0.py.
"""
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

TOOL_NAME = "test_builder_compliance_scanner"
TOOL_VERSION = "1.0.0"

TOOLS_DIR = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "builder_compliance_scanner_v1_0",
    TOOLS_DIR / "builder_compliance_scanner_v1.0.py",
)
scanner = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(scanner)


def _write(path: Path, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def test_directory_scan_only_counts_builder_corpus_files():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        compliant = """#!/usr/bin/env python3
# Builder v1.7 compliant
# HumanAIOS
TOOL_NAME = "kept_tool"
TOOL_VERSION = "1.0.0"
class SpecLoadFailed(Exception): pass
def write_report(o, d): pass
def run_smoke_test(): return True
if __name__ == "__main__": run_smoke_test()
"""
        helper = "def helper():\n    return True\n"
        _write(root / "kept_tool_v1_0.py", compliant)
        _write(root / "legacy_helper.py", helper)
        _write(root / "tests" / "test_tool.py", helper)
        _write(root / "__init__.py", helper)
        _write(root / "agents" / "api_monitoring_bot_v1.py", helper)
        _write(root / "acat_adversarial_suite_v1.py", compliant)
        _write(root / "legacy_ARCHIVED_2026-07-16.py", "def broken(\n")

        results = scanner.scan_directory(root)
        output = scanner.aggregate(results)

        assert [Path(result["file"]).name for result in results] == ["kept_tool_v1_0.py"]
        assert output["files_scanned"] == 1
        assert output["files_passed"] == 1
        assert output["pass_rate"] == 1.0


def test_this_module_passes_explicit_file_scan():
    results = scanner.scan_directory(Path(__file__))

    assert len(results) == 1
    assert Path(results[0]["file"]).name == Path(__file__).name
    assert results[0]["passed"], results[0]["hard_failures"]


def test_single_file_scan_skips_test_modules():
    with tempfile.TemporaryDirectory() as tmp:
        path = _write(Path(tmp) / "tests" / "test_sample.py", "def test_thing():\n    assert True\n")
        result = scanner.scan_file(path)

        assert result["passed"] is True
        assert result["skipped"] is True
        assert result["skip_reason"] == "test module"


def test_single_file_scan_still_fails_non_compliant_tool_files():
    with tempfile.TemporaryDirectory() as tmp:
        path = _write(Path(tmp) / "new_tool.py", "def helper():\n    return 1\n")
        result = scanner.scan_file(path)

        assert result["passed"] is False
        assert "BUILDER_MISSING_HEADER" in result["hard_failures"]


def test_directory_scan_ignores_checkout_ancestor_names():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "_checkout" / "live_tools"
        compliant = """#!/usr/bin/env python3
# Builder v1.7 compliant
# HumanAIOS
TOOL_NAME = "kept_tool"
TOOL_VERSION = "1.0.0"
class SpecLoadFailed(Exception): pass
def write_report(o, d): pass
def run_smoke_test(): return True
if __name__ == "__main__": run_smoke_test()
"""
        _write(root / "kept_tool_v1_0.py", compliant)

        results = scanner.scan_directory(root)

        assert [Path(result["file"]).name for result in results] == ["kept_tool_v1_0.py"]
        assert results[0]["passed"], results[0]["hard_failures"]


def test_smag_predict_lint_passes_builder_checks():
    results = scanner.scan_directory(TOOLS_DIR / "smag_predict_lint.py")

    assert len(results) == 1
    assert results[0]["passed"], results[0]["hard_failures"]
