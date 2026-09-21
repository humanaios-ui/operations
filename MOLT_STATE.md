---
# MOLT_STATE.md — Molt Lifecycle State Machine

**Location:** `operations/MOLT_STATE.md` (canonical)  
**Status:** SPECIFICATION (Phase 1, Q-NF-SCHEMA-01)  
**Authority:** Z2 (Night) — ratifies molt state transitions  
**Enforcement:** CI gate validates state consistency, anti-cascade rules

> **Open candidate: Q-MOLT-TEMPORAL-PURITY-01 — molt closure is not a clock.**
> The measurement semantics in this file resolve a molt at `window_end`, which
> Q-TEMPORAL-DISSOLUTION-01 classifies as `INVALID_INTERNAL_DEADLINE`, and which
> `BOOT_PROCESS_MAP.md` already published as removed ("Molt `window_end` at
> timestamp" → "Molt completes when measurement criteria met") without this file
> being migrated to match. Both readings are currently live in the tree.
>
> The successor semantics are specified below under **Measurement closure**. They
> are **PROPOSED** and take effect on a Z2 ratification hash, not on merge. Until
> that hash exists, the v1 window fields remain the ratified shape and are read
> as `OBSERVATIONAL` provenance — see `z1-inbox/2026-09-21/Q-MOLT-TEMPORAL-PURITY-01.md`
> and the `O-MOLT-CYCLE ↔ O-TEMPORAL-GATE` row in `INTENT_GRAPH.yaml`.

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
| **MEASURED** | Code | Falsifier tested at closure; brier_actual computed over the pinned observation set. *(v1: at `window_end`. See **Measurement closure** — Q-MOLT-TEMPORAL-PURITY-01.)* | KEPT, REVERTED |
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
  "window_start": "2026-09-16T10:00:00Z",   ← v1; temporal_class: OBSERVATIONAL
  "window_end": "2026-09-23T00:00:00Z",     ← v1; retired as control under
                                            ←   Q-MOLT-TEMPORAL-PURITY-01
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

## Measurement closure

**Status: PROPOSED — Q-MOLT-TEMPORAL-PURITY-01. Not in force until a Z2 hash.**

### What is wrong with the v1 shape

A molt in v1 closes because a timestamp arrived. `window_days: 7` fixes the
close in advance, `window_end` names the instant, and the falsifier reads
"Brier score >= 0.20 **at window close**". Three consequences follow, and all
three are the failure Q-TEMPORAL-DISSOLUTION-01 exists to prevent:

1. **The verdict is a function of the calendar, not the evidence.** A molt with
   four resolved predictions and a molt with four hundred both resolve on day
   seven. The first produces a Brier score that means almost nothing and writes
   `KEEP` or `REVERT` against a constant anyway.
2. **The K=3 slot frees on a clock.** Anti-cascade concurrency is released by
   time passing rather than by a measurement completing, so the bound stops
   meaning "three things are being measured" and starts meaning "three things
   started recently".
3. **A molt can become late.** Once `window_end` is in the past and the outcome
   is unresolved, the row reads as late — and internal work that can be late
   solely because time passed is exactly the state the policy prohibits.

### The successor predicate

Closure is a **state predicate over a pinned observation set**, not an instant:

```yaml
measurement_gate:
  temporal_class: OBSERVATIONAL      # provenance only; no scheduling authority
  scheduling_authority: false

  # The molt is MEASURED when any closes_on predicate holds. Not before, and
  # not automatically when a date passes.
  #
  # No default is given on purpose. Q-MOLT-TEMPORAL-PURITY-01 open question 4
  # asks Z2 to set this per molt at ratification: the molt ledger has too few
  # closed molts to estimate a defensible number, and a placeholder printed here
  # would become the de facto policy by being the only number in the spec.
  min_resolved_observations: <Z2-set at ratification>
  observation_set_ref: <NF_LEDGER range or hash>   # pinned; makes it reproducible
  closes_on:
    - resolved_observations >= min_resolved_observations
    - constant_superseded_by_later_ratified_molt
    - z2_explicit_close                            # a decision, always available

  # Evidence-state invalidation. Replaces "the window expired".
  invalidated_by:
    - constant_changed_outside_this_molt
    - instrument_changed                            # the metric stopped meaning the same thing
    - observation_set_source_superseded

  opened_at: <RFC3339>               # HISTORICAL_RECORD once written; not a start gun
```

The falsifier is restated against the set rather than the instant:

```text
v1:  "Brier score >= 0.20 at window close"
v2:  "Brier score >= 0.20 over the pinned observation set at closure"
```

`prediction.window_days` is **retired as control** and retained, where a
pre-existing ratified molt carries it, as `HISTORICAL_RECORD`: it records the
normalization convention a measurement was reported under. It does not close
anything.

### Starvation is a resource state, not a deadline

The honest objection to removing the window is that a molt could hold a K=3 slot
forever if observations never arrive. Under the resource model that is a
**measurement-starvation** condition and is detected as one:

```text
MEASUREMENT_STARVED  ← the pinned observation set has not grown across N
                       consecutive resource censuses (default N=2)
```

This is a state-change predicate. It compares two measurements of the same set;
it reads no clock and it does not escalate. Its effect is a `GAUGE` callout to
Z2 with the slot and the starved molt named — Z2 then closes, reverts, or
reallocates. The slot is freed by a decision, which is where that authority
belongs, and never by the calendar.

This is the same substitution `RBE_TEMPORAL_MIGRATION_CANDIDATE.md` makes for
`review_cadence_days` (→ `min_completed_censuses` + state invalidators). The
molt cycle is the second consumer of that pattern, not a new one.

### What does not change

Anti-cascade rules 1–5 are untouched. One open molt per constant, K=3
system-wide, freeze after two consecutive reverts, no self-reference, queue-rank
precedence — none of these are time-derived, and none of them need to be. Rule 1
("no new candidate inside window W") re-reads as "no new candidate while the
prior molt on that constant is unclosed", which is what it was always trying to
say.

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
   
4. Observation set reaches min_resolved_observations; falsifier tested:
   - Prediction: Brier < 0.20
   - Actual: Brier = 0.14 over the pinned set
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
   
2. Observation set closes: falsifier fails
   Prediction: Brier < 0.20, Actual: Brier = 0.25
   State: MEASURED → REVERTED
   NF_LEDGER: M-A, outcome=REVERT
   F/IC candidate filed
   Constant X reverted to 0.5
   
3. Z1 proposes molt B: constant X (0.5 → 0.60)  [different target]
   State: PROPOSED
   Z2 approves
   State: RATIFIED, NF_LEDGER: M-B, outcome=MEASURING
   
4. Observation set closes: falsifier fails again
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
| APPLIED → MEASURED | a `closes_on` predicate holds, falsifier tested *(v1: `window_end` reached)* | outcome updated (KEEP or REVERT), brier_actual set |
| MEASURED → KEPT | Falsifier passed | Constant change permanent; next molt can propose |
| MEASURED → REVERTED | Falsifier failed | Constant reverted; F/IC candidate filed; freeze check |
| PROPOSED → CONTESTED | Z1 contest request, <48h of Z2 decision | MOLT_STATE marked contested; Z2 re-reads |
| CONTESTED → ACCEPTED | Z2 re-reads, approves with context | New ratification hash; → RATIFIED |
| CONTESTED → REJECTED | Z2 re-reads, declines | Rejected state, with contest_response in NF_LEDGER |

---

## Enforcement in CI

**z2_ratification_gate.yml** checks:
1. No REVERT → PROPOSED transition on the same constant while the prior molt's
   root cause is unidentified (anti-cascade rule 4). *(v1 read "within 48h";
   `BOOT_PROCESS_MAP.md` already publishes "Frozen until root cause identified".)*
2. No concurrent molts > K=3 (open_molt_count in anti_cascade_check)
3. All state transitions have required NF_LEDGER entries
4. Recorded timestamps are monotonically increasing. `temporal_class:
   OBSERVATIONAL` — this is a provenance-ordering check on the ledger, not a
   schedule; no transition is triggered by reaching any of these instants.

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

**Scope:** Pilot molt on single trading constant (rebalance correlation threshold). Falsifier: Sharpe ratio < 0.80 or realized max drawdown > 5%. Z2 ratifies; code applies; receipt reconciliation at closure determines KEEP or REVERT.

**Q-MOLT-TEMPORAL-PURITY-01 annotation.** The record above is left byte-exact: its
`ratification_hash` covers the string `7-day`, and re-deriving a Z2 signature over
edited text is not a Z1 act. It is read under the v1 semantics it was signed under.

Note that this molt is the case the successor predicate is for. `window_days: 7`
on a Sharpe ratio is a measurement window whose sample size is whatever the
market supplied; seven days of a thin series can produce a Sharpe that trips or
clears an 0.80 falsifier on noise alone. Under **Measurement closure** the same
molt would pin its observation set and close on `min_resolved_observations`, and
the 7-day figure would survive as the reporting normalization it actually is.

Z2 decision needed: re-ratify this molt under v2 with a new hash, or let it run
to closure under v1 as the last molt of the old shape. Z1 recommends the latter —
re-ratifying mid-measurement changes the instrument while it is reading.

---

## Open Questions for Z2

1. Should contested decisions create a new molt_id, or reuse the prior one with new hash?
2. How long is a constant frozen after 2 reverts? — **superseded by
   Q-MOLT-TEMPORAL-PURITY-01.** "How long" is the wrong axis; `BOOT_PROCESS_MAP.md`
   already answers "frozen until root cause identified". The open question is what
   counts as identified, and who says so.
3. Should MOLT_STATE.md be part of a separate molt_events.jsonl, or projections from NF_LEDGER entries only?
4. **Q-MOLT-TEMPORAL-PURITY-01:** what is the default `min_resolved_observations`,
   and is it per-constant or per-metric? Z1 has no basis for a number — the
   existing molt ledger has too few closed molts to estimate one. Proposed: Z2
   sets it per molt at ratification until enough closures exist to measure a
   default, rather than a placeholder constant nobody can defend.
5. **Q-MOLT-TEMPORAL-PURITY-01:** is `MEASUREMENT_STARVED` a `GAUGE` callout (Z1's
   proposal) or does it warrant its own callout row in CLAUDE.md?

(See Q-NF-SCHEMA-01 for additional context.)
