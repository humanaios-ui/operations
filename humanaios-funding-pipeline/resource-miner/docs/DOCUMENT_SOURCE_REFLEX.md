# Document-source reflex v0.1

## Contract

`resource_miner.document_source_reflex.project_report()` is a pure, bounded
projector over caller-supplied data. It performs no network access, Git reads,
file writes, branch updates, issue creation, or status mutation. It emits
`ResourceCandidate`-shaped evidence-gathering opportunities and `EvidenceRef`
records; it is not a knowledge authority or an approval mechanism.

Input collections are limited to 50 Git sources, 500 explicit bindings, and 50
pull requests. Repositories are restricted to the three GitHub repositories
registered as `GITHUB_REPOSITORY` / `EVIDENCE_SOURCE` Mines. Paths must be
relative Git paths without traversal. Blob and PR head IDs must be full
40-character SHA-1 or 64-character SHA-256 object IDs. The caller supplies
stable source and receipt identities plus a timezone-aware observation time.

Each binding explicitly names `(repo, path, claim_id, document_id)`; no
semantic/topic matching is performed. Optional SHA-256 claim fingerprints
allow conflicting values for the same claim ID to be surfaced. Source changes
with bindings produce `SOURCE_CHANGED_REVERIFY`; changes without bindings
produce `SOURCE_CHANGE_UNMAPPED`, never `NO_IMPACT`. An unchanged blob is
reported only as unchanged-from-input, with impact still `UNKNOWN`.

PR facts include merged state, CI, CodeRabbit, human-approval, admission
statuses, and the receipt head. A merged PR is flagged
`MERGED_WITH_FAILED_ADMISSION` only when the reported admission failure's
receipt head exactly matches the reported PR head. A mismatch produces
`STALE_RECEIPT`; missing checks, review, approval, or exact-head admission
evidence produce `MISSING_VERIFICATION`. These statuses are still only
caller-reported facts.

Every output labels the observation as `OBSERVED_FROM_CALLER_INPUT` and the
transport as `UNVERIFIED_CALLER_SUPPLIED`. `overall` stays `UNVERIFIED`;
every candidate has `evidence_state=UNVERIFIED`, `authority_effect=NONE`, and
`merge_authority=false`. No private document text is accepted or emitted.
Deterministic output digest is an integrity aid, not an authenticated receipt.
The reflex must not be wired to the scheduled scan or an event runner until a
separate, reviewed change repairs and tests the currently unregistered
`reconcile` CLI subcommand and obtains the required human authorization.

## Three-PR baseline comparison

This table records a manual baseline against the task-time connected GitHub
queries, not authenticated ground truth for every linked document. Exact PR
heads and check/review states below are API observations as retrieved on
2026-10-20; issue descriptions and other caller-provided facts remain claims.
The three census totals are 329 + 2,106 + 976 = 3,411 paths; those inventory
counts do not establish semantic claim/source coverage.

| Case | Manual review baseline | Reflex-assisted extraction | What remains unknown |
|---|---|---|---|
| lasting-light-ai #63 | API: merged at `3f7b1b6d322c9c93436afd38e1d658f1f2b20d2b`; exact-head human and CodeRabbit approvals; five reported check runs succeeded. PR body says 8 files inspected, 10 source-linked selected spans, and 308 pending in its 329-file census. | The pinned offline baseline fixture emits one `MISSING_VERIFICATION` candidate because no exact-head admission receipt is supplied. Without source bindings, it cannot claim semantic coverage. | Impacted-document recall and false-suggestion count are unmeasured; `#62` remains incomplete per the issue context. |
| operations #924 | API: merged at `3423817775ab46852414a2ac5889b720673ced3e`. Exact-head admission run `39202947422` failed `ADMISSION_REVIEW`: “ready non-maintenance work has no explicit admission record”; this is separate from the issue-reported passing workflows. | The pinned offline baseline fixture emits `MERGED_WITH_FAILED_ADMISSION` plus `MISSING_VERIFICATION` for an absent CodeRabbit receipt. The failure requests separate investigation and cannot grant approval. | Whether any PR's CI success satisfies all unrelated gates is not inferred. Review-time savings and impacted-doc recall are unmeasured. |
| humanaios #116 | API: merged at `d9c8c1be4d80d3150644afdecf81d1ba5fed2e14`; human and CodeRabbit approvals and four successful check runs were returned by the task-time query. This differs from the issue's earlier statement that no Actions runs were observed. | The pinned offline baseline fixture emits one `MISSING_VERIFICATION` candidate because no exact-head admission receipt is supplied; the reported CI state does not authenticate that missing receipt. | Conflicting observation snapshots require human reconciliation; neither the earlier absence nor later checks self-authenticate here. |

The extractor's deterministic work is bounded by its input caps and yields the
same report for identical input. This implementation did not time a human
manual review, independently verify document mappings, or collect a held-out
impact gold set. The offline anchor fixture emits four candidate rows across
the three PRs above. Accordingly, missed impacted documents, false suggestions,
and time-to-review are **NOT MEASURED**, not zero. The trust-boundary checks
exercised in tests cover unknown repositories, path traversal, malformed OIDs,
duplicate records, conflicting claim fingerprints, absent approvals, stale
receipts, and failed exact-head admission. A future benchmark needs explicit
reviewer timing and independently adjudicated source/claim/document ground
truth before reporting precision, recall, or time savings.
