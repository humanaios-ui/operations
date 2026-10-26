# #1002 First Replay — Source Feedback / Behavioral Evidence Baseline

**Stage:** Z1, offline *shadow* replay. **Status:** pending PR CI evidence and independent human source review.  
**Source:** [operations issue #1002](https://github.com/humanaios-ui/operations/issues/1002).  
**Method:** [#746](https://github.com/humanaios-ui/operations/issues/746); **instrument blocker:** [#750](https://github.com/humanaios-ui/operations/issues/750).

## Experimental distinction

The first issue #1002 run is a **deterministic source-status replay**, NOT a model-training trial and NOT an ACAT assessment. The existing Resource Miner lexical/taxonomy ranker is the subject. The experiment is performed with an **unchanged** 51-record snapshot and an in-memory counterfactual after-arm that withholds one exact URL. No source catalogs, historic records, or production ranking are modified.

### Frozen inputs

- Main reference commit: `9951e5dcbbc50c40a4bfbce3ca9f480b9b07fcdf`.
- Snapshot Git blob: `e7fba397546cbb6b97117a80ede245ecdb55af3b`.
- Current ranker Git blob: `94b2590754ea209db2b3bcba9698e78b6311c8f3`.
- Fixture: `fixtures/feedback_replay_1002_v1.json` (public, no resume or private objective).
- Historic source: Convergent Research Program Launch Manager, `RES-26D48CDE47BB2BB0`.
- User-reported failure: [#992](https://github.com/humanaios-ui/operations/issues/992), 2026-10-22.
- Separate public-web observation, 2026-10-26: direct Lever listing returned HTTP 404; the rendered employer board did not list this role. However, indexed cached pages still displayed the listing/application. **That conflict prevents a claim of permanent closure.** The public-web observation is not an independently authenticated reviewer signature.
- Paired requests: `Find Program Launch Manager work`; held-out `Find compute credits`.
- Source and model IDs are explicitly pinned. The existing ranker depends on the current system date to discard expired items; the receipt records its runtime date. Do not generalize cross-day determinism.

## Expected baseline and acceptance

The command below generates an **unsigned** JSON observation; CI also archives it as a 90-day workflow artifact.

```sh
cd humanaios-funding-pipeline/resource-miner
python3 -m unittest discover -s tests -p 'test_feedback_replay_1002.py' -v
python3 -m resource_miner.feedback_replay_1002 \
  --output ../../outputs/feedback-replay-1002/first-shadow-replay.json
```

**Checks:** exact URL binding; stale source appears in before/first-10 and is held in proposed after; held-out results stay in the same order; same frozen ranker; repeatable runs; no eligibility claim, no authority or execution. The code rejects tampered snapshot bytes, fuzzy source identity, forged closure statuses, and fabricated shared approval.

**Measurements:** `stale_source_exposure_at_10` before/after; exact ordered candidate ID arrays; matched counts; `unexamined_count`; replay identity; excluded resource ID; unsupported closure statements emitted. `verified_relevant_recall_at_10` and `false_closure_count` remain **NOT_ESTABLISHED** until independently reviewed relevance and live-status labels exist. A passing shadow replay is **not** full #1002 acceptance.

## Subsequent review required

1. Independent, authenticated operator/reviewer rechecks employer board and exact source, records timestamp and evidence digest, and reconciles contradictory index results without declaring closure from HTTP status alone.
2. Human reviews and approves **a versioned shared source revision**, keeping original user report distinct. No approval is inferred from this draft PR, CI, or a web crawl.
3. Once #993 is resolved, replay again against the admitted source-status hold implementation with an unchanged ranker and the authorized before/after catalog versions.
4. Independently assess other live relevant resources and unrelated held-out objectives to establish recall and false-closure measures. Keep #750 pending before numeric ACAT comparisons.

## Future training experiments

Preserve task input and output digests, exact ranking strategy, source revision, case IDs, uncertainty, controls, version IDs, and limitations. This supports a later measured comparison but contains **no model-weight intervention, no parameter inference, no training label, and no claim that training caused any difference**. A later training study must run control and treatment model checkpoints on blinded, held-out tasks under a separate authorization.

**Governance:** `authority_effect: NONE`, `execution: DISABLED`, no external API calls, no provider action, no source deletion, no new graph authority, no merge or deployment authorization.
