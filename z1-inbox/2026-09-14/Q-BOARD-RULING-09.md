# Ruling request Q-BOARD-RULING-09 — board ruling d9

**Z1 Proposer:** Claude (Z1) — transcribing an open owner ruling carried on the Intent-OS board since 2026-09-08
**Date Submitted:** 2026-09-14
**Source:** `ui/intent-os-humanaios-v3_3.html` · `rulings[d9]` · filed under Z2 ruling d18 (`z1-inbox/2026-09-14/Z2_RULING_INTENTOS_LAUNCH.md`): every board ruling lives in the same queue as every other Z2 decision
**Status:** AWAITING Z2 RATIFICATION

## Question

B1 — is the platform contract id / feedback / task count covered by the contractor agreement?

## Context carried on the board

Z2 reads the contract; nothing about SPC-01 enters the tree until answered · Cycle 1 week is now

## Options

- `not covered`
- `covered`
- `later`

## How this gets ruled

Either path produces the same record:

1. **From the board:** tap the option under Decisions, then **→ PR**. `tools/decision_relay.py` writes the
   choice into the *Ruling* section below on a branch and opens a PR marked PENDING with the block's
   sha256. Tap **→ PR** again and paste the hash back: the relay then signs this file the way
   `.z1-control/ratify.py` does, appends the signature to `z1-inbox/<date>/Z2_RULINGS_<date>.md`, marks
   this candidate `ratified` in `z1-inbox/INDEX.yaml`, and regenerates `Z1_INBOX_INDEX.md`.
2. **By hand:** write the chosen option on the `choice:` line below, then run
   `python3 .z1-control/ratify.py Q-BOARD-RULING-09 --decision ACCEPT --by Night --apply`. The signature covers the
   choice because it is computed over this file's bytes at the moment of decision.

A choice of `later` is a ruling too: it is recorded with a date and the question stays on the board.

## Ruling

choice: later
by: Night
at: 2026-09-18T01:22:05Z
status: PENDING
block_hash: c8bfe310bb19b6d97d10425494709f72d3e6a6f44bf28e6fa093c528a70c36d7
body_hash: 4c94fae3136d01f3fc8a190974b49284e97ee2448244ade4a3cf6a201592b29e

```
RULING d9
  by: Night (tagline)
  project: HumanAIOS
  question: B1 — is the platform contract id / feedback / task count covered by the contractor agreement?
  choice: later
  note: 
  at: 2026-09-18T01:22:05Z
  status: PENDING
```

## Z2 Review Checklist

- [ ] B1 — is the platform contract id / feedback / task count covered by the contractor agreement? — options: not covered, covered, later

## Falsifier

If this ruling is still `status: OPEN` on 2026-10-14 (30 days after filing), the question was not one the
work needed answered: the board step that lists it under `blockedOn` drops that blocker and proceeds on
Z1's stated default reading, and this block is withdrawn rather than carried.
