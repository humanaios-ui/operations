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
    RAT-min: 225     # PRIOR: ~80 for Decision Sheet 1 + ~3 per ADMIT x ~25 PRs + ~3 per merge act x ~25 (Z2 merges by hand, D1)
    Z1-ktok: 700     # PRIOR: 6-8 proposer sessions at the 100 Z1-ktok per-session cap
    Z3-hr: 0         # Z2 performs the merge acts herself (D1, recorded 2026-10-14); no Z3 seat is drawn on
    CI-min: 2400     # PRIOR: ~60 pushes x ~40 CI-min across the path-filtered gate stack
  dependencies:
    - "REPOSITORY_COORDINATOR_POLICY.json (capacity.active_operator_queue = 4)"
    - "RESOURCE_UNITS.yaml (RAT-min constraint; demand_priors)"
    - "PRIORITY_QUEUE.md (Q-TEMPORAL-DISSOLUTION-01: no internal deadlines)"
    - "CLAUDE.md P19 (K <= 13 files per authored commit)"
  blocking_on: []    # D1 resolved in-session (Z2 merges by hand); Q-Z3-EXECUTOR-ASSIGNMENT-BATCH-01 no longer gates this plan

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
  z2_notes: |
    2026-10-14, in-session, human-attested, unsigned (see §9): Z2 answered D1, D2, D8, D9
    and open questions 6-8, and asked for an ROI matrix before deciding D3 (§5b). These are
    recorded as Z2 statements made in conversation with the filing session; they bind by
    the same convention as the IC-065 "confirmed live" precedent, not by hash. The hash
    on this block is still owed.

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
| Open GNER PRs for files main already carries | 6 | Main has E0, E1, E2 tools, tests, docs and manifest rows via merged #779; #770 and #771 are ancestors of main; see the matrix in §5b |
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
| A8 | Jester (adversarial, provider-diverse) | Z1 external check | each batch before its sheet | Copilot and CodeRabbit are the other lineages (Z2, 2026-10-14); a second Claude reader forms the same-lineage pair; findings stratified per §4b | PR threads, A7 table |
| A9 | Domain-Agent Scaffolder | Z1 cross-repo | #747, #749–#752 | three bounded agent manifests (Human Resource Agent, Operations Agent, Translation/Research Agent), read-only, E1 deterministic tests | proposals; draft PRs only per D9 |
| Z2 | Night | Z2 | decision sheets | ADMIT dispatches, closes, ratification hashes, merge acts | state branch, REGISTERED.md |
| Z3 | Night, by hand (D1, recorded 2026-10-14) | Z2 acting as merger | Z2 hash + ADMIT receipt | merge acts in serial order; A7 records the RAT-min each one costs | main |

