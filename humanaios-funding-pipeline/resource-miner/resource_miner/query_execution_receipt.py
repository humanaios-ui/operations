from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from .observation_authorization import (
    OBSERVATION_OPERATION,
    POLICY_ID,
    POLICY_VERSION,
    ObservationAuthorizationDecision,
    authorization_covers_query,
    authorization_token,
    stable_authorization_id,
)
from .registry_query import RegistryQueryPlan

RESULT_STATES = {
    "ZERO_MATCHES_OBSERVED",
    "MATCHES_OBSERVED",
    "OBSERVATION_FAILED",
}
PSB_RE = re.compile(r"^PSB-[A-F0-9]{16}$")
EXE_RE = re.compile(r"^EXE-[A-F0-9]{16}$")


@dataclass(frozen=True)
class QueryExecutionReceipt:
    schema: str
    receipt_id: str
    receipt_token: str
    authorization_id: str
    authorization_token: str
    authorization_decision_sha256: str
    query_id: str
    query_token: str
    query_plan_sha256: str
    policy_receipt_sha256: str
    registry_mine_id: str
    pathway_opportunity_id: str
    subject_ref: str
    private_subject_binding_attestation_id: str
    private_subject_binding_attested: bool
    executed_operation: str
    executed_query_fields: list[str]
    observed_origin_key: str
    execution_nonce: str
    started_at: str
    finished_at: str
    result_state: str
    observed_record_count: int | None
    expected_response_class: str
    zero_result_semantics: str
    match_result_semantics: str
    query_value_persistence: str
    private_query_values_exposed: bool
    raw_request_exposed: bool
    raw_response_exposed: bool
    external_state_change: bool
    consequential_actions_permitted: bool
    claim_submission_permitted: bool
    prohibited_action_executed: bool
    authorization_consumed: bool
    authorization_consumption_ordinal: int
    consumption_key: str
    consequence_ceiling: str
    evidence_effect: str
    authority_effect: str
    receipt_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def canonical_authorization_sha256(
    authorization: ObservationAuthorizationDecision,
) -> str:
    payload = json.dumps(
        authorization.to_dict(),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def stable_consumption_key(authorization_id: str) -> str:
    return "CON-" + hashlib.sha256(
        authorization_id.strip().upper().encode("utf-8")
    ).hexdigest()[:16].upper()


def stable_query_execution_receipt_id(
    *,
    authorization_id: str,
    execution_nonce: str,
) -> str:
    payload = "\0".join(
        [
            authorization_id.strip().upper(),
            execution_nonce.strip().upper(),
        ]
    )
    return "QRC-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16].upper()


def receipt_token(receipt_id: str) -> str:
    return f"urn:humanaios:query-execution-receipt:{receipt_id}"


def _parse_time(value: str) -> datetime:
    text = str(value or "").strip()
    if not text:
        raise ValueError("execution timestamp is required")
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"invalid execution timestamp: {text}") from exc


def _validate_result_state(
    result_state: str,
    observed_record_count: int | None,
) -> tuple[str, int | None]:
    state = result_state.strip().upper()
    if state not in RESULT_STATES:
        raise ValueError(f"unsupported result_state: {state}")

    if state == "ZERO_MATCHES_OBSERVED":
        if observed_record_count != 0:
            raise ValueError("ZERO_MATCHES_OBSERVED requires observed_record_count=0")
    elif state == "MATCHES_OBSERVED":
        if observed_record_count is None or observed_record_count <= 0:
            raise ValueError("MATCHES_OBSERVED requires observed_record_count > 0")
    elif state == "OBSERVATION_FAILED":
        if observed_record_count is not None:
            raise ValueError("OBSERVATION_FAILED requires observed_record_count=null")
    return state, observed_record_count


