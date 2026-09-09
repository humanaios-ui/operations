"""
HumanAIOS
Builder v1.7 compliant
"""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "builder_compliance_scanner_v1.0.py"
spec = importlib.util.spec_from_file_location("builder_compliance_scanner_v1_0", MODULE_PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _builder_tool(name: str = "good_tool") -> str:
    return "\n".join([
        "#!/usr/bin/env python3",
        '"""',
        "Builder v1.7 compliant",
        "HumanAIOS",
        '"""',
        "import argparse",
        "",
        f'TOOL_NAME = "{name}"',
        'TOOL_VERSION = "1.0.0"',
        "",
        "class SpecLoadFailed(Exception):",
        "    pass",
        "",
        "def write_report(output, output_dir):",
        "    return output_dir",
        "",
        "def run_smoke_test():",
        "    return True",
        "",
        "def main():",
        "    argparse.ArgumentParser()",
        "",
        'if __name__ == "__main__":',
        "    main()",
        "",
    ])


class TestBuilderComplianceScanner(unittest.TestCase):
    def test_scan_directory_filters_non_corpus_files(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            (tmp_path / "good_tool_v1_0.py").write_text(_builder_tool(), encoding="utf-8")
            (tmp_path / "test_sample.py").write_text(_builder_tool("test_sample"), encoding="utf-8")
            archived = tmp_path / "archived"
            archived.mkdir()
            (archived / "archived_tool_v1_0.py").write_text(_builder_tool("archived_tool"), encoding="utf-8")
            shared = tmp_path / "_shared"
            shared.mkdir()
            (shared / "helper.py").write_text(_builder_tool("helper"), encoding="utf-8")
            (tmp_path / "__init__.py").write_text(_builder_tool("__init__"), encoding="utf-8")
            (tmp_path / "plain_helper.py").write_text("def helper():\n    return True\n", encoding="utf-8")

            results = mod.scan_directory(tmp_path)

        self.assertEqual([Path(result["file"]).name for result in results], ["good_tool_v1_0.py"])
        self.assertTrue(results[0]["passed"])

    def test_scan_directory_keeps_explicit_file_scans_unchanged(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "test_sample.py"
            path.write_text("def helper():\n    return True\n", encoding="utf-8")

            results = mod.scan_directory(path)

        self.assertEqual(len(results), 1)
        self.assertEqual(Path(results[0]["file"]).name, "test_sample.py")
        self.assertFalse(results[0]["passed"])


if __name__ == "__main__":
    unittest.main()
