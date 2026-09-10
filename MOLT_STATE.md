---
# MOLT_STATE.md — Molt Lifecycle State Machine

**Location:** `operations/MOLT_STATE.md` (canonical)  
**Status:** SPECIFICATION (Phase 1, Q-NF-SCHEMA-01)  
**Authority:** Z2 (Night) — ratifies molt state transitions  
**Enforcement:** CI gate validates state consistency, anti-cascade rules

---

## Overview

**MOLT_STATE** is the authoritative record of all molt lifecycles in HumanAIOS. Each molt moves through predictable states: proposal → ratification → application → measurement → keep/revert.

**Relationship to NF_LEDGER:**
- Each molt entry in NF_LEDGER carries a `molt_id` and `outcome`
- MOLT_STATE tracks the **journey** (from PROPOSED to MEASURING to KEEP/REVERT)
- NF_LEDGER is the **permanent record** (append-only, hash-chained)

---

## State Machine

```
┌──────────────┐
│   PROPOSED   │  ← Z1 proposes molt_candidate to Priority Queue
└──────┬───────┘
       │ (Z2 decision)
       ├─→ REJECTED    (end state: Z2 rejects, no molt created)
       │
       ├─→ ACCEPTED    (Z2 approves, assigns molt_id, ratification hash)
       │   └─→ RATIFIED ← entry created in NF_LEDGER with outcome="MEASURING"
       │       │ (code applies constant change)
       │       └─→ APPLIED (constant updated, molt_id tracked)
       │           │ (window_end timestamp reached)
       │           └─→ MEASURED (falsifier tested, brier_actual computed)
       │               │ (outcome resolved)
       │               ├─→ KEPT      (prediction held, outcome="KEEP" written)
       │               │              end state: constant change permanent
       │               │
       │               └─→ REVERTED  (falsifier tripped, outcome="REVERT" written)
       │                             constant reverted to prior_value
       │                             F/IC candidate filed
       │                             end state: constant rolled back
       │
       └─→ CONTESTED (Z2 decision contested by Z1; re-read requested)
           └─→ ACCEPTED or REJECTED (new Z2 decision with contest_response)
```

---

## State Definitions

| State | Owner | What It Means | Next States |
|:------|:------|:-------------|:-----------|
| **PROPOSED** | Z1 | Molt candidate in Priority Queue, awaiting Z2 decision | ACCEPTED, REJECTED, CONTESTED |
| **REJECTED** | Z2 | Z2 declined the molt; no entry created | (terminal) |
| **ACCEPTED** | Z2 | Z2 approved; molt_id assigned, ratification hash computed | RATIFIED |
| **RATIFIED** | Z2 | Z2 signature on molt complete; code can apply | APPLIED |
| **APPLIED** | Code | Constant changed to proposed_value; molt_id tracked on constant | MEASURED |
| **MEASURED** | Code | Falsifier tested at window_end; brier_actual computed | KEPT, REVERTED |
| **KEPT** | Code | Prediction held; constant change permanent | (terminal) |
| **REVERTED** | Code | Falsifier tripped; constant rolled back to prior_value | (terminal, but may trigger new molt) |
| **CONTESTED** | Z1 | Z1 contests Z2 decision; re-read requested within 48h | ACCEPTED, REJECTED (with contest_response) |

---

## NF_LEDGER Entry Fields Mapped to State

Each MOLT_STATE entry corresponds to an NF_LEDGER row. Progression is encoded in the `outcome` field:

```json
{
  "molt_id": "M-20260916-0001",
  "constant": "behavior_spec.json:impact_dial",
  "prior_value": 0.5,
  "proposed_value": 0.55,
  "prediction": {
    "metric": "Brier",
    "target": 0.15,
    "window_days": 7,
    "falsifier": "Brier score >= 0.20 at window close"
  },
  "z2_ratified_at": "2026-09-16T10:00:00Z",
  "ratification_hash": "sha256(...)",
  "window_start": "2026-09-16T10:00:00Z",
  "window_end": "2026-09-23T00:00:00Z",
  "outcome": "MEASURING",           ← State marker
  "brier_actual": null,            ← Set at MEASURED
  "timestamp": "2026-09-16T10:00:00Z",
  "prior_hash": "abc123...",
  "hash": "def456..."
}
```

