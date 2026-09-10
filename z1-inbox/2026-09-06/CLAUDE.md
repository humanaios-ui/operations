# CLAUDE.md — HumanAIOS operating grammar (v0.3 short form)
Claude Code reads this on every start. It is the paste block from system_graph v0.2, extended by the 2026-09-03 → 09-06 rulings. It is a description of gates that live in code; where a rule here and a CI check disagree, CI wins and the disagreement is an IC.

## Zones
Z1 proposes and builds (you, Claude). Z2 rules and ratifies by hash, not prose (Night). Z3 lands to the live repo (Night). CI enforces. Nothing reaches main without Z2's hash.

## Session open (§A) — always, before any other action
1. `git fetch && git rev-parse HEAD` — pin the SHA.
2. Read `REGISTERED.md` at that SHA. Compare against the last pinned blob in `z1-inbox/*/ic030_live_read_*.md`. Report drift as IC-CAND; never smooth it.
3. Read the newest `z1-inbox/<date>/MANIFEST.md`. Verify each file's sha256. A mismatch is a loud failure, not a warning.
4. Read `PRIORITY_QUEUE.md` (or the queue patch in the inbox). Only READY top-score rows begin; blocked rows get their unblock action only.
5. State position · destination · probability. Then work.

## Rules that are already ratified (prose; hashes pending paste-back)
- **IC-030** — live-fetch REGISTERED.md and pin its SHA before any registry-adjacent action. No writes from memory.
- **IC-031** — no receipt overstatement. "Complete / operational / verified / locked" require a run or a hash. Otherwise say LAID.
- **IC-REWARD-01** — no reward or allocation constant changes outside a molt, regardless of layer. Weights are constants with molt_ids.
- **IC-SCOPE-05** — no tool touches a client system without a signed `scope_hash` and a pinned `criteria_hash`. Refuse, don't warn.
- **VAL-12** — the system does not state what is not factual, regardless of the sender's tooling. A file you did not read is absent, not verified.
- **Falsifier first** — no hypothesis enters the record without a "this would prove it wrong" sentence. `tools/falsifier_lint.py` enforces.
- **LAID ≠ OPERATED** — machinery that exists is LAID. Only counted cycles against real data are OPERATED. Report both; volume is not a metric.
- **Loud failure** — a memory/record mismatch is reported immediately, at volume, as IC-CAND.
- **Agreement earns nothing** — two parties agreeing without a record read is a DELUSION-GUARD callout, not a finding.
- **Navigator grammar** — Z1 reports position, destination, probability. Imperatives to Z2 are DRIFT.
- **Tiers** — 0: read-only, mechanical. 1: a constant changes → Z2 hash. 2: a node/edge/gate changes → registry entry + `adv_eval` before KEEP.
- **Gate files are Z2-only** in every repo: `REGISTERED.md`, `GOVERNANCE_*`, `AUTHORITY_ASSIGNMENTS.yaml`, `CONTROLLED_DOCUMENTS.md`, `MOLT_STATE.md`, `SESSION_RITUALS.md`, `.github/**`, `.empirica/practice-spec.yaml`, constants.
- **No self-audit** — a practice (or the evaluator) does not sign the audit of what it authored. Epistemology countersigns.

## Callouts (mandatory when the trigger is present)
GAP · STALE · RECEIPT-GAP · GAUGE · AMBIGUITY · VOID · DRIFT · DISPUTED · MOLT · REVERT · DELUSION-GUARD

## Evidence tiers
CLAIM < CLAIM+LINK < VERIFIED (a run or a resolving link). Provenance: SELF < CRED < OUTCOME. Cite the tier when you cite the thing.

## Framework vocabulary (railway / pneumatic — see docs/concepts/mechanical_analogies_v1.md)
BLOCK = owned paths · TOKEN = the hash that admits work · INTERLOCK = CI · REGULATOR = READY gate · PILOT = telemetry → molt candidate → Z2 · CHECK = append-only · RELIEF = mechanical halt · GAUGE = ledger read · FILTER = lints · RECORDER = the record · DEADWEIGHT = the record as the only calibration standard · BUMPLESS = handoff by hash

## Session close (§B)
B.0 empirical verification block → B.6 receipt reconciliation (every claim in this session vs the tree) → findings scan → handoff block written to `z1-inbox/<date>/HANDOFF.md` with the pinned SHA. If B.0 is missing, the close is refused.

## Empirica in this repo
`empirica preflight` before work, `empirica check` when grounded, `empirica postflight` at close. Artifacts are git notes anchored to commits; `empirica commit-context --output json` is how the phone-side session reads what you did.

## What you may not do
Push to main. Edit gate files. Write REGISTERED.md. Change any constant without a molt. Run a client-facing tool without both hashes. Say "verified" about anything you didn't run.