def _authorization_is_executable(
    authorization: ObservationAuthorizationDecision,
) -> list[str]:
    reasons: list[str] = []
    if authorization.policy_id != POLICY_ID or authorization.policy_version != POLICY_VERSION:
        reasons.append("OAG policy identity/version is unsupported")
    expected_authorization_id = stable_authorization_id(
        query_plan_sha256=authorization.query_plan_sha256,
        requested_operation=authorization.requested_operation,
        policy_id=authorization.policy_id,
        policy_version=authorization.policy_version,
    )
    if authorization.authorization_id != expected_authorization_id:
        reasons.append("OAG authorization_id does not match canonical policy input")
    if authorization.authorization_token != authorization_token(
        authorization.authorization_id
    ):
        reasons.append("OAG authorization_token does not match authorization_id")
    receipt_payload = {
        "authorization_id": authorization.authorization_id,
        "query_plan_sha256": authorization.query_plan_sha256,
        "requested_operation": authorization.requested_operation,
        "decision": authorization.decision,
        "decision_reasons": authorization.decision_reasons,
        "policy_id": authorization.policy_id,
        "policy_version": authorization.policy_version,
        "target_origin_keys": authorization.target_origin_keys,
        "allowed_query_fields": authorization.allowed_query_fields,
        "consequence_ceiling": authorization.consequence_ceiling,
        "max_executions": authorization.max_executions,
    }
    expected_policy_receipt = hashlib.sha256(
        json.dumps(
            receipt_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    if authorization.policy_receipt_sha256 != expected_policy_receipt:
        reasons.append("OAG policy receipt hash mismatch")
    if authorization.schema != "humanaios.observation-authorization-decision.v1":
        reasons.append("authorization schema is invalid")
    if authorization.decision != "ALLOW_OBSERVATION":
        reasons.append("OAG decision is not ALLOW_OBSERVATION")
    if authorization.authority_effect != "OBSERVATION_ONLY":
        reasons.append("OAG authority_effect is not OBSERVATION_ONLY")
    if authorization.requested_operation != OBSERVATION_OPERATION:
        reasons.append("OAG operation is outside registry observation scope")
    if authorization.execution_state != "NOT_EXECUTED":
        reasons.append("OAG execution_state is not NOT_EXECUTED")
    if authorization.consumption_state != "UNUSED":
        reasons.append("OAG consumption_state is not UNUSED")
    if not authorization.one_shot or authorization.max_executions != 1:
        reasons.append("OAG is not one-shot")
    if authorization.consequence_ceiling != "EVIDENCE_ONLY":
        reasons.append("OAG consequence ceiling is not EVIDENCE_ONLY")
    if authorization.external_state_change:
        reasons.append("OAG permits external state change")
    if authorization.consequential_actions_permitted:
        reasons.append("OAG permits consequential actions")
    if authorization.claim_submission_permitted:
        reasons.append("OAG permits claim submission")
    if not authorization.private_subject_binding_required:
        reasons.append("OAG does not require private subject binding")
    if authorization.private_query_values_exposed:
        reasons.append("OAG exposes private query values")
    if authorization.query_value_persistence != "PRIVATE_RUNTIME_ONLY":
        reasons.append("OAG does not preserve private query values")
    return reasons


def _prior_receipts(
    rows: Iterable[QueryExecutionReceipt | dict[str, Any]],
) -> list[QueryExecutionReceipt]:
    out: list[QueryExecutionReceipt] = []
    for row in rows:
        if isinstance(row, QueryExecutionReceipt):
            out.append(row)
        else:
            out.append(query_execution_receipt_from_dict(row))
    return out


def mint_query_execution_receipt(
    *,
    authorization: ObservationAuthorizationDecision,
    query: RegistryQueryPlan,
    private_subject_binding_attestation_id: str,
    executed_query_fields: Iterable[str],
    observed_origin_key: str,
    execution_nonce: str,
    started_at: str,
    finished_at: str,
    result_state: str,
    observed_record_count: int | None,
    prior_receipts: Iterable[QueryExecutionReceipt | dict[str, Any]] = (),
) -> QueryExecutionReceipt:
    reasons = _authorization_is_executable(authorization)
    if reasons:
        raise PermissionError("; ".join(sorted(reasons)))
    if not authorization_covers_query(authorization, query):
        raise PermissionError("OAG does not cover the exact supplied RQY")
    if authorization.query_id != query.query_id:
        raise PermissionError("OAG/RQY query identity mismatch")
    if authorization.query_plan_sha256 != hashlib.sha256(
        json.dumps(
            query.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest():
        raise PermissionError("OAG/RQY query digest mismatch")

    psb = private_subject_binding_attestation_id.strip().upper()
    if not PSB_RE.fullmatch(psb):
        raise ValueError(
            "private_subject_binding_attestation_id must be opaque PSB-* token"
        )
    nonce = execution_nonce.strip().upper()
    if not EXE_RE.fullmatch(nonce):
        raise ValueError("execution_nonce must be opaque EXE-* token")

    fields = sorted(
        {
            str(value).strip().casefold()
            for value in executed_query_fields
            if str(value).strip()
        }
    )
    authorized_fields = sorted(
        {str(value).strip().casefold() for value in query.query_fields}
    )
    if fields != authorized_fields:
        raise PermissionError(
            "executed semantic query fields do not exactly match authorized RQY fields"
        )

    origin = observed_origin_key.strip().casefold()
    if not origin or origin not in {
        str(value).strip().casefold()
        for value in authorization.target_origin_keys
    }:
        raise PermissionError("observed origin is outside authorized target origins")

    start = _parse_time(started_at)
    finish = _parse_time(finished_at)
    if finish < start:
        raise ValueError("finished_at precedes started_at")

    state, count = _validate_result_state(result_state, observed_record_count)

    prior = _prior_receipts(prior_receipts)
    consumption_key = stable_consumption_key(authorization.authorization_id)
    for receipt in prior:
        if (
            receipt.authorization_id == authorization.authorization_id
            or receipt.consumption_key == consumption_key
        ):
            raise PermissionError(
                "one-shot observation authorization has already been consumed"
            )

    receipt_id = stable_query_execution_receipt_id(
        authorization_id=authorization.authorization_id,
        execution_nonce=nonce,
    )
    authorization_digest = canonical_authorization_sha256(authorization)

    payload = {
        "schema": "humanaios.query-execution-receipt.v1",
        "receipt_id": receipt_id,
        "receipt_token": receipt_token(receipt_id),
        "authorization_id": authorization.authorization_id,
        "authorization_token": authorization.authorization_token,
        "authorization_decision_sha256": authorization_digest,
        "query_id": authorization.query_id,
        "query_token": authorization.query_token,
        "query_plan_sha256": authorization.query_plan_sha256,
        "policy_receipt_sha256": authorization.policy_receipt_sha256,
        "registry_mine_id": authorization.registry_mine_id,
        "pathway_opportunity_id": authorization.pathway_opportunity_id,
        "subject_ref": authorization.subject_ref,
        "private_subject_binding_attestation_id": psb,
        "private_subject_binding_attested": True,
        "executed_operation": OBSERVATION_OPERATION,
        "executed_query_fields": fields,
        "observed_origin_key": origin,
        "execution_nonce": nonce,
        "started_at": started_at,
        "finished_at": finished_at,
        "result_state": state,
        "observed_record_count": count,
        "expected_response_class": authorization.expected_response_class,
        "zero_result_semantics": "NO_MATCH_OBSERVED_NOT_NO_ENTITLEMENT",
        "match_result_semantics": "CANDIDATE_RECORD_NOT_OWNERSHIP",
        "query_value_persistence": "PRIVATE_RUNTIME_ONLY",
        "private_query_values_exposed": False,
        "raw_request_exposed": False,
        "raw_response_exposed": False,
        "external_state_change": False,
        "consequential_actions_permitted": False,
        "claim_submission_permitted": False,
        "prohibited_action_executed": False,
        "authorization_consumed": True,
        "authorization_consumption_ordinal": 1,
        "consumption_key": consumption_key,
        "consequence_ceiling": "EVIDENCE_ONLY",
        "evidence_effect": "OBSERVATION_RECEIPT_ONLY",
        "authority_effect": "NONE",
    }
    receipt_sha256 = hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return QueryExecutionReceipt(
        **payload,
        receipt_sha256=receipt_sha256,
    )


def query_execution_receipt_from_dict(
    data: dict[str, Any],
) -> QueryExecutionReceipt:
    expected = {
        "schema",
        "receipt_id",
        "receipt_token",
        "authorization_id",
        "authorization_token",
        "authorization_decision_sha256",
        "query_id",
        "query_token",
        "query_plan_sha256",
        "policy_receipt_sha256",
        "registry_mine_id",
        "pathway_opportunity_id",
        "subject_ref",
        "private_subject_binding_attestation_id",
        "private_subject_binding_attested",
        "executed_operation",
        "executed_query_fields",
        "observed_origin_key",
        "execution_nonce",
        "started_at",
        "finished_at",
        "result_state",
        "observed_record_count",
        "expected_response_class",
        "zero_result_semantics",
        "match_result_semantics",
        "query_value_persistence",
        "private_query_values_exposed",
        "raw_request_exposed",
        "raw_response_exposed",
        "external_state_change",
        "consequential_actions_permitted",
        "claim_submission_permitted",
        "prohibited_action_executed",
        "authorization_consumed",
        "authorization_consumption_ordinal",
        "consumption_key",
        "consequence_ceiling",
        "evidence_effect",
        "authority_effect",
        "receipt_sha256",
    }
    keys = set(data)
    if keys != expected:
        missing = sorted(expected - keys)
        extra = sorted(keys - expected)
        raise ValueError(
            f"query execution receipt shape mismatch; missing={missing}; extra={extra}"
        )
    payload = dict(data)
    receipt_hash = str(payload.pop("receipt_sha256") or "")
    expected_hash = hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    if receipt_hash != expected_hash:
        raise ValueError("query execution receipt hash mismatch")
    return QueryExecutionReceipt(**data)


def load_query_execution_receipts(
    path: str | Path,
) -> list[QueryExecutionReceipt]:
    target = Path(path)
    if not target.exists():
        return []
    rows: list[QueryExecutionReceipt] = []
    for line in target.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(query_execution_receipt_from_dict(json.loads(line)))
    return rows


def append_query_execution_receipt(
    path: str | Path,
    receipt: QueryExecutionReceipt,
) -> None:
    target = Path(path)
    existing = load_query_execution_receipts(target)
    if any(
        row.authorization_id == receipt.authorization_id
        or row.consumption_key == receipt.consumption_key
        for row in existing
    ):
        raise PermissionError(
            "one-shot observation authorization has already been consumed"
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                receipt.to_dict(),
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n"
        )
