# Xerodrome Seal v2.0 — integration and spatial audit

**Classification:** Fictional narrative design, **candidate only**.  
**Source:** User-supplied "PATCHED OUTPUT: The Xerodrome Seal — Complete Tokenization & Spatial Map (v2.0)", patches P-01 through P-09.  
**Targets:** [Genesis Soil PR #994](https://github.com/humanaios-ui/operations/pull/994) (five-zone **intro**), [Genesis Soil protocol #922](https://github.com/humanaios-ui/operations/pull/922) (read-only W1, human W2), [Council #921](https://github.com/humanaios-ui/operations/pull/921) (advisory proposals), [Lineage #984](https://github.com/humanaios-ui/operations/pull/984) (persistent identity); do not modify those contracts here.  
**Authority effect:** NONE. **No game-world deployment, model invocation, Azure spend, Discord registration, Seed ratification, or production player changes.**

## What is ready

The patched source provides a **usable campaign content vocabulary**, not yet a validated executable 30-tick world:

- Complete **50-ID typed registry**: eight conceptual anchors (including planet), eight named character archetypes, seven factions, five systems, ten missions, three canonical endings, nine spatial routes.
- A precise **dual-hub story**: Keeper Sanctuary (surface) and Null Ground (orbital + surface cap).
- An event-hazard narrative: growing Black Dawn, collapsing Lattice, Furnace decision, Tether and Exodus horizon.
- Three competing outcomes, **Control / Awakening / Severance**, that make governance and resource dependencies part of fictional choices.
- Motivations, flaws, relationships and role anchors for named **NPCs** and party archetypes.

The v2 manifest in `XERODROME_V2_SOURCE_CANDIDATE.json` retains the supplied contradictions for **visible review**, rather than quietly altering or treating them as resolved. `audit.py` independently evaluates readiness. Passing its unit tests means it **correctly detects known inconsistencies**, not that the narrative can be imported into the live game.

## Major blockers before executable timeline

### X-01 — The Null Ground contact has *two* times

Given the source values, Vessel is `(1,0)` AU, Null Ground is `(2.78,1.95)` AU (heliocentric), shield radius `0.28` AU, front rate `0.09` AU/tick.

- Center distance = **2.640246 AU**.
- First front contact with shield edge = **tick 27** (ceil[(2.640246 − 0.28)/0.09]).
- Front crossing of Null Ground **center** = **tick 30** (ceil[2.640246/0.09]).

**Proposed v2.1 wording:** "Shield contact begins at tick 27; center crossing at tick 30. The shield effect and losing condition remain to be specified." Retain tick 30 as a story deadline only after its precise semantics are selected. The rounded polar position `(3.4 AU, 35°)` is consistent with the Cartesian coordinate at supplied precision.

### X-02 — Black Dawn has two origins

The source says the wave begins at the **Furnace surface projection at azimuth 300°**; the orbital equation centers it on Vessel's **center `(1,0)`**. These are extremely close physically on an AU chart, but are **not exactly equal**. A valid Frame-D to Frame-O transform requires a declared planet radius, surface azimuth reference and orbit epoch.

**Proposed:** Pin a **planet-centered approximation** for *orbital display only*; retain "Furnace at 300°" as lore/spawn source. Resolve the exact projection before deterministic physics.

### X-03 — R-09 joins incompatible spaces

R-09 is called a `space elevator / drill shaft`, but Null Ground orbit is about **2.64 AU from Vessel**. A conventional elevator or shaft is not a contiguous interplanetary link. It also supposedly avoids the Black Dawn front but no physical course or protection is defined.

**Proposed:** Separate **surface cap → near-planet orbital terminal** from a distinct fictional **interplanetary shielded transfer** to Null Ground. This requires a new typed travel edge and a player-visible rule about travel costs; do not treat "tether" as real aerospace engineering.

### X-04 — Missions are not demonstrably reachable

- The OC collector ring is overtaken at tick 2; Inquisitor HQ at tick 3. Both host early missions (especially M-048, required for Control).
- The party begins at FC-3, but no planet-surface → orbital OC route is defined.
- M-049 requires contact with Null Settlers **after** reaching Null Ground, while its task is to secure R-09, a route **to** Null Ground. R-07 could bypass this, but no action-cost budget shows it can happen before tick 25.
- The Lattice fails at tick 12 but M-041 also starts then and is required for Awakening; the exact playable decision window is unclear.
- All movement and quest costs are undefined although **every major action advances the clock**.

**Proposed:** Add a reachability table with start, per-edge tick cost, prerequisite states, travel mode, window open/close, and flags for orbital remote contacts. Use a state-graph solver to establish whether all three endings are actually attainable. Until then **none of the endings is proven reachable**.

### X-05 — Time starts before the supposed decisive Furnace breach

The Black Dawn expands at tick 1; M-042's Furnace breach becomes "irreversible" only at tick 20. The story may mean early pre-breach radiation/front activity, but no state machine currently declares that.

**Proposed:** `PRECURSOR_FRONT` at tick 0–19, `FURNACE_IRREVERSIBLE` from tick 20. The front never depends on a retroactive trigger.

### X-06 — The front is not a traversable route

R-08 is a radial hazard, not an infrastructure edge. Keep it as `dynamic_hazard` with overlap/intersection events; do not include it in pathfinding as a road.

### X-07 — Player agency and the three endings

The supplied endings prescribe deaths, imprisonment and irreversible merging for A–F. Those are **candidate cinematic outcomes**, not compulsory effects on a human user's persistent character. Map A–H to **fictional NPC roles/archetypes**; maintain user-created characters, explicitly approved form changes, and save history separately. Personal lineage is never erased by an ending. Any irreversible character outcome requires a clear, deliberate game choice and rules-approved state transition.

### X-08 — Voice H is not the HumanAIOS Witness

`TOK-CH-H` is a **fictional coercive antagonist/herald**. It may lie, tempt and mislead as narrative. It has no access to real player history or the HumanAIOS read-only Witness memory API. The W1 Witness only describes authorized game events with receipts, expresses uncertainty, does not advise or act. A claim from the Voice becomes **NPC dialogue**, never corroborated evidence just because it appeared in a game log.

### X-09 — Fiction vs research and theology

`TOK-F-026` Solar Temple and any allusion to dualism are **fictional institutions**, not claims about present-day religious followers or real cosmic struggle. Resonance is an in-world scalar, not psychological profiling, biological DNA processing or real human identity. Maintain research OFF unless separately consented and reviewed.

## How the campaign layers attach to PR #994

**Do not replace the five-zone vertical slice with a 30-tick campaign yet.** Treat the existing intro as a playable prologue and Xerodrome as its later world:

| Existing introductory zone | Proposed Xerodrome connection | Engine boundary |
|---|---|---|
| 01 Genesis | Generation Zero first event; offer four *player-chosen* forms. | Timeline starts at user join, not the global 30-tick campaign countdown. |
| 02 Golden Thread | Choose one **introduction**: Ember / Archive / Forge. | These are **not automatically** Control / Awakening / Severance commitments. |
| 03 Witness | W1 recalls the player's events; W2 challenges or affirms. | H Voice remains another actor with zero access to W1's tools. |
| 04 Erasure | Black Corpse lore introduces missing/contested claims. | Unknown does not prove concealment or erasure. |
| 05 Council | Nonbinding proposal about world exploration/governance. | The Council cannot directly write game code or ratify the Seed. |

Only after this prologue might a distinct `XERODROME_CAMPAIGN_STARTED` event initialize the 30-tick mission arc. Keep multi-user co-op arbitration and SCVC continuity under the existing authoritative game backend; the local slice is not a replacement.

## Minimum development stages

**Stage A (this PR):** preserve tokens, detect contradictions with deterministic tests, share corrections for design approval.

**Stage B (not yet implemented):** decide contact vs center deadline; pin one coordinate transform; define early orbital access and travel tick costs; eliminate M-049 circular dependency; model faction/NPC movement, quest windows and player-owned outcomes. Add a solver proving at least one witnessable path to each ending.

**Stage C (not yet implemented):** implement a standalone multi-turn **sandbox campaign** with dynamic hazard overlay, state provenance and three endings, without cloud account requirements.

**Stage D (blocked):** review the live game's editable source, integrate the new world behind opt-in, retain the 33 original checks and first-valid-move arbitration, then stage Azure/Discord after user authorization and cost/credential checks.

## Verification

From repository root:

```sh
cd experiments/wardens-xerodrome
python -m unittest -v test_audit.py
python audit.py              # diagnostic JSON; returns success even if candidate is blocked
python audit.py --strict     # fails while any design blocker remains
```

A green test run validates the **audit**, not the v2.0 world's correctness. The strict audit is expected to **fail** until contradictions are resolved.

**Rule:** *Tokenize what was proposed; calculate what is possible; never confuse the two.*
