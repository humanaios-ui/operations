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

def stable_relation_id(resolution_set_id: str, relation_type: str, source_id: str, target_id: str, basis: str) -> str:
    relation_type = relation_type.strip().upper()
    if relation_type not in RELATION_TYPES:
        raise ValueError(f"unsupported relation_type: {relation_type}")
    source = source_id.strip().upper()
    target = target_id.strip().upper()
    if relation_type in SYMMETRIC_RELATIONS and target < source:
        source, target = target, source
    payload = "\0".join([resolution_set_id.strip().upper(), relation_type, source, target, " ".join(basis.split())])
    return "REL-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16].upper()


def _relation(resolution_set_id: str, relation_type: str, source: PropositionCandidate, target: PropositionCandidate, basis: str) -> PropositionRelation:
    relation_type = relation_type.upper()
    source_id = source.proposition_id
    target_id = target.proposition_id
    symmetric = relation_type in SYMMETRIC_RELATIONS
    if symmetric and target_id < source_id:
        source_id, target_id = target_id, source_id
    return PropositionRelation(
        schema="humanaios.proposition-relation.v1",
        relation_id=stable_relation_id(resolution_set_id, relation_type, source_id, target_id, basis),
        resolution_set_id=resolution_set_id,
        relation_type=relation_type,
        source_proposition_id=source_id,
        target_proposition_id=target_id,
        basis=basis,
        symmetric=symmetric,
    )


def _parse_time(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat((value or "").strip().replace("Z", "+00:00"))
    except ValueError:
        return None


def _same_day(a: PropositionCandidate, b: PropositionCandidate) -> bool:
    ta, tb = _parse_time(a.extracted_at), _parse_time(b.extracted_at)
    return bool(ta and tb and ta.date() == tb.date())


def _later_pair(a: PropositionCandidate, b: PropositionCandidate) -> tuple[PropositionCandidate, PropositionCandidate] | None:
    ta, tb = _parse_time(a.extracted_at), _parse_time(b.extracted_at)
    if not ta or not tb or ta == tb:
        return None
    return (a, b) if ta > tb else (b, a)


def _pair_relations(prs_id: str, a: PropositionCandidate, b: PropositionCandidate) -> list[PropositionRelation]:
    av, bv = _norm(a.object_value), _norm(b.object_value)
    if av == bv:
        out = [_relation(prs_id, "SAME_AS", a, b, "same subject, proposition type, predicate, and normalized object")]
        if a.mine_id and b.mine_id and a.mine_id != b.mine_id:
            out.append(_relation(prs_id, "SUPPORTS", a, b, "independent Mines asserted the same normalized proposition"))
        return out

    if a.proposition_type in BOOLEAN_EXCLUSIVE_TYPES and isinstance(a.object_value, bool) and isinstance(b.object_value, bool):
        if a.object_value != b.object_value and _same_day(a, b):
            return [_relation(prs_id, "CONTRADICTS", a, b, "exclusive boolean assertions conflict within the same observation day")]
        if a.mine_id and a.mine_id == b.mine_id:
            later = _later_pair(a, b)
            if later:
                newer, older = later
                return [_relation(prs_id, "SUPERSEDES", newer, older, "same Mine emitted a later exclusive state observation")]

    if a.proposition_type in {"STATUS", "DEADLINE"} and a.mine_id and a.mine_id == b.mine_id:
        later = _later_pair(a, b)
        if later:
            newer, older = later
            return [_relation(prs_id, "SUPERSEDES", newer, older, "same Mine emitted a later value for the same temporal predicate")]

    if a.proposition_type in ADDITIVE_TYPES:
        return [_relation(prs_id, "CONTEXT_FOR", a, b, "predicate is multi-valued; distinct objects may coexist")]

    return [_relation(prs_id, "UNRESOLVED", a, b, "same reconciliation scope and predicate but relation is not safely inferable")]

def _derive_state(relations: list[PropositionRelation], distinct_source_count: int, object_variant_count: int) -> str:
    kinds = {row.relation_type for row in relations}
    if "CONTRADICTS" in kinds:
        return "CONTESTED"
    if "UNRESOLVED" in kinds:
        return "UNRESOLVED"
    if "SUPERSEDES" in kinds:
        return "SUPERSEDED"
    if object_variant_count > 1 and kinds <= {"CONTEXT_FOR", "QUALIFIES"}:
        return "QUALIFIED"
    if distinct_source_count >= 2 and object_variant_count == 1:
        return "CORROBORATED"
    return "SINGLE_SOURCE"


def proposition_from_dict(data: dict[str, Any]) -> PropositionCandidate:
    payload = dict(data)
    payload["evidence"] = [row if isinstance(row, EvidenceRef) else EvidenceRef(**row) for row in payload.get("evidence") or []]
    return PropositionCandidate(**payload)


def reconcile_propositions(propositions: Iterable[PropositionCandidate | dict[str, Any]]) -> list[PropositionResolutionSet]:
    rows = [row if isinstance(row, PropositionCandidate) else proposition_from_dict(row) for row in propositions]
    groups: dict[str, list[PropositionCandidate]] = {}
    for row in rows:
        groups.setdefault(resolution_key(row), []).append(row)

    output: list[PropositionResolutionSet] = []
    for key in sorted(groups):
        members = sorted(groups[key], key=lambda row: row.proposition_id)
        first = members[0]
        prs_id = stable_resolution_set_id(key)
        relations: list[PropositionRelation] = []
        for i, left in enumerate(members):
            for right in members[i + 1:]:
                relations.extend(_pair_relations(prs_id, left, right))

        rel_map = {row.relation_id: row for row in relations}
        relations = [rel_map[rid] for rid in sorted(rel_map)]

        variants: dict[str, Any] = {}
        for member in members:
            variants.setdefault(_norm(member.object_value), member.object_value)
        object_variants = [variants[k] for k in sorted(variants)]
        source_mines = sorted({row.mine_id for row in members if row.mine_id})
        times = sorted(row.extracted_at for row in members if row.extracted_at)
        unresolved = sorted({row.basis for row in relations if row.relation_type == "UNRESOLVED"})
        state = _derive_state(relations, len(source_mines), len(object_variants))

        output.append(PropositionResolutionSet(
            schema="humanaios.proposition-resolution-set.v1",
            resolution_set_id=prs_id,
            resolution_token=resolution_token(prs_id),
            resolution_key=key,
            subject_key=first.resolution_subject_key,
            proposition_type=first.proposition_type,
            predicate=first.predicate,
            state=state,
            member_proposition_ids=[row.proposition_id for row in members],
            member_opportunity_ids=sorted({row.opportunity_id for row in members}),
            source_mine_ids=source_mines,
            distinct_source_count=len(source_mines),
            object_variants=object_variants,
            canonical_object_value=object_variants[0] if len(object_variants) == 1 else None,
            relations=relations,
            unresolved_reasons=unresolved,
            observed_from=times[0] if times else "",
            observed_through=times[-1] if times else "",
        ))
    return output


def write_resolution_sets_jsonl(path: str | Path, resolution_sets: Iterable[PropositionResolutionSet]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("".join(json.dumps(row.to_dict(), ensure_ascii=False, sort_keys=True) + "\n" for row in resolution_sets), encoding="utf-8")
