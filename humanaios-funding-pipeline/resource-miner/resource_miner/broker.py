from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

from .models import EvidenceRef, ResourceCandidate

PROVIDER_CLASSES = {
    "HUMANAIOS_INTERNAL",
    "LOCAL_MACHINE",
    "OPEN_SOURCE",
    "EXTERNAL_SERVICE",
    "DATASET",
    "HUMAN_EXPERT",
    "OTHER",
}
SUITABILITY_STATES = {"ADEQUATE", "PARTIAL", "INADEQUATE", "UNKNOWN"}
SCREEN_STATES = {"PASS", "PASS_WITH_CONDITIONS", "FAIL", "UNKNOWN"}
NETWORK_BEHAVIOR_STATES = {
    "NONE",
    "READ_ONLY",
    "ACTIVE",
    "PASSIVE_PUBLIC_SOURCE",
    "THIRD_PARTY_API_READ_ONLY",
    "TARGET_READ_ONLY",
    "TARGET_ACTIVE",
    "MIXED",
    "UNKNOWN",
}
ACTIONS = {
    "REVIEW_RESOURCE_METADATA",
    "COMPOSE_CAPABILITY_PACKAGE",
    "INSTALL_LOCAL_RESOURCE",
    "EXECUTE_EXTERNAL_TOOL",
    "SUBMIT_FINDING",
}
AUTH_DECISIONS = {"AUTHORIZED_BOUNDED", "REQUIRE_HUMAN", "DENY", "NOT_APPLICABLE"}
OUTCOME_STATES = {
    "REVIEW_COMPLETED",
    "RESOURCE_ACCEPTED",
    "RESOURCE_REJECTED",
    "NO_SUITABLE_RESOURCE",
    "EXECUTION_NOT_ATTEMPTED",
    "EXECUTION_REPORTED",
}


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _stable_id(prefix: str, payload: Any) -> str:
    return f"{prefix}-" + _canonical_sha256(payload)[:16].upper()


def _evidence_to_dict(rows: Iterable[EvidenceRef]) -> list[dict[str, Any]]:
    return [asdict(row) for row in rows]


@dataclass(frozen=True)
class BrokerOpportunity:
    opportunity_id: str
    title: str
    source_kind: str
    source_url: str
    sponsor: str
    evidence: list[dict[str, Any]]
    authority_effect: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BrokerRequirement:
    requirement_id: str
    opportunity_id: str
    label: str
    objective: str
    required_affordances: list[str]
    allowed_resource_types: list[str]
    method_permission_state: str
    target_scope_state: str
    external_state_change_allowed: bool
    evidence: list[dict[str, Any]]
    demand_requirement_id: str = ""
    demand_mode: str = ""
    demand_semantic_class: str = ""
    authority_effect: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResourceScreen:
    screen_id: str
    resource_id: str
    provenance_state: str
    license_state: str
    permissions_state: str
    network_behavior: str
    credential_requirement: str
    external_state_change: bool | None
    auditability: str
    least_privilege_compatible: bool | None
    state: str
    findings: list[str]
    authority_effect: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SuitabilityAssessment:
    assessment_id: str
    opportunity_id: str
    requirement_id: str
    resource_id: str
    provider_class: str
    resource_sha256: str
    matched_affordances: list[str]
    missing_affordances: list[str]
    matched_resource_types: list[str]
    suitability_state: str
    screen_id: str
    screen_state: str
    evidence: list[dict[str, Any]]
    rationale: list[str]
    authority_effect: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BrokerAuthorization:
    authorization_id: str
    opportunity_id: str
    requirement_id: str
    resource_id: str
    suitability_id: str
    requested_action: str
    human_authorized: bool
    decision: str
    reasons: list[str]
    execution_performed: bool
    consequence_ceiling: str
    authority_effect: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BrokerOutcome:
    outcome_id: str
    opportunity_id: str
    requirement_id: str
    resource_id: str
    suitability_id: str
    authorization_id: str
    outcome_state: str
    observation: str
    evidence: list[dict[str, Any]]
    execution_claimed: bool
    authority_effect: str
    outcome_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_opportunity(
    *,
    title: str,
    source_kind: str,
    source_url: str,
    sponsor: str,
    evidence: Iterable[EvidenceRef],
) -> BrokerOpportunity:
    rows = _evidence_to_dict(evidence)
    if not rows:
        raise ValueError("broker opportunity requires provenance-bearing evidence")
    payload = {
        "title": title.strip(),
        "source_kind": source_kind.strip().upper(),
        "source_url": source_url.strip(),
        "sponsor": sponsor.strip(),
        "evidence": rows,
    }
    return BrokerOpportunity(
        opportunity_id=_stable_id("BOP", payload),
        title=payload["title"],
        source_kind=payload["source_kind"],
        source_url=payload["source_url"],
        sponsor=payload["sponsor"],
        evidence=rows,
    )


