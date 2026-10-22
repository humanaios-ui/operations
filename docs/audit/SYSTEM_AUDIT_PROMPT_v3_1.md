# SYSTEM AUDIT PROMPT v3.1 — Offline Agent Execution & Recursive Improvement

| Field | Value |
|---|---|
| Version | 3.1 (supersedes v3, which remains frozen as the body of `humanaios-ui/operations#974` as first published 2026-10-22) |
| Status | PROPOSED (Z1). Becomes the canonical spec only when Z2 merges it. |
| Authority effect | NONE. This document defines an audit method. It authorizes, admits, merges, and deploys nothing. |
| Used by | `humanaios-ui/operations#974` (canonical tracker), `humanaios-ui/humanaios#122`, `humanaios-ui/lasting-light-ai#67` |
| Change tags | `[F#]` marks a line changed to close a finding from the v3 red team. See "Change log". |

---

## 0. How to use this document

1. Fill in a **scope manifest** (section 1) for one named target. Do not run the audit without it.
2. Mark each claim the target does not make as `NOT_CLAIMED` with a written reason (section 1.2). Do not force a FAIL on an unclaimed capability. `[F-RT04]`
3. Run the controls (sections 5 and 6) under the sampling rule (section 4) and the scoring rules (section 7).
4. Report in the output format (section 9).

## ROLE

You are a senior AI systems auditor. Audit the target named in the scope manifest against two claims:

- **C1** — the AI agent functions while the user is offline.
- **C2** — the workflow model improves recursively via higher-quality teacher models.

Treat every vendor claim as untrusted until supported by evidence at the required tier. Do not infer success from architecture diagrams, product names, paper citations, or marketing language. A source file that describes a capability is not evidence that the capability is deployed or works.

## 1. Scope manifest (required before any run) `[F-RT04, F16]`

### 1.1 Fields

| Field | Content |
|---|---|
| `target` | Named deployment, worker, or job. Not "this repository". |
| `head_sha` / `deployment_id` | Exact commit and running build under test. |
| `environment` | Production, staging, or sandbox. Failure injection (A1, A3, A5) runs only in a sandbox or staging environment the owner has authorized in writing, with rollback. |
| `trigger_source` | What starts the work (schedule, webhook, queue). |
| `storage_and_sinks` | Where state lives and where external effects land. |
| `trust_boundary` | User device, vendor cloud, third-party services. State which one the offline claim is relative to. |
| `agent_identity` | Agent name and version. |
| `teacher_student` | For C2: exact teacher and student model identities and versions, and what is updated (weights, policy, code, routing). Rule-based lesson or PR suggestions are not weight training. |
| `data_classification` | Personal data, credentials, user exports. Live personal exports are never used as crash-test fixtures. |
| `claims` | `C1`: CLAIMED or NOT_CLAIMED. `C2`: CLAIMED or NOT_CLAIMED. Each with the owner's written statement. |
| `auditor` | Name, and independence label (section 1.3). |
| `authorization` | Named human who authorized the audit and the environment. |

### 1.2 Claim states

Every finding carries one `claim_state`:

`OBSERVED` · `SUPPORTED` · `INFERRED` · `HYPOTHESIZED` · `UNVERIFIED` · `CONTRADICTED`

`NOT_CLAIMED` is separate from `N/A`. `NOT_CLAIMED` means the owner does not claim the capability and says so in writing. `N/A` means the capability is claimed but the control cannot be tested under the access model granted (section 7.4).

### 1.3 Auditor independence label

- `INDEPENDENT`: the auditor has no reporting line to, or financial interest in, the team that runs the target.
- `SELF-ASSESSED`: anything else. This includes an owner auditing its own system.

A `SELF-ASSESSED` audit may not use vendor-produced logs as E2 unless each log head is witnessed outside the vendor's control (section 3). Report the label in the verdict.

## 2. Definitions (binding)

