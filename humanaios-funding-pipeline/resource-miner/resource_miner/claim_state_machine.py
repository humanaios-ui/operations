from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from .models import EvidenceRef
from .opportunity_claim import (
    ClaimEvidence,
    ClaimFacet,
    FalsifierSpec,
    OpportunityClaim,
    add_claim_evidence,
    record_falsifier_evaluation,
)

EVENT_TYPES = {
    "CLAIM_ASSERTED",
    "EVIDENCE_RECORDED",
    "FALSIFIER_EVALUATED",
    "FACET_RESOLVED",
}
ACTOR_TYPES = {"SYSTEM", "AI", "HUMAN", "AUTHORITY", "RESOLVER"}
RESOLUTION_STATES = {"SUPPORTED", "CONTRADICTED", "FALSIFIED", "NOT_APPLICABLE"}


@dataclass
class ClaimEvaluationEvent:
    schema: str
    event_id: str
    claim_id: str
    claim_token: str
    opportunity_id: str
    proposition_id: str
    proposition_token: str
    sequence: int
    previous_event_id: str | None
    event_type: str
    observed_at: str
    actor_type: str
    actor_id: str
    method: str
    facet: str | None
    prior_overall_state: str | None
    resulting_overall_state: str
    prior_facet_state: str | None
    resulting_facet_state: str | None
    evidence_ids: list[str]
    payload: dict[str, Any]
    uncertainty: str = ""
    confidence: float | None = None
    authority_effect: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def opportunity_claim_from_dict(data: dict[str, Any]) -> OpportunityClaim:
    return OpportunityClaim(
        schema=str(data["schema"]),
        claim_id=str(data["claim_id"]),
        claim_token=str(data["claim_token"]),
        claim_type=str(data["claim_type"]),
        opportunity_id=str(data["opportunity_id"]),
        opportunity_token=str(data["opportunity_token"]),
        claim_text=str(data["claim_text"]),
        asserted_at=str(data["asserted_at"]),
        mine_id=str(data.get("mine_id") or ""),
        mine_name=str(data.get("mine_name") or ""),
        canonical_url=str(data.get("canonical_url") or ""),
        opportunity_kind=str(data.get("opportunity_kind") or ""),
        overall_state=str(data["overall_state"]),
        facets=[ClaimFacet(**row) for row in data.get("facets") or []],
        evidence=[ClaimEvidence(**row) for row in data.get("evidence") or []],
        falsifiers=[FalsifierSpec(**row) for row in data.get("falsifiers") or []],
        unknowns=list(data.get("unknowns") or []),
        constraints=list(data.get("constraints") or []),
        required_capabilities=list(data.get("required_capabilities") or []),
        required_resources=list(data.get("required_resources") or []),
        warrant_state=str(data.get("warrant_state") or "NOT_EVALUATED"),
        authorization_state=str(data.get("authorization_state") or "NOT_REQUESTED"),
        actionability_state=str(data.get("actionability_state") or "NOT_ACTIONABLE"),
        authority_effect=str(data.get("authority_effect") or "NONE"),
        proposition_id=str(data.get("proposition_id") or ""),
        proposition_token=str(data.get("proposition_token") or ""),
        proposition_type=str(data.get("proposition_type") or ""),
        proposition_semantic_key=str(data.get("proposition_semantic_key") or ""),
    )


def event_from_dict(data: dict[str, Any]) -> ClaimEvaluationEvent:
    return ClaimEvaluationEvent(
        schema=str(data["schema"]),
        event_id=str(data["event_id"]),
        claim_id=str(data["claim_id"]),
        claim_token=str(data["claim_token"]),
        opportunity_id=str(data["opportunity_id"]),
        proposition_id=str(data.get("proposition_id") or ""),
        proposition_token=str(data.get("proposition_token") or ""),
        sequence=int(data["sequence"]),
        previous_event_id=data.get("previous_event_id"),
        event_type=str(data["event_type"]),
        observed_at=str(data["observed_at"]),
        actor_type=str(data["actor_type"]),
        actor_id=str(data["actor_id"]),
        method=str(data["method"]),
        facet=data.get("facet"),
        prior_overall_state=data.get("prior_overall_state"),
        resulting_overall_state=str(data["resulting_overall_state"]),
        prior_facet_state=data.get("prior_facet_state"),
        resulting_facet_state=data.get("resulting_facet_state"),
        evidence_ids=list(data.get("evidence_ids") or []),
        payload=dict(data.get("payload") or {}),
        uncertainty=str(data.get("uncertainty") or ""),
        confidence=(
            float(data["confidence"])
            if data.get("confidence") is not None
            else None
        ),
        authority_effect=str(data.get("authority_effect") or "NONE"),
    )


