# Q-MOLT-TEMPORAL-PURITY-01 — molt closure is a state predicate, not a clock

**Type:** IC (Implementation Candidate) · Tier 2 (touches a GATE path)
**Author:** Z1 (Claude)
**Status:** awaiting_ratification
**Parent gate:** Q-TEMPORAL-DISSOLUTION-01 / #378
**Sibling:** Q-INTENT-GRAPH-01 (the structural half of this finding)

---

## The finding

`MOLT_STATE.md` resolves a molt when a timestamp arrives. `prediction.window_days`
fixes the close in advance, `window_end` names the instant, `brier_actual` is
computed "at window close", and the CI gate asserts `window_start < window_end <
timestamp`. A molt verdict — whether a ratified constant change is kept or rolled
back — is therefore a function of the calendar.

`TEMPORAL_DISSOLUTION_POLICY.md` classifies exactly this as
`INTERNAL_WORK_DEADLINE` / `INVALID_INTERNAL_DEADLINE` and prohibits it.

`BOOT_PROCESS_MAP.md` already published the successor reading:

> ~~"Molt window_end at timestamp"~~ → "Molt completes when measurement criteria met"

`MOLT_STATE.md` was never migrated to match. Both readings have been live in the
tree simultaneously since the boot map merged. This is an **AMBIGUITY** callout
under CLAUDE.md's mandatory-trigger table: two governance surfaces give
conflicting answers on the same topic.

### Three consequences, not one

1. **The verdict is independent of the evidence.** A molt with four resolved
   predictions and one with four hundred both resolve on day seven. The first
   writes `KEEP` or `REVERT` against a ratified constant on a Brier score that
   means almost nothing.
2. **The anti-cascade bound decays.** K=3 releases a slot when a clock runs out
   rather than when a measurement completes, so the bound stops meaning "three
   things are being measured" and starts meaning "three things started recently".
3. **A molt can be late.** An unresolved molt past `window_end` reads as overdue
   internal work, which is the state the policy exists to make impossible.

The ratified pilot molt `Q-BLOCKCHAIN-TRADING-CALIBRATION-W90PD1-MOL-001` is a
live instance: a Sharpe-ratio falsifier at 0.80 closing on a 7-day window has
whatever sample size the market happened to supply, and seven days of a thin
series can trip or clear that threshold on noise.

---

## Proposal

### 1. Closure by pinned observation set

Replace window-instant closure with a state predicate. Specified in full at
`MOLT_STATE.md` § **Measurement closure**; summarized:

```yaml
measurement_gate:
  temporal_class: OBSERVATIONAL
  scheduling_authority: false
  min_resolved_observations: <N>                 # set by Z2 at ratification
  observation_set_ref: <NF_LEDGER range or hash> # pinned; reproducible
  closes_on:
    - resolved_observations >= min_resolved_observations
    - constant_superseded_by_later_ratified_molt
    - z2_explicit_close
  invalidated_by:
    - constant_changed_outside_this_molt
    - instrument_changed
    - observation_set_source_superseded
  opened_at: <RFC3339>                           # provenance; not a start gun
```

Falsifier phrasing moves from "at window close" to "over the pinned observation
set at closure". `window_days` is retired as control and retained, where a prior
ratified molt carries it, as `HISTORICAL_RECORD` reporting normalization.

This is the same substitution `RBE_TEMPORAL_MIGRATION_CANDIDATE.md` already makes
for `review_cadence_days` (→ `min_completed_censuses` + state invalidators). The
molt cycle is that pattern's second consumer, not a new mechanism.

### 2. Starvation as a resource state

The honest objection: without a window, a molt could hold a K=3 slot forever.
Answer — detect it as a measured condition, not a deadline:

```text
MEASUREMENT_STARVED ← the pinned observation set has not grown across N
                      consecutive resource censuses (proposed default N=2)
```

