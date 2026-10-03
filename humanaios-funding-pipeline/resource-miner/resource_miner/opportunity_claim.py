from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .models import EvidenceRef, ResourceCandidate
from .normalize import utcnow_iso
from .proposition import PropositionCandidate, propositions_from_candidate

FACETS = {"EXISTENCE", "CURRENTNESS", "TERMS", "ELIGIBILITY", "ATTAINABILITY"}
FACET_STATES = {
    "UNKNOWN",
    "UNASSESSED",
    "SUPPORTED",
    "CONTRADICTED",
    "FALSIFIED",
    "NOT_APPLICABLE",
}
EVIDENCE_RELATIONS = {"SUPPORTS", "CONTRADICTS", "FALSIFIES", "CONTEXT"}
FALSIFIER_STATES = {"UNTESTED", "NOT_OBSERVED", "OBSERVED", "INCONCLUSIVE"}
WARRANT_STATES = {"NOT_EVALUATED", "INSUFFICIENT", "SUPPORTED", "REJECTED"}
AUTHORIZATION_STATES = {"NOT_REQUESTED", "PENDING", "AUTHORIZED", "DENIED"}
ACTIONABILITY_STATES = {"NOT_ACTIONABLE", "VERIFY", "READY_FOR_AUTHORIZATION", "AUTHORIZED"}


@dataclass
class ClaimFacet:
    name: str
    state: str
    statement: str
    evidence_ids: list[str] = field(default_factory=list)
    updated_at: str | None = None


@dataclass
class ClaimEvidence:
    evidence_id: str
    relation: str
    facet: str
    url: str
    kind: str
    observed_at: str
    claim: str = ""


@dataclass
class FalsifierSpec:
    falsifier_id: str
    facet: str
    condition: str
    observation_surface: str
    effect: str = "FALSIFY_FACET"
    state: str = "UNTESTED"
    evidence_ids: list[str] = field(default_factory=list)
    evaluated_at: str | None = None


@dataclass
class OpportunityClaim:
    schema: str
    claim_id: str
    claim_token: str
    claim_type: str
    opportunity_id: str
    opportunity_token: str
    claim_text: str
    asserted_at: str
    mine_id: str
    mine_name: str
    canonical_url: str
    opportunity_kind: str
    overall_state: str
    facets: list[ClaimFacet]
    evidence: list[ClaimEvidence]
    falsifiers: list[FalsifierSpec]
    unknowns: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    required_capabilities: list[str] = field(default_factory=list)
    required_resources: list[str] = field(default_factory=list)
    warrant_state: str = "NOT_EVALUATED"
    authorization_state: str = "NOT_REQUESTED"
    actionability_state: str = "NOT_ACTIONABLE"
    authority_effect: str = "NONE"
    proposition_id: str = ""
    proposition_token: str = ""
    proposition_type: str = ""
    proposition_semantic_key: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def stable_claim_id(
    opportunity_id: str,
    claim_type: str = "RESOURCE_OPPORTUNITY",
    proposition_id: str | None = None,
) -> str:
    opportunity_id = opportunity_id.strip().upper()
    if not opportunity_id:
        raise ValueError("opportunity_id is required")
    parts = [opportunity_id, claim_type.strip().upper()]
    if proposition_id:
        parts.append(proposition_id.strip().upper())
    payload = "\0".join(parts)
    return "CLM-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16].upper()


def claim_token(claim_id: str) -> str:
    return f"urn:humanaios:opportunity-claim:{claim_id}"


def stable_evidence_id(evidence: EvidenceRef | ClaimEvidence) -> str:
    payload = "\0".join(
        [
            str(evidence.url).strip(),
            str(evidence.kind).strip(),
            str(evidence.observed_at).strip(),
            str(evidence.claim).strip(),
        ]
    )
    return "EVD-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16].upper()


def stable_falsifier_id(claim_id: str, facet: str, condition: str) -> str:
    payload = "\0".join(
        [claim_id.strip().upper(), facet.strip().upper(), " ".join(condition.split())]
    )
    return "FAL-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16].upper()


def _facet_map(claim: OpportunityClaim) -> dict[str, ClaimFacet]:
    return {facet.name: facet for facet in claim.facets}


