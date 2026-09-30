# Cycle-003 Analyst Contract under DHP

The Cycle-003 experimental freeze remains authoritative. DHP changes transport/state custody only; it does not change the frozen universe, cohorts, ontology, costs, schedules, rubric, H0 window, prediction rules, or omission audit.

## Before analysis
1. Resolve canonical state and require ACCEPTED.
2. Require Cycle-003 H0 validity conditions when canonical is H0.
3. Inspect the **repository DHP queue and receipts** for an unresolved candidate whose predecessor equals canonical.
4. If found: emit `HOLD_PENDING_DOWNSTREAM`; do not recompute.
5. Otherwise execute the frozen analysis state machine.

Gmail drafts are no longer the Analyst backpressure substrate. Gmail is a Courier-only communication capability.

## After analysis
1. Build the complete immutable candidate.
2. Assign semantic checkpoint candidate ID and a unique generation ID.
3. Hash exact bytes.
4. Persist candidate + manifest under the Cycle-003 repository queue.
5. Read the persisted candidate bytes back from the repository.
6. Recompute SHA-256 from read-back bytes and compare with the manifest.
7. Only on exact equality emit a separate `queued-receipt.json`.
8. Stop at `QUEUED`.

The Analyst performs **no Gmail draft creation, SEND, communication read-back, ACCEPT, or canonical advancement**.

A material omission blocks warrant exactly as before. DHP persistence success does not imply prediction validity, allocation warrant, communication success, or acceptance.

## Failure semantics
A write, read-back, or hash mismatch produces `PERSISTENCE_FAILED`; the canonical state is unchanged. A generated-but-unpersisted artifact is NONCANONICAL. Regeneration requires a distinct generation ID and may not inherit unverified hashes.

PAPER ONLY / NO REAL CAPITAL.
