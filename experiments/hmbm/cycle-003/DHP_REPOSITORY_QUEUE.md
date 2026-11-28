# DHP Repository Queue Contract

The repository queue is the durable Analyst→Courier handoff substrate for HMBM-CYCLE-003.

## Queue layout

candidate.json + manifest.json + queued-receipt.json form the normal queue package. New generations embed artifact_reference in the queued receipt. A legacy queued generation may carry additive artifact-reference.json remediation only when the original evidence remains unchanged.

A directory is not QUEUED merely because files exist. QUEUED requires successful read-back of exact candidate bytes and a downstream-consumable immutable artifact reference.

## Producer transaction

Analyst MUST:
1. resolve the latest ACCEPTED canonical state and enforce backpressure;
2. persist immutable candidate + manifest;
3. read candidate bytes back and verify SHA-256;
4. capture repository full name, full 40-hex commit SHA containing the candidate, candidate path, Git blob SHA, SHA-256, byte length, and media type;
5. construct a commit-pinned raw transport URL; mutable branch/tag URLs are prohibited;
6. resolve the commit-pinned reference and verify blob identity;
7. embed artifact_reference in the new queued-receipt.json;
8. only then emit QUEUED and stop.

If write/read/hash/reference resolution fails, emit PERSISTENCE_FAILED; do not communicate and do not advance canonical.

## Courier transaction

Courier consumes only a valid QUEUED receipt/reference. It materializes the exact referenced bytes without semantic parsing/re-serialization, verifies byte length + SHA-256 before Gmail, and uses those bytes as the attachment. After send, Courier reads the exact sent attachment back and re-verifies identity before producing COMMUNICATED.

A Courier MUST NOT reconstruct candidate bytes from prose, model output, parsed JSON, or a new generation.

## GEN-003 remediation

GEN-003 predates the transport-addressability invariant. Its original candidate, manifest, and queued receipt remain unchanged. artifact-reference.json is an additive remediation sidecar bound to the original hashes and commit-pinned candidate blob. C003-DHP-ARTIFACT-REFERENCE-REMEDIATION-001 receipts that correction.

## Witness transaction

Witness consumes independently verifiable COMMUNICATED evidence and may emit ACCEPTED. Only Witness may advance the HMBM canonical pointer.

PAPER ONLY / NO REAL CAPITAL.
