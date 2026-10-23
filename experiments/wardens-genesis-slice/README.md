# Genesis Soil — local playable test slice

A standalone, asset-backed, **local only** front-end prototype. This is not the hosted Wardens of the Craft game; it neither connects to the player identity service nor supersedes Council, Witness, Discord or Azure infrastructure.

## Run

```bash
cd wardens-genesis-slice
python -m http.server 8765
# open http://127.0.0.1:8765/
```

All five artwork assets are optimized WebP derivatives of the five reference images provided by the user in this chat. They are not fetched from third-party providers. Obtain publishing rights approval before hosting publicly.

The demo's localStorage supports reload only on the same browser origin. **It is not permanent Witness identity or verified archival storage.** Its Witness is deterministic, event-cited history replay, not an AI model; it makes no moves, votes, recommendations, or outbound requests.

No live Azure, Discord, co-op, real Council voting or production account is connected here. The prototype does not re-run the game engine's existing 33 tests. Production integration requires the actual live game source and gates listed in DESIGN_BRIEF.md.

## Tests

```bash
node tests/test_logic.mjs\n# Optional real Chromium test when the browser environment allows local URLs:\npython -m pytest -q tests/test_playable.py
```

The Node harness verifies the state machine and core boundaries without a browser. Playwright tests need an environment that permits local HTTP; the current secure browser blocked localhost navigation. Never run tests against production.
