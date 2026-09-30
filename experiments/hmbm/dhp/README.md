# Durable Handoff Protocol (DHP)

DHP separates computation, persistence, communication, acceptance, and canonical advancement into independently receipted transitions.

## Invariants

1. **Canonical immutability:** Analyst and Courier MUST NOT advance canonical state.
2. **One outstanding candidate:** at most one unresolved candidate may exist for a canonical predecessor.
3. **Accepted-only ancestry:** candidates MUST name an ACCEPTED predecessor.
4. **Byte identity:** persisted artifact bytes are SHA-256 hashed and read-back verified before QUEUED.
5. **No silent regeneration:** a persistence failure is a failure record. Regeneration receives a new generation ID.
6. **Custody separation:** Analyst computes/persists; Courier communicates; Witness accepts/advances.
7. **State distinction:** QUEUED != COMMUNICATED != ACCEPTED != CANONICAL.
8. **Paper boundary:** HMBM artifacts cannot authorize real trades, wallets, keys, or fund movement.

## State graph

ANALYSIS_COMPLETE -> PERSISTED -> QUEUED -> COMMUNICATED -> ACCEPTED -> CANONICAL

Each edge records: authority, actor, artifact hash, predecessor, transition time/evidence, verification receipt, and failure/unknown state.

Terminal/hold states include PERSISTENCE_FAILED, COMMUNICATION_FAILED, ACCEPTANCE_FAILED, HOLD_PENDING_DOWNSTREAM, and AUTHORITY_REQUIRED.

## Node authority

| Node | Analyze | Persist candidate | Communicate | Accept | Advance canonical |
|---|---:|---:|---:|---:|---:|
| Analyst | yes | yes | no | no | no |
| Courier | no | no | yes | no | no |
| Witness | no | no | no | yes | yes |

## Analyst opening handshake

Read canonical pointer. Validate it resolves to an ACCEPTED receipt. Search the candidate index for unresolved records whose predecessor equals canonical. If any exists, return HOLD_PENDING_DOWNSTREAM and stop. Otherwise analysis may proceed.

## Persistence handshake

Write immutable candidate bytes, compute file SHA-256, compute canonical semantic SHA-256 according to the experiment contract, write manifest, read all bytes back, recompute hashes, then write a QUEUED receipt. A failed read-back MUST NOT produce QUEUED.

## Courier handshake

Courier consumes QUEUED only. It verifies predecessor still equals canonical, byte hash, manifest, recipient/subject/body contract, and paper-only boundary before communication. Communication produces a separate receipt. Courier cannot edit candidate bytes.

## Witness handshake

Witness consumes COMMUNICATED only, independently verifies evidence and receipts, then emits ACCEPTED or a failure. Only Witness may update the canonical pointer, and only to an ACCEPTED state.

See `dhp.schema.json`, `validate_dhp.py`, and the Cycle-003 migration record.
