# Epistemic Attractor Test 002 — A/B Research Comparison

Status: PROVISIONAL PERFORMANCE TEST  
Date: 2026-09-30  
Tracker: #595

## Test question

Does an attractor-generated multi-intent research pass expose materially more useful graph-changing information than an ordinary free-form search over the same unresolved state?

Seed state:
`DependencyFlag(pyshacl==0.40.1, UNSATISFIED, required_for=canonical SHACL validation)`

## Arm A — ordinary search

Query:
`pyshacl install validation`

Observed candidate classes:
- package installation instructions;
- command-line validation usage;
- basic project description.

Useful output:
- install with pip;
- CLI validation exists;
- virtualenv installation is documented.

Limit:
The ordinary query mostly answered “how do I install/run it?” It did not itself force discovery of alternatives, breaking changes, hidden runtime assumptions, or challenge evidence.

## Arm B — attractor multi-intent search

Generated intents:
- SATISFY_DEPENDENCY
- SEEK_CONTRADICTION
- SEEK_ALTERNATIVE_EXPLANATION
- SEEK_PRIOR_ART
- PROBE_COMPRESSION_LOSS

Representative external findings:

1. Package/version reality:
   - PyPI confirms pyshacl 0.40.1 exists and publishes a Python 3 universal wheel.

2. Compatibility / change surface:
   - project release information documents breaking changes in the 0.40 line, including removal of `rdflib.ConjunctiveGraph` support and raised minimum RDFLib dependencies.

3. Alternative execution path:
   - project documentation describes Docker execution, which means “pip install access” is not the only possible route to canonical validation.

4. Alternative validator:
   - Apache Jena provides a separate SHACL implementation with command-line validation.

5. Current project uncertainty:
   - open project issues exist, including test-suite/run-mode questions, showing that “validator installed” is not equivalent to “all validation behavior is settled.”

## Comparison

| Metric | Arm A ordinary | Arm B attractor |
|---|---:|---:|
| Direct dependency-resolution facts | yes | yes |
| Alternative execution paths | weak/not surfaced | yes |
| Alternative validator | not surfaced | yes |
| Breaking/compatibility signals | not surfaced | yes |
| Challenge evidence | not surfaced | yes |
| Compression subdependencies exposed | partial | yes |
| Search complexity | lower | higher |
| Review burden | lower | higher |

## Result

The attractor arm produced more graph-relevant categories of evidence for this seed, especially alternatives, incompatibility/challenge information, and decomposition of the vague dependency.

This is evidence of **coverage improvement in one controlled case**, not a general retrieval-performance claim.

## Process update candidate

Use ordinary retrieval when the information need is narrow and well-specified.

Escalate to attractor multi-intent research when one or more of these are true:
- unresolved dependency blocks promotion;
- a node is PROVISIONAL and needs falsification;
- a compression residue has HIGH loss risk;
- an omission signal affects action/warrant;
- a contradiction or version-watch exists;
- ordinary retrieval does not change the graph state.

## Falsifier

Withdraw or narrow attractor escalation if repeated A/B tests show that added search breadth mostly increases noise/review effort without increasing useful contradictions, alternatives, omission discovery, or accepted graph mutations.
