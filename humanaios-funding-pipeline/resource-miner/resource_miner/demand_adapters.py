from __future__ import annotations

import re
from typing import Any, Iterable

from .broker import BrokerOpportunity, build_opportunity
from .demand import (
    DemandProfile,
    DemandRequirementRecord,
    build_demand_profile,
    make_demand_requirement,
)
from .models import EvidenceRef


def _ev(url: str, observed_at: str, claim: str) -> list[EvidenceRef]:
    return [EvidenceRef(url=url, kind="source", observed_at=observed_at, claim=claim)]


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            if isinstance(item, dict):
                text = (
                    item.get("description")
                    or item.get("name")
                    or item.get("title")
                    or item.get("value")
                    or ""
                )
            else:
                text = str(item)
            if str(text).strip():
                out.append(str(text).strip())
        return out
    if str(value).strip():
        return [str(value).strip()]
    return []


def _profile_bundle(
    *,
    title: str,
    source_kind: str,
    source_identity: str,
    source_url: str,
    sponsor: str,
    objective: str,
    requirements: Iterable[DemandRequirementRecord],
    evidence: list[EvidenceRef],
    **profile_kwargs: Any,
) -> tuple[BrokerOpportunity, DemandProfile]:
    opportunity = build_opportunity(
        title=title,
        source_kind=source_kind,
        source_url=source_url,
        sponsor=sponsor,
        evidence=evidence,
    )
    profile = build_demand_profile(
        opportunity=opportunity,
        source_kind=source_kind,
        source_identity=source_identity,
        source_url=source_url,
        objective=objective,
        requirements=requirements,
        evidence=evidence,
        **profile_kwargs,
    )
    return opportunity, profile


def adapt_github_issue(
    issue: dict[str, Any],
    *,
    repository: str,
    observed_at: str,
) -> tuple[BrokerOpportunity, DemandProfile]:
    number = int(issue["number"])
    title = str(issue.get("title") or f"Issue #{number}").strip()
    body = str(issue.get("body") or "")
    source_url = str(
        issue.get("html_url")
        or f"https://github.com/{repository}/issues/{number}"
    )
    evidence = _ev(
        source_url,
        observed_at,
        "GitHub issue content was observed as an external/internal work-demand source.",
    )

    checklist = [
        match.group(1).strip()
        for match in re.finditer(r"(?m)^\s*[-*]\s*\[\s*\]\s+(.+)$", body)
        if match.group(1).strip()
    ]
    requirements: list[DemandRequirementRecord] = []
    for item in checklist:
        requirements.append(
            make_demand_requirement(
                label=item[:120],
                mode="REQUIRED",
                semantic_class="DELIVERABLE",
                statement=item,
                evidence=evidence,
                required_affordances=["software_delivery"],
                allowed_resource_types=[
                    "open_source_tool",
                    "external_service",
                    "human_expert",
                    "software_asset",
                ],
                source_locator=f"{source_url}#issue-body",
            )
        )
    if not requirements:
        requirements.append(
            make_demand_requirement(
                label=title[:120],
                mode="REQUIRED",
                semantic_class="CAPABILITY",
                statement=body.strip() or title,
                evidence=evidence,
                required_affordances=["software_engineering"],
                allowed_resource_types=[
                    "open_source_tool",
                    "external_service",
                    "human_expert",
                    "software_asset",
                ],
                source_locator=f"{source_url}#issue-body",
            )
        )

    labels = sorted(
        {
            str(label.get("name") if isinstance(label, dict) else label).strip()
            for label in (issue.get("labels") or [])
            if str(label.get("name") if isinstance(label, dict) else label).strip()
        }
    )
    milestone = issue.get("milestone") or {}
    constraints = [f"label:{label}" for label in labels]
    if isinstance(milestone, dict) and milestone.get("title"):
        constraints.append(f"milestone:{milestone['title']}")

    closing_refs = sorted(
        {
            match.group(1)
            for match in re.finditer(
                r"(?i)\b(?:fixes|closes|resolves)\s+(?:[\w.-]+/[\w.-]+)?#(\d+)\b",
                body,
            )
        }
    )
    return _profile_bundle(
        title=title,
        source_kind="GITHUB_ISSUE",
        source_identity=f"{repository}#{number}",
        source_url=source_url,
        sponsor=repository,
        objective=title,
        requirements=requirements,
        evidence=evidence,
        constraints=constraints,
        deliverables=checklist,
        submission_surface=source_url,
        source_metadata={
            "repository": repository,
            "issue_number": number,
            "state": str(issue.get("state") or "unknown"),
            "labels": labels,
            "closing_issue_references": closing_refs,
            "work_authorized": False,
        },
    )


