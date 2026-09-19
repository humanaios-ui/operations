#!/usr/bin/env python3
"""
behavioral_compliance_gate_v1_0.py
Builder v1.7 compliant
HumanAIOS

Behavioral compliance gate — IC-045 generalization (issue #98).

AST-level structural checks that replace/complement marker-presence scanning.
Unlike regex-based checks, these verify actual code structure so a builder-lint
"fix" that injects compliance markers cannot silently hollow-out a real endpoint.

Root cause: IC-045 — builder-lint marker injection placed a compliance block
between assess() docstring and body, leaving assess() docstring-only and
re-parenting the real logic as dead code after a `return` inside run_smoke_test().
It parsed, passed the marker-presence scanner, and merged. This gate catches that
class of defect by inspecting the AST, not just text patterns.

Checks performed (all HARD failures):
  BEHAV_DOCSTRING_ONLY         — function body contains only a docstring (no
                                   real statements); the exact IC-045 hollow pattern.
  BEHAV_DEAD_CODE_AFTER_RETURN — statements exist after a top-level `return`
                                   inside a function; unreachable / injected code.
  BEHAV_DUPLICATE_FUNC_DEF     — same function name defined more than once in the
                                   same scope (marker-injection artifact, e.g. two
                                   run_smoke_test() definitions).

Exemptions:
  - Functions decorated with @abstractmethod may have docstring-only bodies.
  - Functions whose body is exactly `pass` or `...` are intentional stubs — not
    flagged as BEHAV_DOCSTRING_ONLY (they lack a docstring and are explicit stubs).

Usage:
  python behavioral_compliance_gate_v1_0.py --path tools/
  python behavioral_compliance_gate_v1_0.py --path tools/some_tool.py
  python behavioral_compliance_gate_v1_0.py --path tools/ --output reports/
  python behavioral_compliance_gate_v1_0.py --smoke-test
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME = "behavioral_compliance_gate"
TOOL_VERSION = "1.0.0"


class SpecLoadFailed(Exception):
    """Raised when a path cannot be loaded or is invalid."""


# ---------------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------------

def _is_docstring_stmt(stmt: ast.stmt) -> bool:
    """Return True if stmt is a bare string-constant expression (a docstring)."""
    return (
        isinstance(stmt, ast.Expr)
        and isinstance(getattr(stmt, "value", None), ast.Constant)
        and isinstance(stmt.value.value, str)
    )


def _body_after_docstring(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ast.stmt]:
    """Return function body with the leading docstring (if any) stripped."""
    body = fn.body
    if body and _is_docstring_stmt(body[0]):
        return body[1:]
    return body


def _is_abstract(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Return True if the function is decorated with @abstractmethod."""
    for dec in fn.decorator_list:
        text = ast.unparse(dec)
        if "abstractmethod" in text:
            return True
    return False