**State indicators in NF_LEDGER:**
- `outcome="MEASURING"` ← APPLIED state (waiting for window_end)
- `outcome="KEEP"` + `brier_actual` ← KEPT state
- `outcome="REVERT"` + `prior_value` restoration ← REVERTED state
- `outcome="HISTORICAL"` ← Backfilled from v0.1, not part of molt cycle

---

## Examples: Molt Sequences

### Example 1: Simple KEEP

```
1. Z1 proposes molt to increase impact_dial (0.5 → 0.55)
   State: PROPOSED
   
2. Z2 approves in REGISTERED.md with ratification hash
   State: ACCEPTED → RATIFIED
   NF_LEDGER entry created: molt_id=M-0001, outcome=MEASURING
   
3. Code applies: impact_dial = 0.55, tracked as molt M-0001
   State: APPLIED
   
4. Seven days later, falsifier tested:
   - Prediction: Brier < 0.20
   - Actual: Brier = 0.14
   - Result: PASS (prediction held)
   State: MEASURED → KEPT
   NF_LEDGER updated: outcome=KEEP, brier_actual=0.14
   
5. End state: constant change permanent, next molt can propose further changes
```

### Example 2: REVERT + Anti-Cascade Freeze

```
1. Z1 proposes molt A: constant X (0.5 → 0.55)
   State: PROPOSED
   Z2 approves
   State: RATIFIED, NF_LEDGER: M-A, outcome=MEASURING
   
2. Seven days later: falsifier fails
   Prediction: Brier < 0.20, Actual: Brier = 0.25
   State: MEASURED → REVERTED
   NF_LEDGER: M-A, outcome=REVERT
   F/IC candidate filed
   Constant X reverted to 0.5
   
3. Z1 proposes molt B: constant X (0.5 → 0.60)  [different target]
   State: PROPOSED
   Z2 approves
   State: RATIFIED, NF_LEDGER: M-B, outcome=MEASURING
   
4. Seven days later: falsifier fails again
   Prediction: Brier < 0.18, Actual: Brier = 0.22
   State: MEASURED → REVERTED
   NF_LEDGER: M-B, outcome=REVERT
   
5. Anti-cascade freeze triggered:
   - Constant X reverted twice in a row (M-A REVERT, M-B REVERT)
   - Per anti-cascade rule 4: constant X now FROZEN
   - No new molts can propose changes to X until Z2 Tier-2 ruling
   - Z2 either: (a) reopens with new context, or (b) retires the constant
```

### Example 3: Contested Decision

```
1. Z1 proposes molt C
   State: PROPOSED
   
2. Z2 rejects (REJECTED state)
   
3. Z1 contests within 48h: "IC-disputed, Z2 decision contested"
   State: CONTESTED
   
4. Z2 re-reads + context; issues new ratification with contest_response
   New decision: ACCEPT (overrides prior rejection)
   State: ACCEPTED → RATIFIED
   NF_LEDGER entry created with new molt_id
   
5. Molt proceeds from RATIFIED onward
```

---

## Anti-Cascade State Tracking

Each NF_LEDGER entry includes `anti_cascade_check`:

```json
{
  "anti_cascade_check": {
    "open_molt_count": 1,
    "reverts_on_constant": 1,
    "rank_in_queue": 4,
    "frozen_constant": false
  }
}
```

**State changes triggered by anti-cascade:**
- `reverts_on_constant` increments on REVERT
- `reverts_on_constant == 2` → `frozen_constant = true`
- `frozen_constant = true` → blocks new PROPOSED molts on that constant
- `open_molt_count` at apply time; error if > K (K=3)

---

## State Diagram (Formal)

