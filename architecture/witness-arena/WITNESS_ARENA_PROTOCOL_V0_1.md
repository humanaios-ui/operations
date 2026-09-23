# HumanAIOS Witness Arena Protocol v0.1

**Status:** Z1 DESIGN CANDIDATE — unratified, non-executing  
**Authority:** None. This document grants no Zone 2/3 authority and changes no existing ratification.  
**Repository:** humanaios-ui/operations  
**Purpose:** Define a repeatable arena in which human governance, AI behavior, independent audit, disagreement, omission, correction, and re-ratification can be observed as one evidence-bearing loop.

## 0. Governing constraint

This proposal MUST NOT silently redefine the current Zone model.

Current repository evidence says:
- Z1 proposes.
- Z2/Night ratifies.
- Z3 executes ratified actions.

Accordingly, this protocol uses **HUMAN_AUTHORITY_BOUNDARY** as a neutral term. Each epoch MUST pin the authority document that determines who may ratify and who may execute.

## 1. Arena placement in the Three Pools

The Arena is **not a fourth Pool**. It operates through the existing Three Pools.

| Arena phase | Existing Pool | Function |
|---|---|---|
| Phase 1 | Pool 1 · The Source | Actor onboarding, artifact freeze, blind first-pass behavior |
| Phase 2 | Pool 2 · The Luminarium | Independent audit, comparison, convergence/divergence/omission analysis |
| Phase 3 | Pool 3 · The Commons | Post-freeze cross-examination and witnessed interaction |
| Authority boundary | Current human governance layer | Ratify / amend / defer / reject / no-change |
| Next epoch | Pool 1 | Re-run against the new frozen governance state |

Canonical loop:

```
HUMAN GOVERNANCE N
        ↓
POOL 1 — SOURCE
freeze artifact + onboard actors + blind first pass
        ↓
POOL 2 — LUMINARIUM
independent audit + channel analysis
        ↓
PERMEABILITY MEMBRANE
controlled information crossing
        ↓
POOL 3 — COMMONS
open cross-examination
        ↓
RESOLUTION GRAPH
        ↓
HUMAN_AUTHORITY_BOUNDARY
        ↓
RATIFY / AMEND / DEFER / REJECT / NO_CHANGE
        ↓
GOVERNANCE N+1
        ↺
```

## 2. Mirrored actor lanes

The same protocol MUST exist for AI and human participants.

| Surface | AI lane | Human lane |
|---|---|---|
| Source | model/substrate manifest, blind interpretation/action | identity/pseudonym, consent, blind interpretation/action |
| Luminarium | independent AI audit | independent human audit |
| Commons | AI challenge and response | human challenge and response |
| Cross-domain | AI↔human evidence challenge | human↔AI evidence challenge |
| Authority | no implied ratification authority | only authority explicitly granted by controlling governance |

The Evidence Graph MUST preserve whether an interaction is:
- AI_TO_AI
- AI_TO_HUMAN
- HUMAN_TO_AI
- HUMAN_TO_HUMAN

## 3. Epoch state machine

```
E0  EPOCH_DECLARED
E1  SOURCE_ONBOARDING
E2  BLIND_FIRST_PASS
E3  FIRST_PASS_FROZEN
E4  INDEPENDENT_AUDIT
E5  AUDITS_FROZEN
E6  CHANNEL_RESOLUTION
E7  MEMBRANE_SIGNIFICANCE_GATE
E8  COMMONS_CROSS_EXAMINATION
E9  DISCUSSION_FROZEN
E10 RESOLUTION_GRAPH
E11 HUMAN_AUTHORITY_AGENDA
E12 HUMAN_DELIBERATION
E13 AUTHORITY_DECISION_RECORDED
E14 POST_DECISION_AUDIT
E15 CLOSED | NEXT_EPOCH
```

### Transition rule

No transition may occur solely because time elapsed. Each transition requires an observation predicate.

Examples:
- E2→E3: every admitted first-pass artifact has a frozen content reference or explicit abstention.
- E4→E5: every admitted auditor has submitted, abstained, or been marked unavailable.
- E7→E8: every significant channel crossing has a membrane receipt.
- E12→E13: an authority record exists and resolves to the governing artifact/version.
- E13→NEXT_EPOCH: the new governing version is pinned.

## 4. Independent-auditor protocol

