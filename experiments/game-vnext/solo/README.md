# THE LAST THREAD — The Vessel Chronicles (working names)

**Playable local browser prototype**, a 30-action-tick narrative resource-strategy campaign. Single player. Not the original hosted co-op game, not Azure, not real Discord, not permanently authenticated personal Witness. **No production authority.**

## Play

Open [`PLAY_OFFLINE.html`](PLAY_OFFLINE.html) in a modern desktop/mobile browser. All HTML/CSS/JS is embedded. If your browser blocks a local file, serve the development folder:

```bash
python3 -m http.server 8765
# then open http://localhost:8765/
```

Choose form → travel via action cards or keyboard-accessible map nodes → complete missions, manage supplies/ticks, rest at hubs, and aim for one of three endings. You may also lose to the 30-tick countdown. Every major action advances time once; invalid actions do not.

## Test

```bash
node --test tests/engine.test.mjs
python3 build_standalone.py
python3 tests/test_browser.py
```

No npm install or third-party runtime dependencies. Browser test uses optional Playwright + local Chromium if present. Because URL navigation is blocked in some secure test environments, it uses `page.set_content` to verify UI interactions in real Chromium; **this is not proof of publicly hosted page access or multi-browser compatibility**.

## Design provenance and autonomy

- [`WORLD_RULES_V2_1.md`](WORLD_RULES_V2_1.md): explicit reconciliation of 27 vs 30, orbit/shaft conflict, HQ flight, M049 loop, action costs and proven branch scripts.
- [`BRAND_GAMEPLAY_BLUEPRINT.md`](BRAND_GAMEPLAY_BLUEPRINT.md): independent player-facing naming and visual identity, IP/licensing checklist, game-design theories, tools and user playtest measurements.
- `engine.mjs` is **pure game logic** with finite typed commands. The human-memory Witness is an opt-in read-only projection of local event receipts; the coercive fictional Murmur is a different character with no memory privileges.
- `ui.mjs`, `style.css`, `index.html`: original prototype interface and topological interactive map. No external requests, analytics, cookies, models or embedded third-party art.
- Local browser saves are **not verified**, tamperproof, encrypted, or safe for sensitive data. Production persistence belongs to the existing first-party service, after server-verified authentication/event integration.

## Authoritative preservation

Original game's **2–8 player shared heroes, first valid move counts, room saves, and 33 reported checks are untouched and not retested by this project**. Source review and gameplay integration tests are required before porting any of these mechanics. Azure hosting and account linking require separate access/budget/security approvals.

## Green ≠ shipped

Unit tests establish reachable *specific paths*, bounded time, event citation, import rejection and deterministic replay. Browser UI tests establish interactions in a local Chromium `set_content` sandbox. The full multiplayer/server behavior, visual quality on devices, accessibility with real players, retention, intellectual property clearance, and cloud testing are still outstanding.

## R1 repaired import
This revised review-only copy comes from archived PR #1017. Changes fix remote 0-supply deadlocks, cost-zero actions, current-location graph highlighting, and standalone build. Its original live multiplayer source is untouched. See `../WORLD_RULES_FREEZE.md`.
