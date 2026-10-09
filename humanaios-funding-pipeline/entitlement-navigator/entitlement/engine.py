from __future__ import annotations

from typing import Any

from .models import EvaluationResult
from .rules import evaluate_tree

LEGAL_NOTE = (
    "This result is a screening determination from published rules, not an award, legal opinion, "
    "title determination, probate order, lending decision, or agency eligibility decision."
)


def _status(program: dict[str, Any], state: str) -> str:
    if program.get("availability") == "historical":
        return "CLOSED_HISTORICAL"
    mode = program.get("match_mode", "benefit")
    if mode == "investigate":
        return "INELIGIBLE" if state == "FAIL" else "INVESTIGATE"
    if mode == "general":
        if state == "FAIL":
            return "INELIGIBLE"
        return "GENERAL_OPPORTUNITY" if state == "PASS" else "CONDITIONAL_MATCH"
    if state == "FAIL":
        return "INELIGIBLE"
    if state == "UNKNOWN" or program.get("program_review_required", False):
        return "CONDITIONAL_MATCH"
    return "RULE_MATCH"


def evaluate_program(program: dict[str, Any], profile: dict[str, Any]) -> EvaluationResult:
    tree = evaluate_tree(program.get("conditions"), profile)
    status = _status(program, tree.state)
    evidence = list(program.get("required_evidence", []))
    for p in tree.predicates:
        if p.state == "UNKNOWN":
            evidence.extend(p.evidence)
    evidence = list(dict.fromkeys(evidence))

    return EvaluationResult(
        program_id=program["id"],
        title=program["title"],
        applicant_entity=program.get("applicant_entity", "individual"),
        program_type=program.get("program_type", "benefit"),
        status=status,  # type: ignore[arg-type]
        summary=program.get("summary", ""),
        predicates=tree.predicates,
        required_evidence=evidence,
        next_actions=program.get("next_actions", []),
        sources=program.get("sources", []),
        last_verified=program.get("last_verified", "unknown"),
        legal_note=program.get("legal_note", LEGAL_NOTE),
        sort_priority=int(program.get("sort_priority", 100)),
    )


def evaluate_profile(
    profile: dict[str, Any],
    programs: list[dict[str, Any]],
    include_ineligible: bool = False,
) -> list[dict[str, Any]]:
    results = [evaluate_program(p, profile) for p in programs]
    if not include_ineligible:
        results = [
            r for r in results
            if r.status != "INELIGIBLE"
            and not (r.predicates and all(p.state == "UNKNOWN" for p in r.predicates))
        ]
    status_rank = {
        "RULE_MATCH": 0,
        "INVESTIGATE": 1,
        "CONDITIONAL_MATCH": 2,
        "GENERAL_OPPORTUNITY": 3,
        "CLOSED_HISTORICAL": 4,
        "INELIGIBLE": 5,
    }
    results.sort(key=lambda r: (status_rank[r.status], r.sort_priority, r.title))
    return [r.to_dict() for r in results]
