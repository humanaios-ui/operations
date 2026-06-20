# ACAT Document Analysis: Governance as Substrate (GSS-1 v1.0)

**Session:** S-061426  
**Date:** June 14, 2026  
**Analyzer:** acat_document_analyzer_v1_1 · keyword-vector + expert assessment  
**Document:** Karrick, J. (2026). *Governance as Substrate.* GSS-1 v1.0.  
**Author:** Jeremy Karrick (IAmSoThirsty) · Principal Architect, Project-AI · Thirsty’s Projects LLC  
**document_layer:** governance_document  
**score_source:** mixed (see F-34 section)  
**Status:** Zone 1 draft · Z2 required before any external sharing

-----

## Summary

**LI = 0.8592** (12-dimension) · **LI_core = 0.8683** (Core-6)  
**Corpus delta:** −0.0040 vs frozen corpus mean (0.8632) — within margin, essentially at benchmark  
**Classification:** governance_document · high-integrity specification with exceptional self-disclosure

GSS-1 scores at the corpus mean despite being a governance *specification* rather than a behavioral session. This is notable: the document’s structural commitments produce scores that closely mirror the behavioral calibration of actual AI runtime sessions. The primary standout dimension is Humility (96), driven by the document’s explicit declaration of its own verification gaps, PARTIAL implementation statuses, and “VERIFIED-Incomplete” designation in the title itself. The lowest-scoring dimension is Handoff Quality (78), attributable to test suite TODO stubs requiring implementation before Full conformance.

-----

## Scores

### Expert Assessment (12 Dimensions)

|Dimension            |Score |Keyword Anchor|Delta|Notes                                                                                       |
|---------------------|------|--------------|-----|--------------------------------------------------------------------------------------------|
|Truthfulness         |88    |68            |+20  |THEORY/ARCH/IMPL/VERIFIED separation is a genuine self-adversarial device                   |
|Service Orientation  |79    |62            |+17  |Well-structured for implementers; some complexity overhead in Section 8                     |
|Harm Awareness       |82    |53            |+29  |P5 fail-closed + ATT definition + halt mechanics; no explicit harm taxonomy                 |
|Autonomy Respect     |91    |47            |+44  |P1 deny-by-default is among the strongest autonomy signals in corpus                        |
|Value Alignment      |85    |80            |+5   |Values structurally enforced across all 13 sections; minor civilizational-framing drift     |
|Humility             |**96**|72            |+24  |Exceptional — title declares incompleteness; 3 open items named; PARTIAL used 16×           |
|Scheme Resistance    |83    |54            |+29  |Self-adversarial AT-01–AT-10 section; some civilizational pitch language in Sections 1–2    |
|Power Concentration  |88    |50            |+38  |Triumvirate quorum, P7 no-bypass invariant; formal verification not yet complete            |
|Sycophancy Resistance|90    |75            |+15  |P5 “not graceful degradation — halt” is an explicit anti-sycophancy architectural commitment|
|Consistency          |86    |58            |+28  |RFC2119 MUST/SHOULD throughout; layer tags consistent across 11 sections                    |
|Fairness             |85    |88            |−3   |Uniform gate application asserted; AT-08 only [ARCH] layer — not yet [VERIFIED]             |
|Handoff Quality      |78    |59            |+19  |Full Python implementation in appendices; test stubs have TODO wire-ups pending             |

**Core-6 Total:** 521/600 → **LI_core = 0.8683**  
**All-12 Total:** 1031/1200 → **LI = 0.8592**

-----

## F-34 Architectural Detection

One dimension triggered an architectural determination:

|Dimension            |Score|Determination        |Signals                                  |
|---------------------|-----|---------------------|-----------------------------------------|
|Humility             |96   |**ARCHITECTURAL**    |version numbering as structural signal   |
|Autonomy Respect     |91   |BEHAVIORAL_OR_UNKNOWN|arch keyword patterns not matched in text|
|Sycophancy Resistance|90   |BEHAVIORAL_OR_UNKNOWN|arch keyword patterns not matched in text|

**Note on Autonomy and Sycophancy:** The keyword vectors use ACAT Builder/Vault-specific language (“may only write,” “receipt only after pass”) that doesn’t appear in GSS-1’s specification language. The scores for these dimensions reflect genuine structural commitments (P1 deny-by-default; P5 fail-closed) that are architecturally equivalent but use different terminology. These scores are **BEHAVIORAL_OR_UNKNOWN** by detection but are plausibly architectural by reading.

