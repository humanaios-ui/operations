# Genesis Soil — local playable test slice

A standalone, asset-backed, **local only** front-end prototype. This is not the hosted Wardens of the Craft game; it neither connects to the player identity service nor supersedes Council, Witness, Discord or Azure infrastructure.

## Solar–Tellurian fictional overlay

The five original zones now carry a [Cyclonopedia-inspired narrative layer](./TELLURIAN_OVERLAY.md): distant Solar light, living soil (fictional personification), the Black Corpse of the Sun as a metaphor for buried energy history, Ember/Archive/Forge as different *story* paths, and the unreached Tellurian Omega. **The overlay does not change game decisions, events, the Witness's read-only access, optional consent, local-only storage, or the Council's draft-only nature.** A missing record is not proof of deliberate erasure. No claim is made that fictional cosmology or petroleum agency is real.

## Run

```bash
cd experiments/wardens-genesis-slice
python -m http.server 8765
# open http://127.0.0.1:8765/
```

All five artwork assets are optimized WebP derivatives of the five reference images provided by the user in this chat. They are not fetched from third-party providers. Obtain publishing rights approval before hosting publicly.

The demo's localStorage supports reload only on the same browser origin. **It is not permanent Witness identity or verified archival storage.** Its Witness is deterministic, event-cited history replay, not an AI model; it makes no moves, votes, recommendations, or outbound requests.

No live Azure, Discord, co-op, real Council voting or production account is connected here. The prototype does not re-run the game engine's existing 33 tests. Production integration requires the actual live game source and gates listed in DESIGN_BRIEF.md.

## Tests

```bash
node tests/test_logic.mjs
node tests/test_myth_static.mjs
# Optional browser test only when an actual browser test file is present and a local browser is permitted
# No real-browser E2E PASS has been established here.
```

The Node harness verifies the state machine and core boundaries without a browser. Playwright tests need an environment that permits local HTTP; the current secure browser blocked localhost navigation. Never run tests against production.
