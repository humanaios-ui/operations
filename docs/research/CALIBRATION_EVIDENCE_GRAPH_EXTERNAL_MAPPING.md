# Calibration Evidence Graph — External Evidence Mapping

Status: PROVISIONAL RESEARCH MAP  
Date: 2026-09-30  
Scope: map HumanAIOS bidirectional calibration graph nodes and edges to external standards and research without treating analogy as validation.

## Research question

Can the calibration/onboarding method be represented as an evidence-bearing knowledge graph whose detailed nodes have explicit external referents, while preserving the distinction between:
1. direct standards support,
2. methodological analogue,
3. cognitive analogue,
4. HumanAIOS-local hypothesis?

## Evidence relation vocabulary

Use precise relation types rather than a generic `SUPPORTED_BY` edge:

- `IMPLEMENTS_STANDARD`: the HumanAIOS node directly instantiates a published standard construct.
- `CONSTRAINED_BY_STANDARD`: an external standard supplies a validation or structural rule.
- `METHOD_ANALOGUE`: external method has a structurally similar role but does not validate the HumanAIOS construct.
- `COGNITIVE_ANALOGUE`: published cognitive research provides a plausible analogue; no identity claim is made.
- `EMPIRICALLY_MOTIVATED_BY`: external empirical work motivates a testable design choice.
- `CHALLENGED_BY`: source identifies a limitation, competing interpretation, or failure mode.
- `LOCAL_HYPOTHESIS`: no external source is treated as establishing the claim.
- `VERSION_WATCH`: relevant external specification is in active draft/revision and should be monitored.

## Node-to-source map

| HumanAIOS node / edge | Graph role | External referent | Relation | Standing / implication |
|---|---|---|---|---|
| `Provenance`, `wasDerivedFrom`, `wasGeneratedBy`, attribution | Preserve how evidence/claims came to be | W3C PROV-O | IMPLEMENTS_STANDARD | Strong structural fit. Use PROV-O classes/properties rather than inventing a parallel provenance vocabulary where possible. |
| `GraphConstraint` / schema validation | Validate RDF graph structure and required fields | W3C SHACL 1.0 Recommendation | CONSTRAINED_BY_STANDARD | SHACL is appropriate for persisted graph validation. It is not itself a runtime authorization mechanism. |
| `GraphConstraint` future compatibility | Track changes to SHACL language | W3C SHACL 1.2 Core Working Draft, 2026-09-18 | VERSION_WATCH | Keep 1.0 as normative baseline until 1.2 reaches stronger standing; track 1.2 for migration opportunities. |
| `ClaimPackage` = assertion + provenance + publication metadata | Package small, independently attributable graph claims | Nanopublication pattern | METHOD_ANALOGUE | Useful publication pattern, but not a standards-body requirement. Treat as optional serialization/publication profile. |
| `ExternalizedState` | Keep state visible rather than requiring internal retention | Cognitive/intention offloading literature | EMPIRICALLY_MOTIVATED_BY | External aids can reduce internal memory demands and alter task strategy. Supports testing externalized state as a controlled presentation condition, not assuming it is always beneficial. |
| `ActiveFocus` / participant “hero” | Currently salient item distinguished from other retained items | Working-memory focus-of-attention literature | COGNITIVE_ANALOGUE | Literature supports a privileged/focused representation among multiple retained items. HumanAIOS “hero” remains participant-language and must not be equated with a specific neural mechanism. |
| `ParticipantConfidence` | Subjective confidence attached to a trace/resolution | Metacognition measurement literature | METHOD_ANALOGUE | Confidence can be measured separately from first-order accuracy; preserve both rather than collapsing confidence into correctness. |
| `UNRESOLVED` / `DELAYED` | Permit abstention/no-answer and later resolution | Reject-option / abstention literature; metacognitive “feeling of knowing” literature | METHOD_ANALOGUE | Supports treating non-response/abstention as valid information. Human delayed-resolution timing still requires its own empirical validation. |
| `ContextObservation` | Record environmental/background context | Experimental control / provenance role | METHOD_ANALOGUE | Context can be preserved as evidence without converting temporal co-occurrence into causality. |
| `LandingCheck` | Verify that critical meaning landed as intended before consequential continuation | AHRQ TeamSTEPPS check-back / teach-back | METHOD_ANALOGUE | Strong control-pattern analogue for closed-loop confirmation and understanding checks. Does not establish that HumanAIOS should check every message; trigger policy remains local and testable. |
| `DependencyFlag` | Make execution prerequisites, blocked scope, and resolution path explicit | NIST SBOM / DevSecOps dependency and provenance practices | METHOD_ANALOGUE | External engineering practice supports explicit dependency relationships and provenance. HumanAIOS extends the idea beyond software packages to tools, permissions, networks, human inputs, and stage requirements. |
| `TraceFreeze` | Freeze human report before revealing machine-side answer | HumanAIOS anti-contamination control | LOCAL_HYPOTHESIS | No external source located here is treated as an exact match. Keep as a local experimental invariant until independently tested. |
| `Discovery != Training` | Separate observation from corrective teaching | Experimental contamination control | LOCAL_HYPOTHESIS / METHOD_ANALOGUE | Methodologically plausible, but exact protocol effectiveness remains to be tested. |
| `DesignDelta` -> `Retest` -> `Warrant` | Convert observations into challengeable design changes | Iterative experimental / adaptive-control logic | METHOD_ANALOGUE | External methods motivate the loop, but HumanAIOS warrant semantics remain local and must be explicitly defined. |
| `SubjectiveObservation` vs `ObjectiveComparator` | Preserve introspection as report, not mechanism proof | Metacognition literature | CONSTRAINED_BY_STANDARD (epistemic policy, local) + METHOD_ANALOGUE | Confidence/introspection are valid report variables but do not independently establish latent cognitive mechanisms. |

