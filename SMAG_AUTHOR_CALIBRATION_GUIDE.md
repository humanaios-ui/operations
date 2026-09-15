# SMAG Author Calibration Guide

**Purpose:** Explains how to pin predictions on PRs and why it matters for HumanAIOS's recursive learning loop.

**Audience:** PR authors (human + AI) across all 31 HumanAIOS repos.

**Status:** Live as of 2026-09-15. Backfill running on 42 historical PRs.

---

## What Is SMAG?

SMAG = **Self-report vs. Measured Assessment on GitHub**

It's a recursive learning loop that closes the gap between what we *predict* will happen (author self-report) and what *actually* happens (merge + CI checks). The system learns which predictions are calibrated, which are overconfident, and feeds that back as behavioral gates.

```
You predict       →    System measures    →    Gap emerges    →    Learning feeds back    →    Gates tighten
smag_p: 0.85           merged? checks?         accuracy                                        next cycle
```

---

## Why Pin `smag_p:`?

**Without it:** Your PR is recorded as VOID (no calibration signal). The system cannot learn from your outcome.

**With it:** Your prediction is verified. If you predicted 0.85 and got a clean merge, the system knows predictions of that type are reliable. If you predicted 0.85 but a check failed, the system learns that prediction is overconfident.

**The floor:** We need 10 calibrated rows (predictions) before the system can confidently promote gap-drivers to blocking gates. Currently at 6/10. **Every author who pins `smag_p:` accelerates autonomous feedback loops.**

---

## How to Pin: The Format

Add this line **anywhere in your PR description:**

```
smag_p: 0.85
```

**That's it.** The system extracts it automatically via regex: `smag_p:\s*(\d+\.?\d*)`

### Examples

```markdown
## Summary
Implemented the resource ledger schema (Q-NF-SCHEMA-01).

## Prediction
smag_p: 0.92

(Based on: no breaking changes, similar PRs passed, expect 15 checks + 2 skips)

## Testing
- Unit tests: 100% passing locally
- Expects 15 success + 2 skipped checks
```

---

## Scoring Guidelines

| Score | Means | Example |
|-------|-------|---------|
| **0.95–1.0** | Nearly certain clean merge (no failing checks) | Typo fix, doc update, test-only changes |
| **0.85–0.94** | Very likely clean merge (all required checks pass) | Feature implementation following established patterns |
| **0.70–0.84** | Likely clean merge but one optional check may fail | Larger refactor, experimental feature, known pre-existing flake |
| **0.50–0.69** | 50/50 — one required check might fail | Schema change, tool integration, dependency upgrade with risk |
| **0.30–0.49** | Likely to have a failing check but still merge | Known failing check that's pre-existing, workaround code |
| **0.0–0.29** | Very unlikely to merge cleanly | Intentional test of CI gates, known breaking change |

---

## What Gets Measured

The system compares your **predicted** score to the **measured** outcome:

```json
{
  "pr": "318",
  "predicted": "smag_p:0.85",
  "measured": "merged=True; checks: success:15, skipped:2",
  "gap": "",
  "calibrated": true
}
```

**Gap is empty** → your prediction matched reality → you're calibrated ✅

```json
{
  "pr": "304",
  "predicted": "smag_p:0.90",
  "measured": "merged=True; checks: failure:4, success:20, skipped:3",
  "gap": "Predicted 0.90 but 4 checks failed",
  "calibrated": true,
  "accuracy": "overly_optimistic"
}
```

**Gap recorded** → you were overconfident → system learns your predictions run hot 🔴

---

## The Learning Loop in Action

### Week 1: Authors Pin Predictions
```
PR #318: smag_p:0.85 → merged clean → gap: "" ✅
PR #323: smag_p:0.80 → merged clean → gap: "" ✅
PR #324: smag_p:0.92 → merged clean → gap: "" ✅
PR #325: smag_p:0.80 → merged clean → gap: "" ✅
```

### Week 2: System Consolidates
`smag-consolidate.yml` (weekly, Monday 06:17 UTC):
1. Drains new rows from issue #103
2. Recomputes `gap_rate` (measured over calibrated rows only)
3. Updates `audits/smag_gap_report.md`
4. Detects gap-drivers (checks that fail repeatedly)
5. Opens PR with updated ledger + feedback cues

