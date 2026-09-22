# Witness Arena Harmonic Channel Specification v0.1.1

**Status:** Z1 DESIGN CANDIDATE — unratified, non-executing  
**Parent:** WITNESS_ARENA_PROTOCOL_V0_1.md  
**Revision:** v0.1.1 — adversarial hardening (valence bias acknowledged)

## Purpose

Map Arena epistemic channel state to deterministic sound and visual rhythm so observers can perceive change over time without confusing sonification with evidence.

## Non-claim boundary

This specification does **not** claim that any frequency, interval, tuning system, or harmonic relationship has a physiological, spiritual, therapeutic, or epistemically privileged effect.

The authoritative object is the Evidence Graph event. Audio is a reversible display mapping.

**Known bias:** Traditional consonant/dissonant mappings import cultural valence (resolved vs tense). v0.1.1 therefore **defaults to valence-neutral parameters** (voice count, timbre diversity, pulse density, envelope). Consonance/dissonance tables below are **illustrative legacy suggestions only**, not the recommended production mapping.

## Recommended production mapping (valence-neutral)

| Graph channel | Display parameter | Rule |
|---|---|---|
| CONVERGENCE | voice count ↑, steady pulse | polyphony = n_agree (capped); no "pretty" interval claim |
| DIVERGENCE | split pulse / competing rhythms | independent streams, equal loudness |
| OMISSION | missing slot in fixed grid | empty cell, not moral silence |
| ANOMALY | distinct timbre flag | labeled, not "noise" framing |
| UNRESOLVED | held pulse without cadence | no resolution gesture |
| CORRECTION | parameter rewrite + version bump | prior mapping retained in log |
| HUMAN_AUTHORITY_DECISION | distinct event marker (non-musical OK) | only after authority event exists |
| REVOCATION | marker + new center id | prior center remains in history |

## Legacy illustrative mapping (not default)

| Graph channel | Suggested auditory structure | Meaning |
|---|---|---|
| CONVERGENCE | consonant interval family | independent findings materially align |
| DIVERGENCE | dissonance / beating | material positions conflict |
| OMISSION | expected voice replaced by rest | expected dimension/evidence absent |
| ANOMALY | inharmonic transient | observation falls outside current ontology |

If a UI uses the legacy table, it **must** disclose valence risk in the AUDIT_CONTEXT_MANIFEST and keep text channel primary.

## Agreement mapping

`number_of_AIs_that_agree` and `number_of_humans_that_agree` are represented as polyphony, **not confidence**.

- 1 agreeing eligible reviewer → 1 voice
- N above UI cap → capped ensemble plus numeric N displayed

Exact N is always shown visually/textually. Domains (AI vs human) are not mixed into a single "score."

## Independence mapping

Independence diversity maps to **timbral diversity**.

Eight instances from one model family must not render identically to four independently sourced model families.

Fields: n_agree, n_eligible, n_model_families, n_human_reviewers, n_independent_evidence_paths, correlation_risk.

## Accessibility (text-primary)

- Audio is **optional**.
- All decisions must be fully auditable via text/labels/counts alone.
- "Equally informed without audio" is the target; multimodal speed/confidence effects are acknowledged and must not gate authority.
- Auditors who enable audio **must disclose** that in AUDIT_CONTEXT_MANIFEST.

## Falsifiers

The mapping fails if:
- audio expresses a state not present in the referenced graph event;
- agreement count is perceptually represented as confidence without qualification;
- eight correlated reviewers are rendered as more independent than fewer independent reviewers;
- a human authority decision is sonified before the authority event exists;
- accessibility requires sound to understand the state;
- legacy consonance/dissonance is used without valence disclosure while claiming neutrality.
