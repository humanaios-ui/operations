# WGS Implementation Checklist — June 22–24, 2026 Scan

**Scan window:** June 22, 2026 8:37 PM CT → June 24, 2026 8:37 PM CT  
**Generated:** June 28, 2026  
**Source skill:** WGS File Update & GitHub PR Draft Scout  
**Repository:** humanaios-ui/operations

---

## Summary

| Metric | Count |
|---|---|
| Signals found | 12 |
| PR drafts | 9 |
| Issue drafts | 2 |
| Carry-forward | 1 |

**P0 items requiring immediate action:** S9 (haios_audit.yml false-pass), S10 (acat_merkle_auditor reconciliation)

---

## Signal Checklist

---

### S1 · PR · P1 · Ready to submit

**Title:** `docs(skills): add tools/skills/README.md — 67-skill index`  
**File(s):** `tools/skills/README.md`  
**Status:** Ready to submit  
**Source:** S-061026-01 addendum

**Required actions:**
- [ ] Verify `tools/skills/README.md` does not already exist in repo
- [ ] Submit PR adding 158-line, 9-section README indexing all 67 skills across 7 functional categories with Zone classification table, install instructions, and promotion candidates list
- [ ] Apply labels: `docs`, `skills`; assign GitHub Copilot

**Verification criteria:** `tools/skills/README.md` present in repo, all 67 skill folders listed, CI passes.

---

### S2 · PR · P1 · Ready to submit

**Title:** `chore(governance): commit 5 refactored/new skill SKILL.md files`  
**File(s):**
- `tools/skills/humanaios-mhp-consultation/SKILL.md` (v1.2)
- `tools/skills/humanaios-dual-architecture/SKILL.md` (v1.3)
- `tools/skills/humanaios-realtime-drift/SKILL.md` (refactored)
- `tools/skills/humanaios-findings-scan/SKILL.md` (refactored)
- `tools/skills/humanaios-wgs-sweep/SKILL.md` (refactored)

**Status:** Ready to submit  
**Source:** S-061526 Zone 3 Queue

**Required actions:**
- [ ] Submit PR committing all 5 SKILL.md files: MHP consultation (v1.2, AA Steps 8–12, Z3 Impulse Audit Log), dual-architecture (v1.3, canonical meta-spec, EXEMPT self-compliance), and three refactored skills with Z3 prohibition + impulse logs added
- [ ] Apply labels: `governance`, `skills`, `protocol`; assign GitHub Copilot

**Verification criteria:** All 5 files present with correct version headers, Z3 prohibition blocks, and impulse log sections; CI passes.

---

### S3 · PR · P2 · Ready to submit

**Title:** `chore(governance): add deprecated skill notice for humanaios-core-architecture-pattern`  
**File(s):** `tools/skills/deprecated/humanaios-core-architecture-pattern/SKILL.md`  
**Status:** Ready to submit  
**Source:** S-061526 Close Note · Z3 Queue

**Required actions:**
- [ ] Create `tools/skills/deprecated/humanaios-core-architecture-pattern/` directory if absent
- [ ] Submit PR adding SKILL.md deprecation notice referencing supersession by `humanaios-dual-architecture` v1.3
- [ ] Apply labels: `chore`, `governance`, `deprecated`; assign GitHub Copilot

**Verification criteria:** Deprecation SKILL.md present in `deprecated/` subfolder, references superseding skill, CI passes.

---

### S4 · PR · P1 · Ready to submit

**Title:** `ci: add JSON schema, lint workflow, validator, and pytest harness`  
**File(s):**
- `schemas/architecture.schema.json`
- `.github/workflows/humanaios-lint.yml`
- `scripts/validate_skills.py`
- `tests/test_acat_core.py`

**Status:** Ready to submit  
**Source:** S-061526 Close Note · Z1 Artifacts

**Required actions:**
- [ ] Verify none of the 4 files already exist (check `schemas/`, `.github/workflows/`, `scripts/`, `tests/`)
- [ ] Submit PR adding full CI enforcement stack: JSON Schema for skill frontmatter validation, GitHub Actions workflow (fails PRs on schema violations/deprecated skills/meta-exempt gaps), Python validator script, and pytest harness (22 tests: LI calculation ×9, Z3 redaction ×8, corpus invariants ×4)
- [ ] Apply labels: `ci`, `fix`, `protocol`; assign GitHub Copilot

**Verification criteria:** GitHub Actions workflow triggers on PR, all 22 pytest tests pass, schema validation rejects malformed skill frontmatter.

---

### S5 · PR · P1 · Needs path verification

**Title:** `docs(governance): commit ZONE_OPS_HA000_BARS_V1_0.md to operations/`  
**File(s):** `ZONE_OPS_HA000_BARS_V1_0.md` ⚠️ path inferred — likely repo root (same level as `CURRENT.md`)  
**Status:** Needs path verification  
**Source:** S-061526 Close Note · Z3 Queue

