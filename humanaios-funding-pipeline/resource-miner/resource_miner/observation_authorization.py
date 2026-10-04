from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any

from .models import ResourceMine
from .registry_query import RegistryQueryPlan

POLICY_ID = "humanaios.oag.registry-observation.v1"
POLICY_VERSION = "1.0"

OBSERVATION_OPERATION = "OBSERVE_REGISTRY_QUERY_RESULTS"
PROHIBITED_OPERATIONS = {
    "CREATE_CLAIM",
    "SUBMIT_CLAIM",
    "UPDATE_CLAIM",
    "UPLOAD_DOCUMENT",
    "LOOKUP_PRIVATE_CLAIM_STATUS",
    "CREATE_ACCOUNT",
    "MUTATE_CREDENTIALS",
    "SEND_MESSAGE",
    "MAKE_PAYMENT",
    "PURCHASE",
    "TRANSFER_FUNDS",
}
DECISIONS = {"ALLOW_OBSERVATION", "REQUIRE_HUMAN", "DENY", "NOT_APPLICABLE"}

PROHIBITED_ACTIONS = [
    "CREATE_CLAIM",
    "SUBMIT_CLAIM",
    "UPDATE_CLAIM",
    "UPLOAD_DOCUMENT",
    "LOOKUP_PRIVATE_CLAIM_STATUS",
    "CREATE_ACCOUNT",
    "MUTATE_CREDENTIALS",
    "SEND_MESSAGE",
    "MAKE_PAYMENT",
    "PURCHASE",
    "TRANSFER_FUNDS",
]


