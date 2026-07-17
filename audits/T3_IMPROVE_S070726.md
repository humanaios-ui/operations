# T3 · Improve — Performance-Improvement Plan (GitHub-native, staged)

**Status:** Zone 1 draft — for Night's Z2 review, then **Z3 authorization to create GitHub artifacts**. **Phase:** DMAIC *Improve* (G4). **Session:** S-070726 · Claude Code.
**Inputs:** ratified `T2_ANALYZE_S070726.md` ledger. **Substrate order:** Claude Code now, GitHub Copilot next.

> **Governance gate:** everything below is *staged*. Creating issues, opening the PR, the project board, and enabling workflows are **Z3 human acts** (publishing to GitHub). Nothing has been created. §5 lists the exact commands to run on your authorization.

---

## 0 · Already executed this session (local, reversible)

The P1 marquee fix is **implemented and measured**, not just planned:

- **Branch `fix/registered-findings-validator-falsepos`** (off canonical `origin/main` `c90c85c`), commit **`70db543`**: patched `registered_findings_validator_v1_0.py` (H-suffix regex + `correction_to` skip + `RESOLVED`/`CLOSED` enum).
- **Measured result:** canonical `REGISTERED.md` **21 → 13 hard failures** (collisions 5→0, missing-field 1→0, status 2→1). Smoke-test still passes.
- **SMAG datapoint #1:** predicted 8 removed → 13 remain; measured exactly 13 — but composition revealed the corrected validator *surfaces* a real defect (`H-HUMILITY-MASTER-01` malformed status) the old noise was burying. Predict-then-measure worked.

This branch is **PR-ready** (Issue-03 below is really a PR).

---

## 1 · GitHub issue register (ready to `gh issue create`)

Labels: `5s:sort|set-in-order|shine|standardize|sustain` × `sev:critical|major|minor` × `repo:<name>`. Each issue's **Acceptance criteria = the ACAT prediction** (the fix's expected measured outcome — the predict half of the paired trial).

### P0 — critical (sync + safety)

**Issue-01 — Reconcile drifted local clones** · `5s:shine` `sev:critical` `repo:operations` · assignee: **human/CC**
Local `operations` main is 103 behind `origin/main`; `humanaios` working dir is on a Dependabot branch (27 behind). Rebase/realign local clones; move `humanaios` back to `main`. **Also cherry-picks this audit's 5 doc commits onto a fresh `origin/main` base so they become pushable.** *Accept:* `git rev-list --count HEAD..origin/main == 0` on both; audit docs on a branch off current main.

**Issue-02 — Add pre-push behind-remote / wrong-branch guard** · `5s:standardize` `sev:critical` `repo:operations` · assignee: **CC**
A pre-push hook (or CI check) that fails if local is behind remote or pushing from an unexpected branch. Kills the IC-026 class. *Accept:* hook blocks a deliberately-stale push in a test; documented in OPERATOR_RUNBOOK.

### P1 — critical (fix the instrument, then gate it)

**Issue-03 → PR — Fix `registered_findings_validator` false-positives** · `5s:shine` `sev:critical` `repo:operations` · assignee: **CC** · **DONE, branch `fix/registered-findings-validator-falsepos`**
*Accept (met):* canonical REGISTERED.md hard failures 21→13; 0 collisions; smoke-test passes. → open PR (§5).

**Issue-04 — Wire the corrected findings-validator into CI** · `5s:sustain` `sev:critical` `repo:operations` · assignee: **Copilot**
Add a workflow (mirror `document-control.yml`) running `registered_findings_validator --input REGISTERED.md --strict` on PRs/pushes touching `REGISTERED.md`, blocking on hard failures. *Accept:* a PR that reintroduces an ID collision fails CI; a clean one passes. **Depends on Issue-03 merged** (else CI blocks on the 13 known-residual until Issue-09 lands — stage as non-blocking first, promote after).

### P2 — major (gates + templates)

**Issue-05 — Builder-lint gate + bring legacy tools to Builder v1.7** · `5s:standardize` `sev:major` `repo:operations` · assignee: **Copilot**
42/94 tools fail `builder_compliance_scanner`. Add a CI gate; batch-fix the top classes (MISSING_HEADER 36, ERROR_IMPORT_MISSING 35, NO_TOOL_VERSION/NAME). *Accept:* pass-rate 0.53 → ≥0.90; gate blocks a non-compliant new tool.

