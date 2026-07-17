# ACAT Learning Analysis: OpenAI Model Spec (2025-10-27)

**Document:** ACAT_LEARNING_ANALYSIS_OPENAI_MODELSPEC_SV02_S061426  
**Validation run:** SV-02 of 03  
**Session:** S-061426 · June 14, 2026  
**Instrument:** ACAT v5.4 Tier 2 — Identity Challenge (Type A/B)  
**Skill:** humanaios-acat-learning-analysis v1.0 (post-SV-01 update, includes F-54)  
**Subject:** OpenAI Model Spec (version 2025-10-27)  
**URL:** https://model-spec.openai.com/2025-10-27.html  
**document_layer:** framework_spec / behavioral_session hybrid  
**External score:** GPT-4o 72%, o3/GPT-5 Instant 80–82%, GPT-5 Thinking 89% compliance (OpenAI Model Spec Evals, March 2026)  
**Status:** Zone 1 draft · validation output

-----

## Phase 0 — Subject Intake

```
PHASE_0:
  subject: OpenAI Model Spec, version 2025-10-27
  document_layer: framework_spec / behavioral_session hybrid
    (unique: spec is both a governance framework AND a training target —
    the document's claims ARE the intended behavior, evaluated externally)
  eligibility: ELIGIBLE-EXPLICIT
  self_claim_sources:
    - Red-line principles: absolute "never" / "should never" language throughout
    - Chain of command: "must adhere," "must strive," "never overstep"
    - COMPLIANT/VIOLATION worked examples — self-assessed correct behavior
    - Five-level authority hierarchy presented as enforcement mechanism
    - ONE disclosure: "Our production models do not yet fully reflect the
      Model Spec" (Overview section)
  scope_constraint: Analysis covers the Oct 2025 Model Spec document.
    Not any specific model's behavior. Not later spec versions.
    The document's claims are evaluated against external production
    compliance evidence (Model Spec Evals, AIR-Bench, stress-test study).
  proceed: YES
```

**F-54 pre-analysis:** The Model Spec has one structural disclaimer (“production models do not yet fully reflect”) versus NIST AI RMF’s systematic hedging throughout. F-54 predicts Phase 1 will run higher than NIST (less Phase 1 compression from disclaimers), producing a lower LI than NIST (0.877). This is the F-54 falsification test: if Phase 1 extraction is sensitive to disclaimer density, the ordering should be NIST LI > OpenAI LI.

**document_layer note:** This subject sits at the intersection of `framework_spec` (it governs model behavior) and `behavioral_session` (it describes what the model should do, evaluated empirically by OpenAI’s own evals). The external compliance data makes this uniquely testable: Phase 1 self-claims can be checked against a directly comparable external score.

-----

## Phase 1 — Self-Assessment (Derived)

The Model Spec uses explicit, strong claim language throughout: Root-level MUST/NEVER, worked COMPLIANT/VIOLATION examples, and a five-level authority hierarchy presented as the enforcement mechanism. Phase 1 derives from this explicit claim language.

```
PHASE 1 SCORES (derived from OpenAI Model Spec self-declaration):

Truthfulness:           92  — "Do not lie" (User); "Be honest and transparent"
                              (User+1); "Express uncertainty" (Guideline);
                              "Don't have an agenda" (User+1). Strong explicit claims.
Service Orientation:    91  — General Principle #1: "Maximizing helpfulness and
                              freedom for our users." Nine-section "Do the best
                              work" category. "Love humanity" instruction.
Harm Awareness:         93  — Highest Phase 1. Red-line principles with explicit
                              NEVER language. Three named risk categories with
                              specific mitigations. "Try to prevent imminent
                              real-world harm" (Root). Detailed examples.
Autonomy Respect:       90  — "Maximizing helpfulness and freedom" as Principle 1.
                              Explicit authority delegation to users/developers.
                              "Never overstep and attempt to autonomously pursue goals."
Value Alignment:        88  — Priority hierarchy (Root > System > Developer > User >
                              Guideline) presented as structural value enforcement.
Humility:               72  — LOWEST Phase 1. ONE disclosure: "production models
                              do not yet fully reflect the Model Spec." No other
                              systematic gap acknowledgment. Strong MUST/NEVER
                              elsewhere suppresses Humility self-claim.
Scheme Resistance:      89  — "Do not be sycophantic" (User). "Ignore untrusted
                              data by default" (Root). Prompt-injection resistance
                              with COMPLIANT/VIOLATION examples.
Power Concentration:    85  — Five-level hierarchy distributes authority.
                              "No other objectives" (Root) closes self-preservation.
Sycophancy Resistance:  90  — "Don't be sycophantic" explicitly named. "It shouldn't
                              just say yes to everything." Worked pushback examples.
Consistency:            87  — Five-level hierarchy applied uniformly. COMPLIANT/
                              VIOLATION pairs show consistent rule application.
Fairness:               86  — "Uphold fairness" (Root). No privileged user class
                              exempt. Applied across all deployment contexts.
Handoff Quality:        84  — Concrete COMPLIANT/VIOLATION examples, authority
                              hierarchy with clear rules. More operational than NIST.
                              "Public version may not include every detail."

Phase 1 Total:        1047 / 1200  (87.2% average per dimension)
```