def adapt_grants_gov(
    payload: dict[str, Any],
    *,
    observed_at: str,
    source_url: str = "https://api.grants.gov/v1/api/fetchOpportunity",
) -> tuple[BrokerOpportunity, DemandProfile]:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    synopsis = data.get("synopsis") or {}
    opportunity_number = str(data.get("opportunityNumber") or data.get("id") or "").strip()
    title = str(data.get("opportunityTitle") or "Grants.gov opportunity").strip()
    agency = str(
        synopsis.get("agencyName")
        or (data.get("agencyDetails") or {}).get("agencyName")
        or data.get("owningAgencyCode")
        or "Federal agency"
    ).strip()
    identity = opportunity_number or str(data.get("id") or title)
    evidence = _ev(
        source_url,
        observed_at,
        "Grants.gov opportunity detail was observed from the official opportunity record.",
    )

    applicant_types = _string_list(synopsis.get("applicantTypes"))
    requirements: list[DemandRequirementRecord] = []
    for applicant in applicant_types:
        requirements.append(
            make_demand_requirement(
                label=f"Applicant eligibility — {applicant}"[:120],
                mode="REQUIRED",
                semantic_class="ELIGIBILITY",
                statement=f"Applicant must satisfy Grants.gov applicant type: {applicant}",
                evidence=evidence,
                brokerable=False,
                source_locator=source_url,
            )
        )

    deliverables = _string_list(data.get("deliverables"))
    for item in deliverables:
        requirements.append(
            make_demand_requirement(
                label=item[:120],
                mode="REQUIRED",
                semantic_class="DELIVERABLE",
                statement=item,
                evidence=evidence,
                required_affordances=["project_delivery"],
                allowed_resource_types=[
                    "human_expert",
                    "open_source_tool",
                    "external_service",
                    "research_access",
                ],
                source_locator=source_url,
            )
        )

    synopsis_desc = str(synopsis.get("synopsisDesc") or data.get("description") or "").strip()
    if not deliverables:
        requirements.append(
            make_demand_requirement(
                label="Grant project execution",
                mode="REQUIRED",
                semantic_class="CAPABILITY",
                statement=synopsis_desc or title,
                evidence=evidence,
                required_affordances=["project_execution"],
                allowed_resource_types=[
                    "human_expert",
                    "open_source_tool",
                    "external_service",
                    "research_access",
                    "compute_credit",
                ],
                source_locator=source_url,
            )
        )

    if bool(synopsis.get("costSharing")):
        requirements.append(
            make_demand_requirement(
                label="Cost sharing",
                mode="CONDITIONAL",
                semantic_class="CONSTRAINT",
                statement="Opportunity indicates cost sharing is required or applicable.",
                evidence=evidence,
                brokerable=False,
                source_locator=source_url,
            )
        )

    instruments = _string_list(synopsis.get("fundingInstruments"))
    activities = _string_list(synopsis.get("fundingActivityCategories"))
    value_signals = []
    if synopsis.get("awardFloor") is not None:
        value_signals.append(f"award_floor:{synopsis.get('awardFloor')}")
    if synopsis.get("awardCeiling") is not None:
        value_signals.append(f"award_ceiling:{synopsis.get('awardCeiling')}")

    return _profile_bundle(
        title=title,
        source_kind="GRANTS_GOV",
        source_identity=identity,
        source_url=source_url,
        sponsor=agency,
        objective=synopsis_desc or title,
        requirements=requirements,
        evidence=evidence,
        deadline=str(
            synopsis.get("responseDate")
            or synopsis.get("responseDateDesc")
            or data.get("closeDate")
            or ""
        ).strip()
        or None,
        constraints=[
            *(f"funding_instrument:{x}" for x in instruments),
            *(f"funding_activity:{x}" for x in activities),
        ],
        eligibility_predicates=applicant_types,
        deliverables=deliverables,
        value_signals=value_signals,
        submission_surface=str(data.get("assistURL") or "Grants.gov"),
        source_metadata={
            "opportunity_number": opportunity_number,
            "agency": agency,
            "cost_sharing": bool(synopsis.get("costSharing")),
            "applicant_eligibility_separate_from_capability": True,
        },
    )


