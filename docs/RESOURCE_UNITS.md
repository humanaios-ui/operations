# Resource Units — operator reference

**Definitions are not in this file.** They live in [`RESOURCE_UNITS.yaml`](../RESOURCE_UNITS.yaml), which the tools read directly. Restating unit definitions in prose is how two surfaces drift (CURRENT.md §0, IC-020 class), so this file carries only what the registry cannot: how to record resource events, how to read the census, and what to do when a number comes back `null`.

Concepts and justification: [`docs/RESOURCE_BASED_ECONOMICS.md`](RESOURCE_BASED_ECONOMICS.md).

---

## See the unit map

```bash
python3 tools/resource_census_v0_1.py units
```

Prints symbol · dimension · kind · sign · status · instrument for every registered unit, straight from the YAML. If a unit prints `CANDIDATE`, the tools will refuse it — that is not a bug, it means nobody measures it yet.

---

## Price a work order

Every work order declares a **cost vector**, not a cost. A row that does not price itself in the constraint unit cannot be claimed:

```bash
python3 tools/resource_ledger_v0_1.py claim ledgers/RESOURCE_LEDGER.jsonl Q-EXAMPLE-01 \
  --budget "RAT-min=15,Z1-ktok=40,Z3-hr=2" \
  --by Z1 --title "what this order does" --source "z1-inbox/<date>/Q-EXAMPLE-01.md"
```

Where to get the `RAT-min` figure: `RESOURCE_UNITS.yaml → demand_priors.classes` has a per-obligation-class prior. Use it, and know that you are using a prior — it is replaced by the measured median once five real SPEND rows of that class exist.

A budget is a forecast. It is not evidence of anything, and the ledger does not treat it as such.

---

## Record what was actually spent

```bash
# consumption — source required, always
python3 tools/resource_ledger_v0_1.py spend ledgers/RESOURCE_LEDGER.jsonl Q-EXAMPLE-01 \
  RAT-min 12 --by Z2 --source "<ratification hash or merged sha>" --obligation-class registry_candidate

# output produced
python3 tools/resource_ledger_v0_1.py yield ledgers/RESOURCE_LEDGER.jsonl Q-EXAMPLE-01 \
  EVID-row 2 --by Z3 --source "<tree-read sha>"

# close; yield density becomes computable at this point and not before
python3 tools/resource_ledger_v0_1.py close ledgers/RESOURCE_LEDGER.jsonl Q-EXAMPLE-01 \
  --by Z1 --source "<merged sha>"

python3 tools/resource_ledger_v0_1.py verify ledgers/RESOURCE_LEDGER.jsonl
```

**Everything that mutates the ledger needs `--source`.** A spend with no source is a claim, and the tool refuses it for the same reason `nf_ledger_v0_1.py` refuses a resolution with no source.

---

## Declare a capacity

Until a capacity exists for a unit, every utilization figure involving it is `null` — not zero, not "fine".

```bash
# the constraint unit is a Z2 act and needs a hash
python3 tools/resource_ledger_v0_1.py cap ledgers/RESOURCE_LEDGER.jsonl RAT-min 120 \
  --by Z2 --hash <ratification hash> --period week --source "<where the number comes from>"
```

---

## Measure an exchange rate

There is no default conversion between dimensions. The only legal rate is a measured margin:

```bash
python3 tools/resource_ledger_v0_1.py price ledgers/RESOURCE_LEDGER.jsonl Z3-hr Z1-ktok 25 \
  --n 12 --window 2026-W37..2026-W40 --constraint RAT-min \
  --by Z1 --source "<the observations behind the rate>"
```

Refused without `n ≥ 8`, without a window, without a named constraint, or without a source. The rate expires with its window; re-measure or it lapses. This is the one place the regime allows apples and oranges to trade, and it is deliberately expensive to use.

---

## Read the census

```bash
python3 tools/resource_census_v0_1.py census                  # table + outputs/resource_census.json
python3 tools/resource_census_v0_1.py census --capacity 120   # adds utilization and clearance time
python3 tools/resource_census_v0_1.py census --json --no-write
```

Reading the output:

| Field | Means |
|---|---|
| `basis: MEASURED` | counted mechanically from a named file |
| `basis: PRIOR` | a Z1 estimate with no measurement behind it — never cite it as a finding |
| `basis: UNMEASURED` | no instrument has run; the value is `null` |
| `utilization: null` | no capacity declared. Not "low utilization". Undefined. |
| `debt_rat_min` | the backlog expressed in constraint-minutes; `basis: PRIOR` until spends land |
| `clearance_sensitivity_weeks` | a what-if table, not a forecast |

**When a number comes back `null`, the answer to "so what is it really?" is that nobody has measured it.** Filling it in with a plausible value is the failure this whole regime exists to prevent.

---

## Refusals, in one place

The tools refuse rather than guess. Each refusal is exercised by `--smoke-test` and by `test_resource_economics.py`.

| Refusal | Why |
|---|---|
| unknown or `CANDIDATE` unit | a unit nobody measures cannot be spent |
| quantity ≤ 0 | a non-positive resource event is a correction, and corrections are new events |
| SPEND / YIELD / WASTE / CLOSE without `--source` | evidence, not assertion |
| claim without the constraint unit in its budget | an unpriced order cannot be scheduled |
| `cap` on the constraint unit without `--by Z2 --hash` | capacity of the Admiral's attention is the Admiral's to declare |
| `spend` of an output unit / `yield` of an input unit | dimensions have direction |
| `waste` of a positive-sign unit | liabilities only |
| `price` with `n < 8`, or missing window / constraint / source | that is an assertion, not a measurement |
| second `close`, or any event after close | orders close once |
| any edited prior line | append-only; `verify` breaks the chain |

---

## Where each unit is actually measured

Instruments are declared per unit in the YAML (`instrument.primary`). Two standing gaps worth knowing without looking them up:

- **`RAT-min` has no capacity declaration.** Demand is imputed from priors; supply is unknown. This is the single highest-value missing number in the system.
- **`RUN-day` is deliberately not restated in-tree.** It is read from Class 1 live state (WGS). Copying a runway number into a repository file is the maintained-headline drift pattern that CURRENT.md §5 already had to correct once.
