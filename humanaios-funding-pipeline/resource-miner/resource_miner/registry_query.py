from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from .mines import stable_opportunity_id
from .models import ResourceMine

SUBJECT_REF_RE = re.compile(r"^SUBJ-[A-F0-9]{16}$")
QUERY_CLASSES = {"UNCLAIMED_PROPERTY_OWNER_SEARCH"}
SUBJECT_KINDS = {"NATURAL_PERSON", "ORGANIZATION", "UNKNOWN"}


@dataclass(frozen=True)
class RegistryQueryPlan:
    schema: str
    query_id: str
    query_token: str
    registry_mine_id: str
    pathway_opportunity_id: str
    query_class: str
    subject_ref: str
    subject_kind: str
    query_fields: list[str]
    privacy_classification: str
    query_value_persistence: str
    purpose: str
    expected_response_class: str
    zero_result_semantics: str
    match_result_semantics: str
    explicit_subject_request: bool
    external_state_change: bool
    planning_state: str = "PLANNED"
    execution_state: str = "NOT_AUTHORIZED"
    authority_effect: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def stable_registry_query_id(
    *,
    registry_mine_id: str,
    pathway_opportunity_id: str,
    query_class: str,
    subject_ref: str,
    subject_kind: str,
    query_fields: Iterable[str],
    purpose: str,
) -> str:
    payload = "\0".join(
        [
            registry_mine_id.strip().upper(),
            pathway_opportunity_id.strip().upper(),
            query_class.strip().upper(),
            subject_ref.strip().upper(),
            subject_kind.strip().upper(),
            ",".join(sorted({str(x).strip().casefold() for x in query_fields})),
            purpose.strip().upper(),
        ]
    )
    return "RQY-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16].upper()


def registry_query_token(query_id: str) -> str:
    return f"urn:humanaios:registry-query:{query_id}"


def _registered_pathway_ids(mine: ResourceMine) -> set[str]:
    ids: set[str] = set()
    for row in mine.config.get("opportunities") or []:
        if not isinstance(row, dict):
            continue
        identity = str(row.get("opportunity_identity") or row.get("url") or "").strip()
        kind = str(row.get("opportunity_kind") or "configured_opportunity").strip()
        if identity:
            ids.add(stable_opportunity_id(mine.mine_id, identity, kind))
    return ids


def _query_contract(mine: ResourceMine) -> dict[str, Any]:
    contract = mine.config.get("query_contract") or {}
    if not isinstance(contract, dict) or not contract.get("queryable"):
        raise ValueError("registry Mine does not declare a queryable contract")
    return contract