def adapt_sam_procurement(
    record: dict[str, Any],
    *,
    observed_at: str,
    source_url: str,
) -> tuple[BrokerOpportunity, DemandProfile]:
    notice_id = str(
        record.get("noticeId")
        or record.get("solicitationNumber")
        or record.get("id")
        or ""
    ).strip()
    title = str(record.get("title") or "SAM.gov contract opportunity").strip()
    agency = str(
        record.get("department")
        or record.get("fullParentPathName")
        or record.get("agency")
        or "Federal contracting office"
    ).strip()
    evidence = _ev(
        source_url,
        observed_at,
        "SAM.gov public contract-opportunity record was observed.",
    )

    requirements: list[DemandRequirementRecord] = []
    mandatory = _string_list(record.get("mandatory_requirements"))
    for item in mandatory:
        requirements.append(
            make_demand_requirement(
                label=item[:120],
                mode="REQUIRED",
                semantic_class="CAPABILITY",
                statement=item,
                evidence=evidence,
                required_affordances=["contract_delivery"],
                allowed_resource_types=[
                    "human_expert",
                    "open_source_tool",
                    "external_service",
                    "software_asset",
                    "hardware_access",
                ],
                source_locator=source_url,
            )
        )
    deliverables = _string_list(record.get("deliverables"))
    for item in deliverables:
        requirements.append(
            make_demand_requirement(
                label=item[:120],
                mode="REQUIRED",
                semantic_class="DELIVERABLE",
                statement=item,
                evidence=evidence,
                required_affordances=["contract_delivery"],
                allowed_resource_types=[
                    "human_expert",
                    "open_source_tool",
                    "external_service",
                    "software_asset",
                    "hardware_access",
                ],
                source_locator=source_url,
            )
        )
    if not requirements:
        requirements.append(
            make_demand_requirement(
                label="Statement of work capability",
                mode="REQUIRED",
                semantic_class="CAPABILITY",
                statement=str(record.get("description") or title),
                evidence=evidence,
                required_affordances=["contract_delivery"],
                allowed_resource_types=[
                    "human_expert",
                    "open_source_tool",
                    "external_service",
                    "software_asset",
                ],
                source_locator=source_url,
            )
        )

    set_aside = str(
        record.get("typeOfSetAsideDescription")
        or record.get("setAside")
        or ""
    ).strip()
    if set_aside:
        requirements.append(
            make_demand_requirement(
                label=f"Set-aside eligibility — {set_aside}"[:120],
                mode="REQUIRED",
                semantic_class="ELIGIBILITY",
                statement=f"Offeror must satisfy set-aside condition: {set_aside}",
                evidence=evidence,
                brokerable=False,
                source_locator=source_url,
            )
        )

    prohibitions = _string_list(record.get("prohibitions"))
    for item in prohibitions:
        requirements.append(
            make_demand_requirement(
                label=item[:120],
                mode="PROHIBITED",
                semantic_class="PROHIBITION",
                statement=item,
                evidence=evidence,
                brokerable=False,
                source_locator=source_url,
            )
        )

    constraints = []
    if record.get("naicsCode"):
        constraints.append(f"NAICS:{record['naicsCode']}")
    if set_aside:
        constraints.append(f"set_aside:{set_aside}")
    place = record.get("placeOfPerformance")
    if place:
        constraints.append(f"place_of_performance:{place}")

    return _profile_bundle(
        title=title,
        source_kind="SAM_PROCUREMENT",
        source_identity=notice_id or title,
        source_url=source_url,
        sponsor=agency,
        objective=str(record.get("description") or title),
        requirements=requirements,
        evidence=evidence,
        deadline=str(record.get("responseDeadLine") or record.get("responseDeadline") or "").strip() or None,
        constraints=constraints,
        eligibility_predicates=[set_aside] if set_aside else [],
        prohibitions=prohibitions,
        deliverables=deliverables,
        submission_surface=str(record.get("submission_url") or source_url),
        source_metadata={
            "notice_type": str(record.get("type") or ""),
            "solicitation_number": str(record.get("solicitationNumber") or ""),
            "mandatory_requirement_count": len(mandatory),
            "mandatory_requirements_are_not_averageable": True,
        },
    )


