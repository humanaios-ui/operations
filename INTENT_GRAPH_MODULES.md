<!-- DERIVED VIEW — do not hand-edit. Source: INTENT_GRAPH.yaml -->

# INTENT_GRAPH_MODULES

**Status:** derived projection only; the graph remains `PROPOSED` and authoritative structure remains in `INTENT_GRAPH.yaml`.

Every entry retains its original node id and source path. Module placement is an operator-facing grouping, not a graph relationship or authority change.

## Intent

| Node | Type | Name | Status | Source |
|:--|:--|:--|:--|:--|
| `V-HAIOS` | vision | Self-sufficient human-AI orchestration | LIVE | `OPS_ROADMAP_V1.2.md` · 1. Vision & Objective |
| `M-OBSERVABILITY` | mission | Behavioral observability | LIVE | `SEED.md` · 1. What HumanAIOS Is |
| `M-GOVERNED-CHANGE` | mission | Governed recursive change | LIVE | `CLAUDE.md` · Decision Routing |
| `M-RESOURCE-TRUTH` | mission | Resource-based operation | LIVE | `docs/RESOURCE_BASED_ECONOMICS.md` |
| `P-FALSIFIER` | principle | Falsifier doctrine | LIVE | `CLAUDE.md` · Decision Routing |
| `P-ADMISSION` | principle | Admission precedes correction | LIVE | `PRINCIPLES_SEED_V1_0.md` · 1.A |
| `P-EVIDENCE-OVER-CLAIM` | principle | Claim reconciles to tree | LIVE | `CLAUDE.md` · B.6 |
| `P-NON-COMMENSURABLE` | principle | Non-commensurable units | LIVE | `RESOURCE_UNITS.yaml` |
| `P-TEMPORAL-PURITY` | principle | Clocks measure, they do not authorize | LIVE | `TEMPORAL_DISSOLUTION_POLICY.md` · Invariant |
| `P-SERIAL-GATE` | principle | Serial ratification | LIVE | `CLAUDE.md` · Authority Roles |

## Resources

| Node | Type | Name | Status | Source |
|:--|:--|:--|:--|:--|
| `O-QUEUE` | objective | Work admission | LIVE | `PRIORITY_QUEUE.md` |
| `O-TEMPORAL-GATE` | objective | Temporal dissolution | LIVE | `TEMPORAL_DISSOLUTION_POLICY.md` |
| `O-CORPUS-INTEGRITY` | objective | Corpus integrity | LIVE | `audits/CORPUS_RECONCILIATION_S-070226.md` |
| `I-RESOURCE-CENSUS` | instrument | Resource census | LIVE | `tools/resource_census_v0_1.py` |
| `I-QUEUE-ENGINE` | instrument | Priority queue engine | LIVE | `priority_queue_engine.py` |
| `I-CORPUS-VALIDATOR` | instrument | Corpus integrity validator | LIVE | `tools/corpus_integrity_validator.py` |

## Control

| Node | Type | Name | Status | Source |
|:--|:--|:--|:--|:--|
| `O-MOLT-CYCLE` | objective | Molt lifecycle | CONFLICTED | `MOLT_STATE.md` |
| `O-REGISTRY` | objective | Findings registry | LIVE | `REGISTERED.md` |
| `O-DECISION-ROUTING` | objective | Z1 to Z2 decision routing | CONFLICTED | `z1-inbox/INDEX.yaml` |
| `O-DOC-CONTROL` | objective | Document control | CONFLICTED | `document-registry.yaml` |
| `O-IDENTITY-ANCHOR` | objective | Identity anchor | CONFLICTED | `SEED.md` |
| `G-Z2-RATIFY` | gate | Z2 ratification gate | LIVE | `.github/workflows/z2_ratification_gate.yml` |
| `G-TEMPORAL-SCAN` | gate | Temporal control scan | LIVE | `tests/test_temporal_dissolution_gate.py` |
| `G-ANTI-CASCADE` | gate | Anti-cascade bounds | LIVE | `molt_cycle.py` |
| `G-FALSIFIER-LINT` | gate | Falsifier lint | CITED_NOT_IMPLEMENTED | `CLAUDE.md` · CI/CD Gates |

## Execution

| Node | Type | Name | Status | Source |
|:--|:--|:--|:--|:--|
| `O-WITNESS` | objective | Witness ledger | PROPOSED | `WITNESS_SERVICE_CONTRACT.md` |
| `O-INTENT-GRAPH` | objective | Shared intent substrate | PROPOSED | `INTENT_GRAPH.yaml` |

## Assurance

| Node | Type | Name | Status | Source |
|:--|:--|:--|:--|:--|
| `I-NF-LEDGER` | instrument | NF ledger | LIVE | `ledgers/NF_LEDGER.jsonl` |
| `I-INTENT-GRAPH` | instrument | Intent graph renderer | PROPOSED | `tools/intent_graph_v1_0.py` |

## Open conflicts

Conflict details and evidence are retained in `CONFLICTS.yaml`.

| From | To | Candidate |
|:--|:--|:--|
| `O-MOLT-CYCLE` | `O-TEMPORAL-GATE` | Q-MOLT-TEMPORAL-PURITY-01 |
| `O-DOC-CONTROL` | `O-TEMPORAL-GATE` | Q-TEMPORAL-DISSOLUTION-01 |
| `O-IDENTITY-ANCHOR` | `V-HAIOS` | Q-SEED-TRL-PROPAGATION-01 |
| `O-IDENTITY-ANCHOR` | `O-CORPUS-INTEGRITY` | Q-CORPUS-STATS-RECONCILE-01 |
| `O-DECISION-ROUTING` | `O-TEMPORAL-GATE` | Q-MOLT-TEMPORAL-PURITY-01 |
