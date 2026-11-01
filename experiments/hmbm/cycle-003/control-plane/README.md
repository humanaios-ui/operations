# HMBM-CYCLE-003 Control-Plane Observation

This directory records append-only observations while DHP custody blocks new Analyst production.

## Rule

If an unresolved successor exists for the current accepted canonical predecessor, Analyst state is `HOLD_PENDING_DOWNSTREAM`.

Observation is allowed. State-producing analysis is not.

## Instrumented fields

Each observation records:

- canonical accepted state;
- unresolved candidate/generation/state;
- Gmail staging/communication/disposition evidence;
- PR/queue receipt state;
- frozen schedule epochs due at observation cutoff;
- epochs already materialized in the unresolved candidate;
- blocked due epochs and corresponding would-be record count;
- custody assertions (no recompute, no GEN+1, no Analyst send, no Witness action, no canonical advance).

Blocked epochs are **not** generated retroactively during the hold. They are measured as governance/backpressure debt only. If custody later resolves, the Analyst may reassess recoverability under the original no-hindsight rule.

## Interpretation

This instrumentation distinguishes:

`COMPUTATION_DEBT` from `CUSTODY_BACKPRESSURE_DEBT`.

For Cycle-003 while GEN-003 remains unresolved, the backlog is classified as `CUSTODY_BACKPRESSURE_DEBT`.

PAPER ONLY / NO REAL CAPITAL.