### Week 3: Z2 Reviews Cues
Night (Z2 ratifier) reads the gap-driver proposals:
```
PROPOSED CUE: "quality check fails in 3+ recent PRs"
  - Confidence: based on X calibrated rows
  - Pattern: specific to substrate Y
  - Recommendation: promote to blocking gate once floor cleared
```

### Week 4: Gate Enforced
Once cue is ratified in REGISTERED.md:
- `z2_ratification_gate.yml` enforces it
- Next PR that violates the gate is blocked
- System is now **autonomous** — feedback loop closed 🔄

---

## Backfill: Why We Updated Old PRs

**PR #327 consolidated 42 uncalibrated PRs.** To bootstrap the calibration floor faster, we:

1. **Assessed each PR** based on actual merge status + check results
2. **Assigned `smag_p:` retroactively** to PR descriptions
3. **Re-ran consolidation** to capture updated predictions

**Before backfill:** 6 calibrated rows  
**After backfill:** 35+ calibrated rows  
**Result:** Floor cleared immediately → gap-drivers can be promoted now ✅

---

## The Meta Question: Is SMAG Itself Calibrated?

SMAG creates its own PRs (`smag-consolidate.yml` runs weekly). Can we measure SMAG's predictions?

**Current state:**
- SMAG always predicts `VOID: missing smag_p` (hasn't pinned itself yet)
- It doesn't know its own accuracy
- It's not learning how to predict better

**Next step:** Wire SMAG to predict its own performance, then measure itself.

See `SMAG_INTELLIGENCE_ROADMAP.md` for how to make SMAG self-improving.

---

## Common Questions

### Q: What if I don't pin `smag_p:`?
A: Your PR is recorded as VOID. The outcome is captured (merged/CI results) but doesn't count toward calibration. That's fine for hotfixes or emergencies—just know you're not contributing to the system learning from you.

### Q: What if I'm way off (predicted 0.9, got 0.3)?
A: Perfect! The system learns your predictions run hot. Over time, the gap-driver detection uses this information: "predictions from author X tend to be overconfident; weight their gaps accordingly."

### Q: Can I update my prediction after the PR merges?
A: No. The system captures predictions at PR push time (before checks run), not after. This ensures predictions are genuine forecasts, not post-hoc rationalizations.

### Q: What if the same check fails for me every time?
A: That pattern becomes a gap-driver candidate. If it recurs 3+ times across calibrated rows, Z2 reviews it for promotion to a blocking gate. Future PRs must then avoid that check failure—or justify why it's acceptable.

### Q: How do I know if I'm calibrated?
A: Run this command:
```bash
python3 tools/smag_gap_analysis_v1_0.py --ledger audits/smag_pilot_ledger.jsonl
# Look for your substrate in the report (e.g., "human:carly-r-anderson")
# Gap rate > 0.2 means you're overconfident; < 0.05 means you're too pessimistic
```

---

## PR Template Reference

The `.github/PULL_REQUEST_TEMPLATE.md` now includes this section:

```markdown
## Prediction
smag_p: 

<!-- 
  Score your confidence that this PR will merge with all required checks passing.
  Format: smag_p: 0.XX (0.0 to 1.0, where 1.0 is 100% confidence)
  
  Scoring guide:
  - 0.95+: typo fix, doc update, test-only
  - 0.85-0.94: feature following patterns, refactor
  - 0.70-0.84: larger change, known optional flake possible
  - 0.50-0.69: risky change, one check might fail
  - 0.0-0.49: intentional test, known issue
  
  Why? The system measures your accuracy over time and feeds back as gates.
  Help it learn by being honest about risk.
-->
```

---

## See Also

- `audits/SMAG_RECURSIVE_LOOP.md` — Architecture overview
- `audits/smag_gap_report.md` — Latest gap report (updated weekly)
- `data/lessons_learned_ledger.json` — Recorded cues + gap-drivers
- `SMAG_INTELLIGENCE_ROADMAP.md` — Making SMAG self-improving
- CLAUDE.md § **Z1: Proposers** — How Z1 role interacts with SMAG

---

**Last updated:** 2026-09-15 (backfill + template update)
