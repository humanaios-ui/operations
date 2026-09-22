# Witness Arena Harmonic Channel Specification v0.1

**Status:** Z1 DESIGN CANDIDATE — unratified, non-executing  
**Parent:** WITNESS_ARENA_PROTOCOL_V0_1.md

## Purpose

Map Arena epistemic channel state to deterministic sound and visual rhythm so observers can perceive change over time without confusing sonification with evidence.

## Non-claim boundary

This specification does **not** claim that any frequency, interval, tuning system, or harmonic relationship has a physiological, spiritual, therapeutic, or epistemically privileged effect.

The authoritative object is the Evidence Graph event. Audio is a reversible display mapping.

## Channel mapping

| Graph channel | Suggested auditory structure | Meaning |
|---|---|---|
| CONVERGENCE | consonant interval family | independent findings materially align |
| DIVERGENCE | dissonance / beating | material positions conflict |
| OMISSION | expected voice replaced by rest | expected dimension/evidence absent |
| ANOMALY | inharmonic transient | observation falls outside current ontology |
| UNRESOLVED | suspension | discriminating evidence absent |
| CORRECTION | resolution to revised center | prior interpretation narrowed/superseded |
| HUMAN_AUTHORITY_DECISION | cadence/grounding gesture | human decision recorded |
| REVOCATION | interrupted cadence + new center | authority withdrawn/superseded |

## Agreement mapping

`number_of_AIs_that_agree` and `number_of_humans_that_agree` are represented as polyphony, not confidence.

Example:
- 1 agreeing eligible reviewer → 1 voice
- 2 → 2 voices
- 3 → 3 voices
- ...
- N above UI cap → capped ensemble plus numeric N displayed

The exact N is always shown visually/textually.

## Independence mapping

Independence diversity maps to timbral diversity.

Eight instances from one model family must not render identically to four independently sourced model families.

Descriptive fields:
- n_agree
- n_eligible
- n_model_families
- n_human_reviewers
- n_independent_evidence_paths
- correlation_risk

## Deterministic event vector

```yaml
channel:
n_actors:
n_agree:
n_independent_families:
n_humans:
n_AIs:
evidence_strength:
consequence_scope:
persistence_epochs:
unresolved:
graph_event_ref:
mapping_version:
```

Possible display derivation:
- pitch/interval relation ← channel
- voice count ← n_agree
- timbre diversity ← independence diversity
- envelope ← evidence strength
- duration ← persistence
- pulse density ← consequence scope

## Accessibility

The harmonic layer must always have a non-audio equivalent:
- channel label;
- numeric agreement counts;
- independence counts;
- evidence references;
- unresolved status;
- text description.

No decision may depend on a user's ability to hear the audio mapping.

## Falsifiers

The mapping fails if:
- audio expresses a state not present in the referenced graph event;
- agreement count is perceptually represented as confidence without qualification;
- eight correlated reviewers are rendered as more independent than fewer independent reviewers;
- a human authority decision is sonified before the authority event exists;
- accessibility requires sound to understand the state.
