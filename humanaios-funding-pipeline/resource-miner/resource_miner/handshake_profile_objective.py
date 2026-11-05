"""Private Handshake-wide summary and skills proposals from owner master + PERs.

No live Handshake access, role-specific job tailoring, external writes, or
biographical claims inferred from job descriptions. PERs are source-linked
candidate evidence, not independent employment verification.
"""
from __future__ import annotations

import json
import re
from typing import Any

from .private_profile_bridge import _git_file, SEED_REPO

PER_SOURCE = "humanaios-funding-pipeline/resource-miner/data/project_evidence_records.seed.json"
PROFILE_OBJECTIVE = "HANDSHAKE_GENERAL_PROFILE"
_ALLOWED_STATE = "SOURCE_SUPPORTED"
_MAX_SKILLS = 10
_STOP = {"the", "and", "for", "with", "from", "systems", "system", "design", "work", "of", "in"}
# Labels are controlled translations; each requires an actual SOURCE_SUPPORTED
# claim and a matching employer in the owner's private master.
_SUMMARY_FAMILIES = (
    ("patient_safety", "hospital patient safety", ("patient safety", "patient-safety")),
    ("quality_data", "healthcare data validation", ("data integrity", "data validation", "migrated data")),
    ("regulatory", "regulatory quality audits", ("regulatory audits", "cap and clia", "iso, cap, and clia")),
    ("ai_research", "AI evaluation research", ("ai evaluation", "ai calibration", "acat")),
    ("programs", "cross-functional program delivery", ("interdepartmental", "cross-functional", "program implementation")),
)
_SKILL_ALIASES = {
    "analysis": ("analytical", "analytics", "analysis"),
    "audit": ("audits", "auditing", "audit"),
    "management": ("managed", "managing", "management"),
    "validation": ("validated", "validate", "validation"),
    "quality": ("quality",),
    "operations": ("operations", "operational"),
    "improvement": ("improvement", "improved"),
    "research": ("research",),
    "data": ("data",),
    "safety": ("safety",),
    "regulatory": ("regulatory",),
    "leadership": ("led", "leader", "leadership"),
    "risk": ("risk",),
}


def load_project_evidence(operations_checkout: str) -> tuple[list[dict[str, Any]], str]:
    """Read committed exact-path PER seed through PR #1029's pinned-origin gate."""
    revision, raw = _git_file(operations_checkout, SEED_REPO, PER_SOURCE)
    records = json.loads(raw)
    if not isinstance(records, list) or len(records) > 100:
        raise ValueError("invalid or oversized PER source")
    for row in records:
        if not isinstance(row, dict) or not isinstance(row.get("project_id"), str):
            raise ValueError("invalid PER row")
        if not re.fullmatch(r"PER-[A-Z0-9-]{3,120}", row["project_id"]):
            raise ValueError("invalid PER identity")
        if not isinstance(row.get("organization"), str) or not isinstance(row.get("evidence"), list):
            raise ValueError("incomplete PER source")
    if len({row["project_id"] for row in records}) != len(records):
        raise ValueError("duplicated PER identity")
    return records, revision


def _terms(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]{3,}", value.lower())) - _STOP


def _evidence_for_master(master: dict[str, Any], records: list[dict[str, Any]]) -> list[dict]:
    """Exclude PERs not linked by exact organization to the committed master."""
    organizations = {
        str(x.get("organization", "")).strip().casefold()
        for x in master.get("experience", [])
        if isinstance(x, dict)
    }
    out = []
    for row in records:
        if row["organization"].strip().casefold() not in organizations:
            continue
        claims = [
            item["claim"].strip()
            for item in row["evidence"]
            if isinstance(item, dict)
            and item.get("claim_state") == _ALLOWED_STATE
            and item.get("source_type") in {"RESUME", "REPOSITORY", "PUBLICATION", "PRIMARY_SOURCE"}
            and isinstance(item.get("claim"), str)
            and 0 < len(item["claim"]) <= 1000
        ]
        if claims:
            out.append({"id": row["project_id"], "text": " ".join(claims)})
    return out


def _family_sources(master: dict[str, Any], sources: list[dict]) -> list[dict]:
    found = []
    competencies = master.get("competencies") or {}
    for key, phrase, signals in _SUMMARY_FAMILIES:
        if key == "ai_research" and not competencies.get("ai_research"):
            continue
        if key != "ai_research" and not master.get("experience"):
            continue
        matches = [s["id"] for s in sources if any(term in s["text"].casefold() for term in signals)]
        if matches:
            found.append({"family": key, "phrase": phrase, "per_ids": sorted(set(matches))})
    return found


