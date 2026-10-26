# R1 / R2 Test Report — 2026-10-25 (America/New_York)

**Target:** draft PR #1028 · feat/game-vnext-r1-freeze-r2-ai-off-20261025 · isolate from live game.  
**Rules freeze:** `WORLD_RULES_FREEZE.md` = `R1-FREEZE-0.1`, review-only.  
**Executed evidence:** GitHub Actions `Game vNext R1 freeze and R2 AI-off mission`, [run 40251487752](https://github.com/humanaios-ui/operations/actions/runs/40251487752), head `339ea622a65c5c3236f561f424229c9bf25dcbf7` (before this documentation commit).

## Verified on the named head

- **Node tests: 24 PASS, 0 FAIL** on GitHub CI. Includes Control/Awakening/Severance/Timeout reachability, the real 0-supply deadlock regression, free M040/Sight Lattice actions, region-wide empty-supply recovery, adjacency map static test, offline HTML parity, R2 deterministic north and south routes, both deck types, hazard counterplay, invalid command no-tick, replay, and Witness boundary.
- **Offline builds:** Python solo and Descent one-file HTML rebuilt from checked-in modular source with `git diff --exit-code`: PASS.
- **Syntax:** All four .mjs files: PASS in CI.
- **AI-off / outbound-network static guard:** PASS.
- **Isolated Chromium test in the assistant's container:** `page.set_content` using complete inline R2 HTML and JS, player selected `Quiet Footfall`, completed north route in **10 accepted actions**, ended `EXTRACTED`, **0 page errors**. Visual screenshot captured separately during the run. `Page.goto(http://127.0.0.1/...)` was blocked by `ERR_BLOCKED_BY_ADMINISTRATOR` in the sandbox; this is **not** a tested HTTP/public/mobile launch.
- **No active connection** to original co-op save backend, Discord, Azure, real player identity or W1. Do not infer the original game's 33 checks passed.

## Not yet verified
- Independent designer / CodeRabbit findings on this exact head.
- Five human player usability/fun scores, no-sound and keyboard-only trials.
- Real browser URL or phone test under a non-blocked runner.
- Concurrent player acceptance, room save continuity, first-valid-move regression, real permanent Witness integration.
- Rights/title publication clearance, Azure budget/identity/production admission.

## Entry to next test
Ship no live changes. Use the downloaded R2 `descent/PLAY_OFFLINE.html` with 5 consenting first-time test participants under `PLAYTEST_PROTOCOL.md`. Test offline and record only volunteered feedback. Fix severity-1 softlocks/unclear controls before attempting #1020 R3 or real co-op integration.

**Research distinction:** The mission is **functionally playable and deterministic** in test. Whether it is **enjoyable** is an open empirical question, not proven by code or a self-run bot path.
