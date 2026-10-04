# Subject-Scoped Registry Query Plan

Issue #703 adds a planning-only query object for queryable registry Mines.

## Why this layer exists

The Colorado Great Colorado Payback Mine demonstrated that the machine can prove an official registry pathway exists without being able to represent the next claimant-specific epistemic question.

The missing step is:

```text
For explicitly supplied subject S,
query registry R
for zero or more candidate records.
```

That question must exist as a first-class object before #700 can authorize observation.

## Canonical progression

```text
REGISTRY MINE
  ↓
PATHWAY OPP
  ↓
RQY-* Subject-Scoped Registry Query Plan
  ↓
OAG-* Observation Authorization Gate
  ↓
QRC-* Query Execution Receipt
  ↓
RMO-* Registry Match Observation [0..N]
```

Only the `RQY-*` layer is implemented here.

## RQY-* contract

A registry query plan contains:

- registry Mine ID;
- registered pathway Opportunity ID;
- query class;
- privacy-safe `SUBJ-*` subject reference;
- subject kind;
- semantic query-field names;
- privacy classification;
- query-value persistence boundary;
- purpose;
- expected response class;
- zero-result semantics;
- match-result semantics;
- explicit-subject-request receipt flag;
- external-state-change invariant;
- planning/execution/authority state.

Every plan is initialized:

```text
planning_state = PLANNED
execution_state = NOT_AUTHORIZED
external_state_change = false
authority_effect = NONE
```

## Privacy boundary

The public plan API does not accept query values.

It accepts only semantic field names such as:

```text
owner_name
business_name
last_known_location
```

Actual names, locations, or other transport values remain:

```text
PRIVATE_RUNTIME_ONLY
```

A `SUBJ-*` token must be supplied by a privacy-preserving subject-binding layer. The public Resource Miner does not generate that token by hashing a person's name, email, SSN, DOB, or other identity data.

## Explicit request boundary

A plan cannot be created unless:

```text
explicit_subject_request = true
```

The planner fails closed otherwise.

This records that a subject-specific lookup was explicitly requested. It does not authorize the lookup.

## Mine/pathway binding

The planner verifies:

1. the Mine is `REGISTRY`;
2. the Mine is enabled;
3. the Mine declares a query contract;
4. the query class is supported;
5. every requested semantic field is allowed by the Mine;
6. query values are private-runtime-only;
7. the operation declares no external state change;
8. the pathway OPP belongs to the Mine's registered configured opportunity set.

Therefore an arbitrary foreign `OPP-*` cannot be substituted into an `RQY-*`.

## Result semantics

The initial unclaimed-property query class uses:

```text
expected_response_class =
  ZERO_OR_MORE_CANDIDATE_RECORDS

zero_result_semantics =
  NO_MATCH_OBSERVED_NOT_NO_ENTITLEMENT

match_result_semantics =
  CANDIDATE_RECORD_NOT_OWNERSHIP
```

Expanded invariants:

```text
NO_MATCH_OBSERVED != NO_ENTITLEMENT

MATCH_OBSERVED != OWNERSHIP
MATCH_OBSERVED != ELIGIBILITY
MATCH_OBSERVED != CLAIM_AUTHORIZED
MATCH_OBSERVED != FUNDS_RECOVERED
```

## Colorado specimen

The Colorado Great Colorado Payback Mine declares:

```text
query_class =
  UNCLAIMED_PROPERTY_OWNER_SEARCH

semantic_query_fields =
  owner_name
  business_name
  last_known_location

transport_field_mapping =
  PRIVATE_ADAPTER_ONLY
```

No registry search is executed by this layer.

## CLI

Example with a synthetic subject reference:

```bash
python3 -m resource_miner.cli plan-registry-query \
  --mine-id MINE-... \
  --pathway-opportunity-id OPP-... \
  --subject-ref SUBJ-AAAAAAAAAAAAAAAA \
  --subject-kind NATURAL_PERSON \
  --query-field owner_name \
  --query-field last_known_location \
  --explicit-subject-request
```

The command prints an `RQY-*` plan. It does not connect to or query the registry.

## Boundary for #700

#700 should receive a concrete `RQY-*` object and decide whether that exact query is eligible for bounded observation.

It should not authorize a vague `VRT-*` route.

Session graph: issue #703.
