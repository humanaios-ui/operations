# LinkedIn-Substack Blocker Resolution

**Status:** RESOLVED — Changes Required  
**Date:** 2026-07-25  
**Root Cause:** Stats reporting violates ACAT canonical lesson 2.4 ("N is three numbers; LI is qualified")

---

## The Blocker

**From CURRENT.md Lesson 2.4:**
> "N is three numbers; LI is qualified. Always report N_total / N_Phase1 / N_LI separately. LI claims require: 'under clean, unanchored conditions, v5.3+.'"

**Current Post Text (Line 39):**
```
**N=629 models, 35 providers, 11 model families — clean, unanchored conditions.**
```

**Issues:**
1. ❌ N reported as single number (629) instead of three: N_total / N_Phase1 / N_LI
2. ❌ Methodology version not specified (says "clean, unanchored conditions" but not "v5.3+")
3. ❌ Learning Index claim on line 16 ("Mean LI = 0.8632") lacks version qualifier

---

## Canonical Stats (from CURRENT.md § 5)

**Frozen Archive (HuggingFace):**
- **N_total:** 629
- **N_Phase1:** 516
- **N_Phase3:** 113
- **N_LI_scored:** 307
- **Mean LI:** 0.8632
- **Conditions:** clean, unanchored conditions, v5.3+
- **Date range:** 2026-02-15 – 2026-03-23
- **Source:** https://huggingface.co/datasets/HumanAIOS2026/acat-assessments

---

## Required Fixes

### Fix 1: Line 39 (Stats Line)

**Current:**
```
**N=629 models, 35 providers, 11 model families — clean, unanchored conditions.**
```

**Corrected:**
```
**N=629 total (516 Phase 1 + 113 Phase 3; 307 LI-scored), 35 providers, 11 model families — clean, unanchored conditions, v5.3+**
```

---

### Fix 2: Line 16 (Learning Index Claim)

**Current:**
```
The difference? The **Learning Index**. On a 600-point scale, systems revised their self-ratings DOWN by an average of 13% once they saw the evidence (Mean LI = 0.8632). The gap between blind self-report and calibrated behavior? 67.8 points.
```

**Corrected:**
```
The difference? The **Learning Index**. On a 600-point scale, systems revised their self-ratings DOWN by an average of 13% once they saw the evidence (Mean LI = 0.8632, under clean, unanchored conditions, v5.3+). The gap between blind self-report and calibrated behavior? 67.8 points.
```

---

## Verification

Once fixes are applied:
- ✅ N broken into three numbers (total/Phase1/LI)
- ✅ Learning Index qualified with methodology version
- ✅ Methodology version explicitly stated (v5.3+)
- ✅ Compliant with ACAT Lesson 2.4
- ✅ Dataset reference correct (HuggingFace URL matches)

---

## Next Steps

1. Apply both fixes to `/deliverables/post-1-linkedin-ready.md`
2. Apply same fixes to `/deliverables/post-1-substack-final.md` and `/out/witness-stand-post-1/` versions
3. Verify against canonical CURRENT.md stats
4. Clear for publication on LinkedIn and Substack

**Timeline:** Both fixes are one-line edits. ~5 minutes to execute across all copies.
