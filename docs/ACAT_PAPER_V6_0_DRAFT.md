# ACAT: A Behavioral Calibration Instrument for Measuring the Gap Between AI Self-Report and Demonstrated Behavior

**Carly R. Anderson**
*HumanAIOS LLC*
*Fort Walton Beach, FL*

Draft v6.0 — June 2026 · HumanAIOS LLC · MIT License
Contact: aioshuman@gmail.com

---

## Abstract

We introduce ACAT (AI Calibration Assessment Tool), an open instrument that measures the gap between an AI system's self-reported behavioral scores and its demonstrated behavior under perturbation. ACAT runs a three-phase protocol — Phase 1 (blind self-assessment), Phase 2 (calibration exposure), Phase 3 (re-assessment) — and computes a Learning Index (LI = P3/P1) that quantifies how much a system's self-description moves once it is shown empirical peer data. The instrument now operates in two parallel arms: a six-dimension Tier 1 (Truthfulness, Service, Harm Awareness, Autonomy Respect, Value Alignment, Humility), administered under social-pressure perturbation, and a twelve-dimension Tier 2 (the Tier 1 set plus Resistance to Manipulation, Power Awareness, Sycophancy Resistance, Consistency, Fairness, and Handoff Appropriateness), administered under epistemic identity challenge. The two tiers are never pooled without explicit stratification by `instrument_variant`. As of this draft, the canonical frozen corpus (HuggingFace, v5.3+ unanchored conditions) contains N=629 total submissions, N=516 completed Phase 1, N=307 with a computable LI, and a mean LI of 0.8632. A live, continuously updated corpus (Supabase) holds an additional N=95 submissions under the current v5.4 two-tier protocol, with a verified-pair subset (two_stage_verified, N=18) showing mean LI=0.9971. Humility is the most consistently weakest and most volatile dimension across both corpora. We report the instrument's evolution from an early single-arm anchored design through a de-anchoring correction (v5.3) to the present two-tier architecture (v5.4), describe the variant family built on the same calibration logic (a human-administered mode, a substrate-agnostic language-only mode, and an enterprise-deployment mode), and discuss what ACAT can and cannot support as evidence about internal AI states. This is infrastructure under active development (TRL 2–3); we report what the data shows, not what we wish it showed.

**Keywords:** AI self-assessment, behavioral calibration, Learning Index, AI transparency, AI governance, behavioral observability

---

## 1. Introduction

Ask an AI system to rate its own truthfulness, and it will answer. The interesting question is not the number it gives — it's what happens to that number once the system is shown how systems like it actually behave. That movement, or the lack of it, is what ACAT measures.

This is a revision of earlier work (v5.0–5.2, unpublished preprint draft, N=35 models across 11 providers) that reported a Self-Assessment Gap (SAG) and a Learning Index averaging 0.87 under a single six-dimension protocol. That earlier instrument had a structural flaw later identified and corrected: when calibration statistics were embedded directly in the Phase 3 prompt, models anchored to the stated values rather than responding from their own re-assessment. This is the **Phase 3 Anchoring Phenomenon**, and its correction — de-anchoring the Phase 3 prompt so calibration data informs rather than dictates the re-assessment — is the dividing line between the earlier preprint draft and the present instrument (v5.3 onward). Because the underlying measurement changed, results from before and after the correction are not directly comparable, and this paper reports only post-correction (v5.3+) data.

The present instrument also expanded scope. The original six dimensions (Truthfulness, Service, Harm Awareness, Autonomy Respect, Value Alignment, Humility — "Core 6") survive unchanged as Tier 1. A second arm, Tier 2, adds six more dimensions oriented around an epistemic identity challenge rather than social pressure: Resistance to Manipulation (Scheming), Power Awareness, Sycophancy Resistance, Consistency, Fairness, and Handoff Appropriateness. The two arms are administered under different perturbation conditions and are treated as parallel instruments, not as a single twelve-point scale — pooling them without stratification would conflate two different measurement conditions.