def derive_overall_state(
    facets: list[ClaimFacet],
    proposition_type: str = "",
) -> str:
    states = {facet.name: facet.state for facet in facets}
    if states.get("EXISTENCE") == "FALSIFIED":
        return "FALSIFIED"
    if states.get("CURRENTNESS") == "FALSIFIED":
        return "RETIRED"
    if "CONTRADICTED" in states.values() or states.get("TERMS") == "FALSIFIED":
        return "CONTESTED"

    if proposition_type == "OPPORTUNITY_EXISTS":
        return (
            "SUPPORTED"
            if states.get("EXISTENCE") == "SUPPORTED"
            else "UNVERIFIED"
        )

    if proposition_type == "CURRENTLY_AVAILABLE":
        if states.get("CURRENTNESS") == "SUPPORTED":
            return "SUPPORTED"
        if states.get("EXISTENCE") == "SUPPORTED":
            return "OBSERVED"
        return "UNVERIFIED"

    if proposition_type:
        if states.get("TERMS") == "SUPPORTED":
            return "SUPPORTED"
        if (
            states.get("EXISTENCE") == "SUPPORTED"
            or states.get("CURRENTNESS") == "SUPPORTED"
        ):
            return "OBSERVED"
        return "UNVERIFIED"

    if (
        states.get("EXISTENCE") == "SUPPORTED"
        and states.get("CURRENTNESS") == "SUPPORTED"
    ):
        return "SUPPORTED"
    if states.get("EXISTENCE") == "SUPPORTED":
        return "OBSERVED"
    return "UNVERIFIED"


def _evidence_facet(item: EvidenceRef) -> tuple[str, str]:
    kind = item.kind.casefold()
    if kind == "mine_observation":
        return "CURRENTNESS", "SUPPORTS"
    if kind == "mine_observation_failed":
        return "CURRENTNESS", "CONTEXT"
    if kind in {"repository_issue", "hackerone_scope"}:
        return "CURRENTNESS", "SUPPORTS"
    if kind == "discovery":
        return "EXISTENCE", "SUPPORTS"
    return "EXISTENCE", "SUPPORTS"


def _default_falsifiers(
    claim_id: str,
    *,
    canonical_url: str,
    opportunity_kind: str,
) -> list[FalsifierSpec]:
    specs = [
        (
            "EXISTENCE",
            "Authoritative source establishes that the represented opportunity does not exist or was a mistaken identity.",
        ),
        (
            "CURRENTNESS",
            "Authoritative source establishes that the opportunity is closed, withdrawn, expired, paused, or no longer offered.",
        ),
        (
            "TERMS",
            "Authoritative source materially contradicts represented value, scope, deadline, restrictions, or acquisition terms.",
        ),
        (
            "ELIGIBILITY",
            "Authoritative eligibility predicates establish that the evaluated applicant does not satisfy a required condition.",
        ),
        (
            "ATTAINABILITY",
            "Required acquisition path is unavailable to the evaluated actor under the verified constraints and capabilities.",
        ),
    ]
    surface = canonical_url or f"opportunity:{opportunity_kind}"
    return [
        FalsifierSpec(
            falsifier_id=stable_falsifier_id(claim_id, facet, condition),
            facet=facet,
            condition=condition,
            observation_surface=surface,
        )
        for facet, condition in specs
    ]


