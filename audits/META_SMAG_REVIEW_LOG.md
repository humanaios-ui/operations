# Meta-SMAG Accuracy Review Log

**Document:** Periodic reviews of SMAG's own calibration accuracy based on consolidation PRs.  
**Owner:** Z2 (Night)  
**Last updated:** 2026-10-20T10:01:27Z

---

## Review Checkpoint 1: 2026-10-20 (4-week window, 2026-09-21 → 2026-10-20)

**Trigger:** Scheduled checkpoint after PR #341 (meta-SMAG feedback loop deploy)  
**Schedule:** META_SMAG_REVIEW_SCHEDULE.md § Scheduled Review Checkpoint

### Data Collected

| PR | Title | Status | smag_p_meta | Outcome | Accuracy |
|:---|:------|:-------|:-----------|:--------|:---------|
| #432 | SMAG: consolidate ledger + refresh gap report | ✅ Merged (2026-09-21) | 0.85 | ✅ Success | Correct |
| #573 | SMAG: consolidate ledger + refresh gap report | ✅ Merged (2026-10-01) | 0.85 | ✅ Success | Correct |
| #724 | SMAG: consolidate ledger + refresh gap report | 🔄 Open (since 2026-10-05) | 0.85 | ⏳ Pending | Awaiting merge |
| #817 | SMAG: consolidate ledger + refresh gap report | 🔄 Open (since 2026-10-12) | 0.85 | ⏳ Pending | Awaiting merge |
| #931 | SMAG: consolidate ledger + refresh gap report | 🔄 Open (since 2026-10-19) | 0.85 | ⏳ Pending | Awaiting merge |

**Resolved observations:** 2 PRs (merged, measurements complete)  
**Pending observations:** 3 PRs (open, outcomes unresolved)  
**Observation floor:** 3 PRs (minimum for stable signal per schedule)  
**Data sufficiency:** 2 resolved < 3-PR floor; 3 pending may resolve before 2026-11-03

### Weekly Consolidation Cycle Inventory

Expected consolidation PRs (weekly Mon 06:17 UTC; grouped by listed opening date):
- 2026-09-21: ✅ PR #432 (merged 2026-09-21)
- 2026-09-28: ✅ PR #573 (merged 2026-10-01)
- 2026-10-05: 🔄 PR #724 (status: open)
- 2026-10-12: 🔄 PR #817 (status: open)
- 2026-10-19: 🔄 PR #931 (status: open)

Workflow execution status for any unobserved run remains unverified pending history inspection.

### Confidence Assessment

| Dimension | Finding |
|:----------|:--------|
| **Observed resolved merge fraction** | 2/2 (100% among resolved, not independently verified rework-free success) |
| **Accuracy confidence** | `insufficient_data` — below 3-PR floor |
| **Focus areas** | None (sample too small for pattern analysis) |
| **Calibration stability** | Cannot assess (need ≥3 observations) |
| **Recommendation** | Extend window 2 more weeks (until 2026-11-03) |

### Open Question: Week 2 Consolidation Status

**Uncertainty:** Week 2 produced PR #573, later merged on October 1. Whether the scheduled workflow ran at its expected time remains unverified; weeks 3–5 produced open PRs.

**Action needed (Z2/Z3):** 
1. Check `.github/workflows/smag-consolidate.yml` execution history for week 2
2. If workflow failed: diagnose and fix root cause
3. If workflow was skipped/not triggered: investigate cron before any authorized prospective rerun; never backdate evidence
4. Track merge of PRs #724, #817, #931 before extended deadline (2026-11-03)

**Data recovery:** A new workflow_dispatch is not evidence of the historical week 2 execution.

### Decision Recommendation

**Per META_SMAG_REVIEW_SCHEDULE.md § When to Review Early (Override):**

Condition: `Zero PRs measured` (no consolidation activity) → Check workflow health  
Status: ❌ Not applicable (2 PRs measured)

**Recommended action:**
- ✅ Extend window 2 more weeks (until ~2026-11-03) to accumulate ≥3 observations
- ⚠️ Verify week 2 workflow scheduling separately; monitor the open PRs #724, #817, #931
- ↻ Re-run this review on 2026-11-03 with extended lookback (outcome sample size remains unknown)

---

## Governance Reference

**Authority:** Z2 ratifies meta-SMAG accuracy interpretation and weighting adjustments  
**Related files:**
- `META_SMAG_REVIEW_SCHEDULE.md` — Review window economics and thresholds
- `.github/workflows/smag-consolidate.yml` — Consolidation workflow schedule (Mon 06:17 UTC)
- `data/lessons_learned_ledger.json` — Updates SMAG-META-CALIBRATION-SELF-ACCURACY entry (latest accuracy checkpoint)

**Confidence threshold for decision:** ≥3 observations, or <0.60 accuracy if observed  
**Current status:** Window extension recommended (2026-10-20 → 2026-11-03)

---

## Next Checkpoint

**Scheduled:** 2026-11-03 (extended window, ~6 weeks total data)  
**Expected data:** Up to five identified PRs; pending outcomes cannot be assumed resolved  
**Expected confidence:** "stable" requires a gap ≤5% **and** independently verified resolved observations meeting the floor; otherwise insufficient_data

