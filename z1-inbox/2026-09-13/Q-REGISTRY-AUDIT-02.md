# Q-REGISTRY-AUDIT-02: ZONE_REGISTRY.md Repo Reconciliation (Phase 2: Add Missing Active Repos)

**Type:** IC (Incomplete Candidate)  
**Date:** 2026-09-13  
**Author:** Z1 (Claude)  
**Status:** Awaiting Z2 Ratification (blocked on Q-REGISTRY-AUDIT-01)  

---

## Problem Statement

7 repositories exist in humanaios-ui GitHub org but are **not listed in ZONE_REGISTRY.md**

**RECEIPT-GAP Callout:**
- GitHub has repos: acat-x, acat-dashboard, acat-observatory, docs, empirica-practice-mesh, research, findlocaltattooartists
- Tree (ZONE_REGISTRY): 0 of these 7 listed
- Gap: 7 active repos unregistered

---

## Classification of 7 New Repos

| Repo Name | Created | Last Push | Status | Proposed Zone |
|-----------|---------|-----------|--------|----------------|
| acat-x | 2026-08-02 | 2026-09-11 | Active, 4 open issues | empirica-autonomy (Z1/WRITE) |
| acat-dashboard | 2026-03-03 | 2026-07-18 | Active, synced from Magic Patterns | acat-inspect (Z1/WRITE) |
| acat-observatory | 2026-03-11 | 2026-03-11 | PRIVATE, synced from Magic Patterns | acat-inspect (Z1/WRITE) |
| docs | 2026-03-22 | 2026-03-22 | Active (MDX), 0 issues | website (Z1/WRITE) |
| empirica-practice-mesh | 2026-09-11 | 2026-09-12 | Active, governance/practices/sync | empirica-mesh-support (Z1/WRITE) |
| research | 2026-04-30 | 2026-07-08 | Frozen snapshots (ACAT papers) | empirica-foundation-evaluator (Z1/READ) |
| findlocaltattooartists | 2026-05-06 | 2026-05-06 | Active (Astro/Tailwind) | website (Z1/WRITE) |

---

## Candidate Actions

**Add to ZONE_REGISTRY.md:**

```markdown
| **acat-x** | empirica-autonomy | Z1 | evaluation, assessment suite |
| **acat-dashboard** | acat-inspect | Z1 | dashboard, visualization |
| **acat-observatory** | acat-inspect | Z1 | private, observational data |
| **docs** | website | Z1 | documentation, MDX |
| **empirica-practice-mesh** | empirica-mesh-support | Z1 | governance, entity sync |
| **research** | empirica-foundation-evaluator | Z1 | papers, datasets (frozen) |
| **findlocaltattooartists** | website | Z1 | portfolio, CMS |
```

---

## Zone Re-Assignments (Implicit)

This action **creates zone entries for:**
- empirica-autonomy (was planned, now has child: acat-x)
- empirica-mesh-support (was planned, now has child: empirica-practice-mesh)
- empirica-foundation-evaluator (was planned, now has child: research)
- **website** (was planned [from Q-REGISTRY-AUDIT-01 missing list], now has children: docs, findlocaltattooartists)

**Note:** These "parent" zones remain unregistered (no top-level repos), only child repos are registered. **All four parent zones are currently planned but not yet created as standalone repositories.** The zone assignment establishes the governance structure; the parent repos may be created later per roadmap.

---

## Falsifier

**Success:** Z2 approves 7 new rows in ZONE_REGISTRY + implicit zone hierarchy  
**Failure:** Ambiguity on zone assignment; missing repos remain unregistered

---

## Blockers

- **Depends on:** Q-REGISTRY-AUDIT-01 (decide repo count claim)
- **Before merge:** Z2 verifies zone assignments align with FRAMEWORK_MAPPING.md

---

## Next Steps (Awaiting Z2)

1. Z2 reviews proposed zone assignments
2. Z2 approves or edits rows for 7 new repos
3. Z1 integrates with Q-REGISTRY-AUDIT-01 solution
4. Handoff: Q-REGISTRY-AUDIT-03 (final registry state + ci gate update)

---

**Proposed Z2 Decision Window:** 48h (after Q-REGISTRY-AUDIT-01 resolved)  
**Associated:** IC-REGISTRY-002 (active repos missing from authority register)
