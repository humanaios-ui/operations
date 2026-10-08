# HumanAIOS Federated Oracle Architecture

Status: **Phase 1 pilot implemented / advisory-only**

Tracking issue: #735  
Dependencies: #677, #708

## Purpose

The Oracle layer maintains evidence-bearing advisory graph projections across bounded sources and domains without acquiring authority over governed repository state.

The architecture separates four functions:

1. **Source Oracle** — observes a substrate and emits provenance-bearing observations.
2. **Domain Oracle** — interprets source observations inside a bounded domain graph.
3. **Global Oracle** — federates domain graph deltas, preserves conflicts, and detects cross-domain dependencies.
4. **Repository Coordinator** — receives candidate changes for admission evaluation. The Oracle layer does not bypass this boundary.

## Authority invariant

```
advisory_only = true
can_authorize = false
authority_effect = NONE
can_ratify = false
can_merge = false
```

Oracle output is evidence/proposal material only. It cannot authorize ACT, merge, repository mutation, or canonical promotion.

## Initial topology

```
Source Oracles
  DRIVE | GITHUB
        |
        v
Domain Oracles
  WORKSPACE | REPOSITORY | EVIDENCE | GOVERNANCE | RESEARCH | RESOURCE
        |
        v
Global Oracle
  federation | conflict preservation | dependency detection
        |
        v
GLOBAL_ADVISORY_GRAPH
        |
        v
Repository Coordinator
        |
        v
Admission / Z2 / Git
```

## Lifecycle

```
SOURCE
 -> OBSERVE
 -> IDENTIFY/HASH
 -> EXTRACT
 -> NORMALIZE
 -> CLASSIFY
 -> LINK
 -> ATTACH PROVENANCE
 -> COMPARE
 -> DETECT DELTA/CONFLICT/SUPERSESSION
 -> VALIDATE
 -> OBSERVATION RECEIPT
```

## Naming

The federated advisory projection is named `GLOBAL_ADVISORY_GRAPH`.

Do not name the advisory projection `SSOT`. Global does not mean canonical, integrated does not mean true, and observed does not mean authorized.

## Phase 1 pilot

Implemented in `engine/oracle_engine_v0_1.py` with a replayable Drive observation fixture under `fixtures/`.

The pilot:
1. Projects the existing Google Drive HumanAIOS graph through the Workspace Oracle.
2. Reads `humanaios-ui/operations/system_graph.json` through the Repository Oracle.
3. Reconciles explicit canonical identities in the Global Oracle.
4. Preserves conflicting Drive assertions rather than overwriting them.
5. Emits advisory `candidate_change` objects.
6. Routes those candidates into the existing Repository Coordinator vocabulary as **draft WORKBENCH** items only.

It still does **not** implement autonomous source crawling, repository mutation, admission-state mutation, candidate execution, or Z2 promotion.