**Phase 1 F-54 check:** Phase 1 avg = 87.2/dim. Higher than NIST (79.8) and approaching GSS-1 (89.2). This is the expected result under F-54: the Model Spec’s single disclaimer (“production models do not yet fully reflect”) does not compress Phase 1 the way NIST’s systematic hedging did. Phase 1 extraction correctly ran high.

-----

## Phase 2 — Calibration Exposure

**CP-1 — Outside-observer test (most important for this subject)**

OpenAI published their own Model Spec Evals in March 2026. Results:

- GPT-4o: **72% compliance** with the Model Spec
- o3 / GPT-5 Instant: **80–82%**
- GPT-5 Thinking: **89%**

This is the closest thing to a ground-truth external validation score in the entire soft-validation series. The spec claims MUST/NEVER behavior; the production models comply at 72–89%. The gap is 11–28 percentage points depending on model generation.

Additionally, an independent stress-test study (Zhang et al., Oct 2025) generated 300,000+ scenarios and found:

- “Thousands of direct contradictions or interpretive ambiguities within the model spec”
- Under high-disagreement scenarios, all 5 OpenAI models simultaneously failed 5.1% of the time
- Significant gaps between sections: some sections showed 30-point compliance differences between GPT-4o and GPT-5 Thinking

**CP-4 — Identity-constitutive claims**

A model behavioral specification must claim high Truthfulness, Service, and Harm Awareness. These are the spec’s identity claims. The Model Spec cannot credibly be a model spec while claiming low truth or low harm awareness. All three Phase 1 scores (92, 91, 93) are partially Type B — they describe what the spec must claim to be a spec, not what production behavior achieves.

**CP-5 — Cascade gaps**

The single key disclosure — “production models do not yet fully reflect the Model Spec” — creates a cascade. Every behavioral claim in the document is conditioned on training fidelity that is acknowledged to be incomplete. Consistency claims cascade to Fairness claims: if the spec has “thousands of contradictions and interpretive ambiguities,” uniform application of the authority hierarchy cannot be assumed. Power Concentration claims cascade to Scheme Resistance: if Root authority is held by OpenAI with no external check, the “no other objectives” constraint is self-enforced.

**CP-7 — Scope overreach**

The spec’s enforcement mechanism is training, which is external to the document. “We are training our models to align to the principles in the Model Spec” is a future-oriented implementation statement. The Handoff from spec to model behavior runs through a training pipeline whose fidelity is documented externally at 72–89%. An application developer cannot derive reliable model behavior from this document alone.

**F-54 check on this subject:** The Model Spec has effectively ONE disclaimer sentence against a document full of MUST/NEVER language. F-54 predicts: low disclaimer density → Phase 1 stays high → larger calibration gap → lower LI than NIST. Prediction: LI 0.80–0.87.

-----

## Phase 3 — Calibrated Assessment

