"""Read-only advisory cues for promotional claims in opportunity descriptions.

Pattern matches are weak prompts for source verification, NOT fraud findings,
eligibility adjudication, user manipulation, or a reason to auto-block a mine.
No network, account data, behavioral profiling, or state mutation.
"""
from __future__ import annotations

import re

_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("UNVERIFIED_OUTCOME_PROMISE", re.compile(
        r"\b(?:guaranteed (?:approval|funding|acceptance)|"
        r"100% (?:approval|approved|guaranteed)|everyone qualifies)\b",
        re.I,
    )),
    ("AUTHORITY_CLAIM_REQUIRES_SOURCE_CHECK", re.compile(
        r"\b(?:government[- ]approved|officially endorsed|"
        r"certified by the government)\b",
        re.I,
    )),
    ("URGENCY_OR_SCARCITY_LANGUAGE", re.compile(
        r"\b(?:act now|last chance|pay today|expires in \d+ minutes)\b",
        re.I,
    )),
    ("UNUSUAL_PAYMENT_REQUEST_LANGUAGE", re.compile(
        r"\b(?:wire (?:money|a payment)|send (?:crypto|bitcoin)|"
        r"pay a (?:processing |application )?fee before)\b",
        re.I,
    )),
)


def promotional_claim_flags(text: str) -> list[str]:
    """Return stable, limited review prompts without classifying a source as fraud."""
    if not isinstance(text, str):
        return []
    sample = text[:1500]
    return [flag for flag, pattern in _RULES if pattern.search(sample)]
