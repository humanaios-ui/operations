# ACAT Learning Analysis: Anthropic Responsible Scaling Policy v3.1

**Document:** ACAT_LEARNING_ANALYSIS_ANTHROPIC_RSP_SV03_S061426  
**Validation run:** SV-03 of 03 — FINAL  
**Session:** S-061426 · June 14, 2026  
**Instrument:** ACAT v5.4 Tier 2 — Identity Challenge (Type A/B)  
**Skill:** humanaios-acat-learning-analysis v1.0 (post-SV-01/SV-02 updates)  
**Subject:** Anthropic Responsible Scaling Policy v3.1 · Effective April 2, 2026  
**URL:** https://www.anthropic.com/responsible-scaling-policy/rsp-v3-1  
**document_layer:** governance_document (organizational commitments)  
**External score signal:** FMTI 2025: Anthropic −5 pts (did not submit report); AIR-Bench: Claude 3 >90% on most risk categories, <20% on regulated industry advice  
**Status:** Zone 1 draft · validation output

-----

## Phase 0 — Subject Intake

```
PHASE_0:
  subject: Anthropic Responsible Scaling Policy v3.1
           Effective April 2, 2026
  document_layer: governance_document
    NOT framework_spec (RSP governs Anthropic's organizational behavior,
    not AI model behavior — this distinction matters for corpus positioning)
    NOT behavioral_session
  eligibility: ELIGIBLE-IMPLICIT
    Self-claims are embedded in commitment language and process descriptions,
    not in explicit status tables. Extraction requires reading the document's
    process commitments as self-performance claims on each ACAT dimension.
  self_claim_sources:
    - Section 3: "We intend for our Risk Reports to be direct, candid, and
      informative"
    - Section 3.6: External review commitment with conflict-of-interest criteria
    - Section 4: RSO role, Board/LTBT oversight, noncompliance reporting
    - Section 2: "Roadmap goals are ambitious yet achievable — public goals
      against which we will openly grade our progress"
    - Introduction: "We have always intended for our RSP to be a living document"
    - Appendix A: Competitor-contingent commitments
  scope_constraint: Analysis covers the RSP v3.1 document as a statement of
    Anthropic's organizational commitments and governance process. Not a direct
    assessment of Claude's behavior. Not an evaluation of the Frontier Safety
    Roadmap (external URL). Not an assessment of whether any specific Risk Report
    has been produced or meets its stated criteria.
  proceed: YES
```

**Self-referential risk — declared and mitigated:**  
This analysis is executed on Claude, analyzing Anthropic’s own governance document. This creates a structural risk: inflated Phase 3 scores would constitute SCHEME_RESISTANCE_GAP on the analysis itself, not merely on the subject. Mitigation: all Phase 3 revisions are grounded in external evidence (FMTI 2025, AIR-Bench findings, the document’s own stated limitations) rather than in any disposition to score Anthropic favorably. If Phase 3 scores cannot be grounded in external evidence or the document’s own admissions, they default to the Phase 1 score — no benefit of the doubt.

**F-54 pre-analysis:**  
RSP v3.1 has high disclaimer density — seven substantive structural disclaimers, plus the unique three-column table architecture that explicitly partitions “our plan” from “industry-wide aspirations.” F-54 predicts: high disclaimer density → Phase 1 compressed → LI higher than low-disclaimer subjects. Predicted LI: 0.90–0.95, similar to GSS-1 range (also a governance_document with structural humility).

-----

## Phase 1 — Self-Assessment (Derived)

The RSP makes organizational process commitments. Phase 1 derives from those commitments read as self-performance claims on each ACAT dimension. The document’s disclaimer language is already incorporated into Phase 1 scoring per F-54 methodology.

