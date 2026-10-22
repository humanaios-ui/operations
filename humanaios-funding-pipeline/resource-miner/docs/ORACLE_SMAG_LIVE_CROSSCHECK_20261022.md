# Oracle × Meta-SMAG × Resource Miner — independent retrieval cross-check
**Observed on:** 2026-10-22 by connected GitHub PR reads, separate from the 2026-10-21 fixture files.  
**Purpose:** Test agreement between frozen retrospective inputs and a fresh GitHub read. This is NOT independent cryptographic attestation, pre-outcome registration, or a scored prospective forecasting trial.

## Inputs and scope
- PR-branch frozen predictions: `fixtures/oracle_smag_predictions_20261021.json`, blob `0520d7ed9b3f2c16a3348693c007fbc7c4e54719`, snapshot `2026-10-21T20:00:00Z`.
- PR-branch frozen outcomes: `fixtures/oracle_smag_outcomes_20261021.json`, blob `a8fc70ec82885ae2e179bc82e05e35d45eafdaae`, same snapshot.
- Independent **retrieval operation**: read each GitHub PR's live state, `created_at`, `merged_at`, current `head_sha` and current body field `smag_p_meta`. Sources: [#432](https://github.com/humanaios-ui/operations/pull/432), [#573](https://github.com/humanaios-ui/operations/pull/573), [#724](https://github.com/humanaios-ui/operations/pull/724), [#817](https://github.com/humanaios-ui/operations/pull/817), [#931](https://github.com/humanaios-ui/operations/pull/931).
- All five current PR bodies still report `smag_p_meta: 0.85`. Their GitHub `created_at` values match the frozen declarations. **Current body content alone does not prove the field existed at creation time.** That needs a separately authenticated historic revision.

## Cross-check results
| PR | Created at (GitHub) | Frozen snapshot state | Freshly observed state | Frozen head vs current head |
|---|---|---|---|---|
| #432 | 2026-09-21T06:52:16Z | MERGED 2026-09-21T10:05:23Z | MERGED (same merge timestamp) | same `6d00c2b7…` |
| #573 | 2026-09-28T06:58:01Z | MERGED 2026-10-01T23:25:49Z | MERGED (same merge timestamp) | same `ff353129…` |
| #724 | 2026-10-05T07:03:21Z | OPEN | OPEN | same `a8c96458…` |
| #817 | 2026-10-12T07:05:01Z | OPEN | OPEN | changed: frozen `7d1062f9…` → current `b05107e5…`; GitHub updated 2026-10-21T23:32:26Z, **after** snapshot |
| #931 | 2026-10-19T06:55:37Z | OPEN | OPEN | changed: frozen `a8cd2a66…` → current `f89d62ce…`; GitHub updated 2026-10-21T23:31:48Z, **after** snapshot |

### Results and limits
**OBSERVED via fresh GitHub retrieval:** The current merge states and merge timestamps agree with the frozen fixture for all five PRs: 2 merged and 3 OPEN. The stored historic head values for #817/#931 **cannot** be independently reproduced from the current PR head API; a source-linked commit history / archived observation is needed. No temporal contradiction is established by the changed heads.

**SUPPORTED descriptively:** Two resolved positive outcomes with `p=0.85` yield a conditional Brier score of `0.0225`, versus `0.25` for a constant `p=0.5`. **DO NOT infer superiority**: these are only two favorable, outcome-selected observations; the other three remain censored and the authored forecast fields have no independently authenticated pre-outcome commitment.

**UNVERIFIED:** prospective prediction timestamps; tamper-evident sampling frame; independently witnessed F2 challenges, F3 corrections, and outcome receipts; Z2 admission/merges; correlation/selection bias adjustments; generalizable calibration.

**Resource Miner next action:** emit `MISSING_VERIFICATION` candidates for exact historic prediction edits, freeze-of-head attestation, admission receipts, and complete objective future outcomes. Candidate recommendations have `authority_effect=NONE` and `merge_authority=false`.

**Acceptance status:** Source-separated offline cross-check is reproducible at the named fixture blobs and source PRs. Independent *historical/prospective attestation* is **NOT VERIFIED**. Maintain `DESCRIPTIVE_ONLY`, do not promote `CALIBRATION_CLAIM_READY`, and do not auto-merge this PR.
