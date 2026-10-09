# Project Evidence Records

Project Evidence Records (PERs) are the canonical career-evidence units used by the HumanAIOS Resource System.

## Purpose

A conventional resume starts with chronology. A PER starts with a bounded project and preserves:

```
MANDATE
→ OBJECTIVE
→ SCOPE
→ STAKEHOLDERS
→ CONSTRAINTS
→ RESOURCES
→ RISKS / DEPENDENCIES
→ EXECUTION
→ DELIVERABLES
→ VALIDATION
→ OUTCOME
→ EVIDENCE
```

Role-specific application documents may render selected PER evidence, but they must not silently promote an inference or market signal into a biographical claim.

## Evidence states

- `SOURCE_SUPPORTED` — directly supported by the current resume, repository, publication, or other identified source.
- `HUMAN_ATTESTED` — supplied by the user but not yet independently documented.
- `INFERRED` — analytical interpretation; not resume-ready as fact.
- `UNVERIFIED` — candidate fact awaiting evidence.

## Job-description gap mining

`job_requirement_signals.seed.json` records recurring capability/experience signals observed across current public job descriptions in AI/technical program management, quality systems, research operations, and clinical/quality leadership.

These signals are used only to generate interrogation targets.

```
JOB_REQUIREMENT_SIGNAL != CANDIDATE_EXPERIENCE
MISSING_FROM_RESUME != ABSENT_FROM_HISTORY
TRANSFERABLE_CAPABILITY != VERIFIED_ROLE-SPECIFIC_EXPERIENCE
```

Example:

```
public jobs repeatedly ask for vendor management
        ↓
resume does not mention vendor management
        ↓
UNKNOWN
        ↓
ask the human which vendors/contracts/partners they actually managed
        ↓
evidence or attestation
        ↓
only then may the claim enter a Project Evidence Record
```

This allows the application process to recover latent professional evidence without inventing experience.
