# Ruling request Q-BOARD-RULING-15 — board ruling d15

**Z1 Proposer:** Claude (Z1) — transcribing an open owner ruling carried on the Intent-OS board since 2026-09-08
**Date Submitted:** 2026-09-14
**Source:** `ui/intent-os-humanaios-v3_3.html` · `rulings[d15]` · filed under Z2 ruling d18 (`z1-inbox/2026-09-14/Z2_RULING_INTENTOS_LAUNCH.md`): every board ruling lives in the same queue as every other Z2 decision
**Status:** AWAITING Z2 RATIFICATION

## Question

FALS-43 — batch ruling on the 43 hypotheses without written falsifiers?

## Context carried on the board

premise partly obsolete: the repaired z2 gate now enforces falsifiers on z1-inbox candidate blocks, and ci_gates.py carries an M11 falsifier gate; falsifier_lint.py as a file still does not exist

## Options

- `rule now`
- `later`

## How this gets ruled

Either path produces the same record:

1. **From the board:** tap the option under Decisions, then **→ PR**. `tools/decision_relay.py` writes the
   choice into the *Ruling* section below on a branch and opens a PR marked PENDING with the block's
   sha256. Tap **→ PR** again and paste the hash back: the relay then signs this file the way
   `.z1-control/ratify.py` does, appends the signature to `z1-inbox/<date>/Z2_RULINGS_<date>.md`, marks
   this candidate `ratified` in `z1-inbox/INDEX.yaml`, and regenerates `Z1_INBOX_INDEX.md`.
2. **By hand:** write the chosen option on the `choice:` line below, then run
   `python3 .z1-control/ratify.py Q-BOARD-RULING-15 --decision ACCEPT --by Night --apply`. The signature covers the
   choice because it is computed over this file's bytes at the moment of decision.

A choice of `later` is a ruling too: it is recorded with a date and the question stays on the board.

## Ruling

choice:
by:
at:
status: OPEN

## Z2 Review Checklist

- [ ] FALS-43 — batch ruling on the 43 hypotheses without written falsifiers? — options: rule now, later

## Falsifier

If this ruling is still `status: OPEN` on 2026-10-14 (30 days after filing), the question was not one the
work needed answered: the board step that lists it under `blockedOn` drops that blocker and proceeds on
Z1's stated default reading, and this block is withdrawn rather than carried.
