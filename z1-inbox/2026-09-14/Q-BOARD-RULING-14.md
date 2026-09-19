# Ruling request Q-BOARD-RULING-14 — board ruling d14

**Z1 Proposer:** Claude (Z1) — transcribing an open owner ruling carried on the Intent-OS board since 2026-09-08
**Date Submitted:** 2026-09-14
**Source:** `ui/intent-os-humanaios-v3_3.html` · `rulings[d14]` · filed under Z2 ruling d18 (`z1-inbox/2026-09-14/Z2_RULING_INTENTOS_LAUNCH.md`): every board ruling lives in the same queue as every other Z2 decision
**Status:** AWAITING Z2 RATIFICATION

## Question

LPCS — independent check (a), convergence specimen (b), destination (c), or none?

## Context carried on the board

three readings carried; Nemeth caveat applies to (a)

## Options

- `(a) check`
- `(b) specimen`
- `(c) destination`
- `none`
- `later`

## How this gets ruled

Either path produces the same record:

1. **From the board:** tap the option under Decisions, then **→ PR**. `tools/decision_relay.py` writes the
   choice into the *Ruling* section below on a branch and opens a PR marked PENDING with the block's
   sha256. Tap **→ PR** again and paste the hash back: the relay then signs this file the way
   `.z1-control/ratify.py` does, appends the signature to `z1-inbox/<date>/Z2_RULINGS_<date>.md`, marks
   this candidate `ratified` in `z1-inbox/INDEX.yaml`, and regenerates `Z1_INBOX_INDEX.md`.
2. **By hand:** write the chosen option on the `choice:` line below, then run
   `python3 .z1-control/ratify.py Q-BOARD-RULING-14 --decision ACCEPT --by Night --apply`. The signature covers the
   choice because it is computed over this file's bytes at the moment of decision.

A choice of `later` is a ruling too: it is recorded with a date and the question stays on the board.

## Ruling

choice: later
by: Night
at: 2026-09-18T01:00:56Z
status: PENDING
block_hash: a04583f5b839958ee1bd970ac216803be9469f7f06b47d8b1f342edf720ada1b
body_hash: 4c7837727a3b199b2c2701388cf22a57cfcea8f936df8f27b7fa8771d01bd61b

```
RULING d14
  by: Night (tagline)
  project: HumanAIOS
  question: LPCS — independent check (a), convergence specimen (b), destination (c), or none?
  choice: later
  note: 
  at: 2026-09-18T01:00:56Z
  status: PENDING
```

## Z2 Review Checklist

- [ ] LPCS — independent check (a), convergence specimen (b), destination (c), or none? — options: (a) check, (b) specimen, (c) destination, none, later

## Falsifier

If this ruling is still `status: OPEN` on 2026-10-14 (30 days after filing), the question was not one the
work needed answered: the board step that lists it under `blockedOn` drops that blocker and proceeds on
Z1's stated default reading, and this block is withdrawn rather than carried.
