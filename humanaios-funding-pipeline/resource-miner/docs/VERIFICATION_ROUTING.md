# Verification Routing

The verification work queue describes what evidence work should happen next. The verification-routing layer determines which observation capability, if any, could satisfy that work.

```text
VFY-* gap
  ↓
VWK-* planned epistemic work
  ↓
VRT-* verification route
```

## Route types

- `EXISTING_MINE_REOBSERVE` — a persistent Mine already declares the relevant evidence origin.
- `KNOWN_ORIGIN_REVIEW` — the evidence origin is known but no Mine is currently bound to it.
- `DISCOVERY_REQUIRED` — no bounded source target is known; new source discovery is required.
- `RESOLVER_REQUIRED` — the work requires explicit conflict/resolver handling rather than source voting.
- `SOURCE_STANDING_REVIEW` — the evidence origin itself needs scoped standing review.

## Mine capability bindings

Persistent Mines may declare privacy-safe `evidence_origins` in their config.

Example:

```text
Microsoft for Startups
  evidence_origins:
    - learn.microsoft.com
    - www.microsoft.com
```

This means the Mine can observe those origins. It does not change their evidence standing and does not grant permission to execute a route.

## Initial routing rules

| VWK operation | VRT result |
| --- | --- |
| DISCOVER_PRIMARY_SOURCE | DISCOVERY_REQUIRED |
| SEEK_DIRECT_EVIDENCE + bound origin | EXISTING_MINE_REOBSERVE |
| SEEK_DIRECT_EVIDENCE + known unbound origin | KNOWN_ORIGIN_REVIEW |
| SEEK_DIRECT_EVIDENCE + no origin | DISCOVERY_REQUIRED |
| RESOLVE_CONFLICT | RESOLVER_REQUIRED |
| ASSESS_SOURCE_STANDING | SOURCE_STANDING_REVIEW |
| DISAMBIGUATE_RELATION | DISCOVERY_REQUIRED |

Conflict work never auto-selects a winning source. Known origins are retained as context only.

## Capability is not authority

Every route carries:

```text
capability_state = ...
execution_state = NOT_AUTHORIZED
authority_effect = NONE
```

The core invariant is:

```text
CAPABILITY_AVAILABLE != AUTHORIZED
ROUTE_FOUND != EXECUTED
EXISTING_MINE != PERMISSION_TO_USE
DISCOVERY_REQUIRED != SEARCH_EXECUTED
RESOLVER_REQUIRED != RESOLVED
```

## Persistence

The scheduled Mine cycle now persists:

```text
data/verification-work-queue.snapshot.jsonl
data/verification-routes.snapshot.jsonl
```

## Machine surfaces

- `resource_miner/verification_routing.py`
- `schemas/verification-route.v1.schema.json`
- `tests/test_verification_routing.py`
- `data/mines.seed.json` evidence-origin bindings

Session graph: issue #697.
