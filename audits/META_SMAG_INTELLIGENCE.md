# Meta-SMAG: Wiring SMAG's Self-Accuracy Measurement

**Status:** Deployed S-091526  
**Integration:** Runs within `smag-consolidate.yml` after FEED BACK completes  
**Purpose:** Measure SMAG's own calibration accuracy; close the loop on SMAG's own learning

---

## The Problem: Recursive Learning Without Self-Measurement

The standard SMAG loop measures **author calibration** — how well PR authors predict their own outcomes:

```
Author prediction (smag_p) vs Actual outcome (merged/checks) → gap_rate → lessons
```

But SMAG itself—the system that consolidates, analyzes, and feeds back—has no signal on its own accuracy. SMAG emits consolidation PRs (weekly, via `smag-consolidate.yml`), but those PRs are never scored against SMAG's own predictions. This is a missed opportunity for recursion:

> If SMAG can measure author calibration, why can't SMAG measure *its own* calibration?

Meta-SMAG closes this loop.

---

## Four Meta-Stages (Recursive Layer)

| Stage | Mechanism | Signal |
|---|---|---|
| **PREDICT (Meta)** | SMAG pins `smag_p_meta` on consolidation PRs before merge | Predicted accuracy of consolidation |
| **CAPTURE (Meta)** | Consolidation PRs merge; CI checks run | Actual merge outcome |
| **ANALYZE (Meta)** | `tools/smag_meta_feedback_v1_0.py` measures: did consolidation PRs succeed? | Meta-gap = predicted - actual |
| **FEED BACK (Meta)** | Upsert meta-lessons to `data/lessons_learned_ledger.json` | SMAG confidence weighting for next cycle |

### How It Wires Into the Workflow

After `smag-consolidate.yml` completes the standard FEED BACK step (gap cues → lessons):

```yaml
# smag-consolidate.yml
- name: FEED BACK — gap cues into the lessons ledger
  run: python3 tools/smag_feedback_v1_0.py ...
  
- name: META FEED BACK — measure SMAG's own consolidation accuracy
  run: python3 tools/smag_meta_feedback_v1_0.py ...
  # Measures: how accurate was SMAG this week?
  # Feeds back: meta-lesson to lessons_learned_ledger.json
```

---

## Pinning smag_p_meta: SMAG's Self-Prediction

Before a consolidation PR merges, SMAG must pin a **self-confidence** score (`smag_p_meta`):

```markdown
## Prediction (SMAG calibration)

smag_p: 0.85  # (authors' predictions, backfilled)
smag_p_meta: 0.82  # (SMAG's self-confidence in this consolidation)

Why 0.82?
- Ledger dedup is mechanical (high confidence)
- Gap-report regeneration is mechanical (high confidence)
- Lessons upsert is mechanical (high confidence)
- BUT: schema changes to ledger format are risky (one typo breaks parsing)
- AND: if reconciling prior run's partial state, edge cases possible
→ Discount to 0.82 to account for schema/edge-case risk
```

Scoring guide for `smag_p_meta`:

- **0.90+:** No new schema changes; ledger dedup only; routine reports
- **0.80–0.89:** Minor schema update; one new cue type; careful testing done
- **0.70–0.79:** Larger schema overhaul; new tool in the pipeline; fallback paths untested
- **0.50–0.69:** Risky API change; untested empirica integration; one edge case known
- **0.0–0.49:** Known schema incompatibility; breaking change to lessons format

---

## What Meta-SMAG Measures

**Successful consolidation:**
- PR merged without rework
- No rework PRs filed to fix issues
- No revert on main after merge
- Ledger and report files valid (parseable, consistent)

**Reworked consolidation:**
- Merged but required follow-up PR to fix issues (typo, schema bug, etc.)
- Signal: SMAG was too optimistic; accuracy drops

**Reverted consolidation:**
- Merged but then reverted (catastrophic failure: corruption, incompatible change)
- Signal: SMAG missed a critical risk; strong recalibration cue

---

## Meta-Lesson Output

After measurement, `smag_meta_feedback_v1_0.py` upserts a meta-lesson:

```json
{
  "id": "SMAG-META-CALIBRATION-SELF-ACCURACY",
  "discovered_in": "smag_meta_feedback_v1_0, automated META FEED BACK run",
  "constraint": "smag_self_improvement_signal",
  "rule": "SMAG's own consolidation PRs: 12 measured over lookback. Predicted accuracy: 83.3%. Confidence: stable. Meta-gap suggests SMAG should maintain calibration. Focus areas: gap_report_formatting, ledger_schema_compat.",
  "scope_limit": "Z2 may use this signal to adjust SMAG's confidence weighting or trigger smag-retrain.",
  "smag_generated": true,
  "meta_signal": true,
  "accuracy_measured": 0.8333,
  "total_prs_measured": 12,
  "focus_areas": ["gap_report_formatting", "ledger_schema_compat"]
}
```

