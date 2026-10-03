from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from .models import EvidenceRef
from .proposition import PropositionCandidate

RELATION_TYPES = {"SAME_AS", "SUPPORTS", "CONTRADICTS", "QUALIFIES", "SUPERSEDES", "CONTEXT_FOR", "UNRESOLVED"}
RESOLUTION_STATES = {"SINGLE_SOURCE", "CORROBORATED", "CONTESTED", "QUALIFIED", "SUPERSEDED", "UNRESOLVED"}
SYMMETRIC_RELATIONS = {"SAME_AS", "SUPPORTS", "CONTRADICTS", "CONTEXT_FOR", "UNRESOLVED"}
BOOLEAN_EXCLUSIVE_TYPES = {"OPPORTUNITY_EXISTS", "CURRENTLY_AVAILABLE"}
ADDITIVE_TYPES = {"RESOURCE_TYPE", "AFFORDANCE", "APPLICANT_TYPE", "CASH_MENTION"}

@dataclass(frozen=True)
class PropositionRelation:
    schema: str
    relation_id: str
    resolution_set_id: str
    relation_type: str
    source_proposition_id: str
    target_proposition_id: str
    basis: str
    symmetric: bool
    authority_effect: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PropositionResolutionSet:
    schema: str
    resolution_set_id: str
    resolution_token: str
    resolution_key: str
    subject_key: str
    proposition_type: str
    predicate: str
    state: str
    member_proposition_ids: list[str]
    member_opportunity_ids: list[str]
    source_mine_ids: list[str]
    distinct_source_count: int
    object_variants: list[Any]
    canonical_object_value: Any | None
    relations: list[PropositionRelation] = field(default_factory=list)
    unresolved_reasons: list[str] = field(default_factory=list)
    observed_from: str = ""
    observed_through: str = ""
    truth_state: str = "NOT_DETERMINED"
    eligibility_state: str = "NOT_EVALUATED"
    warrant_state: str = "NOT_EVALUATED"
    authorization_state: str = "NOT_REQUESTED"
    authority_effect: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["relations"] = [row.to_dict() for row in self.relations]
        return data


def _norm(value: Any) -> str:
    if isinstance(value, (dict, list, bool, int, float)) or value is None:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return " ".join(str(value).strip().split()).casefold()


def resolution_key(proposition: PropositionCandidate) -> str:
    subject = proposition.resolution_subject_key.strip()
    if not subject:
        raise ValueError("proposition reconciliation requires resolution_subject_key")
    return "::".join([subject, proposition.proposition_type.strip().upper(), proposition.predicate.strip().casefold()])


def stable_resolution_set_id(key: str) -> str:
    if not key.strip():
        raise ValueError("resolution key is required")
    return "PRS-" + hashlib.sha256(key.strip().encode("utf-8")).hexdigest()[:16].upper()


def resolution_token(resolution_set_id: str) -> str:
    return f"urn:humanaios:proposition-resolution:{resolution_set_id}"
