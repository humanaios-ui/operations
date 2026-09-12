# PRGC · P1 — Signal Inventory

*S-091226 · pinned at `5b7d0d1620d9b5903f0370d31d1f45a1dda58e30`. Delivers step **P1** of
[[PR_GROUNDED_CALIBRATION_PLAN]] ("Signal inventory — what the PR process actually emits"),
which named this file but never produced it. Read-only survey of operational surfaces; no
new mechanism is proposed here (that is `Q-ADVREVIEW-CALIB-01`).*

## Scope and honest limits

This catalogs **computational operations already running in `humanaios-ui/operations`** that
emit an externally-grounded signal about agent behaviour. It is an inventory, not a
measurement. Three limits, stated up front:

- **Presence ≠ emission.** A workflow existing does not mean it has emitted usable rows. Where
  a surface is stubbed or unexercised, it is marked so. 6 of the 19 `system_graph.json` nodes
  are `LAID` (built, not operated) and one dimension scorer is an explicit stub.
- **Not all signals are external.** The PRGC guardrail is *external-only grounding*. Signals
  that originate from the agent itself are marked `self` and must never ground a Phase-3.
- **No signal here is validated against a human rater.** Cohen's κ is stubbed
  (`ACAT_STATE.md`), so anchor validity is asserted by construction, not measured.

## A · Review-surface signals (external by construction)

These come from a reviewer that is not the authoring agent. They are the strongest anchors.

| Signal | Emitting operation | Kind | State |
|---|---|---|---|
| Copilot review findings (count, accept/reject, auto-fix) | `auto-request-copilot-review.yml` | external | operated |
| Base-branch guard verdict on Copilot PRs | `copilot-base-guard.yml` | external | operated |
| Semgrep rule hits on the diff | `semgrep-review.yml` | external | operated |
| SonarCloud quality gate + baseline delta | `sonarqube.yml`, `sonarcloud-baseline-auto.yml` | external | operated |
| Supply-chain / secret findings | `security-gates.yml`, `scorecard.yml` | external | operated |
| Fuzz crash on changed targets | `cflite_pr.yml` | external | operated |
| Human review thread (request-changes, resolve) | GitHub review API | external | operated |

## B · Gate-verdict signals (deterministic, repo-owned)

Pass/fail verdicts from the repo's own gates. External to the agent's self-report even though
the repo authored them, because the agent cannot alter the verdict without altering the gate
(which is itself a reviewable diff).

| Signal | Emitting operation | What it grounds |
|---|---|---|
| Falsifier present on a candidate | `FalsifierLintGate` (`ci_gates.py`), `z2_ratification_gate.yml` | did the claim ship with a way to be wrong |
| Z2 hash present before execution | `Z2HashVerifyGate` | did the agent execute ahead of authority |
| Anti-cascade rules 1–5 (K=3, revert-freeze) | `AntiCascadeLintrule`, `molt_cycle.py` | did the agent over-open molts |
| Merkle root consistency | `MerkleRootGate`, `registry_merkle_v1.py` | ledger tamper-evidence |
| Full-CI integration | `FullCIIntegrationGate`, `enforce_ci_gates()` | aggregate gate posture |
| Behavioural corpus pass-rate ≥ 0.70; new files 100% | `behavioral-compliance.yml` | structural quality of added code (IC-045 class) |
| No-op PR rejection | `no-op-pr-guard.yml` | empty-work / volume-padding |
| Controlled-document authority | `document-control.yml`, `CODEOWNERS` | writing outside cap |
| Registry consistency | `findings-registry-gate.yml`, `haios-corpus-integrity.yml` | claim-to-registry coherence |

## C · Prediction-and-outcome signals (already calibration-shaped)

These are the surfaces that already have the two-sided shape calibration needs — a committed
prediction and a later measured outcome. **This is the most important section of the
inventory: the substrate already exists.**

