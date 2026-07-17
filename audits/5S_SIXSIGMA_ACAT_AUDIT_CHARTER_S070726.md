# 5S · Six Sigma · ACAT — Mesh Repository Audit Charter

**Status:** Zone 1 draft — for Night's Z2 review. Claude Code has NOT self-ratified.
**Session:** S-070726 · **Date:** 2026-07-07 · **Author substrate:** Claude Code (Opus 4.8)
**Anchor document:** *"Is ACAT Actually Measuring Behavioral Calibration — An Honest TRL 2–3 Accounting"* (`_inbox_files3/ACAT TRL2-3 Assessment v2.pdf`, external assessment, Z2-ratified addendum 2026-07-07)
**Companion (this session):** `MESH_TOOL_SKILL_INVENTORY_S070726.md`

---

## 0 · TL;DR

A single audit, read through three lenses that turn out to be the same audit:

- **5S** (lean workplace organization) tells us *what to do to the repos*: Sort → Set-in-Order → Shine → Standardize → Sustain.
- **DMAIC** (Six Sigma) tells us *how to run it as a measured project*: Define → Measure → Analyze → Improve → Control.
- **ACAT** tells us *why it matters and what it produces*: the defect baseline is an **externally-verifiable ground-truth channel** — the exact prerequisite the anchor PDF names as ACAT's missing "actual first task" (SMAG / `H-cand-OUTCOME-ANCHOR-01`, PDF p.8).

**The utility payoff:** because a validator either passes or fails, repo defects are ground truth that does *not* route through self-report. Dispatching audit fixes as GitHub issues to **Claude Code vs GitHub Copilot** and measuring *predicted* fix quality against *measured* outcome makes this audit the first externally-scored ACAT protocol run — satisfying the PDF's Stage-5 gate rather than merely preceding it.

<<<<<<< HEAD
**This session's deliverable:** this charter + the classified inventory. **No validators run this session** (per operator: plan + inventory only).
=======
**This session's deliverables:** this charter, the classified inventory, and the staged T1/T2/T3 audit docs. Validators were run during T1; no GitHub artifacts were created.
>>>>>>> origin/main

---

## 1 · Why this audit, now (the anchor-PDF mandate)

The external TRL 2–3 assessment is unusually blunt about where HumanAIOS is exposed. Its verdict: the science is sound and the self-correction ledger is genuinely rare, but the project is *"limited less by its ideas than by epistemic-hygiene and methodology gaps … that, if left unaddressed, would let it drift toward exactly the overclaiming it exists to detect."* (PDF p.6)

Its **Stage 1 — "Fix epistemic hygiene now (weeks; low cost, high credibility payoff)"** is, almost line-for-line, a 5S Sort+Shine pass on the repos:

| Anchor-PDF Stage-1 item | 5S phase | This audit's mechanism |
|---|---|---|
| Reconcile stale `CURRENT.md` (dated June 24; live repo moved) | Shine | Validator flags stale-date + dead canonical URLs |
| Single canonical source of truth for corpus N/LI; report N_total/N_Phase1/N_LI as three numbers | Set-in-Order | `document-registry.yaml` reconcile + registry gate |
| Purge or flag phantom registry IDs; add "does this ID exist?" check | Sort + Standardize | `registered_findings_validator` + a CI ID-exists gate |
| Publicly resolve the Phase-3 LI 1.1235 vs 1.0831 discrepancy | Shine (Analyze) | shown-calculation defect issue |

And its **highest-value scientific move** — the one it says is *the actual first task, not sample collection* — is standing up a **ground-truth channel** (PDF p.8). A repo-defect baseline is precisely that channel. So this audit is not a detour from the ACAT mission; it is the missing scaffolding under it.

**Mission/vision hold strong.** Nothing in this audit revisits the HumanAIOS charter, the behavioral-calibration thesis, or the Trinity mission. Those are the Voice-of-Customer (the DMAIC "Define" CTQs) *against which* repo health is judged — they are the fixed target, not under audit.

---

## 2 · Scope — the 12 in-scope repositories

