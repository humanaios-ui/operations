# Cycle-003 Analyst Contract under DHP

The Cycle-003 experimental freeze remains authoritative. DHP changes transport/state custody only; it does not change the frozen universe, cohorts, ontology, costs, schedules, rubric, H0 window, prediction rules, or omission audit.

Before analysis:
1. Resolve canonical state and require ACCEPTED.
2. Require Cycle-003 H0 validity conditions when canonical is H0.
3. Inspect DHP receipts/index for an unresolved candidate whose predecessor equals canonical.
4. If found: emit HOLD_PENDING_DOWNSTREAM; do not recompute.
5. Otherwise execute the frozen analysis state machine.

After analysis:
1. Build the complete immutable candidate.
2. Assign semantic checkpoint candidate ID and a unique generation ID.
3. Hash exact bytes.
4. Persist candidate + manifest.
5. Read back exact bytes and re-hash.
6. Only on equality emit QUEUED.
7. Stop. Analyst performs no SEND, communication read-back, ACCEPT, or canonical advancement.

A material omission blocks warrant exactly as before. DHP persistence success does not imply prediction validity, allocation warrant, communication success, or acceptance.

PAPER ONLY / NO REAL CAPITAL.
