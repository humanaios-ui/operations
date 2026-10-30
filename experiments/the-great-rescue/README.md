# The Great Rescue — S0 Engineering Workshop

**Status:** two-player local prototype, code review required. **Not hosted, merged, or Handshake-submitted.**

Fresh game design, independently scoped from the archived Wardens/Last Thread experiments. Issue: [humanaios-ui/operations#1085](https://github.com/humanaios-ui/operations/issues/1085).

## The point of the game

Two players enter one workshop. Each builds a machine to carry a capsule over a deep gap and into the extraction dock. Players can inspect clues, place/rotate components, run physics tests, observe each other's builds, and offer parts. Official activations produce scores and a champion. If the capsule falls, adjust the machine and try again.

No hidden quests or narrative clocks. The object, the gap, the controls, the result, and how to win are visible.

## Run locally

Node.js **22+** is required. No packages or environment variables are needed.

```bash
npm start
```

Open **http://localhost:8765**. Create a room, then open a second *independent* browser or device at the same server address and join with the room code. A second physical device must use the hosting computer's LAN address (and the local firewall must allow inbound TCP on port 8765); `localhost` on the second device points to itself. Internet players require deployment to a reachable Node host with HTTPS.

`PORT=3000 npm start` changes the listening port. This prototype's rooms live only in one Node process and expire after three hours. Use one process; multi-instance deployment needs a transactional shared room store, which is **not** included.

## Rules — clear to first-time players

1. Two players are required. The first creates a six-character room code. The second joins independently.
2. Each has a separate construction bay, four platforms, two ramps, one spring and one lever. Explore the workshop for spare spring and lever parts and clues. Share spare parts by an offer that must be accepted by the other player.
3. Build on snap-to-grid anchors using a **Platform** (flat support), **Ramp** (up/down support), **Spring** (vertical launch and horizontal boost), or **Lever** (momentum boost). There is a **12-point material cap** and **8-part cap** per construction. Remove pieces to recover inventory. All the same launch physics apply to both players.
4. Hit **Test for free** to simulate the whole machine as often as needed. The capsule can fall into the gap, stall or reach the dock. Small launch variations are used only in official reliability scoring.
5. Hit **Launch official run** for a scored activation. Each player gets **two** official attempts. Their **best** score counts; no successful delivery means 0 points. You can also finish after one official attempt.
6. Both players finish, or the round deadline expires. See overall champion and separate speed, material-efficiency and reliability awards. Vote for the other player's ingenuity after results. Ties share first place; ingenuity is not part of the overall score.
7. Host can start a rematch with a fresh starting inventory.

A useful *learning experiment*: a platform can support the capsule only where the flight crosses the part's surface. Try supporting the lower part of the gap, then see what happens when a support is removed.

### Scoring (maximum 100)

- **Completion: 40** points if the standard launch reaches the dock.
- **Speed: up to 20** = `round(20 * (1 - steps / 215))`, minimum 0.
- **Efficiency: up to 20** = `round(20 * (1 - materialCost / 12))`, minimum 0.
- **Reliability: up to 20** = `round(20 * successes / 3)` across 3 launches with speed variations -1.6%, nominal, +1.6%.
- All four components are 0 for a failed nominal launch. Ties share overall first place. Peer ingenuity votes do not change points.

## Tests

```bash
npm test
node --check server.mjs
node --check engine.mjs
node --check public/app.mjs
```

The engine and API tests cover real gap failure, successful rescue through a four-platform bridge, deterministic physics, player isolation, two clients in one room, material caps, duplicate request IDs, official attempts, trades with consent, scores, awards, and rematch.

An additional **Chromium two-context UI smoke test** was executed with the complete page inlined and browser `fetch` proxied to the real local server, because the automation sandbox blocked direct `localhost` navigation (`ERR_BLOCKED_BY_ADMINISTRATOR`). It confirmed the full host/join/build/test/submit/win flow, a guest viewing another builder's machine, and a 430px mobile layout without horizontal overflow. It **does not** establish a real external browser or device connection. Genuine deployment and two-device field testing remain gates.

## Security and limitations

- All accepted moves and scores are calculated by the Node host, not the client; bearer player tokens stay in the local browser session store.
- Each room is limited to two participants; names are stripped of control characters; HTTP request bodies are capped; same-origin POST is required; action IDs prevent accidental double-spending.
- **Ephemeral state:** server restart deletes rooms and builds. There are no user accounts, production persistence, distributed locks, user-generated text chat, AI model calls, or monetization.
- Simplified **2D game physics**, not engineering-grade dynamics: fixed timestep, gravity, linear supports, contact impulses, bounded launch perturbations. Do not represent this as physically accurate simulation of complex machinery.
- Component attachment and rigid-body constraints are not modeled. Two-user interaction is **observe and exchange parts**, not collaborative editing of one shared mechanism. Rich alliances, sabotage, and persistent sandbox progression are later requirements.
- Actual Handshake acceptance needs **publicly reachable HTTPS URL**, two genuinely separate devices, a new-player comprehension test and human playtest. No public deployment or human approval to merge is asserted here.
