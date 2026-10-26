# Game vNext — R1 World Rules Freeze v0.1

**State:** a versioned *prototype rules freeze for review* under game charter [operations #1020](https://github.com/humanaios-ui/operations/issues/1020). Not constitution, not ratified HumanAIOS law, not an approved product/production release. Do not modify the original 2–8 player co-op game or the Seed Constitution.

**Source and provenance**
- World model derives from the archived prototype [PR #1017, HEAD `2ede7880`](https://github.com/humanaios-ui/operations/pull/1017), itself a reconciliation of Xerodrome audit [PR #1016](https://github.com/humanaios-ui/operations/pull/1016).
- This PR creates a reviewable, repaired copy in `experiments/game-vnext/solo`. It is **not** a merge or retroactive modification of old archived PRs.
- The real game source, original 33 checks, permanent player identity, Discord and Azure deployment remain separate and untouched.

## Frozen gameplay truth

| Rule | Locked prototype behavior |
|---|---|
| Genesis | User chooses name and one of four fictional forms. No phenotype/genomic/psychological profiling. |
| Legacy solo clock | Exactly 1 action = 1 `world_tick`; 0..30. Invalid command = 0 ticks, state unchanged. All three endings plus timeout remain reachable by authored paths. |
| R2 Descent clock | Each mission has separate `runTick` 0..30 **accepted actions**. It cannot advance `worldTick` automatically. Hub/menu states do not consume a run turn. A future cross-layer settlement requires authoritative idempotent receipt + per-player approval, not included. |
| World events | Lattice fractures at tick 12; Furnace irreversible breach at tick 20; unsecured local tether breaks at tick 25; outer shield contact at tick 27; center arrival and timeout at tick 30. Contact (27) is **not** center crossing (30). |
| Fictional motion | Source Cinder Veil moves schematically 0.09 AU per global tick from planet-centered frame. This is not validated astrophysics. Upper orbit is 2.6402462 AU from center; radius 0.28 AU gives first shield contact tick 27 and center tick 30. |
| Travel | Physical local shaft/tether only inside a shared frame; distant relay uses declared fictional accelerated transport (R-07), never a 2.64 AU elevator. Graph movement 1 tick, normally 1 supply; explicit upgrade can grant cost-zero TRANSIT. |
| Scarcity | No unwinnable 0-supply silent deadlocks: hubs REST (+3 supply, 1 tick); remote exhausted character can SCAVENGE (+2 supply, +1 Resonance, 1 tick). Cost-zero `M040` and free Sight Lattice TRANSIT remain legal without supplies. Every recovery trades time for resources. |
| Missions | Always validate **actual per-choice cost**, time window, location, and requirements. M040 costs 0. M045 fictional Murmur ≠ W1 Witness. M048 envoy evacuated; M049 tether authorization is remote and before arrival. |
| Map | Only edges incident on **current node** can be marked available. Future remote links are not highlighted as reachable. |
| Endings | CONTROL requires M048 and Furnace 20..29. AWAKENING requires M045 + M041 SHATTER and Furnace 20..29. SEVERANCE requires M049 + M046 + NULL_CAP before 30; all carried fragments relinquished voluntarily. All paths remain player-selected. |
| R2 mission | One 7×5 board `The Sounding` (M045). Two routes, one Dawn Deck selection, one scripted Resonant Kin encounter, optional relay, specimen and extraction. AI disabled. Deterministic movement, Attention threshold 10, Resonance threshold 4, max 30 actions. |
| Player autonomy | No forced form transition, forced Council vote, automatic campaign settlement, or loss of personal history from an optional Descent. |
| Witness | Read-only, opt-in, scoped memory. No hints, tactical predictions, game actions, private cross-player access, voting, or authoritative assertions. R2 runs without a real W1 connection. |
| Council | Existing #921 rule changes governed and checkpoint-bound; R2 does not grant Council or source amendment power. |
| Accessibility | Important faction cues must work without sound. R2 uses readable text and icon markers; no real audio dependencies or latent personality inference. |
| Data | Prototype stores only local temporary data. Local event IDs are not signed first-party receipts. No external telemetry. |

## Freeze policy / changes

- The values above are pinned as `R1-FREEZE-0.1`, not "forever". Any change requires its own authored rule diff, explicit reason, tests for all affected endings, and protected review under #1020.
- Derived animation / exact art may change without changing rules, but map coordinates, resource costs, time gates, privacy and authority are rules.
- R2 shares **ideas**, not authoritative state, with the repaired solo engine. Until integrated into a verified server, do not make R2 settlement increment canonical world time.

## Repair ledger (archived PR #1017 reviewer findings)

| Problem | Repair | Regression expected |
|---|---|---|
| Resource-zero deadlock outside hub | Remote `SCAVENGE`, finite tick cost | Any legal 0-supply nonterminal state has a next action; eventually timeout even if stranded |
| Free travel hidden at 0 supply | Cost-aware move filter; Sight Lattice free TRANSIT | Free TRANSIT remains available with zero supply |
| Free M040 hidden | Cost-aware mission filter | M040 remains available at 0 supply at HAVEN, within window |
| Map shows nonadjacent links as available | Must include current node | Only current incident edges marked active |
| Packaging rejects SVG namespace URL | Exact namespace exception and no outbound request check rather than blanket `http` assertion | Static source can use `http://www.w3.org/2000/svg` as an XML namespace; no network is created |
| Stale bundled HTML vs modules | Build standalone from repaired modular files; compare generated output in CI | Standalone is regenerated and checked for current repairs |

## Required evidence for R1/R2 promotion

1. Replay Control/Awakening/Severance + TIMEOUT and 0-supply edge cases under the same solo engine.
2. R2 two routes and both Deck choices complete, hazard/counterplay failure, one scripted faction signal, extraction + optional task, source-attributed local receipts.
3. Keyboard/mouse, no-sound comprehension, five real players with independent usability feedback — **not yet proven**.
4. Confirm full original hosted game 33 checks and concurrent move/save behavior after real integration; cannot be inferred from these tests.
5. Azure credentials, costs, Discord and signed event adapters need separate human authorization. No deployment in R1/R2.

**Core:** Campaign gives choices meaning. Descent tests those choices. NPCs may present bounded offers. The Witness remembers and does not act.
