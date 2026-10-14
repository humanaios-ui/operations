# Q-MULTI-AGENT-QUEUE-PLAN-01 — Multi-agent plan for the backed-up PR queue

**Document ID:** Q-MULTI-AGENT-QUEUE-PLAN-01
**Date:** 2026-10-14
**Author:** Z1 (Claude)
**Status:** Awaiting Z2 ratification
**Pinned main:** `3bf3b215a725f533c4b99ab3e0ee9cac66f4305c` (fetched 2026-10-14; IC-030 live-fetch)
**Evidence record:** `z1-inbox/2026-10-14/QUEUE_MAP_2026-10-14.md`
**Authority effect:** NONE. This is a proposal. Nothing here admits, ratifies, merges, deploys, or assigns authority.

---

## Candidate block

```yaml
candidate_id: "Q-MULTI-AGENT-QUEUE-PLAN-01"
title: "Multi-agent plan to work the intentionally backed-up PR queue as a governed experiment"

description: |
  Z2 stated the PR queue was backed up on purpose, for five reasons: stress testing,
  personal learning, integration of the framework into the repository agents of
  operations / humanaios / lasting-light-ai, demonstration of the framework, and
  recursive learning. This candidate proposes a multi-agent arrangement that works
  the queue while serving all five, and that treats the clearance itself as a
  preregistered experiment with pinned predictions and a falsifier.
  - 36 PRs are open; 32 of the 33 swept on 2026-10-12 show the Repository
    admission/backpressure gate check as failed. That check result mixes at least
    three causes that need different acts: a FAIL decision for want of a Z2 ADMIT
    record; a PASS decision whose receipt comment then failed with HTTP 403
    (verified on PR #740: PASS / MAINTENANCE, then 403 publishing the receipt);
    and non-draft PRs that would route to WORKBENCH if their draft flag matched
    their prose. The split across the 32 is not yet measured.
  - Ten PRs collide on tools-manifest.yaml; three GNER lineages compete for the
    same files; four PRs are superseded by newer ones.
  - RAT-min (Z2 attention) is the ratified binding constraint, so the design
    batches every Z2 act into decision sheets and keeps all agent work upstream
    of the admitted set, which is capped at four by REPOSITORY_COORDINATOR_POLICY.json.

author: "Z1 (Claude)"
proposed_at: "2026-10-14T23:00:00Z"

scope:
  - "operations (Z-000): PR queue, z1-inbox, ci_predictions, ledgers"
  - "humanaios (Z-001) and lasting-light-ai (Z-008): agent manifests, proposals only"
  - "No constants, gates, workflows, or REGISTERED.md are changed by this candidate"

resource_cost:
  cost:
    RAT-min: 150     # PRIOR: ~75 for Decision Sheet 1 (10 rows) + ~3 per ADMIT x ~25 PRs
    Z1-ktok: 700     # PRIOR: 6-8 proposer sessions at the 100 Z1-ktok per-session cap
    Z3-hr: 5         # PRIOR: ~25 merges x 0.2 h; Z3 seat is TBD (ZONE_REGISTRY.md)
    CI-min: 2400     # PRIOR: ~60 pushes x ~40 CI-min across the path-filtered gate stack
  dependencies:
    - "REPOSITORY_COORDINATOR_POLICY.json (capacity.active_operator_queue = 4)"
    - "RESOURCE_UNITS.yaml (RAT-min constraint; demand_priors)"
    - "PRIORITY_QUEUE.md (Q-TEMPORAL-DISSOLUTION-01: no internal deadlines)"
    - "CLAUDE.md P19 (K <= 13 files per authored commit)"
  blocking_on:
    - "Q-Z3-EXECUTOR-ASSIGNMENT-BATCH-01 (or a narrower Z3 assignment for this plan; Decision D1)"

impact_prediction:
  resource_impact: 7
  areas_affected:
    - "Z-000 operations PR queue (36 open PRs)"
    - "96 z1-inbox candidates awaiting Z2 (only as decision-sheet batching; not cleared by this plan)"
    - "Per-repo agent surfaces in humanaios and lasting-light-ai (proposals only)"
  positive_outcomes:
    - "Queue reduced to the admitted capacity without any merge outside Z2 authority"
    - "RAT-min per cleared PR measured for the first time (replaces the demand prior)"
    - "Brier-scored disposition predictions become CAL-pt rows (recursive learning)"
    - "H-CAND-MULTI-AGENT-CASCADE-01 gets its first stratified data (same-lineage vs diverse review)"
    - "Three bounded domain agents (#747) drafted against the live framework, read-only"
  risk_factors:
    - "Agents pushing to existing PR branches could reset reviews; D2 settles the posture"
    - "Serial manifest lane makes the Manifest Steward a single point of delay"
    - "Decision sheets concentrate RAT-min into sittings; if Z2 cannot sit, nothing admits (by design)"
    - "Cross-repo lane could outrun #747's own sequencing (#749/#750 first); D9 gates it"

falsifier: |
  This plan is FALSE (and the orchestrator halts, files an IC candidate, and hands off) if:
  - F1: any agent-originated change reaches main without BOTH a Repository Coordinator
        ADMIT receipt AND a Z2 merge act (governance breach; halt immediately).
  - F2: at Phase 2 exit, the number of open PRs red on any check other than the admission
        gate has not fallen by at least 50% from the Phase 0 baseline. Cohort: 17 of the 33
        swept on 2026-10-12 (15 mechanical failures plus #781 and #805 on the no-op guard);
        target <= 8. A PR leaves the cohort by going green or by being closed on a D5 row.
  - F3: measured RAT-min per cleared PR exceeds 2x the registry_candidate demand prior
        (12 -> 24 RAT-min) over the first 10 cleared PRs.
  - F4: the Manifest Steward's serial lane produces a second tools-manifest.yaml conflict
        on a PR the steward has already rebased once (single-writer model is wrong).
  - F5: the Brier score of per-PR disposition pins exceeds 0.25 over >= 20 resolved pins.
  Measurement: the queue pin ledger of §4a (scored with tools/nf_ledger_v0_1.py score),
  ledgers/RESOURCE_LEDGER.jsonl SPEND rows (unit RAT-min), the QUEUE_MAP record refreshed
  at each phase exit, and receipt_reconciliation.py at close.

evidence:
  - "z1-inbox/2026-10-14/QUEUE_MAP_2026-10-14.md (PR triage table, issue program map, conflict map)"
  - ".github/workflows/repository-admission-gate.yml (ADMIT via workflow_dispatch or /coordinator admit)"
  - "REPOSITORY_COORDINATOR_POLICY.json (capacity 4; invariants)"
  - "PR #815 body: ADMIT dispatched for #812 and #815 on 2026-10-14; gate read PASS/ACTIVE afterward"
  - "Issue #328 (96 candidates awaiting Z2); Issue #747 (three domain agents and their four blockers)"
  - "registry-candidates/blocks/H-CAND-MULTI-AGENT-CASCADE-01.md"
  - "RESOURCE_UNITS.yaml demand_priors.classes.registry_candidate (12 RAT-min)"

z2_decision:
  status: "awaiting_ratification"
  ratified_at: null
  ratification_hash: null
  z2_notes: ""

related_candidates:
  - "Q-Z3-EXECUTOR-ASSIGNMENT-BATCH-01"
  - "Q-TIER-ASSIGNMENT-BATCH-01"
  - "Q-EXTERNAL-JESTER-01"
  - "Q-AGENT-CHECKIN-CALIBRATION-01"
  - "Q-ISSUE-TRIAGE-CONVENTION-01 (PR #831; this plan does not define labels)"
external_constraint: null
links:
  - name: "Issue #747 (three domain agents)"
    url: "https://github.com/humanaios-ui/operations/issues/747"
  - name: "Issue #328 (Z2 decision queue)"
    url: "https://github.com/humanaios-ui/operations/issues/328"
```

