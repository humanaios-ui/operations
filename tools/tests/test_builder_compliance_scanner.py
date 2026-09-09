"""
test_builder_compliance_scanner.py
Builder v1.7 compliant - builder_compliance_scanner_tests
HumanAIOS - S-090926-builder-compliance-fix
Focused tests for directory-scan target selection in builder_compliance_scanner_v1.0.py.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

try:
    import pytest
except ModuleNotFoundError:  # pragma: no cover
    pytest = None

TOOL_NAME = "test_builder_compliance_scanner"
TOOL_VERSION = "1.0.0"

TOOLS_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = TOOLS_DIR / "builder_compliance_scanner_v1.0.py"

spec = importlib.util.spec_from_file_location("builder_compliance_scanner_v1_0", MODULE_PATH)
scanner = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(scanner)


def _write(path: Path, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def test_directory_scan_skips_support_and_validation_files(tmp_path):
    compliant = """#!/usr/bin/env python3
# Builder v1.7 compliant
# HumanAIOS
TOOL_NAME = "kept_tool"
TOOL_VERSION = "1.0.0"
def run_smoke_test(): return True
if __name__ == "__main__": run_smoke_test()
"""
    helper = "def helper():\n    return True\n"
    _write(tmp_path / "kept_tool_v1_0.py", compliant)
    _write(tmp_path / "agents" / "api_monitoring_bot_v1.py", helper)
    _write(tmp_path / "tests" / "test_tool.py", helper)
    _write(tmp_path / "__init__.py", helper)
    _write(tmp_path / "acat_adversarial_suite_v1.py", helper)
    _write(tmp_path / "legacy_ARCHIVED_2026-07-16.py", helper)

    results = scanner.scan_directory(tmp_path)

    assert [Path(result["file"]).name for result in results] == ["kept_tool_v1_0.py"]


def test_explicit_file_scan_still_checks_skipped_categories(tmp_path):
    target = _write(tmp_path / "agents" / "api_monitoring_bot_v1.py", "def helper():\n    return True\n")

    results = scanner.scan_directory(target)

    assert len(results) == 1
    assert Path(results[0]["file"]).name == "api_monitoring_bot_v1.py"
    assert not results[0]["passed"]


def test_smag_predict_lint_passes_builder_checks():
    results = scanner.scan_directory(TOOLS_DIR / "smag_predict_lint.py")

    assert len(results) == 1
    assert results[0]["passed"], results[0]["hard_failures"]