def _facet_state(claim: OpportunityClaim, facet: str | None) -> str | None:
    if facet is None:
        return None
    for row in claim.facets:
        if row.name == facet:
            return row.state
    raise KeyError(f"unknown claim facet: {facet}")


def _canonical_event_body(data: dict[str, Any]) -> str:
    material = dict(data)
    material.pop("event_id", None)
    return json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_event_id(data: dict[str, Any]) -> str:
    return "CEV-" + hashlib.sha256(
        _canonical_event_body(data).encode("utf-8")
    ).hexdigest()[:20].upper()


def _finalize_event(event: ClaimEvaluationEvent) -> ClaimEvaluationEvent:
    if event.event_type not in EVENT_TYPES:
        raise ValueError(f"unsupported event_type: {event.event_type}")
    if event.actor_type not in ACTOR_TYPES:
        raise ValueError(f"unsupported actor_type: {event.actor_type}")
    if event.authority_effect != "NONE":
        raise ValueError("Claim evaluation events cannot grant authority")
    if event.confidence is not None and not (0.0 <= event.confidence <= 1.0):
        raise ValueError("confidence must be in [0, 1]")
    data = event.to_dict()
    event.event_id = stable_event_id(data)
    return event


def claim_asserted_event(
    claim: OpportunityClaim,
    *,
    actor_type: str = "SYSTEM",
    actor_id: str = "resource-miner",
    method: str = "mine_resolution",
) -> ClaimEvaluationEvent:
    event = ClaimEvaluationEvent(
        schema="humanaios.claim-evaluation-event.v1",
        event_id="",
        claim_id=claim.claim_id,
        claim_token=claim.claim_token,
        opportunity_id=claim.opportunity_id,
        proposition_id=claim.proposition_id,
        proposition_token=claim.proposition_token,
        sequence=0,
        previous_event_id=None,
        event_type="CLAIM_ASSERTED",
        observed_at=claim.asserted_at,
        actor_type=actor_type,
        actor_id=actor_id,
        method=method,
        facet=None,
        prior_overall_state=None,
        resulting_overall_state=claim.overall_state,
        prior_facet_state=None,
        resulting_facet_state=None,
        evidence_ids=[row.evidence_id for row in claim.evidence],
        payload={"claim_seed": claim.to_dict()},
    )
    return _finalize_event(event)


def _next_context(
    history: list[ClaimEvaluationEvent],
    claim: OpportunityClaim,
) -> tuple[int, str]:
    if not history:
        raise ValueError("history must include CLAIM_ASSERTED before evaluation events")
    replayed = replay_claim_events(history)
    if replayed.to_dict() != claim.to_dict():
        raise ValueError("provided claim does not equal replayed history state")
    return len(history), history[-1].event_id


def evidence_recorded_event(
    history: list[ClaimEvaluationEvent],
    claim: OpportunityClaim,
    *,
    facet: str,
    relation: str,
    evidence: EvidenceRef,
    actor_type: str,
    actor_id: str,
    method: str,
    uncertainty: str = "",
    confidence: float | None = None,
) -> tuple[ClaimEvaluationEvent, OpportunityClaim]:
    sequence, previous = _next_context(history, claim)
    facet = facet.upper()
    prior_facet = _facet_state(claim, facet)
    updated = add_claim_evidence(
        claim,
        facet=facet,
        relation=relation,
        evidence=evidence,
    )
    evidence_id = next(
        row.evidence_id
        for row in reversed(updated.evidence)
        if row.url == evidence.url
        and row.kind == evidence.kind
        and row.observed_at == evidence.observed_at
        and row.claim == evidence.claim
    )
    event = ClaimEvaluationEvent(
        schema="humanaios.claim-evaluation-event.v1",
        event_id="",
        claim_id=claim.claim_id,
        claim_token=claim.claim_token,
        opportunity_id=claim.opportunity_id,
        proposition_id=claim.proposition_id,
        proposition_token=claim.proposition_token,
        sequence=sequence,
        previous_event_id=previous,
        event_type="EVIDENCE_RECORDED",
        observed_at=evidence.observed_at,
        actor_type=actor_type,
        actor_id=actor_id,
        method=method,
        facet=facet,
        prior_overall_state=claim.overall_state,
        resulting_overall_state=updated.overall_state,
        prior_facet_state=prior_facet,
        resulting_facet_state=_facet_state(updated, facet),
        evidence_ids=[evidence_id],
        payload={
            "facet": facet,
            "relation": relation.upper(),
            "evidence": asdict(evidence),
        },
        uncertainty=uncertainty,
        confidence=confidence,
    )
    return _finalize_event(event), updated


