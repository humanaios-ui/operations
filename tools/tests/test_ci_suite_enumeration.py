#!/usr/bin/env python3
"""The enumerated pytest list in CI must actually cover `tools/tests/`.

WHY THIS FILE EXISTS
--------------------
`.github/workflows/quality-baseline.yml` names its pytest suites one path per
line. That is a deliberate policy — CI states what it owns rather than globbing
a directory and inheriting whatever lands in it — but it has a failure mode the
policy does not mention: **a test file that is not on the list does not run, and
nothing says so.**

Measured before this guard existed: 7 of 21 files under `tools/tests/`, carrying
67 tests between them, were absent from the list. All 67 passed when run by
hand, so nothing was broken — they were simply unguarded. A suite that could go
red tomorrow while CI stays green is not coverage, it is the appearance of it.

A second copy of the same list lives in `tools/intent_os_test_harness_v1_0.py`
(`t3-pytest-baseline`), whose whole purpose is to reproduce what the workflows
run. It had already drifted from the workflow. Two hand-maintained copies of one
list drift by default; this asserts they agree.

THIS FILE IS ON THE LIST IT CHECKS
----------------------------------
Deliberately, and asserted below. A coverage rule that exempts its own
definition is silently self-amendable — the finding registered this session as
`F-CAND-SELF-EXEMPT-RULE-01`, from a path-scoped classifier whose path list
omitted itself. The same shape would apply here: drop this file from the
workflow and the guard stops running, which is exactly the state it exists to
refuse.

WHAT IT DOES NOT ASSERT
-----------------------
It does not require every test file in the repository to be enumerated. Root
level (`test_resource_economics.py`), `tests/` and `acat/tests/` have their own
arrangements, and sweeping them in here would be this guard deciding policy it
was not given. It covers `tools/tests/` — the directory whose convention the
enumeration was chosen to serve — and the agreement between the two copies.

Runs under pytest and standalone
(`python3 tools/tests/test_ci_suite_enumeration.py`).
"""
from __future__ import annotations

import glob
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORKFLOW = os.path.join(REPO, ".github", "workflows", "quality-baseline.yml")
HARNESS = os.path.join(REPO, "tools", "intent_os_test_harness_v1_0.py")
SELF = "tools/tests/test_ci_suite_enumeration.py"


def workflow_suites() -> list[str]:
    """The paths in quality-baseline's blocking pytest step, in order.

    Parsed from the text rather than by loading the YAML: the step is a shell
    block with backslash continuations, so a YAML load hands back one string
    that still has to be split. Reading the continuations directly keeps the
    failure mode obvious if the step is ever reformatted — this returns nothing
    and every assertion below fails loudly, rather than quietly matching an
    empty set.
    """
    text = open(WORKFLOW, encoding="utf-8").read()
    m = re.search(r"python3 -m pytest \\\n(.*?)^\s*-q\s*$", text, re.S | re.M)
    if not m:
        return []
    out = []
    for line in m.group(1).splitlines():
        line = line.strip().rstrip("\\").strip()
        if line and not line.startswith("#"):
            out.append(line)
    return out


def harness_suites() -> list[str]:
    """The `baseline = [...]` list in the Intent-OS harness's t3-pytest-baseline."""
    text = open(HARNESS, encoding="utf-8").read()
    m = re.search(r"baseline = \[(.*?)\]", text, re.S)
    return re.findall(r'"([^"]+\.py)"', m.group(1)) if m else []


def tools_tests_on_disk() -> list[str]:
    paths = glob.glob(os.path.join(REPO, "tools", "tests", "test_*.py"))
    return sorted(os.path.relpath(p, REPO).replace(os.sep, "/") for p in paths)


# --------------------------------------------------------------------------- #

def test_the_workflow_step_is_still_parseable() -> None:
    """If this fails, every other assertion here is vacuous. Check it first."""
    suites = workflow_suites()
    assert suites, (
        "could not find the enumerated pytest step in quality-baseline.yml. "
        "If the step was reformatted, update workflow_suites() — do not delete "
        "this guard, or the coverage assertions below silently pass on nothing."
    )
    assert len(suites) >= 10, f"only {len(suites)} suites parsed; the regex is probably truncating"


def test_every_tools_test_file_is_enumerated() -> None:
    """The gap this guard was written for: 7 files, 67 tests, not running."""
    listed = set(workflow_suites())
    missing = [p for p in tools_tests_on_disk() if p not in listed]
    assert not missing, (
        "test files under tools/tests/ that CI does not run:\n  "
        + "\n  ".join(missing)
        + "\n\nAdd each to the pytest step in .github/workflows/quality-baseline.yml "
          "AND to the `baseline` list in tools/intent_os_test_harness_v1_0.py."
    )


def test_this_guard_is_itself_enumerated() -> None:
    """A coverage rule that does not cover its own definition is self-amendable."""
    assert SELF in workflow_suites(), (
        f"{SELF} is not in the pytest step, so this guard does not run in CI and "
        f"cannot refuse the next unwired suite."
    )


def test_enumerated_paths_all_exist() -> None:
    """The inverse drift: a renamed or deleted file left behind on the list.

    pytest exits non-zero on a missing path, so this would surface in CI anyway
    — but as `ERROR: file not found` against a list of eighteen, which is a
    worse thing to read than a named assertion.
    """
    missing = [p for p in workflow_suites() if not os.path.isfile(os.path.join(REPO, p))]
    assert not missing, f"enumerated in quality-baseline.yml but not on disk: {missing}"


def test_the_harness_copy_matches_the_workflow() -> None:
    """Two hand-maintained copies of one list drift by default. This one had."""
    wf, harness = workflow_suites(), harness_suites()
    assert harness, "could not parse the `baseline = [...]` list from the harness"
    only_wf = [p for p in wf if p not in harness]
    only_harness = [p for p in harness if p not in wf]
    assert not only_wf and not only_harness, (
        "tools/intent_os_test_harness_v1_0.py's t3-pytest-baseline list has drifted "
        "from quality-baseline.yml.\n"
        f"  in the workflow, not the harness: {only_wf}\n"
        f"  in the harness, not the workflow: {only_harness}\n"
        "The harness exists to reproduce what CI runs; a harness that runs a "
        "different set reports a pass CI would not give."
    )


def test_no_duplicate_entries() -> None:
    """A path listed twice runs twice and hides a paste error in a long list."""
    suites = workflow_suites()
    dupes = sorted({p for p in suites if suites.count(p) > 1})
    assert not dupes, f"listed more than once in quality-baseline.yml: {dupes}"


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  ok   {t.__name__}")
        except AssertionError as exc:
            failed += 1
            print(f"  FAIL {t.__name__}: {exc}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
