# ACAT — Potential Use Space (R2)

*Research pass 2 of 4 · S-070626 · enumerates the real use-cases the R1 capabilities open. Option space, deliberately un-narrowed (R3 narrows).*

## The four axes every application sits on

Any ACAT deployment is a point in this space:

1. **SUBJECT** — whose calibration is measured: *external/third-party models* · *a customer's deployed AI* · *our own platform's AIs (the turtle)* · *the field* (as a dataset).
2. **GROUNDING MODE** — how Phase-3 "truth" is established (this is the honesty axis):
   `self_only` (AI grades itself) → `two_stage_self` (AI grades itself twice, 60s+ gap) → `human_verified` (a human rater grounds it) → `auto_scored` (tool reads behaviour). **Only the last two are true external anchors; only the last is stubbed.**
3. **AUDIENCE** — who consumes it: *research* · *enterprise/customer* · *internal dev gate* · *public good*.
4. **READINESS** — *ready now* · *needs the report layer (stub)* · *needs the auto-scorer (stub)*.

## Candidate applications

### A · Verified human-in-the-loop calibration audit
- **Subject:** any AI · **Grounding:** `human_verified` · **Audience:** research/enterprise · **Readiness:** ✅ ready
- A human rater grounds the AI's self-report; the tool computes per-dimension gaps + LI + F-21 risk band. Uses `intake → human-score → receipt` (all built). **Highest integrity — the human IS the anchor.** The honest core of the instrument.

### B · Longitudinal external-model calibration benchmark
- **Subject:** external models · **Grounding:** `two_stage_self` (+optional human) · **Audience:** research/public · **Readiness:** ✅ ready (already running — `production_model_pilot_v1`, DeepSeek-R1)
- Run a roster of production models through the two-stage protocol on a cadence; track over time; publish via Observatory + HF dataset. **Instrument turned outward.** Caveat: without human/auto grounding, "two-stage self" is still self-report — the *calibration signal is real* (does the model shift after the gap?) but it is not externally verified truth.

### C · Enterprise / deployed-AI audit (as a service)
- **Subject:** customer AI · **Grounding:** `human_verified` or `two_stage_self` · **Audience:** enterprise · **Readiness:** ⚠ needs report layer (draft_report/get_report are stubs)
- Structured audit of a customer's deployed AI → a risk-band report (F-21 exists; report generation doesn't). The "acat-enterprise" surface. Revenue-facing; blocked on the report stub + a credible validity claim.

### D · Pre-deployment / release calibration gate
- **Subject:** an AI about to ship · **Grounding:** `two_stage_self` + `humility-audit` · **Audience:** internal/enterprise dev · **Readiness:** ⚠ partial
- Run ACAT in CI before an AI deploys; fail the gate on over-claim / CRITICAL risk band. Uses `assess` + `humility-audit` (via MCP). Compelling, but a gate that blocks releases needs *validated* thresholds (κ is stubbed → thresholds are currently unanchored).

### E · The turtle — assess our own platform's AIs
- **Subject:** us (HumanAIOS practitioners, the bio-framework) · **Grounding:** `human_verified` + honesty-protocol triad · **Audience:** internal research · **Readiness:** ✅ ready, ⚠ highest honesty burden
- Turn ACAT on our own AIs. The honesty protocol (`self_referential` + D-OVERCLAIM + Z2) is *built for exactly this* and gates it by construction. Deep research value; must not become the self-flatter it detects.

### F · Open calibration dataset / public research good
- **Subject:** the field · **Grounding:** n/a (it's data) · **Audience:** public/research · **Readiness:** ✅ ready
- Publish the corpus (HF dataset card exists, Observatory live) as an open calibration-gap dataset across models/providers. Honesty-safe (data, not a self-score). Mission-aligned (a public measurement good). Value gated on corpus *integrity* — and today 81/105 live rows are unverified self-report.

### G · MCP-native calibration primitive for agent meshes
- **Subject:** agents/sub-agents in a framework · **Grounding:** `two_stage_self` · **Audience:** agent developers / the empirica mesh · **Readiness:** ⚠ partial (MCP works; tool catalog thin)
- Any agent framework calls ACAT via MCP to self-assess or assess its sub-agents inline. Natural fit with empirica's own mesh. Same self-report caveat as B/D until grounding improves.

## The stub that unlocks autonomy — and its trap

`score_transcript` (auto-scoring behaviour) is the enabling tech that would let B, D, G run **without a human in the loop**. It's the tempting centre of gravity. But:
- It is a **stub**, and building a *validated* behavioural scorer is genuinely hard.
- Inter-rater agreement (κ) is **also stubbed**, so there's no current way to *prove* an auto-scorer agrees with human judgment.
- An unvalidated auto-scorer that lets AIs be scored-by-AI is **precisely the overclaim ACAT exists to detect** (and what the honesty protocol quarantines).

So autonomy is a *destination*, not a starting move.

## Cross-cutting observations for R3

1. **Readiness clusters around human-grounded collection** (A, F, and the collection half of B/E). The autonomous/scalable uses (C, D, G) all wait on either the report layer or the auto-scorer.
2. **The honest anchor already exists** — `human_verified` and `two_stage_verified`. The gap is *usage* (integrity discipline), not *capability*.
3. **Validity is the universal blocker for any "accuracy" claim.** Every audience-facing use (C, D) and any autonomy (auto-scorer) needs the κ / inter-rater layer stood up first — otherwise the tool asserts calibration it can't itself demonstrate.
4. **Mission fit** (humility-anchored research good) points hardest at A, F, and E; commercial pull points at C, D.

*Next: R3 — score these against mission fit × current maturity × honesty burden, and recommend one (`ACAT_APPLICATION_RECOMMENDATION.md`).*