Two measurements of the same set are compared. No clock is read. Effect is a
`GAUGE` callout to Z2 naming the slot and the starved molt; Z2 closes, reverts,
or reallocates. The slot is freed by a decision, never by the calendar.

### 3. Scope correction on the gate

`MOLT_STATE.md` was absent from the active-control-surface list in
`TEMPORAL_DISSOLUTION_POLICY.md` and from `CONTROL_EXACT` in
`tests/test_temporal_dissolution_gate.py`. Root `.md` files are not caught by
that test's suffix rule, so control surfaces of this shape must be named
explicitly. **This omission is why the defect survived the first audit pass.**
Both lists are extended in this diff (`MOLT_STATE.md`, `INTENT_GRAPH.yaml`).

This makes the candidate **Tier 2** — it touches a gate path — so it needs a
registry entry and an ADV run before KEEP, per `MOLT_STATE.md` § Tier Measurement.

### 4. Recorded, not fixed here

Three further instances of the same defect are recorded in
`TEMPORAL_CONTROL_AUDIT.md` § Second pass and deliberately **not** changed in
this diff:

| Surface | Why deferred |
|---|---|
| `FRAMEWORK_MAPPING.md` ("Stop Condition = Window close date") | unratified candidate Q-FRAMEWORK-MAPPING-01; Z2 should rule on it as one decision, not have Z1 edit a pending block |
| `CLAUDE.md` (48h decision window, contest rights expiring) | changes the authority document's own escalation model; Z2's call, and larger than this candidate |
| `z1-inbox/INDEX.yaml` (`decision_window_days: 2`) + `.z1-control/validate.py` | same decision as the CLAUDE.md row; splitting them would leave the two disagreeing again |
| `molt_ledger.py` (`window_close_at = now + 30 days`, marked `# Stub`) | code change; lands with the ratified `measurement_gate` shape, not before it |

---

## Resource cost

Per `TEMPORAL_CONTROL_AUDIT.md`, `CANDIDATE_BLOCK_TEMPLATE.md`'s scalar
`estimated_effort_units` is recorded DRIFT (a scalar numeraire violates
`P-NON-COMMENSURABLE`). Cost is given as a vector in registered symbols:

```yaml
resource_cost:
  Z1-ktok: 48        # spent: audit, specification, gate change, this block
  RAT-min: 30        # Z2 read of the specification and the two open numbers
  CI-min: 2          # temporal gate + intent graph check
  Z3-hr: 0           # nothing to execute until ratified
dependencies:
  - TEMPORAL_DISSOLUTION_POLICY.md
  - BOOT_PROCESS_MAP.md
  - RBE_TEMPORAL_MIGRATION_CANDIDATE.md
  - MOLT_STATE.md
blocking_on: []
```

---

## Impact prediction

**resource_impact: 7** — the molt cycle is the only mechanism by which a
constant changes under measurement. A verdict mechanism that can fire on
insufficient evidence corrupts every constant it touches, and the corruption is
invisible because the ledger records a number either way.

**Positive:**
- A molt verdict becomes a statement about evidence rather than about elapsed days.
- K=3 recovers its meaning: three measurements in flight.
- `MOLT_STATE.md` is under the temporal gate, so this class of defect is refused
  mechanically rather than found by a human reading two files.

**Risks:**
- A molt with no arriving observations holds a slot until a Z2 decision. Mitigated
  by `MEASUREMENT_STARVED`, but the mitigation costs `RAT-min` rather than being
  free the way a window was. This is the honest trade: the calendar was doing
  unpriced work, and pricing it makes the cost visible.
- `min_resolved_observations` has no defensible default yet (open question 4 in
  `MOLT_STATE.md`). Z1 proposes Z2 set it per molt rather than Z1 inventing a
  constant. **If Z2 wants a default, Z1 cannot supply one from current evidence.**
- Tier 2 gate change: a bug in the `CONTROL_EXACT` addition could block unrelated
  merges touching `MOLT_STATE.md`. The gate scans added lines only, and this diff
  passes it.

