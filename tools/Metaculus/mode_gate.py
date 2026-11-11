# Builder v1.7 compliant
"""Fail-closed approval guard for Metaculus actions with external side effects.

This is a technical safety belt, not HumanAIOS governance admission. GitHub issue
admission, code review, bot registration and operator deployment consent remain
separate obligations. No API credentials are read or required by this module.
"""
from __future__ import annotations

TOOL_NAME = "metaculus_mode_gate"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "security_gate_tool"
TOOL_ZONE = 1

import os
from collections.abc import Mapping


class ExternalWritesNotApproved(RuntimeError):
    """Raised when a run has no explicit external-write authorization."""


LIVE_MODES = frozenset({"tournament", "metaculus_cup", "test_questions"})


def require_explicit_live_approval(
    *, mode: str, publish: bool, environ: Mapping[str, str] | None = None
) -> None:
    """Require both a CLI opt-in and a deployment-scoped opt-in for writes.

    Test questions are *not* a dry-run: they can submit forecasts and comments.
    This gate is invoked before constructing clients or dispatching any forecast.
    """
    if mode not in LIVE_MODES:
        raise ExternalWritesNotApproved(f"Unsupported live mode: {mode!r}")
    env = os.environ if environ is None else environ
    if not publish or env.get("METACULUS_LIVE_WRITES") != "APPROVED":
        raise ExternalWritesNotApproved(
            "External writes disabled. An approved deployment requires --publish "
            "and METACULUS_LIVE_WRITES=APPROVED. Even test_questions posts to Metaculus."
        )
    if mode in {"tournament", "metaculus_cup"} and env.get(
        "METACULUS_SCORED_WRITES"
    ) != "APPROVED":
        raise ExternalWritesNotApproved(
            "Scored tournament writes disabled. Explicit "
            "METACULUS_SCORED_WRITES=APPROVED is also required."
        )


def run_smoke_test() -> bool:
    """Offline safety gate smoke test; never reads live credentials."""
    try:
        require_explicit_live_approval(mode="test_questions", publish=False, environ={})
    except ExternalWritesNotApproved:
        return True
    return False


if __name__ == "__main__":
    raise SystemExit(0 if run_smoke_test() else 1)
