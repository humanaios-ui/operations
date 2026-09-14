# Z2 Ruling — 2026-09-14 · Intent-OS board launch (Q-INTENTOS-LAUNCH-01)

**Decision by:** Night (Z2 / Admiral)
**Given:** 2026-09-14, in session `session_01EuQSM7W5YPweVo6f3FThnG`, in response to the four decisions
asked in `z1-inbox/2026-09-14/Q-INTENTOS-LAUNCH-01.md` and the board rulings d17–d19 carried on
`ui/intent-os-humanaios-v3_3.html`.
**Recorded by:** Claude (Z1), as transcription of Z2's decision, in the same form as
`z1-inbox/2026-09-13/Z2_RULING_ZONE2_RATIFY_TOOL.md`. Z1 did not make these calls.
**Content signature:** the ACCEPT on the candidate block is signed by `.z1-control/ratify.py` in
`z1-inbox/2026-09-14/Z2_RULINGS_2026-09-14.md`; that hash pins the candidate's bytes. This file
records the *choices* inside that ACCEPT, which the candidate left open.

## Rulings

| id | question | ruling |
|---|---|---|
| **d17** | Publish surface | **local only** — the board stays a file Z2 opens from the repository. No copy under `site/`, no GitHub Pages deploy. The relay remains the board's only exit. |
| **d18** | Relay landing path | **z1-inbox + INDEX.yaml** — a ruling landed by `tools/decision_relay.py` is written under `z1-inbox/<date>/`, indexed in `z1-inbox/INDEX.yaml`, and ratified through the same signature `.z1-control/ratify.py` produces, so the z2 gate, the validator and the triage job cover it. `z2-rulings/` is retired before it was ever used. |
| **d19** | Board versioning | **freeze path** — `ui/intent-os-humanaios-v3_3.html` is the stable consumer target. A re-read changes the data inside the file, never the filename. |
| **row** | Priority-queue row for the launch | not requested; the candidate's ACCEPT stands as the decision. Z1 adds no row (PRIORITY_QUEUE.md §Ratification Authority). |

## Receipt recorded by Z2

**Temporary GitHub tokens — revoked.** Z2 states that the temporary org-wide token used for the
2026-09-06 push and the pushes after it is no longer listed, closing board step 3's gate ("Z2 states,
in a dated ruling file, that no temporary token is listed"). This is a settings-page fact the tree
cannot verify; the statement is the receipt.

## Effects (Z1 executes)

1. `tools/decision_relay.py` lands rulings per d18 (this PR).
2. Each open board ruling (d2, d3, d5–d16) is filed as its own `z1-inbox/` candidate so the Z2 queue
   is one list (this PR) — the step the candidate block deferred until d18 ruled.
3. The board records d17–d19 as RULED with the hash from `Z2_RULINGS_2026-09-14.md`; step 3 turns
   green on this file; step 19's and step 20's blockers clear.
4. The runbook's §5 (publish) becomes "not until a later ruling reverses d17"; §4 describes the
   inbox landing path.

Still open after this ruling: the fourteen board rulings themselves (now in the queue), the 22
candidates awaiting Z2 before this one, and the falsifier on Q-INTENTOS-LAUNCH-01 (a ruling lands
through the relay by 2026-09-30).
