# OSA v0.1 — Opportunity Surface Area (Z1 candidate)

**Status:** draft / unadmitted; planning anchor issue #795, parent Resource System #588.
**Implementation:** services/opportunity_surface.py (pure read-only projection).
**Boundary:** authority_effect=NONE; no execution, credentials, network calls, persistent store, eligibility warrant, admission, or human authorization.

## Purpose

Observe whether bounded activities correlate with surfaced, screened, pursued, and reportedly successful opportunities **without estimating a probability of luck**. The nine dimensions and 33 rules are a *descriptive self-assessment taxonomy*, not a validated predictive scale.

This instrument is a projection over existing interfaces, not a new Oracle, database, source of truth or evaluator.

## Exact supplied interfaces

| Upstream | Read-only input | What is preserved |
|---|---|---|
| Resource Miner / URA | ResourceCandidate.to_dict() or AdapterRegistry.normalize() dictionary in resource_candidates[] | resource_id, discovered_at, source URL and time-stamped evidence references; eligibility remains unassessed or as originally stated |
| Guiding Light | evaluate_snapshot(...) output in guiding_light, including results[].target_id/classification/assessment_state/mandatory_unknowns/mandatory_blockers | Original pathway states; no invented matching, scores, eligibility, or authority |
| Explicit translation | bindings[] with exact resource_id, target_id, nonempty source_refs | No title/semantic guessed joins; only a source-bound resource may be linked to an existing evaluated target |
| Observation / Session Graph | activity_events[], behavior_observations[] with stable IDs, offset-aware timestamps and source references | Caller-supplied **claims**, not automatically authenticated graph records; no graph mutation or private source retrieval |
| HLKS / SCVC | Existing VLR/source/correction references may be carried as opaque source_refs | No reconstruction/verification claim; SCVC must verify any continuity request independently under its own contract |

All inputs are supplied by a caller. A hash, claimed source reference, label, or Guiding Light result is not independent proof. The output deliberately does not echo free-form source content, URLs or private payloads.

## Input contract

~~~python
from services.opportunity_surface import SCHEMA, project

projection = project({
    "schema_version": SCHEMA,
    "as_of": "2030-01-01T00:00:00Z",
    "resource_candidates": [ura_normalized_dictionary],
    "guiding_light": guiding_light_evaluate_snapshot_output,
    "bindings": [{
        "resource_id": ura_normalized_dictionary["resource_id"],
        "target_id": "exact-guiding-light-result-id",
        "source_refs": ["opaque-evidence-id"],
    }],
    "activity_events": [],
    "behavior_observations": [],
})
~~~

No action takes place in this example. Real resource and target data must be supplied from their existing approved sources. No automatic discovery, scraping or private-data hydration is permitted here.

## Activity state progression

For each bound resource, activity claims must proceed:

**EXPOSED → QUALIFIED → PURSUED → SUCCEEDED**

- Every activity claim has a unique event_id, existing resource_id, stage, offset-aware observed_at, source_refs[], and evidence_state (SELF_ATTESTED, SOURCE_LOCATED, or SOURCE_OBSERVED).
- A qualification claim additionally requires an explicit Guiding Light binding whose target is REACHABLE or BRIDGE, MAPPED, and free of mandatory unknowns/blockers. This is **mapped opportunity screening**, never applicant eligibility.
- A success claim must be SOURCE_OBSERVED, but **the claimed source is still not authenticated**. All reported counts retain this caveat.
- RETRACTED records a negative correction; an opportunity is removed from the active numerator/denominator and may not advance further in v0.1. The caller retains original append-only evidence upstream.
- Missing stages, duplicate IDs, future or naive times, unbound resources, forged authority and missing source refs fail closed.
- The core deliberately abstains on source freshness and issuer identity: freshness_assessment=NOT_ESTABLISHED, authenticated=false.

Reported ratios are qualified_claims/exposed_claims and succeeded_claims/pursued_claims. Zero denominators return JSON null, never 0% or 100%.

## Behavioral observations

Nine dimensions preserve exactly 33 rule IDs. Source-referenced claims are PLANNED, SELF_ATTESTED, SOURCE_OBSERVED, or RETRACTED. Missing rules are UNKNOWN. Newer observations may supersede earlier claims without overwriting the upstream append-only history. A behavior claim can optionally reference a source-bound resource_id. Reports show state counts per dimension, **not** a luck score or permission to act.

## Security and governance

1. No file/network/database/credential operations in this module.
2. No inferred eligibility or resource acquisition, no automated outreach, no recommendations disguised as authorizations.
3. The repository Coordinator remains the only repository routing authority; **OSA neither requests nor grants admission**. Admission never implies merge authority.
4. Public metadata only. Raw emails, private recovery content, names, credentials and source bodies must not be supplied or published as observations.
5. The translation has *no independent verification of issuer/run provenance*. Treat a projected successful event as a reported claim until separate host-protected evidence authenticates it.
6. Do not use OSA metrics to make unconsented consequential decisions about individuals or communities.
7. No new UI or persistence is included in v0.1. The supplied HTML self-assessment can remain a separate untrusted input instrument until persistence, consent and accessibility are reviewed.

## Acceptance and validation

Tests import **real** resource_miner.universal_adapter normalization and **real** services.guiding_light.evaluate_snapshot to create synthetic cross-contract inputs. They cover all 9/33 taxonomy identifiers, no automatic opportunity promotion, explicit joins, progression, retractions, zero denominators, chronology, conflicts and attempted authority elevation.

~~~bash
python3 -m pytest tests/test_opportunity_surface.py -q
~~~

Registered in .tool-control/baseline_tests.yaml for the existing PR quality-baseline job. Local/synthetic pass is not protected CI attestation; exact-head checks and independent admission/review remain separate.

**Follow-on (not implemented):** independently verify source/run custody; separately authorize consent-scoped longitudinal persistence; compare longitudinal exposures against outcomes with denominators and falsifiers. Do not widen v0.1 automatically.
