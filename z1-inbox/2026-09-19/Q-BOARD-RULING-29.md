# Ruling request Q-BOARD-RULING-29 — board ruling d29

**Z1 Proposer:** Claude (Z1) — transcribing a decision carried inside `Q-INTENTOS-BUS-01` onto the Intent-OS board as its own block
**Date Submitted:** 2026-09-19
**Source:** `z1-inbox/2026-09-17/Q-INTENTOS-BUS-01.md` (the question as Z2 was asked it there) · `ui/intent-os-humanaios-v3_3.html` · `rulings[d29]` · filed under Z2 ruling d18: every board ruling lives in the same queue as every other Z2 decision, one block per decision
**Status:** AWAITING Z2 RATIFICATION
**Gates:** board pipeline step 23

## Question

Smoke contract — make `smoke_test: true` in the tool manifest mean carries a flag (`--smoke-test` or `--self-test` exists in the source), not mentions; the scan records `smoke_flag` and 18 no-flag rows drop (141 → 123) while the 17 whose flag fails stay claimed and red in T5 — or keep the text match?

## Context carried on the board

The two IC-candidates step 3 measured (a manifest smoke_test that is a text match; a smoke test with side effects) are filed with the bus block as d29. A flag that fails is a bug to fix, not a claim to drop.

## Options

- `flag means carries`
- `keep the text match`
- `later`

## How this gets ruled

One act, and only one: tap the option under Decisions on the board, then **→ PR**. `tools/decision_relay.py`
writes the choice into the *Ruling* section below on a branch and opens a one-file pull request. **Merging
that pull request is the ratification** (Z2, 2026-09-18): `.github/workflows/intent-os-reconcile.yml` then
signs the merged bytes, records the signature in `z1-inbox/<date>/Z2_RULINGS_<date>.md`, marks this candidate
`ratified` in `z1-inbox/INDEX.yaml` and regenerates `Z1_INBOX_INDEX.md` in a reconcile pull request. Without
the relay, the same one-file pull request can be opened by hand (write the option on the `choice:` line,
`status: DECIDED`) — the merge is still the act. `.z1-control/ratify.py --apply` refuses a block of this shape,
so there is no second, unreviewed path to a signature.

A choice of `later` is a ruling too: it closes this block (its bytes are signed); the question returns only
as a new block citing this one.

## Ruling

choice:
by:
at:
status: OPEN

## Z2 Review Checklist

- [ ] The smoke contract in the manifest — options: flag means carries, keep the text match, later
- [ ] The parent block `Q-INTENTOS-BUS-01` keeps its own status; this block records the choice for d29 only

## Falsifier

Event-based, no clock. If board pipeline step 23 — the step whose `blockedOn` names d29 — is marked
verified complete while this block is still `status: OPEN`, the work proceeded without the call it said it
needed: that step drops d29 from its `blockedOn`, and this block is withdrawn rather than carried.
Conversely, if this ruling lands and step 23 still cannot proceed, d29 was not the blocker: a successor
block names the real one, citing this one as provenance. Both are read off the board and the tree, not a
calendar.
