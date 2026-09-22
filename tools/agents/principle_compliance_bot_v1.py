#!/usr/bin/env python3
"""
Agent 1.1: Principle Compliance Bot
====================================
Builder v1.7 compliant · audit_tool
HumanAIOS

Purpose: Validate decisions/artifacts against 22-principle constitution.
Triggers: On commit + decision-log entry
Output: GitHub issues for violations
Zone: Z1 (autonomous — reports violations, humans decide severity)

Implementation: P19 (Detection beats compliance) — surface drift before
justifying it.

Usage:
  python3 tools/agents/principle_compliance_bot_v1.py --check-commit "msg" --files file1.py,file2.py [--base REF]
  python3 tools/agents/01_principle_compliance_bot_v1.py --smoke-test
"""

import sys
import json
import re
import argparse
import subprocess
from pathlib import Path
from typing import List

# Builder v1.7 compliance
TOOL_NAME = "principle_compliance_bot_v1"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "audit_tool"

# --------------------------------------------------------------------------
# Q-P19-GATE-INERT-01. Two defects, fixed together because fixing either alone
# is worse than fixing neither.
#
# 1. The caller passes a NEWLINE-separated file list (the workflow builds it
#    with `git diff --name-only`) and this bot split it on COMMAS. Every
#    multi-file change therefore arrived as one unsplittable blob that did not
#    end in ".py", so no file was ever opened and the gate reported green having
#    inspected nothing. It only ran at all when a change touched exactly one
#    .py file and nothing else.
#
# 2. The scan read the WHOLE FILE and matched a bare substring. Measured on this
#    tree: 113 of 373 .py files contain one of these words somewhere. Repairing
#    defect 1 without repairing this would have switched on a gate that fails
#    ~30% of Python files for words the change did not write.
#
# So the scan now looks only at lines this change ADDS, matches whole words, and
# refuses to report success when it cannot determine what was added — a gate
# that cannot see its input must not report green, which is the whole finding.
# --------------------------------------------------------------------------

# P-HUMILITY: overconfident absolutes. Word-boundary, not substring: a bare
# `"never" in content` also fires on "nevertheless".
ABSOLUTE_LANGUAGE = re.compile(r"\b(always|never|impossible)\b", re.IGNORECASE)

# This module cannot be scanned by its own rule: a detector has to contain the
# pattern it detects. Same exemption, and the same reason, as
# tests/test_temporal_dissolution_gate.py carries for the temporal scan.
SELF_EXEMPT = ("tools/agents/principle_compliance_bot_v1.py",)


def split_file_list(raw: str) -> List[str]:
    """Split a changed-file list on commas OR newlines.

    Defect 1 above. Accepting both means the bot is correct whichever way a
    caller builds the list, rather than correct only for the one the docstring
    happened to describe.
    """
    return [f.strip() for f in re.split(r"[,\n]+", raw or "") if f.strip()]


def added_lines(filepath: str, base: str) -> List[str]:
    """Lines this change adds to `filepath`, via `git diff`.

    Raises CalledProcessError if the diff cannot be computed. The caller turns
    that into a loud failure rather than an empty result, because "I could not
    tell what changed" and "nothing objectionable changed" must not look alike.
    """
    out = subprocess.run(
        ["git", "diff", "-U0", f"{base}...HEAD", "--", filepath],
        capture_output=True, text=True, check=True,
    ).stdout
    return [ln[1:] for ln in out.splitlines()
            if ln.startswith("+") and not ln.startswith("+++")]

# Add tools/agents to path so we can import _shared
sys.path.insert(0, str(Path(__file__).parent))

from _shared.constitution_checker import ConstitutionChecker
from _shared.github_client import GitHubClient