def build_requirement(
    *,
    opportunity: BrokerOpportunity,
    label: str,
    objective: str,
    required_affordances: Iterable[str],
    allowed_resource_types: Iterable[str],
    method_permission_state: str,
    target_scope_state: str,
    external_state_change_allowed: bool,
    evidence: Iterable[EvidenceRef],
    demand_requirement_id: str = "",
    demand_mode: str = "",
    demand_semantic_class: str = "",
) -> BrokerRequirement:
    affordances = sorted({str(x).strip() for x in required_affordances if str(x).strip()})
    resource_types = sorted({str(x).strip() for x in allowed_resource_types if str(x).strip()})
    rows = _evidence_to_dict(evidence)
    if not affordances:
        raise ValueError("broker requirement requires at least one affordance")
    if not rows:
        raise ValueError("broker requirement requires evidence")
    permission = method_permission_state.strip().upper()
    scope = target_scope_state.strip().upper()
    if permission not in {"PERMITTED", "PROHIBITED", "UNKNOWN"}:
        raise ValueError("unsupported method_permission_state")
    if scope not in {"IN_SCOPE", "OUT_OF_SCOPE", "UNKNOWN", "NOT_APPLICABLE"}:
        raise ValueError("unsupported target_scope_state")
    payload = {
        "opportunity_id": opportunity.opportunity_id,
        "label": label.strip(),
        "objective": objective.strip(),
        "required_affordances": affordances,
        "allowed_resource_types": resource_types,
        "method_permission_state": permission,
        "target_scope_state": scope,
        "external_state_change_allowed": bool(external_state_change_allowed),
        "evidence": rows,
        "demand_requirement_id": demand_requirement_id.strip(),
        "demand_mode": demand_mode.strip().upper(),
        "demand_semantic_class": demand_semantic_class.strip().upper(),
    }
    return BrokerRequirement(
        requirement_id=_stable_id("BRQ", payload),
        opportunity_id=opportunity.opportunity_id,
        label=payload["label"],
        objective=payload["objective"],
        required_affordances=affordances,
        allowed_resource_types=resource_types,
        method_permission_state=permission,
        target_scope_state=scope,
        external_state_change_allowed=bool(external_state_change_allowed),
        evidence=rows,
        demand_requirement_id=payload["demand_requirement_id"],
        demand_mode=payload["demand_mode"],
        demand_semantic_class=payload["demand_semantic_class"],
    )