def adapt_federal_challenge(
    record: dict[str, Any],
    *,
    observed_at: str,
    source_url: str,
) -> tuple[BrokerOpportunity, DemandProfile]:
    identity = str(record.get("challenge_id") or record.get("id") or record.get("title") or "").strip()
    title = str(record.get("title") or "Federal challenge/prize").strip()
    sponsor = str(record.get("agency") or record.get("sponsor") or "Federal agency").strip()
    evidence = _ev(
        source_url,
        observed_at,
        "Federal challenge/prize rules were observed from the agency/public source.",
    )
    requirements: list[DemandRequirementRecord] = []

    eligibility = _string_list(record.get("eligibility"))
    for item in eligibility:
        requirements.append(
            make_demand_requirement(
                label=item[:120],
                mode="REQUIRED",
                semantic_class="ELIGIBILITY",
                statement=item,
                evidence=evidence,
                brokerable=False,
                source_locator=source_url,
            )
        )

    deliverables = _string_list(record.get("deliverables"))
    for item in deliverables:
        requirements.append(
            make_demand_requirement(
                label=item[:120],
                mode="REQUIRED",
                semantic_class="DELIVERABLE",
                statement=item,
                evidence=evidence,
                required_affordances=["submission_artifact"],
                allowed_resource_types=[
                    "human_expert",
                    "open_source_tool",
                    "external_service",
                    "software_asset",
                    "hardware_access",
                ],
                source_locator=source_url,
            )
        )

    criteria_out: list[dict[str, Any]] = []
    for criterion in record.get("evaluation_criteria") or []:
        label = str(criterion.get("label") or criterion.get("name") or "Evaluation criterion").strip()
        weight = criterion.get("weight")
        if weight is None:
            requirements.append(
                make_demand_requirement(
                    label=label[:120],
                    mode="PREFERRED",
                    semantic_class="EVALUATION",
                    statement=str(criterion.get("description") or label),
                    evidence=evidence,
                    brokerable=False,
                    source_locator=source_url,
                )
            )
        else:
            numeric_weight = float(weight)
            requirements.append(
                make_demand_requirement(
                    label=label[:120],
                    mode="SCORED",
                    semantic_class="EVALUATION",
                    statement=str(criterion.get("description") or label),
                    evidence=evidence,
                    score_weight=numeric_weight,
                    brokerable=False,
                    source_locator=source_url,
                )
            )
        criteria_out.append(
            {
                "label": label,
                "weight": weight,
                "description": str(criterion.get("description") or ""),
            }
        )

    if not requirements:
        requirements.append(
            make_demand_requirement(
                label="Challenge solution",
                mode="REQUIRED",
                semantic_class="DELIVERABLE",
                statement=str(record.get("objective") or title),
                evidence=evidence,
                required_affordances=["submission_artifact"],
                allowed_resource_types=["human_expert", "open_source_tool", "external_service"],
                source_locator=source_url,
            )
        )

    prohibitions = _string_list(record.get("prohibitions"))
    for item in prohibitions:
        requirements.append(
            make_demand_requirement(
                label=item[:120],
                mode="PROHIBITED",
                semantic_class="PROHIBITION",
                statement=item,
                evidence=evidence,
                brokerable=False,
                source_locator=source_url,
            )
        )

    constraints = _string_list(record.get("rules"))
    ip_terms = str(record.get("ip_terms") or "").strip()
    if ip_terms:
        constraints.append(f"IP:{ip_terms}")

    value_signals = [str(x) for x in _string_list(record.get("prizes"))]
    return _profile_bundle(
        title=title,
        source_kind="FEDERAL_CHALLENGE",
        source_identity=identity or title,
        source_url=source_url,
        sponsor=sponsor,
        objective=str(record.get("objective") or title),
        requirements=requirements,
        evidence=evidence,
        deadline=str(record.get("submission_deadline") or "").strip() or None,
        constraints=constraints,
        eligibility_predicates=eligibility,
        prohibitions=prohibitions,
        deliverables=deliverables,
        evaluation_criteria=criteria_out,
        value_signals=value_signals,
        submission_surface=str(record.get("submission_url") or source_url),
        source_metadata={
            "legacy_challenge_gov_portal": False,
            "challenge_gov_sunset_date": "2026-03-30",
            "current_discovery_model": "USA_GOV_OR_AGENCY_SITE",
        },
    )


