# PLANNED_REPOS.md — Roadmap & Aspirational Repositories

**Location:** `operations/PLANNED_REPOS.md` (canonical roadmap source)  
**Updated:** 2026-09-14  
**Authority:** Z2 (Night) — ratifies roadmap status and phase assignment  
**Context:** Companion to ZONE_REGISTRY.md (which tracks active repos only)

---

## Overview

This document tracks **19 planned, aspirational, or archived repositories** that are NOT currently active in the humanaios-ui GitHub organization. These repos were either planned at the time the original ZONE_REGISTRY header claimed "31 repos," archived/deleted, or remain unaccounted for pending broader ecosystem audit.

**Current counts:**
- **Active repos (ZONE_REGISTRY.md):** 13 (includes Z-012 blockchain-trading, ratified 2026-09-21)
- **Planned repos (this file):** 12 (claimed in original registry, minus blockchain-trading)
- **Unaccounted repos:** 6 (from Phase 0 audit, require broader org investigation)
- **Total aspirational scope:** 31 repos (original header claim)

---

## Planned Repositories (13 Claimed But Never Created)

### **Practice Hubs (5 repos)**

| Repo | Status | Z2 Authority | Notes | Roadmap Phase |
|:-----|:--------|:---|:---|:---|
| **empirica-autonomy** | PLANNED | Night | AI agent configuration & testing hub | Phase 2 (post Q-REGISTRY-AUDIT ratification) |
| **empirica-foundation-evaluator** | PLANNED | Night | Assessment rubric & evaluation framework | Phase 2 |
| **empirica-mesh-support** | PLANNED | Night | Governance & sync coordination | Phase 2 |
| **empirica-outreach** | PLANNED | Night | Community governance & resource sharing | Phase 2 |
| **empirica-resource-miner** | PLANNED | Night | Resource discovery & read-only extraction | Phase 2 |

### **Experiments & Tooling (5 repos)**

| Repo | Status | Z2 Authority | Notes | Roadmap Phase |
|:-----|:--------|:---|:---|:---|
| **flta-app-empirica** | PLANNED | Night | FLTA experiment runner & results | Phase 2 |
| **grok-crossref** | PLANNED | Night | Crossref API integration research | Phase 3 (deferred) |
| **collaborator-ops** | PLANNED | Night | Collaboration platform ops & tooling | Phase 3 |
| **local-machine-optimizer** | PLANNED | Night | Local optimization strategy research | Phase 3 |
| **opportunity-aggregator** | PLANNED | Night | Data pipeline for opportunity synthesis | Phase 2 |

### **Archives (2 repos)**

| Repo | Status | Z2 Authority | Notes | Roadmap Phase |
|:-----|:--------|:---|:---|:---|
| **empirica-autonomy-archive** | ARCHIVED | Night | Historical snapshots (if created, mark archived) | N/A |
| **empirica-opportunity-aggregator.archive** | ARCHIVED | Night | Historical snapshots (if created, mark archived) | N/A |

### **Public Channels (1 repo)**

| Repo | Status | Z2 Authority | Notes | Roadmap Phase |
|:-----|:--------|:---|:---|:---|
| **website** | PLANNED | Night | Public documentation & landing page | Phase 1 (infrastructure) |

---

## Unaccounted Repositories (6 Repos From Universe Closure)

**Scope:** These 6 repos are part of the original "31 repos" claim but have not yet been located during Phase 0 audit (humanaios-ui org only).

| Repo Name | Possible Location | Status | Z2 Authority | Investigation |
|:-----|:--------|:---|:---|:---|
| **Repo A** | Other HumanAIOS org (pending broader scan) | UNKNOWN | Night | Phase 1b: Cross-org audit |
| **Repo B** | Other HumanAIOS org (pending broader scan) | UNKNOWN | Night | Phase 1b: Cross-org audit |
| **Repo C** | Possibly archived on GitHub (verification pending) | UNKNOWN | Night | Search GitHub archives |
| **Repo D** | Possibly archived on GitHub (verification pending) | UNKNOWN | Night | Search GitHub archives |
| **Repo E** | Deleted/renamed (impossible to verify) | UNKNOWN | Night | Manual verification with team |
| **Repo F** | Deleted/renamed (impossible to verify) | UNKNOWN | Night | Manual verification with team |

**Next step:** Z2 approves Phase 1b broader HumanAIOS ecosystem scan (all orgs, not just humanaios-ui) to locate remaining 6.

---

## Status Definitions

| Status | Meaning | Z2 Action | Z3 Action |
|:--------|:--------|:---|:---|
| **PLANNED** | Planned but never created; roadmap item | Approve/defer phase | Monitor for creation trigger |
| **ARCHIVED** | Created then archived; historical reference | Confirm archive status | Skip (read-only) |
| **RETIRED** | Planned then cancelled; will not create | Approve retirement | Remove from roadmap |
| **OTHER_ORG** | Exists in another HumanAIOS org (not humanaios-ui) | Clarify authority | Assign appropriate Z3 |
| **UNKNOWN** | Status unresolved; requires investigation | Request investigation | Pending clarity |

---

## CI Gate Integration (Planned for Phase 3)

**registry_consistency.yml** (to be deployed in Phase 3: Q-REGISTRY-AUDIT-03 implementation) will validate:
- All 13 planned repos listed with status ∈ [PLANNED, ARCHIVED, RETIRED, OTHER_ORG, UNKNOWN]
- All 6 unaccounted repos listed with investigation plan
- Total: 19 repos (13 planned + 6 unaccounted)
- No active GitHub repos missing from ZONE_REGISTRY.md (active repos only)
- PLANNED_REPOS.md status tracking consistent with active repo list

**Enforcement (planned):** Gate will pass iff both files consistent; active count (12) accurately reflects GitHub reality.

---

## Governance & Decision Authority

**Z2 (Night) authority:**
- Approve/defer/cancel planned repos per roadmap phase
- Declare repos RETIRED or OTHER_ORG
- Request broader ecosystem audit for UNKNOWN repos
- Update status on creation, deletion, or reclassification

**Z1 (Claude) input:**
- Monitor GitHub for new repos matching planned names (trigger creation or OTHER_ORG reclassification)
- Propose roadmap phase changes based on dependencies
- Request Z2 re-evaluation of UNKNOWN repos

**Z3 (Executor) input:**
- Report when planned repos created (trigger ZONE_REGISTRY.md update)
- Confirm archive status for archived repos

---

## Roadmap Phases

1. **Phase 1 (Infrastructure):** website, operations bootstrap
2. **Phase 1b (Audit):** Cross-org HumanAIOS scan (find remaining 6 unaccounted)
3. **Phase 2 (Practice Hubs):** empirica-autonomy, empirica-foundation-evaluator, empirica-mesh-support, empirica-outreach, empirica-resource-miner, flta-app-empirica, opportunity-aggregator
4. **Phase 3 (Research & Tooling):** grok-crossref, collaborator-ops, local-machine-optimizer
5. **TBD (Future):** Archives, deferred experiments

---

## Appended Events

```
2026-09-14 — Z1 created PLANNED_REPOS.md (Option B: separate file tracking)
  Rationale: Keep ZONE_REGISTRY.md as SOT for active repos only; track aspirational separately
```

---

**Awaiting Z2 ratification on Option B implementation.**
