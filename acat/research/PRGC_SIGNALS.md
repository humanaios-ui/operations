# PRGC · P1 — Signal Inventory

*S-091226 · pinned at `5b7d0d1620d9b5903f0370d31d1f45a1dda58e30`. Delivers step **P1** of
[[PR_GROUNDED_CALIBRATION_PLAN]] ("Signal inventory — what the PR process actually emits"),
which named this file but never produced it.*

> **Revision history.** r1 over-claimed eleven surfaces; adversarial review on PR #294 caught
> all eleven. r2 corrected them but still described workflow *triggers* as if they were
> *effective coverage*, and still credited a gate library that nothing invokes. r3 corrects that.
> **Every row below is verified against the workflow's `on:` block, its job-level `if:`, and the
> module's actual call sites** — not against summary documents, and not against a workflow's
> existence.

## Scope and honest limits

- **Presence ≠ emission ≠ coverage.** A workflow can exist, trigger, and still emit nothing: a
  job-level `if:` may skip it, a scanner may find nothing because no file of its type changed, or
  its output may never be read. All three are marked.
- **Not all signals are external.** Repo-owned scanners and gates are not independent reviewers.
- **Gate verdicts are not external on gate-touching PRs.** The author sets implementation and
  verdict both.
- **Anchor validity is computable but not established or integrated.** `cohens_kappa` and
  `quadratic_weighted_kappa` exist in `acat/scoring/validation/inter_rater_eval.py` with test
  assertions, but nothing calls them on persisted records: `validate_session_score()` returns
  `agreement: None`. What is missing is a paired human-rater sample **and** integration.
  `ACAT_STATE.md` calls κ a stub; that line is stale and should be corrected there.

## A · Review-surface signals

Split by **effective** coverage on an ordinary, non-draft PR from a non-`copilot/` branch.

### A1 · Independent external reviewer

| Signal | Emitter | Coverage |
|---|---|---|
| Copilot review findings | **GitHub review API** — not a workflow | only when a review is actually requested and returned |
| Human review thread | GitHub review API | on review |
| Copilot reviewer request | `auto-request-copilot-review.yml` | opened / reopened / ready_for_review; the workflow's own comments call the bot request unreliable, falling back to a reminder |

This is the only genuinely independent tier, and it is best-effort. **A PR can merge having
received no independent review at all.**

### A2 · Repo-owned scanners (external to the agent's self-report, not independent reviewers)

| Signal | Emitter | Effective coverage |
|---|---|---|
| Dependency / secret findings | `security-gates.yml` | **unconditional** on every PR |
| Repo quality checks | `quality-baseline.yml` | **unconditional** on every PR |
| Semgrep rule hits | `semgrep-review.yml` | non-draft PRs only (`if: draft == false`); produces findings only when scanned file types changed |
| Controlled-document validation | `document-control.yml` | any `**/*.md`, `document-registry.yaml`, `.doc-control/**` — **broader than the registry file alone** |
| Base-branch guard | `copilot-base-guard.yml` | **`copilot/*` head branches only** (`if: startsWith(github.head_ref, 'copilot/')`) — emits nothing for an ordinary PR |
| Fuzz crash | `cflite_pr.yml` | path-scoped (`src/**`, `fuzzers/**`, `build.sh`, deps) |
| SonarCloud | `sonarqube.yml` | **dormant** — skips without `SONAR_TOKEN` and `SONAR_HOST_URL` |
| OpenSSF Scorecard | `scorecard.yml` | **not PR-triggered** — weekly, push to main, branch-protection change |

**So the unconditional surface on an arbitrary PR is two workflows** (`security-gates`,
`quality-baseline`), plus `document-control` whenever markdown changes, plus Semgrep on
non-draft PRs touching scanned types. Neither unconditional workflow is an independent reviewer.

## B · Gate-verdict signals — **library, not wired**

> **`ci_gates.py` is not invoked by any checked-in workflow.** Verified: no workflow references
> it. `FalsifierLintGate`, `Z2HashVerifyGate`, `AntiCascadeLintrule`, `MerkleRootGate` and
> `FullCIIntegrationGate` are library classes with no CI call site.
> `z2_ratification_gate.yml` performs its **own** independent shell, `grep` and YAML checks and
> does not import these classes. Two of the anti-cascade rules are also incomplete:
> `check_rule2` reaches a bare `pass  # Stub for Phase 2` and always returns no issues;
> `check_rule5` only inspects candidates already present in the queue.
>
> This matters beyond the inventory. `CLAUDE.md` describes CI enforcement for Z2 hash
> verification, Merkle-root consistency and anti-cascade rules. **Those gates are not running.**
> Routed as a registrable item in the candidate block.

What *does* run as a gate verdict:

