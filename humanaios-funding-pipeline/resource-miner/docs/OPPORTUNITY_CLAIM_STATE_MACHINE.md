# Opportunity Claim Epistemic State Machine

## Purpose

Opportunity Claim v1 is now replayable from an append-only sequence of `humanaios.claim-evaluation-event.v1` events.

The current state is a projection:

```text
CLAIM_ASSERTED
  -> EVIDENCE_RECORDED*
  -> FALSIFIER_EVALUATED*
  -> FACET_RESOLVED*
  -> replay
  -> current OpportunityClaim
```

No current-state mutation is authoritative unless it can be reproduced from the event chain.

## Event chain

Every event carries:

- `event_id` — deterministic hash of the complete event body;
- `sequence`;
- `previous_event_id`;
- claim and opportunity identity;
- actor type/id;
- method;
- affected facet;
- prior overall/facet state;
- resulting overall/facet state;
- evidence IDs and evidence payload;
- uncertainty/confidence;
- `authority_effect=NONE`.

Replay validates event hashes, chain continuity, claim identity, prior-state assertions, and resulting-state assertions.

## Event types

### CLAIM_ASSERTED

Genesis event. Contains the complete seed Opportunity Claim so replay can reconstruct state without an external current-state file.

### EVIDENCE_RECORDED

Adds provenance-bearing supporting, contradicting, falsifying, or contextual evidence.

### FALSIFIER_EVALUATED

Evaluates a pre-registered falsifier as `OBSERVED | NOT_OBSERVED | INCONCLUSIVE` through evidence.

### FACET_RESOLVED

Allows a downstream resolver to resolve a facet. `ELIGIBILITY` and `ATTAINABILITY` cannot be resolved by a generic SYSTEM actor; they require a RESOLVER, AUTHORITY, or HUMAN event producer.

## Append-only persistence

`data/opportunity-claim-events.jsonl` is the longitudinal ledger.

Scheduled Mine resolution reconciles current observations against replayed histories:

1. unseen claim -> append `CLAIM_ASSERTED`;
2. known claim + novel evidence -> append `EVIDENCE_RECORDED`;
3. identical observation -> append nothing;
4. existing bytes are preserved; new records are appended.

The current `data/opportunity-claims.snapshot.jsonl` remains a cache/projection. The event ledger is the reconstructable record.

## Invariants

```text
CURRENT_STATE = REPLAY(EVENT_HISTORY)

EVENT_HASH_MISMATCH => REJECT_REPLAY
BROKEN_PREVIOUS_EVENT => REJECT_REPLAY
PRIOR_STATE_MISMATCH => REJECT_REPLAY
RESULTING_STATE_MISMATCH => REJECT_REPLAY

DISCOVERY_EVENT != ELIGIBILITY_RESOLUTION
EVIDENCE_EVENT != AUTHORIZATION
CLAIM_REPLAY != AUTHORITY
EVENT_LEDGER != EXECUTION_LOG
```

## Machine surfaces

- `resource_miner/claim_state_machine.py`
- `schemas/claim-evaluation-event.v1.schema.json`
- `tests/test_claim_state_machine.py`
