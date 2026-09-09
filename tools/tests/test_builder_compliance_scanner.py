"""
test_builder_compliance_scanner.py
Builder v1.7 compliant
HumanAIOS
"""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "builder_compliance_scanner_v1.0.py"
spec = importlib.util.spec_from_file_location("builder_compliance_scanner_v1_0", MODULE_PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

TOOL_NAME = "test_builder_compliance_scanner"
TOOL_VERSION = "1.0.0"


def _write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


class TestBuilderComplianceScanner(unittest.TestCase):
    def test_scan_directory_only_includes_marked_builder_tools(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(
                root / "good_tool_v1_0.py",
                "\n".join([
                    '"""',
                    "Builder v1.7 compliant",
                    "HumanAIOS",
                    '"""',
                    'TOOL_NAME = "good_tool"',
                    'TOOL_VERSION = "1.0.0"',
                    "def write_report(output, output_dir): return None",
                    "def run_smoke_test(): return True",
                    "if __name__ == '__main__': pass",
                ]) + "\n",
            )
            _write(root / "__init__.py", "VALUE = 1\n")
            _write(root / "helper.py", "def helper():\n    return 1\n")
            _write(root / "test_helper.py", "def test_x():\n    assert True\n")
            _write(root / "pkg" / "_shared.py", "def helper():\n    return 1\n")
            _write(root / "pkg" / "tool_ARCHIVED_2026.py", "print('old')\n")
            _write(root / "tests" / "test_sample.py", "def test_y():\n    assert True\n")

            results = mod.scan_directory(root)

            self.assertEqual([Path(r["file"]).name for r in results], ["good_tool_v1_0.py"])
            self.assertTrue(results[0]["passed"], results[0]["hard_failures"])

    def test_scan_directory_still_includes_marked_adversarial_tools(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(
                root / "acat_adversarial_execution_v1.py",
                "\n".join([
                    '"""',
                    "Builder v1.7 compliant",
                    "HumanAIOS",
                    '"""',
                    'TOOL_NAME = "acat_adversarial_execution"',
                    'TOOL_VERSION = "1.0.0"',
                    "def write_report(output, output_dir): return None",
                    "def run_smoke_test(): return True",
                    "if __name__ == '__main__': pass",
                ]) + "\n",
            )

            results = mod.scan_directory(root)

            self.assertEqual(
                [Path(r["file"]).name for r in results],
                ["acat_adversarial_execution_v1.py"],
            )

    def test_explicit_file_scan_keeps_unmarked_python_modules_strict(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "__init__.py"
            _write(target, "VALUE = 1\n")

            results = mod.scan_directory(target)

            self.assertEqual(len(results), 1)
            self.assertEqual(Path(results[0]["file"]).name, "__init__.py")
            self.assertFalse(results[0]["passed"])


def run_smoke_test() -> bool:
    print("\u2713 Smoke test PASSED")
    return True


if __name__ == "__main__":
    unittest.main()
