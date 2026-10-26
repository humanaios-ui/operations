# Game vNext — R1 repair and R2 AI-off tactical mission

**Review-only research artifact:** base game vNext charter [#1020](https://github.com/humanaios-ui/operations/issues/1020). The original hosted 2–8 player game is unchanged; the new prototypes have **no Azure, Discord, human identity or LLM access**.

1. **R1**: `WORLD_RULES_FREEZE.md` pins the proposed prototype semantics. `solo/` is a repaired import of archived PR #1017, not a merge of the old PR. Its repaired source includes 0-supply recovery, cost-aware actions, adjacency-only map styling and a regenerated offline bundle.
2. **R2**: `descent/` is one complete local mission M045, The Sounding, built to run with no AI. Two routes, a Dawn choice, one scripted faction encounter, optional objective, attention/resonance and extraction. R2 does not settle into world time automatically.

## Run

- Solo campaign: `python solo/build_standalone.py`, open `solo/PLAY_OFFLINE.html` in browser; or serve the modular source over local HTTP.
- R2: open `descent/PLAY_OFFLINE.html` after `python descent/build_standalone.py`, or serve `descent/index.html` over HTTP.
- Tests: `node --test solo/tests/engine.test.mjs descent/tests/engine.test.mjs`; then `python solo/build_standalone.py` and `python descent/build_standalone.py`.

## Explicit launch limits

A green logic/CI run does **not** prove fun, accessibility, real Chromium/mobile/browser support, availability of the protected hosted game source, persistent player Witness, co-op 2–8 behavior, or Azure deployment. These remain gated by #1020 R3–R6 and the separate #920/#915 infrastructure tracks.