def _draft_summary(master: dict[str, Any], sources: list[dict]) -> dict:
    families = _family_sources(master, sources)
    if len(families) < 2:
        return {
            "field": "summary", "action": "DRAFT_REQUIRES_MORE_PER_EVIDENCE",
            "candidate": None, "review": "HUMAN_REVIEW_REQUIRED",
            "source_ref": "master + committed PER evidence",
            "evidence_refs": [x["per_ids"] for x in families],
            "max_chars": 300,
        }
    selected = families[:4]
    phrases = [s["phrase"] for s in selected]
    joined = ", ".join(phrases[:-1]) + " and " + phrases[-1] if len(phrases) > 1 else phrases[0]
    summary = "Quality and operations professional with experience in " + joined + "."
    if len(summary) > 300:
        raise ValueError("bounded summary unexpectedly exceeds Handshake limit")
    return {
        "field": "summary", "action": "DRAFT_FROM_MASTER_AND_PER",
        "candidate": summary, "review": "HUMAN_REVIEW_REQUIRED",
        "source_ref": "master.experience + committed PER evidence",
        "evidence_refs": sorted({pid for row in selected for pid in row["per_ids"]}),
        "evidence_state": "SOURCE_SUPPORTED_BY_RESUME_NOT_INDEPENDENTLY_VERIFIED",
        "max_chars": 300, "needs_shortening": False,
        "generation_method": "FIXED_EVIDENCE_GATED_PHRASES_NOT_LLM",
    }


def _master_skills(master: dict[str, Any]) -> list[dict]:
    competencies = master.get("competencies") or {}
    if not isinstance(competencies, dict):
        raise ValueError("invalid master competencies")
    rows = []
    for domain, values in competencies.items():
        if domain == "technical_skills":
            if not isinstance(values, dict):
                continue
            for subdomain, members in values.items():
                if isinstance(members, list):
                    for text in members:
                        rows.append((str(text), subdomain, "master.competencies.technical_skills." + subdomain))
        elif isinstance(values, list):
            for text in values:
                rows.append((str(text), domain, "master.competencies." + domain))
    unique = {}
    for label, domain, ref in rows:
        label = label.strip()
        if not 0 < len(label) <= 100:
            continue
        unique.setdefault(label.casefold(), {"candidate": label, "domain": domain, "source_ref": ref})
    return list(unique.values())[:140]


def _skill_match(skill: str, sources: list[dict]) -> tuple[int, list[str]]:
    terms = _terms(skill)
    if not terms:
        return 0, []
    expanded = set(terms)
    for term in terms:
        expanded.update(_SKILL_ALIASES.get(term, ()))
    matched = []
    score = 0
    for src in sources:
        text = src["text"].lower()
        found = sum(1 for w in terms if any(re.search(r"\b" + re.escape(alias) + r"\b", text)
                                           for alias in (w, *_SKILL_ALIASES.get(w, ()))))
        if found:
            matched.append(src["id"])
            score += min(found, 3)
    return score, sorted(set(matched))


def _rank_skills(master: dict[str, Any], sources: list[dict], existing: list[str]) -> list[dict]:
    observed = {x.casefold().strip() for x in existing}
    candidates = []
    for row in _master_skills(master):
        if row["candidate"].casefold() in observed:
            continue
        score, per_ids = _skill_match(row["candidate"], sources)
        if score == 0:  # Master-supported only, but no PER grounding; hold for separate review.
            continue
        candidates.append({**row, "score": score, "evidence_refs": per_ids})
    # Deterministic, evidence-driven ranking; diversify source competency domains.
    candidates.sort(key=lambda x: (-x["score"], x["candidate"].casefold()))
    selected, domain_counts = [], {}
    for cap in (2, 4, _MAX_SKILLS):
        for candidate in candidates:
            if len(selected) >= _MAX_SKILLS:
                break
            domain = candidate["domain"]
            if candidate in selected or domain_counts.get(domain, 0) >= cap:
                continue
            selected.append(candidate)
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        if len(selected) >= _MAX_SKILLS:
            break
    return [
        {
            "field": "skill", "action": "CONSIDER_ADD",
            "candidate": x["candidate"], "source_ref": x["source_ref"],
            "evidence_refs": x["evidence_refs"],
            "ranking_basis": "PER_CLAIM_TERMS_MATCH_NOT_SKILL_VERIFICATION",
            "review": "HUMAN_REVIEW_REQUIRED",
        }
        for x in selected
    ]


def enrich_profile_proposals(
    result: dict[str, Any],
    master: dict[str, Any],
    per_records: list[dict[str, Any]],
    per_revision: str,
    observed_fields: dict[str, Any],
) -> dict[str, Any]:
    """Replace legacy first-ten skills and long-summary placeholder, preserve everything else."""
    if not re.fullmatch(r"[a-f0-9]{40}", per_revision):
        raise ValueError("PER revision required")
    if not isinstance(per_records, list) or len(per_records) > 100:
        raise ValueError("invalid PER evidence collection")
    sources = _evidence_for_master(master, per_records)
    updated = dict(result)
    proposals = [p for p in result["proposals"] if p["field"] not in {"summary", "skill"}]
    if observed_fields["summary"] == "":
        proposals.insert(0, _draft_summary(master, sources))
    if observed_fields["skills"] is not None:
        proposals.extend(_rank_skills(master, sources, observed_fields["skills"]))
    updated["proposals"] = proposals
    updated["profile_objective"] = PROFILE_OBJECTIVE
    updated["per_revision"] = per_revision
    updated["per_evidence_scope"] = "MASTER_ORG_MATCH_AND_SOURCE_SUPPORTED_CLAIMS_ONLY"
    updated["ranked_skill_count"] = sum(1 for p in proposals if p["field"] == "skill")
    updated["profile_write"] = "DISABLED"
    updated["authority_effect"] = "NONE"
    return updated