def falsifier_evaluated_event(
    history: list[ClaimEvaluationEvent],
    claim: OpportunityClaim,
    *,
    falsifier_id: str,
    observed: bool | None,
    evidence: EvidenceRef,
    actor_type: str,
    actor_id: str,
    method: str,
    uncertainty: str = "",
    confidence: float | None = None,
) -> tuple[ClaimEvaluationEvent, OpportunityClaim]:
    sequence, previous = _next_context(history, claim)
    spec = next(
        (row for row in claim.falsifiers if row.falsifier_id == falsifier_id),
        None,
    )
    if spec is None:
        raise KeyError(f"unknown falsifier_id: {falsifier_id}")
    prior_facet = _facet_state(claim, spec.facet)
    updated = record_falsifier_evaluation(
        claim,
        falsifier_id,
        observed=observed,
        evidence=evidence,
    )
    evidence_id = next(
        row.evidence_id
        for row in reversed(updated.evidence)
        if row.url == evidence.url
        and row.kind == evidence.kind
        and row.observed_at == evidence.observed_at
        and row.claim == evidence.claim
    )
    event = ClaimEvaluationEvent(
        schema="humanaios.claim-evaluation-event.v1",
        event_id="",
        claim_id=claim.claim_id,
        claim_token=claim.claim_token,
        opportunity_id=claim.opportunity_id,
        proposition_id=claim.proposition_id,
        proposition_token=claim.proposition_token,
        sequence=sequence,
        previous_event_id=previous,
        event_type="FALSIFIER_EVALUATED",
        observed_at=evidence.observed_at,
        actor_type=actor_type,
        actor_id=actor_id,
        method=method,
        facet=spec.facet,
        prior_overall_state=claim.overall_state,
        resulting_overall_state=updated.overall_state,
        prior_facet_state=prior_facet,
        resulting_facet_state=_facet_state(updated, spec.facet),
        evidence_ids=[evidence_id],
        payload={
            "falsifier_id": falsifier_id,
            "observed": observed,
            "evidence": asdict(evidence),
        },
        uncertainty=uncertainty,
        confidence=confidence,
    )
    return _finalize_event(event), updated


def _resolved_claim(
    claim: OpportunityClaim,
    *,
    facet: str,
    state: str,
    evidence: EvidenceRef,
) -> OpportunityClaim:
    if state not in RESOLUTION_STATES:
        raise ValueError(f"unsupported resolved facet state: {state}")
    relation = {
        "SUPPORTED": "SUPPORTS",
        "CONTRADICTED": "CONTRADICTS",
        "FALSIFIED": "FALSIFIES",
        "NOT_APPLICABLE": "CONTEXT",
    }[state]
    updated = add_claim_evidence(
        claim,
        facet=facet,
        relation=relation,
        evidence=evidence,
    )
    target = next(row for row in updated.facets if row.name == facet)
    target.state = state
    # Recompute overall state using the public mutation path by adding context
    # to another copy would be wasteful; mirror the Opportunity Claim rules.
    states = {row.name: row.state for row in updated.facets}
    if states.get("EXISTENCE") == "FALSIFIED":
        updated.overall_state = "FALSIFIED"
    elif states.get("CURRENTNESS") == "FALSIFIED":
        updated.overall_state = "RETIRED"
    elif "CONTRADICTED" in states.values() or states.get("TERMS") == "FALSIFIED":
        updated.overall_state = "CONTESTED"
    elif states.get("EXISTENCE") == "SUPPORTED" and states.get("CURRENTNESS") == "SUPPORTED":
        updated.overall_state = "SUPPORTED"
    elif states.get("EXISTENCE") == "SUPPORTED":
        updated.overall_state = "OBSERVED"
    else:
        updated.overall_state = "UNVERIFIED"
    return updated


