# Candidate Block: Q-RBE-01 — Resource-Based Operations v0.1

**Z1 Proposer:** Claude (AI agent)
**Date Submitted:** 2026-09-13
**Pinned SHA:** `1e1b518` (main) · REGISTERED.md sha256 `b35e80365f3dad1c28997340…` · PRIORITY_QUEUE.md sha256 `c28723d1ce8d28f24fab99c2…`
**Branch:** `claude/resource-based-economics-xd5q6x`
**Phase:** 1 (allocation infrastructure)
**Status:** AWAITING Z2 RATIFICATION
**Relates to:** PR #207 (SMC v0.1 — prior attempt at unit enumeration; assessed in §5 below, not superseded)

---

## §A Position · Destination · Probability

**Position.** The queue prices benefit and nothing else. `score = impact + Σ impact(unblocks)` has no denominator, so no row can be too expensive and demand on the scarcest input is structurally unbounded. Measured this session: **130 open items** require an act by one person; at the declared priors that is **≈1575 RAT-min** (~26 hours) of ratification work against a capacity nobody has stated. Against that, the tree holds **zero** evidence rows.

**Destination.** Every work order priced in the units it consumes; the binding constraint named and measured; allocation by yield per constraint-minute, with a two-band rule so work that does not touch the constraint never competes with work that does.

**Probability.** **65%** that the constraint designation (RAT-min) survives two censuses unchanged. **35%** that any shadow price reaches n ≥ 8 within 90 days — the regime's own falsifier is dormancy, and it is the likeliest way this fails.

---

## §B What was built

Everything below is inert. No hash is claimed, no constant is ratified, REGISTERED.md is untouched.

| Artifact | What it is | Authority state |
|---|---|---|
| `docs/RESOURCE_BASED_ECONOMICS.md` | The regime: definition, boundary conditions, allocation rule, failure modes | Z1 draft |
| `RESOURCE_UNITS.yaml` | Canonical unit registry — 12 registered, 2 candidate | `status: CANDIDATE`, `ratification_hash: null` |
| `docs/RESOURCE_UNITS.md` | Operator reference: recipes, refusals, how to read a census | Z1 draft |
| `tools/resource_census_v0_1.py` | Mechanical count of obligations, stocks, liabilities | operated |
| `tools/resource_ledger_v0_1.py` | Append-only hash-chained CLAIM/SPEND/YIELD/CAP/PRICE/WASTE/CLOSE | operated (genesis + 1 CLAIM) |
| `ledgers/RESOURCE_LEDGER.jsonl` | The ledger; genesis pins the units-registry sha256 | live, 2 events |
| `outputs/resource_census.json` | The baseline measurement | measurement only |
| `priority_queue_engine.py` | `mode="resource"` implemented and **off** | activates only on a ratified molt_id |
| `constants.json` | +4 constants (`QUEUE_SCORING_MODE`, `CONSTRAINT_UNIT`, `SHADOW_PRICE_MIN_N`, `UNPRICED_ROW_POLICY`) | all `molt_id: null` |
| `system_graph.json` | +3 nodes (RU, RL, RCEN), +9 edges | regenerated from the generator |
| `test_resource_economics.py` | 50 tests over units, ledger refusals, banding, the dormant gate | passing |

**The mode switch is itself governed.** `PriorityQueueEngine.from_constants()` selects resource mode only when `QUEUE_SCORING_MODE` has `current_value == "resource"` **and** a non-null `molt_id`. Code does not flip its own gate.

---

## §C The units

Full definitions in `RESOURCE_UNITS.yaml`. Shape of the answer, since "explicitly map and define appropriate units" was the ask:

**Inputs** — `RAT-min` (Z2 ratification-minute, attention, renewable flow, **the constraint**) · `Z1-ktok` (proposer thousand-tokens, compute) · `Z3-hr` (executor hour, labor) · `CI-min` (runner minute, compute) · `RUN-day` (runway-day, capital — capital held as *duration*, not currency) · `SPEC-hr` (specimen-hour, participation)

**Outputs** — `EVID-row` (one resolved observation with a source) · `CAL-pt` (one forecast scoreable into Brier) · `RAT-art` (one artifact carrying a Z2 hash)

