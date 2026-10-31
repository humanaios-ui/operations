"""
Metaculus bot E0 safety layer (issue #1101).  Pure stdlib: importable with no
network, no credentials and no forecasting-tools installed.

Guarantees (each is unit-tested in test_safety.py):
  * Default run mode is OFFLINE (no Metaculus / LLM / Supabase I/O).
  * Any live mode fails closed unless BOTH an explicit --publish flag AND the
    operator-set env HUMANAIOS_METACULUS_PUBLISH_APPROVED=1 are present, and the
    kill-switch is not engaged.
  * Run budgets are enforced BEFORE dispatch from known upper bounds.
  * Comments are private by default.

This module authorizes nothing by itself: the env approval is an operator (Z3)
deployment setting, not a Z2 ratification, and is not evidence of permission.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Mapping, Optional

OFFLINE_MODES = frozenset({"offline_fixture"})
LIVE_MODES = frozenset({"tournament", "metaculus_cup", "test_questions"})
ALL_MODES = tuple(sorted(OFFLINE_MODES | LIVE_MODES))
DEFAULT_MODE = "offline_fixture"

APPROVAL_ENV = "HUMANAIOS_METACULUS_PUBLISH_APPROVED"
KILL_SWITCH_ENV = "HUMANAIOS_METACULUS_KILL_SWITCH"
KILL_SWITCH_FILE_ENV = "HUMANAIOS_METACULUS_KILL_SWITCH_FILE"

# Permission states recorded in receipts (issue E0 item 2). Default is unverified.
PERMISSION_UNVERIFIED = "PERMISSION_UNVERIFIED"
NO_CP = "NO_CP"

# Releases known compromised (LiteLLM incident, 2026-10-21).
DENIED_PACKAGE_VERSIONS = {"litellm": {"1.107.0"}}


class RefusedError(RuntimeError):
    """Raised when a run is refused (fail closed)."""


def kill_switch_engaged(env: Mapping[str, str]) -> bool:
    if env.get(KILL_SWITCH_ENV, "").strip().lower() in {"1", "true", "yes", "on"}:
        return True
    path = env.get(KILL_SWITCH_FILE_ENV)
    return bool(path) and os.path.exists(path)


def require_live_allowed(mode: str, publish: bool, env: Mapping[str, str]) -> None:
    """Return None for allowed runs; raise RefusedError otherwise."""
    if mode not in ALL_MODES:
        raise RefusedError(f"unknown mode {mode!r}")
    if mode in OFFLINE_MODES:
        return
    if kill_switch_engaged(env):
        raise RefusedError("kill-switch engaged; live run refused")
    if not publish:
        raise RefusedError(f"mode {mode!r} is live; pass explicit --publish")
    if env.get(APPROVAL_ENV) != "1":
        raise RefusedError(
            f"mode {mode!r} needs operator-approved deployment config "
            f"({APPROVAL_ENV}=1); refusing"
        )


@dataclass(frozen=True)
class Budget:
    max_questions: int = 5
    max_samples_per_question: int = 5
    max_requests_per_question: int = 20
    max_usd_per_run: float = 1.00
    max_usd_per_question: float = 0.25
    max_total_retries: int = 10
    # Known upper bound for one question at max samples; used for pre-dispatch stop.
    est_usd_upper_per_question: float = 0.20

    def validate(self) -> None:
        for name in ("max_questions", "max_samples_per_question",
                     "max_requests_per_question", "max_total_retries"):
            if getattr(self, name) < 0:
                raise RefusedError(f"budget {name} must be >= 0")
        for name in ("max_usd_per_run", "max_usd_per_question",
                     "est_usd_upper_per_question"):
            if getattr(self, name) < 0:
                raise RefusedError(f"budget {name} must be >= 0")


def budget_from_env(env: Mapping[str, str]) -> Budget:
    d = Budget()
    def num(key, default, cast):
        raw = env.get(key)
        if raw is None or raw == "":
            return default
        try:
            return cast(raw)
        except ValueError as e:
            raise RefusedError(f"bad value for {key}: {raw!r}") from e
    b = Budget(
        max_questions=num("BOT_MAX_QUESTIONS", d.max_questions, int),
        max_samples_per_question=num("BOT_MAX_SAMPLES", d.max_samples_per_question, int),
        max_requests_per_question=num("BOT_MAX_REQUESTS_PER_Q", d.max_requests_per_question, int),
        max_usd_per_run=num("BOT_MAX_USD_RUN", d.max_usd_per_run, float),
        max_usd_per_question=num("BOT_MAX_USD_QUESTION", d.max_usd_per_question, float),
        max_total_retries=num("BOT_MAX_RETRIES", d.max_total_retries, int),
        est_usd_upper_per_question=num("BOT_EST_USD_UPPER_Q", d.est_usd_upper_per_question, float),
    )
    b.validate()
    return b


@dataclass
class BudgetTracker:
    budget: Budget
    spent_usd: float = 0.0
    questions_dispatched: int = 0
    retries_used: int = 0
    seen: set = field(default_factory=set)

    def may_dispatch(self, key: str) -> tuple[bool, str]:
        """Pre-dispatch check; never mutates. key = question+bot+competition."""
        b = self.budget
        if key in self.seen:
            return False, "duplicate submission"
        if self.questions_dispatched >= b.max_questions:
            return False, "max_questions reached"
        if b.est_usd_upper_per_question > b.max_usd_per_question:
            return False, "per-question upper bound exceeds per-question ceiling"
        if self.spent_usd + b.est_usd_upper_per_question > b.max_usd_per_run:
            return False, "next upper bound exceeds remaining USD budget"
        return True, "ok"

    def record_dispatch(self, key: str, billed_usd: float = 0.0) -> None:
        self.seen.add(key)
        self.questions_dispatched += 1
        self.spent_usd += max(billed_usd, 0.0)

    def allow_retry(self) -> bool:
        if self.retries_used >= self.budget.max_total_retries:
            return False
        self.retries_used += 1
        return True


def backoff_seconds(attempt: int, retry_after: Optional[float] = None,
                    base: float = 2.0, cap: float = 60.0) -> float:
    """Exponential backoff; honors a 429 Retry-After if larger."""
    delay = min(cap, base * (2 ** max(attempt, 0)))
    if retry_after is not None and retry_after > delay:
        delay = min(retry_after, cap)
    return delay


def dedupe_key(question_id: object, bot: str, competition: str) -> str:
    return f"{competition}:{bot}:{question_id}"


def comment_is_private(requested_private: Optional[bool] = None) -> bool:
    """FutureEval requires private comments. Only an explicit False is ever honored by
    callers that opt in; the default (and None) is private."""
    return True if requested_private is None else bool(requested_private)


def denied_pins(requirement_lines: list[str]) -> list[str]:
    """Return lines that pin a known-compromised package version."""
    bad = []
    for raw in requirement_lines:
        line = raw.split("#", 1)[0].strip().lower().replace(" ", "")
        for pkg, versions in DENIED_PACKAGE_VERSIONS.items():
            for v in versions:
                if line.startswith((f"{pkg}=={v}", f"{pkg}==={v}")):
                    bad.append(raw.strip())
    return bad


def build_receipt(mode: str, outcome: str, budget: Budget, **extra) -> dict:
    """Versioned run receipt. No secrets: only whitelisted scalar fields."""
    receipt = {
        "receipt_version": 1,
        "mode": mode,
        "outcome": outcome,
        "permission_state": PERMISSION_UNVERIFIED,
        "access_tier": NO_CP,
        "network_io": mode in LIVE_MODES and outcome == "dispatched",
        "budget": budget.__dict__.copy(),
    }
    for k, v in extra.items():
        if isinstance(v, (str, int, float, bool, type(None))):
            receipt[k] = v
    return receipt
