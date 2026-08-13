# Governance Unification — Execution Plan

**Decision:** GOV-2026-07-30-GOVERNANCE-UNIFICATION (Z2 RATIFIED)

**Timeline:**
- Phase 1 (Prep): 2026-08-01 to 08-07
- Phase 2 (Setup): 2026-08-08 to 08-14
- Phase 3 (Go Live): 2026-08-15 (all 10 practices simultaneously)

---

## Phase 1: Preparation (2026-08-01 to 08-07)

### Task 1.1: Circulate Proposal to Practice Leads
- Create GitHub discussion in each of 10 practice repos
- Post proposal + 3 design docs
- Request feedback (SLA: 48h)

### Task 1.2: Designate Z2 Authorities
- Create AUTHORITY_ASSIGNMENTS.yaml in operations repo
- Confirm each practice lead designates Z2 authority
- Confirm Admiral veto authority on all

### Task 1.3: Finalize Design Based on Feedback
- Review practice feedback
- Update design docs if needed (with Admiral sign-off)
- Confirm no blockers for Phase 2

---

## Phase 2: Setup (2026-08-08 to 08-14)

### Task 2.1: Deploy PR Template to All 10 Repos
- Create `.github/GOVERNANCE_PR_TEMPLATE.md` in each repo
- Create setup PR + merge

### Task 2.2: Set Up Branch Protection Rules
- Configure GitHub branch protection on `main` (require Z2 review)
- Create `.github/CODEOWNERS` in each repo
- Test branch protection

### Task 2.3: Deploy mesh-sync-batch Workflow
- Create `.github/workflows/mesh-sync-batch.yml` in operations repo
- Create `.github/workflows/mesh-sync-listen.yml` in each practice repo
- Test workflows

### Task 2.4: Deploy divergence-detect Workflow
- Create `.github/workflows/divergence-detect.yml` in operations repo
- Test consistency matrix generation

### Task 2.5: Train Practice Leads
- Create TRAINING_GUIDE.md in operations repo
- Optional: Slack call walkthrough

---

## Phase 3: Go Live (2026-08-15)

### Task 3.1: Merge Decision to Operations Repo
- Create PR: `[GOVERNANCE] RATIFIED: Unified PR Ratification Workflow`
- Merge immediately (Admiral approval secured)

### Task 3.2: Dispatch to All 10 Practices
- Trigger mesh-sync-batch workflow
- Dispatch GOV-2026-07-30-GOVERNANCE-UNIFICATION to all 10 practices

### Task 3.3: All Practices Merge Sync PR
- Each practice receives sync PR
- Practice lead reviews + approves (lightweight)
- Each practice merges sync PR

### Task 3.4: Verify Go-Live Status
- Check all 10 practice repos for merged sync PR
- Run divergence-detect manually
- Verify 100% consistency

---

## Success Metrics (30-day post-launch review, by 2026-09-15)

- ✅ 100% of practices have PR template deployed
- ✅ 100% of practices have branch protection rules active
- ✅ 0 governance PRs merged without Z2 approval
- ✅ 0 orphaned governance changes (all indexed in registry)
- ✅ 100% consistency on divergence-detect (all practices synced within 24h)
- ✅ At least 1-2 real governance changes flowed end-to-end
- ✅ No critical incidents or rollbacks
- ✅ Practice leads report workflow is usable

**If all 8 metrics pass:** Molt hardening phase complete, ready for M3 nervous system integration.