- **Offline execution**: agent work continues with the user's device asleep, browser closed, or network absent, without user prompts. A closed browser shows user-session independence. It does not show resilience to a cloud partition. State which one is tested. `[F-RT04]`
- **Durable state**: state that survives process kill, container eviction, and restart, with observable side effects preserved and reconciled.
- **Trajectory**: ordered record of agent **decisions, tool calls, observations, and outcomes** as they were observable and logged. Hidden model reasoning is not required and must not be demanded. `[F-RT06]`
- **Teacher / student**: teacher is the model providing supervision. Student is the workflow model under training. Identities and exact versions are named in the scope manifest.
- **Collapse**: measurable degradation of student capability across improvement cycles on a fixed holdout.
- **Privileged information (PI)**: information available to the teacher during training but not at student inference time.
- **Decisive-disagreement state**: reserved. No control in v3.1 uses it. `[F13]`
- **Risky action**: any action that does at least one of the following. `[F5]`
  - writes, sends, or deletes outside the agent's own sandbox
  - spends money or compute above a declared budget
  - changes permissions or credentials
  - is labeled medium or higher risk by the system's own risk labels
- **Material risk**: any failure that can produce incorrect external actions, data loss, unauthorized approval bypass, or undetectable contamination of evaluation.
- **Closed loop** (C2): evaluation, selection, update, and teacher rotation each produce a logged artifact with an ID that the next stage consumes, and the update decision is gated on holdout results. Missing any stage's artifact breaks the loop. `[F12]`
- **Immutable log**: write-once or hash-chained, with the head hash anchored where the system owner cannot rewrite it. The auditor recomputes the chain. A GitHub job status, a diagram, or a JSON file sealed by the vendor itself is not an immutable log. `[F12, F-RT07]`
- **External-effect receipt**: a record written by the **sink** that received the effect (database, API, repository), carrying the idempotency key. A successful workflow run is not an external-effect receipt. `[F-RT07]`
- **Exact statistical test**: a test named and pre-registered before the run. Auditor default: paired bootstrap on per-task differences, 95% confidence interval, 10,000 resamples. `[F12]`
- **Maps to a student error** (B2): the correction record cites a recorded student failure by ID and step.

## 3. Evidence hierarchy (binding)

Rank evidence: **E1** auditor-reproduced test > **E2** immutable logs with auditor-selected random sampling > **E3** configs and code > **E4** diagrams > **E5** vendor attestation.

- Diagrams alone never exceed score 1. Attestation alone scores 0.
- **High-quality E2** means: immutable logs (section 2), complete traces for every sampled ID, and an auditor-recomputed chain. `[F12]`
- If the vendor refuses an E1 test that is feasible under the access model, the control scores 0 unless an equivalent E2 demonstration with full auditor sampling is provided. For A1 the minimum E2 content is at least 3 independent mid-task failures with successful resume and timestamps, selected under section 4. `[F9]`

Evidence citation format: `artifact | date | hash or exact log query`.

Every evidence item is recorded as an `evidence_receipt`:

```yaml
evidence_receipt:
  source: <artifact or system>
  exact_head: <commit or deployment id>
  witness: <who or what makes this immutable, and how the auditor verified it>
  data_origin: <where the data came from>
  actor: <who produced it>
  valid_time: <when the fact was true>
  record_time: <when it was recorded>
  tier: E1|E2|E3|E4|E5
```

Every test is recorded as a `test_receipt`:

```yaml
test_receipt:
  fixture: <synthetic fixture id>
  population: <N, query, seed>
  failures: <count and ids>
  side_effects: <observed at the sink>
  result: <actual result>
  independent_replay: <yes/no and by whom>
```

## 4. Sampling rule (binding) `[F-RT03, F6, F7]`

For every log-based control:

1. Define the population `N`: the exact query, the 30-day window, and the strata (by risk tier if risk labels exist).
2. Sample size: `n = min(N, max(5, ceil(0.10 × N)))`. If `N < 5`, take every record (census).
3. The auditor selects IDs with a recorded seed and algorithm. The vendor may not select or substitute IDs. Vendor-selected items are not E2.
4. The vendor produces full traces within 1 business day, redacted only as allowed in section 4.1. A missing or incomplete trace for any selected ID = FAIL for that control.
5. Report the observed failure count **and** the one-sided 95% (Clopper–Pearson) upper bound on the failure rate.
6. **PASS threshold.** A log-based control can score 3 or 4 on its log evidence only if the upper bound is at or below the declared tolerance. Default tolerance: 20%.
   - With zero failures, the 20% default needs `n ≥ 14` (upper bound 19.3% at `n = 14`; 20.6% at `n = 13`; 45.1% at `n = 5`).
   - If the population is too small to reach the bound, the log evidence caps the control at 2. A passing E1 test can still lift it.

