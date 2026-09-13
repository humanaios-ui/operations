# Resource-Based Economics for Organizational Operations (RBE-OPS v0.1)

**Status:** partially ratified. `RESOURCE_UNITS.yaml` was ratified by Night on 2026-09-13; everything else here remains a Z1 proposal and is **not** in force. See §11 for what that does and does not authorise.
**Proposal row:** Q-RBE-01 (`z1-inbox/2026-09-13/Q-RBE-01.md`)
**Companion artifacts:** [`RESOURCE_UNITS.yaml`](../RESOURCE_UNITS.yaml) (canonical unit registry) · [`docs/RESOURCE_UNITS.md`](RESOURCE_UNITS.md) (operator reference: recipes, refusals, how to read a census) · `tools/resource_census_v0_1.py` · `tools/resource_ledger_v0_1.py` · `ledgers/RESOURCE_LEDGER.jsonl`
**Pinned at:** `main@1e1b5189f6ae657c3b1a666eb5b52194327e0b63`, REGISTERED.md sha256 `b35e80365f3dad1c28997340…`, PRIORITY_QUEUE.md sha256 `c28723d1ce8d28f24fab99c2…` (IC-030 live read, 2026-09-13)

---

## 0. Position · destination · probability

**Position.** The operations tree allocates work by impact alone. `PRIORITY_QUEUE.md` scores rows as `impact + Σ impact(unblocks)` — a pure benefit measure with no denominator. Nothing in the tree records what a work order *costs*, in any unit, and nothing records what the organization *has*. Measured this session: 130 open items require an act by a single person, and the tree holds zero sourced evidence rows against them (§8).

**Destination.** A resource-based regime in which every work order is priced in the units it actually consumes, the binding constraint is named and measured rather than assumed, and allocation is decided by yield per constraint-unit. Installed as machinery (registry, ledger, census, scoring mode), dormant until Z2 ratifies.

**Probability.** 0.65 that the constraint designation in §7 (Z2 ratification attention) survives two censuses unchanged. 0.35 that any shadow price reaches `n ≥ 8` within 90 days — the regime's own falsifier is that it may install and never get measured.

---

## 1. Definition

> **Resource-based economics, in organizational operations:** an accounting and allocation regime in which the unit of account is a *measured stock or flow of a scarce input*, not a monetary claim on it; where work is priced in the units it consumes rather than in a single synthetic value; and where priority is set by throughput per unit of the binding constraint, with exchange rates between resources derived as measured marginal rates rather than asserted.

Three things follow from that sentence, and they are the whole regime:

1. **Measurement precedes allocation.** A resource with no instrument is not a resource in the system; it is a candidate (`RESOURCE_UNITS.yaml → status: CANDIDATE`). You cannot allocate what you cannot count, and counting it in a unit you made up is worse than not counting it.
2. **Non-commensurability is the default.** An operator-minute and a CI-minute and a dollar do not add up. There is no numeraire. Where a trade-off genuinely exists, it must be *measured at a margin* — a rate, at a named constraint, over a named window, with `n` observations behind it — and it expires.
3. **Priority is anchored to the constraint.** Work that does not touch the binding constraint is not in competition with work that does; it is scheduled to feed it. Work that does touch it is ranked by yield per constraint-unit, not by impact.

---

## 2. What it is not

Five confusions worth killing before they cost a cycle.

| Not this | Why it fails |
|---|---|
| **Barter** | Barter still needs bilateral coincidence of wants and still prices everything against everything. RBE prices work against *one* scarce input and leaves the rest un-traded. |
| **An internal currency / token / credit** | A credit is money with extra steps: the moment credits convert freely, you have re-introduced a numeraire and lost every property that made the units informative. The ledger here refuses an unwitnessed conversion by design. |
| **Cost accounting in disguise** | Cost accounting allocates overhead across cost objects to compute a unit cost in currency. RBE never leaves the natural unit: the answer to "what did this cost" is a *vector*, not a scalar. |
| **Technocratic central planning (Venus-Project style)** | Whole-economy planning in natural units fails on the knowledge problem (§3). The claim here is deliberately smaller: it works *inside one organization*, and the boundary is stated. |
| **OKRs / a scoring rubric** | Those price benefit and ignore capacity. The reshape in §7 is precisely the addition of a denominator to a benefit-only score. |

