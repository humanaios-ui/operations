# Cross-Repository Coordination — Collaborator Systems

**Status:** Coordination mapping required  
**Date:** 2026-07-22

---

## Problem Statement

HumanAIOS maintains parallel collaborator management systems across multiple repositories:

| Repository | Path | System | Status |
|---|---|---|---|
| empirica-outreach (this) | `/collaborator-ops/` | Empirica-grounded governance framework | ACTIVE (new, 2026-07-22) |
| humanaios-internal | `/collaborator-ops/` | [CHECK: parallel system exists?] | TBD |
| humanaios-internal | `/collaborators/` | [CHECK: collaborator profiles?] | TBD |
| humanaios-ui | [CHECK: coordination layer?] | [CHECK: web/internal UI integration?] | TBD |

**Question:** Are these the same system (should be one source of truth) or separate systems (need sync protocol)?

---

## Immediate Tasks

1. **Audit humanaios-internal structure:**
   - Read `/collaborator-ops/` — compare with empirica-outreach version
   - Read `/collaborators/` — compare profile schema with empirica-outreach version
   - Determine: single-source-of-truth or dual-system with sync?

2. **Establish coordination protocol:**
   - If single source: consolidate → retire one copy
   - If dual: define sync rules (what syncs? direction? frequency?)

3. **Sync or migrate Sarah Preseley validation:**
   - Once structure is clear, add Sarah as test-candidate to both systems

4. **Document integration layer:**
   - How do these systems feed UI / reporting / governance?

---

## Responsible Parties

- **Carly:** Clarify which repo is authoritative
- **Team:** Coordinate migration/sync once decision is made

---

## Linked Decisions

- D-004: David's participation level (affects which system(s) track it)
- Onboarding framework validation (Sarah dry-run depends on system clarity)

---

## Notes for Next Session

Before proceeding with real candidate outreach, the collaborator systems must be consolidated or synchronized. Do NOT maintain parallel versions — that's a source of truth divergence and calibration drift.

Check with team on:
- Which repo contains the "real" collaborator registry?
- Are humanaios-internal systems active or legacy?
- Should empirica-outreach become the canonical source, or maintain them separately with sync?
