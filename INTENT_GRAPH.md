<!-- GENERATED FILE — do not hand-edit.
     Source: INTENT_GRAPH.yaml · Renderer: tools/intent_graph_v1_0.py
     Regenerate: python3 tools/intent_graph_v1_0.py render -->

# INTENT_GRAPH.md — how vision, mission, principles and objectives interact

**Candidate:** Q-INTENT-GRAPH-01  
**Status:** PROPOSED — not effective until Z2 ratification hash  
**Source of truth:** `INTENT_GRAPH.yaml` (edit there; this file is rendered)  
**Temporal class:** OBSERVATIONAL · scheduling authority: false

This page is a projection. It states nothing that is not in the graph, and the
graph states nothing whose source does not resolve in the tree.

---

## The canvas

Read it upward: instruments measure objectives, principles ground them, objectives
realize missions, missions realize the vision. A crossed edge (`x--x`) is a live
contradiction, labelled with the candidate open against it; a resolved one is
drawn as an ordinary dotted edge.

```mermaid
flowchart BT
  subgraph VISION[vision]
    V-HAIOS(["V-HAIOS<br/>Self-sufficient human-AI orchestration"])
  end
  subgraph MISSION[mission]
    M-OBSERVABILITY["M-OBSERVABILITY<br/>Behavioral observability"]
    M-GOVERNED-CHANGE["M-GOVERNED-CHANGE<br/>Governed recursive change"]
    M-RESOURCE-TRUTH["M-RESOURCE-TRUTH<br/>Resource-based operation"]
  end
  subgraph PRINCIPLE[principle]
    P-FALSIFIER{{"P-FALSIFIER<br/>Falsifier doctrine"}}
    P-ADMISSION{{"P-ADMISSION<br/>Admission precedes correction"}}
    P-EVIDENCE-OVER-CLAIM{{"P-EVIDENCE-OVER-CLAIM<br/>Claim reconciles to tree"}}
    P-NON-COMMENSURABLE{{"P-NON-COMMENSURABLE<br/>Non-commensurable units"}}
    P-TEMPORAL-PURITY{{"P-TEMPORAL-PURITY<br/>Clocks measure, they do not authorize"}}
    P-SERIAL-GATE{{"P-SERIAL-GATE<br/>Serial ratification"}}
  end
  subgraph OBJECTIVE[objective]
    O-MOLT-CYCLE["O-MOLT-CYCLE<br/>Molt lifecycle"]
    O-REGISTRY["O-REGISTRY<br/>Findings registry"]
    O-QUEUE["O-QUEUE<br/>Work admission"]
    O-TEMPORAL-GATE["O-TEMPORAL-GATE<br/>Temporal dissolution"]
    O-WITNESS["O-WITNESS<br/>Witness ledger"]
    O-DECISION-ROUTING["O-DECISION-ROUTING<br/>Z1 to Z2 decision routing"]
    O-DOC-CONTROL["O-DOC-CONTROL<br/>Document control"]
    O-IDENTITY-ANCHOR["O-IDENTITY-ANCHOR<br/>Identity anchor"]
    O-CORPUS-INTEGRITY["O-CORPUS-INTEGRITY<br/>Corpus integrity"]
    O-INTENT-GRAPH["O-INTENT-GRAPH<br/>Shared intent substrate"]
  end
  subgraph GATE[gate]
    G-Z2-RATIFY[/"G-Z2-RATIFY<br/>Z2 ratification gate"/]
    G-TEMPORAL-SCAN[/"G-TEMPORAL-SCAN<br/>Temporal control scan"/]
    G-ANTI-CASCADE[/"G-ANTI-CASCADE<br/>Anti-cascade bounds"/]
    G-FALSIFIER-LINT[/"G-FALSIFIER-LINT<br/>Falsifier lint"/]
  end
  subgraph INSTRUMENT[instrument]
    I-NF-LEDGER[("I-NF-LEDGER<br/>NF ledger")]
    I-RESOURCE-CENSUS[("I-RESOURCE-CENSUS<br/>Resource census")]
    I-QUEUE-ENGINE[("I-QUEUE-ENGINE<br/>Priority queue engine")]
    I-CORPUS-VALIDATOR[("I-CORPUS-VALIDATOR<br/>Corpus integrity validator")]
    I-INTENT-GRAPH[("I-INTENT-GRAPH<br/>Intent graph renderer")]
  end

  M-OBSERVABILITY -->|realizes| V-HAIOS
  M-GOVERNED-CHANGE -->|realizes| V-HAIOS
  M-RESOURCE-TRUTH -->|realizes| V-HAIOS
  O-MOLT-CYCLE -->|realizes| M-GOVERNED-CHANGE
  O-REGISTRY -->|realizes| M-GOVERNED-CHANGE
  O-WITNESS -->|realizes| M-GOVERNED-CHANGE
  O-INTENT-GRAPH -->|realizes| M-GOVERNED-CHANGE
  O-DOC-CONTROL -->|realizes| M-GOVERNED-CHANGE
  O-DECISION-ROUTING -->|realizes| M-GOVERNED-CHANGE
  O-IDENTITY-ANCHOR -->|realizes| M-GOVERNED-CHANGE
  O-CORPUS-INTEGRITY -->|realizes| M-OBSERVABILITY
  O-QUEUE -->|realizes| M-RESOURCE-TRUTH
  O-TEMPORAL-GATE -->|realizes| M-RESOURCE-TRUTH
  P-FALSIFIER -.->|grounds| O-MOLT-CYCLE
  P-FALSIFIER -.->|grounds| O-REGISTRY
  P-SERIAL-GATE -.->|grounds| O-MOLT-CYCLE
  P-SERIAL-GATE -.->|grounds| O-REGISTRY
  P-SERIAL-GATE -.->|grounds| O-WITNESS
  P-SERIAL-GATE -.->|grounds| O-DECISION-ROUTING
  P-TEMPORAL-PURITY -.->|grounds| O-DECISION-ROUTING
  P-ADMISSION -.->|grounds| O-REGISTRY
  P-ADMISSION -.->|grounds| O-INTENT-GRAPH
  P-EVIDENCE-OVER-CLAIM -.->|grounds| O-REGISTRY
  P-EVIDENCE-OVER-CLAIM -.->|grounds| O-INTENT-GRAPH
  P-EVIDENCE-OVER-CLAIM -.->|grounds| O-DOC-CONTROL
  P-EVIDENCE-OVER-CLAIM -.->|grounds| O-CORPUS-INTEGRITY
  P-SERIAL-GATE -.->|grounds| O-IDENTITY-ANCHOR
  P-ADMISSION -.->|grounds| O-CORPUS-INTEGRITY
  P-NON-COMMENSURABLE -.->|grounds| O-QUEUE
  P-TEMPORAL-PURITY -.->|grounds| O-QUEUE
  P-TEMPORAL-PURITY -.->|grounds| O-TEMPORAL-GATE
  P-TEMPORAL-PURITY -.->|grounds| O-MOLT-CYCLE
  P-SERIAL-GATE -.->|grounds| G-Z2-RATIFY
  P-FALSIFIER -.->|grounds| G-FALSIFIER-LINT
  P-TEMPORAL-PURITY -.->|grounds| G-TEMPORAL-SCAN
  P-ADMISSION -.->|grounds| G-ANTI-CASCADE
  G-Z2-RATIFY -.->|enforces| P-SERIAL-GATE
  G-Z2-RATIFY -.->|enforces| P-FALSIFIER
  G-TEMPORAL-SCAN -.->|enforces| P-TEMPORAL-PURITY
  G-FALSIFIER-LINT -.->|enforces| P-FALSIFIER
  G-ANTI-CASCADE -.->|enforces| P-ADMISSION
  I-NF-LEDGER ==>|measures| O-MOLT-CYCLE
  I-NF-LEDGER ==>|measures| O-REGISTRY
  I-RESOURCE-CENSUS ==>|measures| O-QUEUE
  I-QUEUE-ENGINE ==>|measures| O-QUEUE
  I-INTENT-GRAPH ==>|measures| O-INTENT-GRAPH
  I-CORPUS-VALIDATOR ==>|measures| O-CORPUS-INTEGRITY
  G-ANTI-CASCADE -.->|constrains| O-MOLT-CYCLE
  G-TEMPORAL-SCAN -.->|constrains| O-DOC-CONTROL
  O-MOLT-CYCLE x--x|conflicts: Q-MOLT-TEMPORAL-PURITY-01| O-TEMPORAL-GATE
  O-DOC-CONTROL x--x|conflicts: Q-TEMPORAL-DISSOLUTION-01| O-TEMPORAL-GATE
  O-IDENTITY-ANCHOR x--x|conflicts: Q-SEED-TRL-PROPAGATION-01| V-HAIOS
  O-IDENTITY-ANCHOR x--x|conflicts: Q-CORPUS-STATS-RECONCILE-01| O-CORPUS-INTEGRITY
  O-DECISION-ROUTING x--x|conflicts: Q-MOLT-TEMPORAL-PURITY-01| O-TEMPORAL-GATE

  classDef conflicted stroke-dasharray: 4 3,stroke-width:2px
  class O-DECISION-ROUTING,O-DOC-CONTROL,O-IDENTITY-ANCHOR,O-MOLT-CYCLE conflicted
```

