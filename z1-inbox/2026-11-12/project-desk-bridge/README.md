# Project Desk evidence / resource bridge (Z1 DRAFT, review only)
Status: DRAFT proposal. authority_effect NONE. Not ratified. Not HUMAN_REVIEW_READY. Nothing here is wired to anything.

## What this is
An offline, read-only candidate for the Gmail -> Project Desk -> INTENT-OS evidence round-trip proof requested in issue 1126 (the Desk-specific test). It contains:
- `engine/intent-bridge.cjs` - deterministic three-way reconciliation of two INTENT-OS workspace exports against a Desk, with explicit human choices, stale-write rejection, history-prefix verification, decision gates, and a review-only round-trip preview. No write-back.
- `engine/evidence-adapter.cjs` - permission-scoped adapter over hand-approved, structured extraction records (never raw mail). Email text is data, never instructions. All proposals are inert (effect NONE, human review required).
- `engine/resource-events.cjs` - hash-chained resource event log over the ratified RESOURCE_UNITS registry snapshot: discovery, acquisition, spending, usage, remaining capacity, yield, waste, benefit as separate events; receipts prove transactions only; no double counting.
- `engine/core.cjs`, `bin/desk-bridge.cjs` (offline CLI), `fixtures/synthetic.cjs` (SYNTHETIC data only), `tests/`, `scripts/` (suite runner, mutation checker), `vendor/resource-units.snapshot.json`.
- `docs/` - sanitized implementation notes, limitation register, audit log (seven fresh-context audits, all REVISE or PASS_FOR_HUMAN_REVIEW recommendations only), and sanitized Test A / reconciliation reports.

## What is NOT here (on purpose)
- The private Project Desk app (`dist/`), its email snapshot, any real export, any Gmail id/address/subject/body, receipt numbers, amounts, or private-run hashes.
- The two private files the code requires: `dist/model.js` (sha256 275b7e05f419fd7cb863a9d195b10194e9f5dcfdb121f7a34912e000050c4da3) and `dist/intent-workspace.js` (sha256 8f84d3edef3c247b02baaabfb60ca4eff48adcb7d8a92ef2ad14341d4738b7ed). Place those exact files at `dist/` next to this README to run the tests:
  `node scripts/run-all.cjs`
  Without them nothing here runs. Without the exact bytes, results are not comparable.

## Honest status
- Seven independent-context audits; the last found no blocker or major and recommended PASS_FOR_HUMAN_REVIEW only if three MINOR items are accepted (see docs/LIMITATION_REGISTER.md). Those audits were Claude contexts started by the author, not independent humans, and never saw the real data.
- Not done: any human-recorded outcome, independent human review, live Gmail beyond one small approved read-only sample, browser UI wiring.
- Boundaries: no INTENT-OS write-back, no Gmail change, no live sync, no deployment, no authority. A human adopts any result by their own act.