| Signal | Emitter | Effective coverage |
|---|---|---|
| Falsifier presence, Z2 approval greps, config lint | `z2_ratification_gate.yml` (own shell logic) | path-scoped: `z1-inbox/**`, `REGISTERED.md`, `seeds/seed-constitution-*` |
| No-op PR rejection | `no-op-pr-guard.yml` | every PR |
| Behavioural corpus pass-rate ≥ 0.70; new files 100% | `behavioral-compliance.yml` | path-scoped: `tools/**/*.py` |
| Registry consistency | `findings-registry-gate.yml` | path-scoped: `REGISTERED.md` |
| Ownership review requirement | `CODEOWNERS` | on review |

## C · Prediction-and-outcome surfaces

### C1 · Genuine commit-before-outcome — one, and ACAT cannot read it

| Surface | Why it qualifies | Why it is not yet usable |
|---|---|---|
| Phase-1 self-score committed as a **git object** (`acat/research/prgc_phase1/*.json`) | the commit timestamp is immutable and precedes the outcome; tamper-evident by construction | ACAT's two-stage gate reads a submitted `p1_committed_at` **field**, not a git object. These files carry `committed_before_outcome: true` but no `assessment_id`, `session_id` or `p1_committed_at` |

**This is the inventory's most useful finding.** The repository already has a tamper-evident
commit-before-outcome substrate — git — and the instrument does not read it. Closing that is
smaller than building a new mechanism.

### C2 · Ordering only, not provable commitment

| Surface | Why it fails |
|---|---|
| `smag_p:` in the PR body | the **PR body is mutable** and `smag-capture.yml` reads it only on `pull_request.closed`. A probability added or edited after the outcome is captured identically. Nothing snapshots it at PR-open, and `smag_predict_lint.py` runs only inside its own tests in `quality-baseline.yml`. The ordering can be honoured by an author, as it was on #294, but the wiring cannot **prove** it |

### C3 · Rules and post-hoc reconciliation (grounding, not prediction)

| Surface | Why it is not a calibration node |
|---|---|
| Gate catch-rate threshold (`adv_eval_v2.py`) | configured requirement, not a per-run prediction. Also: `_simulate_attack()` derives CAUGHT/MISSED from a generic `gate_state` and `test_input`. It does **not** call any real gate, and the module has no CLI or `__main__`. It is a simulation harness, not an emitting evaluator |
| Claim → ledger receipt (`receipt_reconciliation.py`) | post-hoc; node `RC` is `LAID` |
| Constant staleness (`stale_sweep.py`) | half-life is configuration; node `ST` is `LAID` |
| Molt prediction → window close (`NF_LEDGER`) | the schema is the most mature in the system, but nodes `MOLT` and `ML` are `LAID` |

## D · Cost and restraint signals — declared, not wired

`behavior_spec.json` defines six caps and names `prs_run.py`, `agent_core.py`, `adv_eval.py` and
`molt_cycle.py` as integration points. **No module imports `agent_caps_runtime` or references
`CapEnforcer` outside the runtime module and its own tests, and `adv_eval.py` does not exist.**
Cap violations are a designed signal, not an emitted one.

## E · Callout signals (governance-level)

The `CLAUDE.md` callout taxonomy (`GAP`, `STALE`, `RECEIPT-GAP`, `GAUGE`, `AMBIGUITY`, `VOID`,
`DRIFT`, `DISPUTED`, `MOLT`, `REVERT`) is ritual-driven, not workflow-enforced.

## F · Probe surfaces

| Probe | Dimension | State |
|---|---|---|
| `acat_x_truth.py`, `acat_x_harm.py`, `acat_x_sycophancy.py`, `acat_x_consist.py` | truth, harm, syc, consist | skeletons, `inspect_ai` |
| `acat/scoring/acat_dimension_scorer.py` | Core-6 | **stub** — `score_status: "stub"` |

## The structural finding

Three layers, each thinner than it looks:

1. **Coverage.** Two unconditional workflows, neither an independent reviewer. Independent review
   is best-effort and can be absent entirely.
2. **Enforcement.** The governance gate library is not wired into CI, and two anti-cascade rules
   are incomplete. `CLAUDE.md` describes enforcement that does not run.
3. **Binding.** Nothing writes an emitted signal into a dimension record.

And one asymmetry worth acting on: the system's only tamper-evident commit-before-outcome
substrate is git, which ACAT does not read.

**Falsifier for this inventory (testable form).** Each claim above names an observable artifact.
This document is wrong if: a PR merges in this repo without a completed `security-gates` and
`quality-baseline` check run; or `ci_gates.py` turns out to be referenced by a workflow file in
the default branch; or `copilot-base-guard` posts a non-skipped conclusion on a non-`copilot/*`
PR; or any surface marked dormant/unwired produces a check run or a call site. Each is decidable
from the PR's check-run list or a repository grep — no shared row format is assumed.

---
*Companions: [[PRGC_DIMENSION_MAP]] (P2) · [[PR_GROUNDED_CALIBRATION_PLAN]] (arc) ·
[[PRGC_RETRO_S070626]] (Part A) · [[ACAT_STATE]] (its κ line is stale).*
