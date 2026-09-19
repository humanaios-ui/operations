# T1 · Measure — Mesh Defect Baseline (SMAG ground-truth channel)

**Status:** Zone 1 draft — for Night's Z2 review. **Phase:** DMAIC *Measure* (G2). **Session:** S-070726 · 2026-07-07 · Claude Code (Opus 4.8)
**Charter:** `5S_SIXSIGMA_ACAT_AUDIT_CHARTER_S070726.md` · **Inventory:** `MESH_TOOL_SKILL_INVENTORY_S070726.md`
**What this is:** the externally-verifiable defect baseline across the 12-repo mesh — the SMAG ground-truth channel the TRL 2-3 assessment names as ACAT's missing first prerequisite. Every number here is measured (`gh api`, `git`, our own validators), not self-reported.

---

## 0 · Headline

- **Mesh first-pass yield = 42.9%** (44 structural defects / 77 opportunities; ≈571,000 DPMO; ≈1.3σ). Large improvement headroom — expected and healthy for a first baseline.
- **`operations` is the clean reference bar** (0/7 structural defects) — validates the charter's plan to calibrate audit *scale* against operations' own health.
- **Two critical, non-obvious findings the baseline surfaced** that no file-cleanup would have caught:
  1. **Local↔remote drift** — the canonical `operations` working clone is **103 commits behind** origin; `humanaios` (primary) is parked on a Dependabot branch.
  2. **`REGISTERED.md` fails its own validator** — 17 hard failures incl. 4 ID collisions, directly reproducing the external assessor's finding #8.

---

## 1 · Method (honest scope)

The recon confirmed our 25 audit-instruments are **not general repo scanners** — they are artifact-specific governance validators (bound to `REGISTERED.md`, corpus CSV, `SKILL.md` dirs), almost all targeting `operations`. So the baseline is measured in two honest layers:

- **Layer A — cross-repo structural** (`gh api` + `git`): applies to all 12 repos. Sync-drift, staleness, CI, standard-files, license, empty-scaffold.
- **Layer B — governance dogfooding** (our own validators on their proper `operations` targets): the genuine "run our files through our own tools" step.

**Caveat — RESOLVED (§4b):** Layer B first ran against the local (103-behind) clone. It has since been re-run against a fresh `origin/main` clone; canonical is measurably *worse*, confirming the defects are source-of-truth. See §4b.

---

## 2 · Layer A — cross-repo structural scorecard

7 remote-observable conformance checks per repo; a defect = a failing check. DPMO = defects ÷ 7 × 10⁶. Fork excluded from mesh totals (upstream-owned).

| Repo | Defects | DPMO | fresh≤30d | CI | LICENSE | CONTRIB | SECURITY | CODEOWNERS | Note |
|---|---|---|:--:|:--:|:--:|:--:|:--:|:--:|---|
| `operations` | **0/7** | 0 | ✓ | ✓ (5) | ✓ | ✓ | ✓ | ✓ | **reference bar** |
| `lasting-light-ai` | 1/7 | 142,857 | ✓ | ✓ (2) | ✓ | ✓ | ✓ | ✗ | healthiest satellite |
| `humanaios` | 2/7 | 285,714 | ✓ | ✗ (0) | ✓ | ✓ | ✓ | ✗ | **primary — 0 CI** |
| `humanaios-internal` | 4/7 | 571,428 | ✓ | ✓ (1) | ✗ | ✗ | ✗ | ✗ | license NOASSERTION |
| `docs` | 4/7 | 571,428 | ✗ | ✗ | ✓ | ✓ | ✗ | ✗ | stale 03-22 |
| `research` | 5/7 | 714,285 | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ | **empty scaffold** |
| `acat-inspect` | 5/7 | 714,285 | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ | stale 04-28 |
| `HAIOSCC` | 5/7 | 714,285 | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | diff org; no license |
| `ACAT-Dashboard` | 6/7 | 857,142 | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | private, stale |
| `ACAT-Observatory` | 6/7 | 857,142 | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | private, **~4mo stale** |
| `findlocaltattooartists` | 6/7 | 857,142 | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | revenue site, no license |
| `empirica` (fork) | 0/7 | — | ✓ | ✓ (3) | ✓ | ✓ | ✓ | ✓ | excluded (upstream) |
| **MESH (excl. fork)** | **44/77** | **571,428** | | | | | | | **FPY 42.9%** |

