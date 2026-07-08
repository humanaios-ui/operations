#!/usr/bin/env python3
"""
Builder Compliance Scanner - v1.0
Builder v1.7 compliant - meta_validator_tool
HumanAIOS - S-051626-01-acat-tools-alternate-functions-mapping

Scans Python files against the Builder v1.7 compliance checklist.
All new tools in tools/acat/ must pass this scanner before merging.

Checks (HARD unless noted):
  BUILDER_MISSING_HEADER       - Builder v1.7 compliant in docstring
  BUILDER_NO_TOOL_NAME         - TOOL_NAME constant
  BUILDER_NO_TOOL_VERSION      - TOOL_VERSION constant
  BUILDER_NO_HUMANAIOS_TAG     - HumanAIOS in docstring
  BUILDER_NO_SMOKE_TEST        - run_smoke_test or --smoke-test
  BUILDER_NO_MAIN_GUARD        - if name == main
  BUILDER_NO_WRITE_REPORT      - write_report function (SOFT)
  BUILDER_NO_ARGPARSE          - argparse.ArgumentParser (SOFT)
  BUILDER_ERROR_IMPORT_MISSING - SpecLoadFailed defined or imported (SOFT)

Usage:
  python builder_compliance_scanner_v1.0.py --path tools/acat/
  python builder_compliance_scanner_v1.0.py --path tools/acat/ --strict
  python builder_compliance_scanner_v1.0.py --smoke-test
"""

import ast as _ast
import re
import sys
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME = "builder_compliance_scanner"
TOOL_VERSION = "1.0.0"

EXEMPT_WRITE_REPORT = {"errors_acat", "__init__", "run_acat_validation_suite"}
EXEMPT_SMOKE_TEST   = {"errors_acat", "__init__"}
EXEMPT_MAIN_GUARD   = {"__init__"}

_MAIN_PAT = re.compile(r'if __name__')
_CHECKS_RAW = [
    ("BUILDER_MISSING_HEADER",       r"Builder v1\.7 compliant",        "HARD"),
    ("BUILDER_NO_TOOL_NAME",         r"^TOOL_NAME\s*=",                  "HARD"),
    ("BUILDER_NO_TOOL_VERSION",      r"^TOOL_VERSION\s*=",               "HARD"),
    ("BUILDER_NO_HUMANAIOS_TAG",     r"HumanAIOS",                        "HARD"),
    ("BUILDER_NO_SMOKE_TEST",        r"smoke.test|run_smoke_test",        "HARD"),
    ("BUILDER_NO_MAIN_GUARD",        r"if __name__",                      "HARD"),
    ("BUILDER_NO_WRITE_REPORT",      r"def write_report",                 "SOFT"),
    ("BUILDER_NO_ARGPARSE",          r"argparse\.ArgumentParser",        "SOFT"),
    ("BUILDER_ERROR_IMPORT_MISSING", r"class SpecLoadFailed|SpecLoadFailed", "SOFT"),
]
CHECKS = {cid: (re.compile(pat, re.I | re.M), sev) for cid, pat, sev in _CHECKS_RAW}


class SpecLoadFailed(Exception):
    pass


def _stem(path):
    return path.stem.split("_v")[0]


def scan_file(path):
    try:
        text = path.read_text(encoding="utf-8")
    except (IOError, OSError) as e:
        return {"file": str(path), "passed": False,
                "hard_failures": ["FILE_UNREADABLE: " + str(e)], "soft_failures": []}
    try:
        _ast.parse(text)
    except SyntaxError as e:
        return {"file": str(path), "passed": False,
                "hard_failures": ["SYNTAX_ERROR: line " + str(e.lineno) + ": " + str(e.msg)],
                "soft_failures": []}
    stem = _stem(path)
    hard, soft = [], []
    for cid, (pat, sev) in CHECKS.items():
        if cid == "BUILDER_NO_SMOKE_TEST"   and stem in EXEMPT_SMOKE_TEST:   continue
        if cid == "BUILDER_NO_MAIN_GUARD"   and stem in EXEMPT_MAIN_GUARD:   continue
        if cid == "BUILDER_NO_WRITE_REPORT" and stem in EXEMPT_WRITE_REPORT: continue
        if not pat.search(text):
            target = hard if sev == "HARD" else soft
            target.append(cid)
    return {"file": str(path), "stem": stem, "passed": not hard,
            "hard_failures": hard, "soft_failures": soft}


def scan_directory(scan_path, strict=False):
    p = Path(scan_path)
    if p.is_file():
        targets = [p]
    elif p.is_dir():
        targets = sorted(p.rglob("*.py"))
    else:
        raise SpecLoadFailed("Path not found: " + str(scan_path))
    results = []
    for target in targets:
        if "__pycache__" in str(target):
            continue
        r = scan_file(target)
        if strict and r["soft_failures"]:
            r["hard_failures"].extend(r["soft_failures"])
            r["soft_failures"] = []
            r["passed"] = not r["hard_failures"]
        results.append(r)
    return results


