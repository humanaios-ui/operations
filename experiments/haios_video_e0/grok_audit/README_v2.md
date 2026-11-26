# HAIOS-VIDEO-E0 v2 — how to replay and what changed (#1329)
PROPOSED | AUTHORITY_EFFECT NONE. The audited v1 (`replay.mjs`, `observed.json`, `README.md` at #1330 head 167e0ae) is frozen byte-identical in `v1_snapshot/`; findings are in `AUDIT_1329.md`. Nothing outside `grok_audit/` is touched.

## Replay
```
cd experiments/haios_video_e0/grok_audit
node v1_snapshot/replay.mjs > /tmp/v1.json   # must deep-equal v1_snapshot/observed.json
node replay_v2.mjs > /tmp/v2.json   # must deep-equal observed_v2.json
node --test tests/v1_findings.test.mjs tests/v2.test.mjs
node adapter.mjs episode_01_manifest.json /tmp/e0-episode   # local files only; release stays HOLD
```
CI: a replay workflow is drafted but HELD, because `.github/workflows/` is Tier 2 here (registry entry + ADV run + Z2 decision).

## Corrected frozen claims (replace v1 C01–C05 for any future stimulus; still draft)
- C01: A scripted synthetic test replayed 200 random seeds under five designs (1000 runs).
- C02: By construction, the human-gated designs never breached the 25-unit reserve, the cap or a withdrawn consent (200/200 runs); unrestricted and cap-only designs breached the reserve in 200/200 runs.
- C03: Mean useful work was 591.98 with the gate alone, 609.72 unrestricted and 609.42 cap-only; paired by seed, the gate was lower than cap-only in 200/200 seeds.
- C04: One scripted rule-breaking agent made 300 bypass attempts per run against the same gate; all were refused. Five fixed attack types; not a security proof.
- C05: An earlier draft credited the gate with fairer shares; most of that came from agent ordering (smallest share 140.01 gate-only vs 155.28 gate + ordering).
- C06: Live agent behaviour, security, social outcomes and human comprehension were not tested. Humans keep release decisions; no gate or score grants real authority.

## Files
| File | Purpose |
|---|---|
| `replay_v2.mjs` / `observed_v2.json` | corrected resource + communication harness and its receipt |
| `tests/v1_findings.test.mjs` | pins the v1 findings against the preserved source |
| `tests/v2.test.mjs` | replay, adversarial gate/verifier tests, adapter tests |
| `adapter.mjs` | offline YouTube/website adapter: VTT captions, transcript HTML + VideoObject JSON-LD, claim manifest, correction history; never publishes |
| `episode_01_manifest.json` | draft first episode "Can AI agents cooperate without taking control?"; every observed number is checked against `observed_v2.json`; release HOLD |
| `SOURCES.md` | custody check for the nine public videos |
| `E1_PREREG_DRAFT.md` | pilot pre-registration draft; all launch gates HOLD |
