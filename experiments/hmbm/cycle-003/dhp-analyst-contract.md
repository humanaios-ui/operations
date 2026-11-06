# Cycle-003 Analyst Contract under DHP

The Cycle-003 experimental freeze remains authoritative. DHP changes transport/state custody only; it does not change the frozen universe, cohorts, ontology, costs, schedules, rubric, H0 window, prediction rules, or omission audit.

## Before analysis
1. Resolve canonical state and require ACCEPTED.
2. Require Cycle-003 H0 validity conditions when canonical is H0.
3. Inspect the repository DHP queue for an unresolved candidate whose predecessor equals canonical.
4. If found: emit HOLD_PENDING_DOWNSTREAM; do not recompute.
5. Otherwise execute the frozen analysis state machine.

Gmail remains Courier-only.

## After analysis
1. Build the complete immutable candidate and assign candidate/generation IDs.
2. Hash exact bytes and persist candidate + manifest.
3. Read persisted bytes back and verify SHA-256.
4. Obtain the full commit SHA and Git blob SHA for the persisted candidate.
5. Construct DHP-ARTIFACT-REF-1 using repository, full commit SHA, exact path, blob SHA, SHA-256, byte length, media type, and commit-pinned raw URL.
6. Resolve the reference and verify it identifies the same immutable blob.
7. Embed the reference in the QUEUED receipt.
8. Only after all checks pass emit QUEUED and stop.

A missing, mutable, unresolved, or hash-mismatched artifact reference is a persistence failure. It MUST NOT be deferred to Courier.

The Analyst performs no Gmail draft creation, SEND, communication read-back, ACCEPT, or canonical advancement. Material omission still blocks warrant; persistence success does not imply prediction validity, allocation warrant, communication success, or acceptance.

PAPER ONLY / NO REAL CAPITAL.
