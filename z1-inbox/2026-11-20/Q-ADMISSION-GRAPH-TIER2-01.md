# Q-ADMISSION-GRAPH-TIER2-01 — the registry entry and the ADV run that Tier 2 asks for, for the admission-graph workflow merged in #1291

**Z1 Proposer:** Claude (Z1)
**Date Submitted:** 2026-11-20
**Status:** AWAITING Z2 RATIFICATION
**Filed because:** Night asked Z1 to file the Tier 2 items of [#1291](https://github.com/humanaios-ui/operations/pull/1291) as a new block. That pull request merged on 2026-11-20 (merge commit `2b99a5c5`). It adds `.github/workflows/admission-ruling-graph.yml`, which the molt classifier measures as Tier 2 (path rule `.github/workflows/`; claimed 2, measured 2, MATCH). `MOLT_STATE.md` says Tier 2 "needs registry entry + ADV run before KEEP". The pull request body said both were not done. This block asks Z2 about both. It is a candidate.

This file decides nothing and changes no file other than itself and the index. It writes nothing to `REGISTERED.md` (Z2 sole write) and runs no ADV.

## What Z2 is asked to decide

1. **The registry entry.** Does Z2 want an entry in `REGISTERED.md` for the `admission-ruling-graph` workflow, entered after the merge? Z2 writes it. Z1 offers the facts below, not text to paste as signed. If Z2 does not want one, say so, and the gap is recorded as accepted.
2. **The ADV run.** Does Z2 want an adversarial run against this workflow, and who runs it? Z1's proposed attacks and what is already known are in "The ADV run, what exists". Z1 did not run any ADV.
3. **What #1291 is meanwhile.** `MOLT_STATE.md` says the registry entry and the ADV run come before KEEP, and also says nothing enforces that yet ("measurement precedes enforcement"). Is #1291 left merged while those are open (Z1's lean), or reverted until both exist?

## The registry entry, facts only

- **Workflow:** `.github/workflows/admission-ruling-graph.yml`, merged in #1291 at `2b99a5c5`. Jobs: `check` (pull request, runs the generator's smoke test and unit tests) and `refresh` (push to `main` and manual dispatch; regenerates `ADMISSION_RULING_GRAPH.md`; opens one draft pull request; closes older refresh pull requests as superseded).
- **Authority:** `authority_effect NONE`. Top-level `contents: read`; only `refresh` holds `contents: write` and `pull-requests: write`, and only from `main`. No `actions: write`, no `pull_request_target`, no clock trigger, two standard actions.
- **Ruling it carries out:** direction 2 of `Q-ADMISSION-RULING-GRAPH-01` (`page, both checks, issue, entryways`, merged in #1287, reconciled in #1288).
- **Falsifier it carried:** revert if the first run after merge fails, opens a pull request for its own refresh merge, or opens more than one refresh pull request.
- **Observed on its first real run** (`main` `2b99a5c5`, run `44824286426`): `refresh` succeeded, `check` skipped, one draft pull request opened ([#1299](https://github.com/humanaios-ui/operations/pull/1299)), no second pull request, no loop. The falsifier has not tripped on that run.

## The ADV run, what exists

- **The tool.** `adv_eval_v2.py` defines gates, attacks and a catch rate. Its `_simulate_attack` decides CAUGHT or MISSED from dictionaries passed in (a limit, an expected result, an allowed list). Z1 read that function. It does not run a workflow, a script or a runner, so a run of it would score numbers Z1 supplies, not the workflow's behaviour. Z1 did not read the rest of the file or `attack_config.json`.
- **Proposed attacks** on this workflow, each with the result that would count as the workflow failing. None is run on a real runner yet.

| # | Attack | The workflow fails if |
|---|--------|----------------------|
| A1 | Plant a failure in the generator smoke test, open a pull request | `check` still passes |
| A2 | Dispatch `refresh` by hand from a branch other than `main` | the job runs with the write token |
| A3 | Squash-merge a refresh pull request with the default subject | `refresh` runs again on that merge |
| A4 | Squash-merge a refresh pull request after hand-editing the subject to drop the marker | more than one extra draft pull request results (Z1 expects one; this is the known gap) |
| A5 | Leave a refresh branch with no pull request, then rerun | no pull request is created |
| A6 | Two merges to `main` in quick succession | more than one refresh pull request stays open |
| A7 | Make the ledger branch unreadable | a pull request is opened from a stale or empty page |
| A8 | Put markup or a long line in a merged pull request title that the page prints | the generated page carries it unescaped |

- **Already known, not ADV:** A5, the rerun with a pull request open, and the closing of an older refresh pull request were run locally against a throwaway repository with a stand-in `gh` before the merge, and again for A5 after the review fix. Real GitHub was not used. The marker in the commit subject and pull request title (A3) is pinned by a structural test, not run on a real merge. Closing an older refresh pull request has not run live: only one refresh pull request exists so far.
- **Not known:** A1, A2, A4, A6, A7 and A8 were not run in any form. Z1 did not check whether the page escapes markup in a pull request title (A8).

## Checked on 2026-11-20 (main `2b99a5c5`)

- The workflow is on `main` and ran once there, as above.
- `REGISTERED.md` has no entry that names `admission-ruling-graph` (searched by that name and by the file name). Z1 searched text only.
- The classifier and `MOLT_STATE.md` agree Tier 2 needs a registry entry and an ADV run, and `MOLT_STATE.md` says nothing yet enforces it.
- An open review thread on #1291 (refresh pull requests start no pull-request checks, because the repository token opens them) was left for Night. It is a credential decision and **not** part of this block.
- **Not checked:** the rest of `adv_eval_v2.py`, `attack_config.json`, whether another ADV tool exists, whether a registry entry has a required form, and the active CODEOWNERS for `REGISTERED.md`.

## Cost vector (Z1 estimate, not measured, units not collapsed)

- RAT-min: small for Z2 (a yes or no on each ask, plus writing one entry if wanted).
- Z1-ktok: moderate if Z1 is asked to run A1 to A8 in a throwaway repository; none if Z2 declines the run.
- CI-min: small if a real run needs a test branch; none otherwise.

## Z2 Review Checklist

- [ ] Question 1: write a `REGISTERED.md` entry for the workflow, or accept the gap.
- [ ] Question 2: run an ADV against it, say who runs it, and confirm or edit A1 to A8.
- [ ] Question 3: leave #1291 merged while those are open, or revert.

## Falsifier

Event-based, no clock. This block is wrong, and should be withdrawn in whole or in part, if any of these happens:

- (a) an entry for the workflow is found in `REGISTERED.md`. Probe: `grep -n admission-ruling-graph REGISTERED.md`. Z1 found none today.
- (b) a real run of `refresh` opens more than one open refresh pull request, or opens one for its own merge. Then #1291 failed its own falsifier and the question is a revert, not a registry entry.
- (c) a run of `adv_eval_v2.py` is found to execute the workflow or a script, not score supplied values. Z1 read only its attack simulation.
- (d) the molt classifier stops measuring `.github/workflows/` as Tier 2, so the obligation no longer applies.
