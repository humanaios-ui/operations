# Resource-plan combination contract v1

Status: PROPOSED implementation for HumanAIOS review; not policy ratification,
admission, eligibility, acquisition, execution, merge or deployment authority.

## Existing behavior and compatibility

Before this change, planning.py supports only flat alternative substitutions:
ADEQUATE wins over PARTIAL, then UNKNOWN (including no assessments), then solely
INADEQUATE. A single adequate alternative can satisfy a requirement even when
another resource is inadequate. PR #909 characterizes this behavior; current main
already includes overlapping planning regressions. This change does not modify
that draft PR or the separate On-Track safeguard in draft PR #943.

Unversioned valid plans retain that alternative behavior. Existing seeds are not
migrated. New fields require explicit `schema: humanaios.resource-plan.v1`.
Unknown versions fail closed; there is no automatic cumulative interpretation.
In v1, omitted combination_mode means ALTERNATIVES. V1 enums are canonical
uppercase and mine_external must be a boolean. Malformed collections/IDs,
duplicate graph references, and nested non-NONE authority claims now fail closed
also in legacy validation; previously tolerated malformed input is not a supported
compatibility promise. No new runtime dependency is introduced.

The structural schema is `schemas/resource-plan.v1.schema.json` (Draft 2020-12).
`validate_resource_plan` is the runtime validator, including cross-record
uniqueness, membership and reference checks that JSON Schema cannot express.
Extension metadata remains permitted at plan/node/assessment level; its presence
has no action semantics. Component objects have a closed field set.

## Explicit grouping

```json
{
  "schema": "humanaios.resource-plan.v1",
  "plan_id": "RP-SYNTHETIC",
  "authority_effect": "NONE",
  "controlled_resources": [{"resource_id": "R-A"}, {"resource_id": "R-B"}],
  "resource_requirements": [{
    "requirement_id": "Q-1",
    "resource_types": ["compute_credit"],
    "resolution_mode": "HYBRID",
    "activation_state": "ACTIVE",
    "mine_external": true,
    "combination_mode": "ALL_REQUIRED",
    "required_components": [{"component_id": "C-COMPUTE"}, {"component_id": "C-STORAGE"}]
  }],
  "substitution_assessments": [
    {"requirement_id": "Q-1", "component_id": "C-COMPUTE", "controlled_resource_id": "R-A", "status": "ADEQUATE"},
    {"requirement_id": "Q-1", "component_id": "C-STORAGE", "controlled_resource_id": "R-B", "status": "UNKNOWN"}
  ]
}
```

This resolves UNKNOWN, not SATISFIED. Components are declared independently of
assessments so absence cannot shrink the required set. Component IDs must be
globally unique, cannot collide with graph node IDs, and belong to exactly one
requirement. ALL_REQUIRED must declare at least one component; each assessment
must name a component owned by its referenced requirement. Flat and grouped
assessments cannot mix. Missing or foreign component references are errors.

Within each component, resource assessments remain ALTERNATIVES. Across components,
ALL_REQUIRED is cumulative. Duplicate (requirement, component, resource) tuples
are rejected even with different statuses; flat alternatives retain uniqueness
on (requirement, resource). The same resource may be assessed independently for
different components: this asserts per-component fitness, not simultaneous
capacity allocation or a reservation. Scarce capacity/time sharing is unmodeled.

## Deterministic proposed policy

1. Validate the full plan, even when a requirement is INACTIVE/CONDITIONAL.
2. INACTIVE and CONDITIONAL override valid adequacy assessments.
3. ALTERNATIVES (also within each component): ADEQUATE > PARTIAL > UNKNOWN >
   INADEQUATE. No assessments means UNKNOWN.
4. ALL_REQUIRED over component results: any INADEQUATE establishes a gap;
   otherwise any UNKNOWN means UNKNOWN; otherwise any PARTIAL means PARTIAL;
   otherwise every declared component is ADEQUATE, so SATISFIED.
5. A gap maps to CONFIRMED for ACQUIRE_EXTERNAL/HYBRID and
   INTERNAL_COMPOSITION_GAP for COMPOSE_INTERNAL.

Thus INADEQUATE + UNKNOWN is a confirmed gap for cumulative components, whereas
UNKNOWN + INADEQUATE remains UNKNOWN for alternative resources. PARTIAL + UNKNOWN
is UNKNOWN cumulatively but PARTIAL for alternatives. A missing assessment is
UNKNOWN, not an invalid group or proof of inadequacy. Resolution order is stable
under assessment/component permutations.

## Export and authority

Existing export filters remain: mine_external must permit export; SATISFIED,
INACTIVE and INTERNAL_COMPOSITION_GAP are excluded. UNKNOWN, PARTIAL, CONFIRMED
and informational CONDITIONAL may be exported. Export is the aggregate deficit,
not a component allocation or work order. Authority remains NONE. No planning
status authorizes outreach, spending, applications, deployments or other actions.
Versioned resolved plans retain their schema/grouping; legacy resolved objects do
not acquire a schema field. Resolution and export do not mutate their inputs;
returned nested data is detached from source data.

## Decisions for Carly before admission

Ratify or revise: opt-in schema/version and names; nested required-component
grouping; alternative-resource semantics within a component; cumulative
INADEQUATE > UNKNOWN > PARTIAL > ADEQUATE precedence; missing assessment as UNKNOWN;
shared-resource fitness without allocation guarantees; and continued informational
conditional exports. Do not infer ratification from this document or passing tests.
Coordinator policy, ledger, governance, graph, routing weights, source adapters,
On-Track code and deployed behavior remain untouched.
