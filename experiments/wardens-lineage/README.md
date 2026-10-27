# Wardens Lineage — persistent player identity + personal Witness

Status: tested single-worker prototype; **not live**, not Azure deployed. Paired with existing [Genesis Soil](https://github.com/humanaios-ui/operations/blob/main/experiments/wardens-constitution-soil/PROTOCOL_V0_1.md) and Council #921. Existing hosted game code is not here, so no game hookup is claimed.

## Implemented in this package

- Stable first-party `player_id` (UUID), independent of Discord and campaign room code. Trusted game login adapter calls `/v1/server/players/resolve`; browser clients cannot mint IDs, identity claims, or game events.
- Append-only, hash-linked per-campaign records. Idempotent game-server event ingestion with source reference and digest. History survives process restart and spans campaigns. Source digest is *provided by game server*, **not cryptographically verified against source yet**; game integration must supply and verify signed authoritative events.
- Private vs campaign-shared visibility; player consent WITNESS defaults off, separate from research consent (also off). Human Second Witness acknowledges, contests or declines own Genesis Event; never grants authority.
- Discord OAuth2 (`identify`) linking with PKCE, state, expiry, one-use state, `/users/@me` identity verification, uniqueness, unlink. **Discord does not create the canonical user identity.** No token storage; linked Discord user can be reconnected later.
- Signed Discord slash interactions: `/witness` and `/lineage` read **only** authorized history, responding with ephemeral messages. This is deterministic history rendering, **not** a language model, no gameplay advice or write tools.
- Ten automated local tests: restarts, cross-campaign continuity, privacy, revocation, idempotency/collisions, integrity tampering, own-attestation checks, account-link hijack resistance, OAuth state replay, short-lived signature, trusted-server enforcement, Discord request signatures.

## Local run (test only)

```bash
python -m pip install -r requirements.txt
python -m pytest -q
export LINEAGE_DB=/tmp/wardens-lineage.sqlite
export PLAYER_ASSERTION_KEY='REPLACE_WITH_DISTINCT_AT_LEAST_32_CHAR_SECRET'
export GAME_SERVICE_KEY='REPLACE_WITH_ANOTHER_AT_LEAST_32_CHAR_SECRET'
# optional Discord: DISCORD_CLIENT_ID / DISCORD_CLIENT_SECRET / DISCORD_REDIRECT_URI / DISCORD_PUBLIC_KEY
python api.py
```

Never put game-service or OAuth client-secret values in a browser or Discord message. Example identity assertions are minted only by an existing **trusted game auth server**. Public sign-up and account recovery **are not** implemented here.

## Azure gating (must pass before production)

1. Acquire and review actual game source; wire the game server's auth/verified event emitter and preserved move/save authority.
2. Replace local SQLite with transactional Azure PostgreSQL Flexible Server backed by migration, multi-replica tests, managed identity/secure secrets, backups and restore trials. The `postgres_schema.sql` is a **planning migration**, not an operational adapter.
3. Verify identity assurance, subject uniqueness, token rotation, account recovery, Discord authorization, link confirmation and abuse limits. Production should use existing OIDC issuer/JWKS instead of demo HMAC assertions and shared keys.
4. Enforce server-side permissions for undiscovered events and personal snapshots; PII minimization, retention/deletion/export policy, research consent audit, encryption at rest and logging redaction.
5. Provision Discord app secrets, verify callback URL and signature, register limited commands (without privileged Gateway intents). No unprompted messages.
6. Build secure Container App image via protected CI and deploy only after owner budget approval and Azure #915 controls. Keep existing working game backend while testing shadow read-only bridge.
7. Run two-browser, concurrency, replay/tamper, restore, game 33-check regression, and Azure outage tests; do not claim the hosted game is migrated until evidence passes.

## Boundaries

`GAME_EVENT != VERIFIED_REALITY` and `SOURCE_DIGEST_STRING != SOURCE_ATTESTATION`. Oracle/Witness has `authority_effect: NONE`. The Seed Constitution remains unratified; Discord chat, game votes and AI responses never ratify it. No covert profiling, persuasion, external AI advice, or automatic training on player content.

Discord docs: <https://docs.discord.com/llms.txt> and [Interactions](https://docs.discord.com/developers/interactions/overview.md). Azure docs: <https://learn.microsoft.com/en-us/azure/container-apps/managed-identity>.