def facet_resolved_event(
    history: list[ClaimEvaluationEvent],
    claim: OpportunityClaim,
    *,
    facet: str,
    state: str,
    evidence: EvidenceRef,
    actor_type: str,
    actor_id: str,
    method: str,
    uncertainty: str = "",
    confidence: float | None = None,
) -> tuple[ClaimEvaluationEvent, OpportunityClaim]:
    sequence, previous = _next_context(history, claim)
    facet = facet.upper()
    if facet not in {row.name for row in claim.facets}:
        raise ValueError(f"unsupported facet: {facet}")
    if facet in {"ELIGIBILITY", "ATTAINABILITY"} and actor_type not in {
        "AUTHORITY",
        "RESOLVER",
        "HUMAN",
    }:
        raise ValueError(
            f"{facet} resolution requires AUTHORITY, RESOLVER, or HUMAN actor"
        )
    prior_facet = _facet_state(claim, facet)
    updated = _resolved_claim(claim, facet=facet, state=state, evidence=evidence)
    evidence_id = next(
        row.evidence_id
        for row in reversed(updated.evidence)
        if row.url == evidence.url
        and row.kind == evidence.kind
        and row.observed_at == evidence.observed_at
        and row.claim == evidence.claim
    )
    event = ClaimEvaluationEvent(
        schema="humanaios.claim-evaluation-event.v1",
        event_id="",
        claim_id=claim.claim_id,
        claim_token=claim.claim_token,
        opportunity_id=claim.opportunity_id,
        proposition_id=claim.proposition_id,
        proposition_token=claim.proposition_token,
        sequence=sequence,
        previous_event_id=previous,
        event_type="FACET_RESOLVED",
        observed_at=evidence.observed_at,
        actor_type=actor_type,
        actor_id=actor_id,
        method=method,
        facet=facet,
        prior_overall_state=claim.overall_state,
        resulting_overall_state=updated.overall_state,
        prior_facet_state=prior_facet,
        resulting_facet_state=state,
        evidence_ids=[evidence_id],
        payload={
            "facet": facet,
            "state": state,
            "evidence": asdict(evidence),
        },
        uncertainty=uncertainty,
        confidence=confidence,
    )
    return _finalize_event(event), updated


def _validate_event_integrity(event: ClaimEvaluationEvent) -> None:
    if event.event_type not in EVENT_TYPES:
        raise ValueError(f"unsupported event_type: {event.event_type}")
    if event.actor_type not in ACTOR_TYPES:
        raise ValueError(f"unsupported actor_type: {event.actor_type}")
    if event.confidence is not None and not (0.0 <= event.confidence <= 1.0):
        raise ValueError("confidence must be in [0, 1]")
    expected = stable_event_id(event.to_dict())
    if expected != event.event_id:
        raise ValueError(
            f"event integrity mismatch: expected {expected}, got {event.event_id}"
        )
    if event.authority_effect != "NONE":
        raise ValueError("claim evaluation event cannot grant authority")


