# Phase 2A: Monitoring & Validation — Implementation Plan

**Status:** IN PROGRESS  
**Start Date:** 2026-09-25  
**Duration:** 1-2 weeks  
**molt_tier:** 0 (monitoring only, no code changes)

---

## Objective

Validate Phase 1 deployment frequency improvements in production and capture behavioral data to inform Phase 2C/2D decisions.

---

## Monitoring Tasks

### Task 1: Daily Deployment Count Tracking

**Metric:** Total deployments/day (Vercel + GitHub Actions)

**Collection method:**
- GitHub Actions API: Count workflow runs per day
- Vercel webhook or API: Count deployments per day
- Combine for total deployment frequency

**Target baseline:** 2-3 deployments/day (60-70% reduction from 5-8/day)

**Duration:** 7 consecutive days (2026-09-25 to 2026-10-02)

**Data format:**
```
Date       | GH Actions Runs | Vercel Deploys | Total | Target? |
2026-09-25 |        3        |       2        |   5   | ✅      |
2026-09-26 |        2        |       1        |   3   | ✅      |
...
```

---

### Task 2: Vercel Quota Utilization

**Metric:** % of 100 deployments/day free tier used

**Collection method:**
- Check Vercel project settings daily
- Track cumulative deployments for the day
- Alert if > 50% quota used (triggers Phase 2D escalation)

**Target:** Stay < 50% utilization (leave headroom for urgent deploys)

**Duration:** Entire monitoring period (7 days)

**Data captured:**
- Date
- Deployments used
- % of 100-deployment quota
- Peak usage time
- Any quota warnings/errors

---

### Task 3: Workflow Trigger Accuracy (Sample-based)

**Metric:** Do path filters trigger/skip correctly?

**Method:** Select 5 PRs weekly; verify each workflow triggered appropriately

**Test cases:**
```
PR Type          | Expected Quality | Expected Gov | Actual Q | Actual G | ✅/❌ |
Code PR          | ✅ RUN           | ❌ SKIP      | RUN      | SKIP     | ✅    |
Governance PR    | ❌ SKIP          | ✅ RUN       | SKIP     | RUN      | ✅    |
Doc-only PR      | ❌ SKIP          | ❌ SKIP      | SKIP     | SKIP     | ✅    |
Dependency PR    | ✅ RUN           | ❌ SKIP      | RUN      | SKIP     | ✅    |
Workflow change  | ✅ RUN           | ✅ RUN       | RUN      | RUN      | ✅    |
```

**Duration:** Sample 5 PRs each week for 2 weeks (10 total samples)

**False negatives:** Critical to catch (code PR without quality check)  
**False positives:** Acceptable (unnecessary check is better than missing one)

---

### Task 4: CI Log Audit for Unexpected Behavior

**Metric:** Any skipped checks that should have run?

**Method:**
- Review GitHub Actions logs weekly
- Search for "Path filter excluded" or similar messages
- Flag any cases where a check didn't run when it should have

**Duration:** Weekly audit, 2 weeks total

**Red flags to catch:**
- Quality check skipped on code change
- Governance check skipped on `.gov-control/` change
- Workflow checks skipped on workflow change

---

### Task 5: Behavioral Data Capture

**Metric:** How are developers using the new workflow triggers?

**Collection method:**
- Gather PR metadata: title, description, files changed
- Track which workflows ran for each PR
- Correlate PR intent with actual trigger behavior
- Identify patterns (e.g., "docs-only PRs consistently skip quality checks as expected")

**Data captured per PR:**
```json
{
  "pr_number": 543,
  "pr_title": "docs: update README",
  "files_changed": ["README.md", "docs/guide.md"],
  "workflows_triggered": ["governance-files"],
  "workflows_skipped": ["quality-baseline"],
  "developer_intent": "documentation-only",
  "accuracy": "MATCH (expected both skipped, got governance triggered)"
}
```

**Duration:** Collect for all PRs during 2-week monitoring period

**Purpose:** Identify edge cases or unexpected workflow usage

---

## Reporting Schedule

**Daily (end of day UTC):**
- Deployment count update
- Vercel quota status
- Any urgent issues flagged

**Weekly (Friday 5pm UTC):**
- Deployment frequency summary (cumulative + daily average)
- Workflow trigger accuracy report (sample results)
- CI log audit findings
- Behavioral data trends
- Data points collected this week: N

**Final Report (2 weeks):**
- Phase 1 impact validation (actual vs. estimated)
- Confidence level in sustained improvement
- Edge cases identified
- Recommendations for Phase 2C/D
- Full behavioral dataset for governance review

---

## Success Criteria

✅ **Deployment frequency:** Sustained at 2-3/day (±20% variance acceptable)  
✅ **Vercel quota:** Never exceed 50% utilization on any single day  
✅ **Workflow accuracy:** 100% of sampled PRs trigger correct workflows (≥95% acceptable)  
✅ **False negatives:** Zero code PRs without quality checks  
✅ **Behavioral data:** Collected on ≥90% of PRs during period  

---

## Blockers & Dependencies

- **Dependency:** Phase 1 already merged (commit ec544e5)
- **Dependency:** Real PR activity (minimum 3-5 PRs/day for meaningful data)
- **External:** Vercel API access (check credentials)
- **External:** GitHub Actions API access (check token)

---

## Deliverables

1. **Daily deployment tracking spreadsheet** (or CSV in z1-inbox/)
2. **Weekly monitoring report** (3 reports: Week 1, Week 2, Final)
3. **Workflow trigger accuracy audit** (10 sample PRs tested)
4. **Behavioral data export** (JSON or CSV with all PR metadata)
5. **Final validation report** (Phase 1 impact confirmed + Phase 2C/D recommendations)

---

## Timeline

- **2026-09-25:** Monitoring setup + Task 1-5 start
- **2026-09-29:** First weekly report (Week 1 data)
- **2026-10-02:** Final report + Phase 2C/D recommendation

**Go/No-Go Decision:** 2026-10-02 (Z2 decides Phase 2C expansion based on data)

---

## Integration with Phase 2B

Option B (Process Improvement) runs in parallel. Option A data informs whether Option B's validator is catching real issues.

**Handoff:** Phase 2A reports will show if any workflow trigger edge cases were missed, which validates Option B's need for automated path filter validation.

---

**Status:** READY TO START  
**Awaiting:** Z2 approval to proceed (or user approval for immediate start)  
**molt_tier:** 0 (no governance changes, monitoring only)