def _is_pass_only(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Return True if the function body is just `pass` or `...` (explicit stub)."""
    real_body = [s for s in fn.body if not _is_docstring_stmt(s)]
    if not real_body:
        return False  # docstring-only, not pass-only
    return all(
        (isinstance(s, ast.Pass))
        or (isinstance(s, ast.Expr) and isinstance(getattr(s, "value", None), ast.Constant)
            and s.value.value is ...)
        for s in real_body
    )


# ---------------------------------------------------------------------------
# Per-file scanning
# ---------------------------------------------------------------------------

def _collect_toplevel_functions(
    tree: ast.Module,
) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    """Yield all function defs that are direct children of the module or a class."""
    fns: list = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fns.append(node)
    return fns


def scan_file(path: Path) -> dict:
    """
    Scan one Python file and return a result dict.

    Result schema:
      file          str  — absolute path
      passed        bool — True when hard_failures is empty
      hard_failures list — list of finding strings
    """
    result: dict = {
        "file": str(path),
        "passed": True,
        "hard_failures": [],
    }

    # --- parse ---
    try:
        source = path.read_text(encoding="utf-8")
    except (IOError, OSError) as exc:
        result["passed"] = False
        result["hard_failures"].append(f"FILE_UNREADABLE: {exc}")
        return result

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        result["passed"] = False
        result["hard_failures"].append(f"SYNTAX_ERROR: line {exc.lineno}: {exc.msg}")
        return result

    hard: list[str] = []

    # --- collect all functions ---
    fns = _collect_toplevel_functions(tree)

    # --- check BEHAV_DOCSTRING_ONLY and BEHAV_DEAD_CODE_AFTER_RETURN ---
    for fn in fns:
        qual = fn.name

        # BEHAV_DOCSTRING_ONLY
        body_after = _body_after_docstring(fn)
        has_docstring = len(fn.body) > len(body_after)  # docstring was stripped
        body_is_empty_after_doc = len(body_after) == 0

        if has_docstring and body_is_empty_after_doc and not _is_abstract(fn) and not _is_pass_only(fn):
            hard.append(
                f"BEHAV_DOCSTRING_ONLY:{fn.lineno}: {qual}() — "
                "body is docstring-only (no real statements); IC-045 hollow pattern"
            )

        # BEHAV_DEAD_CODE_AFTER_RETURN — only checks the direct body (not nested)
        for i, stmt in enumerate(fn.body):
            if isinstance(stmt, ast.Return) and i < len(fn.body) - 1:
                hard.append(
                    f"BEHAV_DEAD_CODE_AFTER_RETURN:{fn.lineno}: {qual}() — "
                    f"return at body[{i}] with {len(fn.body) - i - 1} unreachable "
                    "statement(s) after it (IC-045 dead-code pattern)"
                )
                break  # one report per function

    # --- check BEHAV_DUPLICATE_FUNC_DEF (module-level scope) ---
    module_fn_names: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            module_fn_names.append(node.name)

    seen: dict[str, int] = {}
    for name in module_fn_names:
        seen[name] = seen.get(name, 0) + 1
    for name, count in seen.items():
        if count > 1:
            hard.append(
                f"BEHAV_DUPLICATE_FUNC_DEF: function '{name}' defined {count} times "
                "at module scope (marker-injection artifact)"
            )

    result["hard_failures"] = hard
    result["passed"] = not hard
    return result


def scan_directory(scan_path: str, strict: bool = False) -> list[dict]:
    """Scan a file or directory recursively and return a list of per-file results."""
    p = Path(scan_path)
    if p.is_file():
        targets = [p]
    elif p.is_dir():
        targets = sorted(p.rglob("*.py"))
    else:
        raise SpecLoadFailed(f"Path not found: {scan_path}")

    results = []
    for target in targets:
        if "__pycache__" in str(target):
            continue
        results.append(scan_file(target))
    return results


def aggregate(results: list[dict]) -> dict:
    """Aggregate per-file results into a summary dict."""
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    all_hard: list[str] = []
    for r in results:
        for f in r["hard_failures"]:
            all_hard.append(r["file"] + ": " + f)

    failure_counts: dict[str, int] = {}
    for r in results:
        for f in r["hard_failures"]:
            code = f.split(":")[0]
            failure_counts[code] = failure_counts.get(code, 0) + 1

    return {
        "result": "PASS" if passed == total else "FAIL",
        "status": "PASS" if passed == total else "FAIL",
        "tool": TOOL_NAME,
        "version": TOOL_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "files_scanned": total,
        "files_passed": passed,
        "files_failed": total - passed,
        "pass_rate": round(passed / total, 4) if total else 1.0,
        "all_hard_failures": all_hard,
        "most_common_failures": sorted(failure_counts.items(), key=lambda x: -x[1])[:5],
        "file_results": results,
    }


def write_report(output: dict, output_dir: str) -> str:
    """Write a JSON report and return the path."""
    p = Path(output_dir)
    p.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = p / f"behavioral_compliance_{ts}.json"
    path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    return str(path)


def print_summary(output: dict, min_pass_rate: float = 1.0) -> None:
    """Print a human-readable summary."""
    b = "=" * 60
    verdict = output["result"]
    rate = output["pass_rate"]
    if verdict != "PASS" and rate >= min_pass_rate:
        pct = round(rate * 100)
        min_pct = round(min_pass_rate * 100)
        verdict = f"PASS (threshold met: {pct}% >= {min_pct}%)"
    print("")
    print(b)
    print(f" Behavioral Compliance Gate - {TOOL_VERSION}")
    print(f" Verdict: {verdict}")
    print(f" Files: {output['files_passed']}/{output['files_scanned']} "
          f"({round(output['pass_rate'] * 100)}%)")
    print(b)
    for r in output["file_results"]:
        sym = "OK" if r["passed"] else "FAIL"
        print(f"  {sym} {Path(r['file']).name}")
        for f in r["hard_failures"]:
            print(f"    HARD: {f}")
    if output["most_common_failures"]:
        print("")
        print("  MOST COMMON:")
        for code, count in output["most_common_failures"]:
            print(f"    {code}: {count}")
    print("")
    print(b)
    print("")


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

def run_smoke_test() -> bool:
    """Minimal compliance smoke test — verifies all three check types with synthetic code."""
    import tempfile

    cases = {
        "clean.py": (
            True,
            "\n".join([
                "# Builder v1.7 compliant",
                "# HumanAIOS",
                "TOOL_NAME = 'clean'",
                "TOOL_VERSION = '1.0.0'",
                "def real_func():",
                "    '''Docstring.'''",
                "    return 42",
                "def run_smoke_test():",
                "    return True",
                "if __name__ == '__main__': run_smoke_test()",
            ]),
        ),
        "docstring_only.py": (
            False,
            "\n".join([
                "def hollow():",
                "    '''This function has no body beyond its docstring.'''",
            ]),
        ),
        "dead_code.py": (
            False,
            "\n".join([
                "def bad():",
                "    return 1",
                "    x = 2  # dead code",
            ]),
        ),
        "duplicate_def.py": (
            False,
            "\n".join([
                "def run_smoke_test():",
                "    return True",
                "def run_smoke_test():",
                "    return False",
            ]),
        ),
        "abstract_ok.py": (
            True,
            "\n".join([
                "from abc import abstractmethod",
                "class Base:",
                "    @abstractmethod",
                "    def method(self):",
                "        '''Abstract — docstring-only body is OK.'''",
            ]),
        ),
    }

    try:
        with tempfile.TemporaryDirectory() as d:
            for fname, (expect_pass, src) in cases.items():
                fp = Path(d) / fname
                fp.write_text(src, encoding="utf-8")
                r = scan_file(fp)
                if r["passed"] != expect_pass:
                    print(
                        f"  FAILED: {fname} expected passed={expect_pass}, "
                        f"got {r['passed']}; failures={r['hard_failures']}",
                        file=sys.stderr,
                    )
                    return False
        print("✓ Smoke test PASSED", file=sys.stderr)
        return True
    except Exception as exc:
        print(f"✗ Smoke test FAILED: {exc}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=f"Behavioral Compliance Gate v{TOOL_VERSION} — AST-level IC-045 checks"
    )
    parser.add_argument("--path", "-p", help="File or directory to scan")
    parser.add_argument("--output", "-o", default="outputs/", help="Report output directory")
    parser.add_argument(
        "--min-pass-rate", type=float, default=1.0,
        help="Exit 0 when pass rate >= this threshold (0.0–1.0). Default 1.0.",
    )
    parser.add_argument("--smoke-test", action="store_true", help="Run smoke test and exit")
    args = parser.parse_args()

    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)

    if not args.path:
        parser.print_help()
        sys.exit(1)

    try:
        results = scan_directory(args.path)
    except SpecLoadFailed as exc:
        print(f"SPEC_LOAD_FAILED: {exc}", file=sys.stderr)
        sys.exit(2)

    output = aggregate(results)
    rp = write_report(output, args.output)
    threshold = args.min_pass_rate
    print_summary(output, min_pass_rate=threshold)
    print(f"Report: {rp}")
    sys.exit(0 if output["pass_rate"] >= threshold else 1)


if __name__ == "__main__":
    main()