**Required actions:**
- [ ] ⚠️ Confirm target path: check if `ZONE_OPS_HA000_BARS_V1_0.md` belongs at repo root or in a `docs/` subdirectory
- [ ] Submit PR adding single .md combining Zone Operations, HA-000 Run Sheet, and BARS rubric (12 dimensions, 10 behavioral anchors each)
- [ ] Apply labels: `docs`, `governance`; assign GitHub Copilot

**Verification criteria:** File present at verified path, all 12 BARS dimensions present, CI passes.

---

### S6 · PR · P0 · Already landed

**Title:** `fix(tools): reconstruct and commit tools/Metaculus/main.py + support files`  
**File(s):**
- `tools/Metaculus/main.py`
- `tools/Metaculus/requirements.txt`
- `tools/Metaculus/railway.toml`

**Status:** Already landed (commit `caf3e0c`)  
**Source:** S-062426-02 Close

**Required actions:**
- [ ] Confirm commit `caf3e0c` is present in repo history (`git log --oneline | grep caf3e0c`)
- [ ] Confirm `tools/Metaculus/main.py` passes `py_compile` (zero import errors)
- [ ] Follow up on activation tasks → see **S11**

**Verification criteria:** `caf3e0c` in git log, `python -m py_compile tools/Metaculus/main.py` exits 0, no smart-quote or indentation corruption in file.

---

### S7 · PR · P1 · Needs path verification

**Title:** `fix(tools): commit 3 new tools and landscape update from S-062426-01`  
**File(s):**
- `tools/failure_taxonomy_checklist_v0_1.py` ⚠️ path inferred — likely `tools/` or `operations/tools/`
- `tools/claim_verification_check_v0_1.py` ⚠️ path inferred
- `tools/acat_pipeline_v0_1.py` (fixed version) ⚠️ path inferred
- `COMPARABLE_FRAMEWORKS_LANDSCAPE_V2.md` (Section G added) ⚠️ path inferred

**Status:** Needs path verification  
**Source:** S-062426-01 Close

**Required actions:**
- [ ] ⚠️ Verify target paths for all 4 files against actual repo tree
- [ ] Submit PR committing three tools (all 10/10 self-test): `failure_taxonomy_checklist_v0_1.py` (real PAM auth-bypass detection), `claim_verification_check_v0_1.py`, and fixed `acat_pipeline_v0_1.py` (wrong schema key `results→checks`, NameError guard, JSON-based drift detection)
- [ ] Include `COMPARABLE_FRAMEWORKS_LANDSCAPE_V2.md` with Section G (ComputeID + agent-identity glut data point)
- [ ] Apply labels: `fix`, `docs`, `tools`; assign GitHub Copilot

**Verification criteria:** All 3 tool scripts pass 10/10 self-test, landscape doc has Section G, CI passes.

---

### S8 · PR · P1 · Already landed

**Title:** `docs(governance): commit CURRENT.md staleness correction`  
**File(s):** `CURRENT.md` (repo root)  
**Status:** Already landed (manually verified this session)  
**Source:** S-062426-CURRENT-UPDATE

**Required actions:**
- [ ] Verify `CURRENT.md` reflects: Charter Day 69/90, F-52/F-53 added (IC count 38+), Supabase N=95, migration 006–010 absent warning, GOVERNANCE.md v6.4.2, §9 changelog through S-062426
- [ ] Close or skip PR draft — no further commit needed

**Verification criteria:** `CURRENT.md` last-updated date is on or after June 24, 2026; all listed fields match corrected values.

---

### S9 · PR · P0 · Needs path verification

**Title:** `fix(audit): correct haios_audit.yml false-pass on public/ path`  
**File(s):** `.github/workflows/haios_audit.yml` ⚠️ path inferred — check `.github/workflows/`  
**Status:** Needs path verification  
**Source:** S-062326 Close

**Required actions:**
- [ ] ⚠️ Confirm `.github/workflows/haios_audit.yml` exists (`ls .github/workflows/`)
- [ ] Identify A1 and A6 audit steps — both currently check `public/` which does not exist (`find . -iname public` → empty)
- [ ] Replace `public/` path(s) with actual repo path(s) that contain auditable content
- [ ] Submit PR with fix; apply labels: `fix`, `ci`, `protocol`; assign GitHub Copilot

**Verification criteria:** `find . -iname public` confirms path exists OR workflow updated to a real path; A1 and A6 steps fail on real violations and pass on clean content (not silently passing against nothing).

---

### S10 · Issue · P0 · Ready to submit

