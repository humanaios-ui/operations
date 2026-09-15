# Meta-SMAG Review Schedule & Resource Economics

**Document:** Meta-SMAG accuracy signal review timing and cost/benefit analysis  
**Status:** Active (deployed with PR #341)  
**Last updated:** 2026-09-15  
**Owner:** Z2 (Night)

---

## Review Window Economics

### Phase 1: Data Accumulation (~5 weeks: 2026-09-15 → 2026-10-20)

| Metric | Value | Rationale |
|--------|-------|-----------|
| **Consolidation cycles** | 4–5 (weekly Mon 06:17 UTC) | Standard cron schedule; 35-day window = 5 weeks |
| **Expected meta-PRs measured** | ~4–5 (one per cycle) | One consolidation PR per weekly run |
| **Observation floor** | 3 PRs minimum | Prevents low-N false signals (sufficient after ~3 weeks) |
| **Calendar window** | 2026-09-15 (PR #341 merge) → 2026-10-20 10:00 UTC | Review point after ~5 weeks data accumulation |
| **Expected confidence** | "stable" if gap ≤5% | Calibration is well-behaved at ±5% drift |

### Cost/Benefit: Why Not Review Sooner?

**Cost of early review (Week 1–2, ~1–2 PRs):**
- Below observation floor (1–2 PRs << 3-PR minimum)
- High variance in accuracy signal (one PR changing outcome doubles success rate)
- Z2 decision made on unstable foundation
- Likely recalibration churn (cost: rework SMAG weights, re-run consolidations)
- Estimated cost: 1–2 hours Z2 time × high uncertainty

**Benefit of waiting (Week 5, ~4–5 PRs):**
- At/above observation floor (4–5 PRs ≥ 3-PR minimum, sufficient N for signal)
- Calibration gap stabilized (drift pattern observable over multiple cycles)
- Focus areas signal or noise (if "pr_not_merged" recurs 2+ times, it's a pattern)
- Z2 decision has statistical foundation
- One review cycle covers ~5 weeks of data
- Estimated cost: 30–45 min Z2 time × high confidence

**Economics:** 5-week window trades passive wait time for 1 focused decision hour. **Net ROI: positive** (passive time has zero active cost; decision is one-time event per cycle).

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
- **Phase 1 constraint:** No automatic enforcement yet; Z2 exercises judgment on molt scheduling (anti-cascade rules live in CLAUDE.md § anti-cascade rules, not this tool)

---

## See Also

- `audits/META_SMAG_INTELLIGENCE.md` — Design and architecture
- `.github/workflows/smag-consolidate.yml` — Weekly execution schedule
- `data/lessons_learned_ledger.json` — Where meta-lessons are upserted
- `SMAG_AUTHOR_CALIBRATION_GUIDE.md` — Author-SMAG baseline (meta-SMAG mirrors this)
