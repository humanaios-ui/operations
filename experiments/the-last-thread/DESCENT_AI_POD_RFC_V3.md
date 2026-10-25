# The Last Thread — Descent / AI / Pod gameplay RFC v3.0

**Status:** REVIEW CANDIDATE — branch stacked on `feat/last-thread-original-campaign-v2-1` (PR #1017). **No change to existing campaign engine, multiplayer game, Azure infrastructure, Witness model, or canonical ending admission.**  
**Authority:** Existing standalone 30-action game `engine.mjs` remains the runnable reference; original 2–8 player co-op has not been migrated.  
**Proposal:** Add an *optional* run-based mission mode, bounded NPC negotiation, and an opt-in cetacean-inspired faction while preserving existing world rules and token history.

## Product promise and scope

**The player fantasy:** Enter a dangerous zone. Choose one objective worth risking everything for. Build a temporary tactical advantage. Negotiate with forces that remember what you did. Escape before the wave arrives. Return to a safe hub where your choices reshape relationships and future contracts.

**First playable target:** one 8–15 minute mission with visible risk/choice/payoff, plus a repeatable 30-action hard limit. This time is a design target, **not** measured by tests.

**Don't build an AI demo that masquerades as a game.** If the core loop is unfun with the AI disabled, fix map affordances and mission tension first.

## Stack and ownership

| Layer | Owns | May not own |
|---|---|---|
| **Campaign** (v2.1 baseline, authoritative for campaign state) | Quest prerequisites M040–M049, relationships, faction reputation, path P050/051/052 and ending availability, persistent character lineage, world stage | In-match cosmetic dialogue |
| **Descent Run** (new, temporary but replay-logged) | A 30-accepted-action local tick budget, objectives, mission map, hazards, Attention, Resonance thresholds, Dawn Deck and extraction | Canonical mission completion unless the campaign settlement validates a result |
| **AI agent candidates** | Select **allowed, typed** offer/pressure/glyph intents based only on permitted game state and faction goals | Raw game state writes, unlisted modifiers, hidden player profiling, Witness memory, human authorization, Council vote |
| **Hub** (Rootvault / Outer Haven) | Time-free menus, contract choice, pact drafting, upgrades, reviewing outcomes | Unlimited free resource grants, reroll farming, extra Council rights |
| **Read-only Memory Archive** (W1) | Explains authorized **settled** campaign events with citations | Tactical recommendations, choices, enemy AI, game writes, factual claims from NPC speech |

## Timing reconciliation: two clocks, one canonical world

The user proposal says *reset a 30-tick clock for each mission* AND *preserve the old 30-tick desertification milestones*. These cannot both refer to the same clock: the Furnace would become irreversible during **every** mission and the orbital Black Dawn would somehow begin anew each run.

**v3 test rule (provisional, preserve v2.1 in production):**

- `run_tick`: integer 0…30, resets at each `DESCENT_STARTED`. Only a **server-accepted action** advances it. If players extract at 18, the run ends immediately and results settle; if they hit 30, deterministic forced extraction/failure handling runs. A 30-tick cap need not require 30 actions.
- `world_tick`: integer 0…30, **monotonic across runs**. Hubs consume no world ticks; the world advances only when a Descent **settles or aborts**, never when a player opens a menu or talks to a Witness.
- **Proposed advancement for balancing**: `Δworld_tick = min(6, 1 + ceil(run_tick / 6))` on settlement; aborted runs pay the same time cost. This is **one candidate pacing formula**, not an accepted canon or physically derived rate. No zero-cost retreat exploit.
- `world_tick` triggers world-stage events at 12 (Lattice), 20 (irreversible Furnace decision), 25 (unsecured local tether), 27 (first Null shield contact), 30 (Null center crossing). This preserves the exact existing 27/30 distinction.
- `run_tick` triggers **in-match** pressure, modifiers and escape threats. It is **not** a second real orbital `0.09 AU/tick` Black Dawn front reset. Use a named **local Veil surge** whose intensity depends on region, `world_tick`, and the current run rather than duplicating the solar system.
- At `world_tick>=30`, forbid launching new Descents; resolve a campaign end/aftermath. No player can hang out safely at a hub and produce resources forever. Hubs can remain time-free, with finite purchases, cooldowns per run, and 1 pact per run.
- In multiplayer, `run_tick` increments exactly once for the **first validated authoritative action**, not once per viewer, rejected input, queued model output, or speculative client animation.

`world_tick` after a run is computed by the **campaign engine**, not by an LLM or a Dawn card. A full reachability search must show all three existing endings remain obtainable after this pacing change. **Until that test passes, v2.1's single global clock remains the reference.**

## Contract and match loop — P-10, P-11, P-12, P-13, P-17, P-18

`CONTRACT_OFFERED → HUB_PREP → DAWN_DRAFT → RUN_STARTED → ACTION+COUNTERPLAY → EXTRACT/FAIL → SETTLEMENT → CAMPAIGN_STATE`

A contract binds:
```json
{
  "template": "TOK-M-045",
  "contract_id": "run-opaque-id",
  "zone": "RN-2",
  "primary": "contact_murmur",
  "secondary": "save_root_node",
  "secret": null,
  "extraction": ["return_to_entry", "secured_route"],
  "run_cap": 30,
  "world_tick_at_start": 12,
  "seed": 408,
  "ruleset_version": "descent.v3.0-candidate"
}
```
The optional hidden objective must never be a required countermeasure the player cannot reasonably discover. Its existence, rules and rewards must be signposted. Hidden objectives may be **fictional character offers**, never covert psychological profiling.

### Dawn Deck

- Draft 3 bounded rule cards at `run_tick 0`. Take 1. With qualifying faction reputation, ban 1; otherwise other cards are discarded. A ban affects **that run only** and must not accidentally alter global factions or card pools.
- The proposed 5-tick repeat cadence means up to six draft interrupts; test whether it ruins flow. **Recommended first-build cadence:** 0, 10, 20 (3 windows); advanced 0,5,10,15,20,25 only after player testing.
- Every card defines `effect_id`, timing, duration, scope, stack cap, counterplay, UI icon, accessible non-color cue, and exact replay seed. `Solar Interdiction`, `Null Silence`, `Resonance Echo` are candidate **effect categories**; rebrand distinctive names and visuals before publishing.
- Prevent **softlocks**: no card may erase the only valid extraction route; any lock has a displayed countermeasure or alternate exit.

### Attention

- Node-local numeric `attention` is capped (first prototype: 0…10). Travel +1, hazardous fragment activity +2, quiet action 0 (candidate defaults).
- At 4, patrol threat telegraphs. At 7, patrol acts on its next eligible tick. At 10, a pressure event forces visible counterplay, never a surprise unpreventable loss.
- Reducing pressure spends **bounded faction favor** or requires a deliberate stealth action; don't allow infinite negative Attention or free favors.
- Agent intent cannot spoof a valid human action or advance an extra tick. No AI action outside its documented schedule.

### Resonance Surge

- Trigger **once per crossing** at 3/6/9 `resonance`, not on every frame or each value oscillation.
- Offer a risky one-run power through a *player-visible accept/decline*, with a concrete cost. Reversible cosmetic/temporary changes should be favored in a run; permanent player-form evolution remains explicitly approved through the campaign's separate system.
- NPC "hallucination" is labeled **in-world illusion**, not a falsification of the read-only Witness's event record.

### Extraction and settlement

- Extraction requires the character at a valid exit route; early extraction earns carried rewards and partial contract outcome, **not automatic full mission completion**.
- Campaign settlement validates provenance, accepted turn sequence, template-specific primary objective, inventory and ally requirements, then appends **one idempotent** receipt keyed by `contract_id`. Duplicate network deliveries cannot double reputation/resources.
- Run failure must still produce legible consequences and a **recoverable reason**. All endings can be pursued without a perfect first run; a failed run is not always dead progress.

## Agent classes — P-14, P-15, P-16, and Pod extension

**AI permission is below the game server:** Models may propose **structured intents only**, which a server-owned `authorize→validate→apply` reducer checks; LLM "function calling" alone is not a permission system.

- **TOK-AI-001 / Murmur** (formerly Voice H): Allowed intents `offer`, `threaten`, `illusion`, `propose_modifier`, `propose_route_reveal`, `request_spawn`. No actual private-memory read, character-form overwrite, research targeting, or generation of hidden new effect IDs. Influence is an in-game resource held by the **campaign state**.
- **TOK-AI-002 / Faction Conclave**: Each agent controls only its faction's permitted offer catalog; `reputation`, `faction_budget`, `world_stage`, player-approved pact flags. All contracts expire, have a displayed price and can be declined. Betrayal requires a predeclared rule and visible evidence, not arbitrary LLM whim.
- **TOK-AI-003 / Pact Forge**: Translate natural-language intent into **one of a finite number of pre-authored pact templates**. Return exact preview (effect, cost, limits, consequences). The user must explicitly sign/select it before server application; ambiguous proposals get no pact.
- **TOK-AI-004 / Pod Conclave**: **Non-prose glyph intentions** `ping`, `warn`, `offer_passage`, `withdraw`. A deterministic glyph script may be sufficient for first playtest; model output adds no authority or extra action IDs. Distinct sonar art/audio with accessibility text alternative.

Required validated intent minimum: `{actor_id, action_id, target_id, contract_id, ruleset_version}`. All properties allowlisted; target type and timing validated against current node and authoritative state; model result never provides free-form executable code. Reason and dialogue fields are **untrusted presentation text**, stripped of tool instructions.

**Every agent has a deterministic fallback.** The run must still work when AI service is down, times out, returns invalid JSON, or suggests a disallowed action.

**Witness distinction:** `The Murmur`, faction agents, and Pod can lie or bargain **as labeled fictional NPCs**. The private Memory Archive must only describe authorized campaign history and provide evidence citations. Agents must never read across another player's lineage or join tokens. AI dialog is not independent historical corroboration.

## Cetacean-inspired extension — review, not canonical commitment

Candidate tokens: `TOK-C-008` Echo-Song, `TOK-F-027` The Pod, `TOK-CH-I` Echo-That-Remembers, `TOK-S-040` Echolocation Map, `TOK-S-041` Pod Cohesion, `TOK-AI-004` Pod Conclave, `R-10` The Sounding. `TOK-P-053` Communion is **experimental, not a fourth canonical ending**.

**World-coherence repair:** In the reconciled v2.1 world, **Outer Haven is a distant habitat ~2.64 AU from Vessel**; its `Stillground` surface is *there*, not on Vessel. RN-1..4 are deep below Vessel. A natural water-filled tunnel between them is impossible. **Define R-10 strictly as a local flooded passage on Vessel** (RN-1..4 ↔ planet-side hydro-station). Travel from the hydro-station to Outer Haven requires an explicitly separate space-transfer edge / escort, not acoustic teleportation. Any remote communication must use a declared relay, not sound through vacuum.

If these are literal terrestrial **dolphins**, they are air-breathing aquatic mammals; stable water, surfacing/oxygen access, habitat history, a reproductive population, food and welfare are required. Dolphins cannot naturally swim at 1,500 km underground or in unpressurized orbital space. Alternative: develop a visibly original **fictional cetacean-descendant civilization** adapted through described engineered habitats. Its specific capability must be justified by **world rules** and clearly fictional, not claimed as science. Sonar through rock/planet-scale distances should be an in-fiction engineered sensor network, not literal biological echolocation.

- **Pod Cohesion 0…5** measures visible *faction trust*, not human psychological traits. Harming a Turned NPC after a warned nonlethal option has a stated trust cost; no secret irreversible moral trap.
- **Echolocation Map** is a time-limited **instrument/sensor reveal** with line-of-sight / relay scope; 3 run ticks; cost 1 faction favor; discloses only game-permitted nodes. Never reads Witness private memory.
- Pod passage ability is subject to trust, habitat and faction negotiation. Its loss **cannot remove the only possible extraction route** unless that danger was telegraphed and another outcome remains playable.
- Shattering the Lattice may damage acoustic relays and complicate relations, but does **not automatically deafen a real animal or delete a human player's evolution**. This is a high-impact fictional consequence to test and communicate.
- `TOK-P-053` Communion begins as a **non-canonical optional epilogue/Severance variant**. Promote to a fourth ending only after independently demonstrating reachable prerequisites and compelling game-play differences, not just extra lore.

## Original brand and protectable expression

Public brand remains working title **The Last Thread** pending trademark/source-rights clearance. New Pod names, symbols, UI sounds, character silhouettes and dialog should be original and reviewed. **Do not erase original authorship, licenses or code provenance to make ownership claims.** Internal TOK IDs are useful to the game engine but need not appear in player UI. The cetacean faction should not copy particular branded dolphin characters or make real-world wildlife/Native cultural or religious claims.

## What a genuinely playable MVP must prove

1. **Core play with AI disabled:** two routes, one objective choice, one tension-building hazard, real spatial counterplay, extraction, and a nonempty result.
2. **No perfect-run treadmill:** returning after failure yields at least one meaningful story/upgrade/relationship change that the player can observe.
3. **Reliable clocks:** `run_tick` resets; `world_tick` never resets; 12/20/25/27/30 stage events occur once, are displayed to players, and preserve 27 contact vs 30 center.
4. **Safety and rules:** malformed or forbidden agent intents result in deterministic fallback. A valid pact cannot bypass mission, faction, permission or resource requirements.
5. **Co-op compatibility:** first server-valid player move advances one tick, not one per simultaneous player; no AI can impersonate a player.
6. **Player comprehension:** give a first-time player one understandable verb within 30 seconds; first nontrivial choice before 90 seconds; 3/5 unaided testers should complete an extraction; measure in a genuine small playtest, not a developer-only test harness.
7. **Accessibility:** no sound-only clues for the Pod; spatial cues have labels; reduced motion; readable cost previews; save/exit mid-run.
8. **Scientific honesty:** no claim that fictional player choices diagnose psychology, expose real sentience, or prove Negarestani's theory-fiction as physical fact.

## References (design lessons, not copies)

- Hunicke/LeBlanc/Zubek, *Mechanics, Dynamics, Aesthetics*: code choices must be tested for actual tension, discovery and player agency, not just counted as features: https://www.cs.northwestern.edu/~hunicke/MDA.pdf
- **Hades** / Supergiant: persistent narrative and progress across runs, meaningful failure: https://www.supergiantgames.com/blog/hades-faq/
- **FragPunk** official Shard Clash update: bounded match-rule modifiers and tradeoffs, **not** copying its cards/art: https://www.fragpunk.com/news/update/20250617/40588_1241063.html
- NOAA, dolphins are air-breathing mammals: https://oceanservice.noaa.gov/facts/dolphin.html
- Dolphin Research Center, biological echolocation is acoustic (not a vacuum signal): https://dolphins.org/dolphin-information/acoustics/

**Decision gate:** Keep this as a design candidate until clock semantics, player experience of a single fun Descent, existing P050–P052 reachability, and exact Pod spatial transport are validated. Existing campaigns and 2–8 multiplayer must stay untouched until protected regression tests and approved integration.