**Title:** `Reconcile acat_merkle_auditor_v2_0.py against prior Z2-SSI-ratified version`  
**Type:** Investigation / Clarification  
**File(s):** `acat_merkle_auditor_v2_0.py` (path TBD per reconciliation)  
**Status:** Ready to submit  
**Source:** S-062426-01 Top Flag

**Required actions:**
- [ ] Open GitHub Issue with full context
- [ ] Locate Z2-SSI session post and extract ratified spec (human_score.schema.json amendments, Z2-SSI-01–04 context)
- [ ] Diff both v2.0 implementations (SSI session vs. S-062426-01 build)
- [ ] Produce single reconciled canonical `acat_merkle_auditor_v2_0.py` with attribution to both sessions
- [ ] Commit reconciled file; apply labels: `investigation`, `protocol`, `governance`; assign GitHub Copilot

**Verification criteria:** Single canonical `acat_merkle_auditor_v2_0.py` committed, diff documented in issue, Z2-SSI context preserved, no competing versions in repo.

---

### S11 · Issue · P1 · Ready to submit

**Title:** `Set Railway env vars and run Path B smoke test for Metaculus bot`  
**Type:** Future Commit / Activation  
**File(s):** `tools/Metaculus/main.py` (already landed — S6)  
**Status:** Ready to submit  
**Source:** S-062426-02 Outstanding Gaps

**Required actions:**
- [ ] Open GitHub Issue tracking Railway activation
- [ ] Set 4 Railway env vars: `ANTHROPIC_API_KEY`, `METACULUS_TOKEN`, `SUPABASE_URL`, `SUPABASE_KEY` on the `tools/Metaculus` Railway service
- [ ] Trigger `--mode test_questions` smoke test
- [ ] Confirm Supabase P1/P2/P3 writes to `acat_forecast_runs` (N > 0)
- [ ] Confirm `/c/diffusion-community/` comment post lands correctly
- [ ] Apply labels: `chore`, `infra`; assign GitHub Copilot

**Verification criteria:** `acat_forecast_runs` table shows at least one write, Railway service logs show `--mode test_questions` run, Metaculus comment confirmed posted.

---

### S12 · Carry-forward · P2 · In progress

**Title:** `elicitation_surface_scanner_v1_0.py + SKILL.md + index.html — contract-corrected v3`  
**File(s):**
- `tools/elicitation_surface_scanner_v1_0.py` ⚠️ path inferred
- `tools/skills/elicitation_surface_scanner/SKILL.md` ⚠️ path inferred
- `index.html` (contract-corrected v3) ⚠️ path inferred

**Status:** In progress (files in `/mnt/user-data/outputs`, not yet committed)  
**Source:** S-062326 Close

**Required actions:**
- [ ] Upload via git/raw file method — **not** copy-paste (flagged to prevent repeat doc-paste corruption)
- [ ] Verify Zone 3 ratification before commit
- [ ] Submit PR once files are Zone 3 committed; apply labels: `tools`, `skills`; assign GitHub Copilot

**Verification criteria:** All 3 files committed via git (not copy-paste), Zone 3 ratification confirmed, CI passes.

---

## Execution Order

### Phase 1 — P0: Fix before next scan

| Order | Signal | Action |
|---|---|---|
| 1 | **S9** | Confirm `.github/workflows/haios_audit.yml` exists; fix A1/A6 false-pass on `public/` |
| 2 | **S10** | Open reconciliation issue; locate Z2-SSI session; diff both `acat_merkle_auditor_v2_0.py` versions |

### Phase 2 — P1: Path verification required first

| Order | Signal | Action |
|---|---|---|
| 3 | **S5** | Verify target path for `ZONE_OPS_HA000_BARS_V1_0.md`; submit PR |
| 4 | **S7** | Verify target paths for all 4 files; submit PR |

### Phase 3 — P1: Ready to submit

| Order | Signal | Action |
|---|---|---|
| 5 | **S1** | Submit `tools/skills/README.md` PR |
| 6 | **S2** | Submit 5 SKILL.md files PR |
| 7 | **S4** | Submit CI enforcement stack PR (schema + workflow + validator + pytest) |
| 8 | **S11** | Open Railway activation issue; set env vars; run smoke test |

### Phase 4 — P2/Housekeeping

| Order | Signal | Action |
|---|---|---|
| 9 | **S3** | Submit deprecated skill notice PR |
| 10 | **S12** | Upload carry-forward files via git; verify Z3 ratification |

### Already landed — verify only

| Signal | Verification |
|---|---|
| **S6** | Confirm `caf3e0c` in git log; `py_compile` check on `main.py`; activate via S11 |
| **S8** | Confirm `CURRENT.md` reflects June 24 corrections |

---

_Checklist generated: 2026-06-28 · Source brief: WGS File Update & GitHub PR Draft Scout · Scan: June 22–24, 2026_