def plan_registry_query(
    *,
    mine: ResourceMine,
    pathway_opportunity_id: str,
    subject_ref: str,
    subject_kind: str,
    query_fields: Iterable[str],
    explicit_subject_request: bool,
    purpose: str = "DISCOVER_CANDIDATE_UNCLAIMED_PROPERTY_RECORDS",
) -> RegistryQueryPlan:
    if mine.mine_kind != "REGISTRY":
        raise ValueError("subject-scoped registry query requires REGISTRY Mine")
    if not mine.enabled:
        raise ValueError("registry Mine must be enabled")
    if not explicit_subject_request:
        raise PermissionError("explicit claimant/subject request is required")
    if not SUBJECT_REF_RE.fullmatch(subject_ref.strip().upper()):
        raise ValueError("subject_ref must be a privacy-safe SUBJ-* token")
    subject_kind = subject_kind.strip().upper()
    if subject_kind not in SUBJECT_KINDS:
        raise ValueError(f"unsupported subject_kind: {subject_kind}")

    pathway_opportunity_id = pathway_opportunity_id.strip().upper()
    if not re.fullmatch(r"OPP-[A-F0-9]{16}", pathway_opportunity_id):
        raise ValueError("pathway_opportunity_id must be an OPP-* token")
    registered_pathways = _registered_pathway_ids(mine)
    if registered_pathways and pathway_opportunity_id not in registered_pathways:
        raise ValueError("pathway opportunity is not registered under this Mine")

    contract = _query_contract(mine)
    query_class = str(contract.get("query_class") or "").strip().upper()
    if query_class not in QUERY_CLASSES:
        raise ValueError(f"unsupported query_class: {query_class}")

    requested = sorted(
        {str(x).strip().casefold() for x in query_fields if str(x).strip()}
    )
    if not requested:
        raise ValueError("at least one semantic query field is required")
    allowed = {
        str(x).strip().casefold()
        for x in contract.get("semantic_query_fields") or []
        if str(x).strip()
    }
    unknown = [field for field in requested if field not in allowed]
    if unknown:
        raise ValueError(f"query fields outside Mine contract: {unknown}")

    if str(contract.get("query_value_persistence") or "").upper() != "PRIVATE_RUNTIME_ONLY":
        raise ValueError("registry query values must remain PRIVATE_RUNTIME_ONLY")
    if bool(contract.get("external_state_change", True)):
        raise ValueError("registry query planning requires external_state_change=false")
    if str(contract.get("authority_effect") or "").upper() != "NONE":
        raise ValueError("registry query contract cannot grant authority")

    query_id = stable_registry_query_id(
        registry_mine_id=mine.mine_id,
        pathway_opportunity_id=pathway_opportunity_id,
        query_class=query_class,
        subject_ref=subject_ref,
        subject_kind=subject_kind,
        query_fields=requested,
        purpose=purpose,
    )

    return RegistryQueryPlan(
        schema="humanaios.registry-query-plan.v1",
        query_id=query_id,
        query_token=registry_query_token(query_id),
        registry_mine_id=mine.mine_id,
        pathway_opportunity_id=pathway_opportunity_id,
        query_class=query_class,
        subject_ref=subject_ref.strip().upper(),
        subject_kind=subject_kind,
        query_fields=requested,
        privacy_classification="SENSITIVE_QUERY_INPUT",
        query_value_persistence="PRIVATE_RUNTIME_ONLY",
        purpose=purpose.strip().upper(),
        expected_response_class=str(
            contract.get("expected_response_class")
            or "ZERO_OR_MORE_CANDIDATE_RECORDS"
        ).strip().upper(),
        zero_result_semantics=str(
            contract.get("zero_result_semantics")
            or "NO_MATCH_OBSERVED_NOT_NO_ENTITLEMENT"
        ).strip().upper(),
        match_result_semantics=str(
            contract.get("match_result_semantics")
            or "CANDIDATE_RECORD_NOT_OWNERSHIP"
        ).strip().upper(),
        explicit_subject_request=True,
        external_state_change=False,
    )



def registry_query_from_dict(data: dict[str, Any]) -> RegistryQueryPlan:
    expected = {
        "schema",
        "query_id",
        "query_token",
        "registry_mine_id",
        "pathway_opportunity_id",
        "query_class",
        "subject_ref",
        "subject_kind",
        "query_fields",
        "privacy_classification",
        "query_value_persistence",
        "purpose",
        "expected_response_class",
        "zero_result_semantics",
        "match_result_semantics",
        "explicit_subject_request",
        "external_state_change",
        "planning_state",
        "execution_state",
        "authority_effect",
    }
    keys = set(data)
    if keys != expected:
        missing = sorted(expected - keys)
        extra = sorted(keys - expected)
        raise ValueError(f"registry query plan shape mismatch; missing={missing}; extra={extra}")
    return RegistryQueryPlan(**data)


def write_registry_query_plans_jsonl(
    path: str | Path,
    plans: Iterable[RegistryQueryPlan],
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "".join(
            json.dumps(row.to_dict(), ensure_ascii=False, sort_keys=True) + "\n"
            for row in sorted(plans, key=lambda row: row.query_id)
        ),
        encoding="utf-8",
    )
