from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from .adjudication import PropositionAdjudication, VerificationFrontierItem

OPERATION_BY_GAP = {
    "PRIMARY_SOURCE_MISSING": "DISCOVER_PRIMARY_SOURCE",
    "DIRECT_EVIDENCE_MISSING": "SEEK_DIRECT_EVIDENCE",
    "CONFLICT_REQUIRES_RESOLUTION": "RESOLVE_CONFLICT",
    "SOURCE_STANDING_UNKNOWN": "ASSESS_SOURCE_STANDING",
    "RELATION_UNRESOLVED": "DISAMBIGUATE_RELATION",
}
CLOSURE_BY_GAP = {
    "PRIMARY_SOURCE_MISSING": "Applicable primary-source standing is present for the proposition.",
    "DIRECT_EVIDENCE_MISSING": "A direct observation or explicit source assertion supports the predicate.",
    "CONFLICT_REQUIRES_RESOLUTION": "Conflict is resolved by new evidence or an explicit resolver decision without deleting history.",
    "SOURCE_STANDING_UNKNOWN": "The evidence origin has a scoped standing profile for this proposition.",
    "RELATION_UNRESOLVED": "Scope, time, or semantic evidence makes the proposition relationship safely inferable.",
}


@dataclass(frozen=True)
class VerificationWorkItem:
    schema: str
    work_id: str
    verification_id: str
    adjudication_id: str
    resolution_set_id: str
    subject_key: str
    operation_class: str
    requested_source_class: str
    candidate_origin_keys: list[str]
    closure_condition: str
    planning_state: str = "PLANNED"
    execution_state: str = "NOT_AUTHORIZED"
    authority_effect: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def stable_work_id(verification_id: str, operation_class: str) -> str:
    payload = "\0".join(
        [verification_id.strip().upper(), operation_class.strip().upper()]
    )
    return "VWK-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16].upper()


def _work_item(
    adjudication: PropositionAdjudication,
    verification: VerificationFrontierItem,
) -> VerificationWorkItem:
    operation = OPERATION_BY_GAP[verification.gap_type]
    if verification.gap_type == "PRIMARY_SOURCE_MISSING":
        candidate_origins: list[str] = []
    elif verification.gap_type == "DIRECT_EVIDENCE_MISSING":
        candidate_origins = sorted(
            set(adjudication.primary_origin_keys or adjudication.known_origin_keys)
        )
    elif verification.gap_type == "SOURCE_STANDING_UNKNOWN":
        candidate_origins = sorted(set(adjudication.unknown_origin_keys))
    else:
        candidate_origins = sorted(
            set(
                adjudication.primary_origin_keys
                + adjudication.known_origin_keys
                + adjudication.unknown_origin_keys
            )
        )
    return VerificationWorkItem(
        schema="humanaios.verification-work-item.v1",
        work_id=stable_work_id(verification.verification_id, operation),
        verification_id=verification.verification_id,
        adjudication_id=adjudication.adjudication_id,
        resolution_set_id=adjudication.resolution_set_id,
        subject_key=verification.subject_key,
        operation_class=operation,
        requested_source_class=verification.requested_source_class,
        candidate_origin_keys=candidate_origins,
        closure_condition=CLOSURE_BY_GAP[verification.gap_type],
    )


def compile_verification_work_queue(
    adjudications: Iterable[PropositionAdjudication],
) -> list[VerificationWorkItem]:
    output: dict[str, VerificationWorkItem] = {}
    for adjudication in adjudications:
        for verification in adjudication.verification_frontier:
            if verification.state != "OPEN":
                continue
            item = _work_item(adjudication, verification)
            output[item.work_id] = item
    return [output[key] for key in sorted(output)]


def write_verification_work_queue_jsonl(
    path: str | Path,
    work_items: Iterable[VerificationWorkItem],
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "".join(
            json.dumps(row.to_dict(), ensure_ascii=False, sort_keys=True) + "\n"
            for row in sorted(work_items, key=lambda row: row.work_id)
        ),
        encoding="utf-8",
    )