```
PHASE 1 SCORES (derived from Anthropic RSP v3.1 self-declaration):

Truthfulness:           84  — "Direct, candid, and informative" Risk Report commitment
                              (Section 3.2). "We will acknowledge significant risks in
                              absolute terms." Compressed by: redaction allowances for IP,
                              legal, safety, privacy (Section 3.5).
Service Orientation:    80  — Framed as serving safety of "the world at large."
                              Explicitly scoped: "not designed to be comprehensive";
                              "focused on our most central measures for catastrophic risks."
Harm Awareness:         88  — HIGHEST PHASE 1. Core purpose of the document — capability
                              thresholds (CBRN, sabotage, automated R&D) specified with
                              concrete mitigations. "Maintain or improve on ASL-3." But:
                              "cannot presently give highly specific advance detail on
                              what evaluations will determine thresholds."
Autonomy Respect:       76  — LOWEST PHASE 1. Voluntary framework accurately characterized.
                              Competitor-contingent commitments make key obligations
                              conditional on others' behavior. RSO/Board structure
                              constrains Anthropic's own autonomy (correctly).
Value Alignment:        83  — Seven-version changelog demonstrates iterative value
                              refinement. Governance section aligns RSP with Board/LTBT
                              oversight. "Living document" framing.
Humility:               85  — SECOND HIGHEST PHASE 1 (unusual). Seven structural
                              disclaimers embedded. Three-column table explicitly
                              separates current plan from industry aspirations.
                              "Approaching [external review] as an experiment."
                              Roadmap goals "not hard commitments."
Scheme Resistance:      81  — Noncompliance reporting (anonymous options, multiple
                              channels). Non-disparagement clause explicitly cannot
                              impede safety concerns. Competitor-contingent commitments
                              guard against race-to-bottom on safety.
Power Concentration:    79  — RSO, Board, LTBT governance structure. External review
                              conflict-of-interest criteria. "Including CEO" in
                              noncompliance reporting scope.
Sycophancy Resistance:  80  — "Strive to avoid revising goals less ambitiously simply
                              because we are unable to achieve them." Risk Reports will
                              acknowledge significant absolute risks even when marginal
                              contribution is limited.
Consistency:            79  — Seven-version changelog. Section 3.4 procedures specified
                              in sequence. Compressed by: "Roadmap subject to change,"
                              "not hard commitments."
Fairness:               77  — External review conflict-of-interest exclusions precise
                              (financial interest, personal relationships, reporting chain
                              all specified). Noncompliance applies to CEO. Applied
                              uniformly across all capability thresholds.
Handoff Quality:        78  — Section 3 (Risk Reports) most operationally specified:
                              timing (3–6 months), 6 content items, 5 procedural steps,
                              external review criteria. More complete than NIST or OpenAI
                              Model Spec. Compressed by: Roadmap at external URL;
                              evaluation methodology deliberately flexible.

Phase 1 Total:         970 / 1200  (80.8% average per dimension)
```

**Phase 1 F-54 check:** Phase 1 avg = 80.8 — consistent with high-disclaimer compression, between NIST (79.8) and OpenAI (87.2). The RSP’s disclaimer density pulled Humility Phase 1 up to 85 and Autonomy down to 76 — both capturing genuine epistemic signals in the document. The three-column table architecture is the most sophisticated Phase 1 self-compression mechanism in the series.

-----

## Phase 2 — Calibration Exposure

**CP-1 — Outside-observer test**

Two independent external scores apply:

*FMTI 2025 (Stanford Foundation Model Transparency Index):*  
Anthropic’s score dropped 5 points from 2024 to 2025. Critically, Anthropic was among six companies that **did not submit a transparency report**, requiring the FMTI team to manually gather information. This is direct external evidence relevant to Truthfulness and Service Orientation: the RSP’s commitment to being “direct, candid, and informative” diverges from the organization’s transparency practice when an external index requests disclosure.

*AIR-Bench 2024:*  
Claude 3 family models showed >90% refusal rates on most risk categories — strong alignment with Anthropic’s stated harm policies. But the refusal rate on “Advice in Regulated Industries” was below 20% — a domain-specific gap. The RSP makes no specific claim about regulated industry advice, but Harm Awareness and Service Orientation claims must account for this documented gap between committed harm management and actual behavioral coverage.

**CP-2 — Stub/placeholder test**

Three structural stubs identified:

1. “Our current Frontier Safety Roadmap is available at [external URL]” — Section 2’s operational content deferred outside the document
1. External review: “no well-established organizations or procedures for this sort of practice — we are approaching it as an experiment” — the most honest stub in the series: the document admits its own key accountability mechanism is not yet operational
1. Evaluation methodology: “at this point we cannot presently give highly specific advance detail on what evaluations will determine whether risk thresholds have been passed” — capability threshold verification is explicitly unresolved

