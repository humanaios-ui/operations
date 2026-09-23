from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from typing import Any

from .engine import evaluate_profile
from .research import tasks_from_results
from .interrogator import active_domains



PROGRAM_DOMAIN = {
    "trust_asset": "genealogy",
    "trust_asset_probate": "genealogy",
    "ancestral_asset_investigation": "genealogy",
    "business_capital_and_coaching": "business",
    "procurement_certification": "business",
    "scholarship": "education",
    "vocational_training_assistance": "education",
    "financial_assistance": "household",
    "housing_finance": "housing",
    "historical_settlement": "tribal",
}

def _filter_relevant_results(results: list[dict[str, Any]], profile: dict[str, Any]) -> list[dict[str, Any]]:
    domains = active_domains(profile)
    out = []
    for r in results:
        domain = PROGRAM_DOMAIN.get(r.get("program_type"))
        if domain and domain not in domains:
            continue
        out.append(r)
    return out

def _case_id(profile: dict[str, Any]) -> str:
    safe = {k: v for k, v in profile.items() if k not in {"ssn", "tribal_id", "bank_account"}}
    blob = json.dumps(safe, sort_keys=True, default=str).encode()
    return "CASE-" + hashlib.sha256(blob).hexdigest()[:12].upper()


def build_casefile(
    profile: dict[str, Any], programs: list[dict[str, Any]], genealogy_patch: dict[str, Any] | None = None,
    genealogy_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    merged = dict(profile)
    # Derived data lives under explicit provenance and may route research, but cannot override user facts.
    for k, v in (genealogy_patch or {}).items():
        if k not in merged:
            merged[k] = v
    results = _filter_relevant_results(evaluate_profile(merged, programs, include_ineligible=False), profile)
    research = tasks_from_results(results, genealogy_patch, profile)
    counts = Counter(r["status"] for r in results)

    ready = [r for r in results if r["status"] == "RULE_MATCH"]
    investigate = [r for r in results if r["status"] == "INVESTIGATE"]
    conditional = [r for r in results if r["status"] == "CONDITIONAL_MATCH"]
    actions: list[dict[str, Any]] = []
    for r in ready:
        actions.append({"priority": 1, "type": "APPLICATION", "title": r["title"], "program_id": r["program_id"], "action": r["next_actions"][0] if r["next_actions"] else "Open the authoritative application path."})
    for t in research:
        if t["priority"] < 10:
            actions.append({"priority": 2, "type": "RESEARCH", "title": t["title"], "task_id": t["task_id"], "action": t["purpose"]})
    for r in investigate:
        actions.append({"priority": 3, "type": "CLAIM_INVESTIGATION", "title": r["title"], "program_id": r["program_id"], "action": r["next_actions"][0] if r["next_actions"] else "Resolve evidence gap."})
    for r in conditional:
        actions.append({"priority": 4, "type": "EVIDENCE_GATHERING", "title": r["title"], "program_id": r["program_id"], "action": "Gather missing evidence and re-evaluate."})

    return {
        "case_id": _case_id(merged),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "question": "Is there an existing asset or legally cognizable benefit or funding pathway attached to the applicant entities, and what evidence or action is required to establish or obtain it?",
        "profile": merged,
        "provenance": {
            "user_asserted_fields": sorted(profile.keys()),
            "derived_genealogy_fields": sorted((genealogy_patch or {}).keys()),
            "genealogy_summary": genealogy_summary,
        },
        "resolution": {
            "status_counts": dict(counts),
            "rule_matches": len(ready),
            "investigations": len(investigate),
            "conditional_matches": len(conditional),
        },
        "pathways": results,
        "research_queue": research,
        "action_plan": sorted(actions, key=lambda x: (x["priority"], x["title"])),
    }
