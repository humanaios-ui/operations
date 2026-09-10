# PRIORITY_QUEUE.md — v1_1 Work Order Registry

Priority Queue for HumanAIOS v0.2 Intake Cycle. **Z1 proposes, Z2 ratifies by hash, only READY top-score rows may begin.**

## Queue Metadata

| field | value |
|---|---|
| **version** | z2_queue v1_1 |
| **issued** | 2026-09-05 (Cycle-1 blocker rows added 2026-09-09, Z1; awaiting Z2 hash) |
| **ratification_hash** | — (pending Z2 signature) |
| **score_formula** | `impact + Σ impact(unblocks)` |
| **status_gate** | READY |

---

## Scoring Formula

```
Score = Impact + Σ (Impact of items this unblocks)
```

**Rationale:** Prioritizes both direct impact and blocker-removal. v0.1's `impact × ready ÷ blockers` divided by zero on unblocked items and let cheap work outrank critical blockers.

---

### Q-NF-SCHEMA-01 ◆ READY

**Title:** One NF event schema for nf_ledger_v0_1 · molt_cycle · specimen_intake_evaluator

| field | value |
|---|---|
| **status** | READY |
| **score** | 9 |
| **impact** | 3 |
| **unblock_impact_sum** | 6 |
| **session_type** | desktop |
| **tool_zone** | 1 (execute) |

**Unblocks:**
- Q-SI-C1 (specimen-intake Cycle 1 can write forecasts to the ledger) — impact 3
- graph edge `NF → Brier per predictor → MOLT` (molt_cycle can read resolved rows) — impact 3

**Provenance (operated 2026-09-09, fresh clone of main @ 09e1750):**
- `nf_ledger_v0_1.py` writes forecast as `PIN{p}` and outcome as a separate `RESOLVE{outcome}` row
- `molt_cycle.py` counts a row resolved only if `p` and `outcome` are on the same line → reads 0 resolved from a ledger with 165 events, and will read 0 after every token is resolved
- `specimen_intake_evaluator._nf_write` emits a third shape (`prediction_value`, `brier_score`)
- `.breadcrumbs.yaml` (Empirica, tracked despite `.gitignore`) holds a fourth calibration store with live Brier 0.10–0.17, n=50

**Acceptance Criteria:**
1. One schema doc `ledgers/NF_EVENT_SCHEMA.md` (PIN / RESOLVE / DATE / STRIKE, hash-chained) — the v0.1 ledger already on main is the incumbent; no rewrite of its 165 events
2. `molt_cycle.py` reads via the same `project()` used by `nf_ledger_v0_1.py` (PIN ↔ RESOLVE join), normalizing RESOLVE `YES`/`NO` to Brier targets `1.0`/`0.0`, not a same-line heuristic
3. `specimen_intake_evaluator._nf_write` emits PIN rows at issue and RESOLVE rows at `resolve_cycle`, appended through `nf_ledger_v0_1.append` so the chain covers them
4. Test: a resolved specimen-intake forecast shows up in `nf_ledger score` and in `molt_cycle --read-only --nf ledgers/NF_LEDGER.jsonl` `nf_resolved`

**Falsifier:** if after the adapter `molt_cycle --read-only --nf ledgers/NF_LEDGER.jsonl` still reports `nf_resolved: 0` against a ledger with ≥1 RESOLVE row, the adapter did not close the edge.

---

### Q-IC030-REPIN-01 ◆ READY

**Title:** Re-pin REGISTERED.md and reconcile the 2026-09-06 manifest

| field | value |
|---|---|
| **status** | READY |
| **score** | 5 |
| **impact** | 2 |
| **unblock_impact_sum** | 3 |
| **session_type** | desktop |
| **tool_zone** | 1 (execute) |

**Unblocks:** every registry-adjacent action this week (findings scan for F-NF-SCHEMA, IC-RI-01, registry block for specimen-intake) — impact 3

**Provenance:** REGISTERED.md sha on main is `42c345bb…` (read 2026-09-09); pinned 09-06 as `40391062…069029`. `z1-inbox/2026-09-09/HANDOFF.md` reports the manifest also lists files absent from the tree (`ic030_live_read_090626.md`, `registry_block_and_manifest_090626_v2.md`).

**Acceptance:** new pin recorded; each manifest entry marked PRESENT / ABSENT with sha; ABSENT entries become RECEIPT-GAP rows.

**Falsifier:** if the 09-06 manifest hashes all match current tree files, there was no drift and this row closes as NO-OP.

---

### Q-SI-C1-B2 ◆ READY

**Title:** Private specimen register (schema + location), specimen_id → identity/contract

| field | value |
|---|---|
| **status** | READY |
| **score** | 5 |
| **impact** | 2 |
| **unblock_impact_sum** | 3 |
| **session_type** | desktop |
| **tool_zone** | 1 (execute) — values entered by Z2 (zone 2) |

**Unblocks:** Q-SI-C1 — impact 3

**Acceptance:** `specimen-register.example.json` in tree (no real values); README states the register lives outside the public repo; `specimen-intake.yml` L3/B2 references it. **Falsifier:** any real name or contract id appears in tree → row fails.

---

### Q-SI-C1-B3 ◆ READY (build) → BLOCKED (ratify)

