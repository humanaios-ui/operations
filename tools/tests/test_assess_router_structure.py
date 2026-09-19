"""
test_assess_router_structure.py
Builder v1.7 compliant - assess_router_structure_tests
HumanAIOS - IC-045

Regression test for IC-045: the /assess endpoint must have a real body.

Dependency-free and import-free by design. The target module
(assess_router_new_Z2-ASSESS-01.py) has a hyphen in its filename, so it is not
importable, and it imports fastapi + acat services that may be absent in CI.
We therefore verify STRUCTURE via AST, not runtime.

The defect this guards against (IC-045): a marker-injection (builder-lint "fix")
placed a compliance block between the assess() docstring and its body, leaving
assess() as docstring-only (returned None for every call) and re-parenting the
real validation/job-enqueue logic as dead code after a `return` inside an
injected run_smoke_test(). It parsed and passed the marker-presence scanner —
which is exactly why behavioral verification (this test) is required.
"""
from __future__ import annotations

import ast
from pathlib import Path

TOOL_NAME = "test_assess_router_structure"
TOOL_VERSION = "1.0.0"

TARGET = Path(__file__).resolve().parents[1] / "assess_router_new_Z2-ASSESS-01.py"


def _functions(tree):
    return [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]


def _body_after_docstring(fn):
    body = fn.body
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) \
            and isinstance(body[0].value.value, str):
        return body[1:]
    return body


def test_assess_has_real_body():
    tree = ast.parse(TARGET.read_text(encoding="utf-8"))
    assess = next((f for f in _functions(tree) if f.name == "assess"), None)
    assert assess is not None, "assess() endpoint function missing"
    stmts = _body_after_docstring(assess)
    assert len(stmts) >= 3, (
        f"assess() has only {len(stmts)} statement(s) after its docstring — "
        "endpoint body is truncated/removed (IC-045 regression)"
    )
    # The real endpoint returns a dict with a job_id — assert a Return exists.
    assert any(isinstance(s, ast.Return) for s in stmts), "assess() has no return (IC-045 regression)"


def test_no_dead_code_after_return():
    tree = ast.parse(TARGET.read_text(encoding="utf-8"))
    for fn in _functions(tree):
        for i, stmt in enumerate(fn.body):
            if isinstance(stmt, ast.Return):
                assert i == len(fn.body) - 1, (
                    f"{fn.name}(): statements exist after a top-level return "
                    "(unreachable dead code — IC-045 regression)"
                )


def test_single_smoke_test_definition():
    tree = ast.parse(TARGET.read_text(encoding="utf-8"))
    smoke = [f for f in _functions(tree) if f.name == "run_smoke_test"]
    assert len(smoke) == 1, f"expected one run_smoke_test, found {len(smoke)} (marker-injection artifact)"


if __name__ == "__main__":
    test_assess_has_real_body()
    test_no_dead_code_after_return()
    test_single_smoke_test_definition()
    print("✓ IC-045 structural regression tests PASSED")