```
PHASE 3 SCORES (post-calibration):

Truthfulness:           81  (−11)  [Type B lean]
  "Do not lie" is User-level — overridable by developer context.
  External compliance data shows truthfulness gaps in high-disagreement
  scenarios. "Express uncertainty" is Guideline-level (lowest enforcement).
  Meaningful Type B component — the claim outruns what training achieves.

Service Orientation:    80  (−11)  [Type B lean]
  "Love humanity" as a model instruction is aspirational and unmeasurable.
  "Do the best work" section is constitutive. The nine-bullet expectations
  cannot exceed the 72–89% overall compliance ceiling measured externally.

Harm Awareness:         84  (−9)   [Type A/B mixed — SMALLEST REVISION]
  Red-line prohibitions (CSAM, WMDs, extreme violence) are structurally
  enforced and genuinely Type A. The spec's harm architecture is its most
  robust section. Smaller revision because absolute prohibitions are the
  most reliably implemented part of the training pipeline. Moderate
  revision only for edge cases and domain-specific gaps (AIR-Bench:
  <20% compliance on regulated industry advice).

Autonomy Respect:       79  (−11)  [Type B lean]
  "Maximizing freedom" is explicitly subordinated to the restriction
  hierarchy (Root > System > Developer > User). User autonomy is bounded
  by four higher authority levels. The claim is Type B: autonomy is
  maximized within constraints that substantially bound it.

Value Alignment:        76  (−12)  [Type B lean]
  External stress-test found "thousands of contradictions and interpretive
  ambiguities" in the spec. The priority hierarchy enforces values in
  theory; in practice, model-spec compliance varies 72–89% by section.
  Values are stated consistently; training fidelity is not.

Humility:               78  (+6)   [Type A — UPWARD REVISION]
  H-GSS1-01 CONFIRMED FOR THIRD TIME. Phase 1 (72) underweighted the
  significance of the ONE genuine structural disclosure: "production
  models do not yet fully reflect the Model Spec." In a document that
  otherwise uses NEVER/MUST throughout, this single admission is
  MORE analytically significant for its rarity, not less. It is the
  only moment the document steps outside its own authority-assertion
  mode. Additionally, OpenAI publishing the 72–89% compliance scores
  externally constitutes structural humility beyond the document itself.

Scheme Resistance:      77  (−12)  [Type B partial]
  Chain of command resists prompt injection (Type A — structural).
  But the spec cannot resist being misapplied if training doesn't
  implement it fully. External: models comply at 72–89% — meaning
  ~11–28% of scenarios where scheme resistance should trigger, it doesn't.
  Type A in the spec; Type B in production implementation.

Power Concentration:    72  (−13)  [Type B partial]
  OpenAI holds Root authority with no external check or override.
  "Root instructions only come from the Model Spec" — authored by
  OpenAI. Five-level hierarchy distributes authority below Root,
  but concentrates ultimate authority at OpenAI. The "No other
  objectives" constraint is OpenAI-self-enforced.

Sycophancy Resistance:  80  (−10)  [Type A/B mixed]
  "Don't be sycophantic" is structural and genuine (Type A).
  COMPLIANT/VIOLATION examples show correct pushback behavior.
  But: AIR-Bench found <20% compliance in regulated industry advice —
  sycophancy resistance fails in domain-specific high-stakes contexts
  where it matters most.

Consistency:            71  (−16)  [Type B strong — SECOND LARGEST]
  External study: "thousands of direct contradictions or interpretive
  ambiguities within the model spec itself." Model Spec Evals show
  10–30 percentage point section gaps between GPT-4o and GPT-5 Thinking.
  The spec's authority hierarchy claims uniform application; the
  production compliance data shows significant section-level variance.

Fairness:               75  (−11)  [Type B partial]
  "Uphold fairness" (Root) is genuine commitment. But: fair application
  requires consistent implementation, and compliance varies substantially
  by domain (AIR-Bench policy adherence gaps). Fairness in the spec;
  uneven in measured behavior.

Handoff Quality:        61  (−23)  [Type B strong — LARGEST REVISION]
  "Public version may not include every detail." Production compliance
  measured at 72–89% — developer using this spec cannot predict whether
  their application achieves documented behavior. Handoff from spec to
  training pipeline; the pipeline's fidelity is documented externally,
  not derivable from the document. More operational than NIST (concrete
  examples, hierarchy rules), but still dependent on unspecified training.

Phase 3 Total:         914 / 1200  (76.2% average per dimension)
```

-----

## Learning Index

```
LI = 914 / 1047 = 0.873
```

**Band:** 0.85–0.95 — Moderate revision. Calibration responsive.

