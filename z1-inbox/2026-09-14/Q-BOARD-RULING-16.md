# Ruling request Q-BOARD-RULING-16 — board ruling d16

**Z1 Proposer:** Claude (Z1) — transcribing an open owner ruling carried on the Intent-OS board since 2026-09-08
**Date Submitted:** 2026-09-14
**Source:** `ui/intent-os-humanaios-v3_3.html` · `rulings[d16]` · filed under Z2 ruling d18 (`z1-inbox/2026-09-14/Z2_RULING_INTENTOS_LAUNCH.md`): every board ruling lives in the same queue as every other Z2 decision
**Status:** AWAITING Z2 RATIFICATION

## Question

docs/ triage — rule by hash over DOC_TRIAGE_2026-09-08.md: archive the 53 as listed, edit the list, or hold?

## Context carried on the board

nothing is deleted either way; archive keeps sha + ruling hash · candidate Q-DOC-LIFECYCLE-01 awaiting_z2 since 09-08

## Options

- `archive as listed`
- `edit list`
- `later`

## How this gets ruled

Either path produces the same record:

1. **From the board:** tap the option under Decisions, then **→ PR**. `tools/decision_relay.py` writes the
   choice into the *Ruling* section below on a branch and opens a PR marked PENDING with the block's
   sha256. Tap **→ PR** again and paste the hash back: the relay then signs this file the way
   `.z1-control/ratify.py` does, appends the signature to `z1-inbox/<date>/Z2_RULINGS_<date>.md`, marks
   this candidate `ratified` in `z1-inbox/INDEX.yaml`, and regenerates `Z1_INBOX_INDEX.md`.
2. **By hand:** write the chosen option on the `choice:` line below, then run
   `python3 .z1-control/ratify.py Q-BOARD-RULING-16 --decision ACCEPT --by Night --apply`. The signature covers the
   choice because it is computed over this file's bytes at the moment of decision.

A choice of `later` is a ruling too: it is recorded with a date and the question stays on the board.

## Ruling

choice: archive as listed
by: Night
at: 2026-09-18T01:22:26Z
status: PENDING
block_hash: 57d71bbc33301bc4478d61ab5eec681bcc3c7fddc995f99e8cc21091c88e70f1
body_hash: e0264493ee42b69a66f9b67f2ef3e7c568e0fff6d9cf6f2ee2be23b7157df9ab

```
RULING d16
  by: Night (tagline)
  project: HumanAIOS
  question: docs/ triage — rule by hash over DOC_TRIAGE_2026-09-08.md: archive the 53 as listed, edit the list, or hold?
  choice: archive as listed
  note: 
  at: 2026-09-18T01:22:26Z
  status: PENDING
```

## Z2 Review Checklist

- [ ] docs/ triage — rule by hash over DOC_TRIAGE_2026-09-08.md: archive the 53 as listed, edit the list, or hold? — options: archive as listed, edit list, later

## Falsifier

If this ruling is still `status: OPEN` on 2026-10-14 (30 days after filing), the question was not one the
work needed answered: the board step that lists it under `blockedOn` drops that blocker and proceeds on
Z1's stated default reading, and this block is withdrawn rather than carried.
