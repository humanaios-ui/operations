"""
test_builder_compliance_scanner.py
Builder v1.7 compliant
HumanAIOS
"""
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1]
SCANNER_PATH = TOOLS_DIR / "builder_compliance_scanner_v1.0.py"
SPEC = importlib.util.spec_from_file_location("builder_compliance_scanner", SCANNER_PATH)
scanner = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(scanner)


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_directory_scan_only_counts_builder_corpus_files():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write(
            root / "good_tool_v1_0.py",
            "\n".join([
                "#!/usr/bin/env python3",
                '"""',
                "Builder v1.7 compliant",
                "HumanAIOS",
                '"""',
                "TOOL_NAME = 'good_tool'",
                "TOOL_VERSION = '1.0.0'",
                "class SpecLoadFailed(Exception): pass",
                "def write_report(o, d): pass",
                "def run_smoke_test(): return True",
                "if __name__ == '__main__':",
                "    run_smoke_test()",
                "",
            ]),
        )
        _write(root / "legacy_helper.py", "def helper():\n    return 1\n")
        _write(root / "tests" / "test_sample.py", "def test_thing():\n    assert True\n")
        _write(root / "broken_ARCHIVED_2026-01-01.py", "def broken(\n")

        results = scanner.scan_directory(str(root))
        output = scanner.aggregate(results)

        assert len(results) == 1
        assert results[0]["file"].endswith("good_tool_v1_0.py")
        assert output["files_scanned"] == 1
        assert output["files_passed"] == 1
        assert output["pass_rate"] == 1.0


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
