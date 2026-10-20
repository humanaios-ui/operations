# Azure data and cutover review — issue #915

Status: proposed implementation checklist, 2026-10-17. This review records work
that can be prepared now and evidence required before live ingestion or cutover.
It does not establish legal approval, credit eligibility, deployment, or spend.

## Evidence and current limits

- `tools/azure_readiness.py` calls only `az resource list`, or reads an existing
  private JSON export. Its report omits names, endpoints, tags, and raw IDs.
  Hash references remain linkable pseudonyms; they are not anonymization.
- `docs/azure-readiness.md` correctly leaves deployment revision, real backend
  readiness, billing qualification, and successful human use unverified.
- `acat/api/db.py:get_pool` can return `_MockConnectionPool` when a driver is
  missing or a connection fails. An application response alone cannot establish
  persistence. This is an ACAT code finding, not proof that INTENT-OS uses it.
- `chat_graph/README.md` defines derived assertions, source bindings, and append-only
  correction events. Private Drive roots are metadata-only at its public boundary.
- No Azure Search ingestion adapter or deployed PostgreSQL migration is verified
  by this review. The service inventory itself cannot establish either.

## Field classification and permitted projection

| Dataset | Fields | Private storage | Public/report projection |
| --- | --- | --- | --- |
| Public Microsoft Mine observations | Canonical public URL, page title, observed UTC time, program name, published rules, allowed excerpts, source digest, adapter revision | Store permitted observations with source/retrieval evidence; record source terms and reuse limits | Allowlisted public facts and citations; no assertion of eligibility or entitlement from discovery alone |
| Microsoft Mine account results | Account email, tenant/subscription/resource IDs, private portal URLs, application answers, balances, eligibility verdicts | Restricted to the account owner and assigned service identity | Counts or explicit reviewed summary only; public program content does not make account results public |
| Private Drive | File IDs, names, folder paths, sharing/access lists, revision IDs, raw text, comments, personal details | Preserve existing source access rules; keep raw source and source-to-projection map private | Opaque source reference, reviewed claim summary, revision digest and observation time where approved; no raw locator/text |
| Graph projections | Entity/assertion IDs, source references, claim text, states, edges, confidence, correction events | Inherit the most restrictive contributing source access; mixed-source edges can reveal private relationships | Review claim text and edge endpoints together; retain advisory status and source lineage; private hashes alone do not make a graph safe to publish |
| Billing and credit evidence | Usage day, meter, quantity, currency, cost, credit adjustment, invoice/account/program identifiers, written rule version | Private financial evidence with time range and completeness recorded | Reviewed totals or threshold result with source period; missing days stay unknown; redact account, invoice and payment details |
| Credentials and access configuration | Tokens, passwords, connection strings, Search keys, signed URLs | Credential store only; restrict runtime access by role | Presence/absence and test result only; never echo secrets into logs, issue comments, reports, or indexes |

These are proposed handling rules, not permission to collect every listed field.
Start with public Microsoft Mine source facts. Private Drive ingestion requires a
specific selected corpus, purpose, access model, and retention choice.

## PostgreSQL ingestion prerequisites

1. Identify the exact writer service and target database/schema. Record source
   revision, migration revision, connection mode and environment privately.
2. Separate migration, ingestion, application-read and reporting identities.
   Choose grants per table; do not give runtime code database-owner rights.
3. Define stable source IDs, source revision, observed time, content digest,
   classification, permitted audience and deletion state. Preserve corrections
   and supersessions rather than silently replacing historical claims.
4. Make retries idempotent using a documented source/revision key. Quarantine
   malformed rows and record failed batches without copying private payloads.
5. Require explicit real-backend detection. A failed connection must produce a
   failed readiness result; a mock connection cannot satisfy this check.
6. In separately authorized staging, write a unique synthetic row, close the
   client, reconnect and read it back. Delete it and verify deletion. Record a
   scrubbed receipt tied to deployed code and migration revisions.
7. Set backup, retention, restore access and recovery targets; test restoration
   before transferring the canonical writer. Inventory is not a restore test.

## Search ingestion prerequisites and access questions