---

## 1. What the queue looks like (Phase 0 result)

Observed via the GitHub API on 2026-10-12 (33 PRs, full triage) and re-listed on 2026-10-14 (36 PRs: #815 merged; #822, #825, #827, #831 opened). Full table in the evidence record.

| Fact | Count | Consequence for the plan |
|:--|--:|:--|
| Open PRs | 36 | Nine times the admitted capacity of 4 |
| Admission-gate check failed, everything else green | 12 | Read each run's `gate.json` before assigning a cause: FAIL (needs ADMIT), PASS with a 403 on the receipt step (needs a workflow-permission fix, not ADMIT), or non-draft routing |
| Red on Builder / Tool manifest / quality / P19 / validate | 15 (of 33 swept) | Mechanical lane work, one PR at a time |
| Touch `tools-manifest.yaml` + `TOOLS_MANIFEST.md` | 10 | Every pair conflicts; must be serialized |
| Competing GNER lineages for the same files | 3 | One survives; Z2 picks (D3) |
| Superseded by a newer open PR | 4 (#724, #781, #798 or #814, #805) | Close, not fix (D5) |
| Self-declared parked / HOLD / DO NOT MERGE | 9 | Left alone unless Z2 lifts the hold |
| z1-inbox candidates awaiting Z2 | 96 | Only batched into decision sheets here |

Three structural facts drive the design:

1. **The admission-gate check is red on 32 of 33 PRs, for more than one reason.** Where the coordinator's decision is FAIL for want of an ADMIT record, only a Z2 act clears it (`workflow_dispatch` ADMIT, or `/coordinator admit` on an `ADMISSION_REQUESTED` issue), so those requests go on a decision sheet with evidence pre-digested. Where the decision was PASS and the job died publishing its receipt comment (HTTP 403 "Resource not accessible by integration", verified on #740's run 38058777239), an ADMIT changes nothing; that is a workflow-permission defect on `pull_request_target` runs for bot-authored PRs and belongs to the CI Mechanic as a proposed patch, never to the sheet. A1's next sweep records the decision in each run's `gate.json` per PR so the two are never conflated again.
2. **`capacity.active_operator_queue = 4`** is a ratified invariant ("AUTONOMOUS_PRODUCTION_CANNOT_OUTRUN_REVIEW_CAPACITY"). Agents work upstream of admission so the admitted set never exceeds four; the stress test is on the upstream lanes, not on the cap.
3. **RAT-min is the binding constraint** (RESOURCE_UNITS.yaml). Every design choice below minimizes Z2 minutes per cleared PR and records the minutes actually spent.

## 2. Agent roster

Each agent is a bounded role with one output and one authority effect. All are Z1 unless stated. None merges, admits, ratifies, or closes anything.

| ID | Agent | Zone | Input | Output | Writes to |
|:--|:--|:--|:--|:--|:--|
| A0 | Orchestrator (this session's role) | Z1 | pinned SHA, QUEUE_MAP | dispatches, WIP enforcement, decision sheets, handoff | z1-inbox only |
| A1 | Cartographer | Z1 read-only | GitHub API | QUEUE_MAP refresh (PR table, issue clusters, conflict map) | QUEUE_MAP record |
| A2 | Supersession and Lineage Analyst | Z1 | QUEUE_MAP + the Repository Coordinator index comment (its per-PR guidance: CLOSE_PRESERVE, REEXAMINE, REBASE_RETEST) | per-PR recommendation: keep / supersede / stack / close, with file-overlap evidence; never recomputes what the coordinator already reports | decision-sheet rows |
| A3 | Manifest Steward (single writer) | Z1 | serial order from D7 | one rebased PR at a time; tool-ID allocation; `TOOLS_MANIFEST.md` regen | the PR branch in lane |
| A4 | CI Mechanic | Z1 | one red PR | fixes for Builder / Tool manifest / quality / P19 / validate; `verify_pr_readiness.sh` green; K <= 13 files per commit | the PR branch (per D2) |
| A5 | Review Responder | Z1 | open review threads | blocking findings fixed; optional ones answered in one line and resolved; reviewer re-requested | PR threads |
| A6 | Decision-Sheet Compiler | Z1 -> Z2 | A2, A3, A4 outputs | one sheet per sitting: rows with evidence, RAT-min prior, ACCEPT/EDIT/REJECT boxes, exact ADMIT inputs | z1-inbox |
| A7 | Calibration Recorder | Z1 | every disposition | one disposition pin per PR in the queue pin ledger (§4a) before the PR is touched; per-check pins in `ci_predictions/pr.json` per head; resolution on outcome; Brier via `nf_ledger_v0_1.py score`; RAT-min SPEND rows; B.6 reconciliation; findings scan | ledgers, ci_predictions, z1-inbox |
| A8 | Jester (adversarial, provider-diverse) | Z1 external check | each batch before its sheet | independent blocking findings, stratified by lineage (Claude vs Copilot vs CodeRabbit vs Codex) | PR threads, A7 table |
| A9 | Domain-Agent Scaffolder | Z1 cross-repo | #747, #749–#752 | three bounded agent manifests (Human Resource Agent, Operations Agent, Translation/Research Agent), read-only, E1 deterministic tests | proposals; draft PRs only per D9 |
| Z2 | Night | Z2 | decision sheets | ADMIT dispatches, closes, ratification hashes, merge acts | state branch, REGISTERED.md |
| Z3 | TBD (D1) | Z3 | Z2 hash + ADMIT receipt | merges in serial order; VERDICT rows | main |

Isolation rule (from #747 §7, applied here): each agent has one identity string in its commit trailer or thread signature, a scoped file set, and the P19 commit cap. A3 is the only agent allowed to touch the manifest pair. A4 and A5 never run on the same PR at the same time.

## 3. Lanes

PRs are assigned to one lane from the QUEUE_MAP; a PR moves lanes only on a decision-sheet row.

- **Lane M, maintenance.** Two cohorts the coordinator routes differently. (1) Dependabot #740, #741, #742 (disjoint files), then #743 before #744 (adjacent lines in `tools/requirements.txt`): `REPOSITORY_COORDINATOR_POLICY.json` grants maintenance standing by author to `dependabot[bot]` only, so these need no working-set ADMIT, just Z2 merge acts; all were owner-approved at sweep. (2) #817 (SMAG consolidation, `github-actions[bot]`, supersedes #724) holds no maintenance standing and goes through ordinary admission; at sweep only the admission job had run on its head, so A1 verifies its exact-head checks before it reaches a sheet row. No agent code work in either cohort.
- **Lane G, green except admission.** #802, #809, #814 (or #798, per D4), #812 (ADMIT already recorded; HOLD is Z2's to lift, D10), #768 (empty template body: EDIT row, author fills the body or A2 recommends close). These need a sheet row each, then Z3.
- **Lane R, red on mechanical checks.** #594, #606, #627, #630, #761, #763, #772, #777, #778, #785, #790, #819, and the four new PRs #822, #825, #827, #831 once swept. A4 takes them in the serial order of D7 where they touch the manifest, otherwise in ascending PR number. A5 follows A4 on each.
- **Lane L, lineage decision pending.** #767, #770, #771 (stacked), #772, #778, #768: frozen until D3. A2 prepares the comparison; nothing is pushed.
- **Lane P, parked by their own text.** #597 (DO NOT MERGE), #781 (close in favor of #785, D5), #805 (planning-only, convert to issue #804 or close, D5), #719 (awaiting admission record; body claims 5 files, PR has 15 including a workflow, so A5 asks for a corrected `molt_tier_claimed` first).

WIP limits: at most 4 admitted PRs at any time (policy); at most 1 PR in the Manifest Steward lane; at most 2 PRs under A4 concurrently; A8 reviews a batch, never a single PR, so lineage stratification has a sample.

## 4. Phases and exit predicates

No phase has a date. Each exits on a resource-state predicate, per Q-TEMPORAL-DISSOLUTION-01.

| Phase | Work | Exit predicate |
|:--|:--|:--|
| P0 Cartography | A1 sweep; A2 supersession pass; A7 baseline pins | Every open PR has a lane, a conflict class, and a disposition pin in the queue pin ledger (§4a); every open issue sits in a program cluster. **Partly met on 2026-10-14:** lanes, conflict classes and clusters are in the evidence record; **no disposition pins exist yet**, so P0 stays open until the pin spec covers every open PR. |
| P1 Decision Sheet 1 | A6 compiles the rows in §5; Z2 sits | Every D-row carries ACCEPT/EDIT/REJECT; the first admission batch (at most 4 minus the PRs already ACTIVE, which were #606 and #812 on 2026-10-14) carries ADMIT receipts; RAT-min SPEND rows recorded. |
| P2 Mechanical lanes | A3 serial manifest lane; A4 and A5 on Lane R; A8 batch review | Every Lane R PR is green except admission or carries one standing-down comment naming the failing check and why; no PR has an unanswered blocking thread. |
| P3 Landing | Rolling batches: admit at most (4 minus ACTIVE) PRs in D7 order, Z3 lands them, slots are released, the next batch is admitted; a batch is never made ready together if it would trip CAPACITY_CONTENTION; A7 resolves pins as each PR reaches a terminal state | Open PR count <= 4 + Lane P; every merge has an ADMIT receipt and a Z2 hash or merge act traceable in the ledger. |
| P4 Domain agents | A9 drafts the three manifests; proposes #749/#750 measurement contracts first per #747 | Three manifests exist as proposals with E1 deterministic tests passing locally; no write path crosses a repo boundary. |
| P5 Learning close | A7 Brier over >= 20 pins; B.6 reconciliation; findings scan; A8 lineage table | Brier reported with n; zero open RECEIPT-GAP rows; F/IC/H candidate blocks filed; H-CAND-MULTI-AGENT-CASCADE-01 stratified table populated. |

Phases P2, P4 run in parallel once P1 exits. P5 can start its reconciliation at every P3 merge.

### 4a. Disposition pins: the F5 and P5 instrument

`ci_predictions/pr.json` and `ci-predict-pin` score GitHub check conclusions per head; they cannot score whether a PR merges or closes. The ratified CAL-pt unit (RESOURCE_UNITS.yaml) is instrumented by `tools/nf_ledger_v0_1.py score` over resolved pins, so A7 uses that tool, not a new one:

- **Spec.** One pin-spec JSON per sweep at `ledgers/queue_pins_<sweep-date>.json`, one token per open PR: `token_id` `QP-<sweep-date>-PR<n>`, claim "PR <n> is MERGED at P3 exit", `p` from A2's recommendation, the QUEUE_MAP commit sha and the PR head sha as `evidence_locator`.
- **Ledger.** Built with `nf_ledger_v0_1.py build <spec> ledgers/QUEUE_PINS_LEDGER.jsonl`, a separate hash-chained file. Nothing is appended to `ledgers/NF_LEDGER.jsonl`; whether queue pins ever enter the canonical ledger is a Z2 ratification.
- **Outcome rule.** `resolve <token> YES --source <merge sha>` when the PR merges; `resolve <token> NO --source <close event or P3-exit QUEUE_MAP sha>` when it closes or is still open at P3 exit. A pin without a tree-read source is refused by the tool. No date windows: resolution is triggered by terminal state or by the P3 exit predicate.
- **Score.** `nf_ledger_v0_1.py score ledgers/QUEUE_PINS_LEDGER.jsonl` gives the Brier score F5 reads, with n reported; F5 is undefined below n = 20 and says so.
- **Baseline.** P0 is not met until the spec covers every open PR, so the first pins are filed before any D-row is executed, not after.

## 5. Decision Sheet 1 (the ten Z2 rows)

RAT-min column is the demand prior for the row's class; A7 replaces it with measured minutes.

| Row | Decision Z2 is asked for | Z1 recommendation | RAT-min |
|:--|:--|:--|--:|
| D1 | Z3 executor for this plan: ratify Q-Z3-EXECUTOR-ASSIGNMENT-BATCH-01, or a narrower assignment scoped to Z-000 for the duration | Narrow Z-000 assignment to the Claude machine identity (already authorized by Q-Z2-DUAL-AUTHORITY-GOVERNANCE-01), with Z2 merge act still required | 12 |
| D2 | May agents push fixes to existing `humanaios-ui` PR branches, or must they open stacked fix-PRs? | Push to branch, merge-commit only, never force-push; one identity trailer per agent | 5 |
| D3 | GNER lineage: A (#767 -> #770 -> #771 stack), B (#772 + #778 to main), or C (#768) | A, because #770/#771 are explicitly stacked on #767 and #778 says it depends on #767; close B and C with a comment pointing at A | 12 |
| D4 | SCVC witness fix: keep #814 (segment-based check, supersedes #798) or #798 (narrow regex) | #814; close #798 with a pointer | 5 |
| D5 | Supersession closes: #724 -> #817, #781 -> #785, #805 -> issue #804 | Close all three | 5 |
| D6 | Lane M routing: merge dependabot #740–#744 (maintenance standing, no ADMIT needed, #743 before #744); route #817 through ordinary admission once its head checks are verified green | Confirm the split; merge the five; defer #817's ADMIT to the batch after A1's verification | 8 |
| D7 | Manifest serial order | #812 (ratified, admitted) -> #809 -> #763 -> #767 -> #594 -> #627 -> #630 -> #719 -> lineage winner's remainder -> new PRs | 8 |
| D8 | Primary stress-test metric | RAT-min per cleared PR (constraint unit), with Brier and lineage-stratified findings as secondary | 5 |
| D9 | Cross-repo lane: draft PRs in humanaios and lasting-light-ai now, or proposals in operations until #749/#750 are ratified | Proposals in operations first; sibling-repo draft PRs only after #749/#750 rows are signed | 8 |
| D10 | Holds: #597 stays parked; is #812's HOLD lifted now that #815 is merged? | #597 parked; #812 HOLD is Z2's call, no recommendation | 5 |

| D11 | Convert prose-draft PRs to API drafts: #597, #767, #770, #771, #777, #790, #812, #814, #819, #825, #827 all say DRAFT/HOLD in their bodies but are `draft=false`; the gate routes API drafts to WORKBENCH (PASS) and out of ADMISSION_REVIEW | Convert them; it makes the gate measure what the authors already claim, and it is reversible with "ready for review" | 5 |

Sum of priors: 78 RAT-min, one sitting.

## 5a. Observations from this PR's own gate run (2026-10-14)

Filed after the first CI run on the PR carrying this candidate; they correct §1 and §2.

- **Drafts pass the admission gate by design.** The Repository Coordinator receipt for this draft PR read `PASS`, lane `WORKBENCH`, reason "draft work is isolated from the operator queue" (receipt `RCD-AB60C8AD94173F77`, state `09479a1b`). So the 32-of-33 red count in §1 conflates three populations: PRs awaiting a Z2 ADMIT, PRs whose gate decision was PASS but whose receipt-publishing step failed with HTTP 403 (verified on #740), and PRs that merely never set the GitHub draft flag. The coordinator index on the same run counted 29 in ADMISSION_REVIEW, 5 MAINTENANCE, 1 ACTIVE (#606, #812 listed), 1 WORKBENCH (this PR), 1 CONTROL_PLANE. D11 is the cheap correction.
- **The coordinator already does Lane M and part of A2.** Its index routes dependabot by cohort (MAINTENANCE 5) and prints technical guidance per PR, including `CLOSE_PRESERVE` for #781 and #805 (zero files) and `REBASE_RETEST` for #606 and #812. A2 consumes that comment; it does not rebuild it (per #747's "map, do not duplicate").
- **Per-check predictions are a separate pin from disposition pins.** `ci-predict-pin` refused the inherited `ci_predictions/pr.json` as a status receipt (`INHERITED`, not a failure), which is why this PR now carries a per-head check prediction. That pipeline scores check conclusions only, so the per-PR merge/close predictions F5 needs live in the separate instrument of §4a.

## 6. How the five purposes are served

- **Stress testing.** The lanes, the WIP cap, and the single-writer manifest lane are the system under test. F2, F3, F4 are the stress falsifiers.
- **Personal learning.** Every sheet row shows its evidence and the prior; A7 reports measured minutes against the prior so Z2 sees her own throughput as data.
- **Integration into repository agents.** A9 instantiates #747's three bounded agents as manifests in each repo's existing agent surface (operations: `.claude/skills`, `.codex/AGENTS.md`; lasting-light-ai: `.claude/skills`, `.agents/skills`; humanaios: has `.github/workflows` only, so a manifest and skill directory would be new). Read-only per #747's vertical slice.
- **Demonstration of the framework.** Every artifact is a ritual artifact: §A pin, candidate block, falsifier, resource vector, decision sheet, receipt reconciliation, handoff. Nothing is bespoke.
- **Recursive learning.** Pins resolve into CAL-pt rows; measured RAT-min replaces priors; lineage-stratified findings feed H-CAND-MULTI-AGENT-CASCADE-01; the findings scan at P5 feeds REGISTERED.md.

## 7. What this candidate does not do

- Does not define issue labels (PR #831, Q-ISSUE-TRIAGE-CONVENTION-01, covers that; this plan consumes whatever Z2 ratifies there).
- Does not clear the 96 awaiting-Z2 candidates; it only reuses the decision-sheet form for them later if Z2 wants.
- Does not touch constants, gates, workflows, REGISTERED.md, or CODEOWNERS.
- Does not claim any PR will merge: `smag_p` pins are predictions, scored at P5.

## 8. Open questions for Z2 (answers change the work)

The decision sheet above is the formal version. In plain terms:

1. Who is Z3 for this clearance: the Claude machine identity under a narrow Z-000 assignment, or Night merging by hand? (D1)
2. May agents push to your existing PR branches? (D2)
3. Which GNER lineage survives? (D3)
4. Is the primary metric RAT-min per PR, throughput under the cap of 4, or lineage-correlated error? (D8)
5. Should the three domain-agent manifests go to the sibling repos as draft PRs now, or stay as proposals in operations until #749/#750 are signed? (D9)
6. Are Copilot and CodeRabbit the intended "other lineages" for the Jester, or should Codex (`.codex/` exists) and Grok (HARC Trial 003) be included?
7. Should the 96 inbox candidates be folded into later decision sheets, or kept out of this plan entirely?
8. Is the Resource Miner trio (#822, #825, #827) in scope for Lane R, or is that program being driven elsewhere?

Until answered, the plan proceeds under the recommendations in §5 only for work that needs no Z2 act: cartography refreshes, supersession analysis, pins, and decision-sheet compilation.

---

_Generated with [Claude Code](https://claude.com/claude-code)_
