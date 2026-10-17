# Reference verification protocol

This protocol treats a reference as a consent-bearing, currentness-bearing resource rather than as a static contact record.

## State dimensions

- contact currentness: `UNKNOWN | CONFIRMED | STALE`
- relationship currentness: `UNKNOWN | CONFIRMED`
- consent by opportunity: `UNKNOWN | CONSENTED | DECLINED | REVOKED`
- availability: `UNKNOWN | AVAILABLE | CONDITIONAL | UNAVAILABLE`
- engagement: `REFERENCE_ONLY | OCCASIONAL_UPDATES | RESEARCH_OPT_IN`

These fields are independent.

## Verification loop

`REF-* -> private contact binding -> Gmail verification draft -> human reply -> candidate receipt -> validation -> Drive receipt -> sanitized GitHub projection -> application availability recompute`

## Required invariants

- `EMAIL_DELIVERED != CONTACT_VERIFIED`
- `EMAIL_REPLIED != REFERENCE_CONSENTED`
- `CONSENT_FOR_ONE_APPLICATION != GLOBAL_CONSENT`
- `REFERENCE_CONSENT != RESEARCH_PARTICIPATION`
- raw name/email/phone/private reply body remain in private Google surfaces
- GitHub stores only the `REF-*` identifier, evidence domains, currentness/consent/availability state, timestamp, opaque pointer and hashes

## First bounded test

Bind one real reference privately after the principal supplies/approves the contact, create a Gmail draft rather than sending automatically, review the draft, then send only with explicit human approval. The reply must update only the bound `REF-*` state and must be idempotent under replay.
