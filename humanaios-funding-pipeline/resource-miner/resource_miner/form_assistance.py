"""E0: offline, read-only application assistance for a captured BlueDot form.

No website interaction, applicant profile lookup, submission, or storage.
"""
from __future__ import annotations
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
    ("process_feedback", "How could the process improve?", "optional", False),
    ("public_consent", "May the grant be shared publicly?", "human_consent", False),
    ("public_url", "Public URL for grant listing", "profile", False),
    ("funder_sharing", "May application be shared with other funders?", "human_consent", False),
)
VALID_ORIGINS = frozenset({"USER_VERIFIED", "SOURCE_VERIFIED"})
VALID_ASSISTANCE = frozenset({"DRAFT_ALLOWED", "RESEARCH_ONLY", "PROOFREAD_ONLY", "UNKNOWN"})
# No live policy determination; UNKNOWN blocks AI-authored content pending review.

def build_packet(verified: Mapping[str, Mapping[str, Any]] | None = None,
                 assistance_policy: str = "UNKNOWN") -> dict[str, Any]:
    if assistance_policy not in VALID_ASSISTANCE:
        raise ValueError("Unknown assistance policy")
    verified = verified or {}
    if not isinstance(verified, Mapping):
        raise ValueError("Verified values must be a mapping")
    fields = []
    for key, label, kind, required in FIELDS:
        candidate = verified.get(key)
        usable = (
            isinstance(candidate, Mapping)
            and candidate.get("origin") in VALID_ORIGINS
            and isinstance(candidate.get("value"), (str, int, float))
            and bool(str(candidate["value"]).strip())
            and kind not in {"human_choice", "human_consent"}
        )
        # Only explicitly confirmed consent/choice may be proposed; never auto-select.
        if kind in {"human_choice", "human_consent"}:
            usable = False
        if kind == "draft" and assistance_policy != "DRAFT_ALLOWED":
            usable = False
        value = str(candidate["value"]) if usable else None
        fields.append({
            "id": key, "label": label, "kind": kind, "required": required,
            "suggested_value": value, "status": "READY_FOR_HUMAN_REVIEW" if usable else "NEEDS_INPUT",
            "evidence_ref": str(candidate.get("evidence_ref", "")) if usable else "",
        })
    return {
        "schema": "humanaios.form_assistance.e0",
        "form_id": FORM_ID,
        "form_source": FORM_SOURCE,
        "source_freshness": "USER_CAPTURED_NOT_LIVE_VERIFIED",
        "policy": assistance_policy,
        "policy_verified": False,
        "fields": fields,
        "submission": "DISABLED",
        "authority": "NONE",
        "requires_human_approval": True,
    }
