# Durable Handoff Protocol (DHP)

DHP separates computation, persistence, communication, acceptance, and canonical advancement into independently receipted transitions.

## Invariants

1. Canonical immutability: Analyst and Courier MUST NOT advance canonical state.
2. One outstanding candidate per accepted predecessor.
3. Accepted-only ancestry.
4. Byte identity: persisted bytes are SHA-256 hashed and read-back verified before QUEUED.
5. No silent regeneration.
6. Custody separation: Analyst computes/persists; Courier communicates; Witness accepts/advances.
7. QUEUED != COMMUNICATED != ACCEPTED != CANONICAL.
8. Paper boundary: no real trades, wallets, keys, or fund movement.
9. Transport addressability: QUEUED must expose a downstream-consumable immutable reference bound to repository, full commit SHA, path, Git blob SHA, SHA-256, byte length, and media type. Branch/tag locators are insufficient.

## State graph

ANALYSIS_COMPLETE -> PERSISTED -> QUEUED -> COMMUNICATED -> ACCEPTED -> CANONICAL

## Artifact reference

DHP-ARTIFACT-REF-1 uses a full Git commit pin, never a mutable branch. Courier materializes those exact bytes and verifies byte length and SHA-256 before communication. Materialization is byte transport, not semantic regeneration.

For new generations the reference is embedded in the QUEUED receipt. A legacy queued generation may use an additive artifact-reference.json sidecar only when it cryptographically binds the original receipt/artifact and leaves original evidence unchanged.

materialize_artifact.py is the reference resolver. validate_queue.py makes missing or invalid transport references a CI failure.

## Persistence handshake

Persist and read back immutable candidate bytes, verify hashes, create a commit-pinned artifact reference, verify that reference resolves to the same Git blob, then emit QUEUED. Failure to establish downstream addressability is PERSISTENCE_FAILED, not QUEUED.

## Courier handshake

Courier consumes QUEUED only. It resolves and materializes the immutable reference without transformation, verifies SHA-256/length, verifies predecessor/canonical relationship and paper-only authority, then communicates. After Gmail send it reads the exact attachment back and hash-compares before emitting COMMUNICATED. Courier cannot edit candidate bytes.

## Witness handshake

Witness consumes COMMUNICATED only and independently verifies evidence before ACCEPTED/canonical advancement.

PAPER ONLY / NO REAL CAPITAL.
