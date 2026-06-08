"""
schema.py — HumanAIOS Funding Pipeline
Data schema for a funding/resource opportunity.
Pydantic v2 compatible.
"""
from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# ─── Enumerations ──────────────────────────────────────────────────────────

class Category(str, Enum):
    native          = "native"
    ai_safety       = "ai_safety"
    research_grant  = "research_grant"
    contest         = "contest"
    compute_credit  = "compute_credit"
    fellowship      = "fellowship"
    paid_work       = "paid_work"
    publishing      = "publishing"
    free_api        = "free_api"
    free_infra      = "free_infra"


class Status(str, Enum):
    active    = "active"
    rolling   = "rolling"
    closed    = "closed"
    upcoming  = "upcoming"
    uncertain = "uncertain"


# ─── Core model ────────────────────────────────────────────────────────────

class Opportunity(BaseModel):
    """One funding, resource, or income opportunity."""

    # Required
    name:     str
    category: Category
    sponsor:  str
    url:      str

    # Optional metadata
    eligibility_tags:  List[str]      = Field(default_factory=list)
    award_size:        Optional[str]  = None   # e.g. "up to $305,000"
    deadline:          Optional[str]  = None   # ISO date or free text
    deadline_cadence:  Optional[str]  = None   # "rolling", "annual", etc.

    # Profile flags (Cherokee Nation / AI-safety / TRL)
    native_eligible:    bool = False
    ai_safety_relevant: bool = False
    trl_fit:            str  = "any"   # e.g. "TRL2-3", "any"

    # Pipeline state
    status:       Status          = Status.active
    last_checked: Optional[str]   = None  # ISO date stamp set by checker
    url_ok:       Optional[bool]  = None  # True/False/None (not yet checked)
    notes:        Optional[str]   = None
    source:       Optional[str]   = None  # attribution domain / org

    # ── Validators ──────────────────────────────────────────────────────

    @field_validator("url")
    @classmethod
    def _require_scheme(cls, v: str) -> str:
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError(f"url must start with http(s)://: {v!r}")
        return v

    # ── Helpers ─────────────────────────────────────────────────────────

    def is_deadline_soon(self, within_days: int = 30) -> bool:
        """Return True if deadline is a parseable ISO date within N days."""
        if not self.deadline:
            return False
        for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
            try:
                d = datetime.strptime(self.deadline.strip(), fmt).date()
                delta = (d - date.today()).days
                return 0 <= delta <= within_days
            except ValueError:
                continue
        return False

    def priority_score(self) -> int:
        """Lower = higher priority. Used for report ordering."""
        CAT_ORDER = {
            "native": 0, "ai_safety": 1, "research_grant": 2,
            "contest": 3, "compute_credit": 4, "fellowship": 5,
            "paid_work": 6, "free_api": 7, "free_infra": 8, "publishing": 9,
        }
        score = CAT_ORDER.get(self.category.value, 99)
        # Boost: native + ai_safety intersection = very high priority
        if self.native_eligible and self.ai_safety_relevant:
            score -= 1
        # Boost: deadline soon
        if self.is_deadline_soon(60):
            score -= 1
        return score


# ─── Summary helper ────────────────────────────────────────────────────────

class PipelineSummary(BaseModel):
    generated: str
    total: int
    native_eligible: int
    ai_safety_relevant: int
    both_flags: int
    by_category: dict
    deadline_soon_30d: int
    active_rolling: int
