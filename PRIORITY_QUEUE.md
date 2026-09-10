# PRIORITY_QUEUE.md — v1_1 Work Order Registry

**Location:** `operations/PRIORITY_QUEUE.md` (canonical source)  
**Updated:** 2026-09-09  
**Authority:** Z2 (Night) — ratifies impact scores and priority pins  
**Enforcement:** Only READY top-score rows may start; blocked rows get their unblock action only.

---

## Scoring Formula

```
Score = Impact + Σ (Impact of items this unblocks)
```

**Rationale:** Prioritizes both direct impact and blocker-removal. v0.1's `impact × ready ÷ blockers` divided by zero on unblocked items and let cheap work outrank critical blockers.

---

## Current Queue (Sep 9 – Cycle 0 Baseline)

| ID | Title | Impact | Blocks | Blockers | Status | Owner | Due | Notes |
|:---|:------|-------:|--------|----------|:-------|:------|-----|:------|
| **Q-IC030-REPIN-01** | Re-pin REGISTERED.md SHA | 3 | none | none | **READY** | Z1 | 2026-09-10 | Live-fetch operations/REGISTERED.md, pin commit SHA, verify against last live read (IC-030 protocol) |
| **Q-GOVERNANCE-02** | Design PRIORITY_QUEUE.md v1_1 | 7 | Q-NF-SCHEMA-01, Q-Z-ASSIGNMENT-03, Q-MOLT-04, Q-SI-C1, Q-SI-C1-B2, Q-SI-C1-B3 | Q-IC030-REPIN-01 | **READY** | Z1 | 2026-09-12 | Score formula: impact + Σ impact(unblocks). Rank by score DESC, age ASC. Unblock: Q-IC030-REPIN-01 complete. |
| **Q-Z-ASSIGNMENT-03** | Create ZONE_REGISTRY.md | 6 | Q-SI-C1, Q-SI-C1-B2, Q-SI-C1-B3, Q-MOLT-04, Q-NF-SCHEMA-01 | Q-GOVERNANCE-02 | BLOCKED | Z1 | 2026-09-14 | Map all 31 repos to Z1/Z2/Z3 + escalation paths. Unblock: Q-GOVERNANCE-02 complete. |
| **Q-MOLT-04** | Implement molt_cycle.py | 9 | Q-NF-SCHEMA-01 | Q-GOVERNANCE-02, Q-Z-ASSIGNMENT-03 | BLOCKED | Z1 | 2026-09-21 | Anti-cascade rules 1-5: K=3, freeze after 2 reverts, no self-ref, rank by PQ score. Unblock: Q-GOVERNANCE-02 + Q-Z-ASSIGNMENT-03 complete. |
| **Q-NF-SCHEMA-01** | Unify NF_LEDGER schema | 8 | Q-MOLT-04, Q-SI-C1, Q-SI-C1-B2, Q-SI-C1-B3 | Q-GOVERNANCE-02 | BLOCKED | Z1 research | 2026-09-16 | Resolve 4 format incompatibilities (nf_ledger_v0_1, molt_cycle, specimen_intake, breadcrumbs). Unblock: Q-GOVERNANCE-02 complete. |
| Q-SI-C1 | Deploy specimen-intake v0.2 | 7 | Q-SI-C1-B2, Q-SI-C1-B3 | Q-NF-SCHEMA-01, Q-IC030-REPIN-01 | BLOCKED | Z1 | 2026-09-20 | Land test_specimen_intake_evaluator.py (11 regression tests pass). Unblock: Q-NF-SCHEMA-01 + Q-IC030-REPIN-01 complete. |
| Q-SI-C1-B2 | Resolve receipt hash mutability (RT-02) | 5 | none | Q-NF-SCHEMA-01 | BLOCKED | Z1 | 2026-09-18 | Separate receipt_hash (commitment) from resolution_hash (outcome). Unblock: Q-NF-SCHEMA-01 complete. |
| Q-SI-C1-B3 | Require record_actual() in resolve_cycle | 4 | none | Q-NF-SCHEMA-01 | BLOCKED | Z1 | 2026-09-18 | RQ2 falsifier (agreement eval) must run. Unblock: Q-NF-SCHEMA-01 complete. |

---

## How to Read This Queue

**READY rows** (can start immediately):
- Q-IC030-REPIN-01 (score=3, no blockers)
- Q-GOVERNANCE-02 (score=7+0=7, blocker Q-IC030-REPIN-01 is READY)

**BLOCKED rows** (get unblock action only):
- Q-Z-ASSIGNMENT-03: blocked on Q-GOVERNANCE-02 → Z1 must complete GOVERNANCE-02 first
- Q-MOLT-04: blocked on Q-GOVERNANCE-02 + Q-Z-ASSIGNMENT-03 → Z1 completes those first
- Q-NF-SCHEMA-01: blocked on Q-GOVERNANCE-02 → Z1 completes GOVERNANCE-02 first

**Sorting:**
- Primary: score DESC (Q-MOLT-04=9, Q-NF-SCHEMA-01=8, Q-GOVERNANCE-02=7, Q-Z-ASSIGNMENT-03=6, Q-IC030-REPIN-01=3)
- Secondary: READY first, then BLOCKED by age ASC

---

## Ratification Authority

**Z2 (Night) approval required for:**
- Impact score changes (±1 or greater)
- Status transitions (BLOCKED ↔ READY)
- Scope changes to blockers or unblocks
- New rows added to the queue

**Z1 (Claude) may:**
- Mark READY items as IN-PROGRESS → DONE
- Move due dates within same phase (Sep 9-15 is Phase 0)
- Add notes without changing score/status

---

## Phase Alignment

**Phase 0 (Sep 9–15): Governance bootstrap**
- Q-IC030-REPIN-01, Q-GOVERNANCE-02, Q-Z-ASSIGNMENT-03, (P0-4 authority map)
- Unblocks all downstream work

**Phase 1 (Sep 16–27): Molt + NF_LEDGER + CI gates**
- Q-MOLT-04, Q-NF-SCHEMA-01, (CI gate implementation)
- Unlocks Cycle 1 automation

**Phase 2 (Oct 1–15): Repo standardization**
- Q-SI-C1, Q-SI-C1-B2, Q-SI-C1-B3, (README/CLAUDE.md/docs across 31 repos)
- All repos to unified structure

**Phase 3 (Oct 15+): Governance activation**
- Molt cycle live, NF_LEDGER tracking, falsifiers operative
- Ad-hoc blockers resolve via priority queue

---

## Appended Events

```
2026-09-09 18:49 CST — Z2 (Night) ratified ORGANIZATION_BLUEPRINT_v1.md | PRIORITY_QUEUE.md v1_1 ratified | Phase 0 READY
2026-09-09 — Z1 created PRIORITY_QUEUE.md baseline from blueprint Q-GOVERNANCE-02 spec
```

