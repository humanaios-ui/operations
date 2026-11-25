# Z2 Ruling — 2026-11-25 · The merge ratifies every candidate, not only board rulings

**Decision by:** Night (Z2 / Admiral)
**Given:** 2026-11-25, in session, after PR #1317 (candidate `Q-DIGEST-COORD-LAYER-01`) was merged by Z2 and the index still read `awaiting_z2`.
**Recorded by:** Claude (Z1), as transcription of Z2's decision, in the same form as `z1-inbox/2026-09-18/Z2_RULING_MERGE_IS_RATIFICATION.md`. Z1 did not make this call.
**Content signature:** none on this file by its own rule; it is the rule. Indexed as a record (no decision asked).

## Z2's statement (verbatim)

> Merging ALWAYS has supposed to be ratification.

> I requested the rule change. I do not always have access to run python code. And the whole point of the merge is to ratify. I swear I even ratified a decision to make that change. I want it changed now

## What was already on record

The 2026-09-18 ruling made the merge the act of ratification, but its mechanism (`tools/intent_os_reconcile_v1_0.py` 1.0.0, run by `.github/workflows/intent-os-reconcile.yml`) signs only candidates whose file carries a board relay block (`status: DECIDED`). A Z1 candidate filed by its own pull request carries none, so its merge was recorded nowhere and it stayed `awaiting_z2` until someone ran `.z1-control/ratify.py` by hand.

## Ruling

| id | question | ruling |
|---|---|---|
| **scope** | Which merges ratify? | The merge of any pull request that carries an `awaiting_z2` candidate, not only board rulings. |
| **who** | Whose merge counts? | A login mapped to a declared ratifier (`RECONCILE_RATIFIERS`, today `humanaios-ui=Night`). A bot, CI or agent login does not count and is refused as NOT-RATIFIER, so NO SELF-GRANT still holds against agents. |
| **from** | From when? | Candidates submitted on or after 2026-11-25 whose pull request merged on or after 2026-11-25. Older candidates stay as they are; widening to them is a separate Z2 call. |
| **record** | Who writes the signature? | The existing reconcile job on `main`, unchanged in shape: ruling file, index entry, rendered index, in one reconcile pull request. The candidate file is never touched. |
| **#1317** | The merge that raised this | Ratified by its merge at 2026-11-25T22:54:25Z; the job records it on its first run after this change merges. |

## Effects (Z1 executes)

1. `tools/intent_os_reconcile_v1_0.py` 1.1.0: the merge path above, with self-tests for a signed merge, a pre-date merge, a pre-date filing and a bot merger.
2. Tool manifests bumped to 1.1.0.
