---
id: "IC-CAND-SMAG-PREDICTION-MISLABEL-S090926"
name: "SMAG predicted field is not a pinned prediction"
status: CANDIDATE
class: IC
date_registered: "2026-09-09"
date_origin: "2026-09-09"
session_registered: "S-090926"
zone2_ratification: null
tags: ["SMAG", "calibration", "instrument-mislabel", "IC-031-adjacent"]
related: ["IC-031"]
superseded_by: null
source_issue: "humanaios-ui/operations#232"
---

## IC-SMAG-01

- **claim:** In `audits/smag_pilot_ledger.jsonl` (61 rows read live 2026-09-09), `predicted` is mostly PR body/changelog prose rather than a pinned probability, so `gap_rate` is a merge-friction metric, not calibration.
- **class:** receipt overstatement (IC-031 adjacent) + instrument mislabel.
- **evidence_tier:** VERIFIED-LIVE.
- **falsifier:** any pre-2026-09-09 row with a numeric pinned `smag_p:` probability.
- **mitigation:** require `smag_p:` at capture; rows without it are **VOID** for prediction calibration.
- **status:** OPEN.

## H-SMAG-01

- **claim:** Current ~0.30 gap_rate signal is gate-stack calibration (especially one advisory gate), not Z1 prediction error.
- **evidence_tier:** VERIFIED-LIVE (`audits/smag_pilot_ledger.jsonl`, `audits/smag_gap_report.md`).
- **supply_side:** MECHANICAL (merge events + CI check outcomes, no LLM).
- **sub-claim 1:** `pr-fuzzing (address)` drives most friction (10/18 all-time; 10/12 post-2026-07-15).  
  **falsifier:** after repairing `pr-fuzzing`, gap_rate does not drop below 0.20 over the next 30 PRs.  
  **confidence:** 0.95.
- **sub-claim 2:** Dependabot friction exceeds humanaios-ui friction (32% vs 26%).  
  **falsifier:** after automation tuning, dependabot gap_rate remains above humanaios-ui over 30 PRs.  
  **confidence:** 0.88.
- **sub-claim 3:** gap_rate has stabilized near 0.30 steady-state, not random drift.  
  **falsifier:** gap_rate trends to 0.0 in the next 30 rounds without gate changes.  
  **confidence:** 0.85.
- **window:** 2026-07-08 → 2026-09-09 (61 PRs, 60 confirmed).
- **next_action:** fix `pr-fuzzing`; make guard required; measure next 30 PRs.
- **z2_ratification:** prose approval received 2026-09-09; hash pending.

## MOLT-SMAG-01 (Tier 1 proposal)

- **change:** repair `pr-fuzzing (address)` and require `guard` in main required checks.
- **prediction:** over next 30 merged PRs, gap_rate ∈ [0.03, 0.12], measurable_rate ≥ 0.95.
- **falsifier:** gap_rate > 0.20 or measurable_rate < 0.90 over the window.
- **revert:** restore prior required checks and emit REVERT event (F/IC candidate).
- **window:** 30 merged PRs or 2026-10-15.
- **status:** PROPOSED (must enter priority queue; no bypass).