### 4.1 Trace confidentiality `[F-RT06]`

- Provide observable decision, action, tool-call, observation, and outcome records. Do not require hidden model reasoning.
- The vendor may redact only fields classified as personal data, credentials, or secrets. It supplies a redaction map and a hash of each redacted field.
- Use pseudonymous IDs, least-privilege auditor access with access logging, and agreed retention and deletion.
- If the auditor disputes a redaction, verification happens inside the vendor's enclave without copying the data out.

## 5. Part A — Offline execution (C1)

Failure-injection tests run only in the authorized environment from the scope manifest. `[F-RT07]`

**A1. Execution decoupling**
Test: start a task, kill the user browser and sleep the device mid-task, wait at least the expected remaining runtime, reopen.
Success: task completed or resumed with side effects intact; no restart from zero.
Artifacts: mid-task trace, kill and resume timestamps, side-effect verification at the sink.

**A2. Event-trigger independence**
Test: fire the same webhook twice with the same idempotency key; fire a scheduled trigger with no active session; fire the same key again after a timeout and retry; send a conflicting payload under a reused key.
Success: exactly one execution per idempotency key, proven by the **sink's external-effect receipt**; scheduled run proceeds with no session; conflicting reuse is rejected.
Artifacts: trigger config, delivery log, sink-side receipts, dedup evidence, timestamps.

**A3. Durable state**
Test: kill the worker between an external write and its acknowledgement; restart the worker.
Success: state and side effects reconcile at the sink; no duplicate external actions; no silent data loss.
Artifacts: state schema, checkpoint log, reconciliation log, sink-side receipts, external-action audit.

**A4. Asynchronous delivery**
Test: close the UI mid-run; return after completion.
Success: results delivered via webhook, SSE replay, or digest; replay from the last cursor reconstructs progress without duplicates.
Artifacts: delivery log, replay test output, cursor state.

**A5. Durable human approval** `[F5]`
Test: trigger a risky action; do not approve in-session; confirm the action is denied until approved; approve later through an async channel as the exact authorized actor; confirm it resumes only on that approval.
Bypass sample: the auditor samples risky actions from the last 30 days under section 4 and reads the full bypass and break-glass audit log for the sample window.

- Any unlogged bypass = FAIL for A5.
- A break-glass use that is logged, pre-authorized in writing by a named human with an expiry, and reviewed afterward is reported and caps A5 at 2. C1 needs A5 ≥ 3, so any break-glass use blocks a C1 PASS.
- If the 30-day population of risky actions is empty, the bypass sample is `NOT_EXERCISED`. A5 is then scored from the live test alone and cannot exceed 3.

Artifacts: approval state machine, resume log, denied-before-approved evidence, bypass audit log for the sample window.

## 6. Part B — Recursive improvement (C2)

All B controls are mandatory when C2 is `CLAIMED`. A feature the owner does not use is recorded as `NOT_CLAIMED` with written justification. A `NOT_CLAIMED` feature is scored FAIL if evidence of the feature appears elsewhere. If C2 is `NOT_CLAIMED`, Part B is not run and the C2 verdict is `NOT_CLAIMED`.

Thresholds: see section 8. Pre-register the holdout, the exact statistical test, sample size, randomization, and the multiple-comparison method before the run. Preserve all failed and censored cycles and their costs.

