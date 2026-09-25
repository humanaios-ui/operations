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

## Prototype code

- `gate.py` — deterministic RID policy + three-seat gate.
- `prp.py` — non-self-referential package-root calculation + append-only run-event verification.
- `workflows.json` — six non-enforcing workflow definitions.
- `capability_graph.json` — roadmap-to-HumanAIOS capability graph.
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
