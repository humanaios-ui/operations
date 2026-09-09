"""
test_builder_compliance_scanner.py
Builder v1.7 compliant
HumanAIOS
"""
from __future__ import annotations

import tempfile
import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_scanner():
    tools_dir = Path(__file__).resolve().parents[1]
    module_path = tools_dir / "builder_compliance_scanner_v1.0.py"
    spec = spec_from_file_location("builder_compliance_scanner", module_path)
    module = module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestBuilderComplianceScanner(unittest.TestCase):
    def test_directory_scan_skips_non_corpus_files(self):
        scanner = _load_scanner()
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            (tmp_path / "good_tool_v1_0.py").write_text(
                "\n".join(
                    [
                        "#!/usr/bin/env python3",
                        '"""Builder v1.7 compliant HumanAIOS"""',
                        "import argparse",
                        "TOOL_NAME = 'good_tool'",
                        "TOOL_VERSION = '1.0.0'",
                        "class SpecLoadFailed(Exception): pass",
                        "def write_report(*_args): pass",
                        "def run_smoke_test(): return True",
                        "if __name__ == '__main__': argparse.ArgumentParser()",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (tmp_path / "__init__.py").write_text("def noop():\n    return 1\n", encoding="utf-8")
            (tmp_path / "acat_archived_tool.py").write_text("def noop():\n    return 1\n", encoding="utf-8")
            (tmp_path / "acat_adversarial_tool.py").write_text("def noop():\n    return 1\n", encoding="utf-8")
            (tmp_path / "tests").mkdir()
            (tmp_path / "tests" / "test_helper.py").write_text("def noop():\n    return 1\n", encoding="utf-8")

            results = scanner.scan_directory(tmp_path)
            self.assertEqual([Path(r["file"]).name for r in results], ["good_tool_v1_0.py"])
            self.assertTrue(results[0]["passed"])

    def test_explicit_file_scan_does_not_apply_directory_skips(self):
        scanner = _load_scanner()
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            skip_name_file = tmp_path / "tests" / "test_helper.py"
            skip_name_file.parent.mkdir()
            skip_name_file.write_text("def noop():\n    return 1\n", encoding="utf-8")

            results = scanner.scan_directory(skip_name_file)
            self.assertEqual(len(results), 1)
            self.assertEqual(Path(results[0]["file"]).name, "test_helper.py")
