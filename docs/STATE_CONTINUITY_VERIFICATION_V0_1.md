# HumanAIOS State Continuity Verification Contract (SCVC) v0.1

**Status:** Z1 candidate / synthetic verified locally; **not** Z2-ratified or production-admitted.  
**Scope:** Finite mathematical test + read-only structural integration with existing HLKS VLR v1 and Session Graph v0.2.  
**Authority:** `advisory_only=true`, `can_authorize=false`, `authority_effect=NONE`, `authenticated=false`.

## Motivation and theorem

A projection `P(s)` and retained information `W(s)` permit exact reconstruction of the admissible state `s` precisely when the joint map `s -> (P(s), W(s))` is injective. For a declared semantic function `q(s)`, semantic recovery is possible precisely when `q` is constant on every fiber of that joint map. This does not establish source authenticity, permission to retrieve, or continuity for states excluded from the tested domain.

`tools/state_continuity_verification_v0_1.py` provides `assess_finite` (exhaustive on at most 4,096 supplied states) and `assess_hlks_session` (read-only compatibility bridge). Both emit `schemas/state_continuity_verification_v0_1.schema.json` reports.

## Interface mapping

| SCVC input | Existing contract | No change to canonical source |
|---|---|---|
| `vlr` | `schemas/validated_learning_record_v1.schema.json` (HLKS VLR v1) | Checks pinned source/contract, validity/retention, domain/purpose, revocation, retrieval state, source/observation/correction refs; does **not** trust self-declared receipts. |
| `graph` / `entity_id` | `chat_graph/schema/longitudinal_graph.schema.json` (Session Graph v0.2) | Joins stable `source_id` references against graph sources and entity `source_refs`; inspects relevant assertions/events for conflict, correction, authority. |
| `request` | Explicit caller-scoped lookup `{domain,purpose,at,source_commit,contract_commit}` | Requires pinned commits and offset-aware time; disallows private data crossing this public metadata interface. |
| `report` | SCVC v0.1 JSON Schema | Uses existing references only; no new memory store, canonical graph mutation, Coordinator decision or evidence attestation. |

## Dispositions

- `EXACTLY_RECOVERABLE`: the finite supplied test set has no joint-map collisions. This is **mathematical/synthetic** verification only.
- `SEMANTICALLY_RECOVERABLE`: the joint map collides, but the declared semantic function is constant on all observed fibers of the finite set.
- `NOT_ESTABLISHED`: unresolved, conflicting, stale/unbound or insufficient information. **Every HLKS/Session Graph adapter success ends here**, even when its references bind cleanly, because the adapter cannot independently authenticate sources or reconstruct original content.
- `RECONSTRUCTION_DENIED`: revocation, retention, domain/purpose/privacy or attempted authority violation blocks reconstruction.

The first two dispositions do **not** assert a live proof; report `authenticated` remains `false`. A future independently anchored attestation extension would require separate host, policy, privacy and admission approval. Do not infer authorization from any disposition.

## Security properties

1. No network, file writes, arbitrary source reads, issuer trust roots, credentials, or code execution occurs inside the SCVC module.
2. Private VLR data classes (`INTERNAL`, `PERSONAL`, `RECOVERY`, `SECRET`) are denied at this public binding interface, even if a record contains a `consent_ref`. A future private adapter requires its own external, current consent resolver.
3. Source/contract commits must match; unpinned sources fail closed. Time validity and revocation take precedence over retrieval flags.
4. Chat-derived claims and source bindings are **not evidence**. `VERIFIED` strings and local digests are **not independent proof of issuer identity or execution**.
5. Corrections are not overwritten; the adapter abstains on a correction until authorized replay resolves its complete lineage.
6. Report IDs are deterministic content digests for reproducibility, not signatures or authenticity attestations.
7. Report contents omit raw source locations, evidence bodies, private user data, original payloads and arbitrary free-text descriptions.

## Run the bounded tests

```bash
python3 -m unittest discover -s tests -p 'test_state_continuity_verification_v0_1.py' -v
```

Tests cover 3–6–9 exact finite recovery, semantic-only recovery, collisions, witness retention, HLKS/Session Graph binding, stale pins, purpose/domain denial, private data denial, revocation/retention, conflicts, corrections, forged authority, and non-elevation of self-claimed verified receipts. Local success is not protected CI evidence; gate and issuer authenticity must be verified separately.

## Governance and next integration boundary

Linked planning: #677 (Session Graph), #782 / #783 (HLKS), #686 (evidence-bearing behavior). **Do not alter** `REPOSITORY_COORDINATOR_POLICY.json`, `ADMISSION_LEDGER.jsonl`, Z2 ratification, host settings, or live source data to land this module. Open a PR as an unadmitted Z1 candidate. After independent review, an authorized protected witness may supply attested reconstruction checks in a separately versioned contract; do not silently upgrade this structural adapter to an executor.
