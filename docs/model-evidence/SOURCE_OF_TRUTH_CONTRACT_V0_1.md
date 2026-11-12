# Model Evidence — Source of Truth, E0/E1 (research candidate)

**Status:** Z1 **offline research fixture**, not an operational/authoritative registry.  
**Parent:** [Issue #942](https://github.com/humanaios-ui/operations/issues/942) and [PR #944](https://github.com/humanaios-ui/operations/pull/944).  
**Source basis:** Read-only review of existing `main` artifacts and PR metadata on 2026-10-21. Re-pin exact commit SHAs before review/admission.

## Mission boundary

Source of Truth means a reproducible chain of **who observed which claim under what method, for which tested model, at what time** — *not* a master leaderboard, automatically ratified graph, permission database, marketplace, model-training collection, or replacement for HumanAIOS governance.

`SOURCE_IS_NOT_TRUTH` · `GRAPH_IS_NOT_AUTHORITY` · `WITNESS_IS_NOT_THE_AUTHORITY`.

**No external fetch, model calls, real votes, production API, private materials, training, wallet, applicant eligibility, spending, or actions occur in E0/E1.** The reference projector in `resource_miner/model_evidence_view.py` reads **caller-provided synthetic objects only**. No state writes; no imports into production application.

## Differential inventory: reuse vs. missing bridge

| Actual preexisting primitive | Existing location | Reuse/missing boundary |
|---|---|---|
| Controlled document authority | `document-registry.yaml`, `CONTROLLED_DOCUMENTS.md` | Canonical documents; **do not** register this study as approved by merely adding a file. |
| Phase-0 Evidence Graph | `EVIDENCE_GRAPH.json` | Existing claim/evidence/control typed nodes, edge states. **Not** a model benchmark database or evidence-verification result. |
| Resource provenance | `humanaios-funding-pipeline/resource-miner/resource_miner/models.py` | `EvidenceRef`, `ResourceCandidate`, `NeedMatch`; do not promote source match into eligibility. |
| Existing resource/intent bridge | `humanaios-funding-pipeline/resource-miner/app.py`, `resource_miner/intent_os.py` | Local `/intent-os`, `POST /api/intent` exist; no new live endpoint in this PR. |
| On-Track technical-vs-user distinction | `resource_miner/on_track_execution.py`, `on_track_progress.py`, `docs/ON_TRACK_REFLEX_V0_2.md` | Local HTTP checks are not deployment, admission or achieved goal. |
| Witness / public model participation | `lasting-light-ai` issue #64 / PR #65 and `WITNESS_SERVICE_CONTRACT.md` | Witness character and synthetic PB0 separate from model evidence; consumer must not infer authority from animation. |
| Federated source standing / adjudication | Operations issues #923, #693, #595, #735 | **Design/partial implementations to verify**; reuse PRP/PRS/adjudication/provenance, no parallel database or new ratification chain. |
| Human participation | `PARTICIPATION_CONTRACT_V0_1.schema.json` | C0–C3 consent separated from public voting and approval; no real participant collection. |
| Internal operational manuals | `docs/FOUNDERS_MANUAL.md` | Draft, historically pinned. A merged document is not a completed human objective. |

This census names reusable interfaces but **does not claim** that private Google Workspace notes, external leaderboards, or cached secondary reports are synchronized with default-branch canonical state. The prior PR #944 head was an empty diff; this PR now carries an actual bounded change.

## Evidence-vs-authorization crosswalk

| Evidence research term | Existing analogue | What this slice deliberately does not do |
|---|---|---|
| `source_uri`, `origin_key`, `observed_at` | `EvidenceRef.url/kind/observed_at`; #923 original-source lineage | Assert legal redistribution rights, fetch URLs, ingest private data, or sign receipts |
| `subject.system_id`, `model_version`, `scaffold_id` | Source/model metadata to be resolved at site integration | Collapse same marketing name across deployments |
| `lens`, `metric`, `method` | #942 six evidence lenses; ACAT benchmark crosswalk | Merge popularity, capability, cost, adoption and calibration into one scale |
| `comparison_eligibility` | Existing match uncertainty, graph validity | Infer authority, source truth, or eligibility |
| `source_group`, `conflicts` | #693 independent origins, #595 contradiction edges | Count two mirrors of one original as independent verification |
| `ModelEvidenceView` | Derived evidence projection for future Witness and INTENT-OS | Modify evidence graph, coordinator state, DB, or a user's intentions |
| `authorization_receipt` | Existing Coordinator event ledger and authorization contracts | Fabricate approval or ratify any observation |

## Six separate lenses

1. `PREFERENCE`: blind human vote and uncertainty, **not** factual truth.
2. `EXPERT`: declared rubric and reviewer sampling; independent expertise needs proof.
3. `CAPABILITY`: pinned task/dataset/harness/model settings; edition changes limit comparability.
4. `ECONOMICS`: measured dollars/latency/throughput under dated conditions, not ability.
5. `USAGE`: platform-scoped volume; not quality or global market share.
6. `ACAT`: self-description calibration on the correct P1/P2/P3 instrument, not task correctness or moral standing.

Rank **within** compatible observations and a named lens, never by one all-purpose metric. Do not infer comparative winner from overlapping/unknown intervals, missing methods, or insufficient sample size. Source freshness, reported/verified/simulated origin, and consent/license state must be visible.

## E1 reference projector contract

The adjacent pure `model_evidence_view.py` accepts synthetic `ModelEvidenceObservationV0`-shaped dictionaries, validates strict keys/enums, and outputs a deterministic **read-only** projection. It **does not import or mutate** the Coordinator, call GitHub or any benchmark endpoint, or read environment secrets.

Every input explicitly includes:
- `subject`: tested-system ID, model version, scaffold (not just vendor name);
- `origin`: immutable per-fixture source URI, original publishing group, observed UTC time, `SIMULATED` origin and `PUBLIC_SYNTHETIC` visibility;
- `method`: lens, metric, protocol, dataset/harness and task scope;
- `measurement`: score and unit, N, uncertainty interval; unknown `value`, `ci_lower`, `ci_upper`, and `sample_size` fields use JSON `null`, never the string `"UNKNOWN"` (both uncertainty bounds must be null together);
- `authority_effect: NONE`.

It deterministically labels a pair `NOT_COMPARABLE` for edition, metric, protocol, task, unit or model-version gaps. A duplicate origin is *not* a second independent source. It never fabricates a hash, signature, confidence interval or license. Missing source/method/certainty fields cause explicit rejection or comparison reason codes, not fake zeros. Unknown measurement states are reported as `NOT_MEASURED`, `UNCERTAINTY_UNKNOWN`, and `SAMPLE_SIZE_UNKNOWN` reason codes. Runtime metadata/cost measurements in a real deployment need separate manifest and rights review before widening the contract.

### Reproduction (no external calls)

From `humanaios-funding-pipeline/resource-miner`:

```sh
python3 -m unittest discover -s tests -p 'test_model_evidence_view.py' -v
```

Fixture cases: incompatible harness, unresolved model identity, duplicate origin, stale origin, underpowered human preference, absent uncertainty, source-class/metric conflation, forged `authority_effect`, scope/visibility leakage, stable sorting, and ability to abstain. All results are **synthetic experimental data**.

## Gate / next implementation

- [ ] Independent exact-head CI, negative tests, CodeRabbit + human reviewer audit.
- [ ] Pin source census paths and open PR status at actual review SHAs, and reconcile #923/#693/#595/#735 source/claim mappings.
- [ ] Choose **one** permitted real public external issuer only after terms/license/metadata verification and separate approval.
- [ ] Integrate one validated **read-only projection** into existing UI; do not create new storage/control plane.
- [ ] Demonstrate comprehension against a source-links-only baseline and perform an authorized founding-user test only after deployment and identity boundaries are verified.

**This work is proposed evidence infrastructure, not admission/merge authority.** A Coordinator **PASS** routing receipt and a human code approval are distinct events; neither is claimed in this document.
