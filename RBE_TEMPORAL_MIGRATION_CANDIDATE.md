# RBE_TEMPORAL_MIGRATION_CANDIDATE.md

**Candidate:** Q-RBE-TEMPORAL-PURITY-01  
**Parent gate:** Q-TEMPORAL-DISSOLUTION-01 / #378  
**Status:** PROPOSED — no change to ratified `RESOURCE_UNITS.yaml` or `constants.json` until separate Z2 ratification  
**Purpose:** remove hidden calendar authority from RBE-OPS without weakening its measurement discipline

## Why this candidate exists

RBE-OPS v0.1 correctly establishes non-commensurable resource vectors, a binding-constraint allocator, a resource ledger, and measured yield density. It also contains several clock-normalized controls inherited from earlier governance:

- `review_cadence_days`;
- `measurement_window_days`;
- unit `period: week/month/day` fields;
- PRICE rates described as expiring with a named time window;
- `STALE-day` / half-life assurance decay;
- trigger/falsifier prose such as “90 days” or “4 weeks of capacity.”

Under Q-TEMPORAL-DISSOLUTION-01, clocks may measure behavior but may not create internal work priority, expiry, escalation, refill, or authority.

## Migration principles

### 1. Preserve the natural-unit vector

Do not introduce a numeraire or generic “effort unit.” `RESOURCE_UNITS.yaml` remains the unit SSOT.

### 2. Replace calendar control with observation/state control

Examples:

```text
OLD: review every 14 days
NEW: re-evaluate after the next two completed resource censuses or when a material source changes

OLD: measure over 28 days
NEW: measure over N resolved observations / completed allocation epochs, with the observation set pinned

OLD: expire a shadow price after N days
NEW: invalidate when the underlying constraint, substitution regime, or source evidence changes; otherwise require a new measured PRICE event before replacement

OLD: capacity refills each week/month
NEW: capacity changes only when measured or explicitly allocated; calendar boundaries alone have no effect
```

### 3. Separate normalization from control

A rate may still be *reported* as `RAT-min/week` or `CI-min/month` for comparison if that is the measurement convention. Such a denominator is `OBSERVATIONAL`; it must not function as an automatic refill scheduler.

### 4. Preserve genuine resource depletion

`RUN-day` can remain a capital-stock measurement because it represents remaining operating capacity, not a work deadline. If the measured stock reaches zero, work may halt because the resource is depleted — not because an arbitrary due date arrived.

## Proposed `RESOURCE_UNITS.yaml` v0.2 changes

These are candidates, not landed edits.

### Constraint review

Replace:

```yaml
review_cadence_days: 14
```

with an event predicate such as:

```yaml
review_trigger:
  kind: OBSERVATION_COUNT_OR_STATE_CHANGE
  min_completed_censuses: 2
  immediate_on:
    - binding_constraint_source_changed
    - capacity_measurement_changed
    - obligation_definition_changed
```

### Flow periods

Retain period labels only as measurement metadata and make their lack of scheduling authority explicit:

```yaml
normalization:
  temporal_class: OBSERVATIONAL
  unit: week
  scheduling_authority: false
  auto_refill: false
```

Actual capacity comes from CAP/measurement/allocation state.

### Shadow PRICE evidence

Replace mandatory time expiry with a pinned observation set and event invalidators:

```yaml
price_validity:
  observation_set_ref: <ledger range/hash>
  min_n: 8
  constraint: <registered unit>
  invalidated_by:
    - constraint_changed
    - source_superseded
    - substitution_regime_changed
```

A timestamp may be recorded for provenance but does not itself invalidate or replace the rate.

### Assurance staleness

`STALE-day` is the strongest semantic conflict because assurance currently degrades as a function of elapsed days.

Candidate successor: an event/state liability such as `DRIFT-row`:

> one ratified artifact whose cited source/dependency has changed, disappeared, become unreproducible, or failed re-verification since ratification.

The final symbol/name must be ratified separately. The required property is event-based invalidation rather than age-based decay.

## Proposed `constants.json` migration

For resource/governance constants, replace calendar trigger windows with sample/state predicates.

Examples:

```text
measurement_window_days: 28
```

becomes conceptually:

```yaml
measurement_gate:
  min_completed_censuses: 2
  min_resolved_observations: <N where applicable>
  observation_set_ref_required: true
```

Specific targets include:

- `QUEUE_SCORING_MODE` — evaluate against completed census / priced-work evidence, not after N days;
- `CONSTRAINT_UNIT` — already uses consecutive censuses; remove redundant day window as authority;
- `SHADOW_PRICE_MIN_N` — retain observation-count falsifier; remove “90 days” trigger as enforcement;
- `UNPRICED_ROW_POLICY` — evaluate against priced-row and measured-SPEND evidence, not 28-day passage.

This candidate does not alter unrelated scientific observation windows where time is part of the phenomenon being measured and has no work-scheduling authority.

## Acceptance conditions

A v0.2 migration is acceptable only if:

1. `RESOURCE_UNITS.yaml` remains non-commensurable and instrument-first;
2. no resource capacity automatically refills solely because a calendar boundary passes;
3. no governance artifact loses authority solely because it became N days old;
4. no queue item changes priority solely because it waited longer;
5. shadow-price replacement requires new evidence/state, not just time passage;
6. resource-mode allocation in `priority_queue_engine.py` remains governed and test-covered;
7. historical v0.1 ratification/provenance is preserved;
8. Z2 ratifies the migration as a new version/hash rather than overwriting v0.1 semantics silently.

## Falsifier

This candidate fails if converting clock-driven controls to event/state predicates makes resource availability or assurance materially less measurable, or if any replacement predicate cannot be mechanically observed and reproduced.
