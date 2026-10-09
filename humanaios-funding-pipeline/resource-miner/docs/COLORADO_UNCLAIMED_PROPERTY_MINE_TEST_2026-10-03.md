# Colorado Great Colorado Payback — New Mine Test

**Test date:** 2026-10-03 (America/Chicago)  
**Session graph:** #701  
**Test PR:** #702  
**Mine:** Colorado Great Colorado Payback  
**Mine kind:** `REGISTRY`

## External source observation

User-supplied entrypoint:

`https://colorado.findyourunclaimedproperty.com/`

Observed canonical destination:

`https://unclaimedproperty.colorado.gov/`

The public source is the Colorado Great Colorado Payback / Colorado State Treasurer Unclaimed Property Division.

The test intentionally did not execute a claimant-name/business search and did not enter DOB, SSN/Tax ID, email, phone, mailing address, claim ID, or documents.

## Bounded Mine model

```text
MINE
Colorado Great Colorado Payback
  kind = REGISTRY
  roles = OPPORTUNITY_SOURCE | EVIDENCE_SOURCE
  origin = unclaimedproperty.colorado.gov
  observation_scope = PUBLIC_LANDING_PATHWAY_ONLY
  authority_effect = NONE
```

The Mine emits one bounded opportunity:

```text
Colorado Great Colorado Payback — claimant asset-recovery pathway
```

This means only that an official recovery mechanism exists.

It does not mean:

```text
PROPERTY_EXISTS_FOR_CLAIMANT
CLAIMANT_OWNS_PROPERTY
CLAIMANT_IS_ELIGIBLE
CLAIM_IS_AUTHORIZED
CLAIM_WAS_SUBMITTED
FUNDS_WERE_RECOVERED
```

## Deterministic graph result

The specimen produced pathway-level propositions including:

- `OPPORTUNITY_EXISTS`
- `CURRENTLY_AVAILABLE`
- `RESOURCE_TYPE`

The official Colorado origin has scoped `OFFICIAL_PRIMARY` standing for pathway existence/currentness/status only.

Result:

```text
OPPORTUNITY_EXISTS
  -> PAD PRIMARY_SOURCE_PRESENT

CURRENTLY_AVAILABLE
  -> PAD PRIMARY_SOURCE_PRESENT

RESOURCE_TYPE
  -> current value = general_resource
  -> PAD DERIVED_ONLY
```

## Finding 1 — taxonomy gap

The configured source category is `asset_recovery`, but Resource Miner's current taxonomy does not contain an `asset_recovery` resource type.

The machine therefore safely falls back to:

`RESOURCE_TYPE = general_resource`

This is a real ontology gap, not a transport failure.

## Finding 2 — missing subject-scoped registry-query primitive

The current proposition ontology has no:

- `CLAIMANT_MATCH`
- `PROPERTY_MATCH`
- subject-scoped registry-query object

Therefore the machine can establish that the official pathway exists, but it cannot yet represent this next epistemic question:

```text
For an explicitly identified claimant,
does the official registry currently return
zero or more candidate property records?
```

Because the question itself is absent from the graph, no `VFY-*`, `VWK-*`, or `VRT-*` can yet represent the claimant lookup.

This is the primary architectural finding from the test.

## Finding 3 — source-standing routing defect exposed and fixed

The test exposed a separate defect.

When an evidence origin was known but its standing was out of scope for a proposition, `PAD-*` correctly retained it as an `unknown_origin_key`, but `VWK-*` dropped the origin while compiling `ASSESS_SOURCE_STANDING`.

The queue now preserves that origin.

Correct behavior:

```text
SOURCE_STANDING_UNKNOWN
  origin = unclaimedproperty.colorado.gov
  ↓
ASSESS_SOURCE_STANDING
  candidate_origin_keys =
    [unclaimedproperty.colorado.gov]
  ↓
SOURCE_STANDING_REVIEW
```

The route remains:

`execution_state = NOT_AUTHORIZED`

## Privacy and authority boundary

The Mine configuration explicitly requires an explicit claimant-specific request before a registry search.

This test did not:

- infer claimant identity from memory;
- query a natural person's name;
- query a business name for a property match;
- enter claimant personal information;
- check private claim status;
- upload documents;
- submit a claim;
- treat registry access as entitlement.

## Regression result

Exact tested head before this report commit:

`993830c7807c6775514aa10f7ad210c6778838f7`

Result:

```text
Ran 121 tests
OK
```

The persistent Mine contract also passed:

- Colorado Mine present;
- Mine state = `RESOLVED`;
- exactly one Colorado pathway-level opportunity emitted;
- `opportunity_kind = unclaimed_property_recovery_pathway`;
- `eligibility_assessed = false`;
- `eligibility_status = UNASSESSED`.

## Architectural conclusion

The existing Resource Miner stack correctly handles the **registry as a recovery pathway** and correctly refuses to infer claimant-specific value.

However, queryable registries reveal a missing layer between `VRT-*` and actual observation:

```text
REGISTRY MINE
  ↓
PATHWAY OPP
  ↓
SUBJECT-SCOPED QUERY PLAN
  ↓
OBSERVATION AUTHORIZATION
  ↓
QUERY RECEIPT
  ↓
0..N REGISTRY MATCH OBSERVATIONS
  ↓
candidate recovery opportunities
  ↓
PRP -> PRS -> PAD -> VFY replay
```

That subject-scoped query layer should be designed before automatic observation under #700.
