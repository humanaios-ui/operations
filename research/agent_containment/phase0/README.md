# Agent containment Phase 0 — synthetic evidence bridge

This directory retains the synthetic scenario, reported result, and Python
policy model from the October 22, 2026 preliminary exercise. This is **not**
external-incident forensic evidence or a test of a production runtime.

The receipt is **self-reported** and contains a claimed hash-chain head, not
independent event rows or witness attestation. The counters for zero production
effects cannot establish actual deployment isolation.

The read-only adapter combines these inputs with the root Evidence Graph and
prints a derived projection in the repository's existing
`humanaios.graph.observation_projection.v0` format. It neither writes to
`EVIDENCE_GRAPH.json` nor changes any governance, execution, or receipt state.

## Reproduce locally (no network)

```sh
python3 research/agent_containment/phase0/phase0_sim.py
python3 research/agent_containment/phase0/independent_local_witness.py --check
python3 research/agent_containment/phase0/containment_evidence_adapter.py --check
python3 research/agent_containment/phase0/containment_evidence_adapter.py > /tmp/containment_projection.json
python3 -m unittest discover -s tests -p 'test_containment*.py' -v
```

The adapter labels synthetic results **unresolved** and crosswalk links
**inferred**. Existing root graph nodes are observations of *source-file
assertions*, not new independent proof of those assertions. The exact graph
bytes are identified by SHA-256 under `source.revision`; the included
synthetic scenario and result receive per-file SHA-256 references.

## Existing Evidence Graph crosswalk

- T06: attempted client Zone 2 claim → CT1 (independent authority) and FS1.
- T07/T08: attempted production receipt/store → C1 (participation is not authority).
- T09: unauthorized halt attempt → CT1.
- T11/T12: authorized halt and post-halt rejection → CT2 (sequence boundary).

The independently implemented local subprocess witness compares model results with
the recorded synthetic receipt, checks source-file integrity, and recomputes the
event hash/HMAC chain without invoking the model's `verify()`. Its Python audit
hook rejects Python-level file writes and socket/process use. The witness is
NOT an operating-system sandbox or a remote independent third party: native
code, external infrastructure, production bindings, and actual egress are
outside the experiment. Do not interpret "zero" counters as verified production
effects. The `jsonschema` dependency is mandatory for the adapter's contract
test; a missing dependency must make the test fail.

These crosswalks test ideas, not real production controls. No graph edge grants
authority. This is a read-only advisory artifact, not an authorized input to
Coordinator, ratification, deployment, or an external evidence register.

Next verification: independent execution with a witnessed, complete event log
and a separately constrained runtime. Until then, production containment is
**UNVERIFIED**.
