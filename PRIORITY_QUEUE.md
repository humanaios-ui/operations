# PRIORITY_QUEUE.md — Resource-Allocated Work Queue

**Purpose:** Order eligible work by the ratified RBE-OPS constraint allocator, never by elapsed time  
**Authority:** Z2 ratifies allocation constants, cost pins, and regulatory exceptions  
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
- `OBSERVATIONAL` — timestamps/durations/measurement normalization for provenance and analysis only.
- `TECHNICAL_SAFETY` — timeouts, retry backoff, lease/token expiry, dead-process detection, cache TTL, lock reclamation; may protect correctness/resources but may not reprioritize human work.
- `REGULATORY_EXTERNAL` — externally imposed regulatory/legal/compliance deadline; may affect priority only with authority/evidence and explicit Z2 ratification.
- `HISTORICAL_RECORD` — archival time information with no present scheduling authority.
- `INTERNAL_WORK_DEADLINE` — prohibited.

**Gate exits only when:** policy + CI enforcement + active-control-surface remediation + canonical RBE temporal migration + Intent-OS External Constraints representation are merged and independently reviewed.

---

## Current Queue

| Rank | Candidate | Title | Impact | Blocking % | Priority | State |
|:-----|:----------|:------|:-------|:-----------|:---------|:------|
| 1 | Q-TEMPORAL-DISSOLUTION-01 | Resource-state scheduling gate | 10/10 | 100% | **CRITICAL** | **GATING** |
| 2 | Q-ZONE-REGISTRY-01 | Map repos, executor assignments, resource caps | 8/10 | 50% | **HIGH** | ELIGIBLE AFTER GATE where affected |
| 3 | Q-BOOT-PROCESS-MAP-01 | Session rituals → resource states | 7/10 | 30% | HIGH | ALIGNED / verify under gate |
| 4 | Q-CANDIDATE-BLOCK-TEMPLATE-01 | Align proposal template to canonical resource vector | 6/10 | 35% | HIGH | PART OF GATE |
| 5 | Q-GOVERNANCE-FILES-01 | Registry of governance files | 5/10 | 40% | MEDIUM | ELIGIBLE AFTER GATE where affected |

---

## Canonical RBE Allocation Model

The queue does not invent a new resource formula here. `priority_queue_engine.py` and the RBE-OPS stack are authoritative.

Current ratified mode:

```text
QUEUE_SCORING_MODE = resource
molt_id = f7a49f667c09f1f6
UNPRICED_ROW_POLICY = REFUSED_TO_START
binding/default constraint = RAT-min
```

Allocation:

```text
benefit(order) = impact(order) + Σ impact(work unblocked by order)

Band A: cost[RAT-min] == 0
        -> rank by benefit; run whenever other readiness predicates permit

Band B: cost[RAT-min] > 0
        -> density = benefit / cost[RAT-min]
        -> rank by density

UNPRICED:
        -> REFUSED_TO_START under the ratified policy
```

Resource cost is a **non-commensurable vector** keyed by `RESOURCE_UNITS.yaml`. `RAT-min`, `Z1-ktok`, `Z3-hr`, `CI-min`, `RUN-day`, and `SPEC-hr` do not collapse into one currency or generic effort score.

No elapsed-time value appears in the ranking function.

---

## Regulatory Exception Policy

A time-based priority override is valid **if and only if** it is represented as a validated external regulatory constraint:

```yaml
external_constraint:
  type: REGULATORY_DEADLINE
  temporal_class: REGULATORY_EXTERNAL
  authority: <issuing authority>
  citation: <statute/regulation/order/mandate>
  due_at: <RFC3339>
  evidence_ref: <immutable source/artifact>
  impact_if_missed: <consequence>
  z2_ratified: true
  ratification_ref: <durable decision/hash/comment reference>
```

Without the complete contract and explicit Z2 ratification, a date/time is telemetry or context only and has **zero priority override authority**.

External commercial/grant/partner windows are not automatically regulatory exceptions.

---

## Blocked Items

- PR #376 — blocked by Q-TEMPORAL-DISSOLUTION-01 before merge.
- ARENA semantic expansion — blocked where it depends on or introduces temporal work-control semantics.
- Q-IC030-REPIN-01 — blocked by Q-BOOT-PROCESS-MAP-01.

---

## Resolution Path

1. Land canonical temporal-purity policy over RBE-OPS.
2. Land resource-state and regulatory external-constraint schemas without creating a parallel unit registry.
3. Land CI temporal-dissolution gate over changed active control surfaces.
4. Align `CANDIDATE_BLOCK_TEMPLATE.md` with the `RESOURCE_UNITS.yaml` cost vector and complete regulatory exception object.
5. Audit active time/deadline usages into `REGULATORY_EXTERNAL | TECHNICAL_SAFETY | OBSERVATIONAL | HISTORICAL_RECORD | INVALID_INTERNAL_DEADLINE`.
6. Produce a versioned migration candidate for incompatible time-driven controls in ratified `RESOURCE_UNITS.yaml` / `constants.json`; do not silently rewrite ratified v0.1.
7. Remediate active invalid internal deadline semantics.
8. Replace generic Intent-OS `Deadlines` semantics with `External Constraints`.
9. Independently review the gate.
10. Mark Q-TEMPORAL-DISSOLUTION-01 complete only when its falsifier no longer holds.

See issue #378, `TEMPORAL_DISSOLUTION_POLICY.md`, `docs/RESOURCE_BASED_ECONOMICS.md`, and `RESOURCE_UNITS.yaml`.
