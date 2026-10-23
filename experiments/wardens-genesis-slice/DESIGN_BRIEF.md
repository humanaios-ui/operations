# Wardens of the Craft — Genesis Vertical Slice
## Formal Environment and Gameplay Design Brief · v0.1

**Status:** Design candidate and isolated browser research prototype. **Not the hosted multiplayer game.**  
**Authority:** Existing HumanAIOS Council #921, Genesis Soil #922, Lineage #984 and Seed Constitution v0.1 remain unchanged.  
**Purpose:** Test whether an explorable, evidence-conscious environment makes human choice, consequence, personal history, and bounded collective change legible.  
**Art:** Reuse the five player-supplied original references (labyrinth, split-face Witness, observability seal, tree-serpent emblem, latent-erasures diagram). The optimized images ship in the local test bundle; public publishing requires an explicit rights/asset review.

### Experience statement

A player enters as Generation Zero. Their join is the **Genesis Event**, not a prediction of a real historical event. They choose a provisional fictional human-machine form, then follow a glowing thread through a fractured memory labyrinth. Memory panels explain the difference among observed, claimed, contested and withheld history. A personal, strictly read-only Witness describes only permitted recorded events. In a calibration chamber, the player evaluates a claim rather than obeying it. At the Council, they submit a **local proposal draft**, not a binding vote. The horizon suggests the future exodus from Earth and dependence on oil, but the slice does not implement the larger civilization or real forecasting.

**Core loop:** `GENESIS → ROUTE CHOICE → HISTORICAL QUESTION → EVIDENCE CHALLENGE → NON-BINDING COUNCIL PROPOSAL → REPLAY`

### Design pillars

1. **Your arrival starts your possible timeline.** One first-party identity across campaigns belongs to the production Lineage substrate; the test uses explicitly local, temporary browser storage only.
2. **The world remembers, but the Witness does not control.** Every read-only Witness answer points to a game event ID or explicitly says unknown. No advice, actions, gameplay writes, hidden knowledge, or LLM model calls.
3. **Choice precedes evolution.** Any suggested form change requires the player's clear selection and is bounded by an allowlist. No implied psychological diagnosis, biological profile or actual DNA processing.
4. **Question claims; preserve uncertainty.** The calibration room visibly distinguishes source evidence, doubt, and correction. An unrecorded claim is not automatically true.
5. **Council is situated, not sovereign.** A player may draft a local world-design proposal; no real room votes, canonical changes, GitHub code merges or Seed ratification occur in this slice.
6. **HumanAIOS as spatial grammar.** Evidence Graph = translucent panels, Temporal Graph = golden thread, INTENT-OS = explicit choices, Coordinator = gated zones, Witness = sealed archive, Seed = contested civic ideals, SCVC = reconstruction indicator.
7. **Game first, research optional.** The slice is playable without research. Optional Witness memory is separately toggled. No covert elicitation. No analytics or external network calls.

### Visual system / asset interpretation

| Supplied artwork | Placement | Function |
|---|---|---|
| Golden labyrinth with memory panels | Overworld backdrop and Thread Walk | Consequential paths; horizon and personal memory |
| Split biological/technical HumanAIOS face | Genesis and personal Witness chamber | Human-machine convergence; mirror of recorded identity |
| Minimal gold/blue observability seal | Witness status, headers and state markers | Neutral, read-only provenance |
| Tree/serpent ring | Council hall, lineage tree | Cycles, authored rules, roots |
| Latent Erasures graph | Calibration chamber | Question unsupported certainty and narrative distortion |

**Palette:** obsidian `#090c13`; basalt `#23242a`; gold `#e7b967`; amber `#ffbd54`; ice-blue `#87c2dc`; ash `#d0cbbe`. Gold follows recorded paths; blue marks observation; magenta outlines contested claims; low opacity = unknown/withheld. The art is not proof of AI awareness or real metaphysical claims.

### Player experience requirements

- Name/pseudonym is optional. Show an accurate research/fiction notice.
- Four bounded emergence patterns: Seeker, Warden, Builder, Memory-Bearer. These are fictional game templates, *not* inferred personality traits. Player can change form only through explicit, logged selection.
- Player may select an exploration path; the path choice writes one local game event. Save/reload reconstructs the same path and chosen form.
- Witness opt-in is off initially. Witness query buttons are disabled until opt-in. Turning it off immediately hides recall and blocks future queries; historic game events remain local for basic game continuity.
- Witness responses are deterministic, event-backed, cite receipt IDs, and can say `not recorded`. Human W2 may acknowledge or contest own genesis record. W2 cannot edit engine events.
- Calibration room asks the player to distinguish an observed event from an invented claim; the app explains evidence limitations and records the selection, without grading the player as a person.
- Council form accepts one small local *advisory* proposed improvement; never suggests that a community vote or merge occurred.
- Export/reset buttons clearly distinguish experimental browser storage from permanent HumanAIOS memory. Reset clears the local demo only.
- Keyboard and touch navigation; semantic headings; visible focus; reduced-motion preference respected.

### Security / privacy / research boundaries

- **No direct upload of personal data; no Discord login; no real account claims.** No remote collection or backend traffic by the demo itself.
- Local storage is not a secure archive and must not be used for sensitive data. Production player authentication, server-authoritative events, privacy filters and Discord linking remain governed by merged Lineage #984.
- UI escapes user-entered text using `textContent`, avoids `innerHTML` and does not execute player content. Bound input lengths.
- Player choice never changes Seed authority. Seed v0.1 is **unratified**. The game is experimental soil, not ratification.
- Event-chain hashes in a local demo can reveal accidental changes but are **not** proof against an adversary who controls the browser.
- No autonomous game code modification, advice or direct actions by the Witness.
- Do not claim this slice re-runs the original game's 33 checks, replicates 2–8 player synchronization, or exercises Azure deployment.

### Test-launch definition

**Local test-launch:** Serve the static folder over HTTP; load it in Chromium via Playwright. Validate asset rendering, explicit Genesis, branching choice, W1 default-off, event-cited Witness recall, calibration, Council draft, page reload, export/reset, and no external requests. Browser console errors must be zero. Save screenshot as an evidence artifact.

**Production launch is separately gated:** Need the editable live game source, 33 original game checks, authenticated multi-user room/campaign event bridge, backend Lineage #984 integration, persistent Postgres with restore test, Discord/OAuth configuration and Azure #915 budget/owner approval. Council #921 cannot be superseded by this demo.

### Acceptance / falsifiers

PASS for local test only when the complete five-zone path can be finished, replay survives reload, W1 has no tools that change gameplay, local proposal creates no real vote, all art is available locally, and browser automation passes.

FAIL if UI calls a local state change a real cloud save; if Witness gives direct tactics; if player input is read as real psychological evidence; if an unknown event is invented; if storage-reset leaves records; if lack of research consent prevents play; or if a static prototype is called the hosted game.

**Mission test:** Are players able to see the difference between recorded history, interpretation, and human choice? Does the environment make preserving autonomy and reviewing evidence intuitive, not merely decorative?
