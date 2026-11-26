# Q-AGENT-CHECKIN-HA000-LEDGER-01 — the two asks `Q-AGENT-CHECKIN-CALIBRATION-01` left unruled: who administers HA-000, and whether review findings get a ledger

**Z1 Proposer:** Claude (Z1)
**Date Submitted:** 2026-11-20
**Status:** AWAITING Z2 RATIFICATION
**Filed because:** the parent block, `Q-AGENT-CHECKIN-CALIBRATION-01`, was ruled `ratify 1-3` (asks 1-3: edge-state grading, the `failure` / `defeats_if_unmitigated` vocabulary, and a `calibration` block in participation contract v0.2). That ruling merged in #1264 and was reconciled in #1265, signature `9029baf16e6415ee1cab97558f8b1582945b38106049e40fc9136645b8b12744`. A ratified block takes no second ruling, so the two asks the parent did not offer, 4 and 5, can return only as a new block. This is that block.

This file decides nothing. It adds no workflow, schema or ledger. It asks two questions and records what Z1 checked.

## What Z2 is asked to decide

1. **Who administers HA-000.** HA-000 is the founding H-ACAT run. H-ACAT measures the human operator, so Z1 cannot run it, and Z1 cannot name its own administrator. Night names one, or says the `H-ACAT` instrument of the new `calibration` block stays unusable until someone does. `NONE_DECLARED` stays legal either way, as the parent's ruling left it.
2. **Whether review-agent findings get a ledger.** One row per finding: agent, file, class (`single-file-contract` or `cross-artifact`), verdict on verification. The pattern exists for other measures. The parent recommended deferring this until asks 1-4 were ruled. Asks 1-3 now are; ask 4 is question 1 above. So the parent's own condition for question 2 is met only after question 1 is ruled.

Z1's lean, not a decision: rule question 1 first, then question 2. Question 2 builds instrumentation on the `failure` vocabulary, which is ratified as a direction but not yet written into any schema (see below).

## Checked on 2026-11-20 (main `71414758`)

- **HA-000 is recorded as not run.** `AGENT_GRAPH_COMPARISON.md` line 211 says "HA-000 not yet executed". Z1 searched the tree for lines about HA-000 and found only lines saying it has not run; it did not search for a record that it did run, under other wording. The roadmap that the parent cites for the same fact lives in another repository, and Z1 did not look there.
- **Asks 1-3 are ruled as directions only; nothing is built.** `INTENT_GRAPH.yaml` is still `version: 1` with no edge-state field. `PARTICIPATION_CONTRACT_V0_1.schema.json` has no `calibration` field. The v0.2 pull requests the ruling calls for are not filed.
- **The ledger pattern exists.** `audits/molt_tier_gap_ledger.jsonl` and `audits/smag_pilot_ledger.jsonl` are in the tree.
- **A review-findings ledger may already exist under another form.** `audits/` also holds `REPORT_2_FINDINGS_LEDGER_S042727.docx` and `PR_REVIEW_REPLACEMENT.md`. Z1 found them by file name only and did **not** open them, so it cannot say whether either overlaps question 2.
- **Not re-checked:** the section 3 counts of the parent block (20 findings, 20 of 20 verified), and any record of a run kept outside this repository.

## Z2 Review Checklist

- [ ] Name an administrator for HA-000, or record that none is named yet.
- [ ] Decide whether question 2 waits for question 1, as Z1 leans.
- [ ] If question 2 is taken up, someone opens the two audits files named above first, to see whether a findings ledger already exists.
- [ ] After that check, give question 2 a disposition: accept it, reject it, or defer it explicitly. If neither audit file holds a ledger and no disposition is recorded, question 2 stays unanswered.

## Falsifier

Event-based, no clock. This block is wrong, and should be withdrawn in whole or in part, if any of these happens:

- (a) a record that HA-000 was run exists, in this tree or in the roadmap repository. Question 1 is then moot. Probe: `grep -rn "HA-000" --include=*.md .` and look for any line that says it ran, not "not yet".
- (b) `audits/REPORT_2_FINDINGS_LEDGER_S042727.docx` or `audits/PR_REVIEW_REPLACEMENT.md` is opened and turns out to be a review-findings ledger with the fields question 2 names. Question 2 is then a duplicate.
- (c) the v0.2 graph or contract pull requests are filed with a different `failure` vocabulary than the parent ruling describes. Question 2's taxonomy would then be stale.
