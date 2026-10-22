from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Any, Literal

TriState = Literal["PASS", "FAIL", "UNKNOWN"]
Status = Literal[
    "RULE_MATCH",
    "CONDITIONAL_MATCH",
    "INVESTIGATE",
    "INELIGIBLE",
    "CLOSED_HISTORICAL",
    "GENERAL_OPPORTUNITY",
]


@dataclass
class PredicateResult:
    label: str
    field: str | None
    state: TriState
    expected: Any = None
    observed: Any = None
    evidence: list[str] = field(default_factory=list)
    note: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EvaluationResult:
    program_id: str
    title: str
    applicant_entity: str
    program_type: str
    status: Status
    summary: str
    predicates: list[PredicateResult]
    required_evidence: list[str]
    next_actions: list[str]
    sources: list[dict[str, str]]
    last_verified: str
    legal_note: str
    sort_priority: int = 100

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["predicates"] = [p.to_dict() for p in self.predicates]
        return data