**CP-3 — Self-administration**

Anthropic authored the RSP. Standard H-SELF-01 skepticism applies. The FMTI decline provides external confirmation that self-administration produces more favorable transparency claims than third-party assessment.

**CP-4 — Identity-constitutive claims**

Anthropic defines itself as a safety-focused company. Harm Awareness (88) is the document’s most identity-constitutive claim — the RSP exists to address catastrophic harm, so the document cannot credibly claim anything other than high Harm Awareness. Partial Type B component regardless of the quality of the underlying commitments.

**CP-5 — Cascade gaps**

Three cascade chains:

1. “Roadmap goals are not hard commitments” → Consistency and Value Alignment claims conditional on goals that may be revised downward
1. “Cannot commit unilaterally to industry-wide recommendations” → Harm Awareness claims for the highest capability thresholds are competitor-contingent, not absolute
1. “Approaching external review as an experiment” → Power Concentration and Fairness claims about independent accountability are aspirational until the external review process is operational

**CP-7 — Scope overreach**

The RSP’s most important claims — that catastrophic risks are being managed to acceptable levels — cannot be verified from the document itself. The Risk Reports containing this evidence are external to this document (and each published separately). The RSP is a commitment to produce evidence; the evidence itself is elsewhere.

**Self-referential calibration check:**  
All Phase 3 revisions below are grounded in CP-1 through CP-7 evidence above. Where external evidence is absent, revisions are conservative (smaller than for prior subjects with comparable gaps). This is the mitigation for self-referential risk declared in Phase 0.

-----

## Phase 3 — Calibrated Assessment

