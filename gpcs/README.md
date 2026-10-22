# GPCS-001 — governed persistent coordination substrate (experimental)
Tracking: #775. Advisory implementation, not canonical ratification.

This translator bridges a source observation into four **non-authoritative** projections:
observation ledger entry, Session Graph link, Evidence Graph delta, and Repository
Coordinator candidate. The Session Graph is currently an **issue convention**;
these projections do not create a canonical graph store or modify coordinator policy.

## Trust boundary
- Source hashes establish integrity of named source bytes only, **not truth**.
- No memory record may authorize, execute, merge, ratify or self-admit.
- All outputs are advisory; coordinator candidate starts `NOT_REQUESTED`.
- Corrections/contradictions append records that link to prior observations.
- Reject unknown input fields and require fixed UTC-offset timestamps.
- Only trusted local code should process projections. Never execute source text.
- The prototype does **not** inspect statements for hidden instructions or secrets:
  external ingestion needs separate secret scanning, source permissions and isolation.
- Replay is deterministic given an ordered input; signatures, storage ACLs, durable
  append-only custody, CI attestation and full cycle detection are not implemented.

## Quick test
`python3 -m unittest discover -s tests -p 'test_gpcs_translation.py'`

## Promotion gate
Reconcile against actual observation/evidence/coordinator registries, integrate CI,
review synthetic adversarial fixtures, then obtain ordinary Z2 admission and
head-pinned passing checks. Do not equate this candidate with admission evidence.
