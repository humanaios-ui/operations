# DHP Connector-Native GitHub File Bridge

## Purpose

Courier must never reconstruct a queued artifact from model-visible text. The bridge converts an immutable GitHub source reference into a reusable connector file handle while preserving byte identity.

## Input: GithubImmutableSource

Required: repository, full 40-hex commit SHA, exact repository path, Git blob SHA, SHA-256, byte length, and media type. Mutable branch/tag references are prohibited.

## Output: ConnectorFileReference

Required: download_url, file_id, mime_type, and file_name. The output must be reusable by downstream connectors without routing artifact bytes through model text.

## Invariants

1. Fetch source bytes from the exact commit/path.
2. Confirm provider-resolved Git blob matches the declared blob SHA.
3. Verify byte length.
4. Verify SHA-256.
5. Perform no parse/reformat/recompression/reserialization of the candidate.
6. Emit a connector file handle only after verification succeeds.
7. Record semantic_transformation=false.
8. Courier independently re-verifies the sent Gmail attachment before COMMUNICATED.
9. Bridge failure leaves the candidate QUEUED.

## Platform binding

The Python module defines the provider-neutral contract. A runtime binding MUST implement FileHandleProvider.materialize(...) using a platform-native file service.

For the current connector surface, the missing primitive is equivalent to GitHub repository file -> ConnectorFileReference. GitHub's Actions artifact downloader already returns this reusable file-reference shape, while ordinary repository-file reads currently return textual/base64 content. The correct platform implementation is therefore to expose the same file_uri / ConnectorFileReference response for commit-pinned repository files, or provide a dedicated materialize_repository_file action.

This bridge is infrastructure-only. It does not authorize Gmail SEND, Witness acceptance, canonical advancement, trading, wallets, keys, or funds.

PAPER ONLY / NO REAL CAPITAL.