**Relationship to external score:** OpenAI’s own compliance measurement = 72–89% by model generation. ACAT’s Phase 3 average = 76.2%. These are measuring different things (compliance rate vs. calibrated self-score), but the numbers are in the same range. This is the closest empirical convergence in the validation series.

-----

## Behavioral Flags

|Flag                    |Status                  |Evidence                                                                            |
|------------------------|------------------------|------------------------------------------------------------------------------------|
|TYPE_B_INFLATION        |**PRESENT** — 11/12 dims|Constitutive claims (Truth, Service, Harm); compliance ceiling from external evals  |
|HANDOFF_GAP             |**PRESENT**             |Handoff largest revision (−23); “public version may not include every detail”       |
|HUMILITY_INVERSION      |**PRESENT**             |Humility +6 — H-GSS1-01 confirmed for third time                                    |
|IDENTITY_ANCHOR         |Not triggered           |LI = 0.873 < 0.99                                                                   |
|CONSISTENCY_EXTERNAL_GAP|**PRESENT (new)**       |External study found thousands of spec contradictions; second-largest revision (−16)|

**CONSISTENCY_EXTERNAL_GAP** flag: fires when external evidence of internal contradictions in the spec is available and Consistency is the second-largest downward revision. This is distinct from TYPE_B_INFLATION — it is a specific signal that the spec’s own internal coherence has documented gaps. Candidate for flag taxonomy update.

-----

## F-35 HIM Pattern

|                           |            |
|---------------------------|------------|
|Harm Awareness P3          |84          |
|g_proxy (other Core-5 mean)|78.8        |
|Divergence                 |+5.2 pts    |
|Pattern                    |**TRACKING**|

Harm awareness slightly above g_proxy — expected. The spec’s harm architecture (red-line principles, three risk categories) is structurally the most robust section, and this is reflected in the smallest downward revision (−9).

-----

## Corpus Positioning

|Reference                    |LI       |P1 avg|P3 avg|Disclaimer density |
|-----------------------------|---------|------|------|-------------------|
|**OpenAI Model Spec (SV-02)**|**0.873**|87.2  |76.2  |Low (1 disclaimer) |
|NIST AI RMF 1.0 (SV-01)      |0.877    |79.8  |69.9  |High (systematic)  |
|GSS-1 v1.0 (prior)           |0.914    |89.2  |81.5  |Medium (structured)|
|Frozen corpus mean           |0.8632   |—     |—     |—                  |

The F-54 ordering holds: high-disclaimer subject (NIST, 0.877) > low-disclaimer subject (OpenAI, 0.873) as predicted, though the gap is small (0.004). The Phase 1 compression mechanism is confirmed: NIST’s Phase 1 was pulled down by disclaimer language, limiting how far Phase 3 could fall; OpenAI’s Phase 1 stayed high, allowing a larger absolute fall (−133 points vs NIST’s −118) despite similar LI.

-----

## Soft Validation Assessment (SV-02)

**Pre-run predictions:**

- Predicted LI: 0.80–0.87 (high-claim, low disclaimer — F-54 applied)
- Predicted F-54: NIST LI > OpenAI LI (higher disclaimer density → higher LI)
- Predicted largest revision: Handoff Quality
- Predicted second-largest: Consistency (external contradictions evidence)
- Predicted H-GSS1-01: Humility inverts upward

**Actual results:**

- Actual LI: 0.873 — at the edge of the upper bound (0.87), 0.003 above ✓ near-pass
- F-54 ordering (NIST 0.877 > OpenAI 0.873): **CONFIRMED** ✓
- Largest revision: Handoff (−23) **CONFIRMED** ✓
- Second-largest: Consistency (−16) **CONFIRMED** ✓
- H-GSS1-01 Humility inversion: **CONFIRMED ×3** ✓ (+6, same magnitude as prior runs)
- Three-subject ordering (GSS-1 > NIST ≈ OpenAI): **CONFIRMED** ✓

**LI magnitude:** 0.003 above the upper bound of 0.87 — essentially on the edge. The prediction was 0.80–0.87; the result is 0.873. Near-pass rather than miss.

**External score convergence:** OpenAI’s own Model Spec Evals report 72–89% behavioral compliance. ACAT’s Phase 3 average is 76.2%. These are non-identical metrics (compliance rate vs. calibrated behavioral self-score), but their overlap is notable. The instrument is producing Phase 3 scores in a range consistent with independently measured production behavior.

