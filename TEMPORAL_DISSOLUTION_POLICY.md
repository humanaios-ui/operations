# TEMPORAL_DISSOLUTION_POLICY.md

**Policy ID:** Q-TEMPORAL-DISSOLUTION-01  
**Authority:** Z2 / Night  
**Model:** resource/state scheduling  
**Status:** proposed on branch; effective only after merge and required review

## Invariant

HumanAIOS does not schedule internal work by elapsed time.

Work becomes executable when its required authority, dependencies, resources, evidence, and safety predicates are satisfied. Work pauses or yields when those predicates are not satisfied.

```text
READY(work) = AUTHORITY ∧ DEPENDENCIES ∧ RESOURCES ∧ EVIDENCE ∧ SAFETY
```

No agent may create urgency, escalation, expiry, priority, or authority from elapsed time alone.

## Temporal classes

| Class | Permitted | Scheduling authority |
|---|---|---|
| `OBSERVATIONAL` | timestamps, durations, created/completed times | none |
| `TECHNICAL_SAFETY` | request timeout, retry backoff, lease/token expiry, dead-process detection, cache TTL, lock reclamation | protects technical correctness/resources only; cannot reprioritize human work |
| `REGULATORY_EXTERNAL` | evidenced externally imposed regulatory/legal/compliance deadlines | allowed only with complete exception contract + explicit Z2 ratification |
| `HISTORICAL_RECORD` | archival records of dates/deadlines that already occurred | none |
| `INTERNAL_WORK_DEADLINE` | internal due dates, arbitrary windows, AI-created urgency | prohibited |

## Regulatory exception contract

A time-based priority override is invalid unless all fields are present and non-empty:

```yaml
external_constraint:
  type: REGULATORY_DEADLINE
  authority: <issuing authority>
  citation: <statute/regulation/order/mandate>
  due_at: <RFC3339 timestamp>
  evidence_ref: <immutable source/artifact>
  impact_if_missed: <consequence>
  z2_ratified: true
  ratification_ref: <durable decision/hash/comment reference>
```

No regulatory evidence means no deadline semantics.

## Resource-state scheduling

Canonical states:

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
    select the highest-value eligible workload
    reserve required resources
    execute within authority and safety floors
ELSE:
    idle or wait for a state/resource change
```

Agent availability does not itself create work.

## Backpressure

Autonomous producers must not flood a scarce downstream resource.

Examples:
- no Z2 review capacity -> do not create additional Z2-dependent governance work unless it directly reduces an active blocker;
- no independent-review capacity -> builders stop at awaiting-review state;
- exhausted tool/write/token budget -> yield or continue bounded read-only analysis if useful.

## Cycles

A cycle is an accounting/allocation epoch, not a duration.

A cycle may open when capacity is allocated and close when resources are depleted, the admitted workload reaches terminal states, or Z2 explicitly closes allocation.

A cycle must not be defined as a day/week/hour window for internal scheduling.

## Time that remains valid

This policy does not prohibit clocks. The following remain legitimate when correctly classified:

- provenance timestamps;
- telemetry durations;
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
- `PRIORITY_QUEUE.md`
- `ZONE_REGISTRY.md`
- `BOOT_PROCESS_MAP.md`
- `REGISTERED.md`
- `.github/**`
- `schemas/**`
- `src/**`
- `tools/**`
- `ui/**`
- active YAML/JSON work-control artifacts

## Intent-OS

Generic internal `Deadlines` are not a first-class work primitive. The UI/control model should expose `External Constraints` and distinguish regulatory constraints from technical-safety timers and observational timestamps.

## Falsifier

Q-TEMPORAL-DISSOLUTION-01 is incomplete if any active HumanAIOS control surface can make internal work more urgent, expire it, auto-escalate it, or reorder it solely because elapsed time passed without a valid `REGULATORY_EXTERNAL` exception.
