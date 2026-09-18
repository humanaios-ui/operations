# Z2 Ruling — 2026-09-18 · The merge is the ratification

**Decision by:** Night (Z2 / Admiral)
**Given:** 2026-09-18, in session `session_01CePrSjPSB8Epbpq3Lj8oKj`, after two hash echoes on d14 were refused
(a partial hash typed from a browser prompt whose text cannot be copied) and two PENDING pull requests (#391 d14,
#393 d2) were merged before their echo.
**Recorded by:** Claude (Z1), as transcription of Z2's decision, in the same form as
`z1-inbox/2026-09-14/Z2_RULING_INTENTOS_LAUNCH.md`. Z1 did not make this call.
**Content signature:** none is possible on this file by its own rule — it is the rule. It is indexed as a record
(no decision asked). The candidates it governs are signed under it by `tools/intent_os_reconcile_v1_0.py`.

## Z2's statement (verbatim)

> Here is what I am finding. The echo hash function on the board puts too much friction. The PR itself acts
> as a governing function. What should be happening is that our PRs act as the final approval and the hash
> is submitted there on the merge. And all PRs must be reviewed and approved. Since I am merging my own PRs,
> I can review them approve them as an override due to having only one member of the team. Once there are
> more than one members, all board ratifications must be approved on the PR side by another member — humans
> cannot ratify on board and merge reviewed PRs.

And, on the mechanism Z1 proposed: "I approve, fold #406 into it. Each PR touches only its candidate file,
and a job on main regenerates the other three after every merge, the same way the refresh workflow already
regenerates derived files."

## Rulings

| id | question | ruling |
|---|---|---|
| **echo** | Is the hash echo the act of ratification? | **No — retired.** A tap lands the choice; the relay signs nothing; `/ratify` answers 404. |
| **merge** | What is the act of ratification? | **The merge of the ruling's pull request.** Whoever merges, and the day they merge, are the signature's `by` and `at`. |
| **one file** | What does a ruling's pull request change? | **Its candidate file only** (the Ruling section). The ruling file, the index entry and the rendered index are written on `main` afterwards by `.github/workflows/intent-os-reconcile.yml`, in one reconcile pull request. |
| **review** | Who may merge? | **Every ruling PR is reviewed and approved.** With one member, the author reviews and merges their own — an override recorded as such in the ruling section (d7's bypass). With more than one member, a board ratification is approved on the pull request by another member; a person does not both rule on the board and merge their own ruling. |
| **signature** | What is signed? | `sha256(candidate | by=<ratifier> | at=<merge date> | decision=ACCEPT)` over the candidate's bytes **as merged** — the construction `.z1-control/ratify.py --verify` recomputes. The candidate file is not touched after the merge. |
| **#391 · #393** | The two PENDING PRs merged before their echo | **Those merges are the ratifications of d14 and d2.** The reconcile job records them on its first run; a 0.4.x `PENDING` block is accepted like a `DECIDED` one. |

## Effects (Z1 executes — #406)

1. `tools/decision_relay.py` 0.5.0: `/decide` writes `status: DECIDED`, refreshes a reused branch from main, opens a
   one-file PR whose body says the merge is the ratification; `/ratify` removed with its tests.
2. `tools/intent_os_reconcile_v1_0.py` (new) and `.github/workflows/intent-os-reconcile.yml` (new): the job on `main`.
   The merger's GitHub login maps to a declared ratifier through `RECONCILE_RATIFIERS` (`humanaios-ui=Night`); any
   other merger is refused as NOT-RATIFIER and nothing is written for that candidate.
3. The board drops the echo: one button, `→ PR`; the status line ends `merge the PR to ratify`; a re-send asks first.
4. `docs/INTENT_OS_BOARD_RUNBOOK.md` §4 and §4c describe tap → review → merge → reconcile PR; the single-member
   override and the two-member rule are written there.
5. The falsifier on `Q-INTENTOS-LAUNCH-01` (b) — a ruling landed *and ratified* through the relay — closes when the
   first reconcile PR (d14, d2) merges.

Still open after this ruling: the twelve decided PRs (#394–#405) await Z2's review and merge; d23 (the refresh job's
auto-PR gate) is a separate question and this job does not depend on it.