def screen_resource(
    resource: ResourceCandidate,
    *,
    provenance_state: str,
    license_state: str,
    permissions_state: str,
    network_behavior: str,
    credential_requirement: str,
    external_state_change: bool | None,
    auditability: str,
    least_privilege_compatible: bool | None,
) -> ResourceScreen:
    normalized_network_behavior = network_behavior.strip().upper()
    if normalized_network_behavior not in NETWORK_BEHAVIOR_STATES:
        raise ValueError(
            f"unsupported network_behavior: {normalized_network_behavior}"
        )
    values = {
        "provenance_state": provenance_state.strip().upper(),
        "license_state": license_state.strip().upper(),
        "permissions_state": permissions_state.strip().upper(),
        "network_behavior": normalized_network_behavior,
        "credential_requirement": credential_requirement.strip().upper(),
        "auditability": auditability.strip().upper(),
    }
    findings: list[str] = []

    hard_fail = (
        values["license_state"] == "RESTRICTED"
        or least_privilege_compatible is False
    )
    unknown = (
        values["provenance_state"] != "VERIFIED"
        or values["license_state"] == "UNKNOWN"
        or values["permissions_state"] == "UNKNOWN"
        or values["network_behavior"] == "UNKNOWN"
        or values["credential_requirement"] == "UNKNOWN"
        or external_state_change is None
        or values["auditability"] == "UNKNOWN"
        or least_privilege_compatible is None
    )
    conditional = (
        values["permissions_state"] == "ELEVATED"
        or values["network_behavior"] == "ACTIVE"
        or values["credential_requirement"] == "REQUIRED"
        or external_state_change is True
        or values["auditability"] == "PARTIAL"
    )

    if hard_fail:
        state = "FAIL"
    elif unknown:
        state = "UNKNOWN"
    elif conditional:
        state = "PASS_WITH_CONDITIONS"
    else:
        state = "PASS"

    if values["provenance_state"] != "VERIFIED":
        findings.append("resource provenance is not independently verified")
    if values["license_state"] != "ALLOWABLE":
        findings.append(f"license_state={values['license_state']}")
    if values["permissions_state"] != "MINIMAL":
        findings.append(f"permissions_state={values['permissions_state']}")
    if values["network_behavior"] in {"THIRD_PARTY_API_READ_ONLY"}:
        findings.append(
            f"third_party_api_interaction={values['network_behavior']}"
        )
    elif values["network_behavior"] not in {
        "READ_ONLY",
        "NONE",
        "PASSIVE_PUBLIC_SOURCE",
    }:
        findings.append(f"network_behavior={values['network_behavior']}")
    if values["credential_requirement"] != "NONE":
        findings.append(f"credential_requirement={values['credential_requirement']}")
    if external_state_change is not False:
        findings.append(f"external_state_change={external_state_change}")
    if values["auditability"] != "ADEQUATE":
        findings.append(f"auditability={values['auditability']}")
    if least_privilege_compatible is not True:
        findings.append(f"least_privilege_compatible={least_privilege_compatible}")

    payload = {
        "resource_id": resource.resource_id,
        **values,
        "external_state_change": external_state_change,
        "least_privilege_compatible": least_privilege_compatible,
        "state": state,
        "findings": sorted(findings),
    }
    return ResourceScreen(
        screen_id=_stable_id("CRS", payload),
        resource_id=resource.resource_id,
        provenance_state=values["provenance_state"],
        license_state=values["license_state"],
        permissions_state=values["permissions_state"],
        network_behavior=values["network_behavior"],
        credential_requirement=values["credential_requirement"],
        external_state_change=external_state_change,
        auditability=values["auditability"],
        least_privilege_compatible=least_privilege_compatible,
        state=state,
        findings=sorted(findings),
    )


