# Oracle × Meta-SMAG × Resource Miner — first bounded replication

**State:** OFFLINE RETROSPECTIVE PROTOCOL / `DESCRIPTIVE_ONLY` / **NOT independently outcome-attested**. This is a governed follow-on to #938 (Miner #939) and Oracle post-merge repair #945. No new graph/database, no production traffic, no privileges, no autonomous Z2 admission.

## Independently checkable input surfaces
Two pinned fixtures are maintained **separately**, with different assertion types:
1. `fixtures/oracle_smag_predictions_20261021.json`: current `smag_p_meta=0.85` author-controlled PR-body declarations for #432, #573, #724, #817, #931. PR-body history and pre-outcome immutability are **UNVERIFIED**.
2. `fixtures/oracle_smag_outcomes_20261021.json`: GitHub API PR metadata retrieved for those numbers on 2026-10-21. #432 and #573 are merged; #724, #817, #931 are OPEN. That observation is independent of the author's PR-body assertion **as a data field**, but is not a cryptographically authenticated or independent human outcome attestation.

The code joins only matching unique PR numbers and observation timestamps, uses the Oracle's pinned binary question **"merged by snapshot"** (not "success", "admitted", "zero rework" or "user benefit"), leaves OPEN episodes unscored, and obtains Resource Miner evidence candidates from `document_source_reflex.project_report()`. All independent CI, CodeRabbit, human approval, and Coordinator admission statuses are `UNKNOWN` unless separately authenticated.

The replay does **not** backdate a witnessed F1 precommitment. Current PR-body probabilities are *retrospectively reconstructed* using PR creation times as reference anchors, and never warrant prospective prediction quality. The F2 challenge and F3 correction stages are deliberately **NOT PERFORMED** on historical cases to prevent outcome leakage.

## Reproduce offline

From `humanaios-funding-pipeline/resource-miner` with this branch checked out:

```sh
python3 -m unittest discover -s tests -p 'test_oracle_smag_experiment.py' -v
python3 -m resource_miner.oracle_smag_experiment
```

No network access, cloud service, new package, or user credentials are required. A standalone path-scoped GitHub Actions test is also proposed; it does not satisfy the separate admission gate.

## Expected observations (not performance evidence)

- 5 forecast declarations, **2 merged and resolved**, **3 censored/pending**.
- Mean reported retrospective Brier over the **two resolved positives**: `(1-.85)^2 = 0.0225`; constant 0.5 baseline `0.25`. This is an extremely biased, outcome-selected two-case slice, not evidence that SMAG outperforms a reference forecaster.
- Oracle `claim_status=DESCRIPTIVE_ONLY`, with no independent cohort precommitment or verified outcome attestation.
- Resource Miner returns five `MISSING_VERIFICATION` *candidates* because independently authenticated CI/review/admission receipts were **not supplied**. They are NOT findings of real-world failure.

## Next prospective falsifiable experiment

Before the **next** SMAG consolidation PR outcome becomes known, independently register:
- a sealed question and pre-outcome sampling-frame list including every eligible PR, with exact question/close time/abstention/annul criteria;
- the F1 SMAG forecast as an immutable authenticated pre-outcome commit/receipt; a separate named F2 challenger and optional F3 corrected forecast;
- the outcome resolver identity, independent exact-head GitHub merge/check/admission receipts, and externally auditable evaluation timestamp;
- all unresolved and annulled cases in the denominator, without backfilling or changing labels after outcomes;
- reference base-rate and 0.5 forecaster, absolute Brier/log-loss and F1/F3 deltas, and sampling uncertainty (report no performance claim at N<20).

**Falsifiers:** replay accepts a re-sealed cross-episode manifest/outcome transplant; a future evidence cutoff passes; F3 precedes F2; a caller-only `VERIFIED` flag grants calibration readiness; unresolved PRs are treated as failures; Miner candidate text is promoted to admission/merge authority; or a retrospective body value is treated as independently precommitted F1. Any is grounds to reject promotion and preserve failed test evidence.

The objective is a **usable, reproducible, evidence-honest instrument**, not to establish that Oracle or SMAG predicts the future. Independent human authority remains unchanged.
