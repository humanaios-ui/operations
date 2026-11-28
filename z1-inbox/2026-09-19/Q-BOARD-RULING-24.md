# Ruling request Q-BOARD-RULING-24 — board ruling d24

**Z1 Proposer:** Claude (Z1) — transcribing a decision carried inside `Q-INTENTOS-REFRESH-01` onto the Intent-OS board as its own block
**Date Submitted:** 2026-09-19
**Source:** `z1-inbox/2026-09-17/Q-INTENTOS-REFRESH-01.md` (the question as Z2 was asked it there) · `ui/intent-os-humanaios-v3_3.html` · `rulings[d24]` · filed under Z2 ruling d18: every board ruling lives in the same queue as every other Z2 decision, one block per decision
**Status:** AWAITING Z2 RATIFICATION
**Gates:** board pipeline step 22

## Question

Board rev — an automated re-seal advances `rev`, so a copy open in a browser is superseded by the new data on its next restore (taps kept). Accept that a job's read may supersede an open copy, or reserve `rev` advances for human re-reads?

## Context carried on the board

If reserved, an open copy keeps showing hashes the tree no longer has until a session re-reads; if accepted, an open copy's narrative can change under a job's hand while its taps are kept. Q-INTENTOS-BUS-01 d30 (mechanical pointer moves) is the sibling question.

## Options

- `a job may advance rev`
- `reserve rev for human re-reads`
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

choice: later
by: Night (by merge; option written by Claude Z1 from Q-STALE-QUEUE-SORT-01)
at: 2026-11-28T08:00:00Z
status: DECIDED
block_hash: 5a38479510d805d4689fa48c7a396bb8b34fecc2f907ef8272fb73afec58cc4e
body_hash: aab74461637b24762319b8337a21f56d132b7bc071fdad43600a208462377034

```
RULING d24
  by: Night (tagline)
  project: HumanAIOS
  question: Board rev — an automated re-seal advances `rev`, so a copy open in a browser is superseded by the new data on its next restore (taps kept). Accept that a job's read may supersede an open copy, or reserve `rev` advances for human re-reads?
  choice: later
  note: Written from the Q-STALE-QUEUE-SORT-01 decision table; the merge of its pull request is the ruling.
  at: 2026-11-28T08:00:00Z
  status: DECIDED
```

## Z2 Review Checklist

- [ ] May a job advance the board's rev? — options: a job may advance rev, reserve rev for human re-reads, later
- [ ] The parent block `Q-INTENTOS-REFRESH-01` keeps its own status; this block records the choice for d24 only

## Falsifier

Event-based, no clock. If board pipeline step 22 — the step whose `blockedOn` names d24 — is marked
verified complete while this block is still `status: OPEN`, the work proceeded without the call it said it
needed: that step drops d24 from its `blockedOn`, and this block is withdrawn rather than carried.
Conversely, if this ruling lands and step 22 still cannot proceed, d24 was not the blocker: a successor
block names the real one, citing this one as provenance. Both are read off the board and the tree, not a
calendar.
