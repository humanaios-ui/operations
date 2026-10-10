# Evidence Standing, Proposition Adjudication, and Verification Frontier

Resource Miner now separates proposition reconciliation from evidence adequacy.

```text
PRP-* observations
  ↓
PRS-* relationship state
  ↓
source-standing profiles
  ↓
PAD-* adjudication posture
  ↓
VFY-* verification frontier
```

## Why this layer exists

A proposition can be corroborated without having adequate evidence standing.

```text
two secondary sources agree
!=
primary evidence exists

official page exists
!=
machine classification is proven

different Mines
!=
independent origins

primary source present
!=
truth established
```

## SourceStandingProfile

A source-standing profile is scoped to an evidence origin and to the proposition types or predicates for which that origin has standing.

Initial source classes:

- `OFFICIAL_PRIMARY`
- `FIRST_PARTY_OPERATIONAL`
- `DIRECT_SOURCE`
- `SECONDARY_REPORT`
- `AGGREGATOR`
- `UNKNOWN`

Standing is not global prestige. A source may be primary for its own program status but have no standing for a HumanAIOS semantic classification derived from that page.

Every profile has `authority_effect=NONE`.

## PAD-* Proposition Adjudication

A `PAD-*` summarizes the evidence posture of one `PRS-*`.

Postures:

- `PRIMARY_SOURCE_PRESENT`
- `MULTI_ORIGIN_NO_PRIMARY`
- `NONPRIMARY_SOURCE_ONLY`
- `DERIVED_ONLY`
- `CONTESTED`
- `UNRESOLVED`
- `SOURCE_STANDING_UNKNOWN`

A PAD never promotes truth:

```text
truth_state         = NOT_DETERMINED
eligibility_state   = NOT_EVALUATED
warrant_state       = NOT_EVALUATED
authorization_state = NOT_REQUESTED
authority_effect    = NONE
```

## VFY-* Verification Frontier

A `VFY-*` is a deterministic description of missing evidence.

Gap types:

- `PRIMARY_SOURCE_MISSING`
- `DIRECT_EVIDENCE_MISSING`
- `CONFLICT_REQUIRES_RESOLUTION`
- `SOURCE_STANDING_UNKNOWN`
- `RELATION_UNRESOLVED`

A frontier item is an epistemic work request, not permission to browse, submit, purchase, test, contact, or otherwise act externally.

## Initial adjudication rules

1. A contested PRS emits `CONFLICT_REQUIRES_RESOLUTION`; no source is automatically selected as winner.
2. An unresolved PRS emits `RELATION_UNRESOLVED`.
3. If all member propositions are machine classifications or text extractions, the posture is `DERIVED_ONLY` and `DIRECT_EVIDENCE_MISSING` is emitted.
4. If no applicable primary source profile is present, `PRIMARY_SOURCE_MISSING` is emitted.
5. Unknown or out-of-scope source standing emits `SOURCE_STANDING_UNKNOWN`.
6. Applicable primary evidence can produce `PRIMARY_SOURCE_PRESENT`, but `truth_state` remains `NOT_DETERMINED`.

## Example

```text
Newsletter A: program status = open
Newsletter B: program status = open

PRS:
  CORROBORATED
  distinct origins = 2

PAD:
  MULTI_ORIGIN_NO_PRIMARY

VFY:
  PRIMARY_SOURCE_MISSING
  requested source class = OFFICIAL_PRIMARY
```

Contrast:

```text
Official program page:
  status = open

PAD:
  PRIMARY_SOURCE_PRESENT

truth_state:
  NOT_DETERMINED
```

The second result means the relevant primary source is present. It does not mean the proposition has passed all semantic, temporal, eligibility, or warrant checks.

## Persistence

The scheduled Mine cycle now persists:

```text
data/propositions.snapshot.jsonl
data/proposition-resolutions.snapshot.jsonl
data/proposition-adjudications.snapshot.jsonl
data/verification-frontier.snapshot.jsonl
data/opportunity-claims.snapshot.jsonl
data/opportunity-claim-events.jsonl
```

## Machine surfaces

- `resource_miner/source_standing.py`
- `resource_miner/adjudication.py`
- `data/source-standing.seed.json`
- `schemas/source-standing-profile.v1.schema.json`
- `schemas/proposition-adjudication.v1.schema.json`
- `schemas/verification-frontier-item.v1.schema.json`
- `tests/test_adjudication.py`

Session graph: issue #693.
