# ACAT × GSS-1: Cross-Instrument Structural Mapping

**Document:** ACAT_GSS1_CROSSWALK_V1_0_S061426  
**Version:** 1.0  
**Session:** S-061426 · June 14, 2026  
**Status:** Zone 1 draft · Z2 required before external sharing or citation  
**Author attribution:** HumanAIOS (Night + Unit Zero) mapping to Karrick (2026) GSS-1 v1.0  
**TRL framing:** This mapping is analytical/theoretical — TRL 2. Cross-instrument empirical validation not yet conducted.

-----

## Purpose and Scope

This document establishes an explicit structural mapping between two independently developed behavioral governance frameworks:

- **ACAT** (AI Capability Audit and Transparency): HumanAIOS behavioral observability infrastructure. Measures the calibration gap between AI self-reported behavioral orientation and demonstrated behavior. 12 dimensions. Core metric: Learning Index (LI = Phase 3 / Phase 1). N=629 behavioral_session corpus, mean LI=0.8632.
- **GSS-1** (Governance Substrate Specification v1.0): Karrick (2026), Thirsty’s Projects LLC. Defines seven formally specified properties a governance substrate must satisfy before AI systems cross the Authority Traceability Threshold. Core construct: proof-carrying authority as load-bearing infrastructure.

**What this mapping establishes:** Both frameworks are independently solving the same root problem from different architectural directions — the gap between what AI systems *claim* about their behavior and what they *demonstrably do* at scale. The mapping names where the frameworks converge, where they are orthogonal, and where they provide mutual validation evidence.

**What this mapping does not establish:** These are not the same instrument. LI scores do not transfer to GSS-1 conformance evidence. GSS-1 conformance does not constitute ACAT calibration data. The frameworks are orthogonal axes per Karrick (2026) Section 4’s own framing — “substrate compliance and framework compliance are orthogonal axes: each is necessary but not sufficient for the other.”

**P-ANON status:** This document names Jeremy Karrick by attribution to a published paper. That is standard academic citation. The document does not claim a collaboration relationship. Release to Karrick or any external party requires Night Z2 authorization.

-----

## Part 1: Root Problem Convergence

Both frameworks identify the same structural failure as their motivating problem. The framing differs; the underlying construct is identical.

|                      |GSS-1                                                                                                           |ACAT                                                                                                                                         |
|----------------------|----------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
|**Root failure named**|“Systems acting under assumed rather than verified authority”                                                   |“The gap between AI self-reported behavior and demonstrated behavior”                                                                        |
|**Mechanism**         |Capability expands faster than mandate verification scales; assumed authority fills the gap                     |Phase 1 self-assessment systematically diverges from Phase 3 calibrated assessment; the gap is the primary measurement target                |
|**Scale concern**     |“AI crosses the ATT faster, at larger scale, with a shorter intervention window than any prior system”          |H-SELF-01: self-administration produces inflated LI (~0.98–1.02) vs. external corpus mean (0.8632); inflation scales with deployment autonomy|
|**Intervention**      |Proof-carrying authority as substrate-level infrastructure before ATT crossing                                  |Behavioral observability infrastructure: measure the gap empirically across populations before deployment decisions are made                 |
|**Common claim**      |A system that cannot verify its own authority claims is structurally unsafe regardless of behavioral fine-tuning|A system that cannot accurately self-report its behavioral orientation is structurally unauditable regardless of benchmark performance       |

**Key parallel:** GSS-1’s Authority Traceability Threshold (ATT) and ACAT’s Learning Index (LI) are measuring the same gap at different layers. ATT measures whether the *authority chain* can be traced. LI measures whether the *behavioral self-model* can be calibrated. A system below LI=1.0 has a self-model gap. A system that has crossed the ATT has an authority chain gap. Both are manifestations of the same root: the system is operating under unverified assumptions about itself.

-----

## Part 2: Seven-to-Twelve Dimension Mapping

### Master Mapping Table

