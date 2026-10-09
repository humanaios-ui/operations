"""
OI-BRIDGE-01 Phase 1 — CI Analyzer

Analyzes CI check run status and transitions.
Tracks state machine: UNKNOWN → QUEUED → RUNNING → PASS|FAIL|NEUTRAL
Prevents false positive (start state UNKNOWN, not PASS).
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone


class CheckStatus(Enum):
    """CI check run status values."""
    UNKNOWN = "UNKNOWN"        # Initial state (not PASS)
    QUEUED = "QUEUED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class CheckConclusion(Enum):
    """CI check run conclusion values."""
    SUCCESS = "success"
    FAILURE = "failure"
    NEUTRAL = "neutral"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"
    STALE = "stale"
    UNKNOWN = "unknown"


@dataclass
class CheckRun:
    """Single CI check run result."""
    check_name: str
    status: CheckStatus
    conclusion: Optional[CheckConclusion] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    output_summary: Optional[str] = None
    output_text: Optional[str] = None
    url: Optional[str] = None


@dataclass
class CIAnalysisResult:
    """Result from CI analysis."""
    pr_number: int
    commit_sha: str
    all_checks_pass: bool
    all_checks_complete: bool
    check_runs: List[CheckRun]
    overall_status: CheckStatus
    overall_conclusion: Optional[CheckConclusion]
    analyzed_at: str


class CIAnalyzer:
    """Analyze CI check runs and determine merge readiness."""

    def __init__(self):
        """Initialize CI analyzer."""
        pass

    def analyze_pr_checks(self, pr_number: int, commit_sha: str,
                         check_runs: List[Dict[str, Any]]) -> CIAnalysisResult:
        """
        Analyze CI check runs for PR.

        Args:
            pr_number: Pull request number
            commit_sha: Commit SHA
            check_runs: List of check run dicts from GitHub API

        Returns:
            CIAnalysisResult with status and conclusions
        """
        now = datetime.now(timezone.utc).isoformat()
        parsed_checks = []

        # Parse each check run
        for check_dict in check_runs:
            check = self._parse_check_run(check_dict)
            parsed_checks.append(check)

        # Determine overall status
        all_complete = all(
            check.status == CheckStatus.COMPLETED
            for check in parsed_checks
        )

        all_pass = all(
            check.conclusion in [CheckConclusion.SUCCESS, CheckConclusion.NEUTRAL, CheckConclusion.SKIPPED]
            for check in parsed_checks
            if check.status == CheckStatus.COMPLETED
        )

        # Determine overall conclusion
        overall_conclusion = None
        if all_complete:
            if all_pass:
                overall_conclusion = CheckConclusion.SUCCESS
            else:
                # Has failures
                has_failure = any(
                    check.conclusion == CheckConclusion.FAILURE
                    for check in parsed_checks
                )
                overall_conclusion = CheckConclusion.FAILURE if has_failure else CheckConclusion.NEUTRAL

        # Overall status (start with UNKNOWN, not PASS)
        if not parsed_checks:
            overall_status = CheckStatus.UNKNOWN
        elif all_complete:
            overall_status = CheckStatus.COMPLETED
        elif any(check.status == CheckStatus.IN_PROGRESS for check in parsed_checks):
            overall_status = CheckStatus.IN_PROGRESS
        elif any(check.status == CheckStatus.QUEUED for check in parsed_checks):
            overall_status = CheckStatus.QUEUED
        else:
            overall_status = CheckStatus.UNKNOWN

        return CIAnalysisResult(
            pr_number=pr_number,
            commit_sha=commit_sha,
            all_checks_pass=all_pass,
            all_checks_complete=all_complete,
            check_runs=parsed_checks,
            overall_status=overall_status,
            overall_conclusion=overall_conclusion,
            analyzed_at=now,
        )

    def _parse_check_run(self, check_dict: Dict[str, Any]) -> CheckRun:
        """
        Parse GitHub API check run into CheckRun object.

        Args:
            check_dict: Check run dict from GitHub API

        Returns:
            Parsed CheckRun
        """
        status_str = check_dict.get("status", "queued").lower()
        conclusion_str = check_dict.get("conclusion", "").lower() if check_dict.get("conclusion") else None

        # Map status
        if status_str == "queued":
            status = CheckStatus.QUEUED
        elif status_str == "in_progress":
            status = CheckStatus.IN_PROGRESS
        elif status_str == "completed":
            status = CheckStatus.COMPLETED
        else:
            status = CheckStatus.UNKNOWN

        # Map conclusion
        conclusion = None
        if conclusion_str:
            try:
                conclusion = CheckConclusion(conclusion_str)
            except ValueError:
                conclusion = CheckConclusion.UNKNOWN

        return CheckRun(
            check_name=check_dict.get("name", "unknown"),
            status=status,
            conclusion=conclusion,
            started_at=check_dict.get("started_at"),
            completed_at=check_dict.get("completed_at"),
            output_summary=check_dict.get("output", {}).get("summary"),
            output_text=check_dict.get("output", {}).get("text"),
            url=check_dict.get("details_url"),
        )

    def is_merge_ready(self, analysis: CIAnalysisResult) -> bool:
        """
        Determine if CI analysis indicates merge readiness.

        Requirements:
        - All checks complete
        - All checks pass or neutral/skipped

        Args:
            analysis: CIAnalysisResult

        Returns:
            True if ready to merge
        """
        return analysis.all_checks_complete and analysis.all_checks_pass

    def get_failing_checks(self, analysis: CIAnalysisResult) -> List[CheckRun]:
        """
        Get list of failing checks.

        Args:
            analysis: CIAnalysisResult

        Returns:
            List of CheckRun with FAILURE conclusion
        """
        return [
            check for check in analysis.check_runs
            if check.conclusion == CheckConclusion.FAILURE
        ]

    def get_incomplete_checks(self, analysis: CIAnalysisResult) -> List[CheckRun]:
        """
        Get list of incomplete checks.

        Args:
            analysis: CIAnalysisResult

        Returns:
            List of CheckRun not in COMPLETED status
        """
        return [
            check for check in analysis.check_runs
            if check.status != CheckStatus.COMPLETED
        ]


if __name__ == "__main__":
    analyzer = CIAnalyzer()

    # Test: Start state UNKNOWN, not PASS
    empty_checks = []
    result = analyzer.analyze_pr_checks(445, "abc123def456", empty_checks)
    print(f"Empty checks → overall_status: {result.overall_status.value} (should be UNKNOWN)")
    print(f"  all_checks_complete: {result.all_checks_complete}")
    print(f"  all_checks_pass: {result.all_checks_pass}")

    # Test: Mixed check run states
    mixed_checks = [
        {
            "name": "test",
            "status": "completed",
            "conclusion": "success",
            "started_at": "2026-09-22T20:00:00Z",
            "completed_at": "2026-09-22T20:05:00Z",
            "output": {"summary": "All tests passed"},
        },
        {
            "name": "lint",
            "status": "in_progress",
            "conclusion": None,
            "started_at": "2026-09-22T20:00:00Z",
            "output": {"summary": "Linting..."},
        },
    ]

    result = analyzer.analyze_pr_checks(445, "abc123def456", mixed_checks)
    print(f"\nMixed checks → overall_status: {result.overall_status.value} (should be IN_PROGRESS)")
    print(f"  all_checks_complete: {result.all_checks_complete}")
    print(f"  incomplete: {len(analyzer.get_incomplete_checks(result))}")

    # Test: All pass
    pass_checks = [
        {
            "name": "test",
            "status": "completed",
            "conclusion": "success",
            "started_at": "2026-09-22T20:00:00Z",
            "completed_at": "2026-09-22T20:05:00Z",
        },
        {
            "name": "lint",
            "status": "completed",
            "conclusion": "success",
            "started_at": "2026-09-22T20:00:00Z",
            "completed_at": "2026-09-22T20:05:00Z",
        },
    ]

    result = analyzer.analyze_pr_checks(445, "abc123def456", pass_checks)
    print(f"\nAll pass → overall_status: {result.overall_status.value} (should be COMPLETED)")
    print(f"  merge_ready: {analyzer.is_merge_ready(result)}")
    print(f"  all_checks_pass: {result.all_checks_pass}")
