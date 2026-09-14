---
id: "IC-CAND-BOARD-STALE-SEALS-S091426"
name: "A governance surface pinned to commits a history reset removed — unnoticed from the 09-10 reset to the 09-14 checker (4 days), on a board last read 09-08 (6 days)"
status: CANDIDATE
class: IC
date_registered: "2026-09-14"
date_origin: "2026-09-10"
session_registered: "S-091426-01"
zone2_ratification: null
tags: ["IC-030-class", "memory-vs-fetch", "intent-os-board", "receipt-gap", "history-reset"]
related: ["IC-030", "IC-031"]
superseded_by: null
source_issue: "humanaios-ui/operations#323"
---

# Candidate Block: Q-IC-BOARD-SEALS-01 — the board's seals outlived the commits they pointed at

**Z1 Proposer:** Claude (AI agent)
**Date Submitted:** 2026-09-14
**Pinned SHA:** `6d3443a` (main after #325; REGISTERED.md sha256 `96507d9f3f9d78e2…`)
**Status:** AWAITING Z2 RATIFICATION

## IC-BOARD-SEALS-01

- **claim:** `ui/intent-os-humanaios-v3_3.html` carried three "verified records" naming commits
  `b8aac1be` (system_graph v0.2 landing), `c08f86c` (research-intake v0.1 direct push) and `5df54b7`
  (H-CAND batch append), plus a `read.against` of `5df54b7` — three unique shas, four references. The
  repository history was reset at `21aec1e` on 2026-09-10 (57 commits total afterwards). From that
  moment none of the three commits was fetchable, yet the board — the Z2 decision surface — kept
  presenting them as verified until 2026-09-14, when `tools/intent_os_board_check_v1_0.py` was written
  and returned STALE on first run. Two reference points for the duration: 4 days from the reset
  (09-10 → 09-14), 6 days from the board's last read (09-08 → 09-14). No RECEIPT-GAP callout *for
  these seals* was raised in the sessions between (09-10, 09-11, 09-12, 09-13 handoffs carry
  RECEIPT-GAPs for other findings, none naming the board or these shas).
- **class:** memory-vs-fetch (IC-030 class): a claim of verification that nothing re-checked after the
  fact. Adjacent to IC-031: the board *read* as a receipt while the receipts were gone.
- **evidence_tier:** VERIFIED-LIVE — `git cat-file -t` on each of the three unique shas fails on main today;
  `git log --reverse | head -1` = `21aec1e 2026-09-10`; the pre-fix board is in #323's diff base.
- **detection:** caught by building the checker, not by any existing gate. Nothing in CI reads the
  board; no session ritual re-hashes a seal; the RECEIPT-GAP trigger in CLAUDE.md fires on a claim
  *in a transcript*, not on a claim already sitting in a file.
- **correction (landed, #323 / #325):** every seal with a `path:` is re-hashed against the tree; commit
  seals require reachability from HEAD (`git merge-base --is-ancestor`), not mere existence; the three
  lost commits are carried as RECEIPT-GAP rows and never counted; a board with no checkable seal is
  STALE, not HOLDS. Runbook §3/§6: run the checker before citing the board and after any merge that
  touches a sealed file.
- **prevention (proposed, Z2 to accept or edit):** (1) a `board-check` job in CI that runs the checker
  on every push to `main` touching `ui/intent-os-humanaios-v3_3.html` or any sealed path, advisory
  first (STALE is expected after a sealed-file merge; the job's value is that the drift is *seen*), and
  (2) the §A session-open ritual gains one line: "run `tools/intent_os_board_check_v1_0.py`; a STALE
  board is a RECEIPT-GAP callout." Neither is built here — both change a gate or a ritual, which are Z2's.
- **falsifier:** if any of the three unique shas is reachable from `main` today (`git merge-base
  --is-ancestor <sha> origin/main` exits 0), the commits were not lost and this IC collapses to "the
  board named the wrong shas" — a lesser finding with the same mitigation. Row-level: if a RECEIPT-GAP
  naming these seals or shas exists in any handoff dated 2026-09-10 → 2026-09-13, the "unnoticed"
  claim is false and the block is withdrawn.
- **status:** OPEN.

## Z2 Review Checklist

- [ ] Register IC-BOARD-SEALS-01 in REGISTERED.md as an IC (class memory-vs-fetch), or fold it into IC-030 as a recurrence
- [ ] Accept, edit or reject prevention (1): an advisory `board-check` CI job on pushes to main touching sealed paths
- [ ] Accept, edit or reject prevention (2): the checker as a §A session-open line in CLAUDE.md

## Falsifier

Stated above per claim: any of the three unique shas (four references) reachable from `main`, or a prior
RECEIPT-GAP naming these seals in a 2026-09-10 → 09-13 handoff, falsifies the block as written.
