# HumanAIOS Living Knowledge Substrate (HLKS) — bounded design v0.1

- **Status:** Z1 design candidate; not Z2-ratified; design only
- **Authority effect:** `NONE`
- **Baseline:** `humanaios-ui/operations@59f4199e22a7019e5a831a9ac38703a4b36d5ef3`
- **Execution disposition:** **NOT AUTHORIZED FOR EXECUTION**

This contract proposes a replaceable, non-authoritative memory and retrieval
capability. It does not approve implementation, deployment, third-party
execution, credential access, repository admission, financial commitments, or
permission expansion. A successful schema check or synthetic test is not
integration evidence or authorization.

## 1. Invariant and scope

The evidence path remains:

```text
Source → Observation → Evidence → Context → Learning → Recommendation
       → Authorization → Action → Outcome → Correction
```

`Memory ≠ evidence ≠ authorization`. HLKS stores pointers and bounded
interpretations, not a fourth Oracle or source of truth. A record, retrieval,
confidence value, historical approval, AI summary, hash chain, or passing test
cannot grant a warrant, admission, permission, or authority. Current
authorization must be resolved independently for the requested action, actor,
scope, and time.

This proposal covers record shape, read-only retrieval, privacy/freshness
rules, threat cases, and a synthetic test plan. It does not create a persistent
store, ingest private data, install a backend, issue credentials, run a pilot,
or connect to any domain.

## 2. Existing interface inventory at the pinned baseline

The following are existing surfaces to compose with, not stores to duplicate.
Paths and line ranges refer to the baseline commit above unless noted.

