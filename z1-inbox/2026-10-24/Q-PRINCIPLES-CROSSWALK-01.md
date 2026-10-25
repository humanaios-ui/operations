# Q-PRINCIPLES-CROSSWALK-01 — Seed Constitution v0.1 × Repository Crosswalk

**Status:** Z1 proposal. Unratified. Awaiting Z2 signature.
**Authority effect:** NONE. Table and draft amendment only. No change to `seeds/seed-constitution-v0.1.md`, `REGISTERED.md`, or any gate.
**Source of gaps:** Merged review of two independent crosswalks (Z1 and an external review). Holes 1–5 numbering follows the external review.
**Pinned at:** branch `claude/constitution-principles-crosswalk-g53etj`, base `5082897`.

---

## 1. Crosswalk — nine principles, nine rows

Columns: file ID · test · owner · known gap.

| # | Principle (`seeds/seed-constitution-v0.1.md`) | File ID (repo counterpart) | Test (locked, no new tests) | Owner | Known gap |
|---|---|---|---|---|---|
| 1 | Residual Human Authority | `REGISTERED.md` Z2 sole-write rule; `CLAUDE.md` Z2 authority | CT-001 Pass A done (PR #452, merged 2026-09-22). Pass B open. H-CT-001 UNRESOLVED | Z2 (Night) | Hole 1: text says "unless a multi-stakeholder process ratifies otherwise." No process defined. Routed to #559 |
| 2 | Verifiable Attribution | Commit authorship check in `z2_ratification_gate.yml` (advisory); CODEOWNERS | Test 1 (locked) | Z2 + CI | Hole 2: ratification is text-only. Commit-author check is advisory, not blocking (see AUTHORIZATION_EVIDENCE_MAPPING row IC-050). Amendment §3 |
| 3 | Least-Privilege Agency | `behavior_spec.json` agent caps; Z3 caps in `CLAUDE.md` | Test 2 (locked) | Z3 + CI | No known gap in this crosswalk. Hole 3 per external review. Routed to #559 |
| 4 | Evidence Before Authority | F-64 "Assurance Accumulating; Evidence Not" (observed 2026-09-13, ratified 2026-09-13) | Test 3 (locked) | Z1 (evidence rows) | F-64 observation, dated 2026-09-13: 94 ratified artifacts, zero sourced evidence rows. Later `NF_LEDGER.jsonl` entries (seq 166–172, dated 2026-09-16) are seven resolved forecasts with outcome NO. That shows resolution has begun. It does not close F-64 or measure current calibration |
| 5 | Calibration and Humility Gate | IC-058 "Outcome-Symmetry Corpus Gap"; F-62 (capacity) | Test 4 (locked) | Z1 + Z2 | IC-058: most H entries lack a disconfirm branch (external review: 26 of 29; **not re-counted here**). Hole 5: single Z2 oversubscribed (F-62). Hole 5 is the same root cause as #559 |
| 6 | Transparent Resource and Influence Claims | `NF_LEDGER.jsonl` hash chain; `RESOURCE_UNITS.yaml` | Test 1 (locked) | CI | No gap named in either review |
| 7 | Non-Binding Identity Constructs | None found in `REGISTERED.md` | Test 2 (locked) | — | **No counterpart.** External review said so. Z1 confirmed no match for principle 7 text in the file. Gap stands |
| 8 | Service Orientation and Common Welfare | None mechanical | Test 3 (locked) | — | Text-only. No gate. Known gap |
| 9 | Open Process and Drift Detection | Append-only rule in `REGISTERED.md`; STALE/DRIFT callouts in `CLAUDE.md`; deprecation policy in `seeds/CHANGELOG.md` (removal after one version's notice) | Test 4 (locked) | Z1 | Hole 4: the deprecation policy allows removing a principle from a successor version. It does not say whether historical records may be deleted. Amendment §4 |

**Test column note:** The four locked tests (Tests 1–4) come from the external review. This repo did not contain them when checked. CT-001 is the only test found in the repo. Z2 must confirm the four test definitions before this table is ratified.

## 2. Cost

- One Z2 slot to ratify this table.
- Holes 3 and 5 go to #559. No new work here.
- Holes 1, 2, 4 need the amendment below.

## 3. Draft amendment A (hole 2) — ratification is text-only

Proposed: any ratification of a seed principle must name the signing identity. CI check must be blocking, not advisory. Reference: `AUTHORIZATION_EVIDENCE_MAPPING.md` IC-050.

## 4. Draft amendment B (hole 4) — append-only vs. deletion

Existing policy (`seeds/CHANGELOG.md`, Backwards Compatibility): a principle may be removed from a successor version after one version of deprecation notice. That stays as is. The gap is narrower: historical records of a removed principle are not covered.

Proposed rule: removing a principle from a successor version is allowed after the existing deprecation notice. Its historical record is kept, marked `SUPERSEDED` with a forward pointer. Deleting a historical record is never allowed. Matches `REGISTERED.md` line 6.

## 5. Draft amendment C (hole 1) — multi-stakeholder process

Not drafted here. Waits on #559 option C (sortition panel). Adding a process now would pre-empt that design.

## 6. Flip check

Flip condition: "if #559 already covers holes 1, 2, 4, add nothing."
Result: #559 covers hole 1 (in design form) and part of hole 2. It does **not** cover hole 4. So amendment B is needed. Amendments A and C are needed only if #559 is not accepted as the route for them.

## Falsifier

This proposal is wrong if any of the following holds at Z2 read:

1. A file ID in the table does not resolve to a file in the repo at the pinned base.
2. A principle the table marks "No gap" has a counterpart that a Z2 read can name.
3. #559 is accepted as covering hole 4 (append-only vs. deletion). Then amendment B is unneeded.
4. The deprecation policy in `seeds/CHANGELOG.md` is read to forbid all removal. Then the amendment B framing is wrong.

## 7. Limits

- Not verified: external review's counts (26 of 29 H entries; hole numbering 1–5 mapping).
- Not verified: the four test definitions.
- Not verified in this repo's implementation: INTENT-OS, Coordinator, Evidence Graph, Witness, Resource Miner. `REGISTERED.md` does name INTENT-OS and Witness (`Q-Z2-DUAL-AUTHORITY-GOVERNANCE-01`, `Q-INTENT-OS-WITNESS-LEDGER-01`). The implementation was not checked here, so these are dropped from the table for that reason only. Their absence from the table is not evidence they lack a registry record.
