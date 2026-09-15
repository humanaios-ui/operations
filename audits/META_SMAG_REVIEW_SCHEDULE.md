# Meta-SMAG Review Schedule & Resource Economics

**Document:** Meta-SMAG accuracy signal review timing and cost/benefit analysis  
**Status:** Active (deployed with PR #341)  
**Last updated:** 2026-09-15  
**Owner:** Z2 (Night)

---

## Review Window Economics

### Phase 1: Data Accumulation (Weeks 1–4)

| Metric | Value | Rationale |
|--------|-------|-----------|
| **Consolidation cycles** | 4 (weekly Mon 06:17 UTC) | Minimum for statistical significance |
| **Expected meta-PRs measured** | 12–20 (3–5 per cycle) | Phase 1 consolidation frequency |
| **Observation floor** | 3 PRs minimum | Prevents low-N false signals |
| **Calendar window** | 2026-09-22 → 2026-10-20 | 4 weeks post-merge |
| **Expected confidence** | "stable" if 0.75–0.95 | Indicates normal operation |

### Cost/Benefit: Why Not Review Sooner?

**Cost of early review (Week 1–2):**
- Insufficient data (1–2 consolidation cycles = 3–6 PRs)
- High variance in accuracy signal (may flip 0.7 → 0.9 → 0.6 in next cycle)
- Z2 decision made on unstable foundation
- Likely recalibration churn (cost: rework SMAG weights, re-run consolidations)
- Estimated cost: 1–2 hours Z2 time × high uncertainty

**Benefit of waiting (Week 4):**
- 12–20 observations (above floor by 4–7×)
- Stable confidence label ("stable" if truly 0.75–0.95)
- Focus areas stabilized (if "pr_rework_needed" recurs 3+ times, it's a signal)
- Z2 decision has statistical foundation
- One review cycle covers 4 weeks of data
- Estimated cost: 30–45 min Z2 time × high confidence

**Economics:** 4-week window trades 4–8 hours of Z2 wait time for 1–1.5 hours of higher-confidence decision-making. **Net ROI: positive** (wait time is passive; decision time is active).

### When to Review Early (Override)

Skip the 4-week window if:
- **Revert signal detected** (consolidation PR reverted after merge) → Review immediately
- **Focus area spike** (same failure 2+ times in weeks 1–2) → Escalate to Z2
- **High accuracy drop** (observed <0.60 in first cycle) → Trigger emergency review
- **Zero PRs measured** (no consolidation activity) → Check workflow health

---

## Scheduled Review Checkpoint

**Automatic check-in:** 2026-10-20 at 10:00 UTC (end of Week 4)

**Check-in prompt:**
```
Review meta-SMAG accuracy signals accumulated over 4 consolidation cycles (2026-09-22 → 2026-10-20).

Required actions:
1. Read latest entry in data/lessons_learned_ledger.json (SMAG-META-CALIBRATION-SELF-ACCURACY)
2. Extract: accuracy_measured, confidence, total_prs_measured, focus_areas
3. Assess Z2 decision: maintain calibration, adjust weighting, or trigger smag-retrain
4. Document decision in audits/META_SMAG_REVIEW_LOG.md (append)
5. If confidence = "insufficient_data": extend window 2 more weeks
```

**Review scope:**
- Is SMAG's accuracy stable (0.75–0.95)?
- Are focus areas noise or signal?
- Should SMAG's gap-driver weighting change?
- Should other tools' predictions be adjusted?

---

## Governance Reference

This schedule implements:
- **CLAUDE.md § Callout Mandatory Triggers:** GAUGE (Z3 assumption violation) and DRIFT (behavior dial change)
- **Z2 decision window:** 48h for routine (meta-accuracy is advisory, so async review ok)
- **Anti-cascade rules:** No new molt inside this observation window (4 weeks is hardcoded in META FEED BACK)

---

## See Also

- `audits/META_SMAG_INTELLIGENCE.md` — Design and architecture
- `.github/workflows/smag-consolidate.yml` — Weekly execution schedule
- `data/lessons_learned_ledger.json` — Where meta-lessons are upserted
- `SMAG_AUTHOR_CALIBRATION_GUIDE.md` — Author-SMAG baseline (meta-SMAG mirrors this)