**Pareto of the 44 structural defects:** CODEOWNERS-missing 10 · SECURITY-missing 8 · CI-missing 7 · CONTRIBUTING-missing 6 · stale>30d 6 · LICENSE-missing 4 · empty-scaffold 1 (research) + 2 empty placeholder files each in operations/humanaios. The single cheapest sweep with the biggest yield lift: **add CODEOWNERS + SECURITY.md org-wide** (18 defects, template-able in one PR each).

---

## 3 · Critical dimension — local↔remote sync health

Not in the 7-check DPMO (it's a working-environment defect, not a repo defect) but the **highest-severity finding**: the local clones the operator works from have drifted hard from canonical.

| Local clone | Branch | Behind `origin/main` | Ahead | Dirty | Severity |
|---|---|---|---|---|---|
| `operations` (SoT) | main | **103** | 2 | 2 | **critical** |
| `humanaios` (primary) | `dependabot/…nestjs/core-11.1.27` | 27 | 0 | 9 | **critical** (wrong branch) |
| `humanaios-internal` | main | 34 | 0 | 0 | major |
| `lasting-light-ai` | feature branch | 2 | 1 | 1 | ok |
| `empirica` | main | 0 | 0 | 1 | ok |

**Implications:** (a) IC-019/023-class org-drift — the exact pattern the team has registered before; (b) the earlier "operations has no CI" inference was a *stale-clone artifact* — remote operations has 5 live workflows (incl. `document-control.yml`, `research-validation.yml`); (c) **this session's audit commits (`6b92277`, `a8a404f`) sit on a local main 103 behind remote — they cannot fast-forward push; reconcile before any push.**

---

## 4 · Layer B — governance dogfooding (our validators on `operations` artifacts)

The org's own validators, run on the org's own canonical artifacts. This is the SMAG channel: pass/fail is external, not self-report.

| Instrument | Target | Verdict | Measured defects |
|---|---|---|---|
| `registered_findings_validator_v1_0` | `REGISTERED.md` | **FAIL** | **17 hard** (4 ID collisions: H-IPM, H-HUMILITY, H-ELICIT, H-OVG each ×2; ~13 date-format e.g. F-18/20/22 `"2026-02"`), **24 warnings** (uncommitted candidates F-52…F-55, H-VERIF/SELF/MECH/CAND… not Z2-verified). Entry counts: F=38, H=27, IC=21. |
| `builder_compliance_scanner_v1.0` | `tools/` (92 files) | **54% pass** | 50 pass / **42 fail**. Top: MISSING_HEADER 36, ERROR_IMPORT_MISSING 35, NO_WRITE_REPORT 33, NO_TOOL_VERSION 28, NO_TOOL_NAME 27. |
| `validate_skills` | `tools/skills/` | **CRASH** | Malformed YAML in `humanaios-findings-scan/SKILL.md` (unquoted colon) → `ScannerError`. Two defects: bad manifest **+** non-resilient validator (halts whole scan). |
| `corpus_integrity_validator` | `acat_corpus_v2.csv` | **PASS** | n=604, n_li_valid=274, mean_li=0.8532, 68 agents, 0 phase-pairing gaps, 82 non-blocking warnings. Confirms the v2 reconciliation held. |
| `skill_compression_scanner_v1_0` | `operations` | **clean** | nothing over threshold. |
| `system_audit_v1_1` | live infra | **not run** | needs `GITHUB_TOKEN`/`SUPABASE_*` env — measurement gap, deferred to a credentialed run. |

**The keystone result:** `REGISTERED.md` — the append-only findings registry that is the org's source of epistemic truth — **fails its own integrity validator**, reproducing precisely the phantom/collision-ID class the external TRL 2-3 assessor flagged (finding #8) without access to the repo internals. The audit's own tooling independently confirms the external critique. *That is the proof-of-concept the whole ACAT thesis rests on, now measured on the repos.*

---

## 4b · Canonical re-run — measurement gap CLOSED

The T1 caveat (Layer B ran against the 103-behind local clone) is now closed: fresh-cloned `operations` `origin/main` (`c90c85c`, 2026-07-07 08:41) and re-ran **canonical tools on canonical artifacts**. Result: **canonical is not cleaner — the registry is measurably *worse*.** The defects are source-of-truth, not stale-clone artifacts.

| Instrument | Working copy (local, 103-behind) | **Canonical (`c90c85c`)** | Delta |
|---|---|---|---|
| `registered_findings_validator` | FAIL — 17 hard (4 collisions), 24 warn | **FAIL — 21 hard (5 collisions), 23 warn** | **+4 hard on canonical** |
| ↳ collisions | H-IPM, H-HUMILITY, H-ELICIT, H-OVG | **+ F-31** (5 total) | new F-31 collision |
| ↳ hard classes | — | **collision ×5, date-format ×13, status-invalid ×2, missing-field ×1** | — |
| ↳ entry counts | F38 H27 IC21 (86) | F38 H27 **IC22 (87)** | +1 IC |
| `builder_compliance_scanner` | 50/92 (54%) | **50/94 (53%)** | ~same (+2 tools) |
| `validate_skills` | CRASH — `humanaios-findings-scan/SKILL.md` | **CRASH — same file** | unchanged (canonical bug) |
| `corpus_integrity_validator` | PASS (604, 0.8532, 82 warn) | **PASS — identical** | none |

**Two conclusions that harden the baseline:**
1. **The registry defects are canonical truth.** The ID collisions, 13 date-format errors, 2 invalid-status entries, and the broken `SKILL.md` all exist on `origin/main`. The external assessor's finding #8 is confirmed against the source of truth, not a working-copy artifact.
2. **Drift and registry-integrity are *independent* problems.** The 103-commit local drift did not *cause* the registry failures (canonical has *more*, not fewer). Both are real; they need separate root-causes in T2. Canonical also carries defects the local copy hadn't yet accumulated (F-31 collision, status-invalid entries) — so *neither* direction of the drift is "the clean one."

**Method note:** `document-control.yml` is live on canonical, yet canonical `REGISTERED.md` still fails integrity — so either that workflow doesn't gate registry ID/format/status, or it isn't enforced on the merge path. T2 should confirm which (it changes whether the Standardize fix is "add a gate" or "fix the existing gate").

---

## 5 · Reconciliation vs the pre-existing `operations` baseline

The audit extends, not replaces, the existing health substrate:

| Existing baseline | Says | T1 reconciliation |
|---|---|---|
| `document-registry.yaml` | 34 docs, 37 excluded, **5 `needs_reconcile`** | Consistent; the 5 needs-reconcile are Set-in-Order defects, additive to the 44 structural. |
| `REGISTERED.md` (registry) | F=38 H=27 IC=21 (total 86) | Validator now quantifies its defects: 17 hard + 24 warnings. |
| `CURRENT.md` | last updated 2026-06-24 | Stale (>10d + points at pre-move URLs) — Shine target, matches PDF #8. |
| `SUBSTRATE_CAPABILITY_REGISTRY.md` §3 | 30/60-day freshness discipline | The freshness rule exists but isn't enforced by CI — Sustain gap. |

---

## 6 · What T1 hands to T2 (Analyze)

The prioritized defect ledger for Pareto + IC-lens root-cause:

1. **[critical] Local↔remote drift** — operations 103 behind, humanaios on stray branch. Root: no sync discipline / CI guard. → IC-019/023 class.
2. **[critical] `REGISTERED.md` integrity** — 4 ID collisions + 13 date-format + 24 unverified candidates. Root: no pre-commit ID-exists/format gate. → IC-021/022 class. (Note: remote `operations` already has `document-control.yml` — check whether it already guards this.)
3. **[major] CI absence** — `humanaios` + 5 satellites have zero workflows; freshness discipline unenforced.
4. **[major] Builder non-compliance** — 42/92 tools fail Builder v1.7.
5. **[major] Governance-file gaps** — CODEOWNERS 10, SECURITY 8, CONTRIBUTING 6, LICENSE 4 missing.
6. **[major] `research` empty scaffold** — Option A populate ratified (separate workstream).
7. **[minor] Broken `SKILL.md`** — one file; also harden the validator.
8. **[minor] Staleness** — 6 repos >30d (ACAT-Observatory ~4mo).

**Measurement gaps:** ✅ canonical Layer-B re-run — DONE (§4b). Remaining: `system_audit_v1_1` (needs `GITHUB_TOKEN`/`SUPABASE_*` credentials); the 7 non-cloned repos measured via `gh` only (no deep file scan yet).

---

## 7 · Governance

Zone protocol honored: T1 **read** all repos and **wrote** only local scratch reports (`scratchpad/t1out/`) + this Z1 draft. **No repo mutations, no GitHub artifacts, nothing pushed.** Baseline pending Night Z2 ratification before T2 (Analyze).

*Zone 1 draft · S-070726 · defect baseline / SMAG channel · measured, not self-reported · pending Z2.*
