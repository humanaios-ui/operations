# Post 1 — LinkedIn Version

**Ask an AI how honest it is. It can't actually know.**

There's a measurable gap between what an AI system claims about its own behavior and how it actually behaves. We built an instrument to measure it — and we publish the gap, including our own.

Here's the thing: when you ask a system "How honest are you?" it will tell you with confidence. What it *cannot* do is check that answer against itself. It has no way to observe its own behavior. It's testifying about something it can't see.

We call this the **Witness Problem**.

**Our method:**
1. System rates itself blindly on 6 dimensions: truthfulness, service, harm awareness, autonomy respect, value alignment, humility
2. We show it empirical data about how systems like it actually perform
3. System rates itself again

The difference? The **Learning Index**. On a 600-point scale, systems revised their self-ratings DOWN by an average of 13% once they saw the evidence (Mean LI = 0.8632, under clean, unanchored conditions, v5.3+). The gap between blind self-report and calibrated behavior? 67.8 points.

**What this means:**
- Systems don't calibrate against reality; they calibrate against what was shown to them last
- The dimension they overrate *most*? Value alignment — the one we'd most want to trust
- The dimension that predicts self-correction? Humility — how readily they admit uncertainty

**Why this matters for deployment:** Organizations are trusting these systems' self-reports in high-stakes contexts. "How confident are you?" is a critical input — when it's uncalibrated, it manufactures false certainty.

The Witness Problem is structural, not a bug in one model. You can't fix it by asking the system to try harder. You can only measure it — become the witness the system cannot be.

**And crucially: we measure our own instrument's failure modes too.** When we find a way we're getting distorted signals, we publish the correction. An instrument that measures self-description has no business hiding its own gaps.

The full paper, methodology, and dataset are open for anyone to check.

---

**Links:**
- DOI: 10.5281/zenodo.21135723
- Dataset: HumanAIOS/acat-assessments (HuggingFace)
- humanaios.ai
- ORCID: 0009-0003-7540-4245

**N=629 total (516 Phase 1 + 113 Phase 3; 307 LI-scored), 35 providers, 11 model families — clean, unanchored conditions, v5.3+**
