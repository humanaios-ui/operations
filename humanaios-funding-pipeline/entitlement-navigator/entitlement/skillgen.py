from __future__ import annotations

from typing import Any


def generate_case_skill(casefile: dict[str, Any]) -> str:
    case_id = casefile["case_id"]
    tasks = casefile.get("research_queue", [])
    task_lines = "\n".join(
        f"- `{t['task_id']}` — {t['title']}: {t['purpose']} Success evidence: {', '.join(t['success_evidence'])}."
        for t in tasks
    ) or "- No external research tasks were generated yet."
    return f"""# Entitlement Evidence Research Skill — {case_id}

## Objective
Answer only this operational question: **Is there an existing asset, legally cognizable benefit, or funding pathway attached to the applicant entities in this case, and what exact evidence and action are required to establish or obtain it?**

## Evidence discipline
1. Keep `USER_ASSERTED`, `USER_FILE_CLUE`, `RESEARCH_CANDIDATE`, `CORROBORATED`, and `AUTHORITY_VERIFIED` distinct.
2. Never convert genealogy, a family story, a same-name match, tribal citizenship, or historical enrollment into present property ownership without the intervening evidence chain.
3. Never call a grant/program a match unless its applicant type and current eligibility predicates were checked against an authoritative source.
4. Record negative searches and contradictions. They are evidence.
5. Prefer primary sources: administering agency, tribe, court/administrative record, NARA/BIA/BTFA title/probate record, official assistance listing, or official application.
6. Minimize sensitive data. Do not request an SSN, full tribal ID, bank number, or identity image during discovery unless the authoritative process requires it for a specific submission.

## Pipeline
General intake → applicant/entity graph → adaptive interrogation → evidence ingestion → authoritative research → predicate resolution → entitlement/funding classification → evidence gap → actionable application/claim packet → agency decision → case resolution.

## Current research queue
{task_lines}

## Required output schema
For every pathway return:
- pathway / legal applicant entity;
- classification: RULE_MATCH | CONDITIONAL_MATCH | INVESTIGATE | INELIGIBLE | CLOSED_HISTORICAL | GENERAL_OPPORTUNITY;
- each material predicate and evidence state;
- authoritative source and verification date;
- missing evidence;
- exact next action;
- what observation would change the current ruling.

## Stop conditions
Stop a research branch when an authoritative source disproves a required identity/eligibility predicate, or when the next step requires a legal/agency determination the researcher cannot make. Preserve the defeated branch and reason instead of deleting it.
"""
