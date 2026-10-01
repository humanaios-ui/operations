# CRB prototype — graph and workflow expansion

This directory turns the Computational Review Board proposal into executable, non-enforcing primitives.

## Why this maps cleanly to the 2026 agentic roadmap

The supplied roadmap is useful as a **capability stack**, but HumanAIOS needs a second axis: **evidence and authority**. A system can possess programming, models, tools, orchestration, memory, RAG, deployment, monitoring, and security capabilities without having warrant to act.

HumanAIOS therefore maps the eleven capability stages into a graph where every consequential path must expose:

```
capability
  -> evidence
  -> review
  -> warrant
  -> authorization
  -> action
  -> consequence
  -> telemetry
  -> challenge/correction
```

The machine-readable mapping is `capability_graph.json`.

## Existing graph reuse

The prototype does not replace the repository's graph families:

- `INTENT_GRAPH.yaml` answers **why / what should be true**.
- `EVIDENCE_GRAPH.json` answers **what supports or defeats a claim**.
- `system_graph.json` answers **what process/gate/ledger actually runs**.
- `docs/WORKFLOW_DEPENDENCY_GRAPH.md` answers **what automation triggers or depends on what**.
- `capability_graph.json` adds **what an agent/reviewer is able to do, and where that ability meets evidence and authority**.

The desired future graph is therefore multiplex rather than one giant graph:

```
INTENT layer
    ↓ grounds
CAPABILITY layer
    ↓ exercised_by
WORKFLOW / SYSTEM layer
    ↓ emits
EVIDENCE layer
    ↓ adjudicated_by
CRB layer
    ↓ produces
WARRANT / AUTHORIZATION
    ↓
ACTION / CONSEQUENCE
    ↺ telemetry back to evidence
```

## Morphogenetic control + HEP prototype

Issue #525 adds a second non-canonical prototype layer in `morphogenesis.json`:

- **Morphogenetic Control Graph (MCG)** captures governed topology adaptation as a reviewable graph-delta lifecycle rather than an autonomous rewrite path.
- **Holographic Evidence Projection (HEP)** is the generic portable projection family for reconstructable decisions.
- **Portable Review Package (PRP)** is represented as a specialized HEP rather than a separate truth surface.

The prototype is intentionally limited to representation:

- it names the Level 0–4 change hierarchy;
- it defines the governed graph-delta event types;
- it records minimum review fields for independently reviewable topology changes;
- it exports HEP projections for review and authorization.

It does **not** alter `system_graph.json`, mutate canonical topology, or grant new authority to any model or workflow.

### Molt tier to change level (recorded before Phase B)

`morphogenesis.json` also records how the Level 0–4 hierarchy lines up with the
path-based molt tiers measured by `tools/molting_protocol_diff_v1_0.py`:

| Level | Measured tier | Authority owed | Gap recorded |
|---|---:|---|---|
| L0 state change | 0 | append-only ledger rules | none |
| L1 parameter adaptation | 1 | molt_id + pinned prediction + window + falsifier (the existing Molt operator) | none |
| L2 component / rule / policy | 0 | Z2 review via CODEOWNERS | under-gated by the classifier |
| L3 morphogenesis (topology) | 2 | registry entry + ADV run | none |
| L4 constitutional | 2 | Tier 2 plus Z2 ratification hash | classifier cannot separate L3 from L4; governance documents measure Tier 0 |

The mapping is `RECORDED_NON_ENFORCING`. It exists so that Phase B candidate
deltas can state which authority they owe; closing the two gaps is a Z2 decision.

## Prototype code

- `gate.py` — deterministic RID policy + three-seat gate.
- `prp.py` — non-self-referential package-root calculation + append-only run-event verification.
- `workflows.json` — six non-enforcing workflow definitions.
- `capability_graph.json` — roadmap-to-HumanAIOS capability graph.
- `morphogenesis.json` — governed graph-delta + HEP prototype surface.
- `../tests/test_crb_prototype.py` — falsification-oriented unit tests.

No GitHub Actions workflow is added in this change. That is deliberate: the repository already treats workflow/gate changes as an authority-bearing surface. The next executable step after Z2 ratification is to wrap these pure functions in an **advisory** workflow, observe them, then separately decide whether any result becomes blocking.

## Expansion rule

Do not add a tool simply because the roadmap names it. Add a capability only when the graph can name:

1. the capability;
2. the permitted scope;
3. the evidence it may read/write;
4. the authority that permits consequential use;
5. the telemetry emitted;
6. the falsifier or failure condition;
7. the replay path.

That is the difference between an agent stack and an evidence-bearing control architecture.

## Capture lint for the multiplex

The reason for keeping the graphs as separate layers is that no single graph can then seal itself. `tools/graph_capture_lint_v1_0.py` is the mechanical check that a layer has not quietly acquired the properties of a graph that cannot be wrong from the inside. It scores a graph file against nine properties and blocks on the three that make a graph unauditable from outside:

| id | property | what it means | gate |
|---|---|---|---|
| P1 | CLOSED_PROVENANCE | nothing cites outside the graph, or a support chain is circular with no grounded member | block |
| P2 | NO_FALSIFIER | no relation, field, state or declared vocabulary can defeat or retract a claim | block |
| P3 | NO_TIMESTAMP | no temporal anchor and no declared `temporal_class` | block |
| P4 | COLLAPSED_CONFIDENCE | every weight is the same maximum, or causal edges carry no uncertainty | advise |
| P5 | IRREVERSIBLE_MERGE | identity merges with no basis and no split channel | advise |
| P6 | SINGLE_ROLE_AUTHORITY | one identity proposes, ratifies and executes | advise |
| P7 | REFLEXIVE_MEASUREMENT | self-loops, or a measure edge paired with a feed edge | advise |
| P8 | OPAQUE_SCHEMA | dangling endpoints, undeclared relations, or no vocabulary at all | advise |
| P9 | UNVERIFIED | no node or edge records whether anything was checked | advise |

```bash
python3 tools/graph_capture_lint_v1_0.py --all                                   # the five canonical graphs
python3 tools/graph_capture_lint_v1_0.py --all --baseline crb/graph_capture_baseline.json   # CI mode
python3 tools/graph_capture_lint_v1_0.py crb/capability_graph.json --json
```

`--all` lints the layers as one set, so an edge whose endpoint is a node in a sibling layer is reported as a seam, not as dangling. `crb/graph_capture_baseline.json` records the blocking debt the canonical set carried when the lint landed, one reason per entry; a listed failure does not block, an unlisted one does, and a listed property that now passes blocks until its entry is removed. The baseline therefore only ratchets down. Candidate: `z1-inbox/2026-10-01/Q-GRAPH-CAPTURE-LINT-01.md`.
