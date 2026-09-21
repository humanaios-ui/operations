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

## Tier Measurement (PROPOSED state)

Tier is no longer an opinion carried in prose. It is measured from the set of
filepaths a diff touches, by `tools/molting_protocol_diff_v1_0.py`:

| Tier | Rule | Obligation |
|:-----|:-----|:-----------|
| **0** | Touches no CONSTANTS path and no GATE path | Not a molt; consumes no slot against K=3 |
| **1** | Touches ≥1 CONSTANTS path | Needs `molt_id`, prediction, measurement window |
| **2** | Touches ≥1 GATE path | Needs registry entry + ADV run before KEEP |

The tier is the **maximum** over every path in the diff. The two path lists are
the published rule; they live as data at the top of the classifier so that a
disputed tier is settled by reading a list rather than by re-arguing.

```yaml
molt_classifier_version: 1.1.0
molt_classifier_tool: tools/molting_protocol_diff_v1_0.py
molt_tier_measured_at_pr_open: true
molt_tier_check_blocking: false          # advisory; measures, does not gate
under_claim_falsifier: >-
  Zero PRs under-claim molt tier by more than one level. Measured as
  (PRs with measured - claimed > 1) / (total PRs) over a rolling 30-day
  window; target < 5%. Directional on purpose: an absolute |claimed -
  measured| would count a two-level OVER-claim as a falsifier trip, and
  molt_tier_gap_record scores over-claims LOW — over-claiming costs
  caution, under-claiming is how a gate change merges labelled "not a
  molt". A sustained under-claim pattern is a DRIFT callout to Z2, not a
  per-PR rejection.
```

**Z2 note — two open items this creates.** (1) ~~The gap rows are currently
retained as CI build artifacts~~ **Superseded: one row per merged PR is now
posted to the molt-tier tracking issue by `molt-tier-check.yml`'s `capture` job
and drained weekly by `smag-consolidate.yml` into
`audits/molt_tier_gap_ledger.jsonl`, which is what makes the falsifier above
computable (tracking issue #350). The build artifact is kept as a per-run debug
copy only.

The captured row is the snapshot the advisory comment recorded **at PR open**,
copied on merge — not a re-measurement. `molt_tier_measured_at_pr_open: true`
above is the contract, and a merge-time recompute would break it twice over:
`molt_tier_claimed` is read from the PR body, which the author can edit after
seeing the advisory result, and the classifier itself may change while a PR is
open. A PR merged with no advisory comment therefore records no row — the series
carries an honest gap rather than a merge-time guess.** Wiring them into the SMAG
self-accuracy ledger
at `data/lessons_learned_ledger.json` waits on the meta-SMAG consumer. (2) The
classifier reports `molt_tier_measured`; nothing yet *enforces* that a measured
Tier 1 carries a `molt_id`, or that a measured Tier 2 carries a registry entry
and an ADV run. Measurement precedes enforcement on purpose — promote only once
the field is actually being filled in.

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

## Ratified Molt: Q-BLOCKCHAIN-TRADING-CALIBRATION-W90PD1-MOL-001

**Z2 Ratification:** 2026-09-21T00:00:00Z | by=carly.r.anderson@gmail.com | decision=ACCEPT  
**Ratification Hash:** `sha256(Q-BLOCKCHAIN-TRADING-CALIBRATION-W90PD1-MOL-001|Z-012|rebalance_threshold|0.50→0.55|Sharpe>=0.80|7-day|by=carly.r.anderson@gmail.com|at=2026-09-21T00:00:00Z)`

```json
{
  "molt_id": "Q-BLOCKCHAIN-TRADING-CALIBRATION-W90PD1-MOL-001",
  "zone": "Z-012",
  "constant": "trading_spec.json:rebalance_threshold",
  "prior_value": 0.50,
  "proposed_value": 0.55,
  "prediction": {
    "metric": "Sharpe",
    "target": ">= 0.80",
    "window_days": 7,
    "falsifier": "Sharpe < 0.80 OR realized_drawdown > 5%"
  },
  "z2_ratified_at": "2026-09-21T00:00:00Z",
  "z2_ratifier": "carly.r.anderson@gmail.com",
  "ratification_hash": "sha256(Q-BLOCKCHAIN-TRADING-CALIBRATION-W90PD1-MOL-001|Z-012|rebalance_threshold|0.50→0.55|Sharpe>=0.80|7-day|by=carly.r.anderson@gmail.com|at=2026-09-21T00:00:00Z)",
  "window_start": "2026-09-21T00:00:00Z",
  "window_end": "2026-09-28T00:00:00Z",
  "outcome": "APPLIED"
}
```

**Scope:** Pilot molt on single trading constant (rebalance correlation threshold). Measures 7 days. Falsifier: Sharpe ratio < 0.80 or realized max drawdown > 5%. Z2 ratifies; code applies; receipt reconciliation at window_end determines KEEP or REVERT.

---

## Open Questions for Z2

1. Should contested decisions create a new molt_id, or reuse the prior one with new hash?
2. How long is a constant frozen after 2 reverts? Indefinite until Z2 Tier-2 ruling, or auto-unfreeze after N months?
3. Should MOLT_STATE.md be part of a separate molt_events.jsonl, or projections from NF_LEDGER entries only?

(See Q-NF-SCHEMA-01 for additional context.)
