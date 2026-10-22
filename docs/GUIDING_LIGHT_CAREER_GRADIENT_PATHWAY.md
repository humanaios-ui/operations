# Guiding Light Career Gradient Pathway Program v0.1

**Status:** pilot implementation  
**Surface:** Intent-OS Cockpit reflex page  
**Authority:** the human user remains the final decision boundary  
**Witness invariant:** `WITNESS_IS_NOT_THE_AUTHORITY`

> **v0.2 architecture note:** Career is now an adapter over the domain-neutral Guiding Light engine in `services/guiding_light.py`. The general contract and cross-domain boundaries are defined in `docs/GUIDING_LIGHT_GENERAL_GRADIENT_ENGINE.md`. This document preserves the career-specific UX and HARVEST vocabulary.

## Purpose

Guiding Light turns career matching into a closed evidence-to-opportunity progression loop.

It answers four questions continuously:

1. What paid work is credibly reachable from the user's current evidence?
2. Which adjacent opportunities create the strongest upward career gradient?
3. What specific capability/evidence delta separates the user from higher-value roles?
4. What is the shortest honest path to close that delta through interrogation, learning, real work, and evidence artifacts?

The program does **not** infer credentials, manufacture experience, or optimize hidden persuasion. It preserves the difference between past evidence, user attestation, transferable capability, planned learning, and unresolved gaps.

## Closed loop

```text
CURRENT EVIDENCE
      ↓
LIVE OPPORTUNITY SET
      ↓
REQUIREMENT MAPPING
      ↓
ACTIONABILITY + CAREER GRADIENT
      ↓
HARVEST / BRIDGE / FRONTIER / HOLD
      ↓
CAPABILITY DELTA
      ↓
INTERROGATE / LEARN / BUILD EVIDENCE / CREDENTIAL DECISION
      ↓
REAL-WORLD DEMONSTRATION
      ↓
NEW EVIDENCE
      ↓
RECOMPUTE FRONTIER
      ↓
APPLICATION + OUTCOME TELEMETRY
      ↺
```

## Opportunity classes

- **HARVEST** — strongly evidenced now; primarily useful for current income/outcome.
- **BRIDGE** — actionable or near-actionable and materially expands future scope, authority, compensation, technical depth, or portability.
- **FRONTIER** — strategically attractive but not yet sufficiently evidenced; retained as a live target specification.
- **HOLD** — blocked, low-value, or materially incompatible with current constraints.

These are pathway states, not claims about a person's worth or an employer's quality.

## Two independent scores

### Current Actionability

Deterministic weighted coverage of the opportunity's mapped requirements. Mandatory hard blockers override the aggregate score.

Mapping states are intentionally distinct:

- DOCUMENTED
- USER_ATTESTED
- TRANSFERABLE
- PARTIAL
- PLANNED
- UNKNOWN
- NOT_HELD
- BLOCKED

### Career Gradient

A separate measure of what the opportunity adds to the user's future option set. The v0.1 axes are:

- compensation trajectory
- scope
- authority
- technical complexity
- strategic exposure
- evidence gain
- portability

Each axis is supplied as an explicit observation/estimate; it is never silently inferred by the deterministic scorer.

## Learn from exactly where you are

The learning engine must not restart the user at fundamentals they already demonstrate.

Every gap is classified before recommending learning:

- **INTERROGATE** — experience may exist but is not yet captured.
- **LEARN** — knowledge gap.
- **BUILD_EVIDENCE** — knowledge may exist, but observable proof is missing.
- **CREDENTIAL_DECISION** — a recurring role requirement is a credential/licensure gate.
- **EXPERIENCE_REQUIRED** — cannot be honestly replaced by coursework.
- **BLOCKER** — current hard eligibility failure.

A learning intervention is complete only when its intended evidence state changes, not merely when content is consumed.

```text
LEARN → DEMONSTRATE → ARTIFACT → EVIDENCE UPDATE
```

## Witness linkage

Guiding Light links to the HumanAIOS Witness as an **observation surface**, never as an authority.

The Witness export records:

- declared goal source,
- opportunity classification inputs,
- requirement/evidence states,
- omissions and unknowns,
- selected target,
- learning/evidence deltas,
- source references,
- canonical snapshot hash,
- `WITNESS_IS_NOT_THE_AUTHORITY`.

The Witness may expose why a pathway was surfaced and what is missing. It may not authorize an application, enrollment, credential purchase, career change, or other consequential action.

This preserves the service contract:
`declaration -> acknowledgement -> consent receipt -> collection event -> derivation -> decision -> policy -> explanation`

For this pilot, the reflex page exports the observation as JSON. Durable Witness-ledger routing is a later integration step.

## PR #472 / Account Hub linkage

PR #472 introduced normalized `Event` infrastructure and a unified activity-feed contract. Guiding Light extends the same event vocabulary with:

- `opportunity_discovered`
- `opportunity_mapped`
- `career_delta`
- `learning_signal`
- `evidence_update`
- `application_outcome`

The career-gradient service can therefore publish pathway changes into the existing Cockpit activity stream rather than creating a parallel telemetry system.

## Reflex-page UX

The Cockpit page is intentionally a reflex, not a full career-management application.

It shows:

- **Position** — current opportunity frontier and counts.
- **Opportunity ladder** — Harvest / Bridge / Frontier / Hold.
- **Target pathway** — one selected target and its unresolved deltas.
- **Learning path** — only the learning/evidence actions required from the current state.
- **Evidence queue** — artifacts that would change the profile if completed.
- **Witness** — provenance, omissions, uncertainty, and exportable observation.

The user can import/export the snapshot locally. No resume text, credentials, or PII are committed to the repository.

## v0.1 falsifiers

The pilot should be considered unsuccessful if any of the following occur:

1. A NOT_HELD or BLOCKED mandatory requirement can still produce an actionable classification.
2. The UI merges past experience with proposed future execution.
3. A learning recommendation is generated without a named capability delta.
4. A credential is treated as equivalent to experience.
5. The Witness export contains an authorization decision not explicitly made by the user.
6. The same snapshot produces non-deterministic scores.
7. Career observations cannot be emitted through the PR #472 normalized event contract.

## Next integration boundary

v0.1 is deliberately source-agnostic. Live job discovery, resume ingestion, learning-provider search, Gmail outcome parsing, and application adapters remain external inputs. They should feed this program only through explicit normalized records with provenance.