---

## 3. Why this works inside a firm and not inside an economy

The standard objection is a century old and it is correct. Neurath argued after 1919 for *Naturalrechnung* — calculation in kind, planning directly in tons, hours and kilowatts, with no common unit ([Neurath in the calculation debate](https://www.tandfonline.com/doi/abs/10.1080/09672560802252354)). Mises' 1920 reply was that without a commensurable unit there is no way to compare the countless technically feasible production plans, so rational allocation collapses ([Mises/Neurath, commensurability](https://www.tandfonline.com/doi/abs/10.1080/03085140500465857)). Hayek then sharpened it: even given the units, the knowledge needed to allocate is dispersed and local, and prices are the mechanism that aggregates it.

Both objections bind on a *whole economy*. Neither binds here, and the reasons are structural, not rhetorical:

1. **The plan is small.** An economy allocates over ~10⁶ distinguishable goods. This organization allocates over **12 registered units and 8 obligation classes**. Enumerating the feasible plans is not a combinatorial catastrophe; it is a table that fits on a screen.
2. **The knowledge is already local.** Hayek's dispersed knowledge is dispersed *across* firms. Inside one, the planner, the resource holder, and the person doing the work are the same small set of agents, already sharing a repository.
3. **Firms already do this.** Coase's point in *The Nature of the Firm* (1937) is that inside the boundary, allocation happens by direction, not by price — that is *what the boundary is for*. Every organization is already a non-price allocation island. RBE does not introduce planning into a market; it makes the planning that is already happening legible, by keeping the books in the units the work actually consumes instead of translating everything into a currency that nobody inside the boundary trades in.
4. **The price mechanism is retained where it is informative.** The regime does not abolish exchange rates; it demotes them from assumptions to measurements. This is the same move as Kantorovich's shadow prices, or the dual values of a constrained allocation: a price is what one more unit of the binding constraint is worth *at this margin*, measured, with an expiry.

So the honest scope claim: **RBE-OPS is defensible at the scale of one organization with a small unit set and shared information; it is not a proposal about economies, and any attempt to scale it past the point where the unit table stops fitting on a screen should be treated as falsified.**

The operations-research tradition supplies the missing allocation rule. Goldratt's Theory of Constraints and [throughput accounting](https://www.accaglobal.com/gb/en/student/exam-support-resources/fundamentals-exams-study-resources/f5/technical-articles/throughput-constraints1.html) reject cost allocation entirely and rank work by **throughput per unit of the bottleneck resource**. That is the rule adopted in §7, with one substitution: throughput is measured in the organization's actual output unit (evidence rows), not in sales.

---

## 4. The unit grammar

Every unit in `RESOURCE_UNITS.yaml` carries the same eight fields, and each field exists to block a specific failure.

| Field | Blocks |
|---|---|
| `dimension` | Adding incomparable things. Units in different dimensions never sum. |
| `kind` (stock \| flow) | Confusing a level with a rate — the most common operations accounting error. |
| `sign` (positive \| negative) | Treating a backlog as if it were not a liability. |
| `conservation` (depletable \| renewable \| non_depleting \| degradable) | Spending a renewable as if it accumulated; counting an information good as consumed when it is copied. |
| `instrument` | A unit nobody measures. **No instrument → `status: CANDIDATE`, and the tools refuse it.** |
| `measurement_procedure` | Two people counting the same unit differently. |
| `substitutes` | Implicit trade-offs. A substitution rate is `null` until a PRICE event measures it. |
| `falsifier` | A unit that cannot be wrong. Every unit states the observation that would retire it. |

**Conservation classes matter more than they look.** Attention is *renewable* (it refills weekly and does not accumulate — an unspent Admiral-minute from last week is gone, not banked). Runway is *depletable* (a stock that only falls). Evidence is *non-depleting* (citing a finding does not consume it — this is why the output side of the books behaves nothing like the input side). Assurance is *degradable* (a ratification hash certifies less as it ages — the `STALE-day` liability is exactly this decay, and it is why `stale_sweep.py` is an economic instrument, not just hygiene).

---

## 5. The registered units

Canonical definitions — instrument, measurement procedure, capacity, substitutes, falsifier — live in [`RESOURCE_UNITS.yaml`](../RESOURCE_UNITS.yaml) and are not restated here. The tables below are an index into it.

### Inputs (what gets consumed)

| Symbol | Unit | Dimension | Kind | Conservation | Instrument |
|---|---|---|---|---|---|
| **RAT-min** | Z2 ratification-minute | attention | flow /week | renewable | RESOURCE_LEDGER SPEND rows; RATIFY timestamps |
| **Z1-ktok** | Z1 proposer thousand-tokens | compute | flow /session | renewable | `behavior_spec.json` cap (100/session) |
| **Z3-hr** | Executor hour | labor | flow /week | renewable | SPEND rows, source = merged sha |
| **CI-min** | CI runner minute | compute | flow /month | depletable | Actions run durations |
| **RUN-day** | Runway-day | capital | stock | depletable | Class 1 live state (WGS) |
| **SPEC-hr** | Specimen-hour | participation | flow /cycle | depletable | specimen-intake cycles (aggregate only) |

### Outputs (what gets produced)

| Symbol | Unit | Dimension | Conservation | Instrument |
|---|---|---|---|---|
| **EVID-row** | Evidence row — one resolved observation carrying a source | evidence | non-depleting | NF_LEDGER RESOLVE events with a source |
| **CAL-pt** | Calibration point — one forecast scoreable into Brier | evidence | non-depleting | `nf_ledger_v0_1.py score` |
| **RAT-art** | Ratified artifact — one thing carrying a Z2 hash | assurance | degradable | REGISTERED.md + constants.json |

### Liabilities (what accrues against you)

| Symbol | Unit | Dimension | Sign | Instrument |
|---|---|---|---|---|
| **OBL-open** | Open obligation — an item blocked on a specific Z2 act | attention | negative | `resource_census_v0_1.py` |
| **GAP-row** | Receipt gap — a claim with no ledger entry (the IC-031 class) | evidence | negative | `receipt_reconciliation.py` |
| **STALE-day** | Constant-day past half-life | assurance | negative | `stale_sweep.py` |

### Two notable design choices

**Capital is held as duration, not currency.** `RUN-day`, not USD. Dollars are an input to *one* dimension among six, and the operationally load-bearing question is never "how many dollars" but "how many more days of deciding". Denominating capital in days also keeps it non-commensurable with attention, which is correct: more money does not buy Admiral ratification minutes, and pretending otherwise is precisely the error RBE exists to prevent.

**Two units were deliberately left CANDIDATE.** `TRUST-pt` (external credibility) and `OP-hr` (non-ratification operator time) have no instrument. They are listed as candidates with their blockers rather than omitted, because an unmeasured resource is still a resource and the gap should be visible. Registering them without instruments would let real demand hide inside an unfalsifiable number.

---

## 6. Accounting identities

```
conservation      open(u,t) + inflow(u,t) − spend(u,t) = close(u,t)      [depletable units]
backlog debt      debt(t)  = Σ_c count_c(t) × price_c                    [RAT-min]
utilization       util(u,t) = demand(u,t) / capacity(u,t)                [null when capacity UNMEASURED]
yield density     density(order) = Σ yield(order) / spend(order, RAT-min)
clearance         weeks_to_clear = debt(t) / capacity(RAT-min)           [null when capacity UNMEASURED]
```

`null` is a first-class result. The census reports `utilization: undefined` rather than filling in a plausible capacity, and `yield_density: UNMEASURED` rather than dividing by a prior. This is the IC-031 discipline in economic form: an unmeasured quantity is reported as unmeasured, never as zero and never as an estimate wearing a measurement's clothes.

### Exchange rates

Cross-dimension conversion exists in exactly one form — a `PRICE` event, which `resource_ledger_v0_1.py` refuses unless it carries all four of:

- `n ≥ shadow_price_min_n` (8) paired observations,
- a **window** (the rate expires with it — a rate that never expires is a currency),
- a named **constraint** (a marginal rate is only defined *at* a constraint),
- a **source**.

There are no default rates and no numeraire. `Z3-hr ↔ Z1-ktok` substitution — the agent-versus-executor trade-off the organization actually faces — is registered with `rate: null, status: UNMEASURED`, which is the truthful state.

### Two ledgers, one discipline

`NF_LEDGER` scores *predictions* (Brier). `RESOURCE_LEDGER` scores *consumption* (density). Same construction — append-only, hash-chained, refusals encoded as code rather than prose, every mutation requiring a source. A forecast without a source and a spend without a source fail for the same reason.

---

## 7. The allocation rule, and the reshape

### The rule

```
Band A — orders that consume 0 RAT-min:  rank by impact. Run them now.
Band B — orders that consume RAT-min:    rank by  density = (impact + Σ impact(unblocks)) / rat_min
Unpriced orders:                          not schedulable. REFUSED at the READY gate.
```

Band A before Band B is not a preference, it is the constraint discipline: work that does not touch the bottleneck never competes with work that does, and should be run to *feed* it. Band B is throughput accounting — benefit per bottleneck-minute — with the organization's own impact score as the numerator until a measured evidence yield replaces it.

### What changes in the tree

| Surface | Today | Under RBE-OPS |
|---|---|---|
| `PRIORITY_QUEUE.md` scoring | `impact + Σ impact(unblocks)` | same numerator, divided by `rat_min`; two-band ordering |
| Work-order fields | impact, status, blockers | **+ `cost:` vector** keyed by registry symbol (`RAT-min`, `Z1-ktok`, `Z3-hr`, `CI-min`) |
| READY gate | no blockers + READY status | **+ priced in the constraint unit**, per the ratified `UNPRICED_ROW_POLICY` (refuse / warn / allow) |
| `priority_queue_engine.py` | one formula | `mode="impact"` (incumbent) \| `mode="resource"`, switched only by a ratified `molt_id` |
| Constants | 3 (specimen-intake priors) | **+ 4** resource constants, `molt_id: null` until Z2 signs |
| `system_graph.json` | 19 nodes, 44 edges | **+ RU** (unit registry), **+ RL** (resource ledger), **+ RCEN** (census) — 22 nodes, 53 edges |

The scoring change is implemented as a **dormant mode**, not a switch that is already flipped. `priority_queue_engine.py` defaults to the incumbent formula and activates resource mode only when `constants.json → QUEUE_SCORING_MODE` carries a non-null `molt_id`. The molt is the ratification; the code merely respects it. This is Q-RBE-01's whole ask.

### Worked example — the live queue re-ranked

Costs below are PRIORS from `RESOURCE_UNITS.yaml → demand_priors`, not measurements. They are shown to demonstrate the mechanism, not to assert a schedule.

| Row | Impact score | RAT-min | Band | Density | Incumbent rank | RBE rank |
|---|---:|---:|:--|---:|---:|---:|
| Q-NF-SCHEMA-01 (Z1 build + test) | 9 | 0 | A | — | 1 | **1** |
| Q-IC030-REPIN-01 (Z1 re-pin) | 5 | 0 | A | — | 2 | **2** |
| Q-SI-C1-B2 (Z2 enters register values) | 5 | 10 | B | 0.50 | 3 | **3** |
| Q-SI-C1-B3 (constant ratification) | 5 | 15 | B | 0.33 | 4 | **4** |
| Q-NF-Z2-PINS (queue: *"no score"*) | — | **168** | B | **unschedulable** | — | **REFUSED** |

The first four rows barely move — which is the point of showing them: the reshape is not a re-shuffle for its own sake. The result that matters is the last row. **Q-NF-Z2-PINS carries no score and consumes 168 RAT-min — more than every other open row in the queue combined.** Under impact-only scoring it is invisible ("Hygiene (no score)"). Under resource scoring it is the single largest draw on the binding constraint and cannot be scheduled at all, because a 168-minute lump has no density: it is four different jobs wearing one id.

Decomposing it is the immediate, concrete recommendation:

| Sub-order | RAT-min | Unblocks |
|---|---:|---|
| ratification hash for the NF build | 10 | the build's own authority |
| 15 Z2 priors (`P2-<practice>:Z2`) | 75 | LT-2 has no input without these — the Brier series cannot start |
| 21 `PENDING_Z2_DATE` tokens (date or strike) | 63 | 21 tokens become scoreable |
| 2 past-date resolutions (tree read) | 20 | the first EVID-rows in the tree |

The 20-minute sub-order produces the organization's first two evidence rows; the 63-minute one produces none until its tokens later resolve. A benefit-only queue cannot see that difference. That is what a denominator buys.

---

## 8. Baseline measurement

`python3 tools/resource_census_v0_1.py census` → [`outputs/resource_census.json`](../outputs/resource_census.json), run against `main@1e1b518` on 2026-09-13.

| Obligation class | n | RAT-min ea (PRIOR) | Load |
|---|---:|---:|---:|
| registry_candidate (F/IC/H awaiting disposition) | 35 | 12 | 420 |
| doc_owner_approval (draft/review documents) | 40 | 20 | 800 |
| nf_token_date (`PENDING_Z2_DATE`) | 21 | 3 | 63 |
| nf_z2_prior (empty Z2 forecast slots) | 15 | 5 | 75 |
| nf_past_date_resolution | 7 | 10 | 70 |
| constant_ratification (`molt_id: null`) | 7 | 15 | 105 |
| queue_row_ratification (BLOCKED or PROPOSED rows) | 4 | 8 | 32 |
| queue_hash (unsigned queue) | 1 | 10 | 10 |
| **Total** | **130** | | **1575** |

**Stocks:** `RAT-art` 94 · `EVID-row` **0** · `CAL-pt` **0**
**Liabilities:** `OBL-open` 130 · `GAP-row` 1 · `STALE-day` undefined (no constant carries a `ratified_at`, so decay from a ratification that never happened is undefined, not zero)
**Constraint capacity:** UNMEASURED — so utilization and clearance time are `null`. At hypothetical capacities: 60 RAT-min/wk → 26.3 weeks to clear; 120 → 13.1; 240 → 6.6.

**This proposal is inside its own accounting.** Five of the 130 are Q-RBE-01's: four unratified constants (60 RAT-min) and one proposed queue row (8). A regime that exempted its own artifacts from the books would be measuring everyone else.

Three findings fall directly out of this table. They are filed as candidates in `z1-inbox/2026-09-13/Q-RBE-01.md`, not registered here.

- **F-RBE-01 (candidate).** One person's signature is the input to 130 open items, ~1575 RAT-min ≈ 26 hours of ratification work, against an undeclared capacity. *Falsifier: if obligations close at a rate implying < 60 RAT-min/week of actual Z2 time over 4 weeks, the priors are inflated and the debt figure is wrong.*
- **F-RBE-02 (candidate).** The queue prices benefit and not cost, so demand on the constraint is structurally unbounded: no row can ever be rejected for being too expensive, because no row has a price. *Falsifier: a queue row rejected or deferred on cost grounds under the incumbent formula would show the gate already exists informally.*
- **F-RBE-03 (candidate).** `EVID-row = 0` and `CAL-pt = 0` against 165 NF_LEDGER events and 94 ratified artifacts: the tree holds a large assurance stock and **no evidence stock at all**. Every pin is a forecast; not one has been resolved against a tree read. *Falsifier: a sourced RESOLVE event anywhere in the tree that this census fails to count.*

F-RBE-03 is the sharpest reason to keep the two ledgers separate. Assurance and evidence are different dimensions, and the organization is currently accumulating the first while producing none of the second. A single blended "progress" score would have hidden that completely.

---

## 9. Assessment of the prior attempt (PR #207)

[PR #207](https://github.com/humanaios-ui/operations/pull/207) — *SMC v0.1 Shared-Memory Census* (Grok/Copilot) — enumerates units mechanically, builds a bipartite unit↔store graph, and reports isolation, spine-attachment and dangling rates per population. It is a genuine census and its method is sound on its own terms: runnable, re-derivable, every finding carrying a metric and a falsifier.

**What it establishes and this work reuses:** mechanical enumeration over declared populations; one runnable extractor as the source of every number; per-finding falsifiers; a machine-readable metrics JSON as the artifact of record. `resource_census_v0_1.py` follows the same shape deliberately.

**Where it stops short of a resource system**, point by point:

1. **Its "unit" is a file, not a resource.** SMC units are artifacts (`tools/*.py`, `docs/**`, root `*.md`). A resource unit is a *quantity with a dimension and a conservation rule*. `110 tools_py` is a count of things, not an amount of anything: you cannot spend it, it does not deplete, and two of them do not add to a meaningful total.
2. **No scarcity.** Nothing in SMC is capacity-constrained. Economics begins where a quantity binds; SMC measures structure, and structure is not scarce.
3. **Stocks only, no flows.** Every metric is a level at census time. There is no per-period rate, so there is no consumption, no regeneration, and no way to ask whether the organization is running a deficit.
4. **No cost side.** `dangling_rate = 0.78` is a quality defect. Whether fixing it is *worth doing* is a question about the cost of fixing it against something else, and SMC has no unit in which to ask.
5. **The tier labels are not units.** L0/L2/L3 are heuristic degree buckets with session-name string matching, and the PR says so. They classify; they do not measure.
6. **It misses the actual constraint.** SMC's top shared store is `REGISTERED.md` at 76 referencing units — a structural fact. The economic fact underneath it is that REGISTERED.md is write-gated on one person and 35 entries are queued on that gate. Reference-counting cannot see a queue.

The short version: **PR #207 answers "what is connected to what"; RBE-OPS answers "what is scarce, who owes what, and what is it worth to spend the next minute."** Those are different questions and both are worth having. The SMC extractor is not superseded by this work and should keep running.

---

## 10. How this regime fails

Stated up front, with the detection for each. A regime that cannot name its own failure modes is not falsifiable.

| Failure mode | Shape | Detection |
|---|---|---|
| **Goodharting the constraint unit** | Decisions get chopped into smaller signatures to raise apparent throughput per RAT-min | Watch `density` against `EVID-row` yield, not against decision count. Rising density with flat evidence is the signature. |
| **Prior laundering** | The PRIOR minute-estimates quietly become facts by being cited | Every emitted number carries `basis: PRIOR`; priors are replaced by measured medians at n ≥ 5, and a >2× divergence forces a re-run. |
| **Unit inflation** | The registry grows to 40 units, nobody measures any of them | Cap the registry at what fits on a screen. A unit without an instrument stays CANDIDATE; a REGISTERED unit with no ledger row for a full cycle is demoted. |
| **Non-commensurability as an excuse** | "Those don't compare" becomes a way to avoid deciding | The PRICE event is the escape hatch and it is cheap to use once n ≥ 8. Refusing to measure a rate that matters is itself a finding. |
| **Dormancy** | The machinery lands, the ratification never comes, nothing is ever measured | The regime's own falsifier: **if no SPEND row and no capacity declaration exist 90 days after ratification, RBE-OPS is inert and should be retired rather than left in the tree as decoration.** |
| **Constraint mis-designation** | Attention is named the bottleneck when something else binds | Two consecutive censuses showing another unit at higher utilization move the designation (`RESOURCE_UNITS.yaml → constraint.falsifier`). |

---

## 11. Authority status

Per `CLAUDE.md` → Decision Routing, nothing is in force without a Z2 hash. One artifact now has one; the rest do not.

| Artifact | State |
|---|---|
| `RESOURCE_UNITS.yaml` | **`status: RATIFIED`** by Night, 2026-09-13. Its `ratification_hash` predates artifact signing and verifies against nothing — `ratify.py --verify-artifact` reports the mismatch, and re-signing it is an open Z2 item (`z1-inbox/2026-09-13/Z2_RULING_RESOURCE_UNITS_HEADER.md`). Unit-level `CANDIDATE` statuses inside the registry are unaffected: `TRUST-pt` and `OP-hr` remain candidates because they still have no instrument. |
| `constants.json` resource constants | `molt_id: null` — inert by the constants node rule |
| `priority_queue_engine.py` resource mode | present, **off**; activates only on a non-null ratified `molt_id` |
| `ledgers/RESOURCE_LEDGER.jsonl` | genesis + one CLAIM (this work order, budget declared as a PRIOR) |
| `outputs/resource_census.json` | measurement, no authority claimed |
| F-RBE-01/02/03 | candidates in `z1-inbox/`, **not** written to REGISTERED.md |

What Z2 is being asked for, in constraint units: **~20 RAT-min** to read this proposal and sign, edit, or reject it — and, separately, one number: **the RAT-min per week that is actually available**, without which every utilization figure in this regime stays undefined.

---

## 12. References

- Coase, R. (1937). *The Nature of the Firm.* — allocation inside the boundary is by direction, not price.
- Goldratt, E. — Theory of Constraints; [throughput accounting: rank by throughput per bottleneck-minute](https://www.accaglobal.com/gb/en/student/exam-support-resources/fundamentals-exams-study-resources/f5/technical-articles/throughput-constraints1.html).
- Kantorovich, L. (1939/1960). *The Best Use of Economic Resources* — shadow prices as duals of a constrained allocation.
- Mises, L. von (1920). *Economic Calculation in a Socialist Commonwealth*; and [the Mises–Neurath commensurability debate](https://www.tandfonline.com/doi/abs/10.1080/03085140500465857).
- Neurath, O. (1919–1928). *Calculation in kind* — [marketless planning in natural units](https://www.tandfonline.com/doi/abs/10.1080/09672560802252354); and [incommensurability, ecology and planning](https://www.researchgate.net/publication/247814208_Incommensurability_Ecology_and_Planning_Neurath_in_the_Socialist_Calculation_Debate_1919-1928).
- Hayek, F. (1945). *The Use of Knowledge in Society* — dispersed knowledge; binds across firms, not within one.
- Barney, J. (1991). *Firm Resources and Sustained Competitive Advantage* — the resource-based view: which resources are worth holding (VRIN), complementary to the question of how to spend them.
- Beer, S. (1972). *Brain of the Firm* — the Viable System Model; variety as an operational resource.
- Odum, H.T. (1996). *Environmental Accounting: Emergy* — accounting in a physical unit across a whole system; the cautionary case for a single natural numeraire.
- [Non-monetary economy and time-based units of account](https://en.wikipedia.org/wiki/Non-monetary_economy) — time banks as the simplest single-unit system, and its limits.
- Internal: `CLAUDE.md` (authority), `PRIORITY_QUEUE.md` (incumbent scoring), `ledgers/NF_LEDGER_README.md` (ledger conventions), [PR #207](https://github.com/humanaios-ui/operations/pull/207) (prior attempt).
