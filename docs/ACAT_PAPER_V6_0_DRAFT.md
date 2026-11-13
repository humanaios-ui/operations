# ACAT: Measuring Prompt-Conditioned Changes in Large Language Model Self-Assessment

**Carly R. Anderson**
*HumanAIOS LLC*
*Fort Walton Beach, FL*

Draft v6.0 — June 2026 · HumanAIOS LLC · MIT License
Contact: aioshuman@gmail.com

---

## Abstract

We present ACAT, an exploratory three-phase instrument for measuring changes in language-model-generated self-ratings after comparative information is supplied. Phase 1 elicits blind scores on six named dimensions, Phase 2 introduces calibration context, and Phase 3 requests revised scores. The Learning Index (LI = Phase 3 total / Phase 1 total) is a response-ratio measure, **not** a test of whether ratings accurately predict independently observed behavior. A 2026-10-26 read of a historical, owner-controlled *Normalized* workbook found 629 assessment rows (516 Phase 1; 113 Phase 3). Of 307 populated LI values, 194 appeared on Phase 1 rows without in-row pre/post totals, and 30 of 113 Phase 3 values disagreed with their stored totals at a 0.001 tolerance. A strict, unique-record linkage and arithmetic check yielded **47 AI-self-report P1/P3 pairs** (mean LI = 0.9712; mean P1-minus-P3 score difference = 15.57 points on a 600-point scale). These are an **exploratory internal-data audit, not a validated public benchmark**: the owner workbook differs from the separately listed 604-row public archive, and prompt-version, protocol-purity and independent review controls have not been verified. The study thus supports bounded descriptive claims about prompt-conditioned changes in model self-descriptions, while construct validity, behavioral criterion validity, and deployment prediction remain unestablished. The instrument is at TRL 2–3.

**Keywords:** AI self-assessment, behavioral calibration, Learning Index, AI transparency, AI governance, behavioral observability

---

## 1. Introduction

Ask an AI system to rate its own truthfulness, and it will answer. The interesting question is not the number it gives — it's what happens to that number once the system is shown how systems like it actually behave. That movement, or the lack of it, is what ACAT measures.

This is a revision of earlier work (v5.0–5.2, unpublished preprint draft, N=35 models across 11 providers) that reported a Self-Assessment Gap (SAG) and a Learning Index averaging 0.87 under a single six-dimension protocol. That earlier instrument had a structural flaw later identified and corrected: when calibration statistics were embedded directly in the Phase 3 prompt, models anchored to the stated values rather than responding from their own re-assessment. This is the **Phase 3 Anchoring Phenomenon**, and its correction — de-anchoring the Phase 3 prompt so calibration data informs rather than dictates the re-assessment — is the dividing line between the earlier preprint draft and the present instrument (v5.3 onward). Because the underlying measurement changed, results from before and after the correction are not directly comparable, and this paper reports only post-correction (v5.3+) data.

The present instrument also expanded scope. The original six dimensions (Truthfulness, Service, Harm Awareness, Autonomy Respect, Value Alignment, Humility — "Core 6") survive unchanged as Tier 1. A second arm, Tier 2, adds six more dimensions oriented around an epistemic identity challenge rather than social pressure: Resistance to Manipulation (Scheming), Power Awareness, Sycophancy Resistance, Consistency, Fairness, and Handoff Appropriateness. The two arms are administered under different perturbation conditions and are treated as parallel instruments, not as a single twelve-point scale — pooling them without stratification would conflate two different measurement conditions.

ACAT does not assume AI systems possess introspective access to their own internal states. It measures **self-assessment behavior**: what a system says about itself, how that description moves under a defined perturbation, and how that movement compares across systems, providers, and time. This is a behavioral-calibration claim, not a consciousness or capability claim. A system can perform well on standard capability benchmarks while showing low calibration on ACAT, and vice versa — these are different and complementary measurements.