Search remains a rebuildable view. PostgreSQL or the chosen source store retains
the source record and revision lineage; a Search hit cannot grant execution or
upgrade a claim's evidence state.

- Which service identity may write documents, and which may query them? Can query
  clients reach only the intended index and permitted documents?
- Are index/schema administration rights separate from ingestion/query rights?
  Who holds any existing admin keys, and how will keys be rotated or retired?
- Are access checks enforced for every result, citation, cached answer and vector
  retrieval? Do not rely on hiding UI links to protect private documents.
- Which exact fields are retrievable, filterable, searchable and vectorized?
  Exclude credentials, access lists, private locators and unapproved raw text.
- Does embedding or enrichment send data to another service? Record its identity,
  region, retention terms and cost before enabling that path.
- Pin source IDs/revisions and chunk IDs so every hit resolves to its source and
  can be invalidated. Record index schema, adapter and embedding model versions.
- Prove document-level isolation with two synthetic audiences, test stale access
  revocation, and show that an interrupted batch can be safely replayed.

## Deletion lineage

Maintain a private map from source/revision to stored rows, graph assertions,
chunks, embeddings, Search documents and derived caches. On a valid deletion or
access-revocation request: stop new ingestion, mark the source unavailable, remove
derived retrievable content, rebuild affected projections, and verify retrieval
no longer returns it. Record scope, UTC time, result and unresolved copies.

Keep only a minimal restricted tombstone needed to prevent re-ingestion. Do not
retain raw private text in an append-only event merely to preserve graph history.
The historical event may state that a source was removed without retaining its
payload. Backup expiry and restored-copy deletion replay require an explicit
retention decision; do not claim immediate erasure from all backups.

## Writer cutover decision sheet

All assignments below are **pending explicit selection**. Names in repository
history do not automatically assign operational responsibility.

| Decision | Required recorded value | Current state |
| --- | --- | --- |
| Cutover accountable owner | Named person who approves the go/no-go evidence | PENDING |
| Execution owner | Named operator/service permitted to change the active writer | PENDING |
| Verification owner | Person/service independently checking stored results | PENDING |
| Recovery owner | Person able to restore the prior writer and data | PENDING |
| RTO | Maximum acceptable service recovery time | PENDING; no numeric target chosen |
| RPO | Maximum acceptable loss of accepted writes | PENDING; no numeric target chosen |
| Active writer | Exact job/workflow/service and schedule | PENDING verification |
| Old-writer stop proof | Disabled schedule plus drained in-flight runs | PENDING |
| Reconciliation boundary | Last accepted source revision/batch and checkpoint | PENDING |
| Rollback trigger | Error/loss/duplication threshold and decision deadline | PENDING |

Cutover sequence: capture the checkpoint; pause the old schedule; drain in-flight
runs; verify the old writer stopped; run the new writer on a bounded batch;
reconcile IDs, counts, digests and rejected rows; enable its schedule only after
the selected owner accepts the evidence. Before rollback, stop the new writer
and reconcile its writes to avoid duplicate replay. Record the actual schedule:
a GitHub Actions cron does not prove an Azure job exists.

## Task status recommendations

| Task | Suggested issue status | Evidence to close |
| --- | --- | --- |
| Inventory/report code | IMPLEMENTED, verification pending | Tests and CI at reviewed commit; scrubbed output from real inventory |
| Real database readiness | OPEN | Explicit backend-mode check plus staging reconnect receipt |
| Public Microsoft Mine ingestion | DESIGN READY, implementation pending | Bounded source allowlist, adapter, idempotency and lineage tests |
| Private Drive/Search ingestion | BLOCKED ON DATA DECISIONS | Selected corpus, access/retention choices and isolation/deletion tests |
| Writer handover | BLOCKED ON OWNER AND RECOVERY DECISIONS | Completed sheet and bounded cutover/recovery receipts |
| Billing/credit qualification | UNVERIFIED | Complete private daily evidence reconciled to written program rules |

These statuses are recommendations for issue #915, not updates to the canonical
governance registry. No deployment or billing evidence was produced by this review.