---

## Open contradictions

Each row is two live artifacts that cannot both be right. `q_ref` names the
candidate that would settle it — an open row with no candidate fails validation.

| Between | And | Candidate | What contradicts |
|:--|:--|:--|:--|
| `O-MOLT-CYCLE` | `O-TEMPORAL-GATE` | Q-MOLT-TEMPORAL-PURITY-01 | MOLT_STATE.md resolves a molt at `window_end` and computes brier_actual "at window close" — a molt outcome determined by elapsed time. TEMPORAL_DISSOLUTION_POLICY.md classifies exactly that as INVALID_INTERNAL_DEADLINE, and BOOT_PROCESS_MAP.md already published the successor reading ("Molt completes when measurement criteria met") without MOLT_STATE.md being migrated to match. |
| `O-DOC-CONTROL` | `O-TEMPORAL-GATE` | Q-TEMPORAL-DISSOLUTION-01 | document-registry.yaml derives review_due from review_interval_days and renders documents "visibly overdue" once the interval elapses. Obligation is created by the calendar rather than by source drift. |
| `O-IDENTITY-ANCHOR` | `V-HAIOS` | Q-SEED-TRL-PROPAGATION-01 | OPS_ROADMAP_V1.2.md records a Z2 ratification — "TRL corrected from 2-3 to 4 throughout \| RATIFIED - Night \| S-061226-02" — and applies TRL 4. SEED.md, the identity anchor that is live-fetched at session open, still states TRL 2-3 in three places including its footer. A ratified correction was applied to one surface and never propagated to the canonical one, so every session boots on the superseded value. Exactly the shape of the molt-window finding. |
| `O-IDENTITY-ANCHOR` | `O-CORPUS-INTEGRITY` | Q-CORPUS-STATS-RECONCILE-01 | audits/CORPUS_RECONCILIATION_S-070226.md is a Zone 1 submission-blocking finding: the cited headline statistics are not reproducible from the published dataset. It offers two resolution options and records no selection. SEED.md still publishes the unreproducible set as canonical — N_total 629, N_LI 307, mean LI 0.8632 — against the audit's measured 608 rows, 0.8431 raw and 0.8572 cleaned. Tree-wide, 0.8632 appears 38 times. A third set (LI 0.87, the "canonical paper numbers") is in use with a written instruction not to mix it with the others. The finding is documented, unresolved, and load-bearing for the instrument's own credibility claim. |
| `O-DECISION-ROUTING` | `O-TEMPORAL-GATE` | Q-MOLT-TEMPORAL-PURITY-01 | z1-inbox/INDEX.yaml carries `decision_window_days: 2` and CLAUDE.md states a 48h Z2 decision window with contest rights expiring on elapsed time. The ratifier's attention is a measured resource (RAT-min); a two-day clock neither creates it nor licenses escalation when it runs out. |

