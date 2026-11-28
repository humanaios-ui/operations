# Ruling request Q-BOARD-RULING-20 — board ruling d20

**Z1 Proposer:** Claude (Z1) — transcribing a decision carried inside `Q-INTENTOS-TEST-01` onto the Intent-OS board as its own block
**Date Submitted:** 2026-09-19
**Source:** `z1-inbox/2026-09-16/Q-INTENTOS-TEST-01.md` (the question as Z2 was asked it there) · `ui/intent-os-humanaios-v3_3.html` · `rulings[d20]` · filed under Z2 ruling d18: every board ruling lives in the same queue as every other Z2 decision, one block per decision
**Status:** AWAITING Z2 RATIFICATION
**Gates:** board pipeline step 21

## Question

Test harness — adopt `tools/intent_os_test_harness_v1_0.py` as session-open (§A) step 3, so a session cites the board only on a GREEN run or one whose every red row is named in a candidate — or keep it advisory?

## Context carried on the board

Q-INTENTOS-TEST-01 was ratified (ACCEPT) with this question inside it, but no choice was recorded; the handoff carries d20–d22 as accepted-as-asked and unrecorded. Adoption makes the pathway's surface falsifier bite; advisory keeps §A at its current three lines. The run costs one harness invocation.

## Options

- `adopt as §A step 3`
- `keep advisory`
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
block_hash: 5992e1c5daca2b84deaebf8c64ce0019958ca557a6bfbfbe47c4185df8d53e68
body_hash: 40a0a78c8a60a767671e134f646b497f793df44f16046d698c2d5b9d43ad9b1a

```
RULING d20
  by: Night (tagline)
  project: HumanAIOS
  question: Test harness — adopt `tools/intent_os_test_harness_v1_0.py` as session-open (§A) step 3, so a session cites the board only on a GREEN run or one whose every red row is named in a candidate — or keep it advisory?
  choice: later
  note: Written from the Q-STALE-QUEUE-SORT-01 decision table; the merge of its pull request is the ruling.
  at: 2026-11-28T08:00:00Z
  status: DECIDED
```

## Z2 Review Checklist

- [ ] Test harness as §A step 3 — options: adopt as §A step 3, keep advisory, later
- [ ] The parent block `Q-INTENTOS-TEST-01` keeps its own status; this block records the choice for d20 only

## Falsifier

Event-based, no clock. If board pipeline step 21 — the step whose `blockedOn` names d20 — is marked
verified complete while this block is still `status: OPEN`, the work proceeded without the call it said it
needed: that step drops d20 from its `blockedOn`, and this block is withdrawn rather than carried.
Conversely, if this ruling lands and step 21 still cannot proceed, d20 was not the blocker: a successor
block names the real one, citing this one as provenance. Both are read off the board and the tree, not a
calendar.
