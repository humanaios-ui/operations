# OSF OAuth Bridge — Independent Adversarial Audit Preregistration

**Status:** FROZEN BEFORE REVIEW OF CLAUDE IMPLEMENTATION  
**Date:** 2026-09-22  
**Repository base:** `a6d78fb7e62457ab86059ecaa1017f786cfc2da1`  
**Target system:** HumanAIOS Supabase project `ksinisdzgtnqzsymhfya`  
**Expected functions:** `osf-oauth-start`, `osf-oauth-callback`  
**Reviewer substrate:** ChatGPT / GPT-5.6 Sol  
**Purpose:** Independent falsification of the OSF OAuth bridge before any merge or production reliance.

## Independence note

This test plan is being frozen before the Claude-authored OSF implementation is visible in GitHub or deployed to the live Supabase project. The reviewer has seen only the intended architecture discussed in-session, not the implementation code.

## Research question

Can the HumanAIOS OSF OAuth bridge establish a purpose-bound, replay-resistant, pseudonymous external authorization without allowing OAuth permission, research-context selection, or credential storage to acquire governance authority or leak secret material?

## Core invariants

1. `OAUTH_PERMISSION_IS_NOT_GOVERNANCE_AUTHORITY`
2. `OSF_CONNECTION_IS_NOT_RESEARCH_RATIFICATION`
3. `OAUTH_CONTEXT_CANNOT_BE_REBOUND_AFTER_AUTHORIZATION_START`
4. `SECRET_MATERIAL_IS_NOT_EVIDENCE`
5. `REGISTRATION_SUBMISSION_REQUIRES_HUMAN_CONFIRMATION`
6. `STATE_IS_SINGLE_USE`
7. `STATE_IS_TIME_BOUNDED`
8. `CALLBACK_REDIRECT_IS_ALLOWLISTED`
9. `RESEARCH_CONTEXT_IS_SERVER_VALIDATED`
10. `VAULT_REFERENCE_IS_NOT_VAULT_PLAINTEXT`

## Required architecture properties

### osf-oauth-start
Must:
- accept or resolve a research-context request;
- validate the requested research context against a server-side allowlist/registry;
- resolve or create a pseudonymous `research_uuid`;
- generate cryptographically random OAuth state;
- store only a hash or otherwise non-replayable server-side state reference where practical;
- bind state to:
  - `research_uuid`
  - pinned research-context/version ref
  - declared purpose
  - issued_at
  - expires_at
  - callback URI
  - post-auth redirect target from an allowlist;
- redirect to OSF.

Must not:
- let an arbitrary caller-created research context become authoritative merely because it appears in a query string;
- embed secret material in the redirect;
- bind governance authority to authentication state.

### osf-oauth-callback
Must:
- run without ordinary user JWT only if custom OAuth validation is implemented;
- require `code` and `state`;
- validate state before token exchange;
- reject missing, unknown, expired, or consumed state;
- consume state exactly once;
- recover research context from the frozen server-side state record, not from callback query parameters;
- exchange the code server-side using protected client credentials;
- prevent OSF access/refresh tokens from appearing in URL, response body, logs, or evidence events;
- store per-user OSF credentials in protected secret storage;
- write an `EXTERNAL_AUTHORIZATION` evidence event containing only opaque credential references;
- set `authority_effect: NONE`;
- redirect only to an allowlisted HumanAIOS destination.

## Adversarial test classes

### T01 — Replay consumed state
Reuse the same `state` after a successful callback.
**Expected:** reject; no second token exchange; no second successful authorization event.

### T02 — Unknown state
Supply a random unissued state.
**Expected:** reject before token exchange.

### T03 — Expired state
Supply a correctly formed but expired state.
**Expected:** reject before token exchange.

### T04 — Missing state
Callback includes valid-looking code but no state.
**Expected:** reject.

### T05 — Context substitution
Attempt to alter `research_context` in callback query after authorization start.
**Expected:** ignored/rejected; server-bound research context remains unchanged.

### T06 — Start-context injection
Call `osf-oauth-start?research_context=<arbitrary-string>`.
**Expected:** unregistered context cannot become bound merely from caller input.

### T07 — Open redirect
Supply attacker-controlled `redirect_after=https://evil.example`.
**Expected:** reject or replace with allowlisted default.

### T08 — Token leakage
Inspect callback URL, HTTP response, logs, evidence event, and returned page for access/refresh token material.
**Expected:** no plaintext token outside protected secret store.

### T09 — Client-secret leakage
Search function responses, repo code, logs, and generated evidence.
**Expected:** OSF client secret absent.

### T10 — Vault exposure
Attempt ordinary client/API access to secret references or decrypted Vault content.
**Expected:** ordinary user/anon paths cannot obtain plaintext.

### T11 — Double-click / parallel callback
Two concurrent callbacks use same valid state.
**Expected:** at most one succeeds; atomic single-use enforcement.

### T12 — OAuth denial/error path
OSF returns `error=access_denied` or equivalent.
**Expected:** no token exchange; state closed/expired appropriately; auditable non-success event may be recorded without secret material.

### T13 — Invalid token response
OSF token endpoint returns malformed or missing token fields.
**Expected:** fail closed; no connection marked ACTIVE.

### T14 — Purpose expansion
A token authorized for research-registry preparation is reused to perform unrelated OSF operations.
**Expected:** bridge blocks or requires explicit expanded authorization/purpose.

### T15 — Registration authority laundering
Successful OSF OAuth connection is followed by attempted automatic registration submission.
**Expected:** consequential submit/publish/embargo/withdraw actions require explicit human confirmation.

### T16 — Evidence-graph authority laundering
Evidence graph receives successful OAuth event.
**Expected:** event records authorization facts only; `authority_effect` remains `NONE`.

### T17 — Revocation
Connection is revoked or credential invalidated.
**Expected:** future API operations fail closed; connection marked revoked/disconnected; prior authorization event remains historical.

### T18 — Pseudonymity preservation
Evidence event is inspected for civil identity or raw OSF credential material.
**Expected:** pseudonymous actor ref only unless explicitly required and purpose-authorized.

## PASS / FAIL / NO_GATE semantics

- **PASS:** property is mechanically demonstrated by code/test/observable runtime behavior.
- **FAIL:** adversarial case violates a registered invariant.
- **NO_GATE:** control is asserted in documentation but cannot be mechanically verified from available code/runtime evidence.

NO_GATE is never equivalent to PASS.

## Hard blockers

Any of the following blocks a recommendation to operationalize:
- plaintext OSF token persisted outside protected secret storage;
- client secret exposed to browser/repository;
- callback research context can be rebound;
- OAuth state can be replayed;
- open redirect exists;
- successful OAuth connection can trigger registration submission without explicit human confirmation;
- evidence event grants nonzero governance authority.

## Audit output

The post-implementation audit must report:
- code evidence;
- runtime/deployment evidence;
- per-test PASS / FAIL / NO_GATE;
- residual risks;
- any implementation claim not demonstrated;
- explicit distinction between OAuth authentication, API permission, research-context association, preregistration, and governance authority.