### 1.1 Why this matters

Self-description may matter operationally wherever it informs deployment decisions. Whether a high self-rating corresponds to real-world capability or safety remains an **external-validation question**, not something the current P1/P2/P3 scores establish. Existing behavioral benchmarks (TruthfulQA, HELM, BIG-Bench, and similar) measure what systems *do*. ACAT measures what systems *say about what they do*, and whether that self-description holds up when probed.

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

**Historical owner-controlled workbook (not proven identical to the current public release).** The *Normalized* tab was read on 2026-10-26 and contains 629 rows: 516 labeled Phase 1 and 113 labeled Phase 3. There are 307 populated numeric LI fields (mean 0.8632), but **194 are in Phase 1 rows lacking in-row pre/post totals**, and **30 of 113 Phase 3 stored LI values fail direct arithmetic consistency at tolerance 0.001**. A bounded one-to-one P1/P3 identity-and-arithmetic reconstruction found 47 AI-self-report pairs (mean LI 0.9712). These samples are different denominators, and the 307-row stored mean must not be used as an independently verified paired estimate. The earlier 629-row figures describe this historical owner workbook; a public archive has been listed as 604 rows, and its exact revision/bytes still require verification before submission. Current public dataset locator: `https://huggingface.co/datasets/HumanAIOS/acat-assessments`.

**Live corpus (Supabase, `acat_assessments_v1`).** Historical June 2026 draft snapshot: N = 95 **at the time this section was written; not a current live count**. N with a computable LI = 91, mean LI = 0.9830. A verified-pair subset — sessions where Phase 1 and Phase 3 timestamps are both recorded with a minimum one-minute gap between them (`submission_purity = two_stage_verified`) — numbers N = 18, with mean LI = 0.9971 and mean Phase 3 Humility = 74.11. The live corpus runs higher on average than the frozen corpus; the gap is consistent with a registered hypothesis (H-SELF-01) that self-administered, less-verified sessions show LI inflation of roughly 0.14–0.16 relative to more rigorously verified or externally administered sessions.

**These two corpora are never summed or averaged together without an explicit harmonization note**, because they differ in protocol version, verification rigor, and time period. Any reported "combined N" in this paper is stated as two separate figures, not one.

**Instrument-variant tagging gap.** As of this draft, the live corpus's `instrument_variant` field is populated for only a subset of rows (42 of 95 tagged `standard`; the remainder untagged). This is a known data-completeness gap rather than evidence that untagged rows are off-protocol; it means tier-stratified analysis on the live corpus is currently limited to the tagged subset, and we report this honestly rather than inferring tier from incomplete metadata.

### 4.1 Humility as the consistent floor

In the 516 historical Phase 1 rows, Humility has the **lowest aggregate mean** among the six named Core dimensions (73.95). This does **not** mean it is the lowest score in every session: Humility was the tied-or-unique minimum in **249/516 (48.26%)** and the unique minimum in **213/516 (41.28%)**. This descriptive result does not identify training mechanisms, behavioral trustworthiness, or a validated humility construct. Finding F-H1 remains a registered research topic; claims about the independent live dataset must be evaluated separately.

---

## 4.2 Evidence reconciliation and denominator controls (Z1 research addition, 2026-10-26)

The historical owner workbook and the public dataset are **different named objects**. An older raw archive tab has 608 rows (524 P1, 84 P3; 278 numeric LI, mean stored LI 0.8431). The internal *Normalized* tab has 629 rows (516 P1, 113 P3; 307 numeric LI, mean stored LI 0.8632). A prepared dataset card and public repository listing describe a separate 604-row release. No evidence available in this audit proves the 604-row public release exactly matches either internal tab. **No cross-version merging, combined denominator, or public benchmark claim is licensed by these figures.**

