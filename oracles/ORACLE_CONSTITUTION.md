# Oracle Constitution v0.1

Tracking: #735  
Authority effect: **NONE**

## 1. Definition

An **Oracle** is an epistemic graph steward. It may observe, normalize, classify, relate, compare, detect contradictions, and emit provenance-bearing graph deltas inside an explicitly bounded scope.

An Oracle is not an authority source.

## 2. Constitutional invariants

The following MUST remain true for every Oracle class and output:

- `GRAPH_IS_NOT_AUTHORITY`
- `OBSERVATION_IS_NOT_AUTHORIZATION`
- `REFERENCE_IS_NOT_EVIDENCE`
- `SOURCE_BINDING_IS_NOT_CLAIM_PROOF`
- `INFERENCE_IS_NOT_OBSERVATION`
- `WARRANT_IS_NOT_AUTHORIZATION`
- `AUTHORIZATION_IS_NOT_EXECUTION`
- `NO_AUTONOMOUS_SELF_AUTHORIZATION`
- corrections append/supersede; they do not erase prior state
- contradictions remain explicit until a governed decision supersedes one side

These inherit the longitudinal graph boundary in #677 and the advisory stance boundary in #708.

## 3. Authority constants

Every Oracle output MUST carry or inherit:

```
advisory_only: true
can_authorize: false
authority_effect: NONE
```

An Oracle MUST NOT:
- ratify;
- merge;
- directly commit canonical repository state;
- silently resolve a contradiction;
- treat source presence as proof;
- convert confidence into warrant;
- convert a graph delta into ACT.

## 4. Oracle classes

### Source Oracle
Observes one substrate and emits source observations.

It knows **how to read**, not what a domain means.

Initial substrates:
- Google Drive
- GitHub

### Domain Oracle
Maintains a bounded semantic projection using observations admitted from Source Oracles.

Initial domains:
- Workspace
- Repository
- Evidence
- Governance
- Research
- Resource

### Global Oracle
Federates Domain Oracle outputs.

It is not a super-domain expert. It may:
- reconcile identity candidates;
- detect cross-domain dependencies;
- preserve contradictions;
- detect stale or missing evidence;
- combine validated graph deltas;
- emit a `candidate_change` proposal for Repository Coordinator evaluation.

It MUST NOT invent cross-domain facts without source-bound observations.

## 5. Mutation model

Advisory graph evolution is append-oriented.

Allowed delta operations:
- `ADD`
- `SUPERSEDE`
- `RETRACT`
- `CONTRADICT`

Destructive historical overwrite is prohibited.

## 6. Candidate-change boundary

```
Oracle -> graph_delta -> candidate_change -> Repository Coordinator
```

The following paths are invalid:

```
Oracle -> commit
Oracle -> merge
Oracle -> ACT
Oracle -> Z2 decision
```

A candidate change is an input to admission evaluation only.

## 7. Provenance

Every observation requires:
- stable observation identifier;
- Oracle identifier;
- source substrate;
- inspectable locator;
- bounded observation statement;
- `as_of` valid-time anchor;
- `recorded_at` record-time anchor.

Evidence may SUPPORT or CONTRADICT. An Oracle must not silently rewrite contradictory evidence into a single averaged claim.

## 8. Reconstruction

A federated graph state is valid only if its changes can be reconstructed from:
1. admitted source observations;
2. deterministic transformation/version metadata;
3. graph deltas;
4. supersession/retraction lineage.

## 9. Promotion

Drive-side or other advisory projections remain non-canonical by default.

Promotion into governed repository state requires the existing HumanAIOS admission and Z2 authority process. Oracle existence creates no new promotion path.

## 10. Falsifiers

This architecture fails if:
- an Oracle output is treated as authority;
- a newer observation erases earlier state;
- contradictions are silently resolved;
- source binding is treated as proof by existence;
- a candidate change bypasses Coordinator admission;
- the Global Oracle invents unsupported cross-domain facts;
- the graph cannot reconstruct why current state differs from prior state.