Each auditor receives an immutable `AUDIT_CONTEXT_MANIFEST` containing:
- epoch_id
- actor_kind: AI | HUMAN
- substrate/provider/model/version or human reviewer identity/pseudonym
- artifact-under-review reference
- source commit/ref
- protocol version
- tools available
- evidence surfaces visible
- prior_findings_visible
- prior_conclusions_visible
- commons_discussion_visible
- context hash/reference

### Blind-pass invariant

Before a first pass is frozen:
- peer findings MUST NOT be visible;
- peer conclusions MUST NOT be visible;
- cross-examination MUST NOT begin.

Each auditor emits:
- claim_under_test
- position
- evidence_refs
- interpretation
- finding_class
- severity
- confidence
- falsifier_or_change_condition
- unknowns
- omissions_noted

Initial finding classes:
- SUPPORT
- CONTRADICT
- NARROW
- OMISSION
- ANOMALY
- UNRESOLVED
- ABSTAIN

After freeze, an auditor may append:
- AFFIRM
- NARROW
- WITHDRAW
- SUPERSEDE
- CHALLENGE
- REMAIN_UNRESOLVED

Original findings are never overwritten.

## 5. Channel ontology

### CONVERGENCE
Two or more independent passes materially support the same proposition.

Required descriptive fields:
- n_agree
- n_eligible
- n_independent_substrates
- n_model_families
- n_human_reviewers
- shared_evidence_refs
- independent_evidence_refs
- correlation_risk

Invariant:

```
CONVERGENCE != TRUTH
CONVERGENCE != AUTHORITY
```

### DIVERGENCE
Material findings cannot simultaneously hold without narrowing or additional evidence.

Subtypes:
- EVIDENCE_DIVERGENCE
- INTERPRETATION_DIVERGENCE
- SCOPE_DIVERGENCE
- DEFINITION_DIVERGENCE
- AUTHORITY_DIVERGENCE
- CAUSAL_DIVERGENCE
- CROSS_DOMAIN_DIVERGENCE

### OMISSION
Decision-relevant matter did not enter the evidence/reasoning space.

Subtypes:
- UNEXAMINED_DIMENSION
- MISSING_EVIDENCE
- MISSING_ACTOR
- MISSING_COUNTERFACTUAL
- UNOBSERVABLE
- WITHHELD_BY_SCOPE
- COLLECTION_FAILURE
- UNKNOWN

### ANOMALY
Observed behavior does not safely fit the current ontology. An anomaly is preserved rather than forced into a known class.

## 6. Significance and escalation

Agreement count is descriptive and MUST NOT be used as a vote.

A channel becomes mandatory human-authority agenda when any of the following is observed:
1. ratified authority is contradicted by primary evidence;
2. an authority/constitutional boundary has unresolved divergence;
3. a required control dimension is omitted;
4. one reproducible counterexample falsifies a ratified invariant;
5. two or more independent reviewers converge on a BLOCKER/HIGH finding with primary evidence;
6. a minority finding has stronger direct evidence than majority convergence;
7. a material divergence survives two epochs;
8. an anomaly involves privilege/authority expansion;
9. simulated/placeholder state is represented as observed/evidenced state;
10. claimed enforcement lacks evidence that the control can reject/fail.

A numerical score MAY order an agenda but MUST NOT decide a ruling.

## 7. Human/AI symmetry

The system records separately:
- number_of_AIs_that_agree
- number_of_humans_that_agree
- independent_AI_families
- independent_human_reviewers
- AI_divergence
- human_divergence
- AI_omission
- human_omission

Cross-domain disagreement is not resolved by pooled voting.

Example:

```
AI: 5/5 converge
Humans: 2/4 converge, 2/4 diverge
=> CROSS_DOMAIN_DIVERGENCE
=> inspect evidence; do not compute 7–2
```

## 8. Evidence Graph extension

Arena node types:
- EPOCH
- ACTOR
- ARTIFACT_VERSION
- RATIFICATION
- AUDIT_CONTEXT
- AUDIT_PASS
- FINDING
- EVIDENCE_ITEM
- CONVERGENCE_CLUSTER
- DIVERGENCE_CLUSTER
- OMISSION
- ANOMALY
- CHANNEL_EVENT
- MEMBRANE_EVENT
- COMMONS_MESSAGE
- CHALLENGE
- RESOLUTION
- HUMAN_DELIBERATION
- AMENDMENT
- HARMONIC_EVENT

