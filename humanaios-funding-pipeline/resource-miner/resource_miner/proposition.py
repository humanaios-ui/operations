from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .models import EvidenceRef, ResourceCandidate
from .normalize import utcnow_iso

PROPOSITION_TYPES = {
    "OPPORTUNITY_EXISTS",
    "CURRENTLY_AVAILABLE",
    "RESOURCE_TYPE",
    "AFFORDANCE",
    "DEADLINE",
    "CASH_MENTION",
    "APPLICANT_TYPE",
    "STATUS",
}
EPISTEMIC_ROLES = {"OBSERVATION", "SOURCE_ASSERTION", "CLASSIFICATION", "TEXT_EXTRACTION"}
EXTRACTION_METHODS = {
    "TOKENIZED_OPPORTUNITY",
    "DIRECT_OBSERVATION",
    "NORMALIZER_CLASSIFICATION",
    "NORMALIZER_EXTRACTION",
}


@dataclass
class PropositionCandidate:
    schema: str
    proposition_id: str
    proposition_token: str
    opportunity_id: str
    opportunity_token: str
    proposition_type: str
    epistemic_role: str
    subject: str
    predicate: str
    object_value: Any
    statement: str
    semantic_key: str
    resolution_subject_key: str
    extracted_at: str
    extraction_method: str
    extraction_confidence: float | None = None
    evidence: list[EvidenceRef] = field(default_factory=list)
    source_url: str = ""
    mine_id: str = ""
    mine_name: str = ""
    authority_effect: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _norm(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return " ".join(str(value).strip().split()).casefold()


def proposition_semantic_key(
    proposition_type: str,
    predicate: str,
    object_value: Any,
) -> str:
    return "::".join(
        [
            proposition_type.strip().upper(),
            _norm(predicate),
            _norm(object_value),
        ]
    )


def resolution_subject_key(resource: ResourceCandidate) -> str:
    explicit = str(resource.raw.get("resolution_subject_key") or "").strip()
    if explicit:
        return _norm(explicit)
    identity = str(resource.opportunity_identity or resource.canonical_url or "").strip()
    kind = str(resource.opportunity_kind or "").strip().lower()
    if not identity:
        return ""
    return "::".join([kind, _norm(identity)])


def stable_proposition_id(opportunity_id: str, semantic_key: str) -> str:
    opportunity_id = opportunity_id.strip().upper()
    semantic_key = semantic_key.strip()
    if not opportunity_id or not semantic_key:
        raise ValueError("opportunity_id and semantic_key are required")
    payload = "\0".join([opportunity_id, semantic_key])
    return "PRP-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16].upper()


def proposition_token(proposition_id: str) -> str:
    return f"urn:humanaios:proposition:{proposition_id}"


def _candidate(
    resource: ResourceCandidate,
    *,
    proposition_type: str,
    epistemic_role: str,
    predicate: str,
    object_value: Any,
    statement: str,
    extraction_method: str,
    evidence: list[EvidenceRef] | None = None,
    extraction_confidence: float | None = None,
) -> PropositionCandidate:
    if proposition_type not in PROPOSITION_TYPES:
        raise ValueError(f"unsupported proposition_type: {proposition_type}")
    if epistemic_role not in EPISTEMIC_ROLES:
        raise ValueError(f"unsupported epistemic_role: {epistemic_role}")
    if extraction_method not in EXTRACTION_METHODS:
        raise ValueError(f"unsupported extraction_method: {extraction_method}")
    if extraction_confidence is not None and not (0.0 <= extraction_confidence <= 1.0):
        raise ValueError("extraction_confidence must be in [0, 1]")
    if not resource.opportunity_id or not resource.opportunity_token:
        raise ValueError("proposition mining requires tokenized Resource Opportunity")

    key = proposition_semantic_key(proposition_type, predicate, object_value)
    pid = stable_proposition_id(resource.opportunity_id, key)
    return PropositionCandidate(
        schema="humanaios.proposition-candidate.v1",
        proposition_id=pid,
        proposition_token=proposition_token(pid),
        opportunity_id=resource.opportunity_id,
        opportunity_token=resource.opportunity_token,
        proposition_type=proposition_type,
        epistemic_role=epistemic_role,
        subject=resource.opportunity_token,
        predicate=predicate,
        object_value=object_value,
        statement=statement,
        semantic_key=key,
        resolution_subject_key=resolution_subject_key(resource),
        extracted_at=resource.discovered_at or utcnow_iso(),
        extraction_method=extraction_method,
        extraction_confidence=extraction_confidence,
        evidence=list(evidence or []),
        source_url=resource.canonical_url,
        mine_id=resource.mine_id,
        mine_name=resource.mine_name,
    )


def _evidence_by_kind(resource: ResourceCandidate, kinds: set[str]) -> list[EvidenceRef]:
    return [row for row in resource.evidence if row.kind.casefold() in kinds]


def propositions_from_candidate(resource: ResourceCandidate) -> list[PropositionCandidate]:
    """Deterministically decompose one normalized opportunity into candidate propositions.

    This mines only already-normalized structure and direct observation evidence.
    It does not use open-ended language-model inference.
    """
    if not resource.opportunity_id or not resource.opportunity_token:
        return []

    out: list[PropositionCandidate] = []

    existence_evidence = list(resource.evidence)
    out.append(
        _candidate(
            resource,
            proposition_type="OPPORTUNITY_EXISTS",
            epistemic_role="OBSERVATION",
            predicate="exists",
            object_value=True,
            statement=(
                f"Resource Miner observed a bounded opportunity represented by "
                f"{resource.opportunity_token}."
            ),
            extraction_method="TOKENIZED_OPPORTUNITY",
            evidence=existence_evidence,
            extraction_confidence=1.0,
        )
    )

    current_evidence = _evidence_by_kind(
        resource,
        {"mine_observation", "repository_issue", "hackerone_scope"},
    )
    if current_evidence:
        out.append(
            _candidate(
                resource,
                proposition_type="CURRENTLY_AVAILABLE",
                epistemic_role="OBSERVATION",
                predicate="currently_available",
                object_value=True,
                statement=(
                    f"A direct current observation was recorded for "
                    f"{resource.opportunity_token}."
                ),
                extraction_method="DIRECT_OBSERVATION",
                evidence=current_evidence,
                extraction_confidence=1.0,
            )
        )

    for value in sorted(set(resource.resource_types)):
        out.append(
            _candidate(
                resource,
                proposition_type="RESOURCE_TYPE",
                epistemic_role="CLASSIFICATION",
                predicate="resource_type",
                object_value=value,
                statement=(
                    f"Resource Miner classified {resource.opportunity_token} "
                    f"as resource type '{value}'."
                ),
                extraction_method="NORMALIZER_CLASSIFICATION",
                evidence=list(resource.evidence),
                extraction_confidence=None,
            )
        )

    for value in sorted(set(resource.resource_affordances)):
        out.append(
            _candidate(
                resource,
                proposition_type="AFFORDANCE",
                epistemic_role="CLASSIFICATION",
                predicate="potential_affordance",
                object_value=value,
                statement=(
                    f"Resource Miner classified {resource.opportunity_token} "
                    f"as potentially affording '{value}'."
                ),
                extraction_method="NORMALIZER_CLASSIFICATION",
                evidence=list(resource.evidence),
                extraction_confidence=None,
            )
        )

    if resource.deadline:
        out.append(
            _candidate(
                resource,
                proposition_type="DEADLINE",
                epistemic_role="TEXT_EXTRACTION",
                predicate="represented_deadline",
                object_value=resource.deadline,
                statement=(
                    f"Resource Miner extracted represented deadline "
                    f"'{resource.deadline}' for {resource.opportunity_token}."
                ),
                extraction_method="NORMALIZER_EXTRACTION",
                evidence=list(resource.evidence),
                extraction_confidence=None,
            )
        )

    for amount in sorted(set(resource.cash_mentions_usd)):
        out.append(
            _candidate(
                resource,
                proposition_type="CASH_MENTION",
                epistemic_role="TEXT_EXTRACTION",
                predicate="source_mentions_usd",
                object_value=amount,
                statement=(
                    f"Source text associated with {resource.opportunity_token} "
                    f"contains a USD amount mention of {amount:g}; this is not "
                    "a guaranteed award value."
                ),
                extraction_method="NORMALIZER_EXTRACTION",
                evidence=list(resource.evidence),
                extraction_confidence=None,
            )
        )

    for applicant_type in sorted(set(resource.applicant_types)):
        out.append(
            _candidate(
                resource,
                proposition_type="APPLICANT_TYPE",
                epistemic_role="CLASSIFICATION",
                predicate="represented_applicant_type",
                object_value=applicant_type,
                statement=(
                    f"Resource Miner classified '{applicant_type}' as a represented "
                    f"applicant type for {resource.opportunity_token}; applicant-specific "
                    "eligibility remains unassessed."
                ),
                extraction_method="NORMALIZER_CLASSIFICATION",
                evidence=list(resource.evidence),
                extraction_confidence=None,
            )
        )

    if resource.status and resource.status != "UNKNOWN":
        out.append(
            _candidate(
                resource,
                proposition_type="STATUS",
                epistemic_role="CLASSIFICATION",
                predicate="represented_status",
                object_value=resource.status,
                statement=(
                    f"Resource Miner recorded represented status '{resource.status}' "
                    f"for {resource.opportunity_token}."
                ),
                extraction_method="NORMALIZER_CLASSIFICATION",
                evidence=list(resource.evidence),
                extraction_confidence=None,
            )
        )

    seen: set[str] = set()
    unique: list[PropositionCandidate] = []
    for row in out:
        if row.proposition_id in seen:
            continue
        seen.add(row.proposition_id)
        unique.append(row)
    return unique


def propositions_from_candidates(
    resources: Iterable[ResourceCandidate],
) -> list[PropositionCandidate]:
    out: list[PropositionCandidate] = []
    for resource in resources:
        out.extend(propositions_from_candidate(resource))
    return out


def write_propositions_jsonl(
    path: str | Path,
    propositions: Iterable[PropositionCandidate],
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "".join(
            json.dumps(row.to_dict(), ensure_ascii=False, sort_keys=True) + "\n"
            for row in propositions
        ),
        encoding="utf-8",
    )
