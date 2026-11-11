# Wardens' Council — HumanAIOS × cooperative campaign (prototype)

**Scope:** A separately deployable governance *prototype* for the existing **Wardens of the Craft** campaign. Its live game is currently hosted at `last-ward.cheeky-amber-5256.chatgpt.site`. This package does **not** modify that hosted site's source. It does not deploy Azure resources. The existing campaign co-op and versus remain the authoritative gameplay implementation (2–8 players, three shared heroes, first valid move wins; campaign saves preserved). The 33 previously reported game checks do not validate this package. This prototype has its own tests; 9 local tests passed on 2026-10-18.

## Game experience

Put a **Council of Wardens** tab next to Campaign co-op. Players submit suggestions (gameplay, design, lore, code), discuss and object, open ballots, and vote. Each room starts with a roster signed by the *game server* (not a room-code guess). The electorate freezes at ballot opening. One vote per verified room subject; passage needs a majority of **all** eligible voters, not merely votes cast. Ballots close once everyone voted, or after 24 hours. No one may close early to suppress votes. Lore/design/code proposals that pass become **advisory**, not executable authority. A bounded gameplay change (only hints enabled or turn timer 30–180 seconds in this specimen) becomes **approved_pending_checkpoint**. At a verified checkpoint the *game server* alone may apply it. The Council cannot change the battle arbiter's first-valid move rule or the story save data.

Player dialogue is stored locally for the room, with length limits. Vote and governance event records are hash-linked; discussion content is deliberately excluded from the event chain and from any research export. Hash linking detects accidental/simple tampering; it is **not** a signed transparency ledger or immutable storage. A server with database access could rewrite the chain; anchor or sign digests before relying on integrity claims.

## HumanAIOS boundaries

- **INTENT-OS:** A suggestion is a declared intent, *not* a command.
- **Coordinator:** Type, actor, room, and state transition are checked; a vote is not HumanAIOS authorization.
- **Session/Evidence/Temporal Graph:** Map `room`, `proposal`, `ballot`, `vote` and `applied_rule` into a non-authoritative graph projection, after consent and privacy review.
- **SCVC:** Checkpoint-tagged rule versions and the game's own save continuity remain distinct, testable invariants.
- **Seed Constitution v0.1:** Inspiration for transparency, attribution and revocable authority only. The Seed is **unratified**; room polls are not a constitutional ratification and cannot merge code or publish the platform constitution.
- **ACAT/Empirica:** AI coding-agent claims can be evaluated separately. Do not silently classify real players as research subjects, infer psychology, or export their speech to research. Obtain clear consent and review before any individual-level research.

## Local test and API

```bash
python -m pip install fastapi uvicorn pytest httpx
pytest -q
COUNCIL_SIGNING_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')" python api.py
```

`api.mint(...)` is a **trusted game-server-only** helper, never expose it as a browser API. The game backend verifies its existing room membership, then issues a **short-lived player-only** bearer token with `sub` + `room`. The browser receives only this player token. The game server separately issues server-role assertions to update the authenticated room roster and apply approved rules. The HMAC secret stays in the game server and Council API; use a secure secret store, rotate it, and do not log it. TLS, rate limits, abuse review, origin restrictions, and robust identity/account recovery remain required before public exposure.

Server wiring (pseudocode, adapt to the actual game stack):

```js
// onRoomRosterChanged: game-server only
PUT /v1/rooms/<room>/members {"members": ["server-verified-subject-1", "..."]}
// server signs room-scoped Council assertions; never accept role from a browser
// after a real, server-verified save/checkpoint:
POST /v1/rooms/<room>/proposals/<id>/apply {"checkpoint": "campaign-stage-3"}
// apply only settings keys already implemented in the engine; never run player text as code
```

Browser wiring (game tab; no gameplay engine migration):

```js
import { mountWardensCouncil } from './council-widget.js';
mountWardensCouncil(document.getElementById('council'), {
  baseUrl: '/api/commons', room: game.roomCode,
  getPlayerToken: async () => (await (await fetch('/api/commons/player-token', {
    credentials: 'include'  // endpoint implemented by the original game backend
  })).json()).token
});
```

## Azure link: shadow first, no new spend in this PR

Link to **operations #915 / #918** and the `aioshuman-1045` Foundry project in `westus3`. Reuse existing Azure architecture and the approved **Azure shadow/secondary** ownership. Do not deploy a parallel game arbiter, duplicate the campaign saves, or enable billing without the existing budget/approval controls.

Target: existing backend emits **opted-in, schema-bounded, non-text** governance observations through an outbox. A single Azure Container App ingests/validates the observations and stores them in controlled PostgreSQL tables when the already planned Postgres service is deployed. Existing room play keeps working if Azure is offline. Later, use Azure Web PubSub for *Council notifications*, not for authoritative movement resolution, if latency and cost justify it. Azure Foundry AI agents may draft **advisory** proposals only: they are marked `agent`, never counted as unique human voters, and cannot execute code or merge PRs. GitHub feature proposals are translated into human-reviewed issues/PRs with protected CI, CodeRabbit and authenticated admission checks.


### Opt-in Azure observation export

`azure_shadow.py` reads Council event metadata **read-only**. By default it returns no events and makes **zero outbound requests**. After game-specific consent, privacy, Azure endpoint and budget review, the game backend can project a room's events and POST them to an explicitly authorized HTTPS collector. The exporter uses separate HMAC pseudonyms for room and proposal IDs. It never ships room codes, player IDs, player text, title, comment, ballot content, or game saves:

```python
from azure_shadow import project_room, send_shadow
observations = project_room(database_path, room_code, privacy_key, enabled=consent_granted)
send_shadow(approved_azure_url, collector_credential, observations, enabled=consent_granted)
```

This is **outbound client wiring only**. An authenticated receiving API, Azure resource deployment, dead-letter/retry/idempotency policy, provenance checks, and Postgres migration remain unimplemented. Do not mistake a projected event for a proof of consent, personhood, or a verified Azure ingestion.

### Deployment blockers (intentional)

1. Obtain the hosted game's editable source or connect its original code project. The public `chatgpt.site` URL does not grant backend access.
2. Build the server token minting adapter using the **real** game session system; room code alone is not an identity. Add bot resistance for game-wide voting; this prototype is **room-only**.
3. Replace local SQLite with Postgres transactions and test under concurrent Azure replicas (this prototype is single-writer/local only).
4. Add consent UX, data retention/moderation/export restrictions, egress limits, Azure budget alerts, identity controls, Key Vault, observability, IaC + protected CI. Keep the subscription owner and Microsoft for Startups credit eligibility decisions with the authorized human.
5. Verify game-rule hooks exist before enabling each key. `turn_timer_seconds` and `hints_enabled` are **example contracts**, not confirmed game features.
6. Run two-browser visual checks and all original 33 game tests again after integration, plus replay, concurrent ballot, Sybil/identity, and rollback tests. Verify that no Council state changes the campaign save until checkpoint.

**Do not describe this as deployed, connected to Azure, or merged.** This is a governed integration specimen ready for review.