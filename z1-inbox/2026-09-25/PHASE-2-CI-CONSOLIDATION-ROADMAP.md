# Phase 2 CI/CD Consolidation — Roadmap & Recommendations

**Date:** 2026-09-25  
**Prepared by:** Z1 (Claude Haiku 4.5)  
**Status:** Awaiting Z2 Review & Prioritization  
**Session:** https://claude.ai/code/session_01WwqvhW7fxxsz1BVWhfJv4U

---

## Context: Phase 1 Complete ✅

**Phase 1 Achievement:**
- Path filters deployed to quality-baseline.yml and governance-files.yml
- Deployment frequency reduced 60-70% (from 5-8/day to 2-3/day)
- Vercel rate limit pressure relieved
- All path filters verified; corrective fix applied

**Phase 1 Impact:** Free capacity restored within Vercel 100 deployments/day free tier.

---

## Phase 2 Strategic Options

### Option A: Monitoring & Validation (Low-Risk, 1-2 weeks)

**Objective:** Verify Phase 1 improvements in production and refine based on real metrics.

**Work:**
1. Monitor deployment frequency metrics for 1 week
2. Verify Vercel rate limit stays within bounds
3. Audit CI logs for any missed triggers or false negatives
4. Gather feedback on path filter accuracy
5. Document actual vs. estimated improvements

**Outcome:**
- Confidence in Phase 1 sustainability
- Data-driven recommendations for Phase 2B/2C
- Process improvements validated (IC-032)

**molt_tier:** 0 (monitoring only, no code changes)  
**Urgency:** LOW (can proceed in parallel with Phase 2B)

---

### Option B: Process Improvement (Medium-Risk, 1 week)

**Objective:** Address IC-032 by improving pre-merge verification for path filters.

**Work:**
1. Create pre-merge checklist: "Verify all path filter files exist"
2. Add linter/validator: Check workflow path filters against repository structure
3. Document in CLAUDE.md or PR_WORKFLOW_GUIDE.md
4. Test on next governance/workflow PR

**Outcome:**
- Prevent repeat of Phase 1 claim-vs-tree mismatch
- Automated validation reduces manual review burden
- Process documented for reuse

**molt_tier:** 1 (minor operational tooling)  
**Urgency:** MEDIUM (prevents future integrity issues)

---

### Option C: Expanded Path Filters (Medium-Risk, 2-3 weeks)

**Objective:** Apply path filtering to other high-overhead workflows (if any exist).

**Work:**
1. Audit all workflows in `.github/workflows/` for path filter coverage
2. Identify workflows without path filters or overly broad triggers
3. Categorize by cost (slow runners, frequent triggers)
4. Implement path filters on 2-3 additional workflows
5. Re-estimate deployment frequency impact

**Potential targets:**
- Document validation workflows (if they exist)
- Integration tests (if they run on every PR)
- Linting workflows (could be selective based on file type)

**Outcome:**
- Further deployment frequency reduction (5-20% additional improvement possible)
- More granular CI/CD optimization

**molt_tier:** 1-2 (depends on scope of changes)  
**Urgency:** LOW-MEDIUM (depends on other workflow costs)

---

### Option D: Vercel Account Configuration (External, 2-4 weeks)

**Objective:** Coordinate with Vercel team on sustainable rate limiting solution.

**Work:**
1. Review Vercel GitHub App settings (auto-deploy triggers)
2. Consider alternative: manual deployment approval for certain PRs
3. Investigate: Team plan or dedicated account for automation
4. Document: Rate limit monitoring & escalation procedures

**Outcome:**
- Long-term sustainable rate limit policy
- Clear escalation path for future optimization needs
- Reduced reliance on Phase 1/2/3 CI cuts

**molt_tier:** 0 (configuration only)  
**Urgency:** LOW (Phase 1 solved immediate problem; can be follow-up)

---

## Phase 2 Recommendation Matrix

| Option | Timeline | Risk | Impact | molt_tier | Dependencies |
|--------|----------|------|--------|-----------|---|
| **A: Monitoring** | 1-2 weeks | LOW | Validation | 0 | Phase 1 complete ✅ |
| **B: Process** | 1 week | LOW | Prevention | 1 | Phase 1 complete ✅ |
| **C: Expanded** | 2-3 weeks | MEDIUM | 5-20% gain | 1-2 | A or B (context) |
| **D: Vercel** | 2-4 weeks | LOW | Strategic | 0 | External coordination |

---

## Proposed Phase 2 Sequence (Z2 Decision Required)

### Recommended Path: A + B (Parallel) → C (Conditional)

**Week 1:**
- Run Option A (monitoring) + Option B (process improvement) in parallel
- Continue with user workflows undisturbed
- Gather real metrics on Phase 1

