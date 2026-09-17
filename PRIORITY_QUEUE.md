# PRIORITY_QUEUE.md — Resource-Impact Ranked Work Queue

**Purpose:** Prioritized work queue ranked by resource impact and available capacity, not elapsed time  
**Authority:** Z2 ratifies scores, rankings, and regulatory exceptions  
**Model:** Resource/state based; internal time-based deadlines prohibited  
**Updated (observational only):** 2026-09-17

---

## GLOBAL ARCHITECTURAL GATE

### Q-TEMPORAL-DISSOLUTION-01 — Resource-State Scheduling Gate

**Issue:** #378  
**State:** `GATING`  
**Priority:** `CRITICAL`  
**Effect:** Downstream governance/ARENA/Intent-OS semantic expansion may be designed but must not merge if it introduces or depends on internal calendar/deadline semantics.

HumanAIOS work is admitted when all execution predicates are satisfied:

```text
READY(work) =
  AUTHORITY(work)
  AND DEPENDENCIES(work)
  AND RESOURCES(work)
  AND EVIDENCE(work)
  AND SAFETY(work)
```

Elapsed time has no internal scheduling authority.

Permitted temporal classes:
- `OBSERVATIONAL` — timestamps/durations for provenance and telemetry only.
- `TECHNICAL_SAFETY` — timeouts, retry backoff, lease/token expiry, dead-process detection, cache TTL, lock reclamation; may protect correctness/resources but may not reprioritize human work.
- `REGULATORY_EXTERNAL` — externally imposed regulatory/legal/compliance deadline; may affect priority only with authority/evidence and explicit Z2 ratification.
- `INTERNAL_WORK_DEADLINE` — prohibited.

**Gate exits only when:** policy + schemas + CI enforcement + active-control-surface remediation + Intent-OS External Constraints representation are merged and independently reviewed.

---

## Current Queue (Ranked by Resource Impact)

| Rank | Candidate | Title | Impact | Blocking % | Priority | State |
|:-----|:----------|:------|:-------|:-----------|:---------|:------|
| 1 | Q-TEMPORAL-DISSOLUTION-01 | Resource-state scheduling gate | 10/10 | 100% | **CRITICAL** | **GATING** |
| 2 | Q-ZONE-REGISTRY-01 | Map repos, executor assignments, resource caps | 8/10 | 50% | **HIGH** | ELIGIBLE AFTER GATE where affected |
| 3 | Q-BOOT-PROCESS-MAP-01 | Session rituals → resource states | 7/10 | 30% | HIGH | ALIGNED / verify under gate |
| 4 | Q-CANDIDATE-BLOCK-TEMPLATE-01 | Z1 proposal template + examples | 6/10 | 35% | HIGH | ELIGIBLE AFTER GATE where affected |
| 5 | Q-GOVERNANCE-FILES-01 | Registry of governance files | 5/10 | 40% | MEDIUM | ELIGIBLE AFTER GATE where affected |

---

## Ranking Model

```text
priority_score = f(resource_impact, downstream_capacity_unlocked, resource_cost, scarcity)
```

Current queue ordering remains resource-impact based. No elapsed-time term is permitted.

A future implementation may use a multidimensional resource vector rather than collapsing all resources into one scalar.

---

## Regulatory Exception Policy

A time-based priority override is valid **if and only if** it is represented as a validated external regulatory constraint:

```yaml
external_constraint:
  type: REGULATORY_DEADLINE
  authority: <issuing authority>
  citation: <statute/regulation/order/mandate>
  due_at: <RFC3339>
  evidence_ref: <immutable source/artifact>
  impact_if_missed: <consequence>
  z2_ratified: true
  ratification_ref: <durable decision/hash/comment reference>
```

Without the complete contract and explicit Z2 ratification, a date/time is telemetry or context only and has **zero priority override authority**.

---

## Blocked Items

- PR #376 — blocked by Q-TEMPORAL-DISSOLUTION-01 before merge.
- ARENA semantic expansion — blocked where it depends on or introduces temporal work-control semantics.
- Q-IC030-REPIN-01 — blocked by Q-BOOT-PROCESS-MAP-01.

---

## Resolution Path

1. Land canonical temporal/resource policy.
2. Land resource-request/state and external-constraint schemas.
3. Land CI temporal-dissolution gate over active control-surface changes.
4. Audit active time/deadline usages into `REGULATORY_EXTERNAL | TECHNICAL_SAFETY | HISTORICAL_RECORD | INVALID_INTERNAL_DEADLINE`.
5. Remediate active invalid internal deadline semantics.
6. Replace generic Intent-OS `Deadlines` semantics with `External Constraints`.
7. Independently review the gate.
8. Mark Q-TEMPORAL-DISSOLUTION-01 complete only when its falsifier no longer holds.

See issue #378 and GOVERNANCE_FILES.md for control-surface scope.
