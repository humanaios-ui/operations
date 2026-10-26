# R2 — The Sounding (M045) · AI-OFF tactical vertical slice

**Status:** standalone local prototype, not connected to the canonical multiplayer engine, not live or cloud-hosted. World vNext #1020 design, with R1 locked prototype rules in `../WORLD_RULES_FREEZE.md`.

Start: open `index.html` in browser using any local HTTP static server; or package with the offline builder. Requires no packages, network, model keys, Discord, or identity.

- 7×5 accessible readable board; barriers force **upper** or **lower** route; one optional repair relay.
- Player selects **Quiet Footfall** (lower noise) or **Prism Ward** (two resonance shields), without inference about the player.
- Every accepted action advances `runTick` once. Neither `worldTick` nor legacy co-op move arbitration can be modified by this engine.
- Primary: secure the living specimen at (5,2) and extract at (6,2). Secondary: stabilize the relay at (3,0).
- Resonant Kin scripted visual signal at (4,1) or (4,3): explicit accept/decline or bypass, not an AI or a Witness.
- Attention reaches 10 = `OVERWHELMED`; Resonance reaches 4 = `FRACTURED`; 30 accepted actions = `TIMEOUT`. Voluntary exit = `WITHDREW`. Failure gives readable feedback and allows restart.
- Explicit player-consented Dawn Deck choice; no automatic evolution, research telemetry, external calls, scoring of real psychological attributes, or cross-player disclosure.
- Header notes local status; this file does not issue a permanent settlement receipt, Council vote, or Seed amendment.

## Tests

`node --test descent/tests/engine.test.mjs` from `experiments/game-vnext/`, or `node --test tests/engine.test.mjs` from this folder. Deterministic trajectories test both routes, protection tradeoffs, failure, replay, invalid input, and no Witness action tools.

## Remaining gates

1. Real-player fun test: 5 first-time testers without instructions; comprehension, tactic choice, failure recovery, replay desire, accessibility; **not yet measured**.
2. Independent browser/mobile visual and keyboard test; full consent and security review.
3. Check source/brand and appropriate rights. `The Last Thread` is a *working* title.
4. Integrate behind an explicit engine adapter only after actual hosted game source and original 33 tests, production Lineage #984 adapter and Azure #915 gate. No network-backed players in this R2 specimen.