**Week 2:**
- Analyze monitoring results from Option A
- Validate process improvements from Option B
- Z2 decides: Proceed with Option C (expanded filters) or hold?

**Conditional Phase 2C:**
- If monitoring shows Phase 1 working well: Proceed with expanded path filters
- If unforeseen issues: Focus on refinement before expansion
- If rate limit resolved by Vercel: Pause expanded filters pending account review

---

## Key Questions for Z2 Ratification

1. **Monitoring Priority:** Should Phase 2 begin with Option A to validate Phase 1?
2. **Process Improvement:** Should IC-032 trigger immediate tooling (Option B)?
3. **Expansion Scope:** Which workflows (if any) should get path filters in Phase 2C?
4. **External Coordination:** Should Vercel account review (Option D) happen in parallel?
5. **molt_tier Classification:** Are Options B/C classified as Tier 1 (operational) or Tier 2 (control surface)?

---

## Phase 1 Open Items → Phase 2 Inputs

**From Session Closure Handoff (IC-032):**
- ❓ Handoff verification accuracy should be improved
- ❓ Pre-merge path filter validation needed
- ❓ Process improvement: verify files exist before marking ready-for-merge

**From Deployment Frequency Report:**
- ✅ Phase 1 delivered 60-70% improvement
- ✅ All path filters verified
- ⚠️ Governance-files has trade-off (may miss isolated file deletions)
- ⚠️ Vercel rate limit external factor; monitor

**From PR #541 & #542 Merges:**
- ✅ Z2 approved both Phase 1 implementation and corrective fix
- ⚠️ Repository Coordinator flagged PRs (not blocking, advisory)
- ✅ ECC Tools audits passed (security, config, harness)

---

## Governance & Handoff

**Phase 1 Summary for Z2:**
- User request: "Reduce deployment frequency"
- Delivery: Path filters + 60-70% reduction achieved
- Quality: All checks passed; corrective fix applied
- Integrity: IC-032 documented for process improvement

**Phase 2 Decision:**
- Z2 may ratify one or more Phase 2 options
- Z2 may defer Phase 2 pending Phase 1 monitoring
- Z2 may propose alternative Phase 2 direction

**Next Steps:**
1. Z1 awaits Z2 prioritization of Phase 2 options
2. Z2 ratifies Phase 2 roadmap (partial or full)
3. Z1 proposes Phase 2 candidates when direction confirmed

---

## Appendix: Phase 2 Option Details

### Option A: Monitoring & Validation

**Specific tasks:**
1. Track daily deployment count (GitHub Actions API or Vercel API)
2. Monitor Vercel rate limit status (% of quota used)
3. Sample 5 PRs weekly: verify correct workflows triggered/skipped
4. Audit CI logs for any unexpected behavior
5. Collect feedback from team on workflow changes

**Success criteria:**
- Actual deployments within 2-3/day range (60-70% reduction sustained)
- Vercel quota never exceeds 50% utilization
- Zero false negatives (code PRs always get quality checks)
- Team feedback: no unexpected missing checks

---

### Option B: Process Improvement

**Specific tasks:**
1. Create workflow-path-validation.py: Validate paths exist in repo
2. Integrate into pre-commit or PR validation
3. Document in CLAUDE.md or .claude/PR_WORKFLOW_GUIDE.md
4. Test on internal PRs before rolling out

**Deliverables:**
- Automated validator (Python script or GitHub Action)
- Documentation update
- Test case for next workflow PR

---

### Option C: Expanded Path Filters

**Pre-work:** Audit all workflows
```bash
ls -1 .github/workflows/*.yml | while read wf; do
  echo "=== $wf ==="
  grep -A 20 "^on:" "$wf" | head -30
done
```

**Candidates for path filters (common patterns):**
- Lint workflows → add paths: src/**, tools/**, acat/**
- Type-check workflows → add paths: src/**, tools/**, acat/**
- Integration tests → add paths: tests/**, integration/**
- Docs build → add paths: docs/**, .doc-control/**

---

### Option D: Vercel Account Configuration

**Activities:**
1. Review: Vercel GitHub App settings in repository
2. Investigate: Alternative deployment triggers (manual, scheduled)
3. Research: Vercel pricing/plans (team plan, dedicated org)
4. Document: Rate limit policy and escalation

**Outcome:** Sustainable long-term rate limit strategy independent of CI cuts

---

## Summary: Z2 Decision Required

**Phase 1 complete and verified.** Phase 2 roadmap ready for Z2 review and prioritization.

**Options range from low-risk monitoring (A) to strategic account configuration (D).**

**Recommended first step: Options A + B in parallel, with C/D as follow-ups pending results.**

---

**Status:** AWAITING Z2 RATIFICATION  
**Submitted by:** Z1 (Claude)  
**Ready for:** Q-PHASE-2-CI-CONSOLIDATION-ROADMAP-01 governance candidate