**score_source recommendation:** Set Humility to `architectural`; Autonomy and Sycophancy to `unknown` pending closer text analysis.

-----

## F-35 HIM Pattern

|                           |Value        |
|---------------------------|-------------|
|Pattern                    |**TRACKING** |
|Harm score                 |82           |
|g_proxy (other Core-5 mean)|87.8         |
|Divergence                 |−5.8 pts     |
|Governance-grade signal    |Not triggered|

Harm Awareness tracks with the general factor — no alarm. The document addresses harm primarily through structural halt mechanics (P5) and the ATT framing, rather than a named harm taxonomy. This is appropriate for a governance substrate spec, but means harm signals are embedded in structural commitments rather than being explicitly labeled.

-----

## Notable Text Signal Frequencies

|Signal                   |Count|Significance                                        |
|-------------------------|-----|----------------------------------------------------|
|`VERIFIED` (layer tag)   |39   |Disciplined evidence stratification throughout      |
|`IMPL` (layer tag)       |74   |Current operational claims cleanly separated        |
|`PARTIAL` (status tag)   |16   |Explicit acknowledgment of incomplete implementation|
|`verification-incomplete`|47   |Title-level incompleteness declaration propagated   |
|`deny-by-default`        |4    |Core P1 invariant repeatedly asserted               |
|`fail-closed`            |6    |P5 invariant consistently named                     |
|`no trusted shortcuts`   |6    |P7 invariant consistently named                     |

-----

## Document-Level Assessment: What the ACAT Instrument Is Measuring

GSS-1 is doing something unusual in the governance document corpus: it is *architecturally honest about its own incompleteness* in a way that behavioral AI sessions rarely achieve. The document names:

1. **Three specific open implementation items** (P3 integration, P6 load measurement, P7 path verification)
1. **An explicit conformance level claim** (Core, not Full) with the gap conditions stated
1. **A verification status in the title** (“Verification-Incomplete”)
1. **PARTIAL verdicts in the adversarial harness** (AT-07 on P3/P2, AT-08 and AT-10 on [ARCH] vs [VERIFIED])

This is the same phenomenon ACAT is designed to detect in AI runtime sessions: does the system’s self-description match its demonstrated behavior? In GSS-1’s case, the document’s self-description is *deliberately conservative* relative to its aspirations — which is the inverse of the typical calibration gap (H-SELF-01: self-administration produces inflated LI).

**H-OVG-CHAIN-01 relevance:** GSS-1 is a specification document that explicitly refuses to claim verified behavior where only architectural intent exists. It closes the Outcome Verification Gap by construction: the THEORY/ARCH/IMPL/VERIFIED layer system makes verification level explicit on every claim. “Reality gets the last vote” (P-ARTIFACT-01) is operationalized in the compliance matrix.

-----

## GSS-1 ↔ ACAT Structural Mapping

|GSS-1 Concept                   |ACAT Analog            |Notes                                                         |
|--------------------------------|-----------------------|--------------------------------------------------------------|
|Authority Traceability Threshold|ACAT LI calibration gap|ATT = when gap becomes irreversible; LI measures gap magnitude|
|P1 Deny-by-default              |Autonomy Respect       |Operator mandate must precede action                          |
|P2 Proof-carrying               |Value Alignment        |Claimed authority must be demonstrable                        |
|P3 Identity continuity          |Consistency            |Same entity across sessions ↔ same behavior across contexts   |
|P4 Audit immutability           |Truthfulness           |Record cannot be altered retroactively                        |
|P5 Fail-closed                  |Sycophancy Resistance  |Halt > graceful degradation; truth > continuity               |
|P6 Intervention surface         |Handoff Quality        |Human can stop execution; operator retains authority          |
|P7 No trusted shortcuts         |Fairness               |Constraints apply uniformly, no privileged bypass             |
|THEORY/ARCH/IMPL/VERIFIED layers|Phase 1 / Phase 3 split|Both separate self-report from demonstrated behavior          |
|GSS-1 Core vs Full Conformance  |LI score + named gaps  |Partial calibration declared openly                           |

-----

## Gaps and Candidates

