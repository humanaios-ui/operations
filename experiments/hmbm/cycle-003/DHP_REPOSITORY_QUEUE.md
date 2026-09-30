# DHP Repository Queue Contract

The repository queue is the durable Analyst→Courier handoff substrate for HMBM-CYCLE-003.

## Queue layout

```
experiments/hmbm/cycle-003/queue/
  <candidate-id>/
    <generation-id>/
      candidate.json
      manifest.json
      queued-receipt.json
```

A directory is **not QUEUED** merely because files exist. QUEUED exists only when `queued-receipt.json` records successful read-back verification of the exact candidate bytes.

## Producer transaction

Analyst MUST:

1. resolve the latest ACCEPTED canonical state;
2. search queue/receipts for an unresolved candidate with that predecessor;
3. return `HOLD_PENDING_DOWNSTREAM` if one exists;
4. generate candidate without changing frozen experiment definitions;
5. write immutable candidate and manifest;
6. read candidate bytes back from repository;
7. recompute SHA-256 from read-back bytes;
8. compare against manifest;
9. only after equality, write `queued-receipt.json`;
10. stop at `QUEUED`.

If any write/read/hash step fails, emit `PERSISTENCE_FAILED`; do not communicate and do not advance canonical.

## Courier transaction

Courier is the only node permitted to cross the Gmail communication boundary. It consumes only a valid QUEUED receipt. Before communication it re-verifies candidate bytes/hash, predecessor/canonical relationship, communication manifest, and paper-only authority.

Courier cannot alter candidate bytes. Gmail draft/send/read-back receipts belong to Courier, never Analyst.

## Witness transaction

Witness consumes independently verifiable communication evidence and may emit ACCEPTED. Only Witness may advance the HMBM canonical pointer.

## Historical generations

GEN-001 and GEN-002 were not successfully persisted into this queue. Their reported hashes are provenance observations, not durable queue receipts. If exact bytes are later recovered, they must be independently verified; otherwise they remain `PERSISTENCE_FAILED/NONCANONICAL`.

PAPER ONLY / NO REAL CAPITAL.
