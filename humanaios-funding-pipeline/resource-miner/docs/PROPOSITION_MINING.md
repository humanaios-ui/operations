# Proposition Mining

Resource Miner increasingly treats source records as **evidence containers** and mines bounded candidate propositions from them.

## Canonical chain

```text
RESOURCE MINE
  -> SOURCE OBSERVATION / NORMALIZED RECORD
  -> RESOURCE OPPORTUNITY          OPP-*
  -> PROPOSITION CANDIDATE         PRP-*
  -> EPISTEMIC CLAIM               CLM-*
  -> CLAIM EVALUATION EVENTS       CEV-*
```

The source page, repository issue, API response, feed item, or program record is not itself the claim.

## Invariants

```text
SOURCE_RECORD != PROPOSITION
PROPOSITION != CLAIM
CLAIM != FACT
OPPORTUNITY != PROPOSITION

ONE_SOURCE_RECORD -> MANY_PROPOSITIONS
ONE_OPPORTUNITY -> MANY_PROPOSITIONS
MANY_SOURCE_RECORDS -> ONE_SEMANTIC_PROPOSITION
DIFFERENT_OBJECT_VALUES -> DIFFERENT_PROPOSITIONS

EXTRACTION_CONFIDENCE != TRUTH_CONFIDENCE
CLASSIFICATION != VERIFIED_EXTERNAL_FACT
TEXT_EXTRACTION != VERIFIED_TERM
PROPOSITION_DISCOVERY != ELIGIBILITY
PROPOSITION_DISCOVERY != AUTHORIZATION
```

## Identity

A proposition ID is derived from:

```text
opportunity_id
+ proposition_type
+ predicate
+ normalized object value
```

Example:

```text
OPP-A
  -> PRP-1  exists = true
  -> PRP-2  currently_available = true
  -> PRP-3  resource_type = compute_credit
  -> PRP-4  potential_affordance = compute_capacity
  -> PRP-5  represented_deadline = 2026-10-31
```

Changing a page title does not change a proposition ID. Changing the semantic object value does.

## Initial deterministic proposition kinds

- `OPPORTUNITY_EXISTS`
- `CURRENTLY_AVAILABLE`
- `RESOURCE_TYPE`
- `AFFORDANCE`
- `DEADLINE`
- `CASH_MENTION`
- `APPLICANT_TYPE`
- `STATUS`

The first implementation mines only normalized structure and direct observation evidence. It does not use open-ended LLM inference.

## Epistemic roles

A proposition candidate records how it was produced:

- `OBSERVATION` — direct observation of an opportunity/current surface;
- `CLASSIFICATION` — Resource Miner assigned a category or affordance;
- `TEXT_EXTRACTION` — a bounded value was extracted from source text;
- `SOURCE_ASSERTION` — reserved for directly represented source assertions.

This matters because extraction/classification does not establish truth.

For example:

```text
PRP: potential_affordance = compute_capacity
epistemic_role: CLASSIFICATION
CLM TERMS: UNKNOWN
```

The claim remains unverified until evidence evaluates the proposition itself.

## Claim state

Proposition-bound claims use `claim_type=OPPORTUNITY_PROPOSITION`.

The claim's overall state depends on the proposition being evaluated. Parent-opportunity existence/currentness provide context but cannot accidentally promote an unrelated classification proposition to `SUPPORTED`.

Thus:

```text
OPP exists = SUPPORTED
OPP current = SUPPORTED
PRP resource_type = compute_credit
PRP truth = UNKNOWN

=> CLM overall = OBSERVED, not SUPPORTED
```

## Persistence

Daily Mine resolution now persists:

- `data/opportunities.snapshot.jsonl` — OPP layer;
- `data/propositions.snapshot.jsonl` — PRP layer;
- `data/opportunity-claims.snapshot.jsonl` — CLM projection;
- `data/opportunity-claim-events.jsonl` — append-only CEV history.

## Machine surfaces

- `resource_miner/proposition.py`
- `schemas/proposition-candidate.v1.schema.json`
- `tests/test_proposition_mining.py`
