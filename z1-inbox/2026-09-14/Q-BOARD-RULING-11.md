# Ruling request Q-BOARD-RULING-11 — board ruling d11

**Z1 Proposer:** Claude (Z1) — transcribing an open owner ruling carried on the Intent-OS board since 2026-09-08
**Date Submitted:** 2026-09-14
**Source:** `ui/intent-os-humanaios-v3_3.html` · `rulings[d11]` · filed under Z2 ruling d18 (`z1-inbox/2026-09-14/Z2_RULING_INTENTOS_LAUNCH.md`): every board ruling lives in the same queue as every other Z2 decision
**Status:** AWAITING Z2 RATIFICATION

## Question

Option A — file the 'orthogonal gap layer' positioning as DRAFT.md until Option B data exists?

## Context carried on the board

H-BM-03 stays PROPOSED until then

## Options

- `file as draft`
- `ratify now`
- `later`

## How this gets ruled

Either path produces the same record:

1. **From the board:** tap the option under Decisions, then **→ PR**. `tools/decision_relay.py` writes the
   choice into the *Ruling* section below on a branch and opens a PR marked PENDING with the block's
   sha256. Tap **→ PR** again and paste the hash back: the relay then signs this file the way
   `.z1-control/ratify.py` does, appends the signature to `z1-inbox/<date>/Z2_RULINGS_<date>.md`, marks
   this candidate `ratified` in `z1-inbox/INDEX.yaml`, and regenerates `Z1_INBOX_INDEX.md`.
2. **By hand:** write the chosen option on the `choice:` line below, then run
   `python3 .z1-control/ratify.py Q-BOARD-RULING-11 --decision ACCEPT --by Night --apply`. The signature covers the
   choice because it is computed over this file's bytes at the moment of decision.

A choice of `later` is a ruling too: it is recorded with a date and the question stays on the board.

## Ruling

choice: file as draft
by: Night
at: 2026-09-18T01:22:15Z
status: PENDING
block_hash: f6e656a5a1f7db7fc2407702d3b91450c7e4570473563bfa29c6541b42ec00d8
body_hash: 9dca83e81cd746e6a8e613178810896edfd49a14f42f1fdfd51cd32c5d95324d

```
RULING d11
  by: Night (tagline)
  project: HumanAIOS
  question: Option A — file the 'orthogonal gap layer' positioning as DRAFT.md until Option B data exists?
  choice: file as draft
  note: 
  at: 2026-09-18T01:22:15Z
  status: PENDING
```

## Z2 Review Checklist

- [ ] Option A — file the 'orthogonal gap layer' positioning as DRAFT.md until Option B data exists? — options: file as draft, ratify now, later

## Falsifier

If this ruling is still `status: OPEN` on 2026-10-14 (30 days after filing), the question was not one the
work needed answered: the board step that lists it under `blockedOn` drops that blocker and proceeds on
Z1's stated default reading, and this block is withdrawn rather than carried.
