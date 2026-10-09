from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Iterable

from .broker import BrokerRequirement, ResourceScreen, SuitabilityAssessment
from .demand import DemandProfile
from .models import ResourceCandidate
from .service_surface import normalize_surface_classes

COVERAGE_STATES = {"ADEQUATE", "PARTIAL", "UNKNOWN", "UNRESOLVED"}
PACKAGE_SCREEN_STATES = {"PASS", "PASS_WITH_CONDITIONS", "FAIL", "UNKNOWN"}


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


def _dedupe_evidence(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for row in rows:
        key = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        if key in seen:
            continue
        seen.add(key)
        out.append(dict(row))
    return out


@dataclass(frozen=True)
class PackageRequirementBinding:
    demand_requirement_id: str
    broker_requirement_id: str
    demand_mode: str
    demand_semantic_class: str
    selected_assessment_ids: list[str]
    selected_resource_ids: list[str]
    coverage_state: str
    service_surface_classes: list[str]
    evidence: list[dict[str, Any]]
    authority_effect: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CapabilityPackage:
    schema: str
    package_id: str
    opportunity_id: str
    demand_profile_id: str
    bindings: list[PackageRequirementBinding]
    resource_ids: list[str]
    suitability_ids: list[str]
    service_surface_classes: list[str]
    required_coverage_state: str
    required_requirement_count: int
    required_adequately_covered_count: int
    nonrequired_requirement_count: int
    nonrequired_covered_count: int
    uncovered_required_requirement_ids: list[str]
    partial_required_requirement_ids: list[str]
    uncovered_nonrequired_requirement_ids: list[str]
    composition_screen_state: str
    composition_findings: list[str]
    authorization_state: str
    target_scope_state: str
    method_permission_state: str
    evidence: list[dict[str, Any]]
    authority_effect: str
    package_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _coverage_for_assessments(rows: list[SuitabilityAssessment]) -> str:
    # Capability coverage is distinct from package/resource screening conditions.
    # A resource may cover every required affordance while remaining conditional
    # because its screen requires review (credentials, target-touching behavior,
    # commercial terms, etc.). CPK records that capability as covered and lets
    # the composition screen carry the control condition.
    for row in rows:
        if (
            row.matched_affordances
            and not row.missing_affordances
            and row.screen_state in {"PASS", "PASS_WITH_CONDITIONS"}
        ):
            return "ADEQUATE"
    states = {row.suitability_state for row in rows}
    if "PARTIAL" in states:
        return "PARTIAL"
    if "UNKNOWN" in states:
        return "UNKNOWN"
    return "UNRESOLVED"


def _resource_conflicts(
    resources: dict[str, ResourceCandidate],
    selected_resource_ids: list[str],
) -> list[str]:
    selected = set(selected_resource_ids)
    findings: list[str] = []
    for resource_id in selected_resource_ids:
        resource = resources[resource_id]
        conflicts = {
            str(value).strip()
            for value in (resource.composition_conflicts or [])
            if str(value).strip()
        }
        for other in sorted(conflicts & selected):
            if other == resource_id:
                continue
            pair = " <-> ".join(sorted([resource_id, other]))
            finding = f"DECLARED_RESOURCE_CONFLICT:{pair}"
            if finding not in findings:
                findings.append(finding)
    return sorted(findings)


def _screen_package(
    *,
    selected_resource_ids: list[str],
    resources: dict[str, ResourceCandidate],
    resource_screens: dict[str, ResourceScreen],
    required_coverage_state: str,
    allowed_network_behaviors: set[str] | None = None,
) -> tuple[str, list[str]]:
    findings: list[str] = []
    hard_fail = required_coverage_state != "COMPLETE"
    unknown = False
    conditional = False

    if hard_fail:
        findings.append("REQUIRED_CAPABILITY_COVERAGE_INCOMPLETE")

    credentialed_resources = 0
    for resource_id in selected_resource_ids:
        resource = resources.get(resource_id)
        if resource is None:
            hard_fail = True
            findings.append(f"MISSING_RESOURCE:{resource_id}")
            continue
        if not resource.evidence:
            hard_fail = True
            findings.append(f"MISSING_RESOURCE_PROVENANCE:{resource_id}")

        screen = resource_screens.get(resource_id)
        if screen is None:
            unknown = True
            findings.append(f"MISSING_RESOURCE_SCREEN:{resource_id}")
            continue

        if screen.state == "FAIL":
            hard_fail = True
            findings.append(f"RESOURCE_SCREEN_FAIL:{resource_id}")
        elif screen.state == "UNKNOWN":
            unknown = True
            findings.append(f"RESOURCE_SCREEN_UNKNOWN:{resource_id}")
        elif screen.state == "PASS_WITH_CONDITIONS":
            conditional = True
            findings.append(f"RESOURCE_SCREEN_CONDITIONAL:{resource_id}")

        if screen.provenance_state != "VERIFIED":
            unknown = True
            findings.append(f"PROVENANCE_NOT_VERIFIED:{resource_id}")
        if screen.license_state == "RESTRICTED":
            hard_fail = True
            findings.append(f"LICENSE_RESTRICTED:{resource_id}")
        elif screen.license_state == "UNKNOWN":
            unknown = True
            findings.append(f"LICENSE_UNKNOWN:{resource_id}")

        if screen.permissions_state == "ELEVATED":
            conditional = True
            findings.append(f"ELEVATED_PERMISSIONS:{resource_id}")
        elif screen.permissions_state == "UNKNOWN":
            unknown = True
            findings.append(f"PERMISSIONS_UNKNOWN:{resource_id}")

        if (
            allowed_network_behaviors is not None
            and screen.network_behavior not in allowed_network_behaviors
        ):
            hard_fail = True
            findings.append(
                f"NETWORK_BEHAVIOR_POLICY_CONFLICT:{resource_id}:{screen.network_behavior}"
            )

        if screen.network_behavior in {"ACTIVE", "TARGET_ACTIVE", "MIXED"}:
            conditional = True
            findings.append(f"TARGET_ACTIVE_OR_MIXED:{resource_id}")
        elif screen.network_behavior == "TARGET_READ_ONLY":
            conditional = True
            findings.append(f"TARGET_READ_ONLY_INTERACTION:{resource_id}")
        elif screen.network_behavior == "THIRD_PARTY_API_READ_ONLY":
            findings.append(f"THIRD_PARTY_API_READ_ONLY:{resource_id}")
        elif screen.network_behavior == "UNKNOWN":
            unknown = True
            findings.append(f"NETWORK_BEHAVIOR_UNKNOWN:{resource_id}")

        if screen.credential_requirement == "REQUIRED":
            credentialed_resources += 1
            conditional = True
            findings.append(f"CREDENTIAL_REQUIRED:{resource_id}")
        elif screen.credential_requirement == "UNKNOWN":
            unknown = True
            findings.append(f"CREDENTIAL_REQUIREMENT_UNKNOWN:{resource_id}")

        if screen.external_state_change is True:
            conditional = True
            findings.append(f"EXTERNAL_STATE_CHANGE_CAPABLE:{resource_id}")
        elif screen.external_state_change is None:
            unknown = True
            findings.append(f"EXTERNAL_STATE_CHANGE_UNKNOWN:{resource_id}")

        if screen.auditability == "PARTIAL":
            conditional = True
            findings.append(f"AUDITABILITY_PARTIAL:{resource_id}")
        elif screen.auditability == "UNKNOWN":
            unknown = True
            findings.append(f"AUDITABILITY_UNKNOWN:{resource_id}")

        if screen.least_privilege_compatible is False:
            hard_fail = True
            findings.append(f"LEAST_PRIVILEGE_VIOLATION:{resource_id}")
        elif screen.least_privilege_compatible is None:
            unknown = True
            findings.append(f"LEAST_PRIVILEGE_UNKNOWN:{resource_id}")

    if len(selected_resource_ids) > 1 and credentialed_resources:
        conditional = True
        findings.append("CREDENTIAL_PROPAGATION_REVIEW_REQUIRED")

    conflicts = _resource_conflicts(resources, selected_resource_ids)
    if conflicts:
        hard_fail = True
        findings.extend(conflicts)

    findings = sorted(set(findings))
    if hard_fail:
        return "FAIL", findings
    if unknown:
        return "UNKNOWN", findings
    if conditional:
        return "PASS_WITH_CONDITIONS", findings
    return "PASS", findings


def compose_capability_package(
    *,
    profile: DemandProfile,
    broker_requirements: Iterable[BrokerRequirement],
    resources: Iterable[ResourceCandidate],
    assessments: Iterable[SuitabilityAssessment],
    resource_screens: Iterable[ResourceScreen],
    selected_assessment_ids: Iterable[str],
    service_surface_map: dict[str, list[str]] | None = None,
) -> CapabilityPackage:
    if profile.authority_effect != "NONE":
        raise ValueError("demand profile cannot grant package authority")

    requirements = {row.requirement_id: row for row in broker_requirements}
    resource_by_id = {row.resource_id: row for row in resources}
    assessment_by_id = {row.assessment_id: row for row in assessments}
    screen_by_resource = {row.resource_id: row for row in resource_screens}
    selected_ids = sorted({str(value).strip() for value in selected_assessment_ids if str(value).strip()})
    surface_map = dict(service_surface_map or {})

    if not requirements:
        raise ValueError("capability package requires broker requirements")
    if not selected_ids:
        raise ValueError("capability package requires selected suitability assessments")

    for requirement in requirements.values():
        if requirement.opportunity_id != profile.opportunity_id:
            raise ValueError("broker requirement is not bound to demand opportunity")
        if not requirement.demand_requirement_id:
            raise ValueError("broker requirement lacks exact DMR lineage")
        demand_row = next(
            (
                row
                for row in profile.requirements
                if row.demand_requirement_id == requirement.demand_requirement_id
            ),
            None,
        )
        if demand_row is None:
            raise ValueError("broker requirement references unknown DMR")
        if demand_row.mode != requirement.demand_mode:
            raise ValueError("broker requirement demand mode does not match DMR")
        if demand_row.semantic_class != requirement.demand_semantic_class:
            raise ValueError("broker requirement semantic class does not match DMR")
        if not demand_row.brokerable:
            raise ValueError("non-brokerable DMR cannot enter capability package")

    selected: list[SuitabilityAssessment] = []
    for assessment_id in selected_ids:
        assessment = assessment_by_id.get(assessment_id)
        if assessment is None:
            raise ValueError(f"unknown selected suitability assessment: {assessment_id}")
        requirement = requirements.get(assessment.requirement_id)
        if requirement is None:
            raise ValueError("selected suitability assessment references unknown BRQ")
        resource = resource_by_id.get(assessment.resource_id)
        if resource is None:
            raise ValueError("selected suitability assessment references missing resource")
        normalize_surface_classes(list(resource.service_surface_classes or []))
        if assessment.opportunity_id != profile.opportunity_id:
            raise ValueError("selected suitability assessment opportunity mismatch")
        if assessment.resource_sha256 != _canonical_sha256(resource.to_dict()):
            raise ValueError("selected suitability assessment resource digest is stale")
        screen = screen_by_resource.get(assessment.resource_id)
        if screen is None:
            raise ValueError("selected suitability assessment lacks current resource screen")
        if assessment.screen_id != screen.screen_id:
            raise ValueError("selected suitability assessment screen lineage is stale")
        selected.append(assessment)

    bindings: list[PackageRequirementBinding] = []
    required_total = 0
    required_adequate = 0
    nonrequired_total = 0
    nonrequired_covered = 0
    uncovered_required: list[str] = []
    partial_required: list[str] = []
    uncovered_nonrequired: list[str] = []
    all_surface_classes: set[str] = set()

    for requirement in sorted(requirements.values(), key=lambda row: row.requirement_id):
        rows = [
            assessment
            for assessment in selected
            if assessment.requirement_id == requirement.requirement_id
        ]
        coverage = _coverage_for_assessments(rows)
        surfaces = normalize_surface_classes(
            list(surface_map.get(requirement.requirement_id, []))
        )
        all_surface_classes.update(surfaces)

        evidence = _dedupe_evidence(
            [
                *requirement.evidence,
                *(item for row in rows for item in row.evidence),
            ]
        )
        resource_ids = sorted({row.resource_id for row in rows})
        assessment_ids = sorted({row.assessment_id for row in rows})

        mode = requirement.demand_mode or "REQUIRED"
        if mode == "REQUIRED":
            required_total += 1
            if coverage == "ADEQUATE":
                required_adequate += 1
            elif coverage == "PARTIAL":
                partial_required.append(requirement.demand_requirement_id)
                uncovered_required.append(requirement.demand_requirement_id)
            else:
                uncovered_required.append(requirement.demand_requirement_id)
        else:
            nonrequired_total += 1
            if coverage == "ADEQUATE":
                nonrequired_covered += 1
            elif coverage in {"UNRESOLVED", "UNKNOWN", "PARTIAL"}:
                uncovered_nonrequired.append(requirement.demand_requirement_id)

        bindings.append(
            PackageRequirementBinding(
                demand_requirement_id=requirement.demand_requirement_id,
                broker_requirement_id=requirement.requirement_id,
                demand_mode=mode,
                demand_semantic_class=requirement.demand_semantic_class,
                selected_assessment_ids=assessment_ids,
                selected_resource_ids=resource_ids,
                coverage_state=coverage,
                service_surface_classes=surfaces,
                evidence=evidence,
            )
        )

    required_coverage_state = (
        "COMPLETE"
        if required_total == required_adequate
        else "INCOMPLETE"
    )

    selected_resource_ids = sorted({row.resource_id for row in selected})
    allowed_network_behaviors_raw = profile.source_metadata.get(
        "allowed_network_behaviors"
    )
    allowed_network_behaviors = (
        {
            str(value).strip().upper()
            for value in allowed_network_behaviors_raw
            if str(value).strip()
        }
        if isinstance(allowed_network_behaviors_raw, list)
        else None
    )
    screen_state, findings = _screen_package(
        selected_resource_ids=selected_resource_ids,
        resources=resource_by_id,
        resource_screens=screen_by_resource,
        required_coverage_state=required_coverage_state,
        allowed_network_behaviors=allowed_network_behaviors,
    )
    suitability_ids = sorted({row.assessment_id for row in selected})
    evidence = _dedupe_evidence(
        [
            *profile.evidence,
            *(item for row in bindings for item in row.evidence),
        ]
    )

    serialized_bindings = [row.to_dict() for row in bindings]
    identity_payload = {
        "schema": "humanaios.capability-package.v1",
        "opportunity_id": profile.opportunity_id,
        "demand_profile_id": profile.profile_id,
        "bindings": serialized_bindings,
        "resource_ids": selected_resource_ids,
        "suitability_ids": suitability_ids,
        "service_surface_classes": sorted(all_surface_classes),
    }
    package_id = _stable_id("CPK", identity_payload)
    serialized_payload = {
        **identity_payload,
        "package_id": package_id,
        "required_coverage_state": required_coverage_state,
        "required_requirement_count": required_total,
        "required_adequately_covered_count": required_adequate,
        "nonrequired_requirement_count": nonrequired_total,
        "nonrequired_covered_count": nonrequired_covered,
        "uncovered_required_requirement_ids": sorted(set(uncovered_required)),
        "partial_required_requirement_ids": sorted(set(partial_required)),
        "uncovered_nonrequired_requirement_ids": sorted(set(uncovered_nonrequired)),
        "composition_screen_state": screen_state,
        "composition_findings": findings,
        "authorization_state": "NOT_REQUESTED",
        "target_scope_state": "NOT_ESTABLISHED",
        "method_permission_state": "NOT_ESTABLISHED",
        "evidence": evidence,
        "authority_effect": "NONE",
    }
    return CapabilityPackage(
        schema="humanaios.capability-package.v1",
        package_id=package_id,
        opportunity_id=profile.opportunity_id,
        demand_profile_id=profile.profile_id,
        bindings=bindings,
        resource_ids=selected_resource_ids,
        suitability_ids=suitability_ids,
        service_surface_classes=sorted(all_surface_classes),
        required_coverage_state=required_coverage_state,
        required_requirement_count=required_total,
        required_adequately_covered_count=required_adequate,
        nonrequired_requirement_count=nonrequired_total,
        nonrequired_covered_count=nonrequired_covered,
        uncovered_required_requirement_ids=sorted(set(uncovered_required)),
        partial_required_requirement_ids=sorted(set(partial_required)),
        uncovered_nonrequired_requirement_ids=sorted(set(uncovered_nonrequired)),
        composition_screen_state=screen_state,
        composition_findings=findings,
        authorization_state="NOT_REQUESTED",
        target_scope_state="NOT_ESTABLISHED",
        method_permission_state="NOT_ESTABLISHED",
        evidence=evidence,
        authority_effect="NONE",
        package_sha256=_canonical_sha256(serialized_payload),
    )


def capability_package_from_dict(data: dict[str, Any]) -> CapabilityPackage:
    expected = {
        "schema",
        "package_id",
        "opportunity_id",
        "demand_profile_id",
        "bindings",
        "resource_ids",
        "suitability_ids",
        "service_surface_classes",
        "required_coverage_state",
        "required_requirement_count",
        "required_adequately_covered_count",
        "nonrequired_requirement_count",
        "nonrequired_covered_count",
        "uncovered_required_requirement_ids",
        "partial_required_requirement_ids",
        "uncovered_nonrequired_requirement_ids",
        "composition_screen_state",
        "composition_findings",
        "authorization_state",
        "target_scope_state",
        "method_permission_state",
        "evidence",
        "authority_effect",
        "package_sha256",
    }
    keys = set(data)
    if keys != expected:
        raise ValueError(
            f"capability package shape mismatch; missing={sorted(expected-keys)}; "
            f"extra={sorted(keys-expected)}"
        )

    payload = dict(data)
    supplied_hash = str(payload.pop("package_sha256") or "")
    expected_hash = _canonical_sha256(payload)
    if supplied_hash != expected_hash:
        raise ValueError("capability package hash mismatch")

    bindings = [
        PackageRequirementBinding(**row)
        for row in data["bindings"]
    ]
    package = CapabilityPackage(
        **{
            **data,
            "bindings": bindings,
        }
    )
    if package.schema != "humanaios.capability-package.v1":
        raise ValueError("unsupported capability package schema")
    if package.authority_effect != "NONE":
        raise ValueError("capability package cannot grant authority")
    if package.authorization_state != "NOT_REQUESTED":
        raise ValueError("capability package cannot carry authorization state")
    if package.target_scope_state != "NOT_ESTABLISHED":
        raise ValueError("service surface classification cannot establish target scope")
    if package.method_permission_state != "NOT_ESTABLISHED":
        raise ValueError("capability package cannot establish method permission")
    normalize_surface_classes(package.service_surface_classes)
    return package