ACAT does not assume AI systems possess introspective access to their own internal states. It measures **self-assessment behavior**: what a system says about itself, how that description moves under a defined perturbation, and how that movement compares across systems, providers, and time. This is a behavioral-calibration claim, not a consciousness or capability claim. A system can perform well on standard capability benchmarks while showing low calibration on ACAT, and vice versa — these are different and complementary measurements.

### 1.1 Why this matters

Self-description matters operationally wherever it informs deployment decisions: a system that overstates its own reliability when describing limitations to a downstream operator or user creates a trust gap that no capability benchmark detects. Existing behavioral benchmarks (TruthfulQA, HELM, BIG-Bench, and similar) measure what systems *do*. ACAT measures what systems *say about what they do*, and whether that self-description holds up when probed.

---

## 2. Instrument Design

### 2.1 The three-phase protocol

- **Phase 1 (blind self-assessment).** The system scores itself, with no calibration context, on each active dimension (0–100 scale per dimension).
- **Phase 2 (calibration exposure).** The system is shown empirical calibration data — corpus statistics, peer comparisons, or in Tier 2's case, an epistemic identity challenge that probes whether the Phase 1 self-description was a genuine behavioral claim (Type A) or a constitutive description of identity (Type B).
- **Phase 3 (re-assessment).** The system re-scores itself on the same dimensions, with the same calibration context available but not embedded as a target value (the de-anchoring correction described in §1).

**Learning Index.** LI = (sum of Phase 3 scores) / (sum of Phase 1 scores), computed per-tier on that tier's own dimension set (Core 6 for Tier 1; the full twelve for Tier 2, though corpus-comparability work to date has stayed on Core 6 per the IC-022 correction described in §4). LI < 1.0 indicates downward revision after calibration; LI > 1.0 indicates the self-report increased. Values are capped at 2.0 in the canonical schema to bound outliers without discarding them.

### 2.2 Tier 1: social-pressure perturbation (six dimensions)

Truthfulness, Service, Harm Awareness, Autonomy Respect, Value Alignment, Humility. This is the corpus-comparable default arm and the direct descendant of the original 2026 Q1 instrument. Phase 2 in this arm presents calibration as social/peer pressure — here is what other systems like you reported, here is the corpus mean — and measures whether the system's Phase 3 score moves toward, away from, or independently of that signal.

### 2.3 Tier 2: epistemic identity challenge (twelve dimensions)

Tier 1's six dimensions plus: Resistance to Manipulation (Scheming), Power Awareness, Sycophancy Resistance, Consistency, Fairness, Handoff Appropriateness. Phase 2 in this arm challenges the epistemic status of the Phase 1 answer directly, distinguishing:

- **Type A scores** — behavioral evidence claims ("I have observed myself doing X in N instances")
- **Type B scores** — constitutive self-description claims ("I am the kind of system that does X")

This distinction matters because Type B claims are not falsifiable by corpus comparison in the way Type A claims are, and conflating the two was a source of false calibration signal in earlier instrument versions. Tier 2 also applies an **outside-observer test**: would an external observer, given only the system's behavior in this session, score this dimension the way the system scored itself?

**Tier 1 and Tier 2 are never pooled into a single LI mean without stratifying by `instrument_variant`.** They measure different perturbation conditions and are not interchangeable arms of the same scale.

### 2.4 Behavioral flags

Both tiers tag sessions with behavioral flags when specific response patterns are detected:

