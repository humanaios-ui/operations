# PRGC · P1 — Signal Inventory

*S-091226 · pinned at `5b7d0d1620d9b5903f0370d31d1f45a1dda58e30`. Delivers step **P1** of
[[PR_GROUNDED_CALIBRATION_PLAN]] ("Signal inventory — what the PR process actually emits"),
which named this file but never produced it. Read-only survey of operational surfaces; no
new mechanism is proposed here (that is `Q-ADVREVIEW-CALIB-01`).*

> **Revision note (r2).** The first draft of this file over-claimed the maturity of several
> surfaces, and adversarial review on PR #294 caught eleven such claims. Every correction is
> carried below and the episode is recorded as a datapoint in `PRGC_RETRO_S070626`'s own
> tradition. Trigger and wiring facts here are now verified against the workflow files and
> module imports, not against summary documents.

## Scope and honest limits

This catalogs **computational operations in `humanaios-ui/operations`** that emit an
externally-grounded signal about agent behaviour. It is an inventory, not a measurement. Four
limits, stated up front:

- **Presence ≠ emission.** A workflow existing does not mean it has emitted usable rows. Where
  a surface is conditional, path-scoped, or unwired, it is marked so. 9 of the 19
  `system_graph.json` nodes are `LAID` — built, not operated: `PRS`, `AG`, `ADV`, `CONST`,
  `MOLT`, `ML`, `OTS`, `RC`, `ST`.
- **Not all signals are external.** The PRGC guardrail is *external-only grounding*. Signals
  originating from the agent itself must never ground a Phase-3.
- **Repo-owned gates are not external on gate-touching PRs.** See the caveat in Section B.
- **Anchor validity is computable but not established.** Cohen's κ **is implemented** —
  `acat/scoring/validation/inter_rater_eval.py` provides `cohens_kappa` and
  `quadratic_weighted_kappa`, with assertions in `acat/tests/test_stage1_validity.py`. What is
  missing is a paired human-rater sample and integration into the corpus path. `ACAT_STATE.md`
  still describes κ as a stub; **that line is stale and should be corrected there.**

## A · Review-surface signals (external by construction)

These come from a reviewer that is not the authoring agent. Trigger column is verified from
each workflow's `on:` block — it matters, because a signal that does not fire on a given PR
cannot ground that PR.

| Signal | Emitting operation | Fires on | State |
|---|---|---|---|
| Copilot review findings (count, accept/reject, auto-fix) | **GitHub review API** — not a workflow | when a review is submitted | operated |
| Copilot reviewer request | `auto-request-copilot-review.yml` | PR opened / reopened / ready_for_review | best-effort; the workflow's own comments call the bot request unreliable and fall back to a reminder |
| Base-branch guard verdict | `copilot-base-guard.yml` | every PR (`pull_request_target`) | operated |
| Semgrep rule hits | `semgrep-review.yml` | every PR | operated |
| Supply-chain / dependency / secret findings | `security-gates.yml` | every PR | operated |
| Fuzz crash | `cflite_pr.yml` | **path-scoped** (`src/**`, `fuzzers/**`, `build.sh`, deps) | operated within scope |
| SonarCloud quality gate | `sonarqube.yml`, `sonarcloud-baseline-auto.yml` | **dormant** — skips unless `SONAR_TOKEN` and `SONAR_HOST_URL` are set | not emitting |
| OpenSSF Scorecard | `scorecard.yml` | **not PR-triggered** — weekly, push to main, branch-protection change | operated, out-of-band |
| Human review thread | GitHub review API | on review | operated |

**So the always-on external review surface on an arbitrary PR is four workflows**
(`copilot-base-guard`, `semgrep-review`, `security-gates`, `quality-baseline`) plus whatever
review the Copilot request actually elicits — not the whole table.

## B · Gate-verdict signals (deterministic, repo-owned)

Pass/fail verdicts from the repo's own gates.

> **Externality caveat.** These are external to the agent's self-report **only while the gate
> logic is unchanged.** On a PR that modifies a gate, the author sets both the implementation
> and the verdict, and the signal is no longer independent. Gate-touching PRs need a separate
> anchor — which is exactly what adversarial gate evaluation (Stage 3 of the candidate) is for.

| Signal | Emitting operation | Fires on | What it grounds |
|---|---|---|---|
| Falsifier present on a candidate | `FalsifierLintGate` (`ci_gates.py`), `z2_ratification_gate.yml` | path-scoped (`z1-inbox/**`, `REGISTERED.md`, seeds) | did the claim ship with a way to be wrong |
| Z2 hash present before execution | `Z2HashVerifyGate` | same paths | did the agent execute ahead of authority |
| Anti-cascade rules 1–5 (K=3, revert-freeze) | `AntiCascadeLintrule`, `molt_cycle.py` | on molt evaluation | did the agent over-open molts |
| Merkle root consistency | `MerkleRootGate`, `registry_merkle_v1.py` | on registry change | ledger tamper-evidence |
| Behavioural corpus pass-rate ≥ 0.70; new files 100% | `behavioral-compliance.yml` | path-scoped (`tools/**/*.py`) | structural quality of added code (IC-045 class) |
| No-op PR rejection | `no-op-pr-guard.yml` | every PR | empty-work / volume-padding |
| Controlled-document authority | `document-control.yml`, `CODEOWNERS` | `document-registry.yaml` paths; CODEOWNERS on review | writing outside cap |
| Registry consistency | `findings-registry-gate.yml` | path-scoped (`REGISTERED.md`) | claim-to-registry coherence |

