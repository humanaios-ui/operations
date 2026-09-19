# Ruling request Q-BOARD-RULING-07 — board ruling d7

**Z1 Proposer:** Claude (Z1) — transcribing an open owner ruling carried on the Intent-OS board since 2026-09-08
**Date Submitted:** 2026-09-14
**Source:** `ui/intent-os-humanaios-v3_3.html` · `rulings[d7]` · filed under Z2 ruling d18 (`z1-inbox/2026-09-14/Z2_RULING_INTENTOS_LAUNCH.md`): every board ruling lives in the same queue as every other Z2 decision
**Status:** AWAITING Z2 RATIFICATION

## Question

Branch protection — turn off admin bypass on main, or keep it and register every bypass as an IC event?

## Context carried on the board

(a) matches the graph ('code, not memory'); (b) is honest about the current state · open since 09-08

## Options

- `no bypass`
- `bypass + IC`
- `later`

## How this gets ruled

Either path produces the same record:

1. **From the board:** tap the option under Decisions, then **→ PR**. `tools/decision_relay.py` writes the
   choice into the *Ruling* section below on a branch and opens a PR marked PENDING with the block's
   sha256. Tap **→ PR** again and paste the hash back: the relay then signs this file the way
   `.z1-control/ratify.py` does, appends the signature to `z1-inbox/<date>/Z2_RULINGS_<date>.md`, marks
   this candidate `ratified` in `z1-inbox/INDEX.yaml`, and regenerates `Z1_INBOX_INDEX.md`.
2. **By hand:** write the chosen option on the `choice:` line below, then run
   `python3 .z1-control/ratify.py Q-BOARD-RULING-07 --decision ACCEPT --by Night --apply`. The signature covers the
   choice because it is computed over this file's bytes at the moment of decision.

A choice of `later` is a ruling too: it is recorded with a date and the question stays on the board.

## Ruling

choice: bypass + IC
by: Night
at: 2026-09-18T01:22:01Z
status: PENDING
block_hash: ffc9e4dd430f525415d42e258fce48d049cf312d37ff820c0738f5be174d8c32
body_hash: 5d11fae0def95f0c80a2e97a591058efe99760bc9f5a592c033f85759ae7b90b

```
RULING d7
  by: Night (tagline)
  project: HumanAIOS
  question: Branch protection — turn off admin bypass on main, or keep it and register every bypass as an IC event?
  choice: bypass + IC
  note: 
  at: 2026-09-18T01:22:01Z
  status: PENDING
```

## Z2 Review Checklist

- [ ] Branch protection — turn off admin bypass on main, or keep it and register every bypass as an IC event? — options: no bypass, bypass + IC, later

## Falsifier

If this ruling is still `status: OPEN` on 2026-10-14 (30 days after filing), the question was not one the
work needed answered: the board step that lists it under `blockedOn` drops that blocker and proceeds on
Z1's stated default reading, and this block is withdrawn rather than carried.