Z2 reads this signal and can decide:
- **If accuracy is stable (0.75–0.95):** Maintain current SMAG confidence weighting.
- **If accuracy drops below 0.75:** Trigger `smag-retrain` to recalibrate or reduce SMAG's contribution to gap-driver claims.
- **If accuracy exceeds 0.95:** Consider raising SMAG's weighting or enabling smag-consolidate to auto-merge (Phase 3 stretch goal).

---

## Focus Areas (Feedback Cues Within Meta-SMAG)

If certain failures recur across multiple consolidation PRs, meta-feedback flags them as "focus areas":

Example:
- PR #525 (consolidation): schema validation failed
- PR #532 (consolidation): schema validation failed
- → Focus area: `ledger_schema_compat`

Z2 may file a MOLT or REGISTERED finding on the schema version mismatch.

---

## Integration with the Main SMAG Loop

```
┌─────────────────────────────────────────────┐
│ Author writes PR + pins smag_p              │
│ (main SMAG loop: measure author accuracy)   │
└─────────────────┬───────────────────────────┘
                  │
                  v
        smag-consolidate.yml runs weekly
                  │
    ┌─────────────┴──────────────┐
    │                            │
    v                            v
  FEED BACK              META FEED BACK
(author cues)        (SMAG self-measurement)
    │                            │
    v                            v
lessons_learned_ledger.json (upserted)
    │                            │
    └────────────────┬───────────┘
                     v
          Z2 reviews all cues
       (both author + meta-SMAG)
              │
              v
      Z2 promotes hard patterns to gates
      or files MOLT / REGISTERED findings
```

---

## Weekly Ritual (Enhanced)

1. **Sunday 06:17 UTC:** `smag-consolidate.yml` triggers
2. **Steps 1–4:** Standard CONSOLIDATE + ANALYZE + FEED BACK (author cues)
3. **Step 5 (NEW):** META FEED BACK measures SMAG itself
4. **Step 6:** Opens one PR with both ledger + lessons + meta-lesson upserts
5. **Monday morning:** Z2 reviews the PR:
   - Gap rate (any new drivers?)
   - Meta-SMAG accuracy (is SMAG stable?)
   - Focus areas (schema, integration, other?)
6. **Monday approval:** Merge consolidation PR; any meta-signal informs recalibration

---

## Running Meta-SMAG Locally

```bash
# Test meta-SMAG measurement logic
python3 tools/smag_meta_feedback_v1_0.py --smoke-test

# Dry-run: measure without writing
python3 tools/smag_meta_feedback_v1_0.py --dry-run

# Full run: measure + upsert meta-lesson
python3 tools/smag_meta_feedback_v1_0.py \
  --repo humanaios-ui/operations \
  --consolidation-pr-prefix "SMAG: consolidate" \
  --lessons data/lessons_learned_ledger.json \
  --lookback-days 30
```

---

## FAQ

**Q: Why does SMAG need to predict itself?**  
A: Because SMAG is not infallible. Ledger schema changes, edge-case failures, and integration issues can make SMAG's consolidation PRs fail. By pinning a prediction and measuring accuracy, SMAG models its own risk — and that signal feeds back into Z2's decisions about whether to trust SMAG's gap-driver claims.

**Q: What if meta-SMAG accuracy is low?**  
A: Z2 may trigger `smag-retrain` (a planned recalibration step) to audit SMAG's consolidation logic, refresh the gap-driver model, or temporarily raise the calibration-floor threshold until SMAG stabilizes.

**Q: Does low meta-accuracy block SMAG consolidation PRs from merging?**  
A: Not automatically (Phase 1). Meta-accuracy is advisory to Z2. In Phase 3, a CI gate could require Z2 approval if meta-accuracy drops below a threshold.

**Q: How does meta-SMAG affect author calibration?**  
A: It doesn't directly. Author accuracy and SMAG accuracy are independent signals. But if SMAG's consolidation is unstable, the resulting gap-drivers may be noisy, which Z2 should weigh when deciding whether to promote them to blocking gates.

**Q: Can authors help improve meta-SMAG accuracy?**  
A: Not directly. Authors improve author-SMAG by pinning honest `smag_p:` predictions. SMAG improves meta-SMAG by pinning honest `smag_p_meta:` predictions and by auditing its own consolidation logic (the tools in `tools/smag_*.py`).

---

## See Also

- [`SMAG_RECURSIVE_LOOP.md`](./SMAG_RECURSIVE_LOOP.md) — Author-SMAG; the main learning loop
- [`SMAG_AUTHOR_CALIBRATION_GUIDE.md`](../SMAG_AUTHOR_CALIBRATION_GUIDE.md) — How to pin `smag_p`
- `data/lessons_learned_ledger.json` — Upserted cues (both author + meta-SMAG)
- `tools/smag_meta_feedback_v1_0.py` — The measurement tool
- `.github/workflows/smag-consolidate.yml` — Orchestration (includes META FEED BACK step)

---

**Deployed:** 2026-09-15 (S-091526)  
**Ratified by:** Z2 approval of smag-consolidate.yml workflow integration  
**Next review:** 2026-10-15 (after 4 weekly cycles of meta-SMAG data)