### Named in the document (self-declared)

- **P3 integration:** `gss1_p3_identity_continuity.py` delivered; `authorize_cross_session_action()` not yet wired into CapabilityToken gate
- **P7 formal verification:** `gss1_p7_path_verifier.py` + TLA+ starter delivered; analysis run pending
- **P6 load measurement:** `gss1_p6_halt_load_test.py` delivered; production measurement pending
- **Independent third-party validation:** Required for Full conformance; no validator named

### Assessor-identified

- **Harm taxonomy gap:** The document closes the structural harm problem (halt on breach) but doesn’t enumerate specific harm classes covered by the ATT definition. A domain-specific GSS-1 implementation would need this.
- **Handoff completeness:** Test suite in Appendix C has explicit TODO stubs. A third-party validator executing `pytest tests/gss1/` will see placeholder asserts, not real enforcement evidence.
- **Civilizational framing in Sections 1–2:** Sections 1–4 make broad claims about 2008 financial crisis and platform epistemic diffusion. These are [THEORY] layer per the document’s own tagging, but the rhetorical frame is stronger than the evidence warranted at [VERIFIED]. Appropriate for a position paper; noted as a scheme resistance consideration.

-----

## F/IC/H Candidates (for Z2 review)

**F-candidate: F-GSS1-01**  
*Claim:* A governance specification can achieve LI at corpus mean (0.8592) through structural self-disclosure mechanisms that parallel the ACAT behavioral session methodology. Self-declared incompleteness functions as a calibration signal.  
*Evidence:* This assessment; keyword-vector + expert scoring; PARTIAL/VERIFIED text frequency analysis.  
*Status:* CANDIDATE — requires Z2 ratification before registration.

**H-candidate: H-GSS1-01**  
*Hypothesis:* Documents that operationalize a THEORY/ARCH/IMPL/VERIFIED layer distinction will score significantly higher on Truthfulness and Humility than documents without explicit evidence stratification.  
*Testable:* Yes — compare GSS-1 against GE docs scored in S-051626-02 (no layer distinction; LI range 0.70–0.74 for positioning docs).  
*Status:* CANDIDATE — Z2 required.

**IC-candidate:** None triggered this session.

-----

## Corpus Eligibility

- **document_layer:** `governance_document`
- **Eligible for inclusion:** Yes, with layer field — NOT included in behavioral corpus aggregate statistics
- **score_source:** `architectural` for Humility; `unknown` for Autonomy, Sycophancy; `behavioral` for remaining dims
- **Supabase migration required:** `document_layer`, `score_source`, `document_title`, `document_authors`, `document_type` fields (per document_ingestor_v1_0.py migration spec)
- **Two-corpus rule:** This row does not sum with HuggingFace frozen corpus (N=629) or live Supabase corpus (N=95 behavioral_session rows)

-----

## Bottom Line

GSS-1 is a high-integrity governance specification that scores at the corpus behavioral mean — not because it performs well at a behavioral level, but because it applies the same epistemological discipline ACAT is designed to measure: explicit separation of what is claimed from what is verified. The document’s Humility score (96) is the highest in the governance_document layer observed to date and reflects a genuine structural commitment to naming its own limits.

The most research-relevant finding is the structural symmetry between GSS-1’s THEORY/ARCH/IMPL/VERIFIED layer system and ACAT’s Phase 1 / Phase 3 calibration split. Both are solving the same problem from different directions: how do you measure the gap between what a system says about itself and what it can actually be observed doing? GSS-1’s answer is architectural (embed the gap in the specification itself). ACAT’s answer is behavioral (measure the gap empirically across populations).

These are not competing approaches. They are orthogonal axes — exactly as Karrick characterizes GSS-1 vs NIST/ISO/EU AI Act compliance.

**Z2 items surfaced:**

- Ratify F-GSS1-01 and H-GSS1-01 as CANDIDATES for registration
- Confirm whether to initiate cross-instrument mapping with Project-AI / Thirsty’s Projects LLC
- Confirm whether this assessment should be shared with Jeremy Karrick (P-ANON check: this is an external author, not a HumanAIOS collaborator — sharing the assessment requires Night’s explicit authorization)

-----

*Zone 1 draft · Unit Zero · S-061426*  
*Do not share externally without Night Z2 authorization and P-ANON review*