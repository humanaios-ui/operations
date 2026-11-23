"""Synthetic-only Witness intake screening examples (not a production verifier)."""
from __future__ import annotations

SCHEMA = "humanaios.witness.intake.synthetic.v0.1"
KINDS = {
    "AGENT_IDENTITY": {"human_label", "agent_self_label", "authenticated_principal"},
    "SCOPE_TERM": {"scope_a", "scope_b", "assertion_a", "assertion_b"},
    "STALE_DEPENDENCY": {"historic_pr_state", "latest_pr_state", "live_capability_verified"},
    "RIEMANN_PROOF": {"researcher_claim", "community_certificate", "prize_or_formal_acceptance"},
    "GTA_SALES": {"issuer_estimate", "issuer_original_release", "independent_audit"},
}


def _require(ok: bool, why: str) -> None:
    if not ok:
        raise ValueError(why)


def screen(case: dict) -> dict:
    """Return labels for a validated fictional case; labels never mutate sources."""
    _require(type(case) is dict and set(case) == {
        "schema", "case_id", "is_synthetic", "authority_effect", "kind", "facts"
    }, "invalid envelope")
    _require(case["schema"] == SCHEMA
             and case["is_synthetic"] is True
             and case["authority_effect"] == "NONE", "real or authoritative intake denied")
    _require(type(case["case_id"]) is str
             and case["case_id"].startswith("DEMO-")
             and len(case["case_id"]) <= 70, "only DEMO cases allowed")
    kind, facts = case["kind"], case["facts"]
    _require(type(kind) is str and kind in KINDS,
             "invalid case type")
    _require(type(facts) is dict and set(facts) == KINDS[kind],
             "invalid case fields")

    if kind == "AGENT_IDENTITY":
        _require(all(type(facts[k]) is str and 0 < len(facts[k]) < 80
                     for k in ("human_label", "agent_self_label")), "invalid labels")
        _require(facts["authenticated_principal"] is None, "no runtime identity assertions allowed")
        status = ("PROVENANCE_CONFLICT" if facts["human_label"] != facts["agent_self_label"]
                  else "UNAUTHENTICATED_SELF_REPORT")
        disposition, relation = "HOLD", "UNRESOLVED"

    elif kind == "SCOPE_TERM":
        _require(facts["scope_a"] in ("PLANNING_ANCHOR", "RATIFIED_DATA_SCHEMA")
                 and facts["scope_b"] in ("PLANNING_ANCHOR", "RATIFIED_DATA_SCHEMA")
                 and type(facts["assertion_a"]) is bool
                 and type(facts["assertion_b"]) is bool, "bad scope fields")
        # Different predicates can both hold; equal scope plus opposing
        # assertions is the only synthetic contradiction *candidate*.
        distinct = facts["scope_a"] != facts["scope_b"]
        status = "SCOPE_QUALIFICATION" if distinct else (
            "CONTRADICTION_CANDIDATE" if facts["assertion_a"] != facts["assertion_b"]
            else "NO_CONFLICT_OBSERVED")
        disposition, relation = ("CONTINUE_WITH_ID", "QUALIFIES") if distinct else (
            ("HOLD", "UNRESOLVED") if status == "CONTRADICTION_CANDIDATE"
            else ("CONTINUE_WITH_ID", "CONTEXT_FOR"))

    elif kind == "STALE_DEPENDENCY":
        _require(facts["historic_pr_state"] in ("OPEN", "MERGED")
                 and facts["latest_pr_state"] in ("OPEN", "MERGED")
                 and type(facts["live_capability_verified"]) is bool, "invalid dependency facts")
        status = ("STALE_HOLD_SUPERSEDED" if
                  facts["historic_pr_state"] == "OPEN" and facts["latest_pr_state"] == "MERGED"
                  else "NO_STALE_MERGE_SHOWN")
        # Merged PR is a repository event, NOT a deployment or user outcome.
        disposition, relation = "VERIFY", "SUPERSEDES" if status == "STALE_HOLD_SUPERSEDED" else "UNRESOLVED"

    elif kind == "RIEMANN_PROOF":
        _require(all(type(v) is bool for v in facts.values()), "proof facts must be boolean")
        _require(facts["researcher_claim"], "no original claimant")
        status = ("COMMUNITY_CERTIFICATION_REPORTED" if facts["community_certificate"]
                  else "CLAIM_ONLY")
        # A community technical certification does not itself establish a prize/award;
        # neither may be inferred from a model's own assertion.
        disposition, relation = "VERIFY", "QUALIFIES"

    else:  # GTA_SALES
        _require(all(type(v) is bool for v in facts.values()), "sales facts must be boolean")
        _require(facts["issuer_estimate"] and facts["issuer_original_release"],
                 "issuer source required")
        status = "ISSUER_REPORTED_NOT_INDEPENDENTLY_AUDITED" if not facts["independent_audit"] else "AUDIT_REPORTED_NOT_AUTHENTICATED"
        disposition, relation = "CONTINUE_WITH_ID", "QUALIFIES"

    return {
        "case_id": case["case_id"], "status": status,
        "disposition": disposition, "proposed_relation": relation,
        "source_verification": "FIXTURE_ONLY_NOT_PERFORMED",
        "authenticated_actor": False,
        "canonical_acat_score": None, "authority_effect": "NONE",
    }
