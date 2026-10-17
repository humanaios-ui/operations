"""E0: read-only motion projection over *private* newsletter proposal records.

No new persistence, agent, consensus process, authority, or publication transport.
The caller must enforce access control before passing an authorized NewsletterStore.
Do not serialize a result into public artifacts without a separate privacy review.
"""
from __future__ import annotations

import hashlib
import re

SCHEMA = "humanaios.motion-candidate.e0"
REVIEW_CAP = 200
KINDS = {"PROPOSAL", "CORRECTION", "OBJECTION"}


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def project_motion(store, proposal_id: str) -> dict:
    """Reconstruct a proposal's non-content state from the existing private store.

    The proposal body and review rationales stay in the original private SQLite
    records. The projection contains hashes and pointers, NOT those raw texts.
    It never treats votes, endorsements or other prose as authorization.
    """
    if not isinstance(proposal_id, str) or not re.fullmatch(r"NLP-[a-f0-9]{32}", proposal_id):
        raise ValueError("invalid proposal ID")

    row = store.db.execute(
        "SELECT proposal, edition, receipt, text, kind FROM newsletter_contributions "
        "WHERE proposal=?", (proposal_id,)
    ).fetchone()
    if row is None or row["kind"] not in KINDS:
        raise ValueError("unknown motion proposal")
    edition = store.edition(row["edition"])  # Verifies the existing edition digest.
    reviews = store.db.execute(
        "SELECT seq, stance, rationale FROM newsletter_review_events "
        "WHERE proposal=? ORDER BY seq LIMIT ?", (proposal_id, REVIEW_CAP + 1)
    ).fetchall()
    if len(reviews) > REVIEW_CAP:
        raise ValueError("review limit reached; no partial deliberation projection")

    # Preserve differences and their sequence. Never collapse them into a vote.
    review_trail = [
        {"seq": item["seq"], "stance": item["stance"],
         "rationale_sha256": _sha(item["rationale"])}
        for item in reviews
    ]
    # Deterministic, non-authoritative content digest. Not an attestation.
    return {
        "schema": SCHEMA,
        "motion_id": "MOT-E0-" + _sha(proposal_id)[:20],
        "motion_type": row["kind"],
        "status": "PROPOSED_FOR_HUMAN_REVIEW",
        "subject": "REQUIRES_HUMAN_INTERPRETATION",
        "source": {
            "kind": "LIVING_NEWSLETTER_PRIVATE",
            "proposal_id": row["proposal"],
            "edition_id": row["edition"],
            "receipt_id": row["receipt"],
            "proposal_text_sha256": _sha(row["text"]),
            "edition_sha256": edition["content_sha256"],
            "evidence_references": edition["content"].get("references", []),
            "content_retained_at": "PRIVATE_NEWSLETTER_STORE",
        },
        "deliberation": {
            "reviews": review_trail,
            "consensus": "NOT_ESTABLISHED",
            "ratification": "HUMAN_PROCESS_REQUIRED",
        },
        "constraints": {
            "authority": "NONE",
            "eligibility": "NOT_ASSESSED",
            "execution": "DISABLED",
            "publication_authorization": "NONE",
            "admission": "NOT_GRANTED",
        },
        "receipt_kind": "UNSIGNED_PRIVATE_PROJECTION_NOT_ATTESTATION",
    }
