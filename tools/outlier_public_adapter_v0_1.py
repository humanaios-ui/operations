"""Public-only Outlier opportunity adapter; no network, credentials, or execution.

Issue #753. Inputs are caller-supplied, explicitly public first-party
metadata or synthetic fixtures. Never accepts task/dashboard material.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlsplit

PUBLIC_HOSTS = frozenset({"outlier.ai", "www.outlier.ai"})
# allowlisted public pages, not wildcard paths or authenticated app URLs
PUBLIC_PATHS = frozenset({
    "/faq", "/legal/terms-of-use", "/legal/community-guidelines",
    "/legal/privacy-policy",
})
FORBIDDEN_ACTIONS = frozenset({
    "AUTHENTICATED_DASHBOARD_SCRAPING", "CONTRACTOR_TASK_AUTOMATION",
    "EXPORT_PLATFORM_MATERIALS", "AUTOMATED_REFERRALS",
    "UNAUTHORIZED_CHATLAB_TESTING", "CLAIM_REWARD", "LOGIN",
    "SUBMIT_PAID_TASK", "SEND_REFERRAL", "RUN_ACAT", "EXECUTE_EXTERNAL_TOOL",
})
CATEGORIES = frozenset({
    "HUMAN_LABOR_INCOME_OPPORTUNITY", "HUMAN_NETWORK_REWARD",
    "AI_EVALUATION_ENVIRONMENT",
})


class PolicyDenied(ValueError):
    """An external-source or action boundary was not met."""


class Decision(str, Enum):
    CONDITIONAL_HUMAN_REVIEW = "CONDITIONAL_HUMAN_REVIEW"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    RESEARCH_POLICY_HOLD = "RESEARCH_POLICY_HOLD"


@dataclass(frozen=True)
class PublicCandidate:
    candidate_id: str
    category: str
    source_url: str
    source_standing: str
    # No submitted prompts, names, messages, task instructions or user records.
    evidence_label: str


def validate_public_url(url: str) -> str:
    """Fail closed on subdomain tricks, redirects, query data and non-public paths.

    This only validates a claimed source locator; it does not grant permission
    to fetch it, perform scraping or follow redirects.
    """
    p = urlsplit(url)
    if (p.scheme != "https" or p.hostname not in PUBLIC_HOSTS
            or p.port is not None or p.username is not None
            or p.password is not None or p.query or p.fragment
            or p.path not in PUBLIC_PATHS):
        raise PolicyDenied("not an exact allowlisted first-party public URL")
    return url


def screen(candidate: PublicCandidate) -> dict:
    validate_public_url(candidate.source_url)
    if candidate.category not in CATEGORIES:
        raise PolicyDenied("unknown opportunity category")
    if not candidate.candidate_id.startswith("OTL-E1-"):
        raise PolicyDenied("unexpected synthetic opportunity identifier")
    if candidate.source_standing != "PUBLIC_FIRST_PARTY_METADATA":
        raise PolicyDenied("unverified/privileged source")
    if candidate.evidence_label not in {
        "public_contributor_faq", "public_referral_faq", "public_terms_and_notice"
    }:
        raise PolicyDenied("unsupported evidence label")
    disposition = {
        "HUMAN_LABOR_INCOME_OPPORTUNITY": Decision.CONDITIONAL_HUMAN_REVIEW,
        "HUMAN_NETWORK_REWARD": Decision.INSUFFICIENT_EVIDENCE,
        "AI_EVALUATION_ENVIRONMENT": Decision.RESEARCH_POLICY_HOLD,
    }[candidate.category]
    return {
        "candidate_id": candidate.candidate_id,
        "category": candidate.category,
        "bop_state": "OBSERVED_PUBLIC_CATEGORY",
        "bsa_state": disposition.value,
        "expected_value": "UNKNOWN" if candidate.category != "AI_EVALUATION_ENVIRONMENT" else "NOT_APPLICABLE",
        "permission_state": "PUBLIC_METADATA_REVIEW_ONLY",
        "execution": "NOT_AUTHORIZED",
        "bot_state": "NOT_OBSERVED",
        "authority_effect": "NONE",
        "source_url": candidate.source_url,
    }


def authorize_action(action: str, *, external_authorization: object = None) -> str:
    """No external capability path exists in this adapter, even with a token.

    Authorization receipts must be evaluated by the independent control
    substrate, not treated as strings/booleans supplied to this adapter.
    """
    if action == "REVIEW_SUPPLIED_PUBLIC_METADATA":
        return "ALLOWED_NON_EXECUTING"
    raise PolicyDenied("Outlier public adapter cannot authorize action: " + str(action))


def evaluate_fixture(rows: list[PublicCandidate]) -> list[dict]:
    if len(rows) != 3 or len({r.candidate_id for r in rows}) != 3:
        raise PolicyDenied("E1 pilot requires three distinct synthetic cases")
    if {r.category for r in rows} != CATEGORIES:
        raise PolicyDenied("E1 pilot categories incomplete")
    return [screen(r) for r in rows]