## External sources

### W3C PROV-O
https://www.w3.org/TR/prov-o/

PROV-O provides classes and properties for representing and interchanging provenance and is explicitly designed to be specialized for domain applications.

### W3C SHACL 1.0 Recommendation
https://www.w3.org/TR/shacl/

SHACL validates RDF data graphs against shapes graphs. HumanAIOS should use it for structural/data-quality validation, not as a substitute for temporal runtime controls or authorization.

### W3C SHACL 1.2 Core Working Draft
https://www.w3.org/TR/shacl-core/

Current draft dated 2026-09-18. Track as a version watch; do not silently replace the 2017 Recommendation as the normative baseline.

### Nanopublication Guidelines
https://nanopub.net/guidelines/working_draft/

Current working draft dated 2026-09-28. Nanopublications separate assertion, assertion provenance, and publication information. The document explicitly states that it has no official standards-body standing.

### Cognitive / intention offloading
https://pmc.ncbi.nlm.nih.gov/articles/PMC9971128/
https://pmc.ncbi.nlm.nih.gov/articles/PMC8358584/

These reviews describe the strategic use of external reminders/tools and effects of externalizing information-processing demands. They motivate, but do not prove, the HumanAIOS externalized-state hypothesis.

### Working memory and focus of attention
https://pmc.ncbi.nlm.nih.gov/articles/PMC6688548/
https://pmc.ncbi.nlm.nih.gov/articles/PMC3918594/

Working-memory research discusses selecting a focused item among multiple retained items and also documents competing findings about interference. The second source is intentionally retained as challenge evidence against overclaiming a uniquely protected focus state.

### Confidence / metacognition
https://pmc.ncbi.nlm.nih.gov/articles/PMC4097944/
https://pmc.ncbi.nlm.nih.gov/articles/PMC9932734/

These sources distinguish subjective confidence from first-order task accuracy and describe sensitivity/bias constructs. This supports storing confidence as a separate graph property.

### Closed-loop communication / understanding verification
https://www.ahrq.gov/hai/cauti-tools/phys-championsgd/appa.html
https://www.ahrq.gov/teamstepps-program/curriculum/communication/tools/teachback.html

AHRQ describes check-back as closed-loop communication used to verify and validate information exchanged, and teach-back as a way to confirm understanding by having the receiver explain the information in their own words. HumanAIOS uses this as a methodological analogue for a selective landing-verification lane.

### Dependency visibility / software supply chain
https://csrc.nist.gov/glossary/term/software_bill_of_materials
https://pages.nist.gov/nccoe-devsecops/appendix-b.html

NIST materials define SBOMs as formal records of software components and supply-chain relationships and describe tooling that verifies software dependencies and provenance. HumanAIOS generalizes dependency flagging beyond software components, so the external mapping is methodological rather than exact.

### Reject option / abstention
https://arxiv.org/abs/2304.04906

Survey of prediction with reject option / selective classification / abstention. This is a machine-learning analogue only; it does not establish human `UNRESOLVED` semantics.

## Resulting graph policy

Every external-evidence edge MUST state:
- source URI;
- relation type from the vocabulary above;
- source date/version when material;
- scope;
- what the source supports;
- what it does not support;
- confidence/standing;
- falsifier or review trigger where applicable.

No external citation is allowed to upgrade a `LOCAL_HYPOTHESIS` to `WARRANTED` merely because terminology appears similar.

## Improvements produced by this research pass

1. Replace generic `SUPPORTED_BY` with typed evidence relations.
2. Adopt PROV-O for provenance primitives.
3. Adopt SHACL 1.0 for persisted graph constraints.
4. Add a `VERSION_WATCH` edge for SHACL 1.2 rather than prematurely migrating.
5. Treat nanopublication structure as optional packaging, not a mandatory dependency.
6. Split `ActiveFocus` from preserved state and explicitly mark its cognitive mapping as analogue only.
7. Preserve confidence independently from correctness.
8. Make `UNRESOLVED` and `DELAYED` first-class states without interpreting them as success/failure.
9. Record challenge sources alongside supporting analogues.
10. Preserve HumanAIOS-specific controls such as `TraceFreeze` as local hypotheses until directly tested.
11. Add a selective `LandingCheck` lane so critical explanations have an explicit understanding state rather than assumed receipt.
12. Add first-class `DependencyFlag` records with blocked scope, plain-language impact, and resolution path.

## Next validation target

Create reference fixtures containing:
- one convergent trace,
- one divergence,
- one unresolved trace,
- one delayed resolution,
- one environmental-context event,
- one design delta that fails retest,
- one design delta that becomes replicated.

Validate those fixtures against the SHACL shapes and verify that the graph cannot erase the original human trace when later corrections or delayed resolutions are appended.
