# Verification Frontier to Epistemic Work Queue

The verification frontier identifies missing evidence. The work queue converts each open gap into a deterministic next-research operation without granting permission to execute it.

```text
PAD-* evidence posture
  ↓
VFY-* verification gap
  ↓
VWK-* verification work item
```

## Work item contract

Every `VWK-*` carries:

- the originating `VFY-*`, `PAD-*`, and `PRS-*`;
- the bounded subject key;
- a deterministic operation class;
- any already-known candidate evidence origins;
- the requested source class;
- an explicit closure condition;
- `planning_state=PLANNED`;
- `execution_state=NOT_AUTHORIZED`;
- `authority_effect=NONE`.

## Operation mapping

| Gap | Work operation |
| --- | --- |
| PRIMARY_SOURCE_MISSING | DISCOVER_PRIMARY_SOURCE |
| DIRECT_EVIDENCE_MISSING | SEEK_DIRECT_EVIDENCE |
| CONFLICT_REQUIRES_RESOLUTION | RESOLVE_CONFLICT |
| SOURCE_STANDING_UNKNOWN | ASSESS_SOURCE_STANDING |
| RELATION_UNRESOLVED | DISAMBIGUATE_RELATION |

The queue does not execute these operations. It describes the epistemic work required next.

## Important boundaries

```text
WORK_PLAN != EXECUTION
PLANNED != AUTHORIZED
READ_ONLY_CANDIDATE != PERMISSION
VERIFICATION != WARRANT
VERIFICATION != CONSEQUENT_ACTION
QUEUE_POSITION != AUTHORITY
```

A conflict work item never chooses a winner. It preserves all known origins and requires new evidence or an explicit resolver decision.

A primary-source discovery work item does not guess an origin. It starts with an empty candidate-origin set until evidence identifies an appropriate source.

A direct-evidence work item may point back to already-known primary origins as candidate observation surfaces, but that reference does not itself authorize an external request.

## Adaptive closure

The queue is derived from the current VFY frontier.

If new evidence closes a gap on replay:

```text
VFY disappears
  ↓
corresponding VWK disappears
```

This keeps the queue aligned with the current epistemic state instead of accumulating stale tasks.

## Persistence

The scheduled Mine cycle now persists:

```text
data/proposition-adjudications.snapshot.jsonl
data/verification-frontier.snapshot.jsonl
data/verification-work-queue.snapshot.jsonl
```

## Machine surfaces

- `resource_miner/work_queue.py`
- `schemas/verification-work-item.v1.schema.json`
- `tests/test_work_queue.py`

Session graph: issue #695.
