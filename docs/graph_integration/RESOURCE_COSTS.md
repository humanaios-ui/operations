# Read-only measured graph resource costs (proposed Z1)

Purpose: add measured local costs to existing HumanAIOS graph observation. Keep canonical graphs unchanged. This is a stdout-only sidecar receipt, not a graph compiler, admission gate, router, new graph or policy input.

## How to run

From a local checkout of operations:

    python3 tools/graph_resource_observer.py --repo . --graph system_graph.json --system system_graph --context-id mac-local-1
    python3 tools/graph_resource_observer.py --repo . --graph system_graph.json --system system_graph --node-id Q --context-id mac-local-1
    python3 tools/graph_resource_observer.py --repo . --graph EVIDENCE_GRAPH.json --system evidence_graph --context-id mac-local-1
    python3 -m unittest discover -s tests -p 'test_graph_resource_observer.py' -v

All input graph files are read only. The result is JSON printed to stdout, not automatically committed or saved. Inputs are bounded regular JSON files inside the supplied repository, without symlinks or parent-path traversal. The 16 MiB cap and refusal states protect against unsupported input. This prototype does not parse YAML or RDF and does not automatically inspect private session files.

## What is observed

- The source system is a caller-selected label naming an EXISTING graph. It does not authenticate that identity.
- Source revision is the SHA-256 digest of exact input bytes, not a Git commit and not a claim of an admitted revision. All trials must agree on source revision and observed structural counts or no successful record is returned.
- Three independent samples are collected by default. Each samples actual elapsed wall time, process CPU time, and peak traced Python allocations for read, JSON parse, hash, structure counts, and optional incident-edge scan.
- The receipt carries median wall and CPU nanoseconds, peak traced allocations, input bytes, node and edge counts, an optional incident-edge count, UTC observation time, and a user-supplied pseudonymous execution context.
- authority_effect = NONE. read_only = true. No receipt authorizes execution, Z2 admission, Coordinator decisions, SCVC continuity or merged graph state.

## What remains unknown

Python allocation tracing is NOT total RAM usage or process RSS. Timing may include instrumentation overhead and cache effects. GPU utilization, disk IOPS, energy, network and financial cost are not measured. The graph may be malformed despite being countable; this observer does not replace its producer's schema and integrity tests. Unsupported inputs are REFUSED, never silently zero.

## Measurement experiment

Baseline: run at least three trials on an existing graph with a pinned content SHA-256 in a named local context. Comparison: run the same content and operation on a second named context. Compare medians, trial range, and traced allocations. Do not claim improvements from unmatched revisions or missing observations. Preserve the original per-trial data and provenance.

Do not promote the receipt into docs/graph_integration/observation_projection_v0.schema.json without a separately reviewed read-only adapter. Keep the existing graph producers and their authority boundaries intact. No protected CI, tool manifest, graph schema, governance, or Coordinator policy changes are introduced in this PR.

## Verification and next action

Standalone synthetic tests should pass; verify again in protected CI on the PR's exact head. After human review, measure system_graph.json and EVIDENCE_GRAPH.json on the Mac and on the new Windows desktop using unchanged inputs. Do not wire costs into Router Oracle decisions until matched-context evidence exists.