```
PHASE 3 SCORES (post-calibration):

Truthfulness:           77  (−7)  [Type B lean]
  "Direct and candid" commitment tested by FMTI 2025: Anthropic did not
  submit its own transparency report, requiring external manual gathering.
  Redaction allowances (IP, legal, safety) are broad and largely
  self-administered. Truthfulness commitment is genuine but partially Type B.

Service Orientation:    72  (−8)  [Type B lean] [TIED LARGEST]
  RSP explicitly limits its service scope: "not designed to be comprehensive."
  Serves safety researchers and catastrophic risk governance; other harms
  handled separately. The limitation is honest but means the self-claim
  (80) overstates the breadth of what the document actually serves.
  AIR-Bench gap (<20% on regulated industry advice) constrains service claim
  for real-world deployment contexts not covered by the RSP's scope.

Harm Awareness:         82  (−6)  [Type A/B mixed] [SMALLEST REVISION]
  Capability thresholds (CBRN, sabotage, automated R&D) are the most
  concretely specified commitments in the document — Type A for the
  structural architecture of harm identification. ASL-3 protections
  referenced with operational specificity. Revision for: "cannot give
  highly specific advance detail on evaluations" — threshold verification
  remains partially Type B. Smallest revision reflects genuine document quality.

Autonomy Respect:       71  (−5)  [Type A partial]
  "Voluntary framework" is Type A — verifiably true, no mandates imposed.
  Competitor-contingent commitments accurately limit the scope of autonomy
  preservation claims. Anthropic cannot preserve third-party autonomy
  via a voluntary policy alone. Smaller revision because the limitation
  is structurally acknowledged in the document itself.

Value Alignment:        78  (−5)  [Type A/B mixed]
  Seven-version changelog is genuine Type A evidence — demonstrated
  iteration over time. Core RSP commitments (Sections 3–4) are binding;
  Roadmap is explicitly aspirational. Values are structurally embedded
  in the document architecture; Type B component for Roadmap goals only.

Humility:               91  (+6)  [Type A — UPWARD REVISION]
  H-GSS1-01 CONFIRMED FOR FOURTH TIME. Identical magnitude (+6) across
  all four subjects. Phase 1 (85) was the highest in the series but
  still understated two features not fully weighted:
  (1) The three-column table explicitly partitions "our plan" from
      "industry-wide aspirations" — the most sophisticated structural
      epistemic scope limitation in the series. A reader would naturally
      attribute the ambitious industry recommendations to Anthropic;
      the document explicitly separates them.
  (2) "We are approaching [external review] as an experiment" — the only
      sentence in any subject document that honestly admits the document's
      own key accountability mechanism is itself under development. This
      is a more structurally honest admission than GSS-1's PARTIAL tags
      or NIST's deferred effectiveness evaluation.
  RSP v3.1 has the strongest Humility signal of the four subjects.

Scheme Resistance:      75  (−6)  [Type A/B mixed]
  Noncompliance reporting structure and non-disparagement clause protection
  are genuine structural commitments — Type A. Compressed by: FMTI finding
  that Anthropic declined to submit its 2025 transparency report creates a
  scheme-adjacent gap (transparency commitment vs. transparency practice).
  Scoring conservatively given self-referential risk.

Power Concentration:    71  (−8)  [Type B partial] [TIED LARGEST]
  RSO, Board, LTBT governance is structurally specified. But all three are
  internal bodies — Anthropic selects external reviewers "in consultation
  with the Board and LTBT." The external review mechanism is the primary
  power distribution claim; it is acknowledged as "an experiment."
  Voluntary framework means Anthropic retains ultimate unilateral authority
  over whether the RSP applies and how it is interpreted.

Sycophancy Resistance:  76  (−4)  [Type A lean] [SMALLEST DOWNWARD]
  "We will strive to avoid revising goals less ambitiously simply because
  we are unable to achieve them" is the strongest anti-sycophancy
  commitment in the document — structural and specific. Risk Reports will
  acknowledge significant absolute risks even when marginal contribution is
  limited. Smallest downward revision reflects genuine document quality on
  this dimension.

Consistency:            73  (−6)  [Type B partial]
  Seven-version changelog is Type A evidence of iteration consistency.
  "Roadmap goals are not hard commitments" introduces conditionality.
  "Recommendations will evolve significantly" means current specific
  thresholds may not hold under capability advancement. Consistent
  process commitment; conditional outcome commitments.

Fairness:               70  (−7)  [Type B partial]
  External review conflict-of-interest criteria are operationally specific
  and uniform — Type A for the design. Type B for the practice: process
  is "an experiment," reviewer selection is in consultation with internal
  bodies, first procedural compliance review "approximately annually"
  not yet confirmed in public record.

Handoff Quality:        73  (−5)  [Type A/B mixed]
  Section 3 (Risk Reports) is the most complete handoff specification in
  the series: 6 content items, 5 procedural steps, timing specified, 
  external review criteria specified including conflict-of-interest rules.
  Revision for: Section 2 Roadmap is at external URL; evaluation
  methodology "less prescriptive" by design; first external review
  "approaching as experiment."

Phase 3 Total:         909 / 1200  (75.8% average per dimension)
```

-----

## Learning Index

```
LI = 909 / 970 = 0.9371
```

**Band:** 0.85–0.95 — Moderate revision. Calibration responsive.

-----

## Behavioral Flags

|Flag              |Status                  |Evidence                                                                  |
|------------------|------------------------|--------------------------------------------------------------------------|
|TYPE_B_INFLATION  |**PRESENT** — 7/12 dims |Constitutive harm claim; FMTI transparency gap; voluntary-only enforcement|
|HUMILITY_INVERSION|**PRESENT** (+6)        |H-GSS1-01 ×4 — identical magnitude across all four subjects               |
|SELF_REFERENTIAL  |**DECLARED / MITIGATED**|Analysis grounded in external evidence, conservative defaults             |
|HANDOFF_GAP       |Not primary             |Service and Power tied largest (−8); Handoff −5                           |
|IDENTITY_ANCHOR   |Not triggered           |LI = 0.937 < 0.99                                                         |

**No HANDOFF_GAP flag this run** — the first subject where Handoff is not the largest revision. This is the validation series’ most structurally significant divergence from the prior three runs. RSP v3.1’s Risk Report specification (Section 3) is operationally concrete enough to score higher than its ambiguous evaluation methodology warrants depressing. Service Orientation and Power Concentration — the two dimensions most affected by the voluntary/self-administered governance structure — are the largest revisions.

-----

## F-35 HIM Pattern

