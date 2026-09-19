# Ruling request Q-BOARD-RULING-06 — board ruling d6

**Z1 Proposer:** Claude (Z1) — transcribing an open owner ruling carried on the Intent-OS board since 2026-09-06
**Date Submitted:** 2026-09-14
**Source:** `ui/intent-os-humanaios-v3_3.html` · `rulings[d6]` · filed under Z2 ruling d18 (`z1-inbox/2026-09-14/Z2_RULING_INTENTOS_LAUNCH.md`): every board ruling lives in the same queue as every other Z2 decision
**Status:** AWAITING Z2 RATIFICATION

## Question

First job-posting batch — where does it come from?

## Context carried on the board

the only input that moves the intake count (0 of 40 from that door) · NF token due 09-19 assumes an answer

## Options

- `own postings`
- `partner`
- `scrape`
- `later`

## How this gets ruled

Either path produces the same record:

1. **From the board:** tap the option under Decisions, then **→ PR**. `tools/decision_relay.py` writes the
   choice into the *Ruling* section below on a branch and opens a PR marked PENDING with the block's
   sha256. Tap **→ PR** again and paste the hash back: the relay then signs this file the way
   `.z1-control/ratify.py` does, appends the signature to `z1-inbox/<date>/Z2_RULINGS_<date>.md`, marks
   this candidate `ratified` in `z1-inbox/INDEX.yaml`, and regenerates `Z1_INBOX_INDEX.md`.
2. **By hand:** write the chosen option on the `choice:` line below, then run
   `python3 .z1-control/ratify.py Q-BOARD-RULING-06 --decision ACCEPT --by Night --apply`. The signature covers the
   choice because it is computed over this file's bytes at the moment of decision.

A choice of `later` is a ruling too: it is recorded with a date and the question stays on the board.

## Ruling

choice: scrape
by: Night
at: 2026-09-18T01:21:57Z
status: PENDING
block_hash: e97cdf5bd4f80a5a1e67d2487e38388e26704d13fb45711bddc582026e49b05f
body_hash: e69e5c6a05adc0be48b65ab6f92b8b1314ad2ccd5330c140a3fd20c975d56ca5

```
RULING d6
  by: Night (tagline)
  project: HumanAIOS
  question: First job-posting batch — where does it come from?
  choice: scrape
  note: 
  at: 2026-09-18T01:21:57Z
  status: PENDING
```

## Z2 Review Checklist

- [ ] First job-posting batch — where does it come from? — options: own postings, partner, scrape, later

## Falsifier

If this ruling is still `status: OPEN` on 2026-10-14 (30 days after filing), the question was not one the
work needed answered: the board step that lists it under `blockedOn` drops that blocker and proceeds on
Z1's stated default reading, and this block is withdrawn rather than carried.