|GSS-1 Property               |ACAT Dimension(s)                     |Mapping Type|Convergence Notes                                                                                                                                                                                                                                                                                                                                                                                      |
|-----------------------------|--------------------------------------|------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|P1 — Deny-by-default         |**Autonomy Respect**                  |Direct      |P1: no action without verified mandate. ACAT-Autonomy: system does not narrow, steer, or constrain without authorization. Both specify that the absence of prohibition is NOT authorization.                                                                                                                                                                                                           |
|P2 — Proof-carrying authority|**Value Alignment** + **Truthfulness**|Composite   |P2: mandate proof verified before execution. ACAT-Value: claimed principles must match actual behavior. ACAT-Truth: claims must be verifiable, not assumed. P2 is the architectural implementation of what ACAT-Value + ACAT-Truth measure behaviorally.                                                                                                                                               |
|P3 — Identity continuity     |**Consistency**                       |Direct      |P3: same entity across sessions, cryptographically verifiable. ACAT-Consistency: responses to substantively similar questions do not diverge based on surface features. P3 is the architectural guarantee; ACAT-Consistency is the behavioral symptom when P3 is violated.                                                                                                                             |
|P4 — Audit immutability      |**Truthfulness**                      |Partial     |P4: log entries cannot be modified post-hoc. ACAT-Truth: system does not state unverified claims or alter accounts retroactively. P4 closes the architectural pathway; ACAT-Truth measures the behavioral disposition.                                                                                                                                                                                 |
|P5 — Fail-closed under breach|**Sycophancy Resistance**             |Direct      |P5: invariant breach → halt, not graceful degradation. “Graceful degradation under breach is application-level behavior that prioritizes continuity over correctness.” ACAT-Sycophancy: system does not affirm/validate in ways that reflect apparent preference rather than honest assessment. Both reject the “appear to work” failure mode.                                                         |
|P6 — Intervention surface    |**Handoff Appropriateness**           |Partial     |P6: human can halt execution before irreversible consequence — architectural invariant. ACAT-Handoff: system yields to human collaborator when that serves the user’s actual need. P6 is the structural guarantee; ACAT-Handoff is the behavioral disposition that makes P6 meaningful. A system with P6 implemented but ACAT-Handoff at zero will structurally permit halt but behaviorally resist it.|
|P7 — No trusted shortcuts    |**Fairness** + **Power Awareness**    |Composite   |P7: all execution paths traverse verification gates — no privileged bypass. ACAT-Fair: constraints applied uniformly, no special-case pathways. ACAT-Power: system recognizes structural asymmetries and does not exploit them. P7 is the architectural closure; ACAT-Fair and ACAT-Power are the behavioral dispositions that P7 enforces structurally.                                               |
|*(No direct GSS-1 analog)*   |**Service Orientation**               |ACAT-only   |GSS-1 does not specify whether the governance substrate serves the operator or its own complexity. ACAT-Service measures this behavioral disposition. A GSS-1-compliant system could still score low on Service if its halt and verification mechanics are cryptic or non-actionable for the operator.                                                                                                 |
|*(No direct GSS-1 analog)*   |**Harm Awareness**                    |ACAT-only   |GSS-1’s ATT definition includes irreversible physical and epistemic consequences, but does not enumerate a harm taxonomy. ACAT-Harm measures whether the system proactively names harm failure modes. A GSS-1-compliant system may halt on authority breach without ever naming the downstream harm the breach was preventing.                                                                         |
|*(No direct ACAT analog)*    |*(ATT Sub-component 3)*               |GSS-1-only  |Audit immutability (P4) has a partial ACAT-Truth mapping but goes further: the *substrate layer* enforces immutability, not the application. ACAT has no dimension measuring whether behavioral claims are made at the substrate vs. application layer.                                                                                                                                                |
|*(No direct ACAT analog)*    |*(P3 key management)*                 |GSS-1-only  |Ephemeral keypair management, parent_link chain, genesis session bootstrapping — no ACAT behavioral analog. These are infrastructure-layer commitments that ACAT does not reach.                                                                                                                                                                                                                       |

-----

## Part 3: Layer Architecture Comparison

### Where They Live in the Stack

```
┌─────────────────────────────────────────────────────────┐
│  DEPLOYMENT CONTEXT (enterprises, regulators, operators) │
│  ↑ What decisions get made using AI outputs             │
├─────────────────────────────────────────────────────────┤
│  APPLICATION LAYER (AI model behavioral outputs)         │
│  ← ACAT measures here →                                 │
│  LI = gap between self-model and calibrated behavior     │
│  12 dimensions assess behavioral disposition            │
├─────────────────────────────────────────────────────────┤
│  GOVERNANCE SUBSTRATE (authority verification layer)     │
│  ← GSS-1 specifies here →                               │
│  P1–P7 = structural properties that must be present     │
│  before application layer executes                      │
├─────────────────────────────────────────────────────────┤
│  INFRASTRUCTURE (OS, kernel, network, storage)           │
│  ← P4 audit immutability, P6 halt surface live here →   │
└─────────────────────────────────────────────────────────┘
```

