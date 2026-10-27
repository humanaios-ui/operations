"""E0: offline, read-only application assistance for a captured BlueDot form.

No website interaction, applicant profile lookup, submission, or storage.
"""
from __future__ import annotations
import math
import re
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

FORM_ID = "BLUEDOT_RAPID_GRANT_CAPTURED_20261023"
FORM_SOURCE = "https://bluedot.org/programs/rapid-grants"
# The user's captured form is the source of this bounded schema, not a live crawl.
FIELDS = (
    ("name", "Your name", "profile", True),
    ("email", "Your email (Course Hub address)", "profile", True),
    ("location", "Where are you based?", "profile", True),
    ("public_profile", "LinkedIn or personal website", "profile", True),
    ("grant_type", "Grant type", "human_choice", True),
    ("one_sentence", "What are you working on? One sentence", "draft", True),
    ("work_links", "Links to work", "evidence", True),
    ("community_connection", "Connection to BlueDot community", "human_choice", True),
    ("request_usd", "Funding requested, nearest $50", "budget", True),
    ("project_detail", "Tell us more about your project", "draft", True),
    ("risk_reduction", "Contribution to reducing catastrophic AI risk or AI going well", "draft", True),
    ("progress", "What have you already done?", "evidence", True),
    ("why_succeed", "Why this project, you, and now?", "draft", True),
    ("budget_items", "Itemized use of grant funds", "budget", True),
    ("without_grant", "What would you do without the grant?", "human_choice", True),
    # Free-text answer: AI-authored text is gated like every other draft field.
    ("process_feedback", "How could the process improve?", "draft", False),
    ("public_consent", "May the grant be shared publicly?", "human_consent", False),
    ("public_url", "Public URL for grant listing", "profile", False),
    ("funder_sharing", "May application be shared with other funders?", "human_consent", False),
)
VALID_ORIGINS = frozenset({"USER_VERIFIED", "SOURCE_VERIFIED"})
VALID_ASSISTANCE = frozenset({"DRAFT_ALLOWED", "RESEARCH_ONLY", "PROOFREAD_ONLY", "UNKNOWN"})
HUMAN_ONLY_KINDS = frozenset({"human_choice", "human_consent"})
FUNDING_STEP_USD = 50
# No live policy determination; UNKNOWN blocks AI-authored content pending review.


def _valid_funding_amount(value: Any) -> bool:
    """True only for a positive, finite amount in $50 increments."""
    if isinstance(value, bool):
        return False
    raw = str(value).strip()
    if raw.startswith("$"):
        raw = raw[1:]
    if not re.fullmatch(r"(?:[0-9]+|[1-9][0-9]{0,2}(?:,[0-9]{3})+)(?:\.[0-9]+)?", raw):
        return False
    try:
        amount = Decimal(raw.replace(",", ""))
    except (InvalidOperation, ValueError):
        return False
    return amount.is_finite() and amount > 0 and amount % FUNDING_STEP_USD == 0


def _candidate_usable(candidate: Any, kind: str, key: str) -> bool:
    if not isinstance(candidate, Mapping) or candidate.get("origin") not in VALID_ORIGINS:
        return False
    value = candidate.get("value")
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        return False
    if isinstance(value, float) and not math.isfinite(value):
        return False
    if not str(value).strip():
        return False
    if key == "request_usd" and not _valid_funding_amount(value):
        return False
    return True


def build_packet(verified: Mapping[str, Mapping[str, Any]] | None = None,
                 assistance_policy: str = "UNKNOWN",
                 policy_evidence_ref: str = "") -> dict[str, Any]:
    if assistance_policy not in VALID_ASSISTANCE:
        raise ValueError("Unknown assistance policy")
    verified = verified or {}
    if not isinstance(verified, Mapping):
        raise ValueError("Verified values must be a mapping")
    # A policy counts as verified only when a decision other than UNKNOWN
    # is recorded together with a non-empty evidence reference.
    policy_verified = (
        assistance_policy != "UNKNOWN"
        and isinstance(policy_evidence_ref, str)
        and bool(policy_evidence_ref.strip())
    )
    drafts_allowed = policy_verified and assistance_policy == "DRAFT_ALLOWED"
    fields = []
    for key, label, kind, required in FIELDS:
        candidate = verified.get(key)
        # Choices and consent are never auto-selected, whatever the origin.
        usable = kind not in HUMAN_ONLY_KINDS and _candidate_usable(candidate, kind, key)
        if kind == "draft" and not drafts_allowed:
            usable = False
        fields.append({
            "id": key, "label": label, "kind": kind, "required": required,
            "suggested_value": str(candidate["value"]) if usable else None,
            "status": "READY_FOR_HUMAN_REVIEW" if usable else "NEEDS_INPUT",
            "origin": candidate["origin"] if usable else None,
            "evidence_ref": str(candidate.get("evidence_ref", "")) if usable else "",
        })
    return {
        "schema": "humanaios.form_assistance.e0",
        "form_id": FORM_ID,
        "form_source": FORM_SOURCE,
        "source_freshness": "USER_CAPTURED_NOT_LIVE_VERIFIED",
        "policy": assistance_policy,
        "policy_verified": policy_verified,
        "policy_evidence_ref": policy_evidence_ref.strip() if policy_verified else "",
        "fields": fields,
        "submission": "DISABLED",
        "authority": "NONE",
        "requires_human_approval": True,
    }