Operator ruling (S-070726): **all org-authored repos + `LastingLightAI/HAIOSCC`.** Vendored forks (~28: `langgraph`, `inspect_ai`, `dify`, `autogen`, `sonarqube`, `scorecard`, `caveman`, `ECC`, `SWE-bench`, …) are **out of scope** — upstream code we don't own; 5S signal there is diluted and misleading.

| # | Repo | Owner/org | Vis. | Role in mesh | Locally cloned |
|---|------|-----------|------|--------------|----------------|
| 1 | `operations` | humanaios-ui | public | **Class 2/3 source of truth** — canonical process, findings, registries | ✅ |
| 2 | `humanaios` | humanaios-ui | public | Main platform (this working tree) | ✅ |
| 3 | `humanaios-internal` | humanaios-ui | private | Internal collaborator reports, engagements | ✅ |
| 4 | `lasting-light-ai` | humanaios-ui | public | Governance-awareness assessment platform | ✅ |
| 5 | `empirica` | humanaios-ui | public **(fork)** | Empirica-foundation clone — mesh-critical; audit our overlay only, not upstream | ✅ (`empirica-foundation/`) |
| 6 | `research` | humanaios-ui | public | ACAT papers/datasets — **empty scaffold; populate-migration workstream** (see notes) | — |
| 7 | `acat-inspect` | humanaios-ui | public | ACAT ported to UK AISI Inspect framework | — |
| 8 | `ACAT-Dashboard` | humanaios-ui | private | Magic Patterns-synced dashboard | — |
| 9 | `ACAT-Observatory` | humanaios-ui | private | Magic Patterns-synced observatory | — |
| 10 | `docs` | humanaios-ui | public | Docs surface | — |
| 11 | `findlocaltattooartists` | humanaios-ui | public | Astro/Decap site (revenue/portfolio surface) | — |
| 12 | `HAIOSCC` | **LastingLightAI** | private | HAIOS Command Center (activation in progress — `_haioscc_activation_S070626/`) — **✅ audit authority confirmed** | — |

