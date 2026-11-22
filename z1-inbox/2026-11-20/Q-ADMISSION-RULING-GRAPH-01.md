# Q-ADMISSION-RULING-GRAPH-01 — a generated, read-only page that joins the admission ledger to Z2 rulings, a pointer issue for it, and telling contributors how admission works

**Z1 Proposer:** Claude (Z1)
**Date Submitted:** 2026-11-20
**Status:** AWAITING Z2 RATIFICATION
**Filed because:** Night asked whether an issue should exist that governance follows for admission, so admission can be tracked and graphed. Z1 compared a tracking issue (A) with a generated page (B); Night said "file B", then added that the entryways need to be updated to inform contributors of the method update. This block files B and that addition. It is a candidate.

This file decides nothing and changes no file other than itself and the index. Z1 reads "the method" as admission as it runs today (an exact-head admit, receipts, a ledger), not a new rule. If Night meant a different method, question 4 changes.

## What Z2 is asked to decide

1. **Adopt a generated, read-only page as a direction.** A script reads the admission ledger and joins each admitted pull request to the Z2 ruling it carried, as edges: admit, voided by a push, merged, ruled. It writes nothing back and carries `authority_effect NONE`. Building it is a separate Tier 2 pull request after ruling, drafted by Z1.
2. **How the page is kept honest.** The ledger lives on another branch and grows on every admit anywhere, so a pull-request `--check` against it would turn red on admits unrelated to that pull request. That is unlike `INTENT_GRAPH.md` and `Z1_INBOX_INDEX.md`, which are checked against files in the same tree. Options: regenerate the page by a workflow on pushes to `main` and open a pull request, as the reconcile job does; gate only the generator's own smoke test; or both. Z1's lean, not a decision: both.
3. **A thin pointer issue.** One open issue that links to the page, holds no rows, and says `authority_effect NONE`, so governance has a place to follow. Yes or no. It carries no `/coordinator` command text: Z1 did not read which issue comments the admission gate acts on.
4. **Tell contributors the method.** Update the entryways to say how admission works today. Z1 drafts the wording in separate pull requests after ruling; Night ratifies it, because these files shape behaviour. What they would say, all observed on pull requests today:
   - A ready pull request needs an explicit `/coordinator admit <full head SHA>` from an authorized identity. Z1 saw only Night's login do it and did not read who else may.
   - Any push after an admit voids it. A draft pull request lands in lane WORKBENCH and carries no weight.
   - The pull request body needs a `molt_tier_claimed` line.
   - Where to see admission status (the page, if question 1 is adopted).

## Options

- `page, both checks, issue, entryways`
- `page, both checks, entryways`
- `page, both checks, issue`
- `page, both checks`
- `entryways only`
- `edit`
- `later`

The words are the four asks in "What Z2 is asked to decide" above. Every `page` option adopts question 1 and answers question 2 with Z1's lean, **both** (a workflow that refreshes the page by pull request, and a gate on the generator's own smoke test). Any other answer to question 2, such as refresh only, is an `edit`. `issue` answers question 3 yes. `entryways` answers question 4 yes for the six files that mention admission zero times: `README.md`, `CONTRIBUTING.md`, `.github/PULL_REQUEST_TEMPLATE.md` and the three issue templates. Narrowing that list is an `edit`.

## What each sets in motion

Every option except `edit` and `later` rules this block, and a merged ruling marks the **whole block** `ratified`. The relay refuses a second ruling, so whatever an option leaves out can return only as a new block. Each adopted item is a direction: it changes no file except this one, and each is a later pull request that Z1 drafts. Any that touches a workflow is reviewed on its own.

- `page, both checks, issue, entryways`: all four. A generator that reuses `tools/repository_coordinator_state_v1.py` (`parse_ledger`, `replay_events`), reads the ledger from the `repository-coordinator-state` branch and joins each admitted pull request to the ruling it carried. A workflow that refreshes the page by pull request after merges to `main`, and a gate on the generator's smoke test. One open issue that links to the page, holds no rows and says `authority_effect NONE`. Updates to the six entryway files, wording drafted by Z1 and reviewed in each pull request; this ruling does not fix the wording.
- `page, both checks, entryways`: the same without the issue.
- `page, both checks, issue`: the same without the entryway updates. Contributors are still not told how admission works.
- `page, both checks`: the page and its checks only.
- `entryways only`: no page. The six files say how admission works today (an exact-head admit from an authorized identity, a push voids it, a draft carries no weight, the `molt_tier_claimed` line) and omit the "where to see status" line. No generator reads the ledger, and the gap seen on #1277 stays unexplained.
- `edit`: Z1 revises the block and files it again.
- `later`: this block closes with its bytes signed; the question returns only as a new block.

## Checked on 2026-11-20 (main `5d61dc97`)

