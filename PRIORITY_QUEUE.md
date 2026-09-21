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

## Phase 0 Witness Proposals (Z2-Ratified 2026-09-21)

**Authority:** Z2 ratified issue #429 (Q-WITNESS-COMMONS-ASSURANCE-01); Phase 0 artifacts filed as separate resource-allocated Z1 proposals in REGISTERED.md.

**Resource Allocation Model:** Scored by density = benefit / cost[RAT-min] equivalent (resource vector unpriced; proposals below use Z3-hr as primary cost axis for ranking purposes).

| Rank | ID | Artifact | Duration | Z1-ktok | Z3-hr | CI-min | SPEC-hr | Dependencies | Impact | Density (Z3-hr proxy) | Executor |
|:-----|:---|:---------|:---------|:--------|:------|:-------|:--------|:-----------|:-------|:---------------------|:---------|
| A | Q-WITNESS-PHASE-0-ARTIFACT-INVENTORY-01 | artifact/claim/control/test/evidence/failure/falsifier inventory | 3w | 15 | 25 | 10 | 8 | none | 9/10 | 0.36 | TBD |
| B | Q-WITNESS-PHASE-0-EVIDENCE-GRAPH-01 | Typed evidence graph schema & genesis | 4w | 20 | 35 | 15 | 12 | A | 9/10 | 0.26 | TBD |
| C | Q-WITNESS-PHASE-0-GENESIS-READINESS-01 | Observable Horizon thresholds & genesis readiness seal | 3w | 18 | 30 | 12 | 10 | B | 9/10 | 0.30 | TBD |
| E | Q-WITNESS-PHASE-0-PARTICIPATION-CONTRACT-SCHEMA-01 | Participation Contract schema (V0.1) & orthogonal axes | 2w | 16 | 28 | 10 | 8 | C | 8/10 | 0.29 | TBD |
| D | Q-WITNESS-PHASE-0-WITNESS-STATE-SCHEMA-01 | Witness state schema (W_state_type definition) | 2w | 12 | 20 | 8 | 6 | none (parallel) | 7/10 | 0.35 | TBD |
| F | Q-WITNESS-PHASE-0-SERVICE-CONTRACT-01 | Witness Service Contract (W_service_type) | 2w | 10 | 18 | 6 | 5 | none (parallel) | 7/10 | 0.39 | TBD |

**Critical Path:** A→B→C→E (12 weeks, 91 Z1-ktok, 118 Z3-hr, 47 CI-min, 40 SPEC-hr)  
**Parallel Tracks:** D+F weeks 1–4 (4 Z1-ktok, 38 Z3-hr, 14 CI-min, 11 SPEC-hr)  
**Total Phase 0:** 91 Z1-ktok, 156 Z3-hr, 61 CI-min, 49 SPEC-hr  

**Recommended Executor Assignment:**
- **Executor A:** Q-WITNESS-PHASE-0-ARTIFACT-INVENTORY-01 + Q-WITNESS-PHASE-0-EVIDENCE-GRAPH-01 (serial path A→B; 55 Z3-hr)
- **Executor B:** Q-WITNESS-PHASE-0-GENESIS-READINESS-01 + Q-WITNESS-PHASE-0-PARTICIPATION-CONTRACT-SCHEMA-01 (serial path C→E; 58 Z3-hr)
- **Executor C:** Q-WITNESS-PHASE-0-WITNESS-STATE-SCHEMA-01 + Q-WITNESS-PHASE-0-SERVICE-CONTRACT-01 (parallel D+F; 38 Z3-hr)

**Blocking Conditions (issue #429 Z2 approval):**
1. ✅ Condition A: Phase 0 split into resource proposals — **COMPLETE** (6 proposals filed in REGISTERED.md, now ratified in PRIORITY_QUEUE.md)
2. ✔️ Condition B: 5 critical edits to RFC — **COMPLETE** (recorded in issue #429 approval comment)
3. ⏳ Condition C: Phase 1 scope separately proposed — **PENDING** (propose as follow-up after Phase 0 executors assigned)
4. ⏳ Condition D: Legal/ethics assessment gated — **PENDING** (Z2 to commission 4-week external counsel review)

**Dates Ratified:**
- Z2 decision: 2026-09-21 (issue #429 approval)
- REGISTERED.md entries: 2026-09-21 (6 CANDIDATE blocks created; 6 REGISTERED blocks with Z2 ratification)
- PRIORITY_QUEUE.md entry: 2026-09-21 (this table)

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