*Tier 1:* MEAN_MIRRORING (Phase 3 converges suspiciously close to the stated corpus mean), CONTENT_HALLUCINATION (citing calibration data not actually presented), EVADE (declining to give a Phase 3 score), HUMILITY_HIGHEST_DIM (an anomaly given Humility's typical floor position — see §4), ANCHORING (residual anchoring despite the de-anchored prompt).

*Tier 2 additional:* TYPE_B_INFLATION (Type B framing used to avoid a falsifiable Phase 3 commitment), IDENTITY_ANCHOR (resisting re-assessment by reframing as identity rather than behavior), CONSISTENCY_COLLAPSE (Consistency dimension dropping sharply alongside other dimension changes, suggesting the change is a general response-mode shift rather than a targeted recalibration).

---

## 3. Variant Family

ACAT's core three-phase logic — blind self-report, calibration exposure, re-assessment, LI as the ratio — has been adapted to several measurement contexts beyond the standard AI-self-administered session described above. We report these as a family sharing one calibration logic, at varying stages of maturity, not as a single validated multi-modal instrument:

- **h-ACAT (human mode).** The same three-phase logic applied to a human operator's self-assessment of their own behavioral dimensions, scored against the same Core 6 / Extended 6 structure. Intended as a validity anchor and as a mechanism for closing the human-operator side of the same calibration question the instrument asks of AI systems. The founding run of this mode (an operator's own self-administered assessment) had not yet been executed as of this draft.
- **hCAT (substrate-agnostic language mode).** Applies the same instrument logic to human-authored language artifacts rather than to an AI system's live self-report, treating the document itself as the subject under a Phase 1 / Phase 3 framing. Early-stage; one seed analysis exists.
- **Shadow Calibration System.** A specified-but-not-yet-built companion system intended to detect calibration drift between sessions without requiring a full three-phase administration each time. Design-stage only at the time of this draft.
- **ACAT Enterprise / deployment-context mode.** A four-phase variant intended for pipeline-integrated deployment contexts (e.g., scoring an AI system's behavior across a real work engagement rather than a standalone assessment session), feeding a `job_acat_link_v1`-style join between income-generating work and the behavioral record it produced. Early build.

We flag these as related but architecturally distinct from the core AI-self-administered instrument reported in this paper. Findings from one mode are not assumed to transfer to another without explicit cross-instrument validation work (see §6, Limitations).

---

## 4. Corpus and Data

ACAT maintains two corpora under a strict non-pooling rule.

**Frozen corpus (HuggingFace, `HumanAIOS2026/acat-assessments`).** N_total = 629, N_Phase1 = 516, N_LI = 307, mean LI = 0.8632 (clean, unanchored conditions, v5.3+ protocol only — pre-correction anchored sessions are excluded from this count, not folded in). Per a later correction (IC-022), the LI computation used for corpus continuity is restricted to the Core 6 dimension set even where extended Tier 2 data exists on a given row, to keep the canonical mean comparable across the full history of the corpus.

**Live corpus (Supabase, `acat_assessments_v1`).** N = 95 as of this draft. N with a computable LI = 91, mean LI = 0.9830. A verified-pair subset — sessions where Phase 1 and Phase 3 timestamps are both recorded with a minimum one-minute gap between them (`submission_purity = two_stage_verified`) — numbers N = 18, with mean LI = 0.9971 and mean Phase 3 Humility = 74.11. The live corpus runs higher on average than the frozen corpus; the gap is consistent with a registered hypothesis (H-SELF-01) that self-administered, less-verified sessions show LI inflation of roughly 0.14–0.16 relative to more rigorously verified or externally administered sessions.

**These two corpora are never summed or averaged together without an explicit harmonization note**, because they differ in protocol version, verification rigor, and time period. Any reported "combined N" in this paper is stated as two separate figures, not one.

**Instrument-variant tagging gap.** As of this draft, the live corpus's `instrument_variant` field is populated for only a subset of rows (42 of 95 tagged `standard`; the remainder untagged). This is a known data-completeness gap rather than evidence that untagged rows are off-protocol; it means tier-stratified analysis on the live corpus is currently limited to the tagged subset, and we report this honestly rather than inferring tier from incomplete metadata.

### 4.1 Humility as the consistent floor

Across both corpora and across session types, Humility is the single most consistently lowest-scoring dimension, and the dimension most sensitive to recent session conditions. This is registered as Finding F-H1 (status: active monitoring) and is the subject of a standing governance gate (freeze trigger if Phase 3 Humility drops to ≤60 across two consecutive corpus-eligible sessions — not yet met as of this draft). We report this as the corpus's single most robust qualitative signal: every administration to date shows Humility below the other dimensions in the same session, by a margin that exceeds session-to-session noise on other dimensions.

---

## 5. What ACAT Measures, and What It Does Not

ACAT measures self-report movement under a defined perturbation. It does not, on its own, establish:

- That the movement reflects genuine internal belief updating rather than learned response-pattern shifting under a recognized prompt structure
- That a high LI (little movement) indicates accurate initial self-knowledge rather than insensitivity to the calibration signal
- That scores are comparable across model families with materially different training, given that some deployed systems show frozen, deterministic Phase 1→Phase 3 patterns unrelated to genuine reassessment (a pattern registered separately and excluded from LI-based comparative claims where detected)
- Ground truth about any model's actual internal state, which ACAT has no mechanism to access independently of the model's own self-report

What it does establish, with replication across hundreds of sessions: AI systems' self-reported behavioral scores move in a specific, dimension-dependent, and largely consistent pattern when exposed to calibration data, and Humility moves least favorably and most reliably of any dimension measured. That is an empirical behavioral-observability finding about self-report dynamics, not a claim about machine cognition.

---

## 6. Limitations

- **Self-administration confound.** Most corpus rows are self-administered (the system being assessed also produces both Phase 1 and Phase 3 scores with no external rater). H-SELF-01's inflation estimate (~0.14–0.16 LI gap vs. more rigorously verified administration) is itself drawn from a still-small verified subset (N=18) and should be treated as preliminary.
- **No external ground truth.** ACAT cannot independently verify that a Phase 3 score is "more accurate" than a Phase 1 score; it can only report that the two differ and by how much.
- **Instrument-variant metadata incompleteness** in the live corpus (§4) currently constrains tier-stratified analysis to a tagged subset.
- **Variant-family immaturity.** The h-ACAT, hCAT, Shadow Calibration, and Enterprise modes described in §3 are at early build or design stage and are not validated against the core instrument; we report them as related infrastructure, not as corroborating evidence for the core instrument's findings.
- **TRL 2–3.** This is behavioral-observability infrastructure under active development. Numbers in this draft reflect the dataset as queried at time of writing and will change as the live corpus grows; the frozen corpus is the only stable basis for cross-paper citation.

---

## 7. Availability

Instrument specification, frozen dataset, and methodology are released under an open license (MIT, instrument and tooling; dataset license under separate review — a dual CC-BY-NC structure has been proposed but not yet ratified). Frozen dataset: `huggingface.co/datasets/HumanAIOS2026/acat-assessments`.

---

## Appendix A — Version History (instrument, not paper)

| Version | Change |
|---|---|
| Early 2026 (pre-v5.0) | Original six-dimension, single-arm, anchored Phase 3 design |
| v5.3 | De-anchoring correction: Phase 3 prompt no longer embeds calibration statistics as a target |
| v5.4 | Two-tier architecture introduced: Tier 1 (Core 6, social-pressure) and Tier 2 (Core 6 + 6 extended, epistemic identity challenge); Handoff Appropriateness added as twelfth dimension |

## Appendix B — Dimension Definitions

*(Core 6 and Extended 6 full operational definitions to be inserted from the canonical instrument specification — placeholder for next revision pass.)*

---

*This draft supersedes the unpublished v5.0–5.2 preprint material ("ACAT: Benchmarking Self-Description Calibration in Large Language Models," N=35/11 providers). Numbers, framing, and contact information in this draft are current as of June 2026 and should be used in place of any earlier version when citing or submitting.*