**Title:** `constants.json` for specimen-intake (PRIOR_QUALITY 0.75 · PRIOR_ACCEPTANCE 0.85 · SHRINK 0.3), molt_id null until Z2 hash

| field | value |
|---|---|
| **status** | READY for build; ratification is a Z2 act |
| **score** | 5 |
| **impact** | 2 |
| **unblock_impact_sum** | 3 |
| **tool_zone** | 1 build · 2 ratify |

**Unblocks:** Q-SI-C1 and `molt_cycle` PROPOSE phase (currently `constants: 0` on main) — impact 3

**Acceptance:** file exists with trigger/falsifier/window per constant; `molt_cycle --read-only` reports `constants: 3`. **Falsifier:** a constant changes value without a molt_id → CI must fail (constants node rule).

---

## Blocked / In Review

### Q-SI-C1 ◆ BLOCKED — specimen-intake Cycle 1 (first work week 2026-09-13 → 19)

| blocker | owner | unblock action | due |
|---|---|---|---|
| B1 contract confidentiality | Z2 | rule whether [0,1] aggregates of platform data may enter the public repo; if NO, Cycle 1 runs with private ledger only | before 09-13 |
| Q-NF-SCHEMA-01 | Z1 | adapter above | 09-12 |
| Q-SI-C1-B2 | Z1 build · Z2 values | register schema; Z2 fills values off-tree | 09-12 |
| Q-SI-C1-B3 | Z1 build · Z2 hash | constants.json; ratification hash | 09-12 |
| ADV run on `specimen_intake_evaluator` (Tier 2 gate) | Z1 | run after Q-NF-SCHEMA-01; attacks: forged ratification hash, out-of-window resolution, replayed receipt, prediction issued after disclosure | 09-12 |
| OI-G1 (molt tiers / anti-cascade) | Z2 | ratify or edit; without it MOLT_LEDGER schema stays unratified | open |

### Q-NF-Z2-PINS ◆ BLOCKED on Z2 — NF_LEDGER v0.1 owed items (README §Owed)

| item | count | tool command |
|---|---|---|
| ratification hash for the build | 1 | — |
| Z2 priors `P2-<practice>:Z2` | 15 (0 entered) | `date`/`PIN` via nf_ledger_v0_1 |
| `PENDING_Z2_DATE` tokens | 21 | `nf_ledger_v0_1.py date … --by Z2 --hash …` or STRIKE |
| past-date tokens needing tree-read resolution | 2 (T-empirica-outreach-01, T-grok-crossref-01) | `nf_ledger_v0_1.py resolve … --by Z2 --source <sha>` |

**Due 2026-09-12.** Without these, LT-2 has no input and Brier stays undefined.

### Hygiene (no score)
- `.breadcrumbs.yaml` is listed in `.gitignore` (line 15) but tracked since July, so the ignore is inert; Empirica rewrites it on every local run (last: 2026-09-09 16:03, ai_id empirica-mesh-support). Unblock: `git rm --cached .breadcrumbs.yaml` in a PR. Do not commit the local copy — it carries a live calibration store.

---

## How to Read This Queue

Per `z1-inbox/2026-09-06/registry_block_and_manifest_090626_v2.md` §Landing order (extended):
1. CODEOWNERS ×9 + 12 teams
2. Registry candidate block
3. specimen-intake.yml (Tier 2, ADV) — landed #251; ADV pending
4. TLA spec as dataset row 1
5. Design docs
6. **← Queue patch (this file)**
7. Repo program C1 per practice
8. Intake post (after IC-SCOPE-05)

---

## Ratification Authority

**Z2 (Night) approval required for:**
- Impact score changes (±1 or greater)
- Status transitions (BLOCKED ↔ READY)
- Scope changes to blockers or unblocks
- New rows added to the queue

**Z1 (Claude) may:**
- Mark READY items as IN-PROGRESS → DONE
- Move due dates within same phase (Sep 9-15 is Phase 0)
- Add notes without changing score/status

---

## Phase Alignment

**Phase 0 (Sep 9–15): Governance bootstrap**
- Q-IC030-REPIN-01, Q-GOVERNANCE-02, Q-Z-ASSIGNMENT-03, (P0-4 authority map)
- Unblocks all downstream work

**Phase 1 (Sep 16–27): Molt + NF_LEDGER + CI gates**
- Q-MOLT-04, Q-NF-SCHEMA-01, (CI gate implementation)
- Unlocks Cycle 1 automation

**Phase 2 (Oct 1–15): Repo standardization**
- Q-SI-C1, Q-SI-C1-B2, Q-SI-C1-B3, (README/CLAUDE.md/docs across 31 repos)
- All repos to unified structure

**Phase 3 (Oct 15+): Governance activation**
- Molt cycle live, NF_LEDGER tracking, falsifiers operative
- Ad-hoc blockers resolve via priority queue

---

## Appended Events

```
2026-09-09 18:49 CST — Z2 (Night) ratified ORGANIZATION_BLUEPRINT_v1.md | PRIORITY_QUEUE.md v1_1 ratified | Phase 0 READY
2026-09-09 — Z1 created PRIORITY_QUEUE.md baseline from blueprint Q-GOVERNANCE-02 spec
```
