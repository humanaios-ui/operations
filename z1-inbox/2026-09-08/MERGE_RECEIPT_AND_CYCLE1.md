# Merge receipt 2026-09-08 · and the shortest path to 1/40

## A. Verified (by fetch from origin/main, not from the PR page)
| PR | merge commit | merged by | files | re-test from main |
|---|---|---|---|---|
| #217 tools | c76da54c | humanaios-ui | tools/ic_scope_check.py, molt_cycle.py, jester_invariants.py, cascade_guard.py | jester SELF-TEST PASS · cascade SELF-TEST PASS · molt NO TRIGGER CROSSED |
| #218 inbox+board | c6eb7202 | humanaios-ui | z1-inbox/2026-09-07/{JESTER_EXTERNAL_CHECK_BLOCK, WITCH_SPELL_CASCADE_BLOCK}.md, ui/intent-os-humanaios-v3_1.html | n/a (documents) |

REGISTERED.md sha 40391062966c6d6f… (3909 lines) — unchanged. Nothing registered by these merges. Correct.
Operated count after merges: **0/40**. Merging code is LAID.

## B. Findings from the verify
- **F-CAND-INTAKE-01** `intake_template.jsonl` is absent from the repo, although it is referenced by the Intent-OS board and the `python tools/prs_run.py --input intake_template.jsonl` command. The "job-posting batch" path has no input schema in the record. Prior sessions carried the filename from memory. Falsifier: `git log --all -- '*intake_template*'` returns a commit.
- **IC-CAND-RI-STACK** `c08f86c` (research-intake v0.1, direct push 2026-09-07) sits under these merges with RT-07 (contract id in public history) and RT-10 (commit message asserts a ratification the yml marks PENDING) open. Not caused here; noted because the chain now builds on it.

## C. What an operated cycle IS (proposed definition; needs a hash)
One cycle = all five, in order, with receipts:
1. a **real input** that did not originate from Z1 (a review by another substrate, a platform export, a posting a third party wrote);
2. a **prediction hash** in REGISTERED.md *before* the run (dial-then-declare guard);
3. the run executed by **code** that emits the verdict (no author override);
4. CYCLE + VERDICT events appended to a **hash-chained ledger**;
5. the prediction **resolved into NF** with its Brier.
Miss any one → LAID, not counted.

## D. Three doors to cycle 1, ranked by distance
| door | real input | blocked on | distance |
|---|---|---|---|
| **1. External-check cycle** | one blind review of one landed artifact by a non-Claude substrate (Grok/Copilot/ChatGPT), written as a row in `reviews.jsonl`; `jester_invariants.py` runs on it | nothing — no contract, no schema, no new ruling. P-J4 (novelty ≥ 0.30, 0.50) is already locked | **hours** |
| 2. Research-intake SPC-01 | platform export for the n=1 specimen through `research_intake_evaluator.py` v0.2 | B1 contract check; v0.2 re-land via PR (RT audit C.1) | days–week |
| 3. Job-posting batch | 10–40 postings | d6 source ruling **and** an intake schema that does not yet exist (F-CAND-INTAKE-01) | week+ |

Z1 read: door 1 is cycle 1. It operates the component both reads say is load-bearing (the external check), and it is the only door with zero open decisions.

## E. Door 1 procedure (Z2 does step 1 and 2; code does the rest)
1. Z2 pastes `system_graph.json` (or either candidate block) to a second substrate with the instruction: "Review this. Do not be told the author's conclusion. List objections and options." No conclusion, no prediction shared (JESTER-01).
2. Z2 pastes the review back here verbatim.
3. Z1 writes the row: `review_id`, `artifact_id`, `author_substrate=claude`, `critic_substrate=<name>`, `critic_saw_conclusion=false`, `author_points` (from the artifact), `critic_points` (from the review), `catches`, `planted=0`, `agreement`, `critic_text`, and `ts` (ISO timestamp).
4. `python3 tools/jester_invariants.py reviews.jsonl --artifacts artifacts.jsonl` → verdict by code.
5. Events appended; P-J4 resolved into NF with Brier; count becomes **1/40**.
Pre-registered prediction already on record in the jester block: P-J4 novelty ratio ≥ 0.30 at 0.50.

## F. Board patch
Step 9 on the Intent-OS board (first operated cycle) gains a sub-step 9a "external-check cycle — door 1"; blockedOn: none.
