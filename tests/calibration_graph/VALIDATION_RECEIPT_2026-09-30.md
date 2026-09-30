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