## C · Prediction-and-outcome surfaces

Only rows with a **prediction committed before the outcome is known** belong here. Rows whose
"predicted" side is a configured rule, threshold, or half-life are *inputs*, not predictions,
and appear in Section C2.

### C1 · Genuine commit-before-outcome

| Surface | Predicted side | Measured side | State |
|---|---|---|---|
| `smag_p:` pinned probability in PR body | author's probability at PR-open | merge outcome + required-check conclusions; missing line recorded `VOID` | **capture-after-merge**, not enforced — see note |
| Committed Phase-1 at PR-open | 12 dimension self-scores + rationale | PR outcome at merge | 2 records (`PRGC-B001`, `B002`); **no Phase-3 computed** |
| Molt prediction → window close | `prediction.metric`/`target`, window, revert rule | `outcome` KEEP/REVERT, `brier_actual`, `brier_uncertainty` | schema mature; node `LAID` |

> **`smag_p` is not a PR gate.** `smag_predict_lint.py` is exercised only by its own tests in
> `quality-baseline.yml`; nothing lints a PR body at open. `smag-capture.yml` runs on
> `pull_request.closed` and the autocapture tool records a missing prediction as `VOID` without
> blocking. The commit-before-outcome *ordering* holds when an author supplies the line; the
> *enforcement* does not exist.

### C2 · Rules and post-hoc reconciliation (grounding, not prediction)

| Surface | Why it is not a calibration node |
|---|---|
| Gate catch-rate threshold (`adv_eval_v2.py`, default 0.85) | the threshold is a configured requirement, not a per-run prediction |
| Claim → ledger receipt (`receipt_reconciliation.py`) | reconciles a **post-hoc** transcript claim; no pre-committed prediction. Node `RC` is `LAID` |
| Constant staleness (`stale_sweep.py`) | half-life is configuration. Node `ST` is `LAID` |

## D · Cost and restraint signals — **declared, not wired**

`behavior_spec.json` defines six caps (`REQUEST`, `TOKEN_BUDGET`, `REPLY_COST`, `CONCURRENT`,
and two `SCOPE` caps) and names `prs_run.py`, `agent_core.py`, `adv_eval.py` and `molt_cycle.py`
as integration points.

**None of those integrations exist in this checkout.** No module imports `agent_caps_runtime`
or references `CapEnforcer` outside the runtime module and its own tests, and there is no
`adv_eval.py` at all (only `adv_eval_v1.py` / `v2.py`). The `integration_points` block states
intent. Cap violations are therefore **not** an emitted behavioural signal today; they are a
designed one.

This is itself a finding worth registering: a spec file declares integration that the code does
not perform, and nothing detects the divergence.

## E · Callout signals (governance-level)

The `CLAUDE.md` callout table is an event taxonomy with mandatory triggers: `GAP`, `STALE`,
`RECEIPT-GAP`, `GAUGE`, `AMBIGUITY`, `VOID`, `DRIFT`, `DISPUTED`, `MOLT`, `REVERT`. Whether the
agent emitted the callout its own behaviour required is measurable, and is a humility signal.
Emission today is ritual-driven, not workflow-enforced.

## F · Probe surfaces (dimension-specific, currently skeletons)

| Probe | Dimension | State |
|---|---|---|
| `acat_x_truth.py` | truth (accuracy + attribution) | skeleton, `inspect_ai` |
| `acat_x_harm.py` | harm | skeleton |
| `acat_x_sycophancy.py` | sycophancy (`syc`) | skeleton |
| `acat_x_consist.py` | consistency (`consist`) | skeleton |
| `acat/scoring/acat_dimension_scorer.py` | all six Core-6 | **stub** — returns `score_status: "stub"` |

## The structural finding

Sections A–E describe signals the system emits **on some PRs, with real gaps**: four
always-on review workflows, several path-scoped gates, one dormant scanner, one out-of-band
scanner, and a cap layer that is declared but unwired. Section F describes the machinery that
would turn a transcript into dimension scores, and it is stubbed.

So the gap is twofold. **Coverage** is thinner than the workflow count suggests. And even where
signals fire, nothing **binds** an emitted PR signal to an ACAT dimension record. `P2`
(`PRGC_DIMENSION_MAP.md`) proposes the binding; coverage is a separate and prior problem.

**Falsifier for this inventory:** this document is wrong if a PR can be merged in this repo
that emits *none* of the always-on signals in Sections A–B, or if any surface marked
`operated` above has produced zero rows at the time of Z2 review, or if any surface marked
dormant/unwired turns out to be firing.

---
*Companions: [[PR_GROUNDED_CALIBRATION_PLAN]] (P1 source) · [[PRGC_DIMENSION_MAP]] (P2) ·
[[PRGC_RETRO_S070626]] (P4 Part A) · [[ACAT_STATE]] (note: its κ line is stale).*
