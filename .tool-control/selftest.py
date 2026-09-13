#!/usr/bin/env python3
"""Adversarial self-test for the tool-control gate: prove every rule can FAIL.

WHY THIS EXISTS
---------------
The gates validate the corpus. Nothing validated the gates. Across three review
rounds on PRs #304 and #306, four defects were found by reviewers and by none of
the gates' own checks, and all four were the same shape — a rule the
documentation asserted and the code did not enforce:

  * `pending_ratification` was self-grantable, while the README said new Zone
    2/3 claims block.
  * A deleted tool's entry was silently dropped, while the README said
    retirement is an explicit act.
  * `extract()` discarded unknown declared categories and fell back to the
    curated value, while the rule said the declaration wins and must be in the
    vocabulary.
  * Two tools were categorized by a word in their filename, against the
    vocabulary's own "role, not subject" rule.

Measured at the time this file was written: `validate.py` had **26 blocking
conditions and its smoke test exercised 10**. The other 16 — including
`unregistered tool`, the coverage rule the whole system rests on — had never
been demonstrated to fire. Each had been driven red by hand in a shell during
development and the demonstration thrown away.

A gate whose failure path is never executed is a claim, not a control. So:

  1. Every blocking condition gets a fixture that triggers it.
  2. Coverage is ENFORCED — a blocking condition with no fixture fails this
     suite. Adding an `err()` without a demonstration is itself a violation.

That second rule is what makes this self-maintaining rather than a snapshot.

Usage:
  python3 .tool-control/selftest.py            # run; non-zero on failure
  python3 .tool-control/selftest.py --list     # show coverage per condition
  python3 .tool-control/selftest.py --smoke-test

Deps: PyYAML. No network. Writes only into a temporary directory.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scan  # noqa: E402
import validate as V  # noqa: E402

TOOL_NAME = "tool_control_selftest"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "validation_tool"
TOOL_ZONE = 1

ROOT = scan.ROOT
VALIDATE_SRC = os.path.join(ROOT, ".tool-control", "validate.py")
DOC_VALIDATE = os.path.join(ROOT, ".doc-control", "validate.py")


FIRED: set[int] = set()
_failures: list[str] = []


def blocking_conditions() -> dict[int, str]:
    """Every err() call site in validate.py, by line number.

    Found with the AST, not a regex. A literal-only pattern (`err("` / `err(f"`)
    misses `err(\'...\')`, `err(message)`, and multi-line calls — and a blocking
    rule it misses is one the coverage requirement never demands a fixture for.
    That would be a bypass in the very mechanism built to prevent bypasses.
    """
    src = open(VALIDATE_SRC, encoding="utf-8").read()
    lines = src.splitlines()
    out: dict[int, str] = {}
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "err":
            out[node.lineno] = lines[node.lineno - 1].strip()
    return out


def _install_tracker() -> None:
    """Record which err() site fired, so coverage is measured not asserted."""
    original = V.err

    def tracking(msg: str) -> None:
        FIRED.add(sys._getframe(1).f_lineno)
        original(msg)

    V.err = tracking


def check(name: str, fn, expect: str) -> None:
    """Run one fixture and require it to produce an error containing `expect`."""
    V.errors, V.warnings = [], []
    try:
        fn()
    except Exception as exc:  # a gate that crashes is a gate that does not gate
        _failures.append(f"{name}: fixture raised {type(exc).__name__}: {exc}")
        return
    if not any(expect in e for e in V.errors):
        _failures.append(f"{name}: expected an error containing {expect!r}, got {V.errors}")


# --------------------------------------------------------------------------
# fixtures
# --------------------------------------------------------------------------
REAL = ".tool-control/scan.py"
REAL_VERSION = scan.extract(os.path.join(ROOT, REAL)).get("declared_version")
LEGACY = sorted(V.UNRATIFIED_ZONE_CLAIMS)[0]


def tool(**over) -> dict:
    """A valid manifest entry; each fixture breaks exactly one thing."""
    base = {
        "tool_id": "HAIOS-TOOL-001", "name": "t", "path": REAL,
        "version": REAL_VERSION, "category": "validation_tool",
        "zone": 1, "status": "draft",
    }
    base.update(over)
    return base


def server(**over) -> dict:
    base = {
        "server_id": "HAIOS-MCP-001", "server": "s", "transport": "http",
        "endpoint": "https://example.invalid", "status": "draft",
    }
    base.update(over)
    return base


def run_tool_cases() -> None:
    V_ = V.validate
    check("empty manifest", lambda: V_({"tools": []}), "has no `tools`")
    check("missing field", lambda: V_({"tools": [{k: v for k, v in tool().items() if k != "name"}]}),
          "missing required field")
    check("malformed id", lambda: V_({"tools": [tool(tool_id="BAD")]}), "does not match HAIOS-TOOL-")
    check("duplicate id", lambda: V_({"tools": [tool(), tool(path="tools/repo_health.py",
                                                        version=None, category="diagnostic_tool")]}),
          "duplicate tool_id")
    check("duplicate path", lambda: V_({"tools": [tool(), tool(tool_id="HAIOS-TOOL-002")]}),
          "duplicate path")
    check("absolute path", lambda: V_({"tools": [tool(path="/etc/passwd")]}),
          "must be a relative path")
    check("traversal path", lambda: V_({"tools": [tool(path="../outside.py")]}),
          "resolves outside the repository")
    check("directory path", lambda: V_({"tools": [tool(path="tools")]}), "is a directory")
    check("dead entry", lambda: V_({"tools": [tool(path="tools/does_not_exist_xyz.py")]}),
          "does not exist")
    check("bad status", lambda: V_({"tools": [tool(status="bogus")]}), "invalid status")
    check("approved without attribution", lambda: V_({"tools": [tool(status="approved")]}),
          "requires approved_by + approved_date")
    check("version drift", lambda: V_({"tools": [tool(version="9.9.9")]}), "!= TOOL_VERSION")
    check("self-granted Z2 waiver",
          lambda: V_({"tools": [tool(zone=2, pending_ratification=True)]}),
          "cannot grant itself")
    check("unratified zone 2", lambda: V_({"tools": [tool(zone=2)]}), "requires 'ratified_by'")
    check("impossible zone", lambda: V_({"tools": [tool(zone=5)]}), "invalid (must be 1, 2 or 3)")
    check("unclassified", lambda: V_({"tools": [tool(category="unclassified")]}),
          "category is 'unclassified'")
    check("non-string category", lambda: V_({"tools": [tool(category=0)]}),
          "category must be a string")
    check("category outside vocabulary", lambda: V_({"tools": [tool(category="made_up_thing")]}),
          "not in the controlled vocabulary")
    check("malformed review_due", lambda: V_({"tools": [tool(review_due="soon")]}),
          "is not an ISO date")
    # The grandfathered Zone 2 path must still be ACCEPTED — a rule that only
    # ever rejects is as broken as one that never does.
    V.errors, V.warnings = [], []
    V.validate({"tools": [tool(path=LEGACY, zone=2, pending_ratification=True,
                               version=scan.extract(os.path.join(ROOT, LEGACY)).get("declared_version"))]})
    if V.errors:
        _failures.append(f"grandfathered Zone 2 path should pass, got {V.errors}")


def run_coverage_case() -> None:
    """The load-bearing rule: a tool on disk that nobody registered."""
    original = scan.discover
    scan.discover = lambda: [os.path.join(ROOT, "tools", "zz_unregistered_probe.py")]
    try:
        check("unregistered tool",
              lambda: V.validate_coverage({"tools": [], "excluded": []}),
              "unregistered tool")
    finally:
        scan.discover = original


def run_cli_dispatch_case() -> None:
    """The same rule, end to end, the way CI actually invokes it.

    Every other fixture calls a validate_* function directly. CI runs
    `python3 .tool-control/validate.py`, and if main() ever stopped wiring the
    coverage check into that path, those fixtures would keep passing while
    unregistered tools merged. This exercises the command, not the function.
    """
    import yaml
    with tempfile.TemporaryDirectory() as td:
        os.makedirs(os.path.join(td, ".tool-control"))
        os.makedirs(os.path.join(td, "tools"))
        for mod in ("scan.py", "validate.py"):
            src = open(os.path.join(ROOT, ".tool-control", mod), encoding="utf-8").read()
            open(os.path.join(td, ".tool-control", mod), "w", encoding="utf-8").write(src)

        stub = '"""{doc}"""\nTOOL_NAME = "{name}"\nTOOL_VERSION = "1.0.0"\n'
        open(os.path.join(td, "tools", "registered.py"), "w", encoding="utf-8").write(
            stub.format(doc="A registered tool.", name="registered"))
        # Present on disk, absent from the manifest — exactly the drift that
        # produced the 6-of-136 gap the whole system exists to prevent.
        open(os.path.join(td, "tools", "unregistered.py"), "w", encoding="utf-8").write(
            stub.format(doc="Nobody registered me.", name="ghost"))

        manifest = {"version": 1, "tools": [{
            "tool_id": "HAIOS-TOOL-001", "name": "registered", "path": "tools/registered.py",
            "version": "1.0.0", "category": "validation_tool", "zone": 1, "status": "draft",
        }], "mcp_servers": [], "excluded": []}
        with open(os.path.join(td, "tools-manifest.yaml"), "w", encoding="utf-8") as fh:
            yaml.safe_dump(manifest, fh)

        proc = subprocess.run([sys.executable, os.path.join(td, ".tool-control", "validate.py")],
                              capture_output=True, text=True)
        out = proc.stdout + proc.stderr
        if proc.returncode == 0:
            _failures.append("CLI dispatch: validate.py exited 0 with an unregistered tool on disk "
                             "— the coverage check is not wired into main()")
        elif "unregistered tool 'tools/unregistered.py'" not in out:
            _failures.append(f"CLI dispatch: expected the unregistered-tool error, got {out.strip()[:200]}")


def run_mcp_cases() -> None:
    M = V.validate_mcp
    check("mcp malformed id", lambda: M({"mcp_servers": [server(server_id="nope")]}),
          "does not match HAIOS-MCP-")
    check("mcp duplicate id", lambda: M({"mcp_servers": [server(), server(server="other")]}),
          "duplicate server_id")
    check("mcp missing field",
          lambda: M({"mcp_servers": [{k: v for k, v in server().items() if k != "endpoint"}]}),
          "missing required field")
    check("mcp bad status", lambda: M({"mcp_servers": [server(status="bogus")]}), "invalid status")
    check("mcp approved without attribution",
          lambda: M({"mcp_servers": [server(status="approved", scope="real",
                                            data_classification="internal")]}),
          "requires approved_by + approved_date")
    check("mcp placeholder scope",
          lambda: M({"mcp_servers": [server(status="approved", approved_by="x",
                                            approved_date="2026-01-01", scope="unscoped",
                                            data_classification="internal")]}),
          "requires a real 'scope'")

    with tempfile.TemporaryDirectory() as td:
        broken = os.path.join(td, "broken.json")
        open(broken, "w").write("{not json")
        original, V.MCP_CONFIG = V.MCP_CONFIG, broken
        try:
            check("unparseable .mcp.json", lambda: V.validate_mcp_config({"mcp_servers": []}),
                  "does not parse")
        finally:
            V.MCP_CONFIG = original

        cfg = os.path.join(td, "mcp.json")
        json.dump({"mcpServers": {"ghost": {"type": "http", "url": "https://x.invalid"}}}, open(cfg, "w"))
        original, V.MCP_CONFIG = V.MCP_CONFIG, cfg
        try:
            check("unregistered MCP server",
                  lambda: V.validate_mcp_config({"mcp_servers": []}),
                  "is in .mcp.json but not in tools-manifest.yaml")
        finally:
            V.MCP_CONFIG = original


# --------------------------------------------------------------------------
# document-control: a script, not a module, so drive it end to end
# --------------------------------------------------------------------------
DOC_CASES = [
    ("doc: malformed id", {"documents": [{"doc_id": "NOPE", "title": "t",
                                          "canonical_repo": "other", "canonical_path": "x.md",
                                          "status": "draft"}]},
     "does not match HAIOS-<AREA>-<nnn>"),
    ("doc: missing field", {"documents": [{"doc_id": "HAIOS-GOV-001", "title": "t",
                                           "canonical_repo": "other", "status": "draft"}]},
     "missing required field"),
    ("doc: bad status", {"documents": [{"doc_id": "HAIOS-GOV-001", "title": "t",
                                        "canonical_repo": "other", "canonical_path": "x.md",
                                        "status": "bogus"}]},
     "invalid status"),
    ("doc: approved without attribution",
     {"documents": [{"doc_id": "HAIOS-GOV-001", "title": "t", "canonical_repo": "other",
                     "canonical_path": "x.md", "status": "approved"}]},
     "requires approved_by + approved_date"),
    ("doc: path escape",
     {"documents": [{"doc_id": "HAIOS-GOV-001", "title": "t", "canonical_repo": "operations",
                     "canonical_path": "/etc/passwd", "status": "draft"}]},
     "must be a relative path inside the repo"),
    ("doc: counts lie",
     {"counts": {"documents": 99, "excluded": 0, "needs_reconcile": 0},
      "documents": [{"doc_id": "HAIOS-GOV-001", "title": "t", "canonical_repo": "other",
                     "canonical_path": "x.md", "status": "draft"}]},
     "counts.documents says 99"),
    ("doc: counts block deleted",
     {"documents": [{"doc_id": "HAIOS-GOV-001", "title": "t", "canonical_repo": "other",
                     "canonical_path": "x.md", "status": "draft"}]},
     "missing a `counts:` mapping"),
]


def run_doc_cases() -> None:
    """Each fixture gets its own throwaway repo root, so ROOT resolves there."""
    import yaml
    for name, registry, expect in DOC_CASES:
        with tempfile.TemporaryDirectory() as td:
            os.makedirs(os.path.join(td, ".doc-control"))
            with open(DOC_VALIDATE, encoding="utf-8") as fh:
                open(os.path.join(td, ".doc-control", "validate.py"), "w", encoding="utf-8").write(fh.read())
            if "counts" not in registry and "counts block deleted" not in name:
                registry = dict(registry)
                registry["counts"] = {"documents": len(registry.get("documents") or []),
                                      "excluded": 0, "needs_reconcile": 0}
            with open(os.path.join(td, "document-registry.yaml"), "w", encoding="utf-8") as fh:
                yaml.safe_dump(registry, fh)
            proc = subprocess.run([sys.executable, os.path.join(td, ".doc-control", "validate.py")],
                                  capture_output=True, text=True)
            if proc.returncode == 0:
                _failures.append(f"{name}: doc gate exited 0 — it did not block")
            elif expect not in proc.stdout + proc.stderr:
                _failures.append(f"{name}: expected {expect!r}, got {proc.stdout.strip()[:200]}")


# --------------------------------------------------------------------------
def report(verbose: bool = False) -> int:
    conditions = blocking_conditions()
    uncovered = sorted(set(conditions) - FIRED)

    if verbose:
        for ln, text in sorted(conditions.items()):
            mark = "OK  " if ln in FIRED else "MISS"
            print(f"  {mark} L{ln}: {text[:86]}")
        print()

    for f in _failures:
        print(f"::error::selftest: {f}")

    if uncovered:
        print("::error::blocking conditions with no fixture proving they fire — "
              "a rule whose failure path is never executed is a claim, not a control:")
        for ln in uncovered:
            print(f"::error::  {os.path.relpath(VALIDATE_SRC, ROOT)}:{ln}  {conditions[ln][:80]}")

    if _failures or uncovered:
        print(f"\nselftest FAILED — {len(_failures)} fixture failure(s), "
              f"{len(uncovered)} undemonstrated blocking condition(s).")
        return 1

    print(f"selftest OK — all {len(conditions)} blocking conditions in validate.py demonstrated "
          f"to fire, plus {len(DOC_CASES)} document-control conditions, and the grandfathered "
          f"Zone 2 path still passes.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Prove every tool-control rule can fail")
    ap.add_argument("--list", action="store_true", help="show per-condition coverage")
    ap.add_argument("--smoke-test", action="store_true", help="self-test and exit")
    args = ap.parse_args()

    if args.smoke_test:
        conditions = blocking_conditions()
        assert len(conditions) > 20, f"expected to find the err() sites, found {len(conditions)}"
        assert REAL_VERSION, "could not read a real tool version for the baseline fixture"
        print(f"smoke-test OK — {len(conditions)} blocking conditions discoverable.")
        return 0

    _install_tracker()
    run_tool_cases()
    run_coverage_case()
    run_cli_dispatch_case()
    run_mcp_cases()
    run_doc_cases()
    return report(verbose=args.list)


if __name__ == "__main__":
    sys.exit(main())
