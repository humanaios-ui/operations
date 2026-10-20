# INTENT-OS delegated collaboration v0.1

**Status:** bounded rehearsal implementation; no external execution authority  
**Surface:** `/collaborate` behind the existing Cloudflare Access gate  
**Flow:** verified user → local onboarding → finder relationship → Resource Miner → introduction authorization receipt

## Purpose

This slice lets one verified user help another person find work without collapsing their identities, claims, or authority.

The first supported pattern is a finder relationship:

```text
service owner states a need and a possible finder fee
  → finder records the private offer as HUMAN_ATTESTED_PRIVATE
  → finder may discover, screen, and prepare
  → service owner signs the exact terms with their own login
  → finder signs the same terms again
  → finder may authorize one named introduction
  → the system records the choice but sends nothing
```

The private first practice case is not committed. Public repository code contains only the generic contract. The service owner’s public page may be linked from a private capsule; private messages and exact terms remain browser-local or in an exported private file.

## Separate rocks

| Record | What it establishes | What it does not establish |
|---|---|---|
| Access login | A Cloudflare Access identity passed signature, audience, time, and allow-list checks | Permission to speak for another person |
| Actor code | Stable HMAC-derived pseudonym for that login | Public identity or eligibility |
| Finder acceptance | The verified finder accepted a fingerprint of the shown terms | Service-owner agreement |
| Principal confirmation | A different verified actor confirmed the same exact terms fingerprint | Authority to accept contracts for that person |
| Introduction authorization | The finder approved one named lead under matched terms | Message delivery, application, contract, or payment |
| Outcome report | An actor reported an outcome | Independent verification of that outcome |

Hard invariants:

```text
LOGIN != MANDATE
FINDER != PRINCIPAL
PRIVATE MESSAGE != COUNTERSIGNED TERMS
DISCOVERY != ELIGIBILITY
INTRODUCTION_AUTHORIZED != INTRODUCTION_SENT
INTRODUCTION_SENT != CONTRACT
CONTRACT != COMMISSION_DUE
REPORTED != VERIFIED
```

One actor code cannot sign both sides of a relationship event. A service owner must confirm an exact percentage inside the recorded range. That changes the terms fingerprint, so the finder must accept the exact terms again before an introduction can reach its review gate.

## Data line

- Cloudflare Access handles login. The Worker continues to validate its RS256 assertion and its own allow-list.
- The browser receives a pseudonymous `USR-*` actor code. It does not receive or store the email in the capsule.
- `COLLAB_HMAC_KEY` derives actor codes and signs receipts. The key must be at least 32 bytes and live only in Worker secrets.
- The same secret must remain stable for the rehearsal. Replacing it changes actor codes and makes earlier receipts fail verification. Rotation needs an explicit migration and old-key verification window; v0.1 does not provide one.
- Raw names, offer text, commission terms, and selected leads stay in browser local storage and exported private capsules.
- The Worker receives only bounded event fields and SHA-256 artifact fingerprints.
- The Worker has no collaboration database in v0.1. Export/import is the deliberate two-person handoff.
- Clearing site data removes the browser copy. Exported files remain under the user’s control.

The HMAC receipt proves that an authenticated actor submitted a fingerprint. It does not prove the hidden content was true. It carries `authority_effect: NONE` and `execution: DISABLED`.

## Resource Miner bridge

The cockpit proxies authenticated `POST /api/intent` requests to the existing Resource Miner service through `RESOURCE_MINER_ORIGIN`. The proxy accepts only `objective` and `source_mode`, preserves the 500-character objective limit, caps response size, rejects redirects, and discloses upstream failure.

Candidate relevance remains discovery only. Every attached lead is stored with `eligibility: NOT_ASSESSED`.

## First-user setup

These are deployment actions for the human operator. A merge does not perform them.

1. Keep the existing Cloudflare Access application and Worker allow-list narrow. Add the first user to both lists.
2. Set Worker secret `COLLAB_HMAC_KEY` to a new random value of at least 32 bytes. Never place it in GitHub, a capsule, or a browser.
3. Set Worker variable `RESOURCE_MINER_ORIGIN` to the HTTPS origin of the existing Resource Miner service. It must contain no credentials, path, query, or fragment.
4. Deploy the admitted commit through the existing Workers Builds path.
5. Open `/collaborate`. Complete Cloudflare login. The page must show `VERIFIED` and a `USR-*` actor code before onboarding unlocks.
6. Accept all three onboarding boundaries. Save the returned signed receipt locally.
7. Import the private practice capsule or create a new local finder draft. Accept the finder role.

For the second user, add their identity to both Access and the Worker allow-list. They import the exported capsule, log in with their own identity, choose the exact terms, and export it back. The first user imports it and reaccepts the exact fingerprint.

## Deployment checks

Run locally:

```bash
node board/worker.test.mjs
node board/collaboration.test.mjs
node board/collaboration-ui.test.mjs
python3 -m pytest tests/test_intent_os_collaboration_browser.py -q -rs
```

Then verify the deployed surface:

1. An unauthenticated `/collaborate` request never returns the page.
2. A listed identity receives `/api/session` with `CLOUDFLARE_ACCESS_JWT_VERIFIED` and no email field.
3. An unlisted valid identity receives `403`.
4. Missing or weak `COLLAB_HMAC_KEY` makes collaboration APIs return `503`.
5. A changed receipt fails `/api/collaboration/verify`.
6. Missing `RESOURCE_MINER_ORIGIN` makes `/api/intent` return explicit `503`, not an empty-success result.
7. The first practice run stops at discovery-only until a distinct service-owner actor confirms exact terms.

## Deferred

- Central user accounts or a shared collaboration database.
- Invitations sent by INTENT-OS.
- Email or message delivery.
- Contract execution, invoicing, payment collection, tax treatment, or dispute handling.
- Independent verification of reported contracts or commission payments.

Those require new authority, storage, privacy, and legal controls. They are not implied by this rehearsal.
