# WORLD_RULES v2.1 — Reconciled, Executable **Prototype** Contract

Status: **LOCAL_SINGLE_PLAYER_TESTED**. Input: supplied Xerodrome Seal v2.0 / audit #1016. This is a fictional ruleset, not physics simulation or the original 2–8 player game.

## Accepted rule decisions (prototype only; subject to game-design review)

1. **One global 30-action clock** begins when the post-Genesis prologue campaign starts, not when a player first creates an account. Each available move, mission, rest, upgrade, or ending action advances exactly one tick. Invalid commands do not advance time. Solo campaign saves are local test data.
2. **Black Dawn** is referred to in player-facing text as **Cinder Veil**. Orbital display assumes wave center at *Vessel / Vael planet center* `(1.0,0.0)` AU, rate `0.09 AU/tick`. Furnace at surface azimuth 300° is **its fictional source event**, not an alternative simulation center. This explicit abstraction separates depth from orbital frames rather than asserting precision for a surface projection. Front is a **hazard**, never a travel link.
3. **Null Ground / Outer Haven** center `(2.78,1.95)` AU; radius `0.28 AU`; center distance `2.6402462 AU`. First shield contact `ceil((2.6402462-.28)/.09)=27`; center crossing `ceil(2.6402462/.09)=30`. **Tick 27 is warning, not instant defeat; the shield holds through 29; tick 30 triggers a timeout ending unless already resolved.** The shield capacity is fictional and not grounded in real spacecraft engineering.
4. **Furnace precursor** begins at tick 1; critical irreversible choice unlocks at tick 20. A player can explicitly choose **Control** or **Awakening** when eligible and at the Crucible. The `M042` mission is completed only by that action.
5. **Lattice cracks at tick 12**, leaving an accessible root repair/rupture window through tick 19. At Living Seam the player chooses `SHATTER` or `REINFORCE`; only shatter qualifies for Awakening, after first meeting the Murmur at Whisper Node.
6. **R-07** is reinterpreted as a declared *fictional accelerated transfer*: Cinder Quay → Evacuation Relay → Far Passage → Outer Haven. Travel costs exactly 1 tick and 1 supply per edge, with no physically impossible elevator spanning interplanetary distance. A marked **surface evacuation relay** survives after the old orbital ring has fallen. The original HQ at tick 3 is gone; M048 is now an **evacuated Inquisitor envoy** meeting at Rootvault before tick 19. These are new fictional premises, not silent repairs to the supplied map.
7. **R-09** is now a physically *local habitat tether*: Outer Haven orbital ring ↔ Stillground surface of the **distant refuge habitat**, NOT the planet Vessel. Securing the tether requires a **remote settlers' envoy** at Rootvault (M049) at ticks 1–24, avoiding the circular first-contact requirement. If never secured, it collapses at tick 25. Secured tethers survive until the end. This supersedes the source candidate's impossible 2.64 AU shaft and misplaced surface cap. Exact engineering is not simulated.
8. **Missions are locally reachable** using a constrained, undirected topological network. All movement costs 1 tick, normal 1 supply (a player-approved form upgrade can change a clearly stated cost). Hubs recover 3 supplies at the cost of a tick. Mission windows are explicit in `engine.mjs`.
9. **Severance** needs M049 prior to Outer Haven, M046 at Outer Haven before tick 27, travel to Stillground, then one explicit `SEVER` action that zeros carried Fragments and Resonance. It can finish before tick 20: a real alternative to waiting for the Crucible. No forced ending, final victory claim or automatic player-character death.
10. **Fictional NPC names and regions** are original candidate expressions, not human IDs. Token IDs and provenance remain in internal dev/research mappings, never as UI signatures. Source narrative characters A-H become authored NPCs only; the user's owned character remains independently saved. The coercive NPC Murmur is not the read-only Witness.

## Verified example paths (deterministic unit test suite)

- **Control:** start HAVEN; Rootvault M048; return, replenish until tick 18; Ashshaft (19), Crucible (20), Control (21).
- **Awakening:** Ashshaft, Living Seam, Whisper Node M045, Rootvault; return to Living Seam at tick 12 for M041:SHATTER; reposition and replenish; Crucible at tick 20; Awakening (21).
- **Severance:** Rootvault M049, return via Ashshaft for optional Fragment, evacuate via relay/far passage to Outer Haven, rest, M046, tether to Stillground, explicit Severance before tick 27.
- **Timeout:** 30 rest actions at starting Cinder Quay; world events at ticks 12, 20, 25 (if unsecured), 27 and 30.

## Out-of-scope guarantees

Playable paths above prove **specific reachable endings**, not an exhaustive traversal of every tactical state. This browser slice is a narrative/resource-and-time strategy game with no combat AI, no grid battle, no multiplayer synchronization, no production account, no authenticated cloud events, no LLM, no claim of physically realistic orbital mechanics. It does not replace original co-op or Azure deployment gates.