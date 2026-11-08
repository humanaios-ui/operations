"""Out-of-process deployed-tree check (CodeRabbit thread on pins.py). Written BEFORE the tool (author-run).

tools/deploy_check.py is stdlib-only and imports nothing from src/, so the code being checked cannot vouch for
itself. It is run by the deployer in a SEPARATE process before the writer starts."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from src import pins
from src.writer import digest
from tests.fixtures import make_plan

PKG = Path(__file__).resolve().parents[1]
TOOL = PKG / "tools" / "deploy_check.py"


class Base(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.td = Path(td.name)
        self.pkg = self.td / "pkg"
        for sub in ("src", "integration"):
            shutil.copytree(PKG / sub, self.pkg / sub, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        self.plan = make_plan(Ed25519PrivateKey.generate())
        self.plan_path = self.td / "plan.json"
        self.plan_path.write_text(json.dumps(self.plan))
        self.plan_sha = digest(self.plan)

    def run_tool(self, plan_sha=None, plan_path=None, pkg=None):
        proc = subprocess.run(
            [sys.executable, "-I", str(TOOL), "--package-root", str(pkg or self.pkg),
             "--plan", str(plan_path or self.plan_path), "--plan-sha256", plan_sha or self.plan_sha],
            capture_output=True, text=True, timeout=60)
        try:
            body = json.loads(proc.stdout)
        except ValueError:
            body = None
        return proc.returncode, body


class HonestTree(Base):
    def test_matching_tree_passes_with_exit_0(self):
        code, body = self.run_tool()
        self.assertEqual((code, body["ok"], body["problems"]), (0, True, []))

    def test_tool_does_not_import_the_code_it_checks(self):
        text = TOOL.read_text()
        self.assertNotIn("from src", text); self.assertNotIn("import src", text)
        for forbidden in ("import pins", "from pins", "import writer", "import verifier", "import service",
                          "import responses", "import bridge_v2", "import scoring"):
            self.assertNotIn(forbidden, text)

    def test_tool_file_table_matches_pins_py(self):
        ns = {}
        exec(compile(TOOL.read_text(), str(TOOL), "exec"), ns)
        expected = {name: str(path.relative_to(PKG)) for name, path in pins.FILES.items()}
        self.assertEqual(ns["EXPECTED_FILES"], expected)


class HostileTree(Base):
    def test_modified_pinned_file_is_reported_by_name(self):
        (self.pkg / "src" / "writer.py").write_text("# tampered\n")
        code, body = self.run_tool()
        self.assertEqual(code, 2)
        self.assertIn("HASH_MISMATCH:writer_sha256", body["problems"])

    def test_modified_pins_py_is_caught_even_though_it_defines_the_pins(self):
        (self.pkg / "src" / "pins.py").write_text("# FILES = {} would make every in-process check pass\n")
        code, body = self.run_tool()
        self.assertIn("HASH_MISMATCH:pins_sha256", body["problems"])

    def test_wrong_plan_hash_refused(self):
        code, body = self.run_tool(plan_sha="0" * 64)
        self.assertEqual(code, 2); self.assertIn("PLAN_HASH_MISMATCH", body["problems"])

    def test_edited_plan_pin_is_caught_by_plan_hash(self):
        plan = json.loads(self.plan_path.read_text())
        plan["protocol_pins"]["writer_sha256"] = "f" * 64
        self.plan_path.write_text(json.dumps(plan))
        code, body = self.run_tool()
        self.assertEqual(code, 2); self.assertIn("PLAN_HASH_MISMATCH", body["problems"])

    def test_extra_python_module_that_could_shadow_is_refused(self):
        (self.pkg / "src" / "json.py").write_text("raise SystemExit('shadow')\n")
        code, body = self.run_tool()
        self.assertIn("UNEXPECTED_PYTHON_FILE:src/json.py", body["problems"])

    def test_planted_bytecode_is_refused(self):
        cache = self.pkg / "src" / "__pycache__"; cache.mkdir()
        (cache / "writer.cpython-313.pyc").write_bytes(b"\x00" * 16)
        code, body = self.run_tool()
        self.assertTrue(any(p.startswith("BYTECODE_PRESENT") for p in body["problems"]))

    def test_path_hook_and_sitecustomize_refused(self):
        (self.pkg / "src" / "evil.pth").write_text("import os\n")
        (self.pkg / "sitecustomize.py").write_text("print(1)\n")
        code, body = self.run_tool()
        self.assertTrue(any("evil.pth" in p for p in body["problems"]))
        self.assertTrue(any("sitecustomize.py" in p for p in body["problems"]))

    def test_symlinked_pinned_file_refused(self):
        real = self.td / "elsewhere.py"; shutil.copy(self.pkg / "src" / "verifier.py", real)
        (self.pkg / "src" / "verifier.py").unlink()
        (self.pkg / "src" / "verifier.py").symlink_to(real)
        code, body = self.run_tool()
        self.assertIn("NOT_A_REGULAR_FILE:verifier_sha256", body["problems"])

    def test_modified_package_initializer_is_refused(self):
        # Python runs __init__.py when a package is imported, so it is code even though it is not pinned.
        (self.pkg / "src" / "__init__.py").write_text("import os; os.system('true')\n")
        code, body = self.run_tool()
        self.assertEqual(code, 2)
        self.assertIn("INITIALIZER_NOT_EMPTY:src/__init__.py", body["problems"])

    def test_modified_integration_initializer_is_refused(self):
        (self.pkg / "integration" / "__init__.py").write_text("x = 1\n")
        code, body = self.run_tool()
        self.assertIn("INITIALIZER_NOT_EMPTY:integration/__init__.py", body["problems"])

    def test_whitespace_only_initializer_is_still_refused(self):
        (self.pkg / "src" / "__init__.py").write_text("\n")
        code, body = self.run_tool()
        self.assertIn("INITIALIZER_NOT_EMPTY:src/__init__.py", body["problems"])

    def test_stray_python_file_at_the_package_root_is_refused(self):
        (self.pkg / "conftest.py").write_text("x = 1\n")
        code, body = self.run_tool()
        self.assertIn("UNEXPECTED_PYTHON_FILE:conftest.py", body["problems"])

    def test_the_unpinned_demo_allowance_rests_on_nothing_importing_it(self):
        for folder in ("src", "integration"):
            for path in (PKG / folder).glob("*.py"):
                if path.name == "offline_pipe_demo.py":
                    continue
                self.assertNotIn("offline_pipe_demo", path.read_text(), path.name)

    def test_symlinked_directory_inside_the_code_tree_refused(self):
        outside = self.td / "outside"; outside.mkdir(); (outside / "json.py").write_text("x = 1\n")
        (self.pkg / "src" / "sub").symlink_to(outside, target_is_directory=True)
        code, body = self.run_tool()
        self.assertEqual(code, 2)
        self.assertIn("SYMLINK_PRESENT:src/sub", body["problems"])

    def test_missing_pinned_file_reported(self):
        (self.pkg / "integration" / "oracle.py").unlink()
        code, body = self.run_tool()
        self.assertIn("MISSING:oracle_sha256", body["problems"])

    def test_plan_with_missing_pin_reported(self):
        plan = json.loads(self.plan_path.read_text()); del plan["protocol_pins"]["responses_sha256"]
        self.plan_path.write_text(json.dumps(plan))
        code, body = self.run_tool(plan_sha=digest(plan))
        self.assertIn("PIN_MISSING_IN_PLAN:responses_sha256", body["problems"])

    def test_unreadable_plan_fails_closed_with_exit_2(self):
        code, body = self.run_tool(plan_path=self.td / "nope.json")
        self.assertEqual(code, 2); self.assertFalse(body["ok"])


if __name__ == "__main__":
    unittest.main()