---

## Falsifier

This candidate is FALSE if any of the following holds after the migration lands:

1. A molt reaches `MEASURED` without a resolvable `observation_set_ref`, or with
   fewer resolved observations than its own `min_resolved_observations` — i.e.
   closure still happens on something other than the evidence.
2. Any closure predicate in the shipped shape can be evaluated from a timestamp
   alone, without reading the observation set.
3. `MEASUREMENT_STARVED` cannot be computed from two consecutive resource
   censuses without reference to a clock.
4. Adding `window_end:` or an equivalent unclassified internal deadline to
   `MOLT_STATE.md` does **not** fail `tests/test_temporal_dissolution_gate.py`
   after this diff.
5. The migration makes molt outcomes materially **less** measurable than the
   window shape — inherited from `RBE_TEMPORAL_MIGRATION_CANDIDATE.md`'s own
   falsifier, which this candidate must not violate.

Condition 4 is mechanically testable today: add such a line, run the gate with
`TEMPORAL_SCAN_ENFORCE=1`, observe the failure.

---

## Evidence

- `MOLT_STATE.md` — `window_start`, `window_end`, `prediction.window_days`;
  state table MEASURED row; transition table APPLIED → MEASURED; CI enforcement
  item 4
- `BOOT_PROCESS_MAP.md` § No Time-Based Gates — "Molt window_end at timestamp"
  listed as REMOVED
- `TEMPORAL_DISSOLUTION_POLICY.md` § Temporal classes — `INTERNAL_WORK_DEADLINE`
- `TEMPORAL_CONTROL_AUDIT.md` § Second pass — full row-by-row classification
- `RBE_TEMPORAL_MIGRATION_CANDIDATE.md` § 2 — the precedent substitution
- `molt_ledger.jsonl` — the ratified pilot molt carrying `window_days: 7`
- `INTENT_GRAPH.yaml` — `O-MOLT-CYCLE ↔ O-TEMPORAL-GATE`, status OPEN
- **`.z1-control/validate.py`, live output on this diff** — the strongest single
  piece of evidence, because it is a gate running today rather than a config key:

  ```
  ::warning::Q-REGISTRY-AUDIT-01: awaiting Z2 for 6d past the 2d window
             (due 2026-09-15) — CLAUDE.md routes this to Admiral re-read
  ...
  z1-inbox: OK — 69 candidates (60 awaiting Z2, 40 past the 2d window)
  ```

  Forty rows are "past the 2d window" and routed to Admiral re-read. Nothing
  about those candidates changed; a date passed. This is `INVALID_INTERNAL_DEADLINE`
  operating in CI: elapsed time manufacturing an escalation path, and forty
  simultaneous escalations to a single ratifier, which is indistinguishable from
  no signal at all. Under the resource model the true statement is that Z2 has
  60 candidates outstanding against finite `RAT-min` — a backpressure condition
  that should stop Z1 producing more governance work, which is the opposite of
  what "escalate to Admiral" does.

---

## What Z2 is being asked to decide

1. **Ratify or reject** the `measurement_gate` closure shape (MOLT_STATE.md
   § Measurement closure).
2. **Set or defer** `min_resolved_observations` policy — per-molt at ratification
   (Z1's proposal) or a global default Z2 supplies.
3. **Rule on the ratified pilot molt**: let it run to closure under v1 (Z1
   recommends — re-ratifying mid-measurement changes the instrument while it is
   reading), or re-ratify under v2 with a new hash.
4. **Confirm the gate scope change** (`MOLT_STATE.md`, `INTENT_GRAPH.yaml` added
   to `CONTROL_EXACT`) — a Tier 2 change requiring a registry entry and an ADV run.
5. **Sequence the four deferred surfaces** above, which are the same defect and
   should land as one decision rather than four drifting ones.

```yaml
z2_decision:
  status: awaiting_ratification
  ratified_at: null
  ratification_hash: null
  z2_notes: ""
```