def assess_suitability(
    *,
    opportunity: BrokerOpportunity,
    requirement: BrokerRequirement,
    resource: ResourceCandidate,
    provider_class: str,
    screen: ResourceScreen,
) -> SuitabilityAssessment:
    if requirement.opportunity_id != opportunity.opportunity_id:
        raise ValueError("requirement is not bound to supplied opportunity")
    provider = provider_class.strip().upper()
    if provider not in PROVIDER_CLASSES:
        raise ValueError("unsupported provider_class")
    if screen.resource_id != resource.resource_id:
        raise ValueError("screen is not bound to supplied resource")
    if not resource.evidence:
        raise ValueError("resource requires provenance-bearing evidence")

    resource_affordances = set(resource.resource_affordances)
    required = set(requirement.required_affordances)
    matched = sorted(resource_affordances & required)
    missing = sorted(required - resource_affordances)
    allowed_types = set(requirement.allowed_resource_types)
    matched_types = sorted(set(resource.resource_types) & allowed_types) if allowed_types else sorted(resource.resource_types)

    rationale: list[str] = []
    if allowed_types and not matched_types:
        state = "INADEQUATE"
        rationale.append("resource type is outside requirement's allowed resource types")
    elif not matched:
        state = "INADEQUATE"
        rationale.append("resource provides none of the required affordances")
    elif missing:
        state = "PARTIAL"
        rationale.append("resource covers only part of the required affordance set")
    else:
        state = "ADEQUATE"
        rationale.append("resource covers the required affordance set")

    if screen.state == "FAIL":
        state = "INADEQUATE"
        rationale.append("constitutional/resource screen failed")
    elif screen.state == "UNKNOWN" and state == "ADEQUATE":
        state = "UNKNOWN"
        rationale.append("resource screen contains unresolved unknowns")
    elif screen.state == "PASS_WITH_CONDITIONS" and state == "ADEQUATE":
        state = "PARTIAL"
        rationale.append("resource screen imposes unresolved conditions")

    resource_payload = resource.to_dict()
    payload = {
        "opportunity_id": opportunity.opportunity_id,
        "requirement_id": requirement.requirement_id,
        "resource_id": resource.resource_id,
        "provider_class": provider,
        "resource_sha256": _canonical_sha256(resource_payload),
        "matched_affordances": matched,
        "missing_affordances": missing,
        "matched_resource_types": matched_types,
        "suitability_state": state,
        "screen_id": screen.screen_id,
        "screen_state": screen.state,
        "evidence": _evidence_to_dict(resource.evidence),
    }
    return SuitabilityAssessment(
        assessment_id=_stable_id("BSA", payload),
        opportunity_id=opportunity.opportunity_id,
        requirement_id=requirement.requirement_id,
        resource_id=resource.resource_id,
        provider_class=provider,
        resource_sha256=payload["resource_sha256"],
        matched_affordances=matched,
        missing_affordances=missing,
        matched_resource_types=matched_types,
        suitability_state=state,
        screen_id=screen.screen_id,
        screen_state=screen.state,
        evidence=payload["evidence"],
        rationale=rationale,
    )


def authorize_broker_action(
    *,
    opportunity: BrokerOpportunity,
    requirement: BrokerRequirement,
    assessment: SuitabilityAssessment,
    requested_action: str,
    human_authorized: bool = False,
) -> BrokerAuthorization:
    action = requested_action.strip().upper()
    reasons: list[str] = []
    decision = "DENY"
    ceiling = "NONE"

    lineage_ok = (
        assessment.opportunity_id == opportunity.opportunity_id
        and assessment.requirement_id == requirement.requirement_id
    )
    if not lineage_ok:
        reasons.append("suitability lineage does not match opportunity/requirement")
    elif action not in ACTIONS:
        reasons.append("requested action is outside broker policy")
    elif assessment.suitability_state in {"INADEQUATE", "UNKNOWN"}:
        reasons.append(f"suitability_state={assessment.suitability_state} fails closed")
    elif assessment.screen_state not in {"PASS", "PASS_WITH_CONDITIONS"}:
        reasons.append(f"screen_state={assessment.screen_state} fails closed")
    elif action in {"REVIEW_RESOURCE_METADATA", "COMPOSE_CAPABILITY_PACKAGE"}:
        decision = "AUTHORIZED_BOUNDED"
        ceiling = "BROKER_REVIEW_ONLY"
        reasons.append("bounded broker review/composition requires no target execution")
    elif action == "INSTALL_LOCAL_RESOURCE":
        if not human_authorized:
            decision = "REQUIRE_HUMAN"
            reasons.append("local installation can change operator state")
        else:
            decision = "AUTHORIZED_BOUNDED"
            ceiling = "LOCAL_INSTALL_ONLY"
            reasons.append("explicit human authorization supplied for bounded local install")
    elif action in {"EXECUTE_EXTERNAL_TOOL", "SUBMIT_FINDING"}:
        if requirement.method_permission_state == "PROHIBITED":
            decision = "DENY"
            reasons.append("program/method policy prohibits requested method")
        elif requirement.target_scope_state == "OUT_OF_SCOPE":
            decision = "DENY"
            reasons.append("target scope is explicitly OUT_OF_SCOPE")
        elif requirement.method_permission_state != "PERMITTED" or requirement.target_scope_state != "IN_SCOPE":
            decision = "REQUIRE_HUMAN"
            reasons.append("method permission or target scope is not fully established")
        elif not human_authorized:
            decision = "REQUIRE_HUMAN"
            reasons.append("explicit human authorization is required for external consequence")
        else:
            decision = "AUTHORIZED_BOUNDED"
            ceiling = "EXTERNAL_ACTION_EXPLICIT_SCOPE_ONLY"
            reasons.append("human authorization plus explicit method/scope evidence present")

    payload = {
        "opportunity_id": opportunity.opportunity_id,
        "requirement_id": requirement.requirement_id,
        "resource_id": assessment.resource_id,
        "suitability_id": assessment.assessment_id,
        "requested_action": action,
        "human_authorized": bool(human_authorized),
        "decision": decision,
        "reasons": sorted(reasons),
        "consequence_ceiling": ceiling,
    }
    return BrokerAuthorization(
        authorization_id=_stable_id("BAU", payload),
        opportunity_id=opportunity.opportunity_id,
        requirement_id=requirement.requirement_id,
        resource_id=assessment.resource_id,
        suitability_id=assessment.assessment_id,
        requested_action=action,
        human_authorized=bool(human_authorized),
        decision=decision,
        reasons=sorted(reasons),
        execution_performed=False,
        consequence_ceiling=ceiling,
        authority_effect="BOUNDED_ACTION_AUTHORITY" if decision == "AUTHORIZED_BOUNDED" else "NONE",
    )