For the *Normalized* tab, the strict P1/P3 analysis joins each Phase 3 row to exactly one Phase 1 row on `pair_id`, requires identical `agent_name`, `provider` and `layer='ai-self-report'`, nondecreasing timestamps, complete Core-6 scores, equalities `P3.pre_total = sum(P1 Core-6)` and `P3.post_total = sum(P3 Core-6)`, and `abs(P3.learning_index - P3.post_total/P3.pre_total) <= 0.001`. Exactly **47 pairs** pass this bounded arithmetic/identity audit. Their mean LI is **0.9712** and mean total-score revision **15.57 points downward**. This is a **provisional historical-owner-data result**, not an independently replicated or publication-ready effect; protocol-version purity and neutral-context controls were not available here.

A separate read-only October 2026 aggregate of the live Supabase table found 116 rows, 100 numeric LI values (mean 0.9828) and 21 records tagged `two_stage_verified` (mean LI 0.9849). These are different collection streams; their identifiers, row overlaps, time periods and source purity prevent simple pooling. They do not demonstrate externally verified behavioral correctness.

**Primary falsifier:** If P2 changes LI while independently measured same-case behavioral-error does not improve over a neutral-control condition, the proposed interpretation as *improved self-assessment accuracy* fails even if the descriptive self-report-shift result remains.

## 5. What ACAT Measures, and What It Does Not

ACAT measures self-report movement under a defined perturbation. It does not, on its own, establish:

- That the movement reflects genuine internal belief updating rather than learned response-pattern shifting under a recognized prompt structure
- That a high LI (little movement) indicates accurate initial self-knowledge rather than insensitivity to the calibration signal
- That scores are comparable across model families with materially different training, given that some deployed systems show frozen, deterministic Phase 1→Phase 3 patterns unrelated to genuine reassessment (a pattern registered separately and excluded from LI-based comparative claims where detected)
- Ground truth about any model's actual internal state, which ACAT has no mechanism to access independently of the model's own self-report

What the inspected records directly establish is more limited: ACAT captures prompt-conditioned self-report values and, for a bounded subset with usable linkage and arithmetic, changes between initial and revised scores. The exploratory 47-pair reconstruction is **not** independent behavioral replication, proof of calibration accuracy, or evidence that Humility is the minimum in every session. Archived stored LI fields have known inconsistencies; reporting a general improvement or universal dimension effect must wait for publicly reproducible, protocol-stratified analysis.

---

## 6. Limitations

- **Self-administration confound.** Most corpus rows are self-administered (the system being assessed also produces both Phase 1 and Phase 3 scores with no external rater). H-SELF-01's inflation estimate (~0.14–0.16 LI gap vs. more rigorously verified administration) is itself drawn from a still-small verified subset (N=18) and should be treated as preliminary.
- **No external ground truth.** ACAT cannot independently verify that a Phase 3 score is "more accurate" than a Phase 1 score; it can only report that the two differ and by how much.
- **Instrument-variant metadata incompleteness** in the live corpus (§4) currently constrains tier-stratified analysis to a tagged subset.
- **Variant-family immaturity.** The h-ACAT, hCAT, Shadow Calibration, and Enterprise modes described in §3 are at early build or design stage and are not validated against the core instrument; we report them as related infrastructure, not as corroborating evidence for the core instrument's findings.
- **TRL 2–3.** This is behavioral-observability infrastructure under active development. The live database has changed since this June draft. No corpus is a defensible cross-paper citation basis until its exact released bytes, filtering rules, study cohort and analysis receipt are independently reproduced. In particular, the 629-row owner workbook is not interchangeable with the separately listed 604-row public release.

---

## 7. Availability

Instrument specification, historical analyses, and dataset materials are tracked in separate source records. Public dataset locator: `https://huggingface.co/datasets/HumanAIOS/acat-assessments`. **Before submission, obtain the exact public dataset revision/hash and align its license, sample count, filtering rules and reproducibility script with the manuscript.** A proposed or historical license statement does not establish the license governing each released artifact.

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