@dataclass(frozen=True)
class ObservationAuthorizationDecision:
    schema: str
    authorization_id: str
    authorization_token: str
    query_id: str
    query_token: str
    query_plan_sha256: str
    registry_mine_id: str
    pathway_opportunity_id: str
    subject_ref: str
    query_class: str
    query_fields: list[str]
    observation_class: str
    requested_operation: str
    decision: str
    decision_reasons: list[str]
    policy_id: str
    policy_version: str
    authority_source: str
    target_origin_keys: list[str]
    allowed_query_fields: list[str]
    expected_response_class: str
    query_value_persistence: str
    private_query_values_exposed: bool
    external_state_change: bool
    consequence_ceiling: str
    prohibited_actions: list[str]
    one_shot: bool
    max_executions: int
    consumption_state: str
    execution_state: str
    authority_effect: str
    policy_receipt_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def canonical_query_plan_sha256(plan: RegistryQueryPlan) -> str:
    payload = json.dumps(
        plan.to_dict(),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def stable_authorization_id(
    *,
    query_plan_sha256: str,
    requested_operation: str,
    policy_id: str = POLICY_ID,
    policy_version: str = POLICY_VERSION,
) -> str:
    payload = "\0".join(
        [
            query_plan_sha256.lower(),
            requested_operation.strip().upper(),
            policy_id.strip(),
            policy_version.strip(),
        ]
    )
    return "OAG-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16].upper()


def authorization_token(authorization_id: str) -> str:
    return f"urn:humanaios:observation-authorization:{authorization_id}"


def _mine_contract(mine: ResourceMine) -> dict[str, Any]:
    contract = mine.config.get("query_contract") or {}
    return contract if isinstance(contract, dict) else {}


def _policy_reasons(
    *,
    query: RegistryQueryPlan,
    mine: ResourceMine,
    requested_operation: str,
) -> tuple[str, list[str]]:
    operation = requested_operation.strip().upper()
    reasons: list[str] = []

    if operation in PROHIBITED_OPERATIONS:
        return "DENY", [f"operation {operation} exceeds observation-only consequence ceiling"]
    if operation != OBSERVATION_OPERATION:
        return "DENY", [f"operation {operation or '<empty>'} is not authorized by registry observation policy"]

    if query.execution_state != "NOT_AUTHORIZED":
        reasons.append("RQY input must still be NOT_AUTHORIZED")
    if query.authority_effect != "NONE":
        reasons.append("RQY input must have authority_effect=NONE")
    if query.planning_state != "PLANNED":
        reasons.append("RQY input must be planning_state=PLANNED")
    if not query.explicit_subject_request:
        reasons.append("explicit subject request is required")
    if query.external_state_change:
        reasons.append("RQY must declare external_state_change=false")
    if query.query_value_persistence != "PRIVATE_RUNTIME_ONLY":
        reasons.append("query values must remain PRIVATE_RUNTIME_ONLY")

    if mine.mine_id != query.registry_mine_id:
        reasons.append("RQY Mine binding does not match evaluated Mine")
    if mine.mine_kind != "REGISTRY":
        reasons.append("target Mine is not REGISTRY")
    if not mine.enabled:
        reasons.append("target Mine is disabled")

    contract = _mine_contract(mine)
    if not contract.get("queryable"):
        reasons.append("target Mine does not declare queryable=true")
    if str(contract.get("query_class") or "").strip().upper() != query.query_class:
        reasons.append("RQY query_class is outside Mine contract")
    if str(contract.get("query_value_persistence") or "").strip().upper() != "PRIVATE_RUNTIME_ONLY":
        reasons.append("Mine query contract does not preserve private runtime values")
    if bool(contract.get("external_state_change", True)):
        reasons.append("Mine query contract permits external state change")
    if str(contract.get("authority_effect") or "").strip().upper() != "NONE":
        reasons.append("Mine query contract carries non-zero authority effect")

    allowed_fields = {
        str(x).strip().casefold()
        for x in contract.get("semantic_query_fields") or []
        if str(x).strip()
    }
    if not set(query.query_fields).issubset(allowed_fields):
        reasons.append("RQY query fields exceed Mine query contract")

    if not mine.config.get("evidence_origins"):
        reasons.append("target Mine has no declared evidence origin")

    if reasons:
        return "DENY", sorted(reasons)
    return "ALLOW_OBSERVATION", [
        "exact RQY is explicit-request-bound and planning-only",
        "target Mine is enabled REGISTRY with matching read-only query contract",
        "query values remain private-runtime-only and are not exposed to OAG",
        "operation is bounded to observing registry query results",
        "external state change is prohibited",
    ]


def evaluate_observation_authorization(
    *,
    query: RegistryQueryPlan,
    mine: ResourceMine,
    requested_operation: str = OBSERVATION_OPERATION,
) -> ObservationAuthorizationDecision:
    operation = requested_operation.strip().upper()
    query_digest = canonical_query_plan_sha256(query)
    decision, reasons = _policy_reasons(
        query=query,
        mine=mine,
        requested_operation=operation,
    )

    contract = _mine_contract(mine)
    target_origins = sorted(
        {
            str(x).strip().casefold()
            for x in mine.config.get("evidence_origins") or []
            if str(x).strip()
        }
    )
    allowed_fields = sorted(
        {
            str(x).strip().casefold()
            for x in contract.get("semantic_query_fields") or []
            if str(x).strip()
        }
    )

    authorization_id = stable_authorization_id(
        query_plan_sha256=query_digest,
        requested_operation=operation,
    )
    authority_effect = "OBSERVATION_ONLY" if decision == "ALLOW_OBSERVATION" else "NONE"
    consumption_state = "UNUSED" if decision == "ALLOW_OBSERVATION" else "NOT_APPLICABLE"

    receipt_payload = {
        "authorization_id": authorization_id,
        "query_plan_sha256": query_digest,
        "requested_operation": operation,
        "decision": decision,
        "decision_reasons": reasons,
        "policy_id": POLICY_ID,
        "policy_version": POLICY_VERSION,
        "target_origin_keys": target_origins,
        "allowed_query_fields": allowed_fields,
        "consequence_ceiling": "EVIDENCE_ONLY",
        "max_executions": 1,
    }
    policy_receipt_sha256 = hashlib.sha256(
        json.dumps(
            receipt_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    return ObservationAuthorizationDecision(
        schema="humanaios.observation-authorization-decision.v1",
        authorization_id=authorization_id,
        authorization_token=authorization_token(authorization_id),
        query_id=query.query_id,
        query_token=query.query_token,
        query_plan_sha256=query_digest,
        registry_mine_id=query.registry_mine_id,
        pathway_opportunity_id=query.pathway_opportunity_id,
        subject_ref=query.subject_ref,
        query_class=query.query_class,
        query_fields=list(query.query_fields),
        observation_class="PUBLIC_REGISTRY_QUERY",
        requested_operation=operation,
        decision=decision,
        decision_reasons=reasons,
        policy_id=POLICY_ID,
        policy_version=POLICY_VERSION,
        authority_source="EXPLICIT_SUBJECT_REQUEST_PLUS_POLICY",
        target_origin_keys=target_origins,
        allowed_query_fields=allowed_fields,
        expected_response_class=query.expected_response_class,
        query_value_persistence="PRIVATE_RUNTIME_ONLY",
        private_query_values_exposed=False,
        external_state_change=False,
        consequence_ceiling="EVIDENCE_ONLY",
        prohibited_actions=list(PROHIBITED_ACTIONS),
        one_shot=True,
        max_executions=1,
        consumption_state=consumption_state,
        execution_state="NOT_EXECUTED",
        authority_effect=authority_effect,
        policy_receipt_sha256=policy_receipt_sha256,
    )


def authorization_covers_query(
    decision: ObservationAuthorizationDecision,
    query: RegistryQueryPlan,
) -> bool:
    return (
        decision.decision == "ALLOW_OBSERVATION"
        and decision.consumption_state == "UNUSED"
        and decision.query_id == query.query_id
        and decision.query_plan_sha256 == canonical_query_plan_sha256(query)
        and decision.requested_operation == OBSERVATION_OPERATION
        and decision.max_executions == 1
        and decision.external_state_change is False
        and decision.consequence_ceiling == "EVIDENCE_ONLY"
    )