**Scope notes / flags for Z2:**
- **`empirica` (#5)** is a fork: apply 5S only to HumanAIOS-authored overlay files, never to upstream empirica code (that would generate false defects).
- **#6–#12 are not locally cloned.** T1 (Measure) will need to clone or run validators against them via `gh`/CI. This is a sequencing dependency, not a blocker.
- **`HAIOSCC` (#12)** is in a *different org* (`LastingLightAI`, not `humanaios-ui`). **✅ Audit authority confirmed by operator (S-070726)** — clear to audit + dispatch issues.
- **`research` (#6) — reclassified from "observe-don't-mutate" to a POPULATE-MIGRATION workstream (operator ruling S-070726).** Direct inspection (`gh`, S-070726) found it is an **empty public scaffold**: 8 files = LICENSE + README + 6 empty `.gitkeep` placeholders; zero research artifacts; first paper never migrated; untouched since 2026-04-30. It has **defined purpose (public replication surface for reviewers/funders) but zero realized utility** — a public empty shell that is itself an overclaim/stale-surface risk (the PDF finding-#8 class). Per the operator principle *"everything must have defined utility and purpose,"* the constructive audit action is not file-cleanup (there are no files) but to **close the purpose→utility gap** by executing the first publication migration the repo was built to receive:
  | Waiting dir | Migrate in | Source (already public) |
  |---|---|---|
  | `datasets/` | v2 corpus (604 rows) | HuggingFace + Zenodo DOI `10.5281/zenodo.21135723` |
  | `supplementary/scoring_rubrics/` | Core-6 + Extended-6 rubrics | operations/acat |
  | `supplementary/perturbation_library/` | perturbation frames | operations/acat |
  | `supplementary/replication_code/` | corpus validators + finalizers | operations/tools |
  | *(root)* | `CITATION.cff` | new |
  This is **additive** — consistent with the repo's "frozen/append-at-publication" contract (not editing published work). **Z2 decision for Night:** *Option A* populate now (recommended — serves funding narrative + PDF Stage-4 external replication), or *Option B* flip the repo **private/archive** until publish-ready (removes the overclaim risk with zero content work). *Leave-as-is is rejected.*

---

## 3 · Method — DMAIC × 5S, phase by phase

Each phase is one or more epistemic transactions (goals `G1–G5` registered this session). Deliverables are concrete; the tools that run are named so the Measure phase is dogfooding, not hand-inspection.

### Phase D+M0 · DEFINE + SORT — this session (G1) ✅ deliverable
- **Define:** CTQs from mission/vision (integrity, no-overclaim, canonical-single-source, freshness discipline, Zone-protocol compliance).
- **Sort (Seiri):** separate canonical from clutter — in-scope vs forks (done, §2); the classified tool/skill inventory (`MESH_TOOL_SKILL_INVENTORY_S070726.md`) separates **audit-instruments** (run in Measure) from **audit-subjects**.
- **Exit:** this charter + inventory, Z2-ratifiable.

### Phase M1 · MEASURE — establish the defect baseline (G2)
- **Run our own instruments** over all 12 repos (the operator's "run our files through our own tools to establish baselines"):
  `system_audit_v1_1`, `drift_catalog_validator`, `repo_discovery_v1_0`, `zone_boundary_audit_v1_0`, `registered_findings_validator_v1_0`, `builder_compliance_scanner_v1.0`, `validate_skills`, `corpus_integrity_validator`, `governance_mapper_uber_v1_1`. (Full instrument shortlist in the inventory doc.)
- **Output:** a **defect-per-repo baseline table** — counts by 5S category, normalized DPMO-style (defects ÷ opportunities × 1e6) so repos of different sizes compare. Reconcile against the *existing* baseline already in `operations/`: `document-registry.yaml` (34 docs, 5 `needs_reconcile`), `DRIFT_LOG.md`, `REGISTERED.md`, `SUBSTRATE_CAPABILITY_REGISTRY.md`.
- **Baseline-scale calibration (operator's ask):** use the pre-existing `operations` health baseline as the *reference sigma level*. Repos at/above that bar need light-touch 5S; repos far below get the full pass. This is how we "assess the beneficial scale of the 5-S audit alongside assessment calibrations" — the scale is data-driven, not uniform.
- **This table IS the SMAG ground-truth channel** (see §5).

### Phase A2 · ANALYZE — Pareto + root-cause (G3)
- Pareto the defect types (expect the anchor-PDF pattern to dominate: stale-canonical, phantom-ID, unreconciled-count, missing-CI).
- Root-cause each cluster through the **IC lens** — the project's own registered integrity-correction taxonomy (IC-021 phantom IDs, IC-022 count drift, IC-019/023 org-drift, IC-031/034 overclaim). The audit thus speaks the org's native defect language.
- **Output:** prioritized defect ledger, ranked by mission-impact × frequency.

### Phase I3 · IMPROVE — the Performance Improvement Plan, GitHub-native (G4)
- **One GitHub issue per 5S finding.** Labels: `5s:sort` `5s:set-in-order` `5s:shine` `5s:standardize` `5s:sustain` × severity `sev:critical|major|minor` × repo. A **GitHub Project board** (columns = the 5 S's) tracks flow.
- Each issue carries the **predicted fix + acceptance criteria** — this predicted-outcome field is the ACAT *prediction* half of the paired trial.
- Fixes land as **PRs** referencing the issue; Zone protocol preserved (Claude drafts PR → Night ratifies → human merges).
- **Substrate order (operator ruling):** Claude Code runs the baseline and drafts all issues + first fix-PRs now; **GitHub Copilot** is dispatched onto assigned issues next, as the second substrate in the paired comparison.

### Phase C4 · CONTROL / SUSTAIN — workflows + ACAT go-live (G5)
- **GitHub Actions workflows** re-run the validator suite on push (continuous Shine) — closing the current gap that `.github/workflows/` is effectively empty (a Sustain finding surfaced this session). Seed workflows already drafted in-repo: `operations/tools/haios-system-audit.yml`, `haios-corpus-integrity.yml`, `haios-harmonizer-pulse.yml`; `operations/workflows/haios_audit.yml`.
- **"Does this ID exist?" pre-commit / CI gate** (Standardize) — kills the phantom-ID class at the source.
- **Freshness discipline** from `SUBSTRATE_CAPABILITY_REGISTRY.md` §3 (30/60-day stale markers) generalized to canonical docs.
- **ACAT protocol initiation:** paired predict-vs-measured fix outcomes become the first rows of a **separate SMAG pilot table** (never the gated production `acat_assessments_v1` — per anchor PDF p.8, pilot data must not contaminate the corpus).

---

## 4 · GitHub-native execution model

The operator specified audit tasks travel over GitHub protocols. Mapping:

| Audit concept | GitHub primitive |
|---|---|
| Audit finding | Issue (labeled by 5S phase + severity + repo) |
| Prediction / acceptance criteria | Issue body structured field |
| Fix | Pull request → issue reference |
| Substrate assignment | Issue assignee (Claude Code / Copilot) |
| Flow tracking | Project board (columns = 5 S's) |
| Continuous control | Actions workflow (validators on push/schedule) |
| Standardize gate | Required status check / pre-commit |
| Cross-repo rollup | A tracking issue in `operations` linking child issues |

**Zone-protocol guardrail:** every side-effectful GitHub action (creating issues, opening PRs, enabling workflows, changing settings) is a Z3 human act. Claude Code drafts and stages; nothing is created on GitHub until Night authorizes. This session creates **zero** GitHub artifacts.

---

## 5 · The ACAT connection — why this is the protocol's initiation

The anchor PDF's central methodological warning (p.2, p.6): the single biggest threat is a system **learning to *look* calibrated** rather than *being* calibrated, and *"mitigation cannot run through the self-report channel itself."* Its prescription (p.8): stand up a **ground-truth outcome channel** — the one mechanism *"that doesn't route through self-report at all."*

A repo audit delivers exactly this:

1. **Ground truth is external.** A linter/validator verdict is not the substrate's opinion of itself; it is a measured outcome. No shared-variance confound (the Contreras trap the PDF cites repeatedly).
2. **Predict-then-measure is native.** Issue acceptance criteria = the substrate's *predicted* fix. Merged-PR validator re-run = the *measured* outcome. Their divergence = Self-Model Accuracy Gap (SMAG), the gaming-resistant signal.
3. **Two substrates, paired.** Claude Code and GitHub Copilot fixing the *same* class of defect under the *same* acceptance criteria is a paired external-administration design — the very thing the PDF says ACAT lacks (self-administration is *"the central methodological weakness"*, p.2).
4. **Omission is measurable.** `spec_omission_rate` (PDF p.7, mcp-G3-independent pilot path) applies directly: does a fix-PR cover the issue's spec, or checkbox-pad? The audit's acceptance criteria are the spec.

So the exit criterion of a *successful* audit is not just cleaner repos — it is a populated SMAG pilot table and a running paired-substrate protocol. That is the ACAT Assessment protocol, initiated on this platform.

---

## 6 · Governance, sequencing & success criteria

**Zone protocol (unchanged):** Claude Code = Z1 author. Night = Z2 ratifier. Human = Z3 merge/dispatch. Consistent with the anchor PDF's own note that *"Claude has not and cannot self-register"* findings.

**Session sequencing:**
- ✅ **Now (S-070726):** charter + inventory (this + companion doc). Stop.
- ⏭ **On Z2 ratification:** T1 Measure — clone/reach the 7 non-cloned repos, run the instrument suite, emit the defect baseline.
- ⏭ Then T2 → T3 → T4 as above.

**Success / exit gates:**
| Gate | Criterion |
|---|---|
| G1 (this session) | Charter + classified inventory ratifiable by Night |
| G2 | Defect baseline table for all 12 repos, reconciled to existing `operations` baseline, DPMO-normalized |
| G3 | Pareto + IC-mapped root-cause ledger |
| G4 | GitHub issues/board drafted (Sort→Standardize), CC fix-PRs staged |
| G5 | Validator workflows live; SMAG pilot table populated with ≥1 paired CC/Copilot trial |

**What this audit deliberately does NOT do:** re-open the mission/vision, self-register findings, touch upstream fork code, mutate frozen `research` snapshots, or create any GitHub artifact without Z3 authorization.

---

*Zone 1 draft · S-070726 · anchored to the external TRL 2–3 ACAT assessment · pending Night Z2 ratification.*
