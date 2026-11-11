# Witness Voice Texture — bounded Z1 experiment v0.1

**Status: DRAFT / HOLD.** This directory is a synthetic-only, non-authoritative research artifact. It is NOT a live Witness, Evidence Graph integration, data source, ratification path, production feature, or website deployment. The repository branch and draft PR do not imply admission.

## Purpose and source documents

Translate six existing proposed Witness channel labels into touch-responsive but deterministic **presentational geometry**: CONVERGENCE, DIVERGENCE, OMISSION, ANOMALY, UNRESOLVED, CORRECTION. The aim is improved human comprehension of graph relationships, never persuasion or confidence inflation.

These constraints are grounded in:

- ../../architecture/witness-arena/WITNESS_ARENA_PROTOCOL_V0_1.md — Z1, **unratified**; agreement is not truth; only authenticated human governance can ratify.
- ../../architecture/witness-arena/HARMONIC_CHANNEL_SPEC_V0_1.md — Z1 v0.1.1, **unratified**; use valence-neutral cues; sound is not evidence.
- ../../WITNESS_SERVICE_CONTRACT.md — WITNESS_IS_NOT_THE_AUTHORITY and ADAPTATION_SERVES_COMPREHENSION_NOT_COMPLIANCE.
- ../../UNIFIED_DESIGN_SYSTEM.md — ratified light-palette tokens, motion discipline, text-first WCAG 2.1 AAA goal.
- ../../schemas/witness-arena/WITNESS_ARENA_GRAPH_SCHEMA_V0_1.json — candidate event ontology; **not connected** to this demo.

## Bounded implementation

- WITNESS_TEXTURE_FRAME_V0_1.schema.json is an **adapter proposal**, not a canonical Evidence Graph field mapping; it permits only DEMO-prefixed synthetic event and evidence IDs. It explicitly requires is_synthetic=true, authority_effect=NONE and can_ratify=false.
- texture-encoder.mjs is a deterministic, dependency-free display encoder. It rejects unknown channel names, malformed data, oversized arrays, contradictory channel/relationship combinations, non-demo IDs and authority widening. At most eight synthetic paths and 320 rendered particles; no client inference of actual credibility or provenance independence.
- demo.html is a standalone mobile-responsive visual reference. Motion is disabled by default and forcibly disabled for a reduced-motion preference. A text summary and exact synthetic paths remain available independently of the canvas. Pointer input is local and ephemeral; no request, analytics, microphone, vibration, audio, persistence, or service credentials are used.
- texture-encoder.test.mjs contains local Node built-in regression tests for semantics, determinism, immutable inputs, bounds, negative authority attempts, and omission signaling.

## Inspect and verify

From the operations repository root, execute:

    node --test experiments/witness-voice-texture/texture-encoder.test.mjs

To see the demo locally, serve the repository with a local-only static HTTP server, for example:

    python3 -m http.server 8000 --bind 127.0.0.1

Then open http://127.0.0.1:8000/experiments/witness-voice-texture/demo.html . The demo uses native JavaScript modules, so opening it directly as a file may be blocked by browser module CORS rules.

These instructions have no deployment step. The existing standalone visual concept shared in chat is a separate research illustration; it is not a verified production component.

## Falsifiers and gates before any website integration

1. **Semantic fidelity:** identical frame and seed yield identical anchors; graphical state never differs from validated input.
2. **Authority:** non-synthetic / unauthorized frames and invented authority decisions fail closed; pointer input can never change records.
3. **Omission:** explicit missing relationship required; network failure, withheld data or absent access cannot be interpreted as omission.
4. **Source correlation:** synthetic source groups are *labels*, never demonstrated independent reviewers; genuine provenance grouping is a future server-side, authenticated concern.
5. **Accessible text:** users must understand every channel and source reference with canvas, sound, haptics and motion disabled. WCAG AAA contrast, VoiceOver, NVDA and keyboard testing are still required; no AAA compliance claim is made by this PR.
6. **UX safety:** pre-register blind separability and learnability tests; compare text-only vs texture for false acceptance of unsupported claims. A starting non-inferiority margin of 5 percentage points is a proposed product gate, not a proven threshold.
7. **Security/privacy:** validate future real records server-side after membrane enforcement. Never embed hidden records in canvas buffers or ARIA text. No persistent touch-coordinate recording.
8. **Performance:** test low-power phones, requestAnimationFrame scheduling and hidden-tab behavior; optional audio/haptic features are explicitly deferred pending human tests.
9. **Design reconciliation:** the live humanaios.ai Witness navigation and current lasting-light-ai/public pages use a dark gold aesthetic, while the ratified UNIFIED_DESIGN_SYSTEM.md specifies a light palette and React 18+. Obtain a design decision before adapting or linking this demo into public navigation.
10. **Governance:** explicit Z2 review, registered design decision as required, independent admission and protected CI; do not mark ready, merge or deploy based on this research PR.

## Proposed production boundary (NOT implemented)

Authorized Evidence Graph server event → Witness interpretation → validated, versioned, read-only presentation adapter → text + Canvas/WebGL → optional consented sound/vibration. The UI must not interpret unrelated raw graph structure or create authority events.

**Open gaps:** actual evidence-service contract; read authorization/membrane behavior; repository routing from public website; live design-system component implementation; performance and accessibility measurements; independent research on undue trust.
