# PER Public Evidence Discovery - E0 read-only contract

## Purpose

Find and link **proposed public sources** to existing Project Evidence Records (PERs) without rewriting a resume or conflating institutional outcomes with a named individual's work. This extends Resource Miner and the existing PER workflow. It is not a second master profile or task tracker.

## Interface

- plan_public_searches(per, aliases=...) builds bounded queries from the canonical PER's organization, scope, and execution fields. No network request is made.
- run_discovery(per, provider, tenure=...) invokes an explicitly injected and separately authorized search-provider callback. No built-in HTTP client, secret access, or background crawling.
- propose_evidence_links(per, search_hits, tenure=..., org_aliases=..., person_aliases=...) deduplicates URLs, classifies institutional/named-person references, and returns source candidates bound to the exact PER ID.

Every return row has status PROPOSED_REVIEW_ONLY, can_append_to_canonical_per false, and can_publish_personal_resume_claim false. Results contain the source URL, title, excerpt, event and publication dates, tenure relationship, evidence tier, and review requirements. A search result is not proof that its content is correct.

## Attribution and safety rules

1. A contemporaneous named-person mention is an evidence candidate, never automatic verification.
2. Hospital-wide quality ratings, program measures, awards and annual reports remain institutional context unless explicit person-level responsibility is independently established.
3. Out-of-tenure events are context-only; an in-tenure event may be described in a later report.
4. Missing exact dates remain review-only and cannot establish work months.
5. Stable (PER ID, canonical public URL) identity avoids duplicate proposals while preserving meaningful query parameters.
6. Colorado Medicaid HTP does not prove Medicare Advantage performance; MA evidence has its own claim source.
7. Identifiable patient information is prohibited. Upstream collection, content checking, and PHI/PII screening need separate gates.

## Test

From the resource-miner root:

    python -m unittest discover -s tests -p 'test_public_evidence_discovery.py' -v

13 synthetic E0 tests cover PER identity, public URL safety, replay deduplication, attribution boundaries, dates and no autonomous evidence promotion.

## Not yet delivered

No live search provider, authenticated crawler, deployed INTENT-OS integration, persistent private review queue, approval UI, external profile update, or job application submission. Independent review and human Z2 ratification are required before operational admission. Real private career evidence and names are not included in this code change.

Source tracking: operations issue #1131.
