"""Local, read-only portfolio resource observation.

Consumes an operator-approved, minimized profile projection plus SEED-derived
business facts. Does not read raw resume, contacts, credentials, or GitHub.
Does not grant eligibility, publish a portfolio, or mutate downstream files.
"""
from __future__ import annotations

import json
import re
from typing import Any

SCHEMA = "humanaios.portfolio-maintainer.v0.1"
PROFILE_SCHEMA = "humanaios.private-profile-projection.v0.1"
BUSINESS_SCHEMA = "humanaios.business-anchor.v0.1"
NODE_ID = "urn:humanaios:controlled-resource:owner-portfolio"
BUSINESS_SOURCE = "https://github.com/humanaios-ui/operations/blob/main/SEED.md"
CAPABILITY_CODES = frozenset({
    "ai_evaluation", "data_quality", "research_operations",
    "quality_compliance", "statistical_analysis", "workflow_automation",
})
_STALE_CLAIMS = (
    "374k verified workers", "10k mrr", "fortune 500",
    "physical execution layer", "market expansion",
)
_REV = re.compile(r"^[a-f0-9]{40}$")


def _exact_keys(value: Any, keys: set[str], what: str) -> dict:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{what}: unexpected or missing fields")
    return value


def _revision(value: Any) -> str:
    if not isinstance(value, str) or not _REV.fullmatch(value):
        raise ValueError("source revision must be an exact 40-character Git SHA")
    return value


def observe_portfolio(
    personal: dict[str, Any],
    business: dict[str, Any],
    consumer: dict[str, Any],
    *,
    prior: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a bounded change report. All inputs are caller-supplied, not authenticated."""
    _exact_keys(personal, {
        "schema", "capability_codes", "approved_for_local_matching", "revision",
    }, "personal projection")
    if personal["schema"] != PROFILE_SCHEMA:
        raise ValueError("wrong personal projection schema")
    if personal["approved_for_local_matching"] is not True:
        raise ValueError("owner approval required for even local profile matching")
    codes = personal["capability_codes"]
    if (not isinstance(codes, list) or len(codes) > 6
            or not all(isinstance(code, str) for code in codes)
            or len(codes) != len(set(codes))
            or any(code not in CAPABILITY_CODES for code in codes)):
        raise ValueError("only allowlisted, non-identifying capability codes are accepted")
    personal_revision = _revision(personal["revision"])

    _exact_keys(business, {
        "schema", "source_url", "revision", "stage", "legal_form", "focus",
    }, "business anchor")
    if business["schema"] != BUSINESS_SCHEMA or business["source_url"] != BUSINESS_SOURCE:
        raise ValueError("only the canonical SEED business anchor is accepted")
    business_revision = _revision(business["revision"])
    if business["stage"] != "research" or business["legal_form"] != "llc":
        raise ValueError("business anchor conflicts with selected model")
    if business["focus"] != "behavioral_observability":
        raise ValueError("business focus conflicts with SEED")

    _exact_keys(consumer, {
        "description", "fundingStage", "budgetRange", "teamSize",
    }, "consumer snapshot")
    if not isinstance(consumer["description"], str) or len(consumer["description"]) > 2000:
        raise ValueError("invalid public consumer description")
    issues = []
    text = consumer["description"].casefold()
    for claim in _STALE_CLAIMS:
        if claim in text:
            issues.append("UNSUPPORTED_CLAIM:" + claim.replace(" ", "_").upper())
    if consumer["fundingStage"] != "research":
        issues.append("STAGE_DRIFT")
    if consumer["budgetRange"] is not None:
        issues.append("UNAPPROVED_BUDGET_RANGE")
    if consumer["teamSize"] != "solo":
        issues.append("TEAM_SIZE_RECHECK")

    if prior is not None:
        _exact_keys(prior, {"personal_revision", "business_revision"}, "prior revisions")
        if _revision(prior["personal_revision"]) != personal_revision:
            issues.append("PERSONAL_SOURCE_CHANGED")
        if _revision(prior["business_revision"]) != business_revision:
            issues.append("BUSINESS_SOURCE_CHANGED")

    return {
        "schema": SCHEMA,
        "node_id": NODE_ID,
        "node_role": "CONTROLLED_RESOURCE_SOURCE",
        "source_states": {
            "personal": "OWNER_CONTROLLED_LOCAL_PROJECTION",
            "business": "CALLER_SUPPLIED_CANONICAL_SEED",
        },
        "capability_codes": sorted(codes),
        "issues": sorted(set(issues)),
        "review_state": "REVIEW_REQUIRED" if issues else "NO_DRIFT_OBSERVED",
        "eligibility_assessed": False,
        "authority_effect": "NONE",
        "mutation_performed": False,
        "next_action": "HUMAN_REVIEW" if issues else "NONE",
        "private_revisions": {
            "personal_revision": personal_revision,
            "business_revision": business_revision,
        },
        "links": [
            {"from": NODE_ID, "rel": "grounded_in", "to": "owner-controlled-profile"},
            {"from": NODE_ID, "rel": "grounded_in", "to": BUSINESS_SOURCE},
            {"from": NODE_ID, "rel": "informs", "to": "grant-matching-profile"},
        ],
    }


def main() -> None:
    """Explicit local invocation only. Never prints source YAML or private notes."""
    import argparse
    from pathlib import Path
    p = argparse.ArgumentParser(description="Read-only owner portfolio drift check")
    p.add_argument("--personal-projection", required=True)
    p.add_argument("--business-anchor", required=True)
    p.add_argument("--consumer-snapshot", required=True)
    p.add_argument("--prior-revisions")
    args = p.parse_args()
    def read(path: str) -> dict:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    output = observe_portfolio(
        read(args.personal_projection),
        read(args.business_anchor),
        read(args.consumer_snapshot),
        prior=read(args.prior_revisions) if args.prior_revisions else None,
    )
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