- **The live ledger is on the `repository-coordinator-state` branch, not on `main`.** The snapshot Z1 read there has 390 rows; the last is sequence 390 (pull request 1275). `main` carries `ADMISSION_LEDGER.jsonl` with 71 rows, the last sequence 71 (pull request 873). A page that read `main` would miss 319 rows.
- **Row mix in that snapshot:** ADMIT 196, TERMINATE_MERGED 95, REVOKE 80, ACK_ALREADY_ADMITTED 10, TERMINATE_CLOSED 9. A REVOKE looks like an admit voided by a push: Z1 saw that pattern on its own pull requests, but did not read the gate code that writes the row. 25 rows have no `sequence`, hash or locator fields (older rows). 7 rows carry an `objective_issue_number`.
- **The ledger does not hold the join to rulings.** Its key is the pull request number (`subject_number`). Rulings are keyed by Q-ID and path in `INDEX.yaml` and `Z2_RULINGS_*.md`. Z1's proposed join: pull request number, to its merge commit on `main`, to the `z1-inbox/**/Q-*.md` files that commit changed. Z1 has not built or tested it.
- **A reader already exists and verifies.** `tools/repository_coordinator_state_v1.py` has `parse_ledger`, `replay_events`, `load_and_replay` and a `verify` command. A generator should call these, not re-parse. Z1 did not run `verify`, and did not check how it treats the 25 older rows.
- **An unexplained gap shows why a generated view helps.** In the snapshot, pull request 1277 shows ADMIT then REVOKE and no TERMINATE_MERGED row, though it merged. Z1 has not found why.
- **Entryways, mentions of admission:** `AGENTS.md` already points to the coordinator's admission state (3 mentions). `README.md`, `CONTRIBUTING.md`, `.github/PULL_REQUEST_TEMPLATE.md` and the three issue templates (`code-quality.md`, `general-issue.md`, `seed-amendment.md`) mention it 0 times. The pull request template already asks for `molt_tier_claimed`. No file under `docs/` is named for admission, the coordinator or contributing; Z1 searched by file name only, not by content.
- **Cost vector, Z1 estimate, not measured, units not collapsed:**
  - RAT-min: B higher up front (a ruling, then review of each pull request), near zero after. A tracking issue costs Night almost nothing.
  - Z1-ktok: B higher once, then near zero. A recurs after every admit and ruling.
  - CI-min: B small and recurring. A none.
  - A hand-kept tracker restates facts by hand; `Q-REFERENT-DECAY-01` named that failure and its option D (generate restated facts) is the cure.
- **Not checked:** whether CI can read the state branch; whether a new generated page must be registered with doc control; the active CODEOWNERS for the entryway files; the hash chain of the ledger.

## Checked again on 2026-11-20 (main `51e16612`), for this ruling

- **The ledger grew.** The state branch now has 395 rows (ADMIT 197, TERMINATE_MERGED 97, REVOKE 81, ACK_ALREADY_ADMITTED 11, TERMINATE_CLOSED 9), the last for pull request 1285. `main` still carries 71.
- **The #1277 gap, now with evidence.** Row 382 is an ADMIT bound to head `0508601e`. Row 383 is a REVOKE recording that the live head had moved to `acd7e7e` (exact-head admission drift). There is no row for the admit that Night posted on the final head `f2dae4e`, and no merged row; the pull request merged within seconds of that comment. Z1's reading, unverified, is that it merged before the admit's state event committed. Z1 did not read the coordinator code. A page built on the ledger would show #1277 as an admit voided by drift and nothing after it.
- **#1285 is the opposite case.** ADMIT (394) then TERMINATE_MERGED (395): the ledger recorded both.
- **A reader still exists and nothing else does.** Only `tools/repository_coordinator_state_v1.py` and its test mention `ADMISSION_LEDGER`.
- **Entryways unchanged:** `README.md`, `CONTRIBUTING.md`, the PR template and the three issue templates mention admission 0 times; `AGENTS.md` mentions it 3 times.
- **Not checked:** CI access to the state branch, doc-control registration of a new page, the active CODEOWNERS for the entryway files, the ledger hash chain, and the proposed pull-request-to-Q-file join.

## Ruling

choice: page, both checks, issue, entryways
by: Z1-prepared (not an identity claim)
at: 2026-11-20T17:08:58Z
status: DECIDED
block_hash: 207de639dcc4d1880bdced9938323feb4bfff8ec1c9405ded5d47a0c995ec1fd
body_hash: dcd608832206669206938f3d8ab7ed9a7be8e9bce78d8be2836bccc5c6bc5f95

```
RULING z1-admissiongraph-01
  by: Z1-prepared (not an identity claim) (tagline)
  project: humanaios
  question: Adopt a generated read-only page joining the admission ledger to Z2 rulings (refreshed by a workflow, with a gate on the generator's smoke test), a thin pointer issue, and updates to the six entryway files? Each is a direction built later in its own pull request, and this ruling does not fix the entryway wording. Anything not named here can return only as a new block (Q-ADMISSION-RULING-GRAPH-01)?
  choice: page, both checks, issue, entryways
  note: 
  at: 2026-11-20T17:08:58Z
  status: DECIDED
```

## Z2 Review Checklist

- [ ] Question 1: adopt the generated read-only page as a direction? A yes starts a separate Tier 2 pull request.
- [ ] Question 2: how the page is kept honest (workflow refresh, smoke-test gate, or both).
- [ ] Question 3: open the thin pointer issue, yes or no.
- [ ] Question 4: ratify updating the entryways, and say which of them.

## Falsifier

Event-based, no clock. This block is wrong, and should be withdrawn in whole or in part, if any of these happens:

- (a) a generator that reads `ADMISSION_LEDGER.jsonl` and writes a page is found. Probe: `grep -rln ADMISSION_LEDGER tools scripts`. Z1 found only the state tool and its test today.
- (b) CI cannot read the `repository-coordinator-state` branch without a credential it lacks. Then B is not feasible and the tracking issue (A) wins.
- (c) for a sample of recent rulings, the join from pull request number to Q-file fails for most of them. The page would then be mostly orphan nodes.
- (d) a contributor-facing doc on admission exists and `README.md` and `CONTRIBUTING.md` link to it. Question 4 is then mostly done.