def replay_claim_events(
    events: Iterable[ClaimEvaluationEvent | dict[str, Any]],
) -> OpportunityClaim:
    rows = [
        event if isinstance(event, ClaimEvaluationEvent) else event_from_dict(event)
        for event in events
    ]
    if not rows:
        raise ValueError("claim replay requires at least one event")

    first = rows[0]
    _validate_event_integrity(first)
    if first.event_type != "CLAIM_ASSERTED" or first.sequence != 0:
        raise ValueError("first event must be CLAIM_ASSERTED sequence 0")
    if first.previous_event_id is not None:
        raise ValueError("CLAIM_ASSERTED must not have previous_event_id")
    seed = first.payload.get("claim_seed")
    if not isinstance(seed, dict):
        raise ValueError("CLAIM_ASSERTED event missing claim_seed")
    claim = opportunity_claim_from_dict(seed)
    if claim.claim_id != first.claim_id or claim.opportunity_id != first.opportunity_id:
        raise ValueError("CLAIM_ASSERTED identity mismatch")
    if claim.proposition_id != first.proposition_id:
        raise ValueError("CLAIM_ASSERTED proposition_id mismatch")
    if claim.proposition_token != first.proposition_token:
        raise ValueError("CLAIM_ASSERTED proposition_token mismatch")
    if claim.overall_state != first.resulting_overall_state:
        raise ValueError("CLAIM_ASSERTED resulting state mismatch")

    previous = first
    for expected_sequence, event in enumerate(rows[1:], start=1):
        _validate_event_integrity(event)
        if event.claim_id != claim.claim_id:
            raise ValueError("event claim_id mismatch")
        if event.opportunity_id != claim.opportunity_id:
            raise ValueError("event opportunity_id mismatch")
        if event.proposition_id != claim.proposition_id:
            raise ValueError("event proposition_id mismatch")
        if event.proposition_token != claim.proposition_token:
            raise ValueError("event proposition_token mismatch")
        if event.sequence != expected_sequence:
            raise ValueError("event sequence is not contiguous")
        if event.previous_event_id != previous.event_id:
            raise ValueError("event chain previous_event_id mismatch")
        if event.prior_overall_state != claim.overall_state:
            raise ValueError("event prior_overall_state does not match replay")
        if event.facet and event.prior_facet_state != _facet_state(claim, event.facet):
            raise ValueError("event prior_facet_state does not match replay")

        payload = event.payload
        if event.event_type == "EVIDENCE_RECORDED":
            claim = add_claim_evidence(
                claim,
                facet=str(payload["facet"]),
                relation=str(payload["relation"]),
                evidence=EvidenceRef(**payload["evidence"]),
            )
        elif event.event_type == "FALSIFIER_EVALUATED":
            claim = record_falsifier_evaluation(
                claim,
                str(payload["falsifier_id"]),
                observed=payload.get("observed"),
                evidence=EvidenceRef(**payload["evidence"]),
            )
        elif event.event_type == "FACET_RESOLVED":
            claim = _resolved_claim(
                claim,
                facet=str(payload["facet"]),
                state=str(payload["state"]),
                evidence=EvidenceRef(**payload["evidence"]),
            )
        else:
            raise ValueError(f"unexpected replay event type: {event.event_type}")

        if claim.overall_state != event.resulting_overall_state:
            raise ValueError("event resulting_overall_state does not match replay")
        if event.facet and event.resulting_facet_state != _facet_state(claim, event.facet):
            raise ValueError("event resulting_facet_state does not match replay")
        previous = event

    return claim


def load_event_jsonl(path: str | Path) -> list[ClaimEvaluationEvent]:
    target = Path(path)
    if not target.exists():
        return []
    out: list[ClaimEvaluationEvent] = []
    for line in target.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(event_from_dict(json.loads(line)))
    return out


def write_event_jsonl(
    path: str | Path,
    events: Iterable[ClaimEvaluationEvent],
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "".join(
            json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True) + "\n"
            for event in events
        ),
        encoding="utf-8",
    )


def reconcile_claim_event_ledger(
    path: str | Path,
    claims: Iterable[OpportunityClaim],
    *,
    actor_id: str = "resource-miner",
    method: str = "mine_resolution",
) -> list[ClaimEvaluationEvent]:
    existing = load_event_jsonl(path)
    by_claim: dict[str, list[ClaimEvaluationEvent]] = {}
    for event in existing:
        by_claim.setdefault(event.claim_id, []).append(event)
    for history in by_claim.values():
        history.sort(key=lambda row: row.sequence)
        replay_claim_events(history)

    appended: list[ClaimEvaluationEvent] = []
    for observed_claim in claims:
        history = by_claim.get(observed_claim.claim_id, [])
        if not history:
            event = claim_asserted_event(
                observed_claim,
                actor_type="SYSTEM",
                actor_id=actor_id,
                method=method,
            )
            existing.append(event)
            by_claim[observed_claim.claim_id] = [event]
            appended.append(event)
            continue

        current = replay_claim_events(history)
        known_evidence = {row.evidence_id for row in current.evidence}
        for item in observed_claim.evidence:
            if item.evidence_id in known_evidence:
                continue
            event, current = evidence_recorded_event(
                history,
                current,
                facet=item.facet,
                relation=item.relation,
                evidence=EvidenceRef(
                    url=item.url,
                    kind=item.kind,
                    observed_at=item.observed_at,
                    claim=item.claim,
                ),
                actor_type="SYSTEM",
                actor_id=actor_id,
                method=method,
            )
            history.append(event)
            existing.append(event)
            appended.append(event)
            known_evidence.add(item.evidence_id)

    if appended:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as handle:
            for event in appended:
                handle.write(
                    json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True)
                    + "\n"
                )
    return appended
