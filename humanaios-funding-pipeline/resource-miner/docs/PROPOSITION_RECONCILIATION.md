# Cross-Mine Proposition Reconciliation

Resource Miner can now relate independent observations without collapsing multiple sources into automatic truth.

## Canonical chain

```text
Mine A -> OPP-A -> PRP-A --\
                         \
                          -> PRS-* Proposition Resolution Set
                         /
Mine B -> OPP-B -> PRP-B --/
```

The source propositions remain intact. Reconciliation creates a separate, non-authoritative relationship layer.

## Resolution identity

Each `PRP-*` carries a `resolution_subject_key`.

That key is derived from the bounded opportunity identity and kind, or may be explicitly supplied by a source adapter when two different transports are known to refer to the same real-world subject.

The `PRS-*` identity is derived from:

```text
resolution_subject_key
+ proposition_type
+ predicate
```

Membership changes do not change the `PRS-*` identity.

## Relation vocabulary

- `SAME_AS` — same subject, proposition type, predicate, and normalized object.
- `SUPPORTS` — independent Mines asserted the same normalized proposition.
- `CONTRADICTS` — safely detectable mutually exclusive assertions conflict.
- `QUALIFIES` — reserved for explicit qualification relationships.
- `SUPERSEDES` — a later observation from the same Mine replaces an earlier value for a temporal predicate without deleting it.
- `CONTEXT_FOR` — compatible multi-valued propositions may coexist.
- `UNRESOLVED` — the machine can see the propositions belong together but cannot safely infer their relationship.

## Resolution states

```text
SINGLE_SOURCE
CORROBORATED
CONTESTED
QUALIFIED
SUPERSEDED
UNRESOLVED
```

None of these states means `SUPPORTED` truth.

A corroborated set means only that multiple independent evidence origins made the same normalized assertion. Different Mines can still share one origin, such as a Gmail message and an API record emitted by the same organization.

## First-pass deterministic rules

1. Same scope + same predicate + same normalized object:
   - `SAME_AS`;
   - plus `SUPPORTS` only when the evidence-origin keys differ.
2. Exclusive boolean assertions observed at the same observation time with opposite values:
   - `CONTRADICTS`.
3. Later temporal value from the same Mine:
   - `SUPERSEDES`.
4. Multi-valued classifications such as resource type, affordance, applicant type, or cash mentions:
   - `CONTEXT_FOR`; values may coexist.
5. Any relation the machine cannot safely infer:
   - `UNRESOLVED`.

## Non-authority invariant

Every `PRS-*` has:

```text
truth_state         = NOT_DETERMINED
eligibility_state   = NOT_EVALUATED
warrant_state       = NOT_EVALUATED
authorization_state = NOT_REQUESTED
authority_effect    = NONE
```

Therefore:

```text
MULTIPLE_SOURCES != AUTOMATIC_TRUTH
SOURCE_COUNT != CONFIDENCE
SOURCE_TRANSPORT_COUNT != INDEPENDENT_ORIGIN_COUNT
CORROBORATED != SUPPORTED
CONTESTED != FALSE
SUPERSEDED != DELETE_HISTORY

RECONCILIATION != ELIGIBILITY
RECONCILIATION != WARRANT
RECONCILIATION != AUTHORIZATION
```

## Persistence

The scheduled Mine workflow writes:

```text
data/propositions.snapshot.jsonl
        ↓
data/proposition-resolutions.snapshot.jsonl
        ↓
data/opportunity-claims.snapshot.jsonl
        ↓
data/opportunity-claim-events.jsonl
```

The reconciliation snapshot is derived and replayable from the current PRP set. It is not an authority ledger.

## Machine surfaces

- `resource_miner/reconciliation.py`
- `schemas/proposition-relation.v1.schema.json`
- `schemas/proposition-resolution-set.v1.schema.json`
- `tests/test_reconciliation.py`

Session graph: issue #691.