class PrincipleComplianceBot:
    """Autonomous principle compliance enforcement."""

    def __init__(self, constitution_path: str = "constitution.json"):
        self.checker = ConstitutionChecker(constitution_path)
        self.github = GitHubClient()
        self.violations_found = []

    def check_commit(self, commit_msg: str, files_changed: List[str]) -> bool:
        """
        Check a commit for principle violations.
        Returns True if clean, False if violations found.
        """
        violations = self.checker.check_commit(commit_msg, files_changed)

        if violations:
            self.violations_found.extend(violations)
            return False

        return True

    def check_code_file(self, filepath: str, base: str = "HEAD~1") -> bool:
        """
        Check the lines this change ADDS to a Python file.

        Scans added lines rather than the whole file, so a change is judged on
        what it writes and not on what the file already contained. See the
        Q-P19-GATE-INERT-01 note at the top of this module for why.
        """
        if filepath in SELF_EXEMPT:
            return True

        added = added_lines(filepath, base)

        violations = []
        for line in added:
            match = ABSOLUTE_LANGUAGE.search(line)
            if match:
                violations.append(
                    f"P-HUMILITY: Absolute language {match.group(0)!r} added in "
                    f"{filepath}: {line.strip()[:80]}"
                )

        self.violations_found.extend(violations)
        return len(violations) == 0

    def report_violations(self) -> bool:
        """
        Create GitHub issues for any violations found.
        Returns True if no violations, False if issues created.
        """
        if not self.violations_found:
            return True

        # Create a single issue per run consolidating all violations
        body = "## Principle Compliance Violations Detected\n\n"
        body += "The following violations were detected by P19 (Detection beats compliance):\n\n"
        for i, v in enumerate(self.violations_found, 1):
            body += f"{i}. {v}\n"

        body += "\n### Action Required\n"
        body += "Review these violations and either:\n"
        body += "- Fix the code/decision to comply\n"
        body += "- File an IC exception with rationale (if the violation serves a higher principle)\n"

        issue = self.github.create_issue(
            title=f"[P19] Principle Compliance: {len(self.violations_found)} violation(s)",
            body=body,
            labels=["governance", "principle-compliance"]
        )

        if issue:
            print(f"✓ Created GitHub issue: {issue.get('url')}")
            return False
        else:
            print("✗ Failed to create GitHub issue")
            return False

    def run_check(self, commit_msg: str, files: List[str],
                  base: str = "HEAD~1") -> int:
        """
        Run compliance check on commit.
        Returns 0 if clean, 1 if violations found or the diff is unreadable.
        """
        print(f"Checking commit: {commit_msg[:60]}...")
        print(f"Files changed: {len(files)}")

        # Check commit message
        commit_clean = self.check_commit(commit_msg, files)

        # Check each changed file
        scanned = 0
        for f in files:
            if f.endswith(".py"):
                try:
                    self.check_code_file(f, base)
                    scanned += 1
                except subprocess.CalledProcessError as exc:
                    # A gate that cannot read its input must not report green.
                    print(f"::error::cannot diff {f} against {base}: "
                          f"{(exc.stderr or '').strip()[:200]}")
                    return 1

        print(f"Python files scanned: {scanned}")

        if self.violations_found:
            print(f"\n⚠ {len(self.violations_found)} violation(s) detected:")
            for v in self.violations_found:
                print(f"  - {v}")
            self.report_violations()
            return 1
        else:
            print("✓ All checks passed")
            return 0


def run_smoke_test() -> bool:
    """Smoke test for Builder v1.7.

    Every check below is a regression test for a way this gate reported green
    while inspecting nothing. The previous smoke test only constructed the bot,
    which is why the defect survived: the thing that was broken was never the
    thing being tested.
    """
    failures = []
    ran = [0]

    def check(name: str, cond: bool) -> None:
        ran[0] += 1
        if not cond:
            failures.append(name)

    try:
        bot = PrincipleComplianceBot()
        print(f"✓ PrincipleComplianceBot initialized ({len(bot.checker.principles)} principles)")
    except Exception as e:
        print(f"✗ Smoke test failed: {e}")
        return False

    # --- defect 1: the file list. This is the bug, pinned. -----------------
    two = "tools/a.py\ntools/b.py"
    check("a newline-separated list splits into its files",
          split_file_list(two) == ["tools/a.py", "tools/b.py"])
    check("a comma-separated list still splits",
          split_file_list("tools/a.py,tools/b.py") == ["tools/a.py", "tools/b.py"])
    check("a mixed list splits",
          split_file_list("a.py,\nb.py") == ["a.py", "b.py"])
    check("blank entries are dropped", split_file_list("\n\n") == [])
    check("an empty list is empty", split_file_list("") == [])
    # The exact failure: the old code split only on commas, so a newline list
    # became ONE entry that did not end in .py and no file was ever opened.
    check("a newline list is not swallowed into a single non-.py entry",
          len(split_file_list(two)) == 2
          and all(f.endswith(".py") for f in split_file_list(two)))

    # --- defect 2: added lines, whole words --------------------------------
    check("an absolute word is matched", bool(ABSOLUTE_LANGUAGE.search("this never fails")))
    check("matching is case-insensitive", bool(ABSOLUTE_LANGUAGE.search("Always true")))
    check("a substring is not a match", ABSOLUTE_LANGUAGE.search("nevertheless") is None)
    check("an unrelated line is not a match", ABSOLUTE_LANGUAGE.search("x = 1") is None)

    # --- self-exemption ----------------------------------------------------
    check("this module exempts itself, because a detector contains its pattern",
          __file__.endswith(SELF_EXEMPT[0].split("/")[-1])
          and bot.check_code_file(SELF_EXEMPT[0]) is True)

    # --- an unreadable diff must raise, never return empty -----------------
    try:
        added_lines("tools/agents/principle_compliance_bot_v1.py",
                    "definitely-not-a-ref-ffffffff")
        check("an unreadable diff raises rather than reporting no additions", False)
    except subprocess.CalledProcessError:
        check("an unreadable diff raises rather than reporting no additions", True)
    except Exception:
        check("an unreadable diff raises CalledProcessError specifically", False)

    print(f"{TOOL_NAME} smoke test: {ran[0] - len(failures)}/{ran[0]} checks")
    for f in failures:
        print(f"  ::error::{f}")
    return not failures


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Principle Compliance Bot — P19")
    parser.add_argument("--check-commit", type=str, help="Commit message to check")
    parser.add_argument("--files", type=str,
                        help="changed files, separated by commas or newlines")
    parser.add_argument("--base", type=str, default="HEAD~1",
                        help="ref to diff against when finding added lines")
    parser.add_argument("--smoke-test", action="store_true", help="Run smoke test")

    args = parser.parse_args()

    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)

    if args.check_commit and args.files:
        files = split_file_list(args.files)
        bot = PrincipleComplianceBot()
        exit_code = bot.run_check(args.check_commit, files, args.base)
        sys.exit(exit_code)
    else:
        parser.print_help()
        sys.exit(1)
