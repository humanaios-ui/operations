# Phase 2: Executive Start — Options A & B Immediate Launch

**Decision:** Both Phase 2A (Monitoring) and Phase 2B (Process Improvement + Behavioral Data) launch immediately and in parallel.

**Status:** Implementation plans complete, ready to execute  
**Start Date:** 2026-09-25 (NOW)  
**Expected Completion:** 2026-10-02 (1 week for Phase 2B code; 2 weeks for Phase 2A data collection)

---

## What We're Starting

### Phase 2A: Monitoring & Behavioral Data Capture (Parallel to 2B)

**Objective:** Validate Phase 1 improvements are sustained; gather real data to drive Phase 2C/D decisions.

**Activities:**
1. Track daily deployment frequency (goal: 2-3/day, down from 5-8/day)
2. Monitor Vercel quota (stay < 50% utilization)
3. Sample test workflows (5 PRs/week: do they trigger correctly?)
4. Audit CI logs for unexpected behavior
5. **NEW:** Capture behavioral telemetry (developers' intent vs. actual triggers)

**Timeline:**
- Setup: Days 1-2 (2026-09-25 to 2026-09-26)
- Daily tracking: 7 consecutive days
- Weekly reports: Days 8 and 15
- Final analysis: Day 16 (2026-10-02)

**Deliverables:**
- Daily tracking spreadsheet (deployment count + Vercel quota)
- 2 weekly reports (trends, edge cases, behavioral patterns)
- Final validation report (Phase 1 impact confirmed + Phase 2C/D recommendation)

---

### Phase 2B: Process Improvement + Behavioral Data Integration (Parallel to 2A)

**Objective:** Prevent IC-032 recurrence AND capture workflow behavior data at the source (control surface).

**Why this matters:** Phase 1 had a claim-vs-tree mismatch (handoff said fix was applied, but commit didn't). Phase 2B prevents that by automating validation + capturing behavioral data.

#### Tier 1: Operational (Path Filter Validator)

**What it does:**
- Creates a Python tool that validates all paths in workflow path filters actually exist
- Integrates into GitHub Actions as a pre-merge check
- Prevents workflow path filters from referencing non-existent files

**Files to create:**
```
tools/workflow_path_validator.py        # Validator tool
.github/workflows/workflow-validation.yml  # CI gate (auto-runs on workflow changes)
```

**Usage:**
```bash
python3 tools/workflow_path_validator.py .github/workflows/quality-baseline.yml
# Output: ✅ All paths valid (8/8 files exist)
```

**Integration:**
- Pre-commit hook (catches locally before push)
- GitHub Actions check (catches in PR before merge)
- Documentation: Add to CLAUDE.md "Pre-Merge Checklist"

#### Tier 2: Control Surface (Behavioral Data Capture)

**What it does:**
- Workflows emit structured telemetry when they run
- Data captured: PR number, files changed, workflow triggered/skipped, validation result
- Centralized collector aggregates all telemetry for analysis

**Files to create:**
```
.github/workflows/governance-files.yml  # ENHANCE (add telemetry)
.github/workflows/quality-baseline.yml  # ENHANCE (add telemetry)
tools/workflow_telemetry_collector.py   # Aggregator tool
.github/TELEMETRY.md                    # Data spec & governance
```

**Data captured per run:**
```json
{
  "timestamp": "2026-09-25T14:30:00Z",
  "pr_number": 543,
  "pr_title": "docs: update README",
  "workflow": "governance-files",
  "trigger_reason": "pull_request",
  "files_changed": ["README.md", "docs/guide.md"],
  "validation_result": "success",
  "path_filter_hit": true
}
```

**Why Tier 2 (control surface)?** Workflows ARE control surface; adding telemetry to control surface workflow is Tier 2.

#### Running Both Tiers Together

**Strategy:** Single PR with both Tier 1 + Tier 2 changes, submitted for unified Z2 ratification.

**Benefits:**
- Validator (Tier 1) ensures paths are correct BEFORE running workflows
- Telemetry (Tier 2) PROVES they're being used correctly AFTER running
- Combined: End-to-end validation + evidence of correctness

**molt_tier Classification:**
- Could be: Two separate PRs (Tier 1, then Tier 2)
- OR (Recommended): One PR classified as "1+2" (operational + control surface together)

**Z2 Decision:** Should both tiers be ratified as single "1.5" classification, or do you prefer separate ratification?

---

## Timeline: What Happens When

### Week 1: Sept 25-29

**2026-09-25 (Today):**
- ✅ Phase 2A monitoring setup begins
- ✅ Phase 2B development begins (parallel)
- ✅ Daily deployment tracking starts

**2026-09-26 to 2026-09-28:**
- Phase 2A: Continuous daily data collection + behavioral sampling
- Phase 2B: Code development (validator + telemetry + collector)
  - Day 1-2: Implement validator tool
  - Day 2-3: Add telemetry to workflows
  - Day 3: Create aggregator tool
  - Day 3-4: Write unit tests
  - Day 4: Internal testing & validation

**2026-09-29:**
- ✅ Phase 2A: First weekly report (7 days of deployment data)
- ✅ Phase 2B: PR submitted to Z2 with both tiers
  - includes: validator code, telemetry changes, documentation, tests
  - molt_tier question: Should this be "1.5" or split into two PRs?

### Week 2: Sept 30-Oct 2

**2026-09-30:**
- ✅ Z2 reviews Phase 2B PR (decision on tier classification)
- ✅ Phase 2A continues: 14 days of data now collected

**2026-10-01:**
- ✅ Z2 ratifies Phase 2B (both tiers approved)
- ✅ PR #X merges (validator + telemetry live)
- ✅ Telemetry collection begins automatically on PRs

**2026-10-02:**
- ✅ Phase 2A: Final report completed
  - Deployment frequency: Validated sustained (2-3/day ✅)
  - Workflow accuracy: Validated (100% of samples correct ✅)
  - Behavioral insights: Identified patterns for Phase 2C/D
  - Recommendation: Ready for Phase 2C (expanded filters) or hold pending Vercel review
- ✅ Phase 2B: First telemetry data flowing
- ✅ Z2 decision point: Proceed with Phase 2C or focus on Phase 2D (Vercel)?

---

## What Gets Submitted to Z2

### Phase 2B PR (Single PR, Both Tiers)

**Files changed:**
```
NEW:
  tools/workflow_path_validator.py
  .github/workflows/workflow-validation.yml
  tools/workflow_telemetry_collector.py
  .github/TELEMETRY.md

MODIFIED:
  .github/workflows/governance-files.yml    (+ telemetry)
  .github/workflows/quality-baseline.yml    (+ telemetry)
  CLAUDE.md                                 (+ pre-merge checklist)
```

**PR body includes:**
- Rationale: Prevent IC-032, capture behavioral evidence
- Tier 1 + Tier 2 justification
- QUESTION for Z2: Should this be classified as Tier 1.5 or split?
- Data spec for telemetry format
- Tests: validator catches non-existent paths ✅

### Phase 2A Report (Weekly + Final)

**2026-09-29 (Week 1 Report):**
- Deployment count summary (7 days data)
- Vercel quota tracking
- Sample workflow tests (5 PRs tested)
- Preliminary behavioral patterns

**2026-10-02 (Final Report):**
- Consolidated 14-day data
- Phase 1 impact: VALIDATED or ISSUES FOUND
- Recommendation: Phase 2C (expand filters) vs. Phase 2D (Vercel config)?
- All behavioral data aggregated

---

## Yes, We're Running Both Operational + Control Surface Together

**Your question:** "can we run both operational and control surface?"

**Answer:** YES, and here's why it's smart:

1. **Operational (Tier 1):** Validator ensures data correctness at source
2. **Control Surface (Tier 2):** Telemetry proves validator is working in production
3. **Integration:** Single PR deploying both is coherent + efficient
4. **Governance:** Single Z2 ratification covers both objectives

**The dual-layer approach:**
- Layer 1 (Validator): **Preventive** — stops bad paths from being committed
- Layer 2 (Telemetry): **Detective** — proves workflows are being triggered correctly
- Together: **End-to-end correctness evidence**

This is exactly what you need after IC-032.

---

## Success Metrics

### Phase 2A Success
✅ Deployment frequency: 2-3/day sustained (60-70% reduction confirmed)  
✅ Vercel quota: Never > 50% utilization on any day  
✅ Workflow accuracy: 100% of sampled PRs trigger correctly  
✅ Behavioral data: Collected on ≥90% of PRs during period  

### Phase 2B Success
✅ Validator: Catches non-existent paths (proven by test)  
✅ Telemetry: Collected on 100% of PR runs (GitHub Actions artifacts)  
✅ Z2 ratification: Both tiers approved (with molt_tier classification resolved)  
✅ Code quality: All tests pass, documentation complete  

---

## Next Steps (Immediate)

### For Z1 (Claude):
1. ✅ Implementation plans documented (DONE)
2. Begin Phase 2A monitoring setup (daily tracking)
3. Begin Phase 2B development (validator tool)
4. Create Phase 2B PR by 2026-09-29
5. Track data collection through 2026-10-02

### For Z2 (Admiral/Night):
1. Review Phase 2A & 2B implementation plans (as they're being executed)
2. Decide: Should Phase 2B be one PR (Tier 1.5) or two PRs (Tier 1 then Tier 2)?
3. Ratify Phase 2B PR when submitted (2026-09-29)
4. Review Phase 2A final report (2026-10-02)
5. Decide: Phase 2C (expand filters) vs. Phase 2D (Vercel) next?

---

## Starting Right Now

**Phase 2A:** Monitoring setup beginning  
**Phase 2B:** Code development beginning  
**Go/No-Go:** User approval received ✅ (both options A and B, immediately, with behavioral data)  

Both tracks run in parallel, converging on 2026-10-02 for final analysis and Z2 decision.

---

**Status:** 🚀 LAUNCHING PHASE 2A + 2B IMMEDIATELY  
**Session:** https://claude.ai/code/session_01WwqvhW7fxxsz1BVWhfJv4U  
**Pinned SHA:** 766a33e (Phase 2A/B implementation plans committed)