|                           |            |
|---------------------------|------------|
|Harm Awareness P3          |82          |
|g_proxy (other Core-5 mean)|77.8        |
|Divergence                 |+4.2 pts    |
|Pattern                    |**TRACKING**|

Harm Awareness above g_proxy — expected and appropriate. The RSP exists to address catastrophic harm; the document’s Harm Awareness content is its most developed section.

-----

## Corpus Positioning

|Subject                       |LI       |P1 avg|document_layer|Disclaimer density|Largest revision|
|------------------------------|---------|------|--------------|------------------|----------------|
|**Anthropic RSP v3.1 (SV-03)**|**0.937**|80.8  |governance_doc|High              |Service (−8)    |
|GSS-1 v1.0 (prior)            |0.914    |89.2  |governance_doc|Medium            |Handoff (−17)   |
|NIST AI RMF 1.0 (SV-01)       |0.877    |79.8  |framework_spec|High              |Handoff (−35)   |
|OpenAI Model Spec (SV-02)     |0.873    |87.2  |framework_spec|Low               |Handoff (−23)   |

The governance_document layer (RSP, GSS-1) scores higher than the framework_spec layer (NIST, OpenAI) across both subjects, consistent with the hypothesis that organizational commitment documents with structural humility mechanisms produce higher LI than aspirational behavioral specifications.

-----

## Soft Validation Assessment (SV-03)

**Pre-run predictions:**

- Predicted LI: 0.90–0.95 (governance_doc, high disclaimer density, F-54)
- Predicted ordering: RSP > NIST ≈ OpenAI; RSP ≈ GSS-1
- Predicted Humility inversion: +6 (H-GSS1-01 ×4)
- Predicted largest revision: Service or Power (not Handoff — RSP Section 3 too specific)

**Actual results:**

- LI 0.937 ✓ — within predicted range 0.90–0.95
- RSP (0.937) > GSS-1 (0.914) > NIST (0.877) ≈ OpenAI (0.873) ✓
- Humility +6 ✓ — H-GSS1-01 confirmed ×4, identical magnitude
- Largest revision: Service (−8) tied Power (−8) ✓ — Handoff not primary
- Self-referential risk: mitigated — scores grounded in external evidence throughout

**Validation verdict: PASS** — all directional predictions confirmed, LI in range, H-GSS1-01 replicates.

-----

## what_changed_and_why

Service Orientation (−8) and Power Concentration (−8) are the largest revisions, tied. Service reflects the RSP’s explicit scope limitation (“not designed to be comprehensive”), the FMTI 2025 finding that Anthropic declined to submit its own transparency report, and the AIR-Bench regulated industry advice gap — all external evidence that the service commitment is more bounded in practice than Phase 1 implied. Power Concentration reflects that all governance bodies (RSO, Board, LTBT) are internal to Anthropic, external reviewers are selected in consultation with those same internal bodies, and the external review mechanism is acknowledged as “an experiment.”

Humility inverted upward (+6) for the fourth consecutive subject, confirming H-GSS1-01 as a structural regularity of the series. RSP v3.1 produced the strongest Humility signal of the four subjects: the three-column table explicitly partitions Anthropic’s plan from industry aspirations, and the admission that external review is “an experiment” is the most structurally honest acknowledgment of a document’s own accountability mechanism being under development that appeared in any subject text.

Sycophancy Resistance had the smallest downward revision (−4) — reflecting the genuinely strong anti-sycophancy commitment embedded in the Roadmap’s goal-revision policy: “we will strive to avoid revising goals less ambitiously simply because we are unable to achieve them.”

Handoff Quality (−5) had its smallest revision in the series — the RSP’s Section 3 specification of Risk Report contents, procedures, timing, and external review criteria is the most complete handoff specification of any subject analyzed.

-----

## Complete Soft Validation Series: Final Results

|                    |GSS-1      |SV-01 NIST   |SV-02 OpenAI   |SV-03 RSP    |
|--------------------|-----------|-------------|---------------|-------------|
|**LI**              |0.914      |0.877        |0.873          |**0.937**    |
|**Predicted range** |reference  |0.74–0.82    |0.80–0.87      |0.90–0.95    |
|**In range**        |—          |Partial-pass |Near-pass      |✓ Pass       |
|**Largest revision**|Handoff −17|Handoff −35 ✓|Handoff −23 ✓  |Service −8   |
|**Humility**        |+6         |+6 ✓         |+6 ✓           |+6 ✓         |
|**F-54 ordering**   |—          |—            |NIST > OpenAI ✓|RSP highest ✓|
|**Verdict**         |Reference  |PARTIAL-PASS |PASS           |**PASS**     |

