# Conformance Run — Q-MESH-LOCAL-COORDINATION-01

**Status:** B.0 Empirical Verification evidence. Z1 candidate, no Z2 hash.
**Pin (HISTORICAL_RECORD):** `operations` @ `44347b79b1d6351bd10bbb5fb6c45b9ead6bd42e`
**Reproduce:**

```bash
python3 mesh/conformance/validate_mesh.py
python3 mesh/conformance/run_constitution_check.py
```

Both were run before this file was written. The outputs below are pasted verbatim from
that run, not transcribed. Neither script tunes its inputs toward a clean result: the
validator asserts failure for eight mutations that must be refused, and the constitution
run reports whatever `tools/agents/_shared/constitution_checker.py` returns.

---

## 1. Schema validation and control demonstration

```
validate_mesh v0.1.0
schema: mesh/practice_local.schema.json

positive cases (3 records on disk):
  PASS  mesh/practices/grok-crossref/practice.yaml
  PASS  mesh/practices/humanaios/practice.yaml
  PASS  mesh/practices/website/practice.yaml

negative cases (8 controls demonstrated):
  PASS  additionalProperties: false rejects an undeclared key — refused
  PASS  authority.grants_authority cannot be set true — refused
  PASS  resolution.class is a closed vocabulary — refused
  PASS  a record cannot drop its falsifier — refused
  PASS  purpose_filter is a closed vocabulary (P5) — refused
  PASS  provenance.pinned_sha must be a 40-hex sha — refused
  PASS  temporal_class cannot be an internal work deadline — refused
  PASS  edges relation is a closed vocabulary — refused

RESULT: PASS — all records valid; all controls demonstrated to refuse
```

Exit code: 0.

The eight negative cases are the P19 evidence — the schema controls are shown to refuse,
not asserted to exist. Case 1 is falsifier 4 in `MESH_LOCAL_CHARTER_V0_1.md` §6, carried
from the "schema soft smuggling" finding on PR #451.

---

## 2. Constitution run

```
run_constitution_check v0.1.0
constitution: HumanAIOS Constitution — 22 Principles (v1.0, 22 principles)

== check_commit ==
  [3 files] docs(mesh): local mesh coordination charter and record schema
      clean
  [6 files] docs(mesh): practice records for humanaios, website, grok-crossref
      clean
  [6 files] docs(mesh): cross-reference register and conformance evidence
      clean

== check_decision_log ==
  clean

== check_finding_log ==
  clean

== check_artifact_graph ==
  15 artifacts, types: assumption, dead_end, decision, finding, unknown
  clean

RESULT: 0 violation(s)
```

Exit code: 0.

### What this run does and does not establish

It establishes that the checks implemented in `constitution_checker.py` — P8 promotional
language, P5 purpose, P-COMMIT-DISCIPLINE granularity, P-T10 overclaim, P-TRANSPARENCY,
P-T2 zone, P-HUMILITY confidence, P3 hedged language, P-ARTIFACT-BREADTH type diversity and
P-GRAPH orphan ratio — return clean against this drop.

It does **not** establish conformance to all 22 principles. The checker implements a
subset; most `runtime_check` names in `constitution.json` have no corresponding
implementation in that module. A clean run is evidence about the implemented checks and
silence about the rest. Reading it as full constitutional conformance would be the
overclaim P-T10 exists to catch.

It also does not read the `/empirica-constitution` plugin text, which is not reachable from
the session that produced this evidence. See `MESH_LOCAL_CHARTER_V0_1.md` §0.

### Commit granularity

P-COMMIT-DISCIPLINE refuses a commit touching more than 10 files. The three commits above
carry 3, 6 and 6 files. The drop was split to satisfy the check rather than landed as one
commit of 15.
