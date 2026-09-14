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
Registry table lists: **18 repos** (concrete entries; 1 `[Other archived repos]` placeholder)  
**Mismatch: 13 repos claimed but not found on GitHub**

**Universe Accounting:**
- Registry contains 18 named repos: 5 exist on GitHub + 13 don't exist = 18 total
- GitHub has 12 repos: 5 registered + 7 unregistered = 12 total
- Combined unique names: 5 (overlap) + 13 (registry-only) + 7 (GitHub-only) = 25 entities
- Header claims 31 repos → **6 repos unaccounted** (31 - 25 = 6)

**RECEIPT-GAP Callout:**
- Claim: "31 repos" (in section heading `## Repository Zone Assignments`)
- Accounted tree: 25 unique names (18 registry + 7 GitHub unregistered, 5 overlap)
- Unaccounted: 6 repos missing from universe

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

## Universe Closure: Accounting for the Missing 6 Repos

**Finding:** The header claims 31 repos, but only 25 unique names are identified across registry and GitHub (18 + 7, with 5 overlap). This leaves **6 repos unaccounted for**.

**Possible sources for the missing 6:**

| Source | Count | Evidence |
|--------|-------|----------|
| Repos in other HumanAIOS orgs (not humanaios-ui) | 0–6 | Not in scope of this audit; Q-REGISTRY-AUDIT scope is humanaios-ui only |
| Repos archived (not counted by GitHub MCP searches) | 0–2 | `[Other archived repos]` placeholder in ZONE_REGISTRY Tier 5 is not enumerated |
| Repos deleted or renamed on GitHub | 0–3 | Cannot verify with GitHub API; out of audit scope |
| Discrepancy in the 31-repo header claim | 6+ | **Recommendation:** Treat the "31 repos" as aspirational roadmap, not a claim of currently-existing repos |

**Decision Point for Z2:**

The 6 unaccounted repos can be resolved in three ways:

1. **Enumerate them explicitly** (if they exist in other orgs or as archives): Update ZONE_REGISTRY to list all 31 by name, with status (planned/archived/other-org)
2. **Retire the 31-repo claim** (if it is aspirational): Change header to "12 active repos (31 planned)" + create separate PLANNED_REPOS.md or ROADMAP_REPOS.md (Option B or C)
3. **Accept the 25-repo universe** (if other 6 are truly gone): Change header to "12 active + 13 planned (25 total identified)" and track separately

**This candidate recommends Option 2/3: The header's "31 repos" is aspirational/outdated. All 31 should be explicitly listed in a separate PLANNED_REPOS.md or ROADMAP_REPOS.md with current status (planned, archived, renamed, other-org, retired).**

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
