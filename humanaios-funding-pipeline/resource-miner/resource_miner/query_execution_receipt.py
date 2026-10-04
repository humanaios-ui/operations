from __future__ import annotations

import fcntl
import hashlib
import json
import os
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
from .registry_query import RegistryQueryPlan, SUBJECT_REF_RE, registry_query_token

RESULT_STATES = {
    "ZERO_MATCHES_OBSERVED",
    "MATCHES_OBSERVED",
    "OBSERVATION_FAILED",
}
QRC_SCHEMA = "humanaios.query-execution-receipt.v1"
QRC_QUERY_FIELDS = {"owner_name", "business_name", "last_known_location"}
PSB_RE = re.compile(r"^PSB-[A-F0-9]{16}$")
EXE_RE = re.compile(r"^EXE-[A-F0-9]{16}$")
QRC_RE = re.compile(r"^QRC-[A-F0-9]{16}$")
OAG_RE = re.compile(r"^OAG-[A-F0-9]{16}$")
RQY_RE = re.compile(r"^RQY-[A-F0-9]{16}$")
MINE_RE = re.compile(r"^MINE-[A-F0-9]{16}$")
OPP_RE = re.compile(r"^OPP-[A-F0-9]{16}$")
CON_RE = re.compile(r"^CON-[A-F0-9]{16}$")
HASH_RE = re.compile(r"^[a-f0-9]{64}$")


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
    if not isinstance(value, str):
        raise ValueError("execution timestamp must be a string")
    text = value.strip()
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
    if not isinstance(result_state, str):
        raise ValueError("result_state must be a string")
    state = result_state.strip().upper()
    if state not in RESULT_STATES:
        raise ValueError(f"unsupported result_state: {state}")

    if observed_record_count is not None and type(observed_record_count) is not int:
        raise ValueError("observed_record_count must be an integer or null")
    if isinstance(observed_record_count, int) and observed_record_count < 0:
        raise ValueError("observed_record_count cannot be negative")

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


def _normalized_fields(values: Iterable[str]) -> list[str]:
    return sorted(
        {
            str(value).strip().casefold()
            for value in values
            if str(value).strip()
        }
    )


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


def _validate_authorization_query_lineage(
    authorization: ObservationAuthorizationDecision,
    query: RegistryQueryPlan,
) -> None:
    comparisons = {
        "query_id": (authorization.query_id, query.query_id),
        "query_token": (authorization.query_token, query.query_token),
        "registry_mine_id": (
            authorization.registry_mine_id,
            query.registry_mine_id,
        ),
        "pathway_opportunity_id": (
            authorization.pathway_opportunity_id,
            query.pathway_opportunity_id,
        ),
        "subject_ref": (authorization.subject_ref, query.subject_ref),
        "query_class": (authorization.query_class, query.query_class),
        "expected_response_class": (
            authorization.expected_response_class,
            query.expected_response_class,
        ),
    }
    mismatches = [
        name
        for name, (authorized, planned) in comparisons.items()
        if authorized != planned
    ]
    if _normalized_fields(authorization.query_fields) != _normalized_fields(
        query.query_fields
    ):
        mismatches.append("query_fields")
    if mismatches:
        raise PermissionError(
            "OAG/RQY duplicated lineage mismatch: " + ", ".join(sorted(mismatches))
        )
    if not SUBJECT_REF_RE.fullmatch(query.subject_ref):
        raise PermissionError("RQY subject_ref is not a privacy-safe SUBJ-* token")


def _prior_receipts(
    rows: Iterable[QueryExecutionReceipt | dict[str, Any]],
) -> list[QueryExecutionReceipt]:
    out: list[QueryExecutionReceipt] = []
    for row in rows:
        payload = row.to_dict() if isinstance(row, QueryExecutionReceipt) else row
        out.append(query_execution_receipt_from_dict(payload))
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
    _validate_authorization_query_lineage(authorization, query)
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

    fields = _normalized_fields(executed_query_fields)
    authorized_fields = _normalized_fields(query.query_fields)
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
        "schema": QRC_SCHEMA,
        "receipt_id": receipt_id,
        "receipt_token": receipt_token(receipt_id),
        "authorization_id": authorization.authorization_id,
        "authorization_token": authorization.authorization_token,
        "authorization_decision_sha256": authorization_digest,
        "query_id": query.query_id,
        "query_token": query.query_token,
        "query_plan_sha256": authorization.query_plan_sha256,
        "policy_receipt_sha256": authorization.policy_receipt_sha256,
        "registry_mine_id": query.registry_mine_id,
        "pathway_opportunity_id": query.pathway_opportunity_id,
        "subject_ref": query.subject_ref,
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
        "expected_response_class": query.expected_response_class,
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


