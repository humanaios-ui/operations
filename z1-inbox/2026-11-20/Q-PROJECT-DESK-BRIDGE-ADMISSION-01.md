# Q-PROJECT-DESK-BRIDGE-ADMISSION-01 — the open items of the Project Desk bridge (merged in #1203): admit it as the issue #1126 E0 receipt, who reviews it independently, how its tests run, and the three accepted minors

**Z1 Proposer:** Claude (Z1)
**Date Submitted:** 2026-11-20
**Status:** AWAITING Z2 RATIFICATION
**Filed because:** #1203 merged the folder `z1-inbox/2026-11-12/project-desk-bridge/` as a candidate. It says so itself: its README is headed "DRAFT proposal. authority_effect NONE. Not ratified. Not HUMAN_REVIEW_READY." A merge of a candidate folder is not a ruling on it. Issue #1126 asked Night to decide whether to admit one private E0 round-trip proof; nothing in `z1-inbox/INDEX.yaml` or `REGISTERED.md` records that decision (Z1 searched both files for "project-desk" and `INDEX.yaml` for "1126"; it did not search further). This block puts the decision, and the items that block it, in front of Night.

This file decides nothing and changes no file other than itself and the index. It does not touch the bridge.

## What Z2 is asked to decide

1. **Admit the bridge as the #1126 E0 receipt?** Issue #1126 asks "whether to admit one private E0 round-trip **proof only**" and says "Done means" seven things, the last being "independent exact-head test and human evaluation record the outcome". Z1 does not recommend admitting before items 2 and 3 are settled, because that last condition is not met (see below).
2. **Who is the independent reviewer.** The bridge's own README says "Not done: any human-recorded outcome, independent human review". Its seven audits were Claude contexts started by the author, not independent humans, and never saw the real data. Night names a reviewer, or says the receipt waits.
3. **How the tests run.** The code needs two files from the private Project Desk app that are not in this repository: `dist/model.js` and `dist/intent-workspace.js` (exact sha256 values are in the README). Without them nothing runs from this repository alone (the README says so). The #1203 description reports 195 checks in 4 suites passing locally with them; Z1 has not re-run them. Options: vendor the two files, rewrite the tests against a public fixture, or accept private-only verification.
4. **The three accepted minors.** The limitation register (item 31) lists three open minors from audit 7: `evidence --overwrite` can leave a private file behind when the public target cannot be renamed over; the adapter can draft events the log then refuses, so "every draft is appendable" is not yet true; and after 99 stale applies the preserved-choices copy stops saving and the exit code changes. Item 33 records a "HUMAN DECISION" that these are accepted and stay OPEN. Z1 found no Z2 ruling that records that acceptance. Night confirms the acceptance, or asks for the repair.

Z1's lean, not a decision: 2 and 3 first, then 1. Questions 2 and 3 are what the issue's "Done means" item 7 depends on.

## Checked on 2026-11-20 (main `71414758`)

- **The folder is on main and is a candidate only.** It was merged in #1203, with its files listed under `excluded:` in `z1-inbox/INDEX.yaml`, so they are staged, not decided.
- **The README still says** "Not HUMAN_REVIEW_READY" and lists as not done "any human-recorded outcome, independent human review, live Gmail beyond one small approved read-only sample, browser UI wiring".
- **Other OPEN items stay in the register** and are not asked here: the browser UI is not wired and was not re-run (item 3); real report values are free text, so the adapter says UNCORROBORATED (item 4); plan output may carry private-looking text (item 5); the log-wide quantity bound is unit-agnostic (item 10); redaction does not catch names or phone numbers (item 14); a weak salt is accepted (item 15); a partial apply is not idempotent (item 18); `verify-history` can exit 0 with events dropped (item 19); grants match by grant id only (item 23). Z1 did not re-run any of the bridge's tests; they need the two private files.
- **Not checked:** the live Desk and INTENT-OS were never touched by the bridge, per the register. Z1 did not verify that independently.

## Z2 Review Checklist

- [ ] Question 2: name an independent reviewer, or record that none is named.
- [ ] Question 3: pick how the tests run.
- [ ] Question 4: confirm the acceptance of the three minors in a Z2 record, or ask for the repair.
- [ ] Question 1: decide admission only after the three above.

## Falsifier

Event-based, no clock. This block is wrong, and should be withdrawn in whole or in part, if any of these happens:

- (a) a Z2 ruling on the bridge, on the E0 receipt, or on the three minors is found in `REGISTERED.md`, `z1-inbox/INDEX.yaml` or a Z2 rulings file. Z1 did not find one. Probe: `grep -rn -i "project-desk\|project desk" REGISTERED.md z1-inbox/INDEX.yaml z1-inbox/*/Z2_RULINGS_*.md`.
- (b) the two private files are placed at the paths the README names and `node scripts/run-all.cjs` does not report 195 passing checks in 4 suites. The #1203 description's claim would then be wrong, and question 3 changes.
- (c) an independent human review of the bridge is recorded. Question 2 is then answered, and this block should be narrowed to the rest.
