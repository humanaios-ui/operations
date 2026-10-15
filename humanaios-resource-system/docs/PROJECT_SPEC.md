# Project specification and assumptions

## Composition boundary

`adapters/resource_miner_adapter.py` calls the existing Miner handoff builder and
selects resource identity and source/action links into an unassessed resource.
`entitlement_navigator_adapter.py` composes that builder with Navigator intake.
The latter opens an investigation; it does not establish eligibility.
No discovery adapter, existing candidate schema, or resolver is rewritten.

## Local flow

1. Import a candidate or append a synthetic existing resource, without collecting
   a complete applicant profile. Boolean predicate claims and evidence can arrive
   progressively. Requirements are explicit input from the external specification.
2. Supply provenance-bearing evidence and current authoritative rule attestations.
   The prototype checks dates, exact predicate coverage and contradictions locally;
   it does not fetch or authenticate the authoritative source. Relevance is unused
   in eligibility decisions. Incompatible known facts block a warrant.
3. `controller/portfolio_sweep.py` batches shared unknown predicates, propagates
   GLOBAL facts across relevant requirements and scopes other facts to resources.
   Material changes identify affected branches. Logic changes replay all branches.
   An exhausted frontier queues the next caller-supplied scope; queueing is not a scan.
4. A verified branch produces an evidence-supported warrant with no authority.
   Scoped human authorization permits creation of a claim-plan artifact under
   review. Every claim is checked against a named evidence snapshot and exact
   requirements. Prior reuse requires explicit predicate overlap and symmetric
   delta mapping. Rendering a submission-ready resume/proposal is deferred.
5. `runtime/state_store.py` validates append-only JSONL events. Evidence, artifacts
   and authorizations have immutable record IDs; resource/value snapshots can
   evolve under a stable resource ID. `latest()` rebuilds projections. Artifact
   insertion requires recorded authorization and evidence. Activity states are
   literal observations: prepared/clicked never imply submitted/acquired.
6. `manager/inventory.py` accepts explicitly acquired resource snapshots, allocates
   only to allowed workload IDs, measures consumption and checks expiration.
   Restricted infrastructure has zero cash value. Consumption alone realizes no
   gain. Conversion requires supporting downstream evidence and records a graph
   edge; the supplied realized amount is an attestation, not an audited valuation.
7. Material success/failure observations change returned portfolio priority.
   Multi-type verified yields rank convergence candidates. `LocalRuntime.run()`
   replays durable claims on an explicit local tick and appends distinct MATCH
   activity once per resource. It never performs an external action.

## Scope and trust limits

All contracts use version `1.0`, Draft 2020-12 and closed object fields. The stdlib
validator implements only the type/required/property/enum/constant/array/range/
pattern/format/conditional subset used here; it is not a general schema engine.
Predicate names, opaque IDs and public links must be curated at intake. Schema
validation cannot prove that an identifier or URL does not encode private data.

The ledger is single-writer, local, append-oriented storage, not encrypted,
tamper-evident, transaction-safe or suitable for concurrent writers. A malformed
or truncated log fails closed. Resource acquisitions, external specifications,
rule authority, human attestations and outcome receipts are trusted local inputs;
the prototype does not authenticate humans or independently verify observations.
Artifact semantic checks occur in the builder and ledger append APIs; files must
not be edited directly. No generic event/free-text research payload is supported.

Inventory allocations/conversions are in-memory calculations; callers must append
updated resource-value snapshots if persistence is needed. Renewal, dependency
optimization, durable resource graph edges, formatted external artifacts, a
deployed worker, browser UI and encrypted persistent vault remain future work.
Explicit ticks are restartable, but there is no background service or automatic
source monitoring. Attention notifications expose only batched unknown facts;
privacy/authority prompts belong to the calling UI. Independent adversarial review
remains required before any authority expansion. This local self-review is not
that independent review.
