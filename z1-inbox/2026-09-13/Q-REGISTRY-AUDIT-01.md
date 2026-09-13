# Q-REGISTRY-AUDIT-01: ZONE_REGISTRY.md Repo Reconciliation (Phase 1: Classify Missing)

**Type:** IC (Incomplete Candidate)  
**Date:** 2026-09-13  
**Author:** Z1 (Claude)  
**Status:** Awaiting Z2 Ratification  

---

## Problem Statement

**Field:** ZONE_REGISTRY.md section heading `## Repository Zone Assignments (31 repos)` (not the document title, which is `# ZONE_REGISTRY.md — Canonical Z1/Z2/Z3 Authority Map`)

The section heading claims **31 HumanAIOS repositories**  
Actual GitHub humanaios-ui org: **12 repos**  
Registry table lists: **18 repos**  
**Mismatch: 13 repos claimed but not found on GitHub**

**RECEIPT-GAP Callout:**
- Claim: "31 repos" (in section heading `## Repository Zone Assignments`)
- Tree (GitHub reality): 12 repos
- Gap: 19 repos unaccounted

---

## Classification of 13 Missing Repos

| Repo Name | Status | Classification |
|-----------|--------|-----------------|
| collaborator-ops | Not found | Planned/Never created |
| empirica-autonomy | Not found | Planned/Never created |
| empirica-autonomy-archive | Not found | Planned/Never created |
| empirica-foundation-evaluator | Not found | Planned/Never created |
| empirica-mesh-support | Not found | Planned/Never created |
| empirica-opportunity-aggregator.archive | Not found | Planned/Never created |
| empirica-outreach | Not found | Planned/Never created |
| empirica-resource-miner | Not found | Planned/Never created |
| flta-app-empirica | Not found | Planned/Never created |
| grok-crossref | Not found | Planned/Never created |
| local-machine-optimizer | Generic name matches (134 unrelated repos) | Planned/Never created |
| opportunity-aggregator | Generic name matches (370 unrelated repos) | Planned/Never created |
| website | Not found | Planned/Never created |

**Summary:** All 13 repos are **planned but never created**. None are archived in humanaios-ui org; none exist under those names in other orgs.

---

## Candidate Actions

**Option A: Correct the Header**
- Change header from "31 repos" to "12 repos" (current truth)
- Remove 13 non-existent entries from table

**Option B: Track Planned Repos Separately**
- Keep ZONE_REGISTRY for current/active repos (12)
- Create PLANNED_REPOS.md for future repos (13 + others)
- Link both in authority index

**Option C: Hybrid**
- Update ZONE_REGISTRY to "Currently 12 repos (31 planned)" 
- Create ROADMAP_REPOS.md with status of each

---

## Falsifier

**Success:** Z2 approves corrected or secondary registry structure  
**Failure:** Registry discrepancy unresolved; claim/tree mismatch persists

---

## Next Steps (Awaiting Z2)

1. Z2 selects Option A, B, or C
2. Z1 implements chosen option
3. CI gate updates registry_consistency lint rule
4. Handoff: Q-REGISTRY-AUDIT-02 (audit 7 repos on GitHub but not in registry)

---

**Proposed Z2 Decision Window:** 48h from ratification request  
**Associated:** IC-REGISTRY-001 (meta-gap: authority structure itself)
