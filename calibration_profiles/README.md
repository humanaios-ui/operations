# Calibration Profiles — Recursive Learning Integration

**Purpose:** Per-substrate behavioral constraints derived from SMAG gap analysis and meta-feedback, wired into merge gates and Intent-OS runtime.

**Schema:** `WITNESS_STATE_V0_1.schema.json` (extended with `calibration_profile` property)

**Authority:** Z2 ratification required; profiles expire 90 days and require renewal.

---

## File Structure

- `BASELINE_S092126.json` — Phase 0 baseline profile (S-092126 ratification date)
  - Based on 126 historical PRs, 10 calibrated
  - Per-substrate rules: `human:humanaios-ui`, `Copilot`, `Claude`
  - Review bars, confidence weights, merge pause thresholds
  - Implementation checklist (CI wiring, Intent-OS binding, automation)

## Reading a Profile

```json
{
  "substrates": {
    "human:humanaios-ui": {
      "confidence_weight": 1.0,        // Proposal scope multiplier
      "review_bar": "standard",         // Pre-merge gate level
      "merge_pause_threshold": 0.25,   // Auto-pause if gap_rate > 25%
      "calibration_floor": 10,          // Min pinned predictions for credibility
      "measured_gap_rate": 0.1,         // Observed from gap analysis
      "next_review_date": "2026-10-21"  // Monthly refresh
    }
  }
}
```

## Lifecycle

1. **COLLECT** — SMAG ledger captures PR predictions/outcomes over 30 days
2. **ANALYZE** — `smag_gap_analysis_v1_0.py` runs monthly, produces gap_report
3. **PROPOSE** — `smag_feedback_v1_0.py` generates lessons, Z2 reviews
4. **RATIFY** — Z2 signs calibration profile update (this file family)
5. **WIRE** — CI/CD and Intent-OS bind to profile (merge gates, capability checks)
6. **MEASURE** — Next month's gap_rate compared to profile's merge_pause_threshold
7. **RENEW** — Profile expires after 90 days; Z2 re-ratifies or reverts to defaults

## Z2 Ratification Checklist

- [ ] Profile is signed with Z2 SHA256(profile | by=Night | at=timestamp | decision=ACCEPT)
- [ ] Authority basis links to Q-RECURSIVE-LEARNING-UPSTREAM-IMPACT-01 or equivalent
- [ ] Expiration date is ≤90 days from ratification_date
- [ ] Each substrate with measured data (≥calibration_floor PRs) has reviewed gap_rate
- [ ] merge_pause_threshold is calibrated to false-positive rate (not reactive to one-off gaps)
- [ ] Implementation checklist is assigned to Z3 executor with clear completion criteria

## Integration Points

### CI/CD (merge-gate.yml)
```yaml
- name: Apply calibration profile constraints
  run: |
    PROFILE=$(curl -s https://raw.githubusercontent.com/.../calibration_profiles/BASELINE_S092126.json)
    SUBSTRATE=$(git log -1 --format='%ae' | cut -d@ -f2)
    REVIEW_BAR=$(echo $PROFILE | jq ".substrates.\"$SUBSTRATE\".review_bar")
    # Enforce review_bar before merge approval
```

### Intent-OS (Phase 1)
```
GET /api/calibration-profiles/{substrate}
→ { "confidence_weight": 1.0, "review_bar": "standard", ... }

System uses this to gate proposal scope and review requirements before merge
```

### SMAG Automation (smag-consolidate.yml)
```yaml
- name: Update calibration profiles
  run: |
    python3 tools/smag_gap_analysis_v1_0.py
    python3 tools/smag_feedback_v1_0.py
    python3 tools/calibration_profile_generator.py  # (TBD: writes new profile PR)
```

---

## Example: Monthly Review & Renewal (Z2 Workflow)

**Month 1 (Current)**
- Ratify `BASELINE_S092126.json` (expires 2026-12-21)
- CI wires profile into merge gates
- SMAG collects calibration data

**Month 2 (2026-10-21)**
- `smag-consolidate.yml` runs, produces new gap_report
- Gap-driver analysis identifies any substrates needing adjustment
- Z2 reviews: "Copilot gap_rate rose from 0% to 0.15? Investigate or tighten review_bar."
- Z2 ratifies updated profile (or same profile renewed)
- If profile not renewed by 2026-12-21, CI reverts to default (confidence_weight=1.0, review_bar=standard)

---

## Historical Data & Backfilling

- `BASELINE_S092126.json` backfilled from 126 historical rows (S-070826 through S-092126)
- Only 10 rows carry pinned `smag_p:` predictions (IC-SMAG-01 VOID mitigation)
- Profile is credible but should be re-measured monthly as new calibration data accumulates
- Goal: Reach ≥20 pinned predictions per substrate per month for statistical confidence

---

See `data/lessons_learned_ledger.json` for lessonsby-data lineage.