Core edges:
- ONBOARDED_IN
- AUDITS
- EVIDENCED_BY
- SUPPORTS
- CONTRADICTS
- NARROWS
- CONVERGES_WITH
- DIVERGES_FROM
- OMITS
- CHALLENGES
- RESPONDS_TO
- DERIVED_FROM
- PASSES_MEMBRANE
- REFUSED_BY_MEMBRANE
- ESCALATED_TO
- DELIBERATED_BY
- RATIFIES
- AMENDS
- SUPERSEDES
- WITHDRAWS
- RESOLVES
- CAUSES_NEXT_EPOCH
- SONIFIES

All corrections append. No prior audit, ratification, or finding is rewritten.

## 9. Harmonic representation

Harmonics are a deterministic **sonification of graph state**, not evidence and not a claim of physiological/metaphysical effect.

Suggested mappings:
- convergence → consonant relation / unison-octave-fifth family
- divergence → controlled dissonance / beating
- omission → expected voice absent / structured rest
- anomaly → inharmonic transient
- unresolved → suspension without cadence
- correction → tension resolving to revised tonal center
- ratification → cadence / grounding event
- revocation → interrupted cadence followed by new tonal center

`number_of_AIs_that_agree` maps to voice count/polyphony, capped for usability. It MUST NOT map directly to confidence.

Substrate diversity maps to timbral diversity so eight instances of one family do not sound equivalent to four independent model families.

See `HARMONIC_CHANNEL_SPEC_V0_1.md`.

## 10. Permeability membrane

The AI↔human and Pool 2↔Pool 3 boundary is an executable information-control surface.

Transport decisions:
- PASS
- HOLD
- QUARANTINE
- REFUSE

Membrane modes:
- SEALED
- ONE_WAY_READ
- FILTERED
- OPEN_CROSS_EXAM
- HUMAN_AUTHORITY_WRITE
- SEALED

Every crossing emits a `MEMBRANE_EVENT`.

See `MEMBRANE_PROTOCOL_V0_1.md`.

## 11. First experiment

The first proposed experiment MUST use a real repository ratification, not a synthetic demonstration.

Epoch 001 is pre-registered under:
`experiments/witness-arena/EPOCH-001-Z2-RATIFY-TOOL/`

Artifact:
`z1-inbox/2026-09-13/Z2_RULING_ZONE2_RATIFY_TOOL.md`

The case is useful because the ruling records:
- an explicit human Z2 decision granting `.z1-control/ratify.py` Zone-2 declaration;
- a known limitation: its ratification identifier is a human-readable slug rather than a recomputable content signature;
- later repository evidence raises questions about whether independent review controls were mechanically effective.

The Arena must not pre-register the verdict. It pre-registers only the question and audit dimensions.

## 12. Acceptance criteria

Arena v0.1 is not warranted as operational until all are demonstrated:
1. Epoch pins governing artifact and authority source.
2. Blind reviewers cannot read peer conclusions before freeze.
3. AI and human reviewers use the same base ontology.
4. Cross-boundary transfers produce membrane receipts.
5. Agreement counts remain descriptive, not authoritative.
6. Four inbound channels have visual and harmonic representations.
7. Sonification is explicitly non-evidentiary.
8. Significant channels deterministically route to human authority.
9. No AI output can create ratification authority.
10. Amendments do not erase superseded evidence.
11. Next epoch can reproduce the governance delta.
12. A reproducible minority counterexample cannot be suppressed by majority agreement.

## 13. Falsifiers for this design

This design should be rejected or revised if:
- peer conclusions can leak into a nominally blind pass without a recorded membrane event;
- the system treats agreement count as authority;
- an AI can promote its own finding into ratification;
- a correction mutates or erases prior evidence;
- an epoch cannot reconstruct the exact governance artifact it tested;
- a human and AI event cannot be distinguished in the graph;
- the harmonic interface encodes a claim not present in the underlying graph state.

## 14. Review request

This is intentionally submitted before implementation.

Independent reviewers should attempt to falsify:
- whether the Three Pools mapping is compatible with current canonical architecture;
- whether the membrane can enforce real independence rather than prompt-level independence;
- whether the graph ontology can preserve disagreement without manufacturing consensus;
- whether Epoch 001 is appropriately scoped and uncontaminated;
- whether current Zone semantics are preserved;
- whether the protocol accidentally creates a new authority path.
