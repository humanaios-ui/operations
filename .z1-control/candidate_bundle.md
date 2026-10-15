# candidate-bundle/v1 — a Z1 candidate block that IS an Empirica bundle

**Status:** B3 of the Substrate Map. Defines one schema so a governance candidate
(F/IC/H/MOLT) and an Empirica `log-artifacts` bundle are the same object, not two
representations kept in sync by hand. Produced/validated by `.z1-control/candidate_bundle.py`.

## Why one schema

A Z1 candidate and an Empirica artifact bundle answer the same questions — what is
claimed, what would falsify it, what evidence backs it. Keeping both is the
parallel-engine failure the whole substrate exists to end. Under candidate-bundle/v1 the
candidate **is** the bundle: `--emit-bundle` produces the exact `empirica log-artifacts`
JSON (graph-canonical, D1); `--validate` enforces the falsifier the Z2 gate requires;
B1 (`ratify_eco.py`) signs it on ECO-accept (D2); B2 renders it into the REGISTERED view.

## Document fields

```yaml
schema: candidate-bundle/v1          # required, exact
candidate_id: Q-<TYPE>-<DESCRIPTOR>-<VERSION>   # required, e.g. Q-F-GOVERNANCE-03
type: F | IC | H | MOLT              # required
title: <one line — the claim itself>            # required
description: <narrative, markdown ok>
falsifier: <FALSE if … — required, or falsifier_waiver with a reason>
impact: <1–10 or 0–1>                # F: becomes node impact (0–1)
confidence: <0–1>                    # H: becomes assumption confidence
prevention: <text>                   # IC: what stops the repeat
reversibility: exploratory|committal|forced     # MOLT
area: <domain>                       # H: assumption domain
evidence: [ "<ref or URL>", … ]
visibility: public | shared | local  # default shared
```

## The mapping (candidate → Empirica nodes + edges)

Uses **only** node types and relations `empirica log-artifacts --schema` accepts — the
tool asserts its own output against them, so a drift fails the self-test, not empirica.

| Candidate `type` | primary node | key data |
|---|---|---|
| **F** Finding | `finding` | `finding`=title, `impact`=impact/10 |
| **IC** Integrity Correction | `mistake` | `mistake`=title, `why_wrong`=description, `prevention` |
| **H** Hypothesis | `assumption` | `assumption`=title, `confidence`, `domain` |
| **MOLT** constant change | `decision` | `choice`=title, `rationale`, `reversibility` |

| Candidate part | becomes | edge |
|---|---|---|
| `falsifier` | an `unknown` ("FALSE if …") | `unknown` **raised_by** primary — resolved at window close (feeds B5 Brier) |
| `evidence[]` ref | a `source` | `source` **evidence** primary |
| `evidence[]` URL | a `source` | `source` **sourced_from** primary |
| Z2 ratification (added by B1 on accept) | a `decision` | `decision` **attached_to** primary |

> **Note for B1:** the ratification edge uses **`attached_to`** (a valid relation);
> `ratifies` is not in empirica's relation set, so `ratify_eco.py`'s emitted graph-cmd
> should attach the RATIFY decision with `attached_to`, not `ratifies`. (One-line
> follow-up on the B1 branch.)

## Usage

```bash
# validate (CI gate runs this + --smoke-test)
python3 .z1-control/candidate_bundle.py --validate Q-F-GOVERNANCE-03.yaml

# emit and record into the graph (D1 — graph is canonical)
python3 .z1-control/candidate_bundle.py --emit-bundle Q-F-GOVERNANCE-03.yaml \
  | empirica log-artifacts -
```

The emitted bundle sets `data.subject = candidate_id` on every node, so B2 can group a
candidate's whole sub-graph and render it as one REGISTERED entry.
