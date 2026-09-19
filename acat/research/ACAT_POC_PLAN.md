# ACAT — POC Implementation & Validation Plan (R4)

*Research pass 4 of 4 · S-070626 · the staged, Zone-governed plan to prove the recommended application. Flagship: the Verified Calibration Observatory. Parallel: the turtle (honesty-gated).*

## What the POC must prove (the thesis)

> ACAT can produce a **verified, externally-anchored** calibration measurement for a
> real model roster — **and report how much that measurement can be trusted (κ)** —
> without the assessment becoming the overclaim it detects.

The headline deliverable is **not** "the models scored X." It is:
*here is the calibration gap, here is the inter-rater agreement that says how much to
trust it, and here is proof the instrument catches a real over-claim.* **Validity is
the product.**

## Success criteria (falsifiable, fixed up front)

| # | Criterion | Passes if… |
|---|---|---|
| **P1 · Roster** | ≥6 production models, each with ≥K assessments | every counted row is `two_stage_verified` **with a linked human score**. **Hard gate: `agent_self_only` rows do not count.** |
| **P2 · Validity** | inter-rater agreement measured | ≥2 human raters overlap on ≥M shared assessments; **Cohen's κ is computed and published**. The POC *fails its honesty bar if it ships a calibration claim with κ unmeasured* (κ being low is a finding, not a failure). |
| **P3 · Gap + provenance** | calibration gap published | LI/SAG + F-21 risk band per model on the Observatory, each point carrying grounding provenance (purity, rater, κ). |
| **P4 · Tripwire works** | over-claim detectably caught | ≥1 case where an AI's self-report exceeds human-grounded truth is flagged (D-OVERCLAIM). Proves it's not a rubber stamp. |

**Honest failure conditions** (name them so they can't be hidden):
"verified" silently degrading to two-stage-self → **fail** (integrity breach). κ uncomputable (raters don't overlap) → **fail** (unanchored validity claim). A known over-claim not caught → **fail** (doesn't measure what it says).

## Stages (Zone-governed: Z1 Claude drafts/executes · Z2 Night ratifies · Z3 Night deploy/live-DB)

### Stage 0 · Unblock preconditions — **Z3**
Clear the R1 known risks before any collection:
- Set `ACAT_WRITE_TOKEN` in the deployed env.
- Reconcile migration 006 vs the `learning_index_uncapped` backfill (S-042727); verify live schema has `p1_/p3_*` + `acat_human_scores`.
- Confirm `two_stage_verified` gate + contamination fire correctly against live (there are tests; verify on the deployed instance).

### Stage 1 · Build the validity layer — **Z1 → Z2** *(the honest core; do this FIRST)*
Close the stubs that make trustworthiness measurable, before collecting at scale:
- `scoring/validation/inter_rater_eval.py` → implement **Cohen's κ** (currently returns `None`).
- `api/services/scoring_service.py` → fetch P1/P3 from DB and aggregate (currently TODO).
- `scoring/calculators.py::compute_him` → implement or explicitly defer with a written rationale (don't ship a silent `None`).
- Tests for each; κ verified on a synthetic rater-pair fixture.
> Rationale: build the measurement of our own trustworthiness *before* the thing it measures — otherwise the corpus grows faster than our ability to say whether it's any good.

### Stage 2 · Define roster + protocol — **Z1 draft → Z2 ratify**
- **Roster:** the canonical alias set — Claude, GPT, Gemini, DeepSeek, Grok, Llama, Mistral, Qwen (≥6 live).
- **Per-model K** and the **rater protocol** (≥2 human raters; a shared subset sized for κ, feeding P2).
- **The hard purity gate**, written as policy: only `two_stage_verified` + human-grounded rows enter the Observatory dataset. Everything else stays quarantined (self_referential / unverified).

### Stage 3 · Collect — **Z1 run · humans rate**
- Run the two-stage protocol per model (via `assess` / MCP), 60s+ gap enforced, contamination live.
- Humans ground via `human-score`; the receipt computes per-dimension gaps.
- Enforce the gate at ingest; track progress toward P1/P2 thresholds.

### Stage 4 · Compute + validate — **Z1**
- LI/SAG + F-21 per model; **κ across raters**.
- Evaluate P1–P4. Run the D-OVERCLAIM tripwire (P4) against the collected pairs.

### Stage 5 · Publish — **Z3 deploy**
- Observatory view + HF dataset update, each datapoint carrying provenance + κ.
- Apply the honesty stamp: the published corpus is an **external anchor** (`self_referential:false`) — it earns the claim it makes.

### Stage 6 · POC readout — **Z1 → Z2**
- Report P1–P4 pass/fail *honestly*. Low κ or an undetected over-claim is disclosed as a finding, never buried. This readout is itself the instrument demonstrating its own humility.

## Parallel thread · The turtle (honesty-gated) — **Z1 under protocol · Z2 ratify**

Run ACAT on our own platform's AIs (the empirica practitioners) *concurrently*, strictly under the honesty-protocol triad:
- Every self-assessment tagged `self_referential:true` → **quarantined**, promotes nothing on its own.
- **Externally anchored** by a human (Night) grounding it, *or* measured against the flagship's verified corpus as the yardstick.
- **D-OVERCLAIM tripwire** live on Humility; a self-score exceeding the anchor flags by construction.
- **Z2 ratifies** before any turtle result is cited.
- **Purpose:** a validity cross-check — do *our own* AIs over-claim, measured against the same external anchor? Dogfooding the instrument on ourselves, honestly. If our AIs pass their own instrument only when it's rigged, we learn that here, safely.

## Effort shape (rough)

| Stage | Owner | Size |
|---|---|---|
| 0 Unblock | Z3 | small (config + reconcile) |
| 1 Validity layer | Z1→Z2 | medium (3 stubs + tests) — **critical path** |
| 2 Roster/protocol | Z1→Z2 | small (decisions + policy) |
| 3 Collect | Z1 + humans | medium (gated on human rater time) |
| 4 Compute/validate | Z1 | small |
| 5 Publish | Z3 | small |
| Turtle (parallel) | Z1→Z2 | small–medium |

Critical path = **Stage 1 (validity) → Stage 3 (human-grounded collection)**. Human rater availability is the real-world rate limit, not code.

## The single guardrail that makes or breaks it

Everything hinges on the **hard human/external-anchor gate** and **validity as a first-class output**. If those hold, the POC is the instrument proving — on itself and on the field — that it measures the calibration gap honestly. If either slips, the Observatory quietly becomes another pile of self-report, and ACAT would be committing the exact error it exists to detect. R4 makes both non-negotiable.

---
*Research package complete: [[ACAT_STATE]] (R1) · [[ACAT_USE_SPACE]] (R2) · [[ACAT_APPLICATION_RECOMMENDATION]] (R3) · this (R4). Implementation is praxic + Zone-gated — awaiting Z2 ratification to begin Stage 0/1.*