Isolation rule (from #747 §7, applied here): each agent has one identity string in its commit trailer or thread signature, a scoped file set, and the P19 commit cap. A3 is the only agent allowed to touch the manifest pair. A4 and A5 never run on the same PR at the same time.

## 3. Lanes

PRs are assigned to one lane from the QUEUE_MAP; a PR moves lanes only on a decision-sheet row.

- **Lane M, maintenance.** Two cohorts the coordinator routes differently. (1) Dependabot #740, #741, #742 (disjoint files), then #743 before #744 (adjacent lines in `tools/requirements.txt`): `REPOSITORY_COORDINATOR_POLICY.json` grants maintenance standing by author to `dependabot[bot]` only, so these need no working-set ADMIT, just Z2 merge acts; all were owner-approved at sweep. (2) #817 (SMAG consolidation, `github-actions[bot]`, supersedes #724) holds no maintenance standing and goes through ordinary admission; at sweep only the admission job had run on its head, so A1 verifies its exact-head checks before it reaches a sheet row. No agent code work in either cohort.
- **Lane G, green except admission.** #802, #809, #814 (or #798, per D4), #812 (ADMIT already recorded; HOLD is Z2's to lift, D10), #768 (empty template body: EDIT row, author fills the body or A2 recommends close). These need a sheet row each, then Z3.
- **Lane R, red on mechanical checks.** #594, #606, #627, #630, #761, #763, #777, #785, #790, #819, the Resource Miner trio #822, #825, #827 (in scope per Z2, 2026-10-14) and #831 once swept. A4 takes them in the serial order of D7 where they touch the manifest, otherwise in ascending PR number. A5 follows A4 on each. Agents push fixes onto the open PR branches (D2, recorded 2026-10-14): merge commits only, never force-push, one identity trailer per agent.
- **Lane L, GNER.** #767, #770, #771, #772, #778, #768: the matrix in §5b replaces the lineage question. Nothing is pushed here until D3 is signed against that matrix.
- **Lane P, parked by their own text.** #597 (DO NOT MERGE), #781 (close in favor of #785, D5), #805 (planning-only, convert to issue #804 or close, D5), #719 (awaiting admission record; body claims 5 files, PR has 15 including a workflow, so A5 asks for a corrected `molt_tier_claimed` first).

WIP limits: at most 4 admitted PRs at any time (policy); at most 1 PR in the Manifest Steward lane; at most 2 PRs under A4 concurrently; A8 reviews a batch, never a single PR, so lineage stratification has a sample.

## 4. Phases and exit predicates

No phase has a date. Each exits on a resource-state predicate, per Q-TEMPORAL-DISSOLUTION-01.

| Phase | Work | Exit predicate |
|:--|:--|:--|
| P0 Cartography | A1 sweep; A2 supersession pass; A7 baseline pins | Every open PR has a lane, a conflict class, and a disposition pin in the queue pin ledger (§4a); every open issue sits in a program cluster. **Partly met on 2026-10-14:** lanes, conflict classes and clusters are in the evidence record; **no disposition pins exist yet**, so P0 stays open until the pin spec covers every open PR. |
| P1 Decision Sheet 1 | A6 compiles the rows in §5; Z2 sits | Every D-row carries ACCEPT/EDIT/REJECT; the first admission batch (at most 4 minus the PRs already ACTIVE, which were #606 and #812 on 2026-10-14) carries ADMIT receipts; RAT-min SPEND rows recorded. |
| P2 Mechanical lanes | A3 serial manifest lane; A4 and A5 on Lane R; A8 batch review | Every Lane R PR is green except admission or carries one standing-down comment naming the failing check and why; no PR has an unanswered blocking thread. |
| P3 Landing | Rolling batches: admit at most (4 minus ACTIVE) PRs in D7 order, Z3 lands them, slots are released, the next batch is admitted; a batch is never made ready together if it would trip CAPACITY_CONTENTION; A7 resolves pins as each PR reaches a terminal state | Open PR count <= 4 + Lane P; every ordinary-lane merge has an ADMIT receipt, every maintenance-standing Lane M merge has a current PASS / MAINTENANCE receipt for the exact PR head, and every merge has a Z2 hash or merge act traceable in the ledger. |
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

### 4b. Lineage-correlated error: the primary metric (Z2, 2026-10-14)

H-CAND-MULTI-AGENT-CASCADE-01 predicts that reviewers sharing a training lineage miss the same things, so a same-lineage pair catches less than independence would predict. The queue gives a natural test bed: every batch is reviewed by Claude agents (A4, A5, a second Claude reader in A8), by Copilot, and by CodeRabbit, on the same heads.

- **Unit of observation.** One confirmed finding: a review finding that a later commit fixed with a CI state change, or that Z2 ruled valid. Unconfirmed findings are not counted against anyone.
- **Lineages.** Claude (two independent Claude readers per batch, run without seeing each other's output), Copilot, CodeRabbit. Copilot and CodeRabbit are the other lineages by Z2's decision; Codex and Grok are out of scope for this plan.
- **Per-lineage marginals.** For each lineage L, miss(L) = share of confirmed findings in the batch that L did not report.
- **Pair statistic.** For each pair, observed joint-miss rate versus the independence prediction miss(L1) × miss(L2). The same-lineage pair is Claude-reader-1 with Claude-reader-2; the cross-lineage pairs are Claude with Copilot and Claude with CodeRabbit.
- **Falsifier F6 (of the null).** Over at least 20 confirmed findings across at least 4 batches, if the same-lineage joint-miss rate exceeds its independence prediction by more than 10 percentage points while the cross-lineage pairs do not, the cascade hypothesis is supported and the plan's same-lineage lanes (A4 then A5) must add a cross-lineage reader before any sheet row. If every pair is within 10 points of independence, the null stands for this queue and the hypothesis block records the negative result.
- **Recording.** A7 keeps `audits/lineage_findings_<sweep-date>.jsonl`: one row per finding with batch, head sha, lineage(s) that reported it, confirmation source. The schema is the `marshal_dispatch_runs_v1` lineage field the hypothesis block already asks for, applied to review rather than dispatch.
- **Secondary metrics** stay as filed: RAT-min per cleared PR (F3) and disposition Brier (F5).

## 5. Decision Sheet 1 (the twelve Z2 rows)

RAT-min column is the demand prior for the row's class; A7 replaces it with measured minutes.

| Row | Decision Z2 is asked for | Z1 recommendation | RAT-min |
|:--|:--|:--|--:|
| D1 | Z3 executor for this plan | **Decided 2026-10-14 (in-session): Z2 merges by hand.** No machine Z3 assignment; merge acts are costed in RAT-min | 12 |
| D2 | May agents push fixes to existing `humanaios-ui` PR branches? | **Decided 2026-10-14: yes.** Merge commits only, never force-push; one identity trailer per agent | 5 |
| D3 | GNER: which of #767, #770, #771, #772, #778, #768 survive | **Z2 asked for an ROI matrix (2026-10-14); it is §5b.** Z1 recommends option D there: close four as merged or superseded, keep #768 as the carrier for the human-objective experiment, decide the independent-witness implementation under D12 | 12 |
| D4 | SCVC witness fix: keep #814 (segment-based check, supersedes #798) or #798 (narrow regex) | #814; close #798 with a pointer | 5 |
| D5 | Supersession closes: #724 -> #817, #781 -> #785, #805 -> issue #804 | Close all three | 5 |
| D6 | Lane M routing: merge dependabot #740–#744 (maintenance standing, no ADMIT needed, #743 before #744); route #817 through ordinary admission once its head checks are verified green | Confirm the split; first repair receipt publication (the HTTP 403 on `pull_request_target` runs for bot-authored PRs, §5a) and re-run the gate on each exact head; verify a current `PASS / MAINTENANCE` receipt before each merge and defer any PR that lacks one; defer #817's ADMIT to the batch after A1's verification | 8 |
| D7 | Manifest serial order | #812 (ratified, admitted) -> #809 -> #763 -> #767 -> #594 -> #627 -> #630 -> #719 -> lineage winner's remainder -> new PRs | 8 |
| D8 | Primary stress-test metric | **Decided 2026-10-14: lineage-correlated error** (H-CAND-MULTI-AGENT-CASCADE-01), measured per §4b; RAT-min per cleared PR and Brier are secondary | 5 |
| D9 | Cross-repo lane: sibling-repo draft PRs now, or operations proposals until #749/#750 are signed | **Decided 2026-10-14: operations proposals until #749/#750 are signed**, per #747's own sequencing | 8 |
| D10 | Holds: #597 stays parked; is #812's HOLD lifted now that #815 is merged? | #597 parked; #812 HOLD is Z2's call, no recommendation | 5 |
| D11 | Convert prose-draft PRs to API drafts: #597, #777, #790, #812, #814, #819, #825, #827 say DRAFT/HOLD in their bodies but are `draft=false` (the GNER PRs drop out under §5b); the gate routes API drafts to WORKBENCH (PASS) and out of ADMISSION_REVIEW | Convert them; it makes the gate measure what the authors already claim, and it is reversible with "ready for review" | 5 |
| D12 | Independent execution witness: two implementations are open, `tools/independent_execution_witness_v0_1.py` inside #772 and the `tools/iew/` package with workflow and negative controls in #777 (IEW-001) | Keep #777 as the IEW lane; drop #772's copy with its close; A2 diffs the two first so nothing #777 lacks is lost | 8 |

Sum of priors: 86 RAT-min; four rows already decided in-session (D1, D2, D8, D9), eight (D3–D7, D10–D12) still open.

## 5b. GNER return-on-investment matrix (requested by Z2, 2026-10-14)

**Fact base, measured 2026-10-14 against main `3bf3b21`** (`git merge-base --is-ancestor`, `git diff --numstat` per file; manifest and prediction files excluded):

| PR | Remaining delta against main | CI at sweep | Review debt | Unique content not on main |
|:--|:--|:--|:--|:--|
| #770 (E1) | **None: the branch is an ancestor of main** (landed through #779's merge chain) | red (quality, Builder, Tool manifest) | Copilot 4 | none |
| #771 (E2) | **None: ancestor of main** | red (Builder, quality, Tool manifest) | Copilot 2 | none |
| #767 (E0) | `tools/gner_notification_e0.py` is an **older** version (main's has `TOOL_CATEGORY = "diagnostic_tool"` and a bool smoke test; the PR's has the superseded `analysis_tool` and dict variant); 3 stale lines in the principle-compliance exemption; docs and tests identical to main | red (Tool manifest, Molt tier advisory) | Copilot 4 | none |
| #778 (E1 Builder) | `tools/gner_verify_e1.py` is an **older** smoke-test variant (main's reconcile fixtures are fuller); all six `.z1-control` tools, docs, tests and E0 identical to main | red (Molt tier, Verify Z2 Ratification, P19, quality) | Copilot 5 | none |
| #772 (E1 baseline + E0 parser) | older E0 (40+/75−); duplicate test under `tools/tests/` | red (quality, P19, Molt tier, Verify Z2 Ratification) | Copilot 7 | `experiments/human_objective_e1.py` + fixture + README + test (issue #760); `tools/independent_execution_witness_v0_1.py` + test; `z1-inbox/2026-10-09/HANDOFF.md` |
| #768 (human objective pilot) | none of its four files exist on main | green except admission | Copilot 3 | the same four `human_objective_e1` files as #772, nothing else; body is an unfilled template |

So the "three lineages" framing was wrong by the time it was written: main already carries GNER E0, E1 and E2 with tests, docs and manifest rows. What is left to land is the human-objective E1 experiment (#760) and one independent-witness implementation.

**Options.** Costs are non-commensurable vectors (RESOURCE_UNITS.yaml); priors, not measurements. Benefit is counted in EVID-row candidates landed (the experiment and its fixture are evidence-bearing; superseded tool copies are not) and in issues unblocked.

| Option | What lands | RAT-min (Z2 acts) | Z1-ktok (to green) | CI-min | Manifest conflicts created | Benefit |
|:--|:--|--:|--:|--:|--:|:--|
| A: land the stack #767 → #770 → #771 | nothing new; three merges of content main has, with two of them already ancestors | 3 ADMIT + 3 merge ≈ 18 | ≈ 60 to re-green #767 against main | ≈ 240 | 1 (#767 vs main's manifest) | 0 EVID-row; #766 closes on paperwork that #779 already did |
| B: land #772 + #778 | the experiment and the IEW file, plus two regressions of tools main already improved | 2 ADMIT + 2 merge ≈ 12 | ≈ 120 (re-green two red PRs, drop the stale E0/E1 copies) | ≈ 320 | 2 | 2 EVID-row candidates, minus the regression risk on E0/E1 |
| C: land #768 alone | the experiment, four files | 1 EDIT (body) + 1 ADMIT + 1 merge ≈ 10 | ≈ 15 (fill the body; already green) | ≈ 40 | 0 | 1 EVID-row candidate (#760 experiment); the IEW tool is left to #777 |
| D (recommended): C plus closes, IEW to #777 | #768; close #770, #771 (merged), #767, #778 (superseded); A2 diffs #772's IEW file against #777's package, carries any missing behaviour into #777, then #772 is closed | 5 closes ≈ 10 + C's 10 ≈ 20 | ≈ 40 | ≈ 40 | 0 | 1 EVID-row candidate now, the IEW decision isolated in D12, five PRs out of the queue |

Density under the PRIORITY_QUEUE.md formula (benefit ÷ cost[RAT-min]): A ≈ 0, B ≈ 0.17, C ≈ 0.10, D ≈ 0.05 on benefit alone, but D also removes five PRs from ADMISSION_REVIEW and zero manifest conflicts, which the formula's "work unblocked" term credits to D (every Lane R PR behind the manifest lane). D is the recommendation. The one thing D must not lose is any behaviour in #772's witness file that #777 lacks, hence D12.

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
- Does not clear the 96 awaiting-Z2 candidates in Decision Sheet 1. Z2 placed them in scope for later sheets (2026-10-14): A6 compiles them in sheets of 10–12 rows, ordered by the tier and density ranking of Q-TIER-ASSIGNMENT-BATCH-01 once that is signed, each row with the candidate's own falsifier status from `Z1_INBOX_INDEX.md`.
- Does not touch constants, gates, workflows, REGISTERED.md, or CODEOWNERS.
- Does not claim any PR will merge: `smag_p` pins are predictions, scored at P5.

## 8. Questions put to Z2 on filing, and their status

1. Who is Z3 for this clearance? **Answered: Night merges by hand** (D1).
2. May agents push to existing PR branches? **Answered: yes** (D2).
3. Which GNER lineage survives? **Z2 asked for an ROI matrix**; §5b; D3 stays open against it.
4. Primary metric? **Answered: lineage-correlated error** (D8, §4b).
5. Sibling-repo draft PRs now, or operations proposals first? **Answered: operations proposals until #749/#750 are signed** (D9).
6. Jester lineages? **Answered: Copilot and CodeRabbit.**
7. The 96 inbox candidates? **Answered: in scope for later decision sheets** (§7).
8. The Resource Miner trio? **Answered: in scope** (Lane R).

Still open for the sheet: D3 (against §5b), D4, D5, D6, D7, D10, D11, D12.

## 9. Z2 responses recorded in-session (2026-10-14)

Recorded by the filing Z1 session from Z2's reply in conversation. Human-attested, unsigned: these bind by the convention the IC-065 "confirmed live" record set, and the ratification hash for this candidate is still owed. Z2 also stated she will merge PR #836 herself when the candidate is complete.

| Z2 statement (verbatim fragment) | Row | Effect in this document |
|:--|:--|:--|
| "i will merge PR when complete" | D1 | Z3 row in §2 is Night; Z3-hr cost 0; merge acts costed in RAT-min; `blocking_on` emptied |
| "agents may push fixes onto open existing" | D2 | Lane R text; A4/A5 push to PR branches, merge commits only |
| "ROI matrix for GNER" | D3 | §5b written; Lane L frozen until D3 is signed against it |
| "lineage-correlated error" | D8 | §4b written; F6 added as the primary falsifier; RAT-min and Brier secondary |
| "stay as operations proposals until #749/#750 are signed, per #747's own sequencing" | D9 | A9 output stays in operations; no sibling-repo PRs |
| "Copilot and CodeRabbit the intended other lineages for the adversarial reviewer" | Q6 | A8 row; §4b lineages fixed |
| "96 inbox candidates in scope for later decision sheets" | Q7 | §7 |
| "RM in scope" | Q8 | #822, #825, #827 in Lane R |

---

_Generated with [Claude Code](https://claude.com/claude-code)_
