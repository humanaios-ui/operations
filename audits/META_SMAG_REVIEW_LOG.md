# Meta-SMAG Accuracy Review Log

**Document:** Periodic reviews of SMAG's own calibration accuracy based on consolidation PRs.  
**Owner:** Z2 (Night)  
**Last updated:** 2026-10-20T10:01:27Z

---

## Review Checkpoint 1: 2026-10-20 (4-week window, 2026-09-21 → 2026-10-20)

**Trigger:** Scheduled checkpoint after PR #341 (meta-SMAG feedback loop deploy)  
**Schedule:** META_SMAG_REVIEW_SCHEDULE.md § Scheduled Review Checkpoint

### Data Collected

| PR | Title | Merged | smag_p_meta | Outcome | Accuracy |
|:---|:------|:-------|:-----------|:--------|:---------|
| #432 | SMAG: consolidate ledger + refresh gap report | ✅ 2026-09-21 | 0.85 | ✅ Success | Correct |
| #573 | SMAG: consolidate ledger + refresh gap report | ✅ 2026-10-01 | 0.85 | ✅ Success | Correct |

**Total observations:** 2 PRs  
**Observation floor:** 3 PRs (minimum for stable signal per schedule)  
**Data sufficiency:** BELOW FLOOR

### Missing Data

Expected consolidation PRs (weekly Mon 06:17 UTC):
- Week 1 (2026-09-15 ~ 2026-09-22): ✅ PR #432 (2026-09-21)
- Week 2 (2026-09-22 ~ 2026-09-29): ❌ **Missing** (expected ~2026-09-29)
- Week 3 (2026-09-29 ~ 2026-10-06): ✅ PR #573 (2026-10-01)
- Week 4 (2026-10-06 ~ 2026-10-13): ❌ **Missing** (expected ~2026-10-13)
- Week 5 (2026-10-13 ~ 2026-10-20): ❌ **Missing** (expected ~2026-10-20)

### Confidence Assessment

| Dimension | Finding |
|:----------|:--------|
| **Accuracy measured** | 2/2 correct (100% on observed PRs) |
| **Accuracy confidence** | `insufficient_data` — below 3-PR floor |
| **Focus areas** | None (sample too small for pattern analysis) |
| **Calibration stability** | Cannot assess (need ≥3 observations) |
| **Recommendation** | Extend window 2 more weeks (until 2026-11-03) |

### Root Cause: Missing Consolidation Runs

**Hypothesis:** Consolidation workflow did not execute on schedule in weeks 2, 4, 5.

**Action needed (Z2/Z3):** 
1. Check `.github/workflows/smag-consolidate.yml` execution history
2. If workflow failed: diagnose and fix root cause
3. If workflow was skipped/not triggered: verify cron or trigger manually
4. Once fixed: re-trigger missing consolidation PRs or wait for next scheduled runs

**Data recovery:** Could manually run `workflow_dispatch` for missed weeks if needed.

### Decision Recommendation

**Per META_SMAG_REVIEW_SCHEDULE.md § When to Review Early (Override):**

Condition: `Zero PRs measured` (interpreted as <3 PRs) → Check workflow health  
Status: ✅ Applicable

**Recommended action:**
- ✅ Extend window 2 more weeks (until ~2026-11-03) to accumulate ≥3 observations
- ⚠️ Investigate why weeks 2, 4, 5 consolidations didn't produce PRs
- ↻ Re-run this review on 2026-11-03 with full 4-week sample (expected 4-5 PRs)

---

## Governance Reference

**Authority:** Z2 ratifies meta-SMAG accuracy interpretation and weighting adjustments  
**Related files:**
- `META_SMAG_REVIEW_SCHEDULE.md` — Review window economics and thresholds
- `.github/workflows/smag-consolidate.yml` — Consolidation workflow schedule (Mon 06:17 UTC)
- `data/lessons_learned_ledger.json` — Upserts SMAG-META-CALIBRATION-SELF-ACCURACY entry

**Confidence threshold for decision:** ≥3 observations, or <0.60 accuracy if observed  
**Current status:** Window extension recommended (2026-10-20 → 2026-11-03)

---

## Next Checkpoint

**Scheduled:** 2026-11-03 (extended window, ~6 weeks total data)  
**Expected data:** 4-5 consolidation PRs with smag_p_meta predictions  
**Expected confidence:** "stable" (sufficient for Z2 decision on weighting/recalibration)