**O-MOLT-CYCLE ↔ O-TEMPORAL-GATE — evidence**

- MOLT_STATE.md: window_start / window_end / prediction.window_days
- BOOT_PROCESS_MAP.md: "Molt window_end at timestamp" listed as REMOVED
- TEMPORAL_DISSOLUTION_POLICY.md: INTERNAL_WORK_DEADLINE class

**O-DOC-CONTROL ↔ O-TEMPORAL-GATE — evidence**

- document-registry.yaml: review_interval_days, review_due, overdue
- TEMPORAL_CONTROL_AUDIT.md: document-control finding

**O-IDENTITY-ANCHOR ↔ V-HAIOS — evidence**

- OPS_ROADMAP_V1.2.md line 18: TRL corrected from 2-3 to 4 throughout, RATIFIED
- SEED.md lines 33, 231, 318: TRL 2-3
- tree-wide: 57 occurrences of TRL 2-3 against 21 of TRL 4

**O-IDENTITY-ANCHOR ↔ O-CORPUS-INTEGRITY — evidence**

- audits/CORPUS_RECONCILIATION_S-070226.md: "Not one of the five headline numbers matches"
- SEED.md lines 89-92: N_total 629, N_LI 307, Mean LI 0.8632
- deliverables/witness-stand-post-1.md: "Do NOT swap in the 0.8632/N=629 draft figures"
- tree-wide mean LI values: 0.8632 x38, 0.8532 x7, 0.8431 x2, 0.8572 x1

