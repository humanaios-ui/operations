# HumanAIOS Federated Oracle Architecture

Status: **Phase 0 scaffold / advisory-only**

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

## Phase 0

This directory defines contracts only. It does **not** implement autonomous crawling, repository mutation, candidate execution, or Coordinator admission.

Next pilots after review:
1. Workspace Oracle over the existing Drive graph corpus.
2. Repository Oracle over `humanaios-ui/operations`.
3. Global Oracle federation over those two projections only.
4. Explicit `candidate_change` adapter into Repository Coordinator admission.