```
START
  │
  ├─ PROPOSED ──(Z2 rejects)──→ REJECTED (terminal)
  │
  ├─ PROPOSED ──(Z2 accepts)──→ ACCEPTED
  │                                 │
  │                          (generate molt_id + hash)
  │                                 │
  │                             ↓
  │                          RATIFIED
  │                                 │
  │                          (code applies change)
  │                                 │
  │                             ↓
  │                          APPLIED ────→ MEASURED ─┐
  │                                      (test falsifier)
  │                                                   │
  │                        ┌─────────────────────────┴────────────────────┐
  │                        │                                              │
  │                    ↓ (PASS)                                  ↓ (FAIL)
  │                   KEPT                                     REVERTED
  │                 (terminal)                            (→ freeze check)
  │                                                       (terminal)
  │
  └─ PROPOSED ──(Z1 contests, <48h)──→ CONTESTED
                                           │
                                   (Z2 re-reads)
                                           │
                                    ┌──────┴──────┐
                                    │             │
                               ↓ (ACCEPT)    ↓ (REJECT)
                             ACCEPTED       REJECTED
                            (→ RATIFIED)    (terminal)
                            
END
```

---

## Transitions and Preconditions

| Transition | Precondition | Postcondition |
|:-----------|:-------------|:--------------|
| PROPOSED → ACCEPTED | Z2 reads candidate + falsifier | molt_id assigned, ratification_hash computed |
| PROPOSED → REJECTED | Z2 reads + decides no | (no NF_LEDGER entry) |
| ACCEPTED → RATIFIED | Code invoked at session open | NF_LEDGER entry created, outcome=MEASURING |
| RATIFIED → APPLIED | Code executes constant assignment | constant updated with molt_id tracking |
| APPLIED → MEASURED | window_end reached, falsifier tested | outcome updated (KEEP or REVERT), brier_actual set |
| MEASURED → KEPT | Falsifier passed | Constant change permanent; next molt can propose |
| MEASURED → REVERTED | Falsifier failed | Constant reverted; F/IC candidate filed; freeze check |
| PROPOSED → CONTESTED | Z1 contest request, <48h of Z2 decision | MOLT_STATE marked contested; Z2 re-reads |
| CONTESTED → ACCEPTED | Z2 re-reads, approves with context | New ratification hash; → RATIFIED |
| CONTESTED → REJECTED | Z2 re-reads, declines | Rejected state, with contest_response in NF_LEDGER |

---

## Enforcement in CI

**z2_ratification_gate.yml** checks:
1. No REVERT → PROPOSED transition on same constant within 48h (anti-cascade rule 4)
2. No concurrent molts > K=3 (open_molt_count in anti_cascade_check)
3. All state transitions have required NF_LEDGER entries
4. Timestamps are monotonically increasing (window_start < window_end < timestamp)

---

## Relationship to PRIORITY_QUEUE.md

Molt candidates enter the queue at PROPOSED state, ranked by:
```
Score = impact + Σ(impact of items this unblocks)
```

**Molt ranking precedence:**
- Anti-cascade rule 5: Molt candidates ranked by Priority Queue score; no bypassing
- High-score molts prioritized over low-score proposals
- Molts on frozen constants blocked regardless of score

---

## Success Criteria (Phase 1 Close)

- ✅ MOLT_STATE.md published in operations/
- ✅ All molt transitions logged in NF_LEDGER with consistent outcome values
- ✅ Anti-cascade state tracking working (open_molt_count, reverts_on_constant, frozen check)
- ✅ Freeze rule verified: 2 consecutive reverts on same constant blocks new proposals
- ✅ Z2 can ratify molts; code applies + measures; outcomes recorded
- ✅ Falsifier doctrine enforced across all molts (no molt without falsifier)

---

## Open Questions for Z2

1. Should contested decisions create a new molt_id, or reuse the prior one with new hash?
2. How long is a constant frozen after 2 reverts? Indefinite until Z2 Tier-2 ruling, or auto-unfreeze after N months?
3. Should MOLT_STATE.md be part of a separate molt_events.jsonl, or projections from NF_LEDGER entries only?

(See Q-NF-SCHEMA-01 for additional context.)