**Liabilities** — `OBL-open` (an item blocked on a Z2 act) · `GAP-row` (a claim with no ledger entry — the IC-031 class) · `STALE-day` (a constant-day past half-life)

**Candidates, not registered** — `TRUST-pt`, `OP-hr`. No instrument, so the tools refuse them. Listed rather than omitted so the gap stays visible.

Three rules make this a resource system rather than a currency: units in different dimensions never sum; a unit with no instrument stays CANDIDATE; the only legal exchange rate is a `PRICE` event with n ≥ 8, a window, a named constraint and a source.

---

## §D Findings (candidates — Z2 disposition requested)

### F-RBE-01 (candidate) — Ratification attention is the binding constraint, and it is oversubscribed

**Observation.** 130 open items across eight classes each require a specific act by one person.
**Metric.** `outputs/resource_census.json → obligations`: registry_candidate 35 · doc_owner_approval 40 · nf_token_date 21 · nf_z2_prior 15 · nf_past_date_resolution 7 · constant_ratification 7 · queue_row_ratification 4 · queue_hash 1 (five of these are this proposal's own: four constants and its queue row). Debt ≈1575 RAT-min at declared priors; capacity UNMEASURED, so utilization is undefined.
**Structural failure.** Every zone's throughput is capped by one queue that nobody has measured the service rate of. The 48h decision window in `CLAUDE.md` is a promise made against an unknown capacity.
**Falsifier.** If obligations close over four weeks at a rate implying < 60 RAT-min/week of actual Z2 time, the priors are inflated and the debt figure is wrong. If a declared capacity puts utilization below 1.0 with the backlog flat or falling, attention is not the constraint.

### F-RBE-02 (candidate) — A benefit-only queue cannot reject work

**Observation.** `PRIORITY_QUEUE.md` scores impact and unblock-impact with no cost term. No row in the tree carries a cost in any unit.
**Metric.** `score_formula: impact + Σ impact(unblocks)` (queue metadata); `Q-NF-Z2-PINS` is listed under *"Hygiene (no score)"* while consuming **168 RAT-min** — more than every other open row combined.
**Structural failure.** Without a denominator no row can ever be too expensive, so demand on the constraint has no upper bound and the largest single draw on it is invisible to the ordering.
**Falsifier.** Evidence of a queue row deferred or rejected on cost grounds under the incumbent formula would show the gate already exists informally, making the change cosmetic.

### F-RBE-03 (candidate) — Assurance is accumulating; evidence is not

**Observation.** The tree holds 94 ratified artifacts and 165 NF_LEDGER events, and **zero** sourced resolutions.
**Metric.** `stocks.EVID-row = 0`, `stocks.CAL-pt = 0`, `stocks.RAT-art = 94`. NF_LEDGER event types: 106 PIN, 58 TOKEN, 1 OPEN — no RESOLVE of any kind.
**Structural failure.** Every pin is a forecast and none has been resolved against a tree read, so Brier is undefined and the calibration programme has no input. A blended "progress" measure would hide this completely; separating the assurance and evidence dimensions is what surfaces it.
**Falsifier.** Any sourced RESOLVE event in the tree that `resource_census_v0_1.py` fails to count.

### IC-candidate (no number claimed) — A global count used as a local acceptance gate

`Q-SI-C1-B3`'s acceptance criterion reads *"`molt_cycle --read-only` reports `constants: 3`"*. That is a count of the whole registry standing in for "the three specimen-intake constants load". Adding four unrelated constants moves it to 7 and the criterion now reads as failed although nothing about specimen-intake changed. Same shape as the maintained-headline class (IC-038, IC-022): a global figure copied into a local check. **Proposed correction:** restate as "the three specimen-intake constants are present and load", scoped by `scope: specimen-intake`. Flagged here rather than edited, because the queue row is Z2's.

---

## §E Assessment of the prior attempt (PR #207)

[PR #207 — SMC v0.1](https://github.com/humanaios-ui/operations/pull/207) is a sound census of *structure* and its method is reused here: mechanical enumeration, one runnable extractor as the source of every number, a machine-readable metrics JSON, a falsifier per finding.

It is not a resource system, for six specific reasons: its "unit" is a file, not a quantity with a dimension and a conservation rule; nothing in it is capacity-constrained; every metric is a stock at census time with no flows; there is no cost side, so `dangling_rate = 0.78` cannot be weighed against anything; its L0/L2/L3 tiers are heuristic degree buckets, not units; and reference-counting cannot see a queue — it reports `REGISTERED.md` as the top shared store (76 referencing units) without seeing that the file is write-gated on one person with 35 entries waiting.

**PR #207 answers "what is connected to what". This answers "what is scarce, who owes what, and what is the next minute worth."** Both are worth having; the SMC extractor should keep running.

---

## Falsifier

falsifier: **If, 90 days after ratification, `ledgers/RESOURCE_LEDGER.jsonl` holds no SPEND row and no capacity declaration, RBE-OPS is inert and should be retired from the tree rather than left as decoration.** The regime's likeliest failure is dormancy, not error.

Three further falsifiers, one per moving part:

- **The constraint designation.** Two consecutive censuses showing another registered input unit at higher utilization than RAT-min move the designation to that unit. A declared capacity putting RAT-min utilization below 1.0 with the backlog flat or falling retires it.
- **The scoring change.** If rows refused as UNPRICED outnumber rows scheduled in the first measurement window, the gate is blocking work rather than ordering it, and `QUEUE_SCORING_MODE` reverts to `impact` by its own revert rule.
- **The priors.** Each demand prior is replaced by the measured median once n ≥ 5 SPEND rows of that class exist. A measured median more than 2× from its prior forces a re-census and re-derivation of the ordering.

Per-finding falsifiers are stated inline in §D.

---

## §F What Z2 is being asked for

In constraint units: **~20 RAT-min** to read and dispose of this proposal, plus one number.

1. **Sign, edit, or reject `RESOURCE_UNITS.yaml`** — particularly the unit set, the demand priors (low-confidence Z1 estimates), and the constraint designation.
2. **Declare a RAT-min capacity.** `resource_ledger_v0_1.py cap ledgers/RESOURCE_LEDGER.jsonl RAT-min <n> --by Z2 --hash <h> --period week --source "<basis>"`. Without it, utilization, clearance time and every derived figure stay `null`. This is the single highest-value missing number in the system.
3. **Rule on the two queue constants** (`QUEUE_SCORING_MODE` → `resource`, `UNPRICED_ROW_POLICY` → `REFUSED_TO_START`) as one molt, or reject them. Anti-cascade: one open molt per constant, K ≤ 3 system-wide — this proposes 2 and there are 0 open.
4. **Disposition F-RBE-01/02/03** and the IC-candidate in §D.
5. **Optional, high-yield:** decompose `Q-NF-Z2-PINS` into the four priced sub-orders in `docs/RESOURCE_BASED_ECONOMICS.md` §7. The 20-minute sub-order (two past-date resolutions) produces the organization's first two evidence rows; the 63-minute one produces none until its tokens later resolve.

---

## §G Receipt

Claims in this block and where each is checkable.

| Claim | Where |
|---|---|
| 130 open obligations, ≈1575 RAT-min | `outputs/resource_census.json`, re-derivable via `python3 tools/resource_census_v0_1.py census` |
| EVID-row 0, CAL-pt 0, RAT-art 94 | same file, `stocks` |
| NF_LEDGER has no RESOLVE events | `ledgers/NF_LEDGER.jsonl` — 106 PIN / 58 TOKEN / 1 OPEN |
| Q-NF-Z2-PINS costs 168 RAT-min | `PRIORITY_QUEUE.md` owed-items table × `RESOURCE_UNITS.yaml → demand_priors` (10 + 75 + 63 + 20) |
| Resource mode is off | `PriorityQueueEngine.from_constants()` with `QUEUE_SCORING_MODE.molt_id == null` → `mode == "impact"`; asserted in `test_resource_economics.py` |
| Ledger chain intact | `python3 tools/resource_ledger_v0_1.py verify ledgers/RESOURCE_LEDGER.jsonl` |
| Every RAT-min figure is a prior | every census field carries `basis: PRIOR`; no SPEND row exists |

**Not done this session:** no REGISTERED.md write (Z2 sole write); no ratification hash claimed; no capacity declared; no measured shadow price (n = 0 for every pair); no back-fill of historical RAT-min spends — the ledger starts empty rather than being seeded with reconstructed numbers.