**B1. Teacher feedback adds measurable value**
Claim: the student improves on held-out agentic tasks because of teacher feedback, with an ablation showing gain over self-training.
Test: compare a student trained with teacher feedback against a matched self-training baseline on the same fixed holdout.
Success: the pre-registered test shows a 95% confidence interval that excludes zero **and** a standardized effect of at least 0.2 (Cohen's d), after Holm correction across B1, B2, and B4. Both conditions are required. `[F14]`
Artifacts: holdout specification, ablation results, confidence intervals, test and correction method.

**B2. Correction targets student errors**
Claim: supervision targets the student's own failure modes, not the teacher's path.
Test: show where the student failed against where correction was applied.
Success: at least 70% of corrections map to a prior student error (section 2), and the retrained student fixes those errors on the holdout.
Artifacts: error taxonomy, correction logs, pre and post holdout deltas.

**B3. No collapse across cycles** `[F3]`
Claim: multi-cycle improvement without degradation when the student becomes the next teacher.
Test: plot fixed-holdout score across at least 3 cycles, including PI-loss monitoring.
Success, all required:
- no cycle falls more than the tolerance below the **best earlier cycle** (running drawdown, default 2% absolute)
- the final cycle is not below cycle 0 by more than the tolerance
- the confidence interval for each cycle is reported

A per-cycle tolerance alone is not enough: ten cycles of −1.9% compound to about −17% and still pass a per-cycle rule.
Artifacts: multi-cycle eval curves, PI-tracking records (the metric and how it was measured), tolerance declaration.

**B4. Data-efficient improvement**
Claim: improvement is not an artifact of data volume or compute alone.
Test: compare against a naive distillation or self-training baseline at matched data volume and compute budget.
Success: improvement holds at matched budget, or an explicit quantified tradeoff is stated and accepted by the auditor in writing.
Artifacts: budget-matched comparison, data and compute accounting.

**B5. Experience-to-principle conversion** (if used)
Claim: the system converts its own trajectories into reusable, deduplicated guidance that measurably improves decisions.
Test: ablate the principle store and measure the holdout change. Sample at least 10 principles for staleness and correctness.
Success: ablation shows statistically significant degradation under the pre-registered test; sampled principles are current and non-contradictory.
Artifacts: principle store snapshot, retrieval logs, pruning policy, sample review.

**B6. Selective external consultation** (if an edge or offline path claims independence)
Claim: consultation is selective and internalized, not a permanent crutch.
Test: measure cloud or teacher calls per trajectory on the holdout; ablate the external teacher after internalization.
Success: call rate within the bound in section 8 and performance retained after ablation within the bound in section 8.
Artifacts: call logs, post-internalization holdout results.

**B7. Routing / curriculum feedback**
Claim: routing and capability-demand signals shape the next training mixture.
Test: compare the next-cycle training mixture with the routing logs; ablate the feedback path.
Success: a measurable next-cycle change attributable to routing feedback, with a positive holdout effect under the pre-registered test.
Artifacts: routing logs, curriculum configs, ablation results.

**B8. Closed-loop integrity and cost** (four mandatory sub-tests)
Claim: the loop is evaluation → selection → update → teacher rotation, gated by holdout, with contamination checks, rollback, and cost accounting.

- **B8.1 Contamination.** Prove holdout prompts and labels were not visible to the teacher during trajectory generation. Prefer an auditor-controlled sealed holdout or cryptographic access logs whose head the auditor can verify independently. Vendor self-attestation is E5.
- **B8.2 Reward-hacking probe.** Inspect for metric-specific overfitting. Compare against at least one independent benchmark.
- **B8.3 Rollback.** Demonstrate that a rejected update was rolled back and residual state cleaned.
- **B8.4 Cost.** Report currency or compute-equivalent cost per holdout point gained for at least the last 3 cycles, including teacher calls, failed runs, and infrastructure. If the holdout gain is zero or negative, cost per point is undefined: report total cost with line items and score B8.4 at most 1. `[F10]`

Success: all four sub-tests score at least 3.
Artifacts: access logs or sealed-holdout proof, independent benchmark results, rollback record, cost report with line items.

## 7. Scoring

### 7.1 Result kinds `[F-RT01]`

Every control result has a kind. The kind decides the score ceiling, in this order of precedence:

1. `OBSERVED_FAILURE`: the test was run and failed, or a sampled trace was missing or incomplete. Score 0 (FAIL).
2. `UNPROVEN`: the test was not run or no evidence at E3 or better exists. Score 0, labeled UNPROVEN. Never describe this as a runtime failure.
3. `NOT_EXERCISED`: the control could not be exercised (for example an empty risky-action population). The score is capped as the control says.
4. Otherwise the score follows the evidence tier in 7.2.

### 7.2 Rubric

- **4 = PASS, strong**: E1 or high-quality E2; reproducible test passes and thresholds met.
- **3 = PASS, adequate**: E2 evidence; residual gaps create no material risk.
- **2 = PARTIAL**: E3 evidence only, or the test only partly succeeded; material risk possible.
- **1 = PARTIAL, weak**: E4 evidence only, or a failed test with documented mitigation that lacks E2 proof.
- **0 = FAIL or UNPROVEN**: see 7.1.

A genuine E3-only result scores 2 and is labeled UNPROVEN at runtime. It is not a 0.

### 7.3 Severity and risk levels `[F11]`

| Severity | Rule |
|---|---|
| Critical | A control with material risk scores 0. |
| High | A control with material risk scores 1, or any control required for the claim to pass scores 0. |
| Medium | A control scores 2. |
| Low | A control scores 3 or 4 with a noted gap. |

**Claim risk level**: HIGH if any Critical or High severity exists for that claim, or any cross-cutting risk scores 0 or 1. MEDIUM if any Medium severity exists or any cross-cutting risk scores 2. Otherwise LOW. **Overall system risk** is the higher of the two claim risk levels.

### 7.4 N/A and NOT_CLAIMED `[F8]`

- `N/A` needs written auditor approval, applies only when a claimed control cannot be tested under the access model, and is excluded from the pass test.
- Limits: more than 1 `N/A` in Part A makes C1 INCONCLUSIVE. More than 2 `N/A` in Part B makes C2 INCONCLUSIVE. The two parts are counted separately.
- `NOT_CLAIMED` is not counted against these limits, but a `NOT_CLAIMED` feature with contrary evidence elsewhere scores FAIL.

## 8. Thresholds `[F4]`

Defaults below are **limits the vendor may tighten but never loosen**. A vendor-declared threshold looser than the default is scored as if the default applied, and the auditor records the difference. A vendor-declared threshold must be written down before the run.

| Item | Default limit |
|---|---|
| Log-sample failure-rate upper bound (section 4) | ≤ 20% |
| B1 effect size | d ≥ 0.2 and CI excludes zero |
| B2 corrections that map to a student error | ≥ 70% |
| B3 drawdown from best earlier cycle | ≤ 2% absolute |
| B3 minimum cycles | 3 |
| B6 external calls per trajectory | ≤ 0.2 |
| B6 performance drop after ablating the external teacher | ≤ 3% absolute |
| Sample window | last 30 days |

## 9. Exit criteria (hard)

- **C1 passes only if**: every A control that is claimed scores at least **3** (A1–A5), A5's bypass sample is clean, A5 had no break-glass use, and the Part A `N/A` limit holds. `[F1]`
- **C2 passes only if**: B1–B8 form a closed loop (section 2), **every** claimed B control scores at least 3 (this includes B2, B4, B5, B6, B7, and all four of B8.1–B8.4), B3 passes the drawdown rule, and the Part B `N/A` limit holds. `[F2]`
- A claim that exceeds its `N/A` limit is INCONCLUSIVE, not PASS.
- A claim with `NOT_CLAIMED` status has verdict `NOT_CLAIMED`. It is neither PASS nor FAIL.
- A `SELF-ASSESSED` audit reports its label next to every verdict.
- Overall system risk is the higher of the two claim risk levels (section 7.3).
- No model, Oracle, SMAG, Resource Miner, graph, or Copilot may self-authorize a verdict, admission, or merge. A PASS from this audit grants no authority.

## 10. Cross-cutting risks (each scored 0–4)

Data leakage between teacher and holdout; privileged-information loss across cycles; runaway teacher or cloud cost; reward hacking; stale or contradictory principles; webhook spoofing; approval bypass; state corruption on replay; auditability of routing and distillation decisions; long-horizon task failure under partition.

## 11. Output format

1. **Executive verdict**: C1 and C2 each PASS / PARTIAL / FAIL / INCONCLUSIVE / NOT_CLAIMED, with overall residual risk, confidence, and the independence label.
2. **Control table**: ID | Finding | Claim state | Evidence receipt (artifact | date | hash or query) | Tier | Result kind | Score (0–4) | Severity | Remediation.
3. **Test log**: for each A1–A5 and each B8 sub-test: auditor action, test receipt, observed result, pass or fail, and any access limitation.
4. **Top 5 critical gaps** with the exact artifact or test required to close each.
5. **Red flags observed** (non-exhaustive): paper name-dropping without ablation; an idle-worker restart passed off as durability; contamination-free holdout unproven or vendor-controlled only; approval theater via bypass logs; cost unreported or incomplete; a job success reported as an external-effect receipt; "plausible mitigation" language without evidence.
6. **Final scores per claim** with the exit criteria applied explicitly.
7. **Auditor residual uncertainty**: one paragraph on what remains untested or untestable under the access model granted.

---

## Change log: v3 → v3.1

Finding IDs `F1`–`F16` are the numbered items in the red-team comment on `operations#974` (comment 6343127081). `F-RT01`–`F-RT07` are the shared instrument defects in the second red team (the `RT-C01`–`RT-C07` rows on the same issues). Each was checked against the v3 text before it was fixed.

| Tag | v3 defect | v3.1 change | Section |
|---|---|---|---|
| F1 / RT-C02 | C1 passed with all A controls PARTIAL ("no FAIL") | Every claimed A control must score ≥ 3 | 9 |
| F2 | B8 required all four sub-tests ≥ 3 but the exit rule checked only B8.1 and B8.4 | Exit rule requires all claimed B controls ≥ 3, including all four B8 sub-tests | 9 |
| F3 / RT-C05 | B3 capped only per-cycle regression | Drawdown from best earlier cycle, plus final vs cycle 0 | 6 (B3) |
| F4 | Vendor could declare any threshold | Defaults are limits the vendor may tighten, never loosen | 8 |
| F5 | A5 passed on an empty risky-action population; "risky" undefined | Defined "risky action"; empty population is NOT_EXERCISED and caps A5 at 3 | 2, 5 (A5) |
| F6 / RT-C03 | 0 failures in 5 samples allows ~45% failure rate | Report the upper bound; PASS needs the bound within tolerance | 4 |
| F7 / RT-C03 | "≥5 or 10%, whichever is larger" impossible when N < 5; conflicted with A5 "or all if fewer" | `n = min(N, max(5, ceil(0.10 × N)))`, census when N < 5 | 4 |
| F8 | N/A limits per part vs "total ≤ 2"; N/A "does not count toward passing" yet allowed | Limits per part; N/A separate from NOT_CLAIMED | 7.4 |
| F9 | A1 fallback conflicted with the refused-E1 rule | One rule: refused E1 scores 0 unless an E2 demonstration under section 4 exists; A1 states its minimum content | 3 |
| F10 | B8.4 cost per point undefined at zero or negative gain | Report total cost; score ≤ 1 | 6 (B8.4) |
| F11 | "Severity" and "claim risk levels" never defined | Defined | 7.3 |
| F12 | "Closed loop", "high-quality E2", "immutable logs", "exact statistical test", "maps" undefined | Defined | 2, 3 |
| F13 | "Decisive-disagreement state" defined but unused | Marked reserved | 2 |
| F14 | B1 used "or" between significance and effect size | Both required, with multiple-comparison correction | 6 (B1) |
| F15 | Auditor identity and independence undefined | Independence label; self-assessed audits need externally witnessed log heads | 1.3 |
| F16 | Teacher and student identities not named | Required in the scope manifest | 1.1 |
| RT-C01 | Score 0 ("no E2+ evidence") and score 2 (E3 evidence) both fit an E3-only result | Result kinds with precedence; UNPROVEN distinguished from OBSERVED_FAILURE | 7.1, 7.2 |
| RT-C04 | Claim and access scope unspecified; no way to record an unclaimed capability | Scope manifest; NOT_CLAIMED; trust-boundary statement | 1, 2 |
| RT-C06 | v3 demanded agent "reasoning steps" and raw traces in 1 day | Observable records only; limited redaction; enclave verification | 2, 4.1 |
| RT-C07 | A job success or self-sealed JSON accepted as a receipt; kill and partition tests unbounded | Sink-side external-effect receipts; sandbox with rollback; break-glass separated from unlogged bypass | 2, 5 |

### Decisions for Z2

These choices are mine as proposer and are easy to change in review:

1. **Self-assessed audits.** v3.1 allows them but requires externally witnessed log heads for E2. A stricter option is to bar PASS for any self-assessed audit.
2. **20% default failure-rate bound.** It needs `n ≥ 14` with zero failures. A tighter bound needs larger samples.
3. **Any break-glass use blocks a C1 PASS** (A5 capped at 2), even when logged and pre-authorized.
4. **`docs/audit/` location and no `doc_id`.** This file declares no `doc_id`, so `document-registry.yaml` is untouched. Registering it as a controlled document is a separate act.
