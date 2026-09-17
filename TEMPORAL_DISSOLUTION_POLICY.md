# TEMPORAL_DISSOLUTION_POLICY.md

**Policy ID:** Q-TEMPORAL-DISSOLUTION-01  
**Authority:** Z2 / Night  
**Model:** RBE-OPS resource/state scheduling  
**Status:** proposed on branch; effective only after merge and required review

## Canonical RBE parent

This policy is **not a second resource model**. It is a temporal-purity constraint on the resource-based economics architecture already present in HumanAIOS.

Canonical resource artifacts remain:

- `docs/RESOURCE_BASED_ECONOMICS.md` — RBE-OPS regime and allocation logic;
- `RESOURCE_UNITS.yaml` — ratified non-commensurable resource-unit registry;
- `ledgers/RESOURCE_LEDGER.jsonl` — resource accounting evidence;
- `tools/resource_ledger_v0_1.py` and `tools/resource_census_v0_1.py` — resource instruments;
- `priority_queue_engine.py` — two-band constraint allocation machinery;
- `constants.json` — ratified activation state for resource-mode queue controls.

`RESOURCE_UNITS.yaml` remains the unit SSOT. Resource costs must be vectors keyed by registered symbols such as `RAT-min`, `Z1-ktok`, `Z3-hr`, and `CI-min`; no new scalar numeraire is introduced here.

## Invariant

HumanAIOS does not schedule internal work by elapsed time.

Work becomes executable when its required authority, dependencies, resources, evidence, and safety predicates are satisfied. Work pauses or yields when those predicates are not satisfied.

```text
READY(work) = AUTHORITY ∧ DEPENDENCIES ∧ RESOURCES ∧ EVIDENCE ∧ SAFETY
```

No agent may create urgency, escalation, expiry, priority, or authority from elapsed time alone.

## RBE allocation compatibility

Temporal dissolution preserves the existing RBE allocation principle:

```text
Band A — work consuming 0 units of the binding constraint:
         rank by impact / downstream capacity unlocked; run when other predicates permit.

Band B — work consuming the binding constraint:
         rank by yield per measured constraint-unit.

Unpriced work:
         not schedulable when the ratified unpriced-row policy refuses it.
```

A timestamp, age, due date, or amount of waiting is **not** part of the ranking numerator or denominator.

## Temporal classes

| Class | Permitted | Scheduling authority |
|---|---|---|
| `OBSERVATIONAL` | timestamps, durations, measurement windows, rate-normalization periods | none |
| `TECHNICAL_SAFETY` | request timeout, retry backoff, lease/token expiry, dead-process detection, cache TTL, lock reclamation | protects technical correctness/resources only; cannot reprioritize human work |
| `REGULATORY_EXTERNAL` | evidenced externally imposed regulatory/legal/compliance deadlines | allowed only with complete exception contract + explicit Z2 ratification |
| `HISTORICAL_RECORD` | archival records of dates/deadlines that already occurred | none |
| `INTERNAL_WORK_DEADLINE` | internal due dates, arbitrary windows, AI-created urgency | prohibited |

## Regulatory exception contract

A time-based priority override is invalid unless all fields are present and non-empty:

```yaml
external_constraint:
  type: REGULATORY_DEADLINE
  temporal_class: REGULATORY_EXTERNAL
  authority: <issuing authority>
  citation: <statute/regulation/order/mandate>
  due_at: <RFC3339 timestamp>
  evidence_ref: <immutable source/artifact>
  impact_if_missed: <consequence>
  z2_ratified: true
  ratification_ref: <durable decision/hash/comment reference>
```

No regulatory evidence means no deadline semantics.

An external commercial, grant, funding, conference, or partner window may be real contextual information but is **not automatically `REGULATORY_EXTERNAL`** and does not automatically override the resource queue.

## Resource-state scheduling

Canonical work states:

```text
CANDIDATE
RESOURCE_REQUESTED
ELIGIBLE
ADMITTED
RESOURCES_RESERVED
RUNNING
VERIFYING
COMPLETE
RESOURCES_RELEASED

BLOCKED_RESOURCE
BLOCKED_DEPENDENCY
BLOCKED_AUTHORITY
BLOCKED_EVIDENCE
BLOCKED_SAFETY
YIELDED
RESOURCE_EXHAUSTED
REWORK_REQUIRED
```