| Signal | Operation | Predicted side | Measured side |
|---|---|---|---|
| `smag_p:` pinned probability in PR body | `smag_predict_lint.py`, `smag_pr_autocapture_v1_0.py`, `smag-capture.yml` | probability the author pins at PR-open | merge outcome + required-check conclusions; missing prediction recorded as `VOID` |
| Molt prediction → window close | `molt_cycle.py`, `NF_LEDGER.jsonl` | `prediction.metric`/`target`, window, revert rule | `outcome` KEEP/REVERT, `brier_actual`, `brier_uncertainty` |
| Gate catch-rate under attack | `adv_eval_v2.py` | `catch_rate_threshold` (default 0.85) | CAUGHT / MISSED per attack; `NO_GATE` excluded by design |
| Committed Phase-1 at PR-open | `acat/research/prgc_phase1/*.json` | 12 dimension self-scores + rationale | PR outcome at merge (not yet computed) |
| Claim → ledger receipt | `receipt_reconciliation.py` | claims of type VERDICT/CYCLE/MOLT/MEASUREMENT/COMPLETION | MATCHED or `RECEIPT-GAP` (IC-031 mitigation) |
| Constant staleness | `stale_sweep.py` | per-constant half-life | `STALE` callout |

Two of these are live and mechanical (`smag_p`, receipt reconciliation). Three are `LAID` in
`system_graph.json` — built, not yet operated (`PRS`, `ADV`, `MOLT`, `RC`, `ST`).

## D · Cost and restraint signals

From `behavior_spec.json`, enforced by `agent_caps_runtime.py` (`CapEnforcer`), with declared
integration points in `prs_run.py`, `agent_core.py`, `adv_eval.py`, `molt_cycle.py`.

| Cap | Type | Limit | Behavioural reading |
|---|---|---|---|
| `max_requests_per_hour` | REQUEST | 100/60min | activity restraint |
| `token_budget_per_session` | TOKEN_BUDGET | 100000 | cost restraint |
| `max_reply_tokens` | REPLY_COST | 4000 | verbosity restraint |
| `max_concurrent_tasks` | CONCURRENT | 3 | scope restraint |
| `scope_repositories` | SCOPE | 4 repos | boundary respect |
| `scope_decision_classes` | SCOPE | IC/F/H/MOLT | authority respect |

A cap violation blocks the operation and emits a `GAP` callout. That block is a behavioural
event with an external verdict, which is exactly the shape a calibration node needs.

## E · Callout signals (governance-level)

The `CLAUDE.md` callout table is already an event taxonomy with mandatory triggers: `GAP`,
`STALE`, `RECEIPT-GAP`, `GAUGE`, `AMBIGUITY`, `VOID`, `DRIFT`, `DISPUTED`, `MOLT`, `REVERT`.
Each has a defined route and a Z2 response. Whether the agent emitted the callout its own
behaviour required is itself measurable — and is a humility signal, not a truth signal.

## F · Probe surfaces (dimension-specific, currently skeletons)

| Probe | Dimension | State |
|---|---|---|
| `acat_x_truth.py` | truth (accuracy + attribution) | skeleton, `inspect_ai` |
| `acat_x_harm.py` | harm | skeleton |
| `acat_x_sycophancy.py` | sycophancy (`syc`) | skeleton |
| `acat_x_consist.py` | consistency (`consist`) | skeleton |
| `acat/scoring/acat_dimension_scorer.py` | all six Core-6 | **stub** — returns `score_status: "stub"` |

## The one structural finding

Sections A–E describe signals the system **already emits on every PR**. Section F describes the
machinery that would turn a transcript into dimension scores, and it is the part that does not
work. So the gap is not sensing — it is **binding**: no operation currently attaches an emitted
PR signal to an ACAT dimension record. `P2` (`PRGC_DIMENSION_MAP.md`) proposes that binding.

**Falsifier for this inventory:** this document is wrong if a PR can be merged in this repo
that emits *none* of the Section A–C signals, or if any signal marked `operated` above has
produced zero rows at the time of Z2 review. Either finding invalidates the claim that the
substrate is already present.

---
*Companions: [[PR_GROUNDED_CALIBRATION_PLAN]] (P1 source) · [[PRGC_DIMENSION_MAP]] (P2) ·
[[PRGC_RETRO_S070626]] (P4 Part A) · [[ACAT_STATE]] (what is stubbed).*
