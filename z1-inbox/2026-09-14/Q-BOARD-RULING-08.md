# Ruling request Q-BOARD-RULING-08 — board ruling d8

**Z1 Proposer:** Claude (Z1) — transcribing an open owner ruling carried on the Intent-OS board since 2026-09-08
**Date Submitted:** 2026-09-14
**Source:** `ui/intent-os-humanaios-v3_3.html` · `rulings[d8]` · filed under Z2 ruling d18 (`z1-inbox/2026-09-14/Z2_RULING_INTENTOS_LAUNCH.md`): every board ruling lives in the same queue as every other Z2 decision
**Status:** AWAITING Z2 RATIFICATION

## Question

c08f86c history — accept that the PII literals stay in history, or rewrite history?

## Context carried on the board

partly overtaken: the repo history was reset 09-10 and c08f86c is no longer reachable locally; whether the literals survive on the remote's full history is Z2's read

## Options

- `accept`
- `rewrite`
- `later`

## How this gets ruled

Either path produces the same record:

1. **From the board:** tap the option under Decisions, then **→ PR**. `tools/decision_relay.py` writes the
   choice into the *Ruling* section below on a branch and opens a PR marked PENDING with the block's
   sha256. Tap **→ PR** again and paste the hash back: the relay then signs this file the way
   `.z1-control/ratify.py` does, appends the signature to `z1-inbox/<date>/Z2_RULINGS_<date>.md`, marks
   this candidate `ratified` in `z1-inbox/INDEX.yaml`, and regenerates `Z1_INBOX_INDEX.md`.
2. **By hand:** write the chosen option on the `choice:` line below, then run
   `python3 .z1-control/ratify.py Q-BOARD-RULING-08 --decision ACCEPT --by Night --apply`. The signature covers the
   choice because it is computed over this file's bytes at the moment of decision.

A choice of `later` is a ruling too: it is recorded with a date and the question stays on the board.

## Ruling

choice: accept
by: Night
at: 2026-09-18T01:22:08Z
status: PENDING
block_hash: 9a7400146d0e290327c7c58691650cb25723f0f9e54185f5a5f1aa66f0bdcbf6
body_hash: 0250b622e3f39fa942aad27acb80964be031e60d8f2f9281d551c75b06caf6fd

```
RULING d8
  by: Night (tagline)
  project: HumanAIOS
  question: c08f86c history — accept that the PII literals stay in history, or rewrite history?
  choice: accept
  note: 
  at: 2026-09-18T01:22:08Z
  status: PENDING
```

## Z2 Review Checklist

- [ ] c08f86c history — accept that the PII literals stay in history, or rewrite history? — options: accept, rewrite, later

## Falsifier

If this ruling is still `status: OPEN` on 2026-10-14 (30 days after filing), the question was not one the
work needed answered: the board step that lists it under `blockedOn` drops that blocker and proceeds on
Z1's stated default reading, and this block is withdrawn rather than carried.