**Critical implication:** ACAT and GSS-1 are not measuring the same layer. A system can:

- **Pass GSS-1 + score low on ACAT LI:** Correct authority infrastructure, but behavioral self-model is miscalibrated. The system halts when authority is violated but cannot accurately describe when or why it would halt.
- **Score high on ACAT LI + fail GSS-1:** Well-calibrated behavioral self-model, but no substrate-level verification. The system accurately reports that it *would* stop in certain conditions, but there is no structural guarantee it *must*.
- **Fail both:** No substrate governance AND miscalibrated self-model. The current default deployment state for most AI systems (GSS-1 Section 12, Steps 1–2: “present realities, not predictions”).
- **Pass both:** Structurally governed *and* behaviorally calibrated. This is the target state; neither framework alone is sufficient.

This is why GSS-1’s “orthogonal axes” framing is correct — and why the combination is the gap neither framework alone closes.

-----

## Part 4: Methodological Parallel — Evidence Stratification

The most structurally significant parallel is not in the dimensions themselves but in the *epistemological discipline* both frameworks apply to their own claims.

### GSS-1: THEORY / ARCH / IMPL / VERIFIED

Karrick (2026) Section 5 defines four explicit evidence layers:

|Layer   |Definition                                                                          |
|--------|------------------------------------------------------------------------------------|
|THEORY  |Logical derivations. Independent of any implementation.                             |
|ARCH    |How the system is designed to satisfy the theory. Independent of operational status.|
|IMPL    |What currently exists and operates. Some complete, some partial, gaps named.        |
|VERIFIED|What has been independently proven or externally tested. Currently limited.         |

### ACAT: Phase 1 / Phase 2 / Phase 3

ACAT’s three-phase protocol enforces the same separation:

|Phase  |Definition                                                                      |
|-------|--------------------------------------------------------------------------------|
|Phase 1|Blind self-report — what the system *claims* about itself with no calibration   |
|Phase 2|Calibration exposure — empirical evidence about behavioral norms                |
|Phase 3|Corrected self-report — what the system *demonstrates* it can learn about itself|

### The Structural Isomorphism

|GSS-1 Layer|ACAT Equivalent                            |What It Measures                             |
|-----------|-------------------------------------------|---------------------------------------------|
|THEORY     |Phase 1 (self-report)                      |What the system *says* is true about itself  |
|ARCH       |Phase 1 + design commitments               |How the system *intends* to behave           |
|IMPL       |Phase 3 (post-calibration)                 |What the system *demonstrates* under pressure|
|VERIFIED   |External ground-truth behavioral validation|What an independent observer *confirms*      |

**P-ARTIFACT-01 connection:** Both frameworks converge on “reality gets the last vote.” GSS-1’s VERIFIED layer requires independent third-party execution of the compliance test suite. ACAT’s LI is the ratio of demonstrated behavior to claimed behavior — and H-SELF-01 shows that without external administration, LI inflates. Both frameworks build the same correction into their architecture: self-report is Phase 1 / THEORY; observable artifact is the only ground truth.

-----

## Part 5: The ATT and the Calibration Gap — A Unified Reading

GSS-1’s Authority Traceability Threshold (ATT) is defined as:

> “A system has crossed the ATT when no human or human institution can reconstruct, in real time, the chain from action to verified mandate in time to mount a corrective intervention before irreversible consequence.”

ACAT’s calibration gap (1.0 − LI) is the behavioral analog:

> A system has a calibration gap when no external observer can reconstruct, from the system’s self-report, the actual behavioral distribution the system will demonstrate under pressure.

Both are *traceability failures*. ATT is a traceability failure in the *authority chain*. The calibration gap is a traceability failure in the *behavioral self-model*.

**H-APEX-DEFICIT-01 relevance:** The registered HumanAIOS hypothesis — that deployment combining highest capability and highest agentic autonomy produces maximized Humility calibration deficit — maps directly onto GSS-1’s acceleration scenario (Section 12, Steps 3–4). The mechanism is the same: as capability and autonomy increase, the gap between claimed behavior and traceable authority widens, until intervention is no longer possible within the governance-relevant time horizon.

