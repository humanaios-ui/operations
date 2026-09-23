from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class ResearchTask:
    task_id: str
    title: str
    purpose: str
    authority: str
    source_url: str
    inputs_required: list[str]
    success_evidence: list[str]
    depends_on: list[str]
    priority: int
    evidence_state: str = "UNTESTED"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def genealogy_tasks(genealogy: dict[str, Any] | None) -> list[ResearchTask]:
    if not genealogy or not genealogy.get("genealogy_research_relevant"):
        return []
    tasks = [
        ResearchTask(
            "GEN-01", "Resolve candidate ancestor against authoritative Dawes records",
            "Determine whether a direct ancestor has an identity-resolved Cherokee Dawes enrollment record; same-name matches are insufficient.",
            "National Archives / authoritative Dawes records",
            "https://www.archives.gov/research/native-americans/dawes",
            ["Ancestor full name and variants", "Approximate birth date", "Known relatives", "Known residence/location"],
            ["Enrollment/census card identifier", "Identity predicates linking record to the direct ancestor"], [], 1,
        ),
        ResearchTask(
            "GEN-02", "Retrieve enrollment packet and allotment evidence if GEN-01 resolves",
            "Establish whether the resolved enrollee received an allotment and extract the exact legal description.",
            "National Archives",
            "https://www.archives.gov/research/native-americans/dawes",
            ["Resolved Dawes enrollment number / census card"],
            ["Enrollment packet", "Allotment jacket", "Legal land description or explicit no-allotment evidence"], ["GEN-01"], 2,
        ),
        ResearchTask(
            "GEN-03", "Trace title and probate succession",
            "Determine whether an historical allotment produced any present trust/restricted interest through the actual chain of title and probate.",
            "BIA Land Titles and Records / Probate",
            "https://www.bia.gov/service/land-title-services",
            ["Legal land description", "Allottee identity", "Known descendant/probate chain"],
            ["Title Status Report or equivalent title evidence", "Probate orders / heirship evidence", "Current ownership status"], ["GEN-02"], 3,
        ),
        ResearchTask(
            "GEN-04", "Verify associated IIM or estate trust funds",
            "Determine whether an agency-recognized beneficiary or estate account exists after identity/title/probate evidence supports the inquiry.",
            "Bureau of Trust Funds Administration",
            "https://www.doi.gov/ost/iim-accounts",
            ["Verified beneficiary/estate identity", "Tribal affiliation", "Probate/title evidence when applicable"],
            ["BTFA verification of account or explicit negative result", "Required beneficiary action"], ["GEN-03"], 4,
        ),
    ]
    return tasks


def tasks_from_results(results: list[dict[str, Any]], genealogy_patch: dict[str, Any] | None = None, profile: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    tasks: list[ResearchTask] = []
    specialized_genealogy_ids = {"BTFA-IIM-UNCLAIMED", "BIA-TRUST-PROBATE", "NARA-DAWES-ALLOTMENT"}
    for r in results:
        if r["status"] in {"INELIGIBLE", "CLOSED_HISTORICAL"}:
            continue
        if genealogy_patch and genealogy_patch.get("genealogy_research_relevant") and r["program_id"] in specialized_genealogy_ids:
            continue
        if not r.get("sources"):
            continue
        src = r["sources"][0]
        tasks.append(ResearchTask(
            task_id=f"VERIFY-{r['program_id']}",
            title=f"Verify and advance: {r['title']}",
            purpose=f"Resolve remaining evidence and confirm the current authoritative application path for status {r['status']}.",
            authority=src.get("label", "Authoritative program source"),
            source_url=src.get("url", ""),
            inputs_required=r.get("required_evidence", []),
            success_evidence=["Current application/claim path verified", "Eligibility blockers resolved or documented", "Submission-ready evidence checklist"],
            depends_on=[],
            priority=10 + int(r.get("sort_priority", 100)),
        ))
    tasks.extend(genealogy_tasks(genealogy_patch))
    profile = profile or {}
    goals = set(profile.get("funding_goals") or [])
    roles = set(profile.get("applicant_roles") or [])
    if "Grants / general funding" in goals or goals or roles:
        tasks.append(ResearchTask(
            "DISCOVERY-ALN", "Search federal Assistance Listings for non-grant benefits and assistance",
            "Expand discovery beyond open grants to federal loans, scholarships, insurance, direct payments, services, and other assistance types without asserting eligibility until the listing rules are tested.",
            "SAM.gov Assistance Listings", "https://sam.gov/assistance-listings",
            ["Applicant entity type", "Purpose / use of funds", "Location", "Material eligibility characteristics relevant to the listing"],
            ["Candidate Assistance Listing number", "Authoritative applicant eligibility text", "Current administering agency and application path"], [], 8,
        ))
    if "Grants / general funding" in goals or goals or roles:
        tasks.append(ResearchTask(
            "DISCOVERY-LOCAL-FUNDING", "Search the canonical HumanAIOS funding dataset",
            "Search the existing curated funding pipeline before external discovery; treat its tags as routing metadata, not proof of eligibility.",
            "HumanAIOS Funding & Resource Pipeline", "humanaios-funding-pipeline/data/sources.json",
            ["Applicant entity type", "Funding objective", "Material eligibility characteristics"],
            ["Candidate source record", "Current source URL", "Opportunity-specific eligibility text queued for verification"], [], 7,
        ))
    if "Grants / general funding" in goals or roles.intersection({"Business", "Nonprofit", "Student", "Farmer / rancher"}):
        tasks.append(ResearchTask(
            "DISCOVERY-GRANTS", "Search current Grants.gov opportunities",
            "Find posted or forecasted federal grant opportunities, then parse each opportunity's applicant eligibility before calling it a match.",
            "Grants.gov", "https://www.grants.gov/search-grants",
            ["Search objective", "Applicant entity type", "Program area / keywords"],
            ["Opportunity number", "Applicant eligibility categories", "Close date", "Required attachments and submission route"], [], 9,
        ))
    # Dedupe, favor specialized task when identifiers collide.
    dedup: dict[str, ResearchTask] = {t.task_id: t for t in tasks}
    return [t.to_dict() for t in sorted(dedup.values(), key=lambda t: (t.priority, t.task_id))]