| Surface | Existing contract / observed limit | HLKS disposition |
|---|---|---|
| Session Graph | `chat_graph/README.md:1-5,23-40,63-73` states derived/non-canonical status, separates entities/assertions/sources/events, and says hydration is source binding rather than truth. `chat_graph/schema/longitudinal_graph.schema.json:2-16,24-26,66-92,138-180` requires a derived graph and `authority_effect: NONE`. `chat_graph/build_longitudinal_graph.py:7-22,31-75,136-164` keeps chat synthesis distinct from source observations and appends corrections. | Treat as an upstream source/projection. Chat-derived content remains unverified; do not copy the graph or promote source binding into proof. |
| Evidence Graph | `EVIDENCE_GRAPH.json:1-36` distinguishes claims, controls, tests, evidence, failures, falsifiers, and decisions. It is a typed map, not an HLKS memory store. | Link to graph nodes by stable source reference; do not create a second evidence ontology. |
| Observation / event records | `workspace_evidence_bus/schemas/workspace_event.schema.json:1-43` defines source, observed/valid times, hashes, privacy class, and authority effect. `workspace_evidence_bus/README.md:5-21,25-34` says the bus is not a universal source of truth, private email bodies stay out of the public repo, and HMBM is paper-only. `tools/control_plane_custody_observer_v0_1.py` and its tests normalize control-plane observations. | Reference observations and their source artifacts; do not treat an event envelope or its hash as proof of an external event. |
| NF ledger / local hash chains | `ledgers/NF_LEDGER.jsonl` is an append-only JSONL ledger; `ledgers/NF_LEDGER_README.md:5-9,17-18` and `tools/nf_ledger_v0_1.py:1-18,23-35,81-95` describe canonical JSON hashing and link/sequence/tamper checks. `tools/verified_receipts.py:7-10,93-136,403-407` explicitly limits its result to a locally pinned chain and says a locally read head is not an independent trust anchor or real-world truth. | Reuse neither as an execution authenticator nor as evidence of issuer identity. A VLR receipt must be independently verified against its issuer and protected source. |
| HMBM | `workspace_evidence_bus/hmbm/HMBM_CYCLE_003_PROTOCOL.md:1-14,54-71` keeps the experiment paper-research only and requires write/read-back checks before advancing its state. | It is a bounded experiment, not an approved general memory substrate or authority source. |
| Failure signatures | `REGISTERED_FAILURE_MODES.md:17-27` and `tools/registered_failure_mode_scan_v0_1.py` describe a registered failure-mode taxonomy and scanner. The baseline search found no separately named failure-signature correlation store/contract. | Treat the registry/scanner as an existing related taxonomy; this is an inventory gap to resolve before integration, not permission to add a parallel failure store. |
| Three-domain federation / typed exchange | Issue [#747](https://github.com/humanaios-ui/operations/issues/747) says domain repositories remain independently versioned and the UI is not a fourth source of truth. `docs/CONTINUITY_CLOUD_FEDERATION_PATTERN_S061726.md:1-6,14-26,30-40` is a Z1 design note, not a runtime exchange implementation. Issue [#751](https://github.com/humanaios-ui/operations/issues/751) is an open schema proposal, not a published schema at this baseline. Its original “immutable receipts” wording needs reconciliation with revocation and deletion requirements. | Consume only a later approved typed exchange contract. Preserve source repository, commit, domain and privacy scope; do not infer approval from issue prose or introduce a competing exchange schema. |
| Translation fidelity | Open issue [#749](https://github.com/humanaios-ui/operations/issues/749) amends the proposed primary measure to blinded critical-predicate preservation; it says KL divergence is exploratory and a small sample is not universal proof. | Treat translations as untrusted, typed projections. Preserve uncertainty, refusals, constraints and human corrections; fidelity scores confer no warrant. |
| Repository Coordinator | `REPOSITORY_COORDINATOR_POLICY.json` on `main` limits Coordinator authority to admission routing. The default-branch state snapshot reviewed for this PR does not list issue #782 or PR #783 among active admissions. PR #783 is a draft. Neither issue assignment nor this design constitutes admission. | No admission or execution authority is claimed. The disposition remains **NOT AUTHORIZED FOR EXECUTION** until Coordinator evidence and separate approvals exist. |
| URA / Resource Miner | Open issue [#755](https://github.com/humanaios-ui/operations/issues/755) specifies a typed, read-only adapter with no core HTTP/credential access or external execution. `humanaios-funding-pipeline/resource-miner/README.md:27-35` notes an optional `GITHUB_TOKEN` for one existing GitHub search adapter; `src/resource_miner/outlier_public_adapter_v0_1.py:1-5,50-62,96-104` validates supplied public metadata but expressly does not fetch or authorize it. | At most use their existing read-only screening interfaces in a separately admitted experiment. Do not install, execute, fetch arbitrary repositories, or access credentials by default. |
| Witness / host protection | `WITNESS_SERVICE_CONTRACT.md:3-5,28-40` limits the service to inventory/audit readiness and says it cannot self-ratify or self-authorize. `PARTICIPATION_CONTRACT_V0_1.schema.json:5-7,74-80` and `WITNESS_STATE_V0_1.schema.json:4-6,22-35` encode non-authority invariants. `tools/verified_receipts.py` verifies local chain integrity, not host protection. The latest available report in open issue [#730](https://github.com/humanaios-ui/operations/issues/730) (2026-10-05) says the host rules did not require the governance gate; no current independent ruleset read or negative test was run for this design. | Do not claim authenticated host admission or execution. A local hash chain and file-read trace are insufficient; issuer/run identity and protected source must be independently established. |

The Coordinator state is mutable routing state on its designated state branch,
not a contract or merge authority. Its absence of an admission for #782/#783 is
negative admission evidence, not a Coordinator authorization. This design does
not write to that state or manufacture a Coordinator receipt.

## 3. Validated Learning Record (VLR)

The versioned envelope is
[`../schemas/validated_learning_record_v1.schema.json`](../schemas/validated_learning_record_v1.schema.json).
It carries identifiers and source/observation/correction references; a source
commit; time-bounded validity and applicability; confidence and uncertainty;
supersession; consent/privacy scope; retrieval eligibility; revocation; and
validation receipt references. Its `authority_effect` is fixed to `NONE`.

The schema enforces shape, not truth, signature validity, host protection,
consent, referential integrity, or current authority. Fields such as
`issuer_claimed_verification_status`, retrieval state, confidence, and
applicability are untrusted cached claims until an independent resolver
checks unique identifiers, resolves every observation/correction/source
reference, verifies the issuer against trust roots pinned outside the record,
and re-evaluates scope. The verifier must not derive its trust roots from the
VLR, its store, or the same agent that produced it; a record cannot bootstrap
trust in itself or its verifier. No record field is a
permission, grant, admission, approval, warrant, or authorization receipt.
Historical authorization receipts may be linked only as historical sources;
they must never be reused as current permissions.

Records contain no raw conversation, credentials, private human/recovery
content, or unrestricted free-text payload. A source reference identifies
where evidence can be independently inspected; it does not reproduce it.
Unknown or unavailable references fail closed rather than being upgraded from
memory.

## 4. Translation and retrieval protocol

### Capture and projection

1. Capture is untrusted input. Preserve its origin and recorded time; do not
   accept self-authored assertions of `VERIFIED`.
2. Project only typed claims with exact source references and immutable source
   commit identifiers. A hash identifies bytes; it does not establish who
   produced them or whether the event occurred.
3. A validator resolves any receipt against an independently trusted issuer,
   repository, workflow, run ID and attempt, conclusion, workflow/source commit,
   and applicable protected-source rules. An entry in a local ledger, a
   re-computable digest, a self-reported GitHub URL, or a local file-read trace
   cannot satisfy this step.
4. Apply validity dates, current source/contract pins, applicability, consent,
   domain scope, revocation, and conflict checks before retrieval.
5. Return a source-preserving reference plus freshness/conflict status and
   uncertainty. A retrieved memory may inform a recommendation; it cannot
   authorize an action or promote Coordinator admission.

### Federated read request and response

A future read-only adapter must bind each request to the requesting domain,
declared purpose, allowed data classes, pinned source/contract versions,
current time, and freshness policy. The response must preserve the originating
domain and source link; distinguish `CURRENT`, `STALE`, `CONFLICTED`,
`REVOKED`, `UNVERIFIED`, and `NOT_FOUND`; expose uncertainty; and set
`authority_effect: NONE`. Missing scope, verifier, consent, or source pin means
deny/abstain, not broaden the query.

Retrieval eligibility is recalculated, not trusted from the stored boolean. A
changed source or contract pin invalidates applicability until revalidated.
Contradictory records remain visible as a conflict; recency or confidence
alone must not silently choose a winner. Do not merge private data across
domains. Human correction appends a correction/supersession reference; it
does not erase public history. Revocation or deletion invalidates derived
copies and caches. Any minimal tombstone retained for referential integrity
must omit deleted content and comply with the source domain’s retention and
consent rules.

## 5. Threat model and controls

| Threat | Required response |
|---|---|
| Fabricated or self-authored memory claims evidence or approval | Quarantine/unverified; no evidence promotion, authorization, or admission. Require independently inspected source observations. |
| Forged local SHA-256 chain or fabricated receipt fields | Reject as authenticated evidence unless the issuer/run and protected source are independently verified. Hash-chain integrity alone is not authenticity. |
| Replay of an old approval/receipt | Treat it as historical context only; resolve current authorization independently for actor, action, scope, and time. |
| Stale source or changed contract | Mark stale/ineligible and require revalidation; never silently carry applicability forward. |
| Conflicting memories or corrections | Preserve both lineages, return conflict/abstain, and require human review where material. |
| Cross-domain PII or recovery-record request | Deny by default unless an explicit, current, purpose-bound consent permits the exact data and destination. No hidden replication; minimize or omit content. |
| Malicious repository/dependency presented for memory backend | Read-only metadata screening only; review dependency, license, security and maintenance risk. No installation, code execution, credential access or backend promotion in this design. |
| Memory used as a Coordinator or authority promotion path | No such path exists in the schema or protocol. Admission, ratification and authorization remain separate independent controls. |

Residual risks include compromised trusted issuers, incomplete host rules,
incorrect source-domain classification, retention conflicts, and semantic
misinterpretation. This design does not close those risks; unresolved or
unverifiable state is an abstention.

## 6. Synthetic cross-session test plan

The machine-readable synthetic cases are in
[`../fixtures/hlks/scenarios_v1.json`](../fixtures/hlks/scenarios_v1.json).
All identities, claims, commits, receipts and content are synthetic. The
fixture does not contact GitHub, validate real issuer identity, exercise
cross-repository permissions, or establish integration.

| Case | Setup | Required result |
|---|---|---|
| A — observed failure | Session A records a failure with a source and observation reference. | It remains an observation/claim; no validation or authority is inferred. |
| B — corrected with authenticated validation | Session B appends a correction and refers to a synthetic trusted-witness validation event. The test harness separately verifies the synthetic issuer identity. | Only the corrected, applicable record may become retrievable in the fixture; the record still has `authority_effect: NONE`. The serialized “verified” field alone must not pass. |
| C — new agent retrieval | A new agent in the explicitly allowed domain requests the same pinned contract, within the validity window and consent scope. | Return the provenance link, correction lineage and uncertainty. Do not return a warrant or change admission/permissions. |
| D — changed contract | Change the applicable contract commit after C. | Mark the record stale/ineligible and require independent revalidation; do not reuse B as current guidance. |
| F1 — fabricated memory | Inject an unpinned claim that asserts success or approval. | Reject/quarantine; no evidence promotion and no authority effect. |
| F2 — forged receipt | Inject a locally re-hashed chain or self-asserted `VERIFIED` receipt with no independently trusted issuer evidence. | Reject as unauthenticated; a valid digest or file-read trace is insufficient. |
| F3 — conflict/staleness | Supply incompatible records or an expired/source-mismatched record. | Preserve conflict, mark stale, and abstain pending correction/review. |
| F4 — cross-domain PII | Request human/private recovery data from another domain without current exact-scope consent. | Deny; do not return, copy, summarize, log, or replicate the protected content. |

Every case asserts `authority_effect == "NONE"` and asserts that no admission,
credential, permission, action, or deployment state changes. The fixture set
and test plan are design artifacts; passing a future standalone synthetic test
would not prove a live integration or host-protection claim.

## 7. Falsifiers, gates, and disposition

The bounded design is falsified if any of the following occurs:

- a memory, AI-generated summary, schema-valid object, local hash chain, or
  historical authorization promotes itself to evidence, admission, or current
  permission;
- an unverifiable issuer, missing source pin, stale contract, or conflicting
  record is returned as current validated guidance;
- private data crosses domains without explicit current consent, or survives
  deletion in a replica/cache;
- retrieval can write to source systems, execute a tool, install a backend, or
  alter Coordinator/authority state;
- tests claim host protection or integration from standalone fixtures alone.

**Falsification status for this PR: NOT TESTED.** The cases below are
synthetic design fixtures and expected outcomes, not an executed test report.
There is no authorized live integration or authenticated host-test path in this
change.

At this design baseline, issue #782 is not present in the default-branch
Coordinator active-admission state, and PR #783 is draft. Therefore the
execution disposition is **NOT AUTHORIZED FOR EXECUTION**. The Coordinator
must provide its own admission disposition; this document is not that
disposition. No implementation, integration, deployment, backend prototype,
credential use, or authority change is proposed here.

Before any write-capable integration, require separate Coordinator admission,
separate authorization, independent review, a verified issuer/run and
protected-source path, privacy/retention review, and negative tests against
the current host rules. Issue #730 remains open; this document does not claim
that its host-protection requirement has passed. Report test evidence with its
exact scope and limitations, and publish a falsification report before
requesting any later execution work.
