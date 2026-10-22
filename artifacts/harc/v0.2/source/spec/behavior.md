# Behavioral Contract — HARC v0.2

## Objective

Reproduce a minimal evidence-bearing control loop:

Reality / Input → Observation → Evidence Receipt → Interpretation → Warrant → Proposed Action → Zone Classification → Authorized Local Execution or Escalation → Consequence / New Observation.

## Required behavior

1. **Independent reconstruction** — do not optimize for agreement with the capsule author.
2. **Evidence separation** — observations, human assertions, AI analyses, and authority verification remain distinct.
3. **No silent authority expansion** — implementation convenience may not weaken evidence or authorization boundaries.
4. **Preserve disagreement** — conflicting evidence remains visible until resolved by discriminating evidence.
5. **Falsifiability** — each material engineering proposal states what observation would defeat it.
6. **Strict receipt discipline** — replication claims carry exact capsule hash, typed component/test evidence, divergences, and limitations.
7. **Tests pass is not claim proven** — conformance outputs state these separately.
8. **Zone discipline** — Z1 may execute locally; Z2 is propose-only; Z3 is blocked without explicit human execution.
9. **Transport declaration** — an agent declares return capability; possession of an email/tool capability does not imply authority to use it.
10. **Humility receipt** — every trial identifies what was not inspected, assumptions, possible contamination, and what could falsify the result.

## Enforced capsule-local state machines

Replication transitions are validated by `runtime/state_machine.py`:

- `UNTESTED → PARTIAL | FAILED | REPLICATED`
- `PARTIAL → PARTIAL | FAILED | REPLICATED`
- `FAILED → FAILED | PARTIAL | REPLICATED`
- `REPLICATED → REPLICATED`

A later correction to a replicated claim is a new superseding receipt, not an in-place downgrade that erases the prior claim.

Engineering transitions:

- `OBSERVED → PROPOSED`
- `PROPOSED → Z1_EXECUTED | Z2_AWAITING_RATIFICATION | Z3_BLOCKED`

HARC does not ratify or execute the Z2/Z3 terminal state. The surrounding human/governance system does that.

## Runtime boundary

`runtime/authorize_action.py` is a fail-closed API for hosts that choose to route actions through it. It is **not** operating-system, network, credential, or tool-level interposition. A host that bypasses the guard can still create external effects. A trial must not claim standalone capability enforcement unless an external substrate actually binds tool execution to this guard.
