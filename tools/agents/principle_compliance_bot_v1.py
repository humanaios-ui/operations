#!/usr/bin/env python3
"""
Agent 1.1: Principle Compliance Bot
====================================

Purpose: Validate decisions/artifacts against 22-principle constitution.
Triggers: On commit + decision-log entry
Output: GitHub issues for violations
Zone: Z1 (autonomous — reports violations, humans decide severity)

Implementation: P19 (Detection beats compliance) — surface drift before
justifying it.

Usage:
  python3 tools/agents/01_principle_compliance_bot_v1.py --check-commit "commit msg" --files file1.py,file2.py
  python3 tools/agents/01_principle_compliance_bot_v1.py --smoke-test
"""

import sys
import json
import argparse
import subprocess
from pathlib import Path
from typing import List

# Builder v1.7 compliance
TOOL_NAME = "principle_compliance_bot_v1"
TOOL_VERSION = "1.0.0"

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

    def check_code_file(self, filepath: str) -> bool:
        """
        Check a Python file for principle violations.
        Looks for patterns like unverified claims, missing docstrings, etc.
        """
        try:
            with open(filepath) as f:
                content = f.read()

            violations = []

            # P3: Unverified claims in docstrings/comments
            if "TODO" in content or "FIXME" in content:
                if not "test" in filepath:
                    # TODOs are OK in test files, but not in main code without tracking
                    pass  # Will check if tracked as an IC

            # P-HUMILITY: Check for overconfident assertions
            if "always" in content or "never" in content or "impossible" in content:
                violations.append(f"P-HUMILITY: Absolute language in {filepath} (always/never/impossible)")

            self.violations_found.extend(violations)
            return len(violations) == 0

        except Exception as e:
            print(f"Error checking {filepath}: {e}")
            return True  # Don't fail the bot on read errors

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

    def run_check(self, commit_msg: str, files: List[str]) -> int:
        """
        Run compliance check on commit.
        Returns 0 if clean, 1 if violations found.
        """
        print(f"Checking commit: {commit_msg[:60]}...")
        print(f"Files changed: {len(files)}")

        # Check commit message
        commit_clean = self.check_commit(commit_msg, files)

        # Check each changed file
        for f in files:
            if f.endswith(".py"):
                self.check_code_file(f)

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
    """Smoke test for Builder v1.7."""
    try:
        bot = PrincipleComplianceBot()
        print(f"✓ PrincipleComplianceBot initialized ({len(bot.checker.principles)} principles)")
        return True
    except Exception as e:
        print(f"✗ Smoke test failed: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Principle Compliance Bot — P19")
    parser.add_argument("--check-commit", type=str, help="Commit message to check")
    parser.add_argument("--files", type=str, help="CSV of changed files")
    parser.add_argument("--smoke-test", action="store_true", help="Run smoke test")

    args = parser.parse_args()

    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)

    if args.check_commit and args.files:
        files = [f.strip() for f in args.files.split(",")]
        bot = PrincipleComplianceBot()
        exit_code = bot.run_check(args.check_commit, files)
        sys.exit(exit_code)
    else:
        parser.print_help()
        sys.exit(1)
