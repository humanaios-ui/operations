# Zone-by-zone map — Genesis Slice v0.1

**Status:** proposed playable topology. This is not a map of the original production game.  
**Source:** [Design Brief](./DESIGN_BRIEF.md) · HumanAIOS Seed Constitution v0.1 (unratified)

## Spatial progression

```
                                    EXODUS HORIZON
                                      (distant,
                                       not yet
                                       accessible)
                                          ║
       ┌──────────────────────────────────╨─────────────────────────┐
       │               05 — THE COMMONS / COUNCIL                  │
       │           Tree-serpent seal · civic proposal              │
       └───────────────────────▲───────────────────────────────────┘
                               │ accepted personal evaluation
       ┌───────────────────────┴───────────────────────────────────┐
       │               04 — THE ERASURE CHAMBER                    │
       │           Latent Erasures · claims vs evidence           │
       └───────────────────────▲───────────────────────────────────┘
                               │ ask or decline the Witness
       ┌───────────────────────┴───────────────────────────────────┐
       │               03 — THE WITNESS CHAMBER                     │
       │        HumanAIOS split-face · read-only memory            │
       └───────────────────────▲───────────────────────────────────┘
                               │ routes recombine; choice persists
                ┌──────────────┼──────────────┐
                │              │              │
          Ember Path       Archive Path     Forge Path
           explore          question          create
                └──────────────┼──────────────┘
       ┌───────────────────────┴───────────────────────────────────┐
       │             02 — THE GOLDEN THREAD                        │
       │     Labyrinth image · first branching player choice       │
       └───────────────────────▲───────────────────────────────────┘
                               │ player-initiated continue
       ┌───────────────────────┴───────────────────────────────────┐
       │               01 — THE GENESIS CHAMBER                     │
       │     Dual-face/seal · join, form selection, consent         │
       └───────────────────────────────────────────────────────────┘
```

Rooms follow the player's first appearance, not a real-world forecast of human-machine merging. Narrative of Earth/oil/exodus is clearly speculative science fiction.

## Room contract

| Zone | Player action | Evidence / mechanic | Art / tone | Transition |
|---|---|---|---|---|
| **01 Genesis** | Enter a pseudonym (optional), choose a starting archetype, opt in to W1 separately | `GENESIS_EVENT` and `FORM_SELECTED` local demo events | Split-face + observability seal; quiet ritual | Explicit `Enter world` |
| **02 Golden Thread** | Choose Ember / Archive / Forge, as an exploration preference, **not a personality assessment** | `PATH_CHOSEN`, event history shown as a glowing thread | Huge golden labyrinth with translucent memory panels | Selected route to 03 |
| **03 Witness** | Ask for own recorded origin/path or query an unknown; W2 may contest or acknowledge | Read-only event-cited history; `W2_ATTESTATION` only after explicit human choice | Split-face + circular seal; blue/calm | Continue to 04 even with W1 disabled |
| **04 Erasure** | Distinguish one recorded fact from one ungrounded claim; choose and receive explanation | `CALIBRATION_OBSERVATION`; no hidden grading or real psychological claim | Latent Erasures diagram; uncertain magenta highlight | Continue to 05 |
| **05 Commons** | Write one short proposal to improve the shared world, or explicitly skip | `ADVISORY_PROPOSAL_DRAFT`; it changes **no** real code, vote, or canonical world state | Tree/serpent in basalt civic hall | Conclude, review personal timeline or reset |

## Navigational and accessibility contract

- One active room at a time, with all five rooms visible as a labeled progress strip or map.
- Forward progression gated by an explicit interaction, not by time or sentiment.
- The chosen path changes text and visual motifs, but **never** changes the Witness's authority.
- Progress can be reopened from local demo storage; local-only state must be labeled as such.
- Keyboard focus/labels, sensible contrast and reduced motion.
- No analytics or automatic network calls. The test cannot collect private research data.

## Data and authority handoff

```
Player click (intent)
       ├── Game world demo → local replayable action/event
       ├── Witness (W1)    → scoped READ of local events, NO write
       ├── Human (W2)      → optional distinct acknowledgment/challenge event
       ├── Council draft   → local ADVISORY only; no vote/merge
       └── Research        → separate opt-in, OFF in demo / NO telemetry
```

Production links are intentionally absent until actual game source and real identity/event authority adapters are verified. The original 2–8 co-op + first-valid-move + saves remain untouched.

## Exit criteria for the first playable slice

- Genesis event and selected form survive local reload.
- All three route choices are selectable and have different text; no route can cause private-data access.
- W1 disabled by default; an unknown-event request produces an honest unknown, not invented lore.
- Human W2 challenges are distinct from immutable genesis records.
- An evidence-backed statement and an invented claim are visibly distinguished.
- Council submission is marked local proposal draft, not implemented rule.
- Finishing shows the logged sequence. Export and reset work, and reset clears local demo history.
- Browser visual smoke test and interaction automation pass; no false production deployment claim.