def aggregate(results):
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    all_hard = []
    for r in results:
        for f in r["hard_failures"]:
            all_hard.append(r["file"] + ": " + f)
    fc = {}
    for r in results:
        for f in r["hard_failures"] + r["soft_failures"]:
            fc[f] = fc.get(f, 0) + 1
    return {
        "result": "PASS" if passed == total else "FAIL",
        "status": "PASS" if passed == total else "FAIL",
        "tool": TOOL_NAME, "version": TOOL_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "files_scanned": total, "files_passed": passed, "files_failed": total - passed,
        "pass_rate": round(passed / total, 4) if total else 0.0,
        "all_hard_failures": all_hard,
        "most_common_failures": sorted(fc.items(), key=lambda x: -x[1])[:5],
        "file_results": results,
    }


def write_report(output, output_dir):
    p = Path(output_dir)
    p.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = p / ("builder_compliance_" + ts + ".json")
    path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    return str(path)


def print_summary(output, min_pass_rate=1.0):
    b = "=" * 60
    verdict = output["result"]
    if verdict != "PASS" and output["pass_rate"] >= min_pass_rate:
        verdict = "PASS (threshold met: " + str(round(output["pass_rate"] * 100)) + "% >= " + str(round(min_pass_rate * 100)) + "%)"
    print("")
    print(b)
    print(" Builder Compliance Scanner - " + TOOL_VERSION)
    print(" Verdict: " + verdict)
    print(" Files: " + str(output["files_passed"]) + "/" + str(output["files_scanned"]) +
          " (" + str(round(output["pass_rate"] * 100)) + "%)")
    print(b)
    for r in output["file_results"]:
        sym = "checkmark" if r["passed"] else "x"
        print("  " + ("OK" if r["passed"] else "FAIL") + " " + Path(r["file"]).name)
        for f in r["hard_failures"]:
            print("    HARD: " + f)
        for f in r["soft_failures"]:
            print("    SOFT: " + f)
    if output["most_common_failures"]:
        print("")
        print("  MOST COMMON:")
        for code, count in output["most_common_failures"]:
            print("    " + code + ": " + str(count))
    print("")
    print(b)
    print("")


def run_smoke_test():
    import tempfile
    compliant_lines = [
        "#!/usr/bin/env python3",
        "# Builder v1.7 compliant",
        "# HumanAIOS",
        "import argparse, sys",
        "TOOL_NAME = 'test_tool'",
        "TOOL_VERSION = '1.0.0'",
        "class SpecLoadFailed(Exception): pass",
        "def write_report(o, d): pass",
        "def run_smoke_test(): return True",
        "def main():",
        "    p = argparse.ArgumentParser()",
        "    p.add_argument('--smoke-test', action='store_true')",
        "    a = p.parse_args()",
        "    if a.smoke_test: sys.exit(0 if run_smoke_test() else 1)",
        "if __name__ == '__main__': main()",
    ]
    compliant = "\n".join(compliant_lines) + "\n"
    noncompliant = "def foo(): pass\n"
    try:
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "good_tool_v1.0.py").write_text(compliant)
            (Path(d) / "bad_tool.py").write_text(noncompliant)
            results = scan_directory(d)
            output = aggregate(results)
            assert output["files_scanned"] == 2
            good = next(r for r in results if "good_tool" in r["file"])
            bad  = next(r for r in results if "bad_tool"  in r["file"])
            assert good["passed"], str(good["hard_failures"])
            assert not bad["passed"]
            print("checkmark Smoke test PASSED")
            return True
    except Exception as e:
        print("x Smoke test FAILED: " + str(e))
        return False


def main():
    parser = argparse.ArgumentParser(description="Builder Compliance Scanner v1.0")
    parser.add_argument("--path", "-p")
    parser.add_argument("--output", "-o", default="outputs/")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--smoke-test", action="store_true")
    parser.add_argument("--min-pass-rate", type=float, default=1.0,
                        help="Exit 0 when pass rate >= this threshold (0.0-1.0). "
                             "Default 1.0 requires all files to pass.")
    args = parser.parse_args()
    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)
    if not args.path:
        parser.print_help()
        sys.exit(1)
    try:
        results = scan_directory(args.path, args.strict)
    except SpecLoadFailed as e:
        print("SPEC_LOAD_FAILED: " + str(e), file=sys.stderr)
        sys.exit(2)
    output = aggregate(results)
    rp = write_report(output, args.output)
    threshold = getattr(args, "min_pass_rate", 1.0)
    print_summary(output, min_pass_rate=threshold)
    print("Report: " + rp)
    sys.exit(0 if output["pass_rate"] >= threshold else 1)


if __name__ == "__main__":
    main()