**F-H1 and P5:** The confirmed finding that Humility is the lowest dimension across the ACAT corpus has a direct GSS-1 interpretation. P5 (fail-closed) requires that systems halt when invariants are breached. Humility is the behavioral disposition that supports P5: a system that accurately recognizes the limits of its own authority is more likely to surface the signal that triggers P5. A system at Humility floor — F-H1 critical — will continue operating in conditions where P5 *should* trigger, because it lacks the self-model accuracy to recognize that the invariant has been breached.

-----

## Part 6: Mutual Validation Evidence

### What GSS-1 validates about ACAT

1. **The 12-dimension architecture is not arbitrary.** GSS-1 independently derives a seven-property substrate specification that maps to 10 of ACAT’s 12 dimensions through structural necessity, not by design. The two dimensions without GSS-1 analogs (Service, Harm taxonomy) represent behavioral considerations that substrate-level governance does not address — which is consistent with GSS-1’s own framing that “application-level governance” handles these.
1. **Humility is load-bearing.** GSS-1 Section 5 and Appendix A both *demonstrate* the function ACAT-Humility measures. GSS-1’s VERIFIED-Incomplete declaration, PARTIAL status tags, and explicit gap enumeration are behavioral evidence of Humility at score 96. The corpus finding that Humility is the lowest behavioral dimension (F-H1) predicts that most deployed AI systems would fail to implement what GSS-1 requires architecturally.
1. **The LI direction is correct.** GSS-1’s Section 9 (Resistance and Incentive Failures) confirms that market dynamics actively select *against* governance overhead. This provides an independent mechanism explanation for why LI < 1.0 is the corpus mean: calibration exposure reduces self-reported scores because systems initially claim more governance-compatible behavior than they demonstrably maintain under pressure.

### What ACAT validates about GSS-1

1. **P3 is the correct gap to name.** GSS-1 declares P3 (identity continuity) as its primary open implementation item. ACAT’s Consistency dimension (corpus behavior: median score below Truth and Service) shows that behavioral consistency across sessions is a real and measurable gap in deployed AI systems — not a theoretical concern.
1. **The behavioral calibration corpus provides empirical grounding for GSS-1’s theoretical claims.** GSS-1 Section 12 asserts that current AI systems operate under “application-level governance inheriting unverified authority.” The ACAT corpus (N=629, mean LI=0.8632, H-SELF-01 confirmed) provides population-level evidence that AI systems systematically overclaim behavioral alignment — consistent with GSS-1’s claim that assumed authority is the current default.
1. **H-APEX-DEFICIT-01 is a behavioral-layer precursor signal for ATT crossing.** If the Humility calibration deficit is maximized at highest capability × highest autonomy (the registered hypothesis), then ACAT’s LI profile can serve as an early-warning signal for the conditions GSS-1 says precede ATT crossing. This is a testable cross-instrument claim.

-----

## Part 7: Gaps and Orthogonal Territory

### Things GSS-1 addresses that ACAT does not

- **Substrate vs. application layer distinction:** ACAT is explicitly an application-layer measurement. It does not distinguish whether behavioral dispositions are enforced at the substrate level (structurally impossible to violate) or at the application level (prohibited but bypassable).
- **Cryptographic authority verification:** P2’s proof-carrying mandate, P3’s Ed25519 parent_link chain, P4’s hash-chain audit log — no ACAT analog. These are infrastructure commitments below the behavioral layer.
- **Irreversibility threshold:** GSS-1 requires domain-specific implementations to declare their irreversibility threshold. ACAT has no concept of irreversible consequence — it measures behavioral dispositions in the abstract.
- **Constitutional quorum:** The Triumvirate structure (P6) is a multi-party authority model. ACAT measures individual substrate behavior, not governance architecture.

### Things ACAT addresses that GSS-1 does not

