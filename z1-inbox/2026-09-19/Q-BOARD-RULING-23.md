# Ruling request Q-BOARD-RULING-23 — board ruling d23

**Z1 Proposer:** Claude (Z1) — transcribing a decision carried inside `Q-INTENTOS-REFRESH-01` onto the Intent-OS board as its own block
**Date Submitted:** 2026-09-19
**Source:** `z1-inbox/2026-09-17/Q-INTENTOS-REFRESH-01.md` (the question as Z2 was asked it there) · `ui/intent-os-humanaios-v3_3.html` · `rulings[d23]` · filed under Z2 ruling d18: every board ruling lives in the same queue as every other Z2 decision, one block per decision
**Status:** AWAITING Z2 RATIFICATION
**Gates:** board pipeline step 22

## Question

Refresh job — set the repository variable `INTENT_OS_REFRESH_AUTOPR=true` so the job opens a re-seal PR per mechanical drift and an issue per NEEDS-HUMAN read, or keep it report-only (summary + artifacts, nothing opened)?

## Context carried on the board

Report-only already ends the silence — every merge produces a summary line reading HOLDS / MECHANICAL / NEEDS-HUMAN. Enabling adds one bot PR per drift that a human still merges, and one issue that a human still closes. Nothing is signed either way. The reconcile job (#406) does not depend on this.

## Options

- `enable auto-PR`
- `report-only`
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

- [ ] Refresh job: enable the PR/issue half — options: enable auto-PR, report-only, later
- [ ] The parent block `Q-INTENTOS-REFRESH-01` keeps its own status; this block records the choice for d23 only

## Falsifier

Event-based, no clock. If board pipeline step 22 — the step whose `blockedOn` names d23 — is marked
verified complete while this block is still `status: OPEN`, the work proceeded without the call it said it
needed: that step drops d23 from its `blockedOn`, and this block is withdrawn rather than carried.
Conversely, if this ruling lands and step 22 still cannot proceed, d23 was not the blocker: a successor
block names the real one, citing this one as provenance. Both are read off the board and the tree, not a
calendar.