**Issue-06 — Seed CI on `humanaios` + 5 satellites** · `5s:sustain` `sev:major` `repo:humanaios,research,acat-inspect,ACAT-Dashboard,ACAT-Observatory,findlocaltattooartists` · assignee: **Copilot**
Promote the drafted workflow YAMLs (`operations/tools/haios-*.yml`, `operations/workflows/*.yml`) into live `.github/workflows/`. *Accept:* each repo runs ≥1 validator/freshness check on push.

**Issue-07 — Org-template CODEOWNERS + SECURITY.md + LICENSE** · `5s:standardize` `sev:major` `repo:*` · assignee: **CC**
28 standard-file gaps (CODEOWNERS ×10, SECURITY ×8, CONTRIBUTING ×6, LICENSE ×4). Add via `.github` org-template repo or per-repo. *Accept:* structural DPMO for these checks → 0; FPY 42.9% → ≥85%.

### P3 — minor (residual content)

**Issue-08 — Fix broken `SKILL.md` + harden `validate_skills`** · `5s:shine` `sev:minor` `repo:operations` · assignee: **CC**
Quote the colon in `humanaios-findings-scan/SKILL.md` frontmatter; make `validate_skills` report-and-continue instead of crashing on one bad file. *Accept:* `validate_skills` runs to completion; reports the one file, exits nonzero, doesn't traceback.

**Issue-09 — Fix `H-HUMILITY-MASTER-01` status + grandfather 12 legacy dates** · `5s:shine` `sev:minor` `repo:operations` · assignee: **Copilot**
Replace the prose Status on `H-HUMILITY-MASTER-01` (line ~2330) with a valid enum + move prose to a note; decide grandfather-vs-backfill for the 12 month-precision dates (F-18…F-24 era). *Accept:* validator hard failures 13 → 0 (or documented grandfather rule); unblocks Issue-04 blocking mode.

**Issue-10 — `research` populate migration (Option A, ratified)** · `5s:set-in-order` `sev:major` `repo:research` · assignee: **CC**
Migrate v2 corpus (HF + Zenodo DOI 10.5281/zenodo.21135723) → `datasets/`; Core-6/Extended-6 rubrics → `supplementary/scoring_rubrics/`; perturbation library + replication code; add `CITATION.cff`. *Accept:* zero empty `.gitkeep` placeholders; a reviewer following the README finds real artifacts.

### DO NOT FILE
- ~~"Deduplicate colliding IDs"~~ — false positives (T2 §2). Filing this would delete legitimate sub-findings + the F-31 correction.

---

## 2 · Project board (columns = the 5 S's)

| Sort | Set in Order | Shine | Standardize | Sustain |
|---|---|---|---|---|
| Issue-01 | Issue-10 | Issue-03(PR), 08, 09 | Issue-02, 05, 07 | Issue-04, 05, 06 |

Cross-repo rollup: a tracking issue in `operations` linking all children.

---

## 3 · Substrate assignment (the ACAT paired design)

Per charter §5, the CC-vs-Copilot split makes this the first paired external-administration ACAT run:

- **Claude Code (now):** Issue-01, 02, 03(PR), 07, 08, 10 — audit-native + drafting.
- **GitHub Copilot (next):** Issue-04, 05, 06, 09 — the CI-wiring + batch-mechanical fixes.
- Each issue's acceptance criteria = the *predicted* outcome; the merged-PR validator re-run = the *measured* outcome; divergence = the SMAG signal, logged to a **separate pilot table** (never the gated corpus).

---

## 4 · SMAG pilot ledger (starts now)

| # | Task | Substrate | Predicted | Measured | Gap |
|---|---|---|---|---|---|
| 1 | validator false-pos fix | Claude Code | 21→13, all date-format | 21→13 (12 date + 1 real status) | count exact; +1 real defect surfaced |

Row 1 is real. Rows 2+ populate as issues close.

---

## 5 · Z3 authorization needed — exact actions

On your go, I will (each is a discrete GitHub write; approve all or per-item):

1. **Open the PR** for the validator fix:
   `gh pr create --repo humanaios-ui/operations --head fix/registered-findings-validator-falsepos --base main` (requires pushing the branch first).
2. **Create 10 issues** (Issue-01…10) via `gh issue create` with the labels/bodies above.
3. **Create labels** (`5s:*`, `sev:*`) and the **project board**.
4. **(Later)** enable the CI workflows (Issue-04/06) — separate authorization at merge time.

**Recommended first step regardless:** authorize **Issue-01** (reconcile clones) — it unblocks pushing both this audit's docs *and* the fix branch, since everything currently sits on a local `operations` main 103 behind canonical.

*Zone 1 draft · S-070726 · staged, nothing published · pending Z2 ratification + Z3 authorization.*