**O-DECISION-ROUTING ↔ O-TEMPORAL-GATE — evidence**

- z1-inbox/INDEX.yaml: decision_window_days: 2
- CLAUDE.md: "Decision window: 48h for routine decisions"
- BOOT_PROCESS_MAP.md: "Z2 responds within 48h" listed as REMOVED

---

## Layers

### Vision

| Id | Name | Statement | Source | State | Persists until |
|:--|:--|:--|:--|:--|:--|
| `V-HAIOS` | Self-sufficient human-AI orchestration | A human-AI orchestration system demonstrating human-generated agency, independent growth, and mutual harmonization between technical systems and human operators — operating as behavioral observability infrastructure rather than as a product. | `OPS_ROADMAP_V1.2.md` · 1. Vision & Objective | live | Z2 supersedes |

### Mission

| Id | Name | Statement | Source | State | Persists until |
|:--|:--|:--|:--|:--|:--|
| `M-OBSERVABILITY` | Behavioral observability | Measure the gap between what an AI system claims about its own behavior and what it does when that claim is tested. The gap is the finding; it requires no claim about consciousness or intent to be meaningful. | `SEED.md` · 1. What HumanAIOS Is | live | Z2 supersedes |
| `M-GOVERNED-CHANGE` | Governed recursive change | Every change to a constant, gate or authority passes a serial ratifier, carries a prediction and a falsifier, and is measured after application — so that the system can correct itself without cascading. | `CLAUDE.md` · Decision Routing | live | Z2 supersedes |
| `M-RESOURCE-TRUTH` | Resource-based operation | Schedule work by measured resource state and readiness predicates, in non-commensurable natural units, with no numeraire and no clock authority. | `docs/RESOURCE_BASED_ECONOMICS.md` | live | Z2 supersedes |

### Principle

| Id | Name | Statement | Source | State | Persists until |
|:--|:--|:--|:--|:--|:--|
| `P-FALSIFIER` | Falsifier doctrine | No hypothesis, molt or candidate enters the registry without a specific observable condition that would prove it wrong. | `CLAUDE.md` · Decision Routing | live | Z2 supersedes |
| `P-ADMISSION` | Admission precedes correction | A system that cannot admit its own malfunction cannot correct it. Sequence is load-bearing — admission, inventory, disclosure, amends. | `PRINCIPLES_SEED_V1_0.md` · 1.A | live | Z2 supersedes |
| `P-EVIDENCE-OVER-CLAIM` | Claim reconciles to tree | Every statement made in a session is walked back against the tree at close. A claim with no matching artifact is a RECEIPT-GAP, not a result. | `CLAUDE.md` · B.6 | live | Z2 supersedes |
| `P-NON-COMMENSURABLE` | Non-commensurable units | Resource cost is a vector of registered natural units. No scalar effort unit, no numeraire, no cross-dimension conversion. | `RESOURCE_UNITS.yaml` | live | Z2 supersedes |
| `P-TEMPORAL-PURITY` | Clocks measure, they do not authorize | No internal work becomes urgent, expired, escalated, reordered or replenished because elapsed time passed. Readiness is authority ∧ dependencies ∧ resources ∧ evidence ∧ safety. | `TEMPORAL_DISSOLUTION_POLICY.md` · Invariant | live | Z2 supersedes |
| `P-SERIAL-GATE` | Serial ratification | One ratifier signs. Proposal, ratification and execution are separate roles and no role may collapse into another. | `CLAUDE.md` · Authority Roles | live | Z2 supersedes |