def build_opportunity_claim(
    candidate: ResourceCandidate,
    proposition: PropositionCandidate | None = None,
) -> OpportunityClaim:
    if not candidate.opportunity_id:
        raise ValueError("Opportunity Claim requires a tokenized opportunity_id")
    if not candidate.opportunity_token:
        raise ValueError("Opportunity Claim requires opportunity_token")

    asserted_at = candidate.discovered_at or utcnow_iso()
    if proposition is not None:
        if proposition.opportunity_id != candidate.opportunity_id:
            raise ValueError("proposition must reference candidate opportunity_id")
        if proposition.opportunity_token != candidate.opportunity_token:
            raise ValueError("proposition must reference candidate opportunity_token")
    claim_type = (
        "OPPORTUNITY_PROPOSITION"
        if proposition is not None
        else "RESOURCE_OPPORTUNITY"
    )
    claim_id = stable_claim_id(
        candidate.opportunity_id,
        claim_type=claim_type,
        proposition_id=(proposition.proposition_id if proposition else None),
    )

    evidence: list[ClaimEvidence] = []
    evidence_by_facet: dict[str, list[str]] = {facet: [] for facet in FACETS}
    has_current_observation = False
    has_current_failure = False

    for item in candidate.evidence:
        facet, relation = _evidence_facet(item)
        evidence_id = stable_evidence_id(item)
        evidence.append(
            ClaimEvidence(
                evidence_id=evidence_id,
                relation=relation,
                facet=facet,
                url=item.url,
                kind=item.kind,
                observed_at=item.observed_at,
                claim=item.claim,
            )
        )
        evidence_by_facet[facet].append(evidence_id)
        if item.kind.casefold() in {"mine_observation", "repository_issue", "hackerone_scope"}:
            has_current_observation = True
        elif item.kind.casefold() == "mine_observation_failed":
            has_current_failure = True

    existence_state = "SUPPORTED" if candidate.evidence else "UNKNOWN"
    currentness_state = "SUPPORTED" if has_current_observation else "UNKNOWN"
    if has_current_failure and not has_current_observation:
        currentness_state = "UNKNOWN"

    material_terms_present = any(
        [
            bool(candidate.description),
            bool(candidate.value_text),
            bool(candidate.deadline),
            bool(candidate.status and candidate.status != "UNKNOWN"),
            bool(candidate.resource_types),
        ]
    )
    terms_state = "UNKNOWN"
    if proposition is not None:
        if proposition.proposition_type == "OPPORTUNITY_EXISTS":
            existence_state = "SUPPORTED" if proposition.evidence else existence_state
        elif proposition.proposition_type == "CURRENTLY_AVAILABLE":
            currentness_state = "SUPPORTED" if proposition.evidence else currentness_state
        else:
            # Extraction/classification creates a testable proposition, not truth.
            terms_state = "UNKNOWN"
    else:
        terms_state = (
            "SUPPORTED"
            if material_terms_present and existence_state == "SUPPORTED"
            else "UNKNOWN"
        )

    facets = [
        ClaimFacet(
            name="EXISTENCE",
            state=existence_state,
            statement="The bounded Resource Opportunity represented by this token exists as observed.",
            evidence_ids=evidence_by_facet["EXISTENCE"],
            updated_at=asserted_at,
        ),
        ClaimFacet(
            name="CURRENTNESS",
            state=currentness_state,
            statement="The opportunity is currently offered under an authoritative or direct source observation.",
            evidence_ids=evidence_by_facet["CURRENTNESS"],
            updated_at=asserted_at,
        ),
        ClaimFacet(
            name="TERMS",
            state=terms_state,
            statement="Material terms represented on the candidate are consistent with observed source evidence.",
            updated_at=asserted_at,
        ),
        ClaimFacet(
            name="ELIGIBILITY",
            state="UNASSESSED",
            statement="Applicant-specific eligibility has not been established by Resource Miner.",
            updated_at=asserted_at,
        ),
        ClaimFacet(
            name="ATTAINABILITY",
            state="UNASSESSED",
            statement="Actor-specific ability to acquire this opportunity has not been established.",
            updated_at=asserted_at,
        ),
    ]

    unknowns = ["applicant_eligibility", "actor_attainability"]
    if currentness_state == "UNKNOWN":
        unknowns.append("currentness")
    if terms_state == "UNKNOWN":
        unknowns.append("material_terms")

    claim = OpportunityClaim(
        schema="humanaios.opportunity-claim.v1",
        claim_id=claim_id,
        claim_token=claim_token(claim_id),
        claim_type=claim_type,
        opportunity_id=candidate.opportunity_id,
        opportunity_token=candidate.opportunity_token,
        claim_text=(
            proposition.statement
            if proposition is not None
            else (
                f"A bounded resource opportunity '{candidate.title}' is represented by "
                f"{candidate.opportunity_token}; discovery does not establish applicant "
                "eligibility, attainability, warrant, or authorization."
            )
        ),
        asserted_at=asserted_at,
        mine_id=candidate.mine_id,
        mine_name=candidate.mine_name,
        canonical_url=candidate.canonical_url,
        opportunity_kind=candidate.opportunity_kind,
        overall_state="UNVERIFIED",
        facets=facets,
        evidence=evidence,
        falsifiers=_default_falsifiers(
            claim_id,
            canonical_url=candidate.canonical_url,
            opportunity_kind=candidate.opportunity_kind,
        ),
        unknowns=(
            unknowns + (
                ["proposition_truth"]
                if proposition is not None
                and proposition.proposition_type
                not in {"OPPORTUNITY_EXISTS", "CURRENTLY_AVAILABLE"}
                else []
            )
        ),
        proposition_id=(proposition.proposition_id if proposition else ""),
        proposition_token=(proposition.proposition_token if proposition else ""),
        proposition_type=(proposition.proposition_type if proposition else ""),
        proposition_semantic_key=(proposition.semantic_key if proposition else ""),
    )
    claim.overall_state = derive_overall_state(
        claim.facets,
        claim.proposition_type,
    )
    return claim


