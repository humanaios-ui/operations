# Queue sweep and pin spec — 2026-10-15

**Status:** Z1 proposal, unsigned. No Z2 date, no hash. Nothing here admits, merges, labels, or comments on any PR.
**Parent:** Q-MULTI-AGENT-QUEUE-PLAN-01 (merged in PR #836, main `ab8ef07a`). Opening move of P0 (sweep and pin).
**Machine-readable pins:** `z1-inbox/2026-10-15/queue_pins_2026-10-15.json` (56 rows, one per open PR).

## 1. Scope

- **56 open PRs** at the sweep (`list_pull_requests`, open). The 53 in the earlier brief were a snapshot from 2026-10-14. Since then 844–858 were added, mostly `ci-predict-consolidate/*` bot PRs.
- **Lane source per PR** is recorded in each pin row (`lane_source`). Three sources, in order of strength:
  1. The coordinator index comment (comment `6181721518` on #841, main `3bf3b21`, head `65f1c0f2`). This covers 41 PRs.
  2. A decision receipt read on or after 2026-10-15 (#841, #843, #852, #854, #836 merged).
  3. Inferred or default. Used for 12 PRs (see §4).
- Merged PRs are excluded (#836).

## 2. Lane → prior

`p_pass` is the probability that the admission gate check (`Repository admission/backpressure gate`) concludes **success** on the PR's head at window close. It is a prediction about the gate, not about merge.

| Lane (technical guidance) | n | p_pass | Basis |
|:--|--:|--:|:--|
| ACTIVE | 1 (#812) | 0.85 | Explicitly admitted, within capacity. Prior is high but not 1: the gate also re-runs on each head. |
| CONTROL_PLANE | 1 (#606) | 0.30 | Coordinator-policy change, needs ordinary review. `dirty` at index time. |
| MAINTENANCE | 8 | 0.50 | Routed by cohort. #740's PASS decision was followed by HTTP 403 on the receipt step (run 38058777239), so a PASS decision does not guarantee a success conclusion. |
| ADVANCE (in ADMISSION_REVIEW) | 4 (#770, #771, #838, #841) | 0.40 | Index says "explicit admission evidence found". Passing still needs a Z2 ADMIT. |
| REBASE_RETEST, CLOSE_PRESERVE | 11 (9 + 2) | 0.05 | Mergeability guidance, not a gate input: the gate checks admission standing, scope drift, duplicate implementations and capacity, not mergeability. The low prior comes from these PRs' admission state (no ADMIT record, and in several cases a closed or superseded lineage), not from `dirty` or `behind`. |
| REEXAMINE, COMPARE_CONSOLIDATE, ADMISSION_REVIEW (other, incl. #843) | 19 (14 + 4 + 1) | 0.10 | No admission record; gate FAILs until ADMIT. |
| UNREAD | 12 | 0.10 | Default, pending a receipt read. |

Row count: 1 + 1 + 8 + 4 + 11 + 19 + 12 = 56. Predicted mean across the 56 rows: **0.19**. Expected number of PASS conclusions at window close: **10.4**. The realised count is the scoreable quantity, once the window is dated.

## 3. Window, resolver, and what counts as a result

- **Window:** 2026-10-22 (proposed; Z2 dates it). Each pin is one check-run conclusion, resolved on the **closing head** (the last head before window close), the same rule used in the resolver below.
- **Resolver:** tree read. The check-run conclusion and head SHA are the source, not a comment. A PR that moved heads during the window is resolved on its **last head before close**, and the head change is recorded.
- **Admissions during the window are not fixed.** If Z2 dispatches ADMIT, the prediction stands as written. This makes the pin measure the system's behaviour, including the admission step.
- **Lineage:** these pins are gate-calibration data only. They do not measure lineage-correlated error. The §4b joint-miss statistic and falsifier F6 need confirmed findings on the same heads, from per-finding review records, and this spec does not supply them. Grouping gate outcomes by GNER or ci-predict family is descriptive only.

## 4. Unread and inferred rows

- **UNREAD (12):** #844–#851 and #855–#858 are `ci-predict-consolidate` bot PRs. Their coordinator receipts were not read. Their lane is assumed to be ADMISSION_REVIEW. Reading them costs one `issue_read` each, and the comment payloads are large. The pins can be corrected in a later revision without touching the rest.
- **Inferred (1):** #853 is a dependabot PR in the same family as #852 and #854 (both MAINTENANCE). Its lane is inferred.
- **Head-dependent (1):** #843 was PASS/WORKBENCH on draft head `d8b6ccf` and FAIL/ADMISSION_REVIEW on head `bef8fe1` (`ready`). The pin uses the later state.

## 5. Findings from the sweep (not filed as IC; for Z2 view)

1. **The ci-predict consolidate PRs stack.** At least 12 are open at once, each titled "consolidate resolved CI predictions" and each on a new timestamped branch. Their own CodeRabbit review on #858 flags that the ledger can score predictions without evidence they were made before the CI outcome was known. This is the same ordering question the NF ledger's `issued` field exists for. Proposed: one consolidate PR at a time, and a pin-before-outcome check in the consolidator. Not filed here.
2. **Gate PASS/receipt split is still live.** #740 shows the 403 receipt defect (PASS decision, failed job). Maintenance-cohort p is set at 0.50 for this reason.
3. **Index count mismatch.** The index comment reports `ACTIVE 2`, but its active table lists three rows (#606, #812, #836). This sweep treats #606 as CONTROL_PLANE and #836 as merged. The mismatch is recorded, not resolved.
4. **Test-file path claims.** #822 cites `tests/test_intent_os_bridge.py` and #802 cites `docs/PROJECT_SPEC.md`, both absent from main and from the PR's changed files. The index already flags these. Not re-checked here.
5. **`nf_ledger_v0_1.py` does not fit this pin shape.** `build` expects `practices[].tokens[]` with a `date_source` and per-practice P2 pins. A gate-conclusion prediction per PR has no deliverable date and no practice. So this spec **does not build an NF ledger**. The pins live in the JSON file above, and they can move into the NF ledger only after a schema decision (a gate-pin token type). Logged as a tool gap for P0.

## 6. Not done, on purpose

- No ADMIT dispatch, label, comment, close, merge, or push to any other PR branch.
- No edit to `z1-inbox/INDEX.yaml` or `Z1_INBOX_INDEX.md`. PR #831 touches both, and whichever lands second re-renders them.
- No edit to `ci_predictions/pr.json`, `REGISTERED.md`, `PRIORITY_QUEUE.md`, or `.z1-control/`.
- No Z2 signature. Nothing here is a RATIFY event.

## 7. Decisions needed from Z2

| Row | Question | Z1 recommendation |
|:--|:--|:--|
| S1 | Accept the window (2026-10-22) and the resolver (last head before close) | Accept |
| S2 | Accept the lane priors in §2 as the opening pins, or set your own | Accept; they are a starting point, and the pins are scored against outcomes |
| S3 | Authorise a read of the 12 UNREAD receipts before the window opens | Yes; it fixes the largest uncertainty in the sweep |
| S4 | One ci-predict consolidate PR at a time, starting now | Yes; the stack is the largest source of churn in the queue |

---

_Generated with [Claude Code](https://claude.com/claude-code)_
