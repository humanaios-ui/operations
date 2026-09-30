# Calibration Graph Validation Receipt — 2026-09-30

Status: STAGE S2 COMPLETE; S3 PARTIAL

## Scope executed

Reference fixtures were created for:
- convergence;
- divergence;
- unresolved;
- delayed resolution;
- contextual interference;
- failed-retest / withdrawn design delta;
- replicated design delta;
- intentionally invalid evidence.

The ontology and SHACL shapes were extended only where fixture construction exposed missing representational primitives:
- `reportedValue`;
- `machineValue`;
- `comparisonType`;
- `sequenceIndex`;
- `retestOutcome`.

## Preflight execution result

A local RDF/Turtle parse and structural preflight was executed against the same constraints represented in the SHACL shapes.

### Valid reference set
- triples parsed: 112
- structural violations: 0
- expected: valid
- result: PASS

### Invalid reference set
Expected invalidity was detected:
1. missing `HumanTrace`;
2. `participantConfidence` outside [0,1];
3. design delta references a trace not typed `HumanTrace`;
4. design delta missing `falsifier`.

Expected: invalid  
Result: PASS (negative fixture was rejected by preflight)

## Canonical SHACL harness

`tools/calibration_graph/validate_graph.py` uses PySHACL 0.40.1 and the machine-readable validation manifest.

The execution environment used for this documentation pass did not have PySHACL installed and could not reach the package index, so canonical PySHACL execution is NOT claimed here. The harness and pinned dependency are committed for deterministic execution in an environment with dependency access.

## What validation staging discovered

Validation staging produced concrete design information before merge:

1. The first ontology did not explicitly represent comparison type, reported/machine values, sequence position, or retest outcome.
2. A positive-only test set would have been insufficient; the negative fixture establishes that the validator must reject malformed evidence.
3. “Delayed” requires append-only sequencing rather than overwriting an earlier unresolved event.
4. A design delta cannot be structurally reviewable without both supporting frozen trace and an explicit falsifier.
5. Context observations can be represented without a causal edge.

These are not retrospective theoretical benefits; they were exposed by constructing and checking the validation fixtures.

## Process assessment

Validation staging improves the process when applied at the promotion boundary.

Recommended integration:

```text
OBSERVATION
 -> TRACE FREEZE
 -> DESIGN DELTA (PROVISIONAL)
 -> GRAPH ENCODE
 -> STRUCTURAL VALIDATION
 -> RETEST
 -> REPLICATED | WITHDRAWN
 -> WARRANT REVIEW
```

Do NOT place structural validation between stimulus and human trace. That would add latency to the discovery loop and risk contaminating observation.

## Standing

- Integrate validation staging for evidence-graph/schema-affecting design deltas: YES.
- Require it for every conversational micro-observation: NO.
- Treat successful structural validation as proof that a cognitive claim is true: NO.
- Treat failure of structural validation as a reason to block promotion until repaired: YES.

This integration remains falsifiable: if repeated use adds substantial review cost without catching defects, preserving provenance, or improving legibility, narrow or withdraw the gate.
## Plain-language note: “dependency-capable run”

This phrase means: run the committed validation script in a computer/environment that is allowed to install and execute the external Python package it depends on, `pyshacl==0.40.1`.

The validation code itself is already written and committed. The current execution environment used during this session could inspect and structurally preflight the files, but it could not install PySHACL from the package index. Therefore:

- the **test harness exists**;
- the **test data exists**;
- the **expected pass/fail behavior is defined**;
- the **canonical PySHACL test has not yet been executed in this session environment**.

A “dependency-capable” environment could be a local computer, CI runner, GitHub Actions job, or other runtime with Python package-install access. Once PySHACL is installed there, the committed command can execute the canonical SHACL validation.

This is an execution-environment limitation, not a known defect in the graph or validator.

## Design delta: landing verification + dependency flags

### Observation

The phrase “dependency-capable run” did not fully land for the participant even though it was technically meaningful to the system.

### Provisional interpretation

Message delivery is not evidence of shared understanding. A critical dependency statement can be technically correct while remaining operationally ambiguous to the human.

### Graph update

Added:
- `LandingCheck` with states `UNVERIFIED | CONFIRMED | CLARIFIED | MISUNDERSTOOD | DEFERRED`;
- `DependencyFlag` with explicit dependency state, required stage, blocking scope, plain-language impact, resolution action, and fallback.

The current PySHACL limitation is now the first concrete dependency-flag example.

### Validation-stage result

The new design delta was passed through the staging process rather than only documented:
- ontology primitives added;
- SHACL shapes added;
- valid reference fixtures added;
- intentionally invalid landing/dependency fixtures added;
- machine-readable manifest expectations extended.

Canonical PySHACL execution remains blocked by the already-declared PySHACL execution dependency, so these new shapes remain PROVISIONAL until that dependency is satisfied and the canonical validator is run.

### Promotion test

Promote the landing lane only if repeated use demonstrates that selective landing checks reduce misunderstanding or false assumptions of completion without materially increasing friction.

Promote dependency flags if they reliably make blocked scope and resolution path clearer than free-form caveat language.

