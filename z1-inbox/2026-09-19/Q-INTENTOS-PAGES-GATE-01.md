# Candidate block Q-INTENTOS-PAGES-GATE-01 — gates for the board's page set (a Tier 2 proposal)

**Z1 Proposer:** Claude (Z1) — from residual risks 1 and 2 of Z2's red-team review on #410, 2026-09-19
**Date Submitted:** 2026-09-19
**Pinned SHA:** `c203835` (main's HEAD, the squash-merge of #409)
**Status:** AWAITING Z2 RATIFICATION
**Relates to:** `Q-INTENTOS-REFRESH-01` (the refresh job), `Q-BOARD-RULING-33` (the filename hold), `tools/intent_os_pages_v1_0.py` (#410)

## What #410 lands without touching a gate (in force once it merges)

1. `tools/intent_os_pages_v1_0.py --check` is a harness row (`t1-pages-fresh`): a board change without a
   regeneration turns the row RED on the test dashboard and in the refresh job's report after every merge
   that touches a sealed path — detection, not prevention.
2. A served section page fetches the board beside it and compares reads: an older page shows a
   *stale page* banner naming both reads and linking to the board — the operator is told, not misled.
3. `tests/test_board_rename_hold.py` fails whenever `ui/intent-os-board.html` exists while d31
   (`Q-BOARD-PUBLISH-01`) or d33 (`Q-BOARD-RULING-33`) is not `ratified` — run by the harness's
   `t3-pytest-research` row, so by the refresh job after a merge, and by anyone running the harness.

None of those is a pre-merge gate: the pre-merge jobs (`quality-baseline`, `z2_ratification_gate`, …) are
GATE paths under `tools/molting_protocol_diff_v1_0.py`, so changing them is a Tier 2 molt with a registry
entry — this block.

## What Z2 is asked to decide

| id | question | Z1 reading (no preference encoded) |
|---|---|---|
| **G1** | Add `python3 tools/intent_os_pages_v1_0.py --check` as an ERROR step to a pull-request job (the natural home is the refresh workflow's PR-facing half, or `quality-baseline`), so a PR that changes the board without regenerating the pages cannot merge? | Makes the pages a derived file with a gate, like `Z1_INBOX_INDEX.md` under `render.py --check`. Cost: one more step per PR; a contributor regenerates with one command. |
| **G2** | Add `tests/test_board_rename_hold.py` to `quality-baseline`'s pytest list, so the d33 hold refuses a rename PR before it merges rather than reporting it after? | The hold then stops being prose. Once d31 and d33 are both ratified the test passes on the renamed tree and can be retired with the successor block that records the rename. |
| **G3** | Treat the runbook's open-the-board card as a sealed surface (a board seal on `docs/INTENT_OS_BOARD_RUNBOOK.md`, re-sealed by the tool on every edit), or leave it prose? | A seal makes drift visible on the board; the reseal tool marks it MECHANICAL on every runbook edit, so the cost is noise. |
| **G4** | Make decomposition a validator rule: `.z1-control/ratify.py --apply` refuses a candidate whose file carries a `**Decomposed into:**` line while any named child is not `ratified`, and `.z1-control/validate.py` reports a decomposed parent that still carries a `\| **dNN** \|` row as a violation? (From the ChatGPT red-team read of #410: the REFRESH and BUS parents held the same calls as their d23–d30/d32 children.) | Today the parents carry no decision rows and `tests/test_decision_decomposition.py` fails if a row returns — post-merge. G4 makes the refusal pre-signature, in the two gate files. |

## Options

- `adopt G1 + G2 + G4` (G3 as Z2 chooses)
- `adopt G1 + G2` (G3, G4 as Z2 chooses)
- `adopt G1 only`
- `keep detection only` (the harness row, the banner and the post-merge tests stand; no pre-merge gate)
- `later`

## Predictions (pre-registered)

| id | text | p | resolves |
|---|---|---|---|
| C29 | before G1 is adopted, at least one merge to `main` changes the board without regenerating the pages, and `t1-pages-fresh` is the first place it shows | 0.55 | the first such refresh report, or G1's adoption — whichever event comes first |
| C30 | no rename PR opens before d31's ruling merges | 0.85 | d31's reconcile PR merges |

## Falsifier

Event-based, no clock. If, after this block is ratified with G1 adopted, a pull request that changes the
board without regenerating the pages still merges to `main` (the harness row goes RED on the merge and no
gate refused it), the gate as landed does not do what this block claims: it is reverted and the block is
withdrawn rather than carried. If `keep detection only` is chosen and a stale page is later served under
the Worker without the banner (an authenticated GET of a page whose embedded read is older than the board's
and whose body carries no `id="stale"`), the detection layer is falsified the same way.
