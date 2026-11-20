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

## Options

- `minors accepted, private-only tests`
- `minors accepted, public fixture tests`
- `minors accepted, vendor the two files`
- `minors accepted`
- `repair minors`
- `edit`
- `later`

Questions 1 and 2 are **not offered as choices**. Question 2 asks for a reviewer, which is a name, and no option can carry one; the ruling record has a `note:` field where Night can write it, but the note is not a choice. Question 1 (admission) should wait for questions 2 and 3, as the block says, so no option admits the bridge. Any other combination is an `edit`.

## What each sets in motion

Every option except `edit` and `later` rules this block, and a merged ruling marks the **whole block** `ratified`. The relay refuses a second ruling, so questions 1 and 2 (and any of 3 or 4 an option leaves open) can then return only as a new block.

- `minors accepted, private-only tests`: a Z2 record that the three audit-7 minors (register item 31) are accepted and stay OPEN, and that the tests stay verifiable only by someone who holds the two private files at the hashes the README names. It changes no file except this one.
- `minors accepted, public fixture tests`: the same acceptance, and a direction to rewrite the tests so they run against a public fixture. That is a later pull request Z1 drafts in the bridge folder. Z1 has not sized it: the code calls into the two private files, so the work is whatever stands in for them.
- `minors accepted, vendor the two files`: the same acceptance, and a direction to copy the two private files into this repository. They come from the private Project Desk app (README), so this would make app code public here. Z1 has not read them and cannot decide that for the app's owner. Night decides whether they may be public at all.
- `minors accepted`: only question 4 is answered. How the tests run (question 3) stays open and returns as a new block.
- `repair minors`: no acceptance. Z1 drafts a pull request repairing the three minors in the bridge code. The register's item 33 ("accepted and stay OPEN") would then be superseded by this ruling. How the tests run stays open.
- `edit`: Z1 revises the block and files it again.
- `later`: this block closes with its bytes signed; the question returns only as a new block.

## Checked on 2026-11-20 (main `71414758`)

- **The folder is on main and is a candidate only.** It was merged in #1203, with its files listed under `excluded:` in `z1-inbox/INDEX.yaml`, so they are staged, not decided.
- **The README still says** "Not HUMAN_REVIEW_READY" and lists as not done "any human-recorded outcome, independent human review, live Gmail beyond one small approved read-only sample, browser UI wiring".
- **Other OPEN items stay in the register** and are not asked here: the browser UI is not wired and was not re-run (item 3); real report values are free text, so the adapter says UNCORROBORATED (item 4); plan output may carry private-looking text (item 5); the log-wide quantity bound is unit-agnostic (item 10); redaction does not catch names or phone numbers (item 14); a weak salt is accepted (item 15); a partial apply is not idempotent (item 18); `verify-history` can exit 0 with events dropped (item 19); grants match by grant id only (item 23). Z1 did not re-run any of the bridge's tests; they need the two private files.
- **Not checked:** the live Desk and INTENT-OS were never touched by the bridge, per the register. Z1 did not verify that independently.

## Checked again on 2026-11-20 (main `16ac24c0`), for this ruling

- **The README is unchanged.** It still says "Not ratified. Not HUMAN_REVIEW_READY" and still names the two private files and their sha256 values.
- **`vendor/` is not the two private files.** The bridge's `vendor/` folder holds one file, `resource-units.snapshot.json`. `dist/model.js` and `dist/intent-workspace.js` are not in the tree.
- **The register is `docs/LIMITATION_REGISTER.md`.** Item 31 lists the three audit-7 minors (NEW-1 to NEW-3). Item 33 records a "HUMAN DECISION after audit 7" that they are accepted and stay OPEN. That is a line in the bridge's own register, not a Z2 ruling record; Z1 found none (searched `REGISTERED.md`, `z1-inbox/INDEX.yaml` and the `Z2_RULINGS_*.md` files for "project desk"; the only hits in the index are this block's own entry and the bridge's file list).
- **Issue #1126 is still open.** It carries the label `proposal` and the status line "PROPOSED / WAITING FOR NIGHT". Its seventh "Done means" item is still the independent exact-head test and human evaluation record.
- **Not re-run:** the bridge's tests (they need the two private files).

## Ruling

choice: minors accepted, private-only tests
by: Z1-prepared (not an identity claim)
at: 2026-11-20T02:52:49Z
status: DECIDED
block_hash: f111a1f2b1762e172877e16f84675340c2709f3b7aef976ebee51d9fab996c69
body_hash: 83ae7661b954c1c42fcf91ceedd663d1c4313a8f70cbd9c8001dba90401f1c85

```
RULING z1-projectdesk-01
  by: Z1-prepared (not an identity claim) (tagline)
  project: humanaios
  question: Accept the three audit-7 minors as open (register item 31) and keep the bridge tests verifiable only with the two private files? Question 1 (admission as the issue 1126 E0 receipt) and question 2 (the independent reviewer) are not ruled and, once this block is ratified, can return only as a new block (Q-PROJECT-DESK-BRIDGE-ADMISSION-01)?
  choice: minors accepted, private-only tests
  note: 
  at: 2026-11-20T02:52:49Z
  status: DECIDED
```

## Z2 Review Checklist

- [ ] Question 2: name an independent reviewer, or record that none is named.
- [ ] Question 3: pick how the tests run.
- [ ] Question 4: confirm the acceptance of the three minors in a Z2 record, or ask for the repair.
- [ ] Question 1: decide admission only after the three above, and only once both of the issue's last prerequisites are recorded as done: the independent exact-head test and the human evaluation record. If no reviewer is named, or either is still pending, admission stays pending.

## Falsifier

Event-based, no clock. This block is wrong, and should be withdrawn in whole or in part, if any of these happens:

- (a) a Z2 ruling on the bridge, on the E0 receipt, or on the three minors is found in `REGISTERED.md`, `z1-inbox/INDEX.yaml` or a Z2 rulings file. Z1 did not find one. Probe: `grep -rn -i "project-desk\|project desk" REGISTERED.md z1-inbox/INDEX.yaml z1-inbox/*/Z2_RULINGS_*.md`.
- (b) the two private files are placed at the paths the README names and `node scripts/run-all.cjs` does not report 195 passing checks in 4 suites. The #1203 description's claim would then be wrong, and question 3 changes.
- (c) an independent human review of the bridge is recorded. Question 2 is then answered, and this block should be narrowed to the rest.