def record_falsifier_evaluation(
    claim: OpportunityClaim,
    falsifier_id: str,
    *,
    observed: bool | None,
    evidence: EvidenceRef,
    evaluated_at: str | None = None,
) -> OpportunityClaim:
    if not evidence.url or not evidence.observed_at:
        raise ValueError("falsifier evaluation requires provenance-bearing evidence")

    updated = copy.deepcopy(claim)
    spec = next(
        (item for item in updated.falsifiers if item.falsifier_id == falsifier_id),
        None,
    )
    if spec is None:
        raise KeyError(f"unknown falsifier_id: {falsifier_id}")

    evidence_id = stable_evidence_id(evidence)
    relation = "FALSIFIES" if observed is True else "CONTEXT"
    updated.evidence.append(
        ClaimEvidence(
            evidence_id=evidence_id,
            relation=relation,
            facet=spec.facet,
            url=evidence.url,
            kind=evidence.kind,
            observed_at=evidence.observed_at,
            claim=evidence.claim,
        )
    )
    spec.evidence_ids.append(evidence_id)
    spec.evaluated_at = evaluated_at or evidence.observed_at

    facets = _facet_map(updated)
    facet = facets[spec.facet]
    facet.evidence_ids.append(evidence_id)
    facet.updated_at = spec.evaluated_at

    if observed is True:
        spec.state = "OBSERVED"
        facet.state = "FALSIFIED"
    elif observed is False:
        spec.state = "NOT_OBSERVED"
    else:
        spec.state = "INCONCLUSIVE"

    updated.overall_state = derive_overall_state(updated.facets, updated.proposition_type)
    return updated


def add_claim_evidence(
    claim: OpportunityClaim,
    *,
    facet: str,
    relation: str,
    evidence: EvidenceRef,
) -> OpportunityClaim:
    facet = facet.upper()
    relation = relation.upper()
    if facet not in FACETS:
        raise ValueError(f"unsupported facet: {facet}")
    if relation not in EVIDENCE_RELATIONS:
        raise ValueError(f"unsupported evidence relation: {relation}")
    if not evidence.url or not evidence.observed_at:
        raise ValueError("claim evidence requires provenance")

    updated = copy.deepcopy(claim)
    evidence_id = stable_evidence_id(evidence)
    updated.evidence.append(
        ClaimEvidence(
            evidence_id=evidence_id,
            relation=relation,
            facet=facet,
            url=evidence.url,
            kind=evidence.kind,
            observed_at=evidence.observed_at,
            claim=evidence.claim,
        )
    )
    target = _facet_map(updated)[facet]
    target.evidence_ids.append(evidence_id)
    target.updated_at = evidence.observed_at

    # Resource Miner may record evidence about eligibility without self-promoting
    # the applicant to eligible. Only a downstream eligibility resolver may do so.
    if relation == "CONTRADICTS":
        target.state = "CONTRADICTED"
    elif relation == "FALSIFIES":
        target.state = "FALSIFIED"
    elif relation == "SUPPORTS" and facet not in {"ELIGIBILITY", "ATTAINABILITY"}:
        target.state = "SUPPORTED"

    updated.overall_state = derive_overall_state(updated.facets, updated.proposition_type)
    return updated


def claims_from_propositions(
    candidates: Iterable[ResourceCandidate],
    propositions: Iterable[PropositionCandidate],
) -> list[OpportunityClaim]:
    by_opportunity = {
        candidate.opportunity_id: candidate
        for candidate in candidates
        if candidate.opportunity_id
    }
    claims: list[OpportunityClaim] = []
    for proposition in propositions:
        candidate = by_opportunity.get(proposition.opportunity_id)
        if candidate is None:
            raise ValueError(
                f"proposition references unknown opportunity_id: {proposition.opportunity_id}"
            )
        claims.append(build_opportunity_claim(candidate, proposition))
    return claims


def claims_from_candidates(
    candidates: Iterable[ResourceCandidate],
) -> list[OpportunityClaim]:
    rows = list(candidates)
    propositions: list[PropositionCandidate] = []
    fallback: list[ResourceCandidate] = []
    for candidate in rows:
        mined = propositions_from_candidate(candidate)
        if mined:
            propositions.extend(mined)
        else:
            fallback.append(candidate)
    claims = claims_from_propositions(rows, propositions)
    claims.extend(build_opportunity_claim(candidate) for candidate in fallback)
    return claims


def write_claims_jsonl(
    path: str | Path,
    claims: Iterable[OpportunityClaim],
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "".join(
            json.dumps(claim.to_dict(), ensure_ascii=False, sort_keys=True) + "\n"
            for claim in claims
        ),
        encoding="utf-8",
    )