def _validate_receipt_semantics(data: dict[str, Any]) -> None:
    patterns = {
        "receipt_id": QRC_RE,
        "authorization_id": OAG_RE,
        "query_id": RQY_RE,
        "registry_mine_id": MINE_RE,
        "pathway_opportunity_id": OPP_RE,
        "subject_ref": SUBJECT_REF_RE,
        "private_subject_binding_attestation_id": PSB_RE,
        "execution_nonce": EXE_RE,
        "consumption_key": CON_RE,
    }
    for field, pattern in patterns.items():
        value = data.get(field)
        if not isinstance(value, str) or not pattern.fullmatch(value):
            raise ValueError(f"query execution receipt has invalid {field}")

    for field in (
        "authorization_decision_sha256",
        "query_plan_sha256",
        "policy_receipt_sha256",
        "receipt_sha256",
    ):
        value = data.get(field)
        if not isinstance(value, str) or not HASH_RE.fullmatch(value):
            raise ValueError(f"query execution receipt has invalid {field}")

    fixed = {
        "schema": QRC_SCHEMA,
        "private_subject_binding_attested": True,
        "executed_operation": OBSERVATION_OPERATION,
        "expected_response_class": "ZERO_OR_MORE_CANDIDATE_RECORDS",
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
        "consequence_ceiling": "EVIDENCE_ONLY",
        "evidence_effect": "OBSERVATION_RECEIPT_ONLY",
        "authority_effect": "NONE",
    }
    for field, expected in fixed.items():
        actual = data.get(field)
        if isinstance(expected, bool):
            if actual is not expected:
                raise ValueError(
                    f"query execution receipt requires {field}={expected!r}"
                )
        elif field == "authorization_consumption_ordinal":
            if type(actual) is not int or actual != expected:
                raise ValueError(
                    "query execution receipt requires "
                    "authorization_consumption_ordinal=1"
                )
        elif actual != expected:
            raise ValueError(
                f"query execution receipt requires {field}={expected!r}"
            )

    fields = data.get("executed_query_fields")
    if not isinstance(fields, list) or not fields:
        raise ValueError("executed_query_fields must be a non-empty list")
    if not all(isinstance(field, str) for field in fields):
        raise ValueError("executed_query_fields must contain strings")
    normalized_fields = _normalized_fields(fields)
    if fields != normalized_fields:
        raise ValueError("executed_query_fields must be canonical and unique")
    if not set(fields).issubset(QRC_QUERY_FIELDS):
        raise ValueError("executed_query_fields contain unsupported v1 fields")

    origin = data.get("observed_origin_key")
    if (
        not isinstance(origin, str)
        or not origin
        or origin != origin.strip().casefold()
    ):
        raise ValueError("observed_origin_key must be a canonical non-empty string")

    start = _parse_time(data.get("started_at"))
    finish = _parse_time(data.get("finished_at"))
    if finish < start:
        raise ValueError("finished_at precedes started_at")

    state, count = _validate_result_state(
        data.get("result_state"),
        data.get("observed_record_count"),
    )
    if state != data.get("result_state") or count != data.get("observed_record_count"):
        raise ValueError("result state/count are not canonical")

    authorization_id = data["authorization_id"]
    execution_nonce = data["execution_nonce"]
    expected_receipt_id = stable_query_execution_receipt_id(
        authorization_id=authorization_id,
        execution_nonce=execution_nonce,
    )
    if data["receipt_id"] != expected_receipt_id:
        raise ValueError("receipt_id does not match authorization_id/execution_nonce")
    if data.get("receipt_token") != receipt_token(expected_receipt_id):
        raise ValueError("receipt_token does not match receipt_id")
    if data.get("authorization_token") != authorization_token(authorization_id):
        raise ValueError("authorization_token does not match authorization_id")
    if data.get("query_token") != registry_query_token(data["query_id"]):
        raise ValueError("query_token does not match query_id")
    if data["consumption_key"] != stable_consumption_key(authorization_id):
        raise ValueError("consumption_key does not match authorization_id")


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

    detached = json.loads(
        json.dumps(
            data,
            ensure_ascii=False,
            sort_keys=True,
            allow_nan=False,
        )
    )
    _validate_receipt_semantics(detached)

    payload = dict(detached)
    receipt_hash = payload.pop("receipt_sha256")
    expected_hash = hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    if receipt_hash != expected_hash:
        raise ValueError("query execution receipt hash mismatch")
    return QueryExecutionReceipt(**detached)


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
    validated_receipt = query_execution_receipt_from_dict(receipt.to_dict())

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            handle.seek(0)
            existing: list[QueryExecutionReceipt] = []
            for line in handle.read().splitlines():
                if not line.strip():
                    continue
                existing.append(
                    query_execution_receipt_from_dict(json.loads(line))
                )
            if any(
                row.authorization_id == validated_receipt.authorization_id
                or row.consumption_key == validated_receipt.consumption_key
                for row in existing
            ):
                raise PermissionError(
                    "one-shot observation authorization has already been consumed"
                )
            handle.seek(0, os.SEEK_END)
            handle.write(
                json.dumps(
                    validated_receipt.to_dict(),
                    ensure_ascii=False,
                    sort_keys=True,
                    allow_nan=False,
                )
                + "\n"
            )
            handle.flush()
            os.fsync(handle.fileno())
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
