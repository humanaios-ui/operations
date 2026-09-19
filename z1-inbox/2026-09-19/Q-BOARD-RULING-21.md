# Ruling request Q-BOARD-RULING-21 — board ruling d21

**Z1 Proposer:** Claude (Z1) — transcribing a decision carried inside `Q-INTENTOS-TEST-01` onto the Intent-OS board as its own block
**Date Submitted:** 2026-09-19
**Source:** `z1-inbox/2026-09-16/Q-INTENTOS-TEST-01.md` (the question as Z2 was asked it there) · `ui/intent-os-humanaios-v3_3.html` · `rulings[d21]` · filed under Z2 ruling d18: every board ruling lives in the same queue as every other Z2 decision, one block per decision
**Status:** AWAITING Z2 RATIFICATION
**Gates:** board pipeline step 21

## Question

Test dashboard — commit the rendered dashboard and receipt with each run (the tree carries the last verified state; `git.head` inside the receipt is the SHA it ran on), or keep `main`'s dashboard unrendered and render locally per session?

## Context carried on the board

Committed = anyone opening the file from the repository sees the last run; unrendered = the file on main reads NO RUN until someone runs it, which is honest but empty. Q-INTENTOS-REFRESH-01 assumes the status quo (the dashboard carries the receipt; the refresh PR commits only the board and the dashboard).

## Options

- `commit the rendered dashboard`
- `render locally per session`
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

- [ ] Dashboard: commit the rendered receipt — options: commit the rendered dashboard, render locally per session, later
- [ ] The parent block `Q-INTENTOS-TEST-01` keeps its own status; this block records the choice for d21 only

## Falsifier

Event-based, no clock. If board pipeline step 21 — the step whose `blockedOn` names d21 — is marked
verified complete while this block is still `status: OPEN`, the work proceeded without the call it said it
needed: that step drops d21 from its `blockedOn`, and this block is withdrawn rather than carried.
Conversely, if this ruling lands and step 21 still cannot proceed, d21 was not the blocker: a successor
block names the real one, citing this one as provenance. Both are read off the board and the tree, not a
calendar.