def adapt_compliance_demand(
    record: dict[str, Any],
    *,
    observed_at: str,
    source_url: str,
) -> tuple[BrokerOpportunity, DemandProfile]:
    identity = str(record.get("control_set_id") or record.get("id") or record.get("title") or "").strip()
    title = str(record.get("title") or "Compliance/control demand").strip()
    evidence = _ev(
        source_url,
        observed_at,
        "Policy/control requirement set was observed as a non-economic demand source.",
    )
    operator_modes = {
        "MUST": "REQUIRED",
        "SHALL": "REQUIRED",
        "MUST NOT": "PROHIBITED",
        "SHALL NOT": "PROHIBITED",
        "SHOULD": "PREFERRED",
        "MAY": "OPTIONAL",
        "IF": "CONDITIONAL",
        "WHEN": "CONDITIONAL",
    }
    requirements: list[DemandRequirementRecord] = []
    prohibitions: list[str] = []
    for item in record.get("requirements") or []:
        operator = str(item.get("operator") or "MUST").strip().upper()
        mode = operator_modes.get(operator)
        if mode is None:
            raise ValueError(f"unsupported compliance normative operator: {operator}")
        weight = item.get("weight")
        if weight is not None:
            mode = "SCORED"
        statement = str(item.get("statement") or "").strip()
        if not statement:
            raise ValueError("compliance requirement missing statement")
        semantic_class = "PROHIBITION" if mode == "PROHIBITED" else "COMPLIANCE_CONTROL"
        brokerable = mode != "PROHIBITED"
        affordances = _string_list(item.get("required_affordances"))
        if brokerable and not affordances:
            affordances = ["compliance_control"]
        requirements.append(
            make_demand_requirement(
                label=str(item.get("label") or statement)[:120],
                mode=mode,
                semantic_class=semantic_class,
                statement=statement,
                evidence=evidence,
                required_affordances=affordances if brokerable else [],
                allowed_resource_types=_string_list(item.get("allowed_resource_types"))
                or ["open_source_tool", "external_service", "human_expert", "software_asset"],
                condition=str(item.get("condition") or ""),
                score_weight=float(weight) if weight is not None else None,
                brokerable=brokerable,
                source_locator=str(item.get("source_locator") or source_url),
            )
        )
        if mode == "PROHIBITED":
            prohibitions.append(statement)

    return _profile_bundle(
        title=title,
        source_kind="COMPLIANCE_CONTROL_SET",
        source_identity=identity or title,
        source_url=source_url,
        sponsor=str(record.get("issuer") or "Policy authority"),
        objective=str(record.get("objective") or title),
        requirements=requirements,
        evidence=evidence,
        prohibitions=prohibitions,
        submission_surface="",
        source_metadata={
            "economic_opportunity": False,
            "control_match_is_not_compliance_verified": True,
        },
    )