### Objective

| Id | Name | Statement | Source | State | Persists until |
|:--|:--|:--|:--|:--|:--|
| `O-MOLT-CYCLE` | Molt lifecycle | Ratified constant changes move PROPOSED → RATIFIED → APPLIED → MEASURED → KEPT\|REVERTED under anti-cascade bounds. | `MOLT_STATE.md` | conflicted | Z2 supersedes |
| `O-REGISTRY` | Findings registry | Append-only record of findings, integrity corrections and hypotheses. | `REGISTERED.md` | live | Z2 supersedes |
| `O-QUEUE` | Work admission | Rank eligible work by impact and by yield per binding-constraint unit. No term in the score is derived from waiting. | `PRIORITY_QUEUE.md` | live | Z2 supersedes |
| `O-TEMPORAL-GATE` | Temporal dissolution | Remove hidden calendar authority from every active control surface; classify every remaining clock. | `TEMPORAL_DISSOLUTION_POLICY.md` | live | Z2 supersedes |
| `O-WITNESS` | Witness ledger | Human-machine decision attribution, so Z3 executors can be onboarded without collapsing authority. | `WITNESS_SERVICE_CONTRACT.md` | proposed | Z2 supersedes |
| `O-DECISION-ROUTING` | Z1 to Z2 decision routing | Candidate blocks reach the ratifier, carry a status the ratifier can act on, and record the decision against the block. | `z1-inbox/INDEX.yaml` | conflicted | handoff resolves |
| `O-DOC-CONTROL` | Document control | Controlled documents carry an owner, a review state and a provenance record. | `document-registry.yaml` | conflicted | Z2 supersedes |
| `O-IDENTITY-ANCHOR` | Identity anchor | SEED.md is the canonical answer to what this organism is, live-fetched at session open. Ratified corrections to identity claims must reach it. | `SEED.md` | conflicted | Z2 supersedes |
| `O-CORPUS-INTEGRITY` | Corpus integrity | The published ACAT corpus and the headline statistics cited from it are the same numbers, reproducible by anyone who downloads the dataset. | `audits/CORPUS_RECONCILIATION_S-070226.md` | live | Z2 supersedes |
| `O-INTENT-GRAPH` | Shared intent substrate | Hold vision, mission, principles and objectives as a typed graph so that grounding, measurement and contradiction are machine-checkable rather than re-derived by reading. | `INTENT_GRAPH.yaml` | proposed | Z2 supersedes |

### Gate

| Id | Name | Statement | Source | State | Persists until |
|:--|:--|:--|:--|:--|:--|
| `G-Z2-RATIFY` | Z2 ratification gate | Blocks a merge on Z1 inbox index integrity — which carries falsifier discipline on candidates, derived decision windows and the no-self-grant rule on Z2 signatures — on the rendered index being in sync, and on a seed Constitution change carrying a Z2 ratification. | `.github/workflows/z2_ratification_gate.yml` | live | Z2 supersedes |
| `G-TEMPORAL-SCAN` | Temporal control scan | Refuses added lines on active control surfaces that create internal deadlines without a permitted temporal classification. | `tests/test_temporal_dissolution_gate.py` | live | Z2 supersedes |
| `G-ANTI-CASCADE` | Anti-cascade bounds | One open molt per constant, K=3 system-wide, freeze after two consecutive reverts. | `molt_cycle.py` | live | Z2 supersedes |
| `G-FALSIFIER-LINT` | Falsifier lint | Named in CLAUDE.md and in z2_ratification_gate.yml as the check that refuses a hypothesis without a falsifier. No workflow implementing it was found under .github/workflows/. | `CLAUDE.md` · CI/CD Gates | cited, not implemented | Z2 supersedes |

### Instrument

