"""
test_behavioral_compliance_gate.py
Builder v1.7 compliant
HumanAIOS

Tests for behavioral_compliance_gate_v1_0 (issue #98 — IC-045 generalization).

Covers:
  - BEHAV_DOCSTRING_ONLY detection and exemption of @abstractmethod
  - BEHAV_DEAD_CODE_AFTER_RETURN detection
  - BEHAV_DUPLICATE_FUNC_DEF detection
  - Clean file passes all checks
  - Syntax errors are handled gracefully
  - Aggregate and write_report helpers
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

# Make tools/ importable when running directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import behavioral_compliance_gate_v1_0 as gate  # noqa: E402

TOOL_NAME = "test_behavioral_compliance_gate"
TOOL_VERSION = "1.0.0"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_temp(src: str) -> Path:
    """Write source to a temporary file and return its path."""
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    )
    f.write(src)
    f.flush()
    return Path(f.name)


# ---------------------------------------------------------------------------
# BEHAV_DOCSTRING_ONLY
# ---------------------------------------------------------------------------

class TestDocstringOnly(unittest.TestCase):
    def test_docstring_only_function_is_flagged(self):
        src = "def hollow():\n    '''This function has no body.'''\n"
        r = gate.scan_file(_write_temp(src))
        assert not r["passed"]
        assert any("BEHAV_DOCSTRING_ONLY" in f for f in r["hard_failures"])

    def test_function_with_docstring_and_return_is_clean(self):
        src = (
            "def real():\n"
            "    '''Docstring.'''\n"
            "    return 42\n"
        )
        r = gate.scan_file(_write_temp(src))
        assert r["passed"], r["hard_failures"]

    def test_function_with_docstring_and_pass_is_clean(self):
        src = (
            "def stub():\n"
            "    '''Stub.'''\n"
            "    pass\n"
        )
        r = gate.scan_file(_write_temp(src))
        assert r["passed"], r["hard_failures"]

    def test_function_with_no_docstring_and_pass_only_is_clean(self):
        src = "def stub():\n    pass\n"
        r = gate.scan_file(_write_temp(src))
        assert r["passed"], r["hard_failures"]

    def test_abstractmethod_docstring_only_is_exempt(self):
        src = (
            "from abc import abstractmethod\n"
            "class Base:\n"
            "    @abstractmethod\n"
            "    def method(self):\n"
            "        '''Abstract — intentionally body-free.'''\n"
        )
        r = gate.scan_file(_write_temp(src))
        assert r["passed"], r["hard_failures"]

    def test_docstring_only_with_ellipsis_body_is_clean(self):
        """A function with `...` (Ellipsis) as its only statement is an explicit stub."""
        src = "def stub():\n    ...\n"
        r = gate.scan_file(_write_temp(src))
        assert r["passed"], r["hard_failures"]


# ---------------------------------------------------------------------------
# BEHAV_DEAD_CODE_AFTER_RETURN
# ---------------------------------------------------------------------------

class TestDeadCodeAfterReturn(unittest.TestCase):
    def test_statements_after_return_are_flagged(self):
        src = (
            "def bad():\n"
            "    return 1\n"
            "    x = 2  # unreachable\n"
        )
        r = gate.scan_file(_write_temp(src))
        assert not r["passed"]
        assert any("BEHAV_DEAD_CODE_AFTER_RETURN" in f for f in r["hard_failures"])

    def test_return_as_last_statement_is_clean(self):
        src = (
            "def good():\n"
            "    x = 1\n"
            "    return x\n"
        )
        r = gate.scan_file(_write_temp(src))
        assert r["passed"], r["hard_failures"]

    def test_return_inside_if_branch_not_flagged(self):
        """An early return inside an if-block is not dead-code at the top-level body."""
        src = (
            "def branched(x):\n"
            "    if x > 0:\n"
            "        return x\n"
            "    return -x\n"
        )
        r = gate.scan_file(_write_temp(src))
        assert r["passed"], r["hard_failures"]

    def test_ic045_exact_pattern_is_flagged(self):
        """The exact IC-045 pattern: real logic moved after return in run_smoke_test."""
        src = (
            "def run_smoke_test():\n"
            "    '''Smoke.'''\n"
            "    return True\n"
            "    # real logic injected here (dead code)\n"
            "    do_something()\n"
        )
        r = gate.scan_file(_write_temp(src))
        assert not r["passed"]
        assert any("BEHAV_DEAD_CODE_AFTER_RETURN" in f for f in r["hard_failures"])


# ---------------------------------------------------------------------------
# BEHAV_DUPLICATE_FUNC_DEF
# ---------------------------------------------------------------------------

class TestDuplicateFuncDef(unittest.TestCase):
    def test_duplicate_module_level_function_is_flagged(self):
        src = (
            "def run_smoke_test():\n"
            "    return True\n"
            "def run_smoke_test():\n"
            "    return False\n"
        )
        r = gate.scan_file(_write_temp(src))
        assert not r["passed"]
        assert any("BEHAV_DUPLICATE_FUNC_DEF" in f for f in r["hard_failures"])

    def test_single_function_definition_is_clean(self):
        src = (
            "def run_smoke_test():\n"
            "    return True\n"
        )
        r = gate.scan_file(_write_temp(src))
        assert r["passed"], r["hard_failures"]

    def test_same_name_in_different_classes_not_flagged(self):
        """Methods with the same name in different classes are not module-level duplicates."""
        src = (
            "class A:\n"
            "    def method(self): pass\n"
            "class B:\n"
            "    def method(self): pass\n"
        )
        r = gate.scan_file(_write_temp(src))
        assert r["passed"], r["hard_failures"]

    def test_marker_injection_artifact_pattern_is_flagged(self):
        """The exact builder-lint artifact: a stub injected before the real definition."""
        src = (
            "# --smoke-test: run_smoke_test() -> bool\n"
            "def run_smoke_test():\n"
            "    return True\n"
            "\n"
            "# ... real implementation ...\n"
            "\n"
            "def run_smoke_test() -> bool:\n"
            "    '''Real smoke test.'''\n"
            "    result = do_checks()\n"
            "    return result\n"
        )
        r = gate.scan_file(_write_temp(src))
        assert not r["passed"]
        assert any("BEHAV_DUPLICATE_FUNC_DEF" in f for f in r["hard_failures"])


# ---------------------------------------------------------------------------
# Clean file
# ---------------------------------------------------------------------------

class TestCleanFile(unittest.TestCase):
    def test_fully_compliant_file_passes(self):
        src = "\n".join([
            "# Builder v1.7 compliant",
            "# HumanAIOS",
            "TOOL_NAME = 'clean'",
            "TOOL_VERSION = '1.0.0'",
            "",
            "def process(data):",
            "    '''Process the data.'''",
            "    result = [x * 2 for x in data]",
            "    return result",
            "",
            "def run_smoke_test():",
            "    '''Smoke test.'''",
            "    assert process([1, 2]) == [2, 4]",
            "    return True",
            "",
            "if __name__ == '__main__':",
            "    run_smoke_test()",
        ]) + "\n"
        r = gate.scan_file(_write_temp(src))
        assert r["passed"], r["hard_failures"]


# ---------------------------------------------------------------------------
# Syntax error handling
# ---------------------------------------------------------------------------

class TestSyntaxError(unittest.TestCase):
    def test_syntax_error_is_reported_as_failure(self):
        src = "def broken(:\n    pass\n"
        r = gate.scan_file(_write_temp(src))
        assert not r["passed"]
        assert any("SYNTAX_ERROR" in f for f in r["hard_failures"])


# ---------------------------------------------------------------------------
# Aggregate and write_report
# ---------------------------------------------------------------------------

class TestAggregate(unittest.TestCase):
    def test_all_passing_results_in_pass_aggregate(self):
        results = [
            {"file": "a.py", "passed": True, "hard_failures": []},
            {"file": "b.py", "passed": True, "hard_failures": []},
        ]
        out = gate.aggregate(results)
        assert out["status"] == "PASS"
        assert out["pass_rate"] == 1.0

    def test_partial_failure_shows_correct_pass_rate(self):
        results = [
            {"file": "a.py", "passed": True, "hard_failures": []},
            {"file": "b.py", "passed": False, "hard_failures": ["BEHAV_DOCSTRING_ONLY:1: foo()"]},
        ]
        out = gate.aggregate(results)
        assert out["status"] == "FAIL"
        assert out["pass_rate"] == 0.5

    def test_empty_results_pass_rate_is_1(self):
        out = gate.aggregate([])
        assert out["pass_rate"] == 1.0

    def test_write_report_creates_json_file(self):
        with tempfile.TemporaryDirectory() as d:
            out = gate.aggregate([{"file": "x.py", "passed": True, "hard_failures": []}])
            path = gate.write_report(out, d)
            assert Path(path).exists()
            data = json.loads(Path(path).read_text())
            assert data["status"] == "PASS"


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

def run_smoke_test() -> bool:
    """Minimal compliance smoke test."""
    return gate.run_smoke_test()


if __name__ == "__main__":
    unittest.main()
