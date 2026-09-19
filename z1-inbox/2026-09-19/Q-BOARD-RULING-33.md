# Ruling request Q-BOARD-RULING-33 — board ruling d33 (successor to d19)

**Z1 Proposer:** Claude (Z1) — transcribing Z2's direction of 2026-09-19 on the board's filename
**Date Submitted:** 2026-09-19
**Source:** Z2 in session (2026-09-19): *"I want a clean file name (intent-os-board.html), the path is a successor block to d19 in one move: rename, update every reference above it, add a one-line redirect in the Worker from the old path so bookmarks and the local-copy instruction keep working, and re-seal. I'd hold it until after d31 rules."* · `ui/intent-os-humanaios-v3_3.html` · `rulings[d33]`
**Status:** AWAITING Z2 RATIFICATION
**Succeeds:** d19 (`z1-inbox/2026-09-14/Z2_RULING_INTENTOS_LAUNCH.md`, *freeze path* — signed `9a2a469be2cbbe1d…`). d19 is not edited: a signed ruling is closed; this block is the successor that asks the next question, citing d19 as provenance.
**Gates:** board pipeline step 19 (this board); sequenced after d31
**Held:** Z2 asked that the move land only after d31 rules. This block is filed now so the question is on the board with every other open decision; the executing pull request is opened only after d31's ruling PR has merged, whatever order the taps come in.

## Question

Board filename — rename `ui/intent-os-humanaios-v3_3.html` to `ui/intent-os-board.html` as the stable consumer target (a successor to d19's freeze, which pinned the versioned name), with a redirect from the old path so bookmarks and the local-copy instruction keep working?

## Context carried on the board

d19 (2026-09-14) froze the path so that each read changes the data inside the file, not the filename; the
frozen name happens to carry a version suffix (`v3_3`). A clean name keeps d19's rule — one stable path,
reads change the data — and drops the suffix. The one move, when this rules `rename`:

1. `git mv ui/intent-os-humanaios-v3_3.html ui/intent-os-board.html`.
2. Every reference above it updated in the same commit: the board's own header comment and `BOARD_FILE`
   constant, `PAGES` strip and the nav's hrefs (inline in the board and the dashboard); the four generated
   pages' canonical link (via `tools/intent_os_pages_v1_0.py`'s `BOARD`); `tools/intent_os_board_check_v1_0.py`
   and `tools/intent_os_board_reseal_v1_0.py` (the board path they read); `tools/intent_os_test_harness_v1_0.py`
   (the board rows it checks); `board/worker.mjs` (`BOARD`, `SERVED`); `docs/INTENT_OS_BOARD_RUNBOOK.md`
   (the card, §3, §5, §6); `docs/ACAT_BENCHMARK_MAP_20260908.md` (`consumer:` points at the board);
   `docs/INTENT_OS_TEST_PATHWAY.md`, `docs/INTENT_OS_GENERAL_USER_SPEC.md`, `REPOSITORY_STRUCTURE.md`; the
   09-17 handoff; the candidates that name the path (`Q-INTENTOS-*`, `Q-BOARD-PUBLISH-01`) are records of
   what was true when they were written and are not rewritten — the 09-14 board-ruling blocks in particular
   must not change while their decided PRs are open.
3. A one-line redirect in the Worker: a request for the old path answers `301` to the new one (after the
   login check, like every other answer), so a bookmark keeps working; a test pins it.
4. The runbook's local-copy instruction names the new file and says the old name redirects on the Worker
   and is simply the old download locally — replace it once.
5. Re-seal: `tools/intent_os_board_reseal_v1_0.py --apply`, the pages regenerated, the checker HOLDS, and
   the `KEY` under which the browser saves taps is kept as it is, so saved state survives the rename.

## Options

- `rename to intent-os-board.html`
- `keep the frozen path`
- `later`

## How this gets ruled

One act, and only one: tap the option under Decisions on the board, then **→ PR**. `tools/decision_relay.py`
writes the choice into the *Ruling* section below on a branch and opens a one-file pull request. **Merging
that pull request is the ratification** (Z2, 2026-09-18): `.github/workflows/intent-os-reconcile.yml` then
signs the merged bytes, records the signature in `z1-inbox/<date>/Z2_RULINGS_<date>.md`, marks this candidate
`ratified` in `z1-inbox/INDEX.yaml` and regenerates `Z1_INBOX_INDEX.md` in a reconcile pull request. Without
the relay, the same one-file pull request can be opened by hand (write the option on the `choice:` line,
`status: DECIDED`) — the merge is still the act. `.z1-control/ratify.py --apply` refuses a block of this shape,
so there is no second, unreviewed path to a signature.

A choice of `later` is a ruling too: it closes this block (its bytes are signed); the question returns only
as a new block citing this one. `keep the frozen path` leaves d19 in force unchanged.

## Ruling

choice:
by:
at:
status: OPEN

## Z2 Review Checklist

- [ ] Board filename — rename to `intent-os-board.html` with a redirect from the old path, keep the frozen path, or later
- [ ] The move is one commit: rename, every reference, the Worker redirect, the runbook, the re-seal — nothing lands piecemeal
- [ ] Sequenced after d31: the executing PR opens only after d31's ruling PR has merged

## Falsifier

Event-based, no clock. (a) If `ui/intent-os-board.html` appears on `main` while this block is still
`status: OPEN`, the rename bypassed the ruling: it is reverted and this block is withdrawn rather than carried.
(b) If this block is ruled `rename` and, after the executing PR merges, either the old path answers anything
but a redirect to the new one on the Worker, or the board checker reads STALE on the new file, or
`tools/intent_os_pages_v1_0.py --check` reports a stale page, the move was not one move: the executing PR is
reverted as a whole and a successor block names what was missed. (c) If the executing PR opens before d31's
ruling PR has merged, the hold was not honoured: it is closed without merging and re-opened after d31. All
three are read off the tree and the Worker, not a calendar.