| Id | Name | Statement | Source | State | Persists until |
|:--|:--|:--|:--|:--|:--|
| `I-NF-LEDGER` | NF ledger | Append-only hash-chained record of predictions and resolved outcomes. | `ledgers/NF_LEDGER.jsonl` | live | Z2 supersedes |
| `I-RESOURCE-CENSUS` | Resource census | Measures obligations, stocks and waste against the binding constraint. | `tools/resource_census_v0_1.py` | live | Z2 supersedes |
| `I-QUEUE-ENGINE` | Priority queue engine | Two-band constraint allocation over eligible work. | `priority_queue_engine.py` | live | Z2 supersedes |
| `I-CORPUS-VALIDATOR` | Corpus integrity validator | Recomputes the Learning Index per row and flags mismatch, anchoring and missing-timestamp defects in the published corpus. | `tools/corpus_integrity_validator.py` | live | Z2 supersedes |
| `I-INTENT-GRAPH` | Intent graph renderer | Validates this file against the tree and renders INTENT_GRAPH.md. Reports orphans, unresolved sources and open conflicts. | `tools/intent_graph_v1_0.py` | proposed | Z2 supersedes |

---

## Grounding crosswalk

For each principle: what it grounds, and what mechanically enforces it. A principle
with no enforcing gate is honoured by convention, which is a thing worth seeing.

| Principle | Grounds | Enforced by |
|:--|:--|:--|
| `P-FALSIFIER` Falsifier doctrine | `O-MOLT-CYCLE`, `O-REGISTRY`, `G-FALSIFIER-LINT` | `G-Z2-RATIFY`, `G-FALSIFIER-LINT` ⚠️ |
| `P-ADMISSION` Admission precedes correction | `O-REGISTRY`, `O-INTENT-GRAPH`, `O-CORPUS-INTEGRITY`, `G-ANTI-CASCADE` | `G-ANTI-CASCADE` |
| `P-EVIDENCE-OVER-CLAIM` Claim reconciles to tree | `O-REGISTRY`, `O-INTENT-GRAPH`, `O-DOC-CONTROL`, `O-CORPUS-INTEGRITY` | — convention only |
| `P-NON-COMMENSURABLE` Non-commensurable units | `O-QUEUE` | — convention only |
| `P-TEMPORAL-PURITY` Clocks measure, they do not authorize | `O-DECISION-ROUTING`, `O-QUEUE`, `O-TEMPORAL-GATE`, `O-MOLT-CYCLE`, `G-TEMPORAL-SCAN` | `G-TEMPORAL-SCAN` |
| `P-SERIAL-GATE` Serial ratification | `O-MOLT-CYCLE`, `O-REGISTRY`, `O-WITNESS`, `O-DECISION-ROUTING`, `O-IDENTITY-ANCHOR`, `G-Z2-RATIFY` | `G-Z2-RATIFY` |

---

## Validator report

Produced by `python3 tools/intent_graph_v1_0.py check`.

No errors: every node resolves to a path in the tree, every objective reaches
the vision, every objective and gate is grounded, and every open contradiction
names a candidate.

**7 warning(s)** — reported, not blocking:

- W1 G-FALSIFIER-LINT: cited by CLAUDE.md with no implementation found
- W6 edge[50] O-DOC-CONTROL-conflicts_with->O-TEMPORAL-GATE: q_ref Q-TEMPORAL-DISSOLUTION-01 is well-formed but not indexed in z1-inbox/INDEX.yaml — check it is not a typo for a real candidate
- W2 O-TEMPORAL-GATE: no instrument measures this objective
- W2 O-WITNESS: no instrument measures this objective
- W2 O-DECISION-ROUTING: no instrument measures this objective
- W2 O-DOC-CONTROL: no instrument measures this objective
- W2 O-IDENTITY-ANCHOR: no instrument measures this objective

---

## How to use this with the other side

- **Night (Z2)** edits meaning in `INTENT_GRAPH.yaml`: node statements, `status`,
  and the resolution of a `conflicts_with` row. Those are decisions.
- **Claude (Z1)** edits structure: proposes edges, keeps `source` honest, files a
  new `conflicts_with` row the moment it reads two artifacts that disagree, and
  regenerates this page.
- **Neither** hand-edits this file.

The exchange that previously needed a session — *does this still ground out in
anything we said we believed?* — is `trace <node-id>`.
