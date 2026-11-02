"""
Builder v1.7 compliant
Metaculus bot run caps and comment privacy (issue #1101). Pure stdlib: importable with no
network, no credentials and no forecasting-tools installed.

Scope: this module does NOT decide whether a live run is allowed. That is `mode_gate.py`
(`--publish` plus deployment approval). This module adds what that gate lacks:

  * kill switch (env var or file) checked before any client is built
  * run budgets enforced BEFORE dispatch from known upper bounds (questions, USD)
  * duplicate-submission guard
  * a per-call attempt setting (BOT_ALLOWED_TRIES) for the two explicit model clients
  * private-by-default comments (FutureEval requires private comments)
  * denial of known-compromised package versions

NOT enforced here, so do not read them as protections:
  * a cap on model or API requests per question (it needs hooks inside forecasting-tools)
  * a run-wide retry budget: BOT_ALLOWED_TRIES is total attempts per call, including the
    first, and applies only to the explicit forecast and researcher clients. The parser and
    summarizer (set by model-name string) and any provider-level retries are not controlled.
  * the backoff_seconds helper is tested but is not called by the bot.

The checks here authorize nothing by themselves.
"""
from __future__ import annotations

TOOL_NAME = "safety"
TOOL_VERSION = "1.2.0"
TOOL_CATEGORY = "security_gate_tool"

import math
import os
from dataclasses import dataclass, field
from typing import Mapping, Optional

DUPLICATE_REASON = "duplicate submission"

KILL_SWITCH_ENV = "HUMANAIOS_METACULUS_KILL_SWITCH"
KILL_SWITCH_FILE_ENV = "HUMANAIOS_METACULUS_KILL_SWITCH_FILE"

# Releases known compromised (LiteLLM incident, 2026-10-21).
DENIED_PACKAGE_VERSIONS = {"litellm": {"1.107.0"}}


class RefusedError(RuntimeError):
    """Raised when a run is refused (fail closed)."""


def kill_switch_engaged(env: Mapping[str, str]) -> bool:
    if env.get(KILL_SWITCH_ENV, "").strip().lower() in {"1", "true", "yes", "on"}:
        return True
    path = env.get(KILL_SWITCH_FILE_ENV)
    return bool(path) and os.path.exists(path)


@dataclass(frozen=True)
class Budget:
    max_questions: int = 5
    max_samples_per_question: int = 5
    max_usd_per_run: float = 1.00
    max_usd_per_question: float = 0.25
    # Total attempts per model call, including the first. Allowed values: 1 or 2.
    allowed_tries: int = 2
    # Known upper bound for one question at max samples; used for pre-dispatch stop.
    est_usd_upper_per_question: float = 0.20

    def validate(self) -> None:
        # forecasting-tools requires at least one prediction per research report.
        if self.max_samples_per_question < 1:
            raise RefusedError("budget max_samples_per_question must be >= 1")
        if self.allowed_tries not in (1, 2):
            raise RefusedError("budget allowed_tries must be 1 or 2")
        if not self.max_questions >= 0:
            raise RefusedError("budget max_questions must be >= 0")
        for name in ("max_usd_per_run", "max_usd_per_question",
                     "est_usd_upper_per_question"):
            value = getattr(self, name)
            # NaN and +/-infinity would silently disable the USD checks.
            if not math.isfinite(value):
                raise RefusedError(f"budget {name} must be finite")
            if not value >= 0:
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
        max_usd_per_run=num("BOT_MAX_USD_RUN", d.max_usd_per_run, float),
        max_usd_per_question=num("BOT_MAX_USD_QUESTION", d.max_usd_per_question, float),
        allowed_tries=num("BOT_ALLOWED_TRIES", d.allowed_tries, int),
        est_usd_upper_per_question=num("BOT_EST_USD_UPPER_Q", d.est_usd_upper_per_question, float),
    )
    b.validate()
    return b


@dataclass
class BudgetTracker:
    budget: Budget
    spent_usd: float = 0.0
    questions_dispatched: int = 0
    seen: set = field(default_factory=set)

    def may_dispatch(self, key: str) -> tuple[bool, str]:
        """Pre-dispatch check; does not mutate state. key = mode + question."""
        b = self.budget
        if key in self.seen:
            return False, DUPLICATE_REASON
        if self.questions_dispatched >= b.max_questions:
            return False, "max_questions reached"
        if b.est_usd_upper_per_question > b.max_usd_per_question:
            return False, "per-question upper bound exceeds per-question ceiling"
        if self.spent_usd + b.est_usd_upper_per_question > b.max_usd_per_run:
            return False, "next upper bound exceeds remaining USD budget"
        return True, "ok"

    def record_dispatch(self, key: str, billed_usd: Optional[float] = None) -> None:
        """Reserve spend. With no actual amount, charge the per-question upper bound
        so the run cap is enforced at runtime."""
        self.seen.add(key)
        self.questions_dispatched += 1
        charge = self.budget.est_usd_upper_per_question if billed_usd is None else billed_usd
        self.spent_usd += max(charge, 0.0)

def backoff_seconds(attempt: int, retry_after: Optional[float] = None,
                    base: float = 2.0, cap: float = 60.0) -> float:
    """Exponential backoff; honors a 429 Retry-After if larger."""
    delay = min(cap, base * (2 ** max(attempt, 0)))  # cap only our own delay
    if retry_after is not None and retry_after > delay:
        delay = retry_after  # do not retry before the server's requested wait
    return delay


def comment_is_private(requested_private: Optional[bool] = None) -> bool:
    """FutureEval requires private comments. The default (and None) is private."""
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


def run_smoke_test() -> bool:
    """--smoke-test: offline checks of caps and privacy. No I/O."""
    t = BudgetTracker(Budget(max_questions=1))
    ok, _ = t.may_dispatch("a")
    t.record_dispatch("a")
    again, why = t.may_dispatch("a")
    return (ok and not again and why == DUPLICATE_REASON and comment_is_private()
            and not denied_pins(["litellm==1.106.0"])
            and bool(denied_pins(["litellm==1.107.0"])))


if __name__ == "__main__":
    import sys
    if "--smoke-test" in sys.argv:
        ok = run_smoke_test()
        print("smoke test PASSED" if ok else "smoke test FAILED")
        raise SystemExit(0 if ok else 1)
    print(f"{TOOL_NAME} {TOOL_VERSION}: library; use --smoke-test")