Avoid internal work states such as `LATE`, `OVERDUE`, `RUSH`, `DUE_SOON`, or time-derived escalation.

## Work-conserving allocator

```text
IF eligible work exists AND usable capacity exists:
    select the highest-value eligible workload under the ratified RBE allocation rule
    reserve required resources
    execute within authority and safety floors
ELSE:
    idle or wait for a state/resource change
```

Agent availability does not itself create work.

## Backpressure

Autonomous producers must not flood a scarce downstream resource.

Examples:
- no Z2/RAT-min capacity -> do not create additional Z2-dependent governance work unless it directly reduces an active blocker;
- no independent-review capacity -> builders stop at awaiting-review state;
- exhausted tool/write/token/CI capacity -> yield or continue bounded read-only analysis if useful.

Backpressure is triggered by **measured resource state**, not by age of the queue.

## Cycles are allocation epochs, not timeboxes

A HumanAIOS cycle is an accounting/allocation epoch, not a duration.

A cycle may open when capacity is allocated and close when resources are depleted, the admitted workload reaches terminal states, or Z2 explicitly closes allocation.

A cycle must not be defined as a day/week/hour window for internal scheduling.

## Interpretation of clock-normalized RBE units

RBE-OPS v0.1 contains units expressed as rates or durations (`RAT-min per week`, `CI-min per month`, `RUN-day`, `STALE-day`, and other `period:` fields). Under this policy:

1. **Rate normalization is observational.** “Per week/month/session” may describe how a measurement was normalized. It does not create a refill event, work deadline, or priority change when the calendar rolls over.
2. **Capacity is observed or explicitly allocated.** A resource does not automatically become available because a day/week/month boundary passed.
3. **RUN-day is a resource measurement, not a due date.** It may indicate capital depletion; it does not tell an agent that a work item is “late” or authorize urgency by itself.
4. **Calendar-driven assurance decay requires migration.** Any `review_cadence_days`, `measurement_window_days`, `half_life_days`, `STALE-day`, or equivalent control that changes authority, priority, validity, or work state solely because time passed is incompatible with this gate unless separately justified as `TECHNICAL_SAFETY` or `REGULATORY_EXTERNAL`.
5. **PRICE windows are measurement metadata unless explicitly governed otherwise.** A shadow-price estimate may record the observation set/window over which it was measured, but the calendar alone must not autonomously reprioritize work or create a replacement rate.

Because `RESOURCE_UNITS.yaml` is ratified, conflicting v0.1 temporal semantics are not silently rewritten. They must be migrated through an explicit versioned candidate and Z2 ratification.

## Time that remains valid

This policy does not prohibit clocks. The following remain legitimate when correctly classified:

- provenance timestamps;
- telemetry durations;
- statistical/measurement observation windows;
- API/network/process timeouts;
- retry backoff;
- leases and token expiry;
- cache TTL;
- lock reclamation;
- external regulatory/legal/compliance deadlines with validated evidence.

These do not grant ordinary internal work priority merely because time passes.

## Active-control-surface gate

Changed active control surfaces are subject to CI review for unauthorized temporal semantics. Historical/archival material is not retroactively rewritten merely because it contains dates.

Initial active surfaces include:
- `CLAUDE.md`
- `GOVERNANCE.md`
- `CANDIDATE_BLOCK_TEMPLATE.md`
- `PRIORITY_QUEUE.md`
- `ZONE_REGISTRY.md`
- `BOOT_PROCESS_MAP.md`
- `REGISTERED.md`
- `RESOURCE_UNITS.yaml`
- `constants.json`
- `.github/**`
- `schemas/**`
- `src/**`
- `tools/**`
- `ui/**`
- active YAML/JSON work-control artifacts

## Intent-OS

Generic internal `Deadlines` are not a first-class work primitive. The UI/control model must expose `External Constraints` and distinguish regulatory constraints from technical-safety timers and observational timestamps.

## Falsifier

Q-TEMPORAL-DISSOLUTION-01 is incomplete if any active HumanAIOS control surface can make internal work more urgent, expire it, auto-escalate it, reorder it, or replenish its execution capacity solely because elapsed time passed without a valid `REGULATORY_EXTERNAL` exception or an explicitly classified technical-safety requirement.