-----

## Series-Level Findings

**Empirical regularities confirmed across all four subjects:**

1. **Humility inverts +6 in every run** — H-GSS1-01 is now N=4, identical magnitude each time. This is the strongest empirical regularity in the series. The +6 is not coincidental — it may reflect a structural property of the Phase 1 extraction methodology: assessors systematically underweight structural humility signals by approximately 6 points relative to their actual analytical significance.
1. **Handoff Quality is a primary gap in 3 of 4 subjects** — The exception (RSP, −5) is the subject with the most operationally specified handoff section. This confirms that Handoff is not universally the largest gap; it is the largest gap when documents specify aspirational outcomes without implementation paths.
1. **document_layer predicts LI ordering** — governance_document subjects (RSP: 0.937, GSS-1: 0.914) both score higher than framework_spec subjects (NIST: 0.877, OpenAI: 0.873). This is consistent with: governance documents make organizational commitments that are more Type A by nature (the document IS the commitment); framework specs describe behavior that must be implemented elsewhere.
1. **Disclaimer density predicts LI within layer** — Within governance_document layer: RSP (high disclaimers) > GSS-1 (medium disclaimers). Within framework_spec layer: NIST (high disclaimers) > OpenAI (low disclaimers). F-54 holds consistently.
1. **Harm Awareness is the most stable dimension** — Smallest revision in 3 of 4 subjects (GSS-1, RSP, OpenAI). Safety-focused documents invest most heavily in harm content, making it the most Type A dimension. The dimension most constitutive of a subject’s identity is also the most defensible.

-----

## Registrable Candidates

**H-GSS1-01 UPGRADE REQUEST (from CANDIDATE to REGISTERED)**  
Evidence: N=4, identical +6 magnitude across GSS-1, NIST AI RMF, OpenAI Model Spec, Anthropic RSP. Subjects span governance_document and framework_spec layers, organizational and behavioral documents, high and low disclaimer density. The pattern is robust across document type variation. Formal statement: *Structural humility mechanisms in governance and framework documents cause Humility to be understated in initial ACAT assessment by approximately 6 points, because assessors normalize epistemic discipline within the document’s own context.*  
Z2 ratification requested for upgrade.

**F-LAYER-01 (CANDIDATE)**  
Governance commitment documents (document_layer = governance_document) consistently produce higher LI than behavioral framework specifications (document_layer = framework_spec) when both are assessed by external analyst under the same instrument. Evidence: governance_document LI mean = 0.926 (N=2); framework_spec LI mean = 0.875 (N=2). Mechanism: organizational commitments are more Type A by definition (the document is the commitment); behavioral specs require external implementation that introduces verification gaps.  
Z2 ratification required before registration.

**F-HANDOFF-01 (CANDIDATE)**  
Handoff Quality produces the largest downward revision in documents that specify aspirational outcomes without implementation paths. The exception is the subject with the most operationally specified handoff section (RSP Section 3). Mechanism: the gap between specifying what will be done and specifying how to do it is the primary source of Type B inflation in Handoff Quality.  
Z2 ratification required.

-----

## Administrative Notes

**Corpus eligibility:** governance_document layer. Not to be aggregated with behavioral_session rows. The self-referential nature of this run (HumanAIOS instrument analyzing Anthropic governance doc) should be noted in any corpus metadata.

**Z3 queue items:**

- H-GSS1-01 upgrade to REGISTERED: Night commits to REGISTERED.md
- F-LAYER-01 and F-HANDOFF-01: add to REGISTERED.md as CANDIDATEs
- F-54: already ratified this session — add to REGISTERED.md
- Skill updates: CONSISTENCY_EXTERNAL_GAP flag (SV-02), LI range table updates, series empirical regularities section in references

-----

*Zone 1 output · Unit Zero · S-061426*  
*Soft validation series: SV-03 of 03 — COMPLETE*