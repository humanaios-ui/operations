"""Passive, bounded independent-verification opportunity classification.

This is a screening instrument only. It cannot authorize contact, network
interaction, artifact execution, publication, or commercial representation.
Inputs must be public, user-submitted observations or synthetic fixtures.
"""
from dataclasses import dataclass
from typing import Mapping
from urllib.parse import urlsplit

OPPORTUNITY_CLASS = "INDEPENDENT_VERIFICATION_OPPORTUNITY"
ALLOWED_SOURCES = frozenset({"manual_public_url", "github_public", "challenge_public", "synthetic"})
NEED_STATES = frozenset({"EXPLICIT_VERIFICATION_REQUEST", "CLAIM_ONLY", "THIRD_PARTY_CRITIQUE", "UNKNOWN"})
CAPABILITY_STATES = frozenset({"OBSERVED_AVAILABLE", "OBSERVED_UNAVAILABLE", "UNKNOWN"})


@dataclass(frozen=True)
class OpportunityObservation:
    identifier: str
    subject: str
    source_url: str
    source_kind: str
    need_state: str
    claim_summary: str
    evidence_refs: tuple[str, ...] = ()
    required_capability: str = ""
    commercial_signal: str = "UNKNOWN"
    external_action_requested: bool = False


def valid_public_url(raw: str) -> bool:
    """Enforce public HTTPS URL shape without performing DNS/network resolution."""
    try:
        u = urlsplit(raw)
        return (
            u.scheme == "https"
            and bool(u.hostname)
            and "." in u.hostname
            and u.username is None
            and u.password is None
            and not u.fragment
            and u.port in (None, 443)
            and not u.hostname.lower().endswith((".local", ".internal"))
            and u.hostname.lower() not in {"localhost"}
        )
    except (ValueError, AttributeError):
        return False


def evaluate(observation: OpportunityObservation, capabilities: Mapping[str, str]) -> dict:
    """Classify *only* provided observations; never execute or obtain evidence."""
    if not observation.identifier or not observation.subject or not observation.claim_summary:
        raise ValueError("Missing candidate identifier/subject/claim")
    if observation.source_kind not in ALLOWED_SOURCES or not valid_public_url(observation.source_url):
        raise ValueError("Missing or invalid public source provenance")
    if observation.need_state not in NEED_STATES:
        raise ValueError("Unknown need state")
    if any(not valid_public_url(ref) for ref in observation.evidence_refs):
        raise ValueError("Evidence reference must be an explicit public HTTPS URL")
    if observation.external_action_requested:
        # Fail closed; do not even advance a candidate with requested external actions.
        status = "BLOCKED_EXTERNAL_ACTION"
    elif observation.need_state == "EXPLICIT_VERIFICATION_REQUEST":
        status = "CANDIDATE"
    elif observation.need_state == "THIRD_PARTY_CRITIQUE":
        status = "REVIEW_ONLY_NO_CONSENT"
    elif observation.need_state == "CLAIM_ONLY":
        status = "CLAIM_ONLY"
    else:
        status = "INSUFFICIENT_SIGNAL"

    capability = capabilities.get(observation.required_capability, "UNKNOWN")
    if capability not in CAPABILITY_STATES:
        capability = "UNKNOWN"
    return {
        "id": observation.identifier,
        "subject": observation.subject,
        "opportunity_class": OPPORTUNITY_CLASS,
        "source_url": observation.source_url,
        "source_kind": observation.source_kind,
        "claim_summary": observation.claim_summary,
        "claim_status": "UNVERIFIED",
        "need_state": observation.need_state,
        "evidence_refs": list(observation.evidence_refs),
        "evidence_state": "REFERENCES_ONLY" if observation.evidence_refs else "NO_INDEPENDENT_EVIDENCE",
        "screening_state": status,
        "required_capability": observation.required_capability,
        "capability_state": capability,
        "capability_fit": (
            "POTENTIAL_ONLY" if status == "CANDIDATE" and capability == "OBSERVED_AVAILABLE"
            else "NOT_ESTABLISHED"
        ),
        "commercial_signal": observation.commercial_signal if observation.commercial_signal in
            {"UNKNOWN", "EXPLICIT_PUBLIC", "DOCUMENTED_OFFER"} else "UNKNOWN",
        "authorization_state": "NOT_AUTHORIZED",
        "can_authorize": False,
        "permitted_action": "PASSIVE_SCREENING_ONLY",
    }


# Seed derived from user-provided public links; summaries are attribution, not verification.
DASE_SEED = OpportunityObservation(
    identifier="RMO-VERIFY-0001",
    subject="DASE (Dillon C.)",
    source_url="https://www.linkedin.com/posts/dillon-c-382b863b7_answer-me-this-i-really-need-to-know-share-7514412319523872769-dSa_/",
    source_kind="manual_public_url",
    need_state="EXPLICIT_VERIFICATION_REQUEST",
    claim_summary="Author reportedly seeks independent review of claimed computational approach; technical novelty unverified.",
    evidence_refs=(
        "https://www.linkedin.com/posts/dillon-c-382b863b7_dase-ugcPost-7496748437804199936-Thyd/",
    ),
    required_capability="computational_reproducibility_review",
)