def record_broker_outcome(
    *,
    opportunity: BrokerOpportunity,
    requirement: BrokerRequirement,
    assessment: SuitabilityAssessment,
    authorization: BrokerAuthorization,
    outcome_state: str,
    observation: str,
    evidence: Iterable[EvidenceRef],
    execution_claimed: bool = False,
) -> BrokerOutcome:
    state = outcome_state.strip().upper()
    if state not in OUTCOME_STATES:
        raise ValueError("unsupported broker outcome state")
    if authorization.opportunity_id != opportunity.opportunity_id:
        raise ValueError("authorization/opportunity lineage mismatch")
    if authorization.requirement_id != requirement.requirement_id:
        raise ValueError("authorization/requirement lineage mismatch")
    if authorization.suitability_id != assessment.assessment_id:
        raise ValueError("authorization/suitability lineage mismatch")
    rows = _evidence_to_dict(evidence)
    if not rows:
        raise ValueError("broker outcome requires evidence")
    if execution_claimed:
        if authorization.decision != "AUTHORIZED_BOUNDED":
            raise PermissionError("cannot record executed outcome without bounded authorization")
        if authorization.requested_action not in {"EXECUTE_EXTERNAL_TOOL", "SUBMIT_FINDING", "INSTALL_LOCAL_RESOURCE"}:
            raise PermissionError("requested action does not support execution_claimed")
    if state == "EXECUTION_REPORTED" and not execution_claimed:
        raise ValueError("EXECUTION_REPORTED requires execution_claimed=true")

    base = {
        "opportunity_id": opportunity.opportunity_id,
        "requirement_id": requirement.requirement_id,
        "resource_id": assessment.resource_id,
        "suitability_id": assessment.assessment_id,
        "authorization_id": authorization.authorization_id,
        "outcome_state": state,
        "observation": observation.strip(),
        "evidence": rows,
        "execution_claimed": bool(execution_claimed),
        "authority_effect": "NONE",
    }
    outcome_id = _stable_id("BOT", base)
    receipt_payload = {**base, "outcome_id": outcome_id}
    return BrokerOutcome(
        outcome_id=outcome_id,
        opportunity_id=opportunity.opportunity_id,
        requirement_id=requirement.requirement_id,
        resource_id=assessment.resource_id,
        suitability_id=assessment.assessment_id,
        authorization_id=authorization.authorization_id,
        outcome_state=state,
        observation=observation.strip(),
        evidence=rows,
        execution_claimed=bool(execution_claimed),
        authority_effect="NONE",
        outcome_sha256=_canonical_sha256(receipt_payload),
    )