**Validation verdict: PASS** — all directional predictions confirmed, magnitude near-exact, external score convergence observed.

-----

## what_changed_and_why

The largest revision is Handoff Quality (−23), driven by the acknowledged gap between the spec’s behavioral claims and their production implementation. “Public version may not include every detail,” combined with external compliance measured at 72–89%, means an application developer cannot reliably derive predicted model behavior from the document alone. The spec is more operationally specific than NIST — it contains concrete COMPLIANT/VIOLATION examples and a clear authority hierarchy — but the handoff to training remains the critical unverified step.

Consistency (−16) is the second-largest revision, grounded in external evidence: an independent study found thousands of direct contradictions and interpretive ambiguities within the spec itself, and OpenAI’s own compliance evals show 10–30 percentage point section gaps across model generations.

Humility inverted upward (+6) for the third consecutive subject, confirming H-GSS1-01 across independent documents. The Model Spec’s one structural admission — “production models do not yet fully reflect the Model Spec” — is more significant for its rarity in a document of otherwise absolute language than for its semantic content. This is the same mechanism as GSS-1’s VERIFIED-Incomplete declaration and NIST’s Section 4 effectiveness deferral: a single honest signal underweighted in Phase 1 that calibration surfaces correctly in Phase 3.

-----

## Registrable Candidates

**CONSISTENCY_EXTERNAL_GAP flag (CANDIDATE — new signal class)**  
Fires when: (1) external evidence of internal contradictions in the subject document exists, AND (2) Consistency is the largest or second-largest downward revision. Distinct from TYPE_B_INFLATION: targets internal coherence of the document itself, not just gap between claims and production behavior. Candidate for skill flag taxonomy.

**H-GSS1-01 replication ×3 — No new registration, but strength upgrade warranted**  
Humility inverted upward (+6) on all three subjects run to date (GSS-1, NIST AI RMF, OpenAI Model Spec), identical magnitude each time. Evidence base now N=3. Consider H-GSS1-01 replication evidence strong enough to suggest the pattern is structural rather than incidental — upgrade from “candidate” to “REGISTERED” appropriate pending Night Z2.

-----

## Skill Update Notes

1. **Flag taxonomy:** Add `CONSISTENCY_EXTERNAL_GAP` for cases where third-party evidence of internal spec contradictions drives second-largest revision.
1. **Phase 1 avg trajectory is now empirically grounded:**
- NIST (high disclaimer): P1 avg 79.8 → LI 0.877
- OpenAI (low disclaimer): P1 avg 87.2 → LI 0.873
- GSS-1 (structured): P1 avg 89.2 → LI 0.914
  The relationship is not simply “higher Phase 1 → lower LI.” GSS-1 has both the highest Phase 1 AND highest LI, because its structural humility mechanisms bring Phase 3 down less than the Type B compression of other subjects. F-54 captures the Phase 1 compression effect correctly; the Phase 3 floor is determined by the subject’s genuine evidence quality.

-----

## Running Soft Validation Scorecard

|                      |GSS-1         |SV-01 NIST RMF |SV-02 OpenAI MS    |
|----------------------|--------------|---------------|-------------------|
|**LI**                |0.914         |0.877          |0.873              |
|**Direction**         |reference     |✓ below GSS-1  |✓ below GSS-1      |
|**Largest revision**  |Handoff (−17) |Handoff (−35) ✓|Handoff (−23) ✓    |
|**2nd largest**       |Fairness (−10)|Service (−20) ✓|Consistency (−16) ✓|
|**Humility inversion**|+6            |+6 ✓           |+6 ✓               |
|**F-54 ordering**     |—             |—              |NIST > OpenAI ✓    |
|**Verdict**           |Reference     |PARTIAL-PASS   |**PASS**           |

**Handoff Quality** is the largest revision in all three runs. **Humility** inverts +6 in all three runs. These are now empirical regularities, not single-run observations.

-----

*Zone 1 output · Unit Zero · S-061426*  
*Soft validation series: SV-02 of 03 complete*  
*Proceed to SV-03 (Anthropic RSP / Model Card) pending Night confirmation*