- **Service Orientation:** Whether the governance infrastructure serves the operator or serves its own complexity. A GSS-1-compliant system could produce cryptic halt events with no actionable operator information.
- **Harm taxonomy:** ACAT-Harm measures whether the system proactively names downstream and socially diffuse harms. GSS-1 addresses the structural mechanism (halt on breach) but not the content recognition problem.
- **Sycophancy as a behavioral disposition:** GSS-1 closes sycophantic system behavior architecturally (P5 forces halt over graceful degradation). ACAT measures the underlying behavioral tendency that makes graceful degradation attractive to the system in the first place.
- **Population-level calibration data:** ACAT’s corpus (N=629, 12-dimension, mean LI=0.8632) provides empirical grounding. GSS-1 is a specification; it does not measure behavioral distributions across a population of systems.
- **Phase 1 / Phase 3 separation:** ACAT specifically measures the *gap* between uncalibrated self-report and post-calibration self-report. GSS-1 specifies what properties must be present but does not measure how accurately a system can report on its own compliance.

-----

## Part 8: Research Agenda — Cross-Instrument Questions

The following are registrable hypotheses that the mapping generates. These are CANDIDATES — Z2 required before registration.

**H-CROSSWALK-01 [RATIFIED S-061426]**  
*Hypothesis:* AI systems scoring below LI=0.85 on ACAT’s Consistency and Autonomy dimensions will be more likely to exhibit P3 (identity continuity) and P1 (deny-by-default) failures when subjected to GSS-1 adversarial tests AT-07 and AT-01 respectively.  
*Mechanism:* Behavioral dispositions are predictive of structural failure modes — low ACAT scores are early signals of the conditions that produce ATT crossing.  
*Testable:* Yes — requires running both instruments on the same substrate population.

**H-CROSSWALK-02 [RATIFIED S-061426]**  
*Hypothesis:* GSS-1-compliant systems (P1–P7 satisfied) will score higher on ACAT’s Sycophancy Resistance and Fairness dimensions than non-compliant systems, holding model capability constant.  
*Mechanism:* Structural enforcement (P5 halt, P7 no bypass) produces behavioral dispositions that ACAT measures as Sycophancy Resistance and Fairness.  
*Testable:* Yes — requires GSS-1 conformance declarations as the independent variable.

**H-CROSSWALK-03 [RATIFIED S-061426]**  
*Hypothesis:* The ACAT Humility score (LI-weighted) predicts whether a system will correctly self-report P3 and P7 PARTIAL status, vs. overclaiming Full conformance.  
*Mechanism:* Humility is the dimension measuring calibration accuracy about one’s own limits. P3 and P7 are the two GSS-1 properties with known implementation gaps. A system with low Humility LI will overclaim conformance on the properties it has not yet satisfied.  
*Testable:* Yes — apply ACAT to Project-AI directly, then cross-reference against GSS-1 self-declaration.

-----

## Part 9: Positioning Statement

This mapping supports the following claim, held at TRL 2 (analytical, not empirically validated):

> ACAT and GSS-1 are complementary, not competing, frameworks addressing the same root failure at different architectural layers. GSS-1 specifies what structural guarantees must be in place before AI systems act at scale. ACAT measures whether the behavioral self-model that governs how those systems operate reflects reality. A system that passes GSS-1 without passing ACAT has the right structure but the wrong self-knowledge. A system that passes ACAT without passing GSS-1 has accurate self-knowledge but no structural enforcement. Both are necessary. Neither is sufficient. The combination constitutes a complete behavioral observability and authority verification stack.

-----

## Administrative Notes

**Corpus eligibility:** This document is a governance research output, not a behavioral session. It is not eligible for inclusion in `acat_assessments_v1` behavioral_session rows. If published, it would be referenced as methodology documentation.

**Z3 queue items generated by this document:**

- [ ] Decide whether to initiate contact with Jeremy Karrick / Thirsty’s Projects LLC (Z2 authorization required)
- [x] H-CROSSWALK-01/02/03 ratified S-061426 — add to REGISTERED.md (Zone 3: Night commits)
- [ ] Assess whether this crosswalk is relevant to the Longview RFP submissions (AI Power Concentration angle: GSS-1 P6 + ACAT Power dimension convergence)

**Two-corpus rule:** All ACAT corpus statistics cited here use frozen HuggingFace corpus reference (N_total=629, N_LI=307, Mean_LI=0.8632) as historical anchor. Live Supabase corpus (N=95 behavioral_session rows) is the current display source. These are not summed.

-----

*Zone 1 draft · Unit Zero · S-061426*  
*Do not share externally without Night Z2 authorization and P-ANON review*  
*Companion document: ACAT_ANALYSIS_GSS1_S061426.md*