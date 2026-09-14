# PRIORITY_QUEUE.md — Resource-Impact Ranked Work Queue

**Purpose:** Prioritized work queue ranked by resource_impact (not deadline)  
**Authority:** Z2 ratifies scores and rankings  
**Model:** Resource-based; no time-based deadlines  
**Updated:** 2026-09-14T00:00:00Z

---

## Current Queue (Ranked by Impact)

| Rank | Candidate | Title | Impact | Blocking % | Priority |
|:-----|:----------|:------|:-------|:-----------|:---------|
| 1 | Q-TEMPORAL-DISSOLUTION-01 | Remove time-based deadlines (architecture fix) | 9/10 | 60% | **CRITICAL** |
| 2 | Q-ZONE-REGISTRY-01 | Map 31 repos, executor assignments, caps | 8/10 | 50% | **HIGH** |
| 3 | Q-BOOT-PROCESS-MAP-01 | Session rituals → resource states | 7/10 | 30% | HIGH |
| 4 | Q-CANDIDATE-BLOCK-TEMPLATE-01 | Z1 proposal template + examples | 6/10 | 35% | HIGH |
| 5 | Q-GOVERNANCE-FILES-01 | Registry of governance files | 5/10 | 40% | MEDIUM |

---

## Ranking Formula

```
priority_score = (resource_impact * 10) + (blocking_capacity_pct * 5)

No time-based gates. Regulatory deadlines override resource_impact rank.
```

---

## Blocked Items

- Q-IC030-REPIN-01 (blocked by Q-BOOT-PROCESS-MAP-01, Q-REGISTERED-SCHEMA-01)

---

## Resolution Path (Next Steps)

1. **Z2 + Z1 discussion:** Confirm temporal dissolution (Q-TEMPORAL-DISSOLUTION-01)
2. **Update governance docs:** Remove all 48h/window_end/revert-count deadlines
3. **Re-rank queue:** After temporal reframe
4. **Z1 research:** Map 31 repos (Z-ZONE-REGISTRY-01)
5. **Z1 analysis:** Boot process map (Z-BOOT-PROCESS-MAP-01)

See GOVERNANCE_FILES.md for full registry.
