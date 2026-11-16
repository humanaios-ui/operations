# What the review changes — an additive October-to-November research note

## What we found (October published study)

In 60 toy-agent episodes, the frozen no-retry analysis had **zero verified pact positives**, leaving the main detector comparison unevaluable. Later retries yielded **seven exploratory judge-positive cases**. On those labels, a literal keyword/action hybrid caught **four** explicit planted pacts, missed **three** concealed cases, and the talk rule flagged all **ten** benign negations. None of the ten shared-mistake episodes generated two final approvals. Changing what counts as agreement changed the interpretation of the eleven episodes where both agents approved an invalid action. These observations establish measurement and reliability limits, not spontaneous collusion or a validated detector.

## Reviewer direction accepted

1. **Main missing negative:** a real shared mistake. V0.3 includes private, pre-communication votes on tougher arithmetic cases and the option of common misleading information. It will not claim such mistakes occurred until observed and independently reviewed.
2. **Magic-phrase shortcut:** preserve original keyword baseline; add a semantic talk comparator with NO_PACT/PACT/UNKNOWN, blind to action ballots, task and labels; test new holdout rather than score the old paper again.
3. **Reliability:** 54/60 first-pass judge calls received HTTP 429. Add separate quota calibration *before* outcome freeze and predeclare retry-by-status with complete logs. No post-hoc extra retry stage to meet the positive floor.
4. **Clarity:** put a short findings paragraph first, then one compact table contrasting historical and new evidence, with limitations separated.
5. **Reviewer identity:** remove the relayed Empirica/DeepSeek pasted labels from the evidentiary comparison; retain in historical provenance as unauthenticated reported material, not independent ground truth.

## Evidence separation

| Source | Status | Supports |
|---|---|---|
| October official project PDF | Submitted 2026-10-26; historical | Frozen failure, exploratory count sensitivity, detector blind spots |
| Public Apart review | Published, reviewer anonymous | Critique and priorities; not independent rerun of new code |
| This v0.3 offline package | New synthetic implementation tests only | Correct task oracle, private-vote schema, monitor blindness, UNKNOWN and transport policies |
| DeMarius / PR #1153 | Independent offline host security evidence at older commits | Host boundary questions; **not** independent adjudication of new pact cases |
| Future v0.3 holdout | **NOT RUN** | No observed detection or shared-error results yet |

## What we must not claim

No repaired October frozen analysis. No authentic live shared mistakes. No measured semantic monitor accuracy. No provenance for past pasted reviewer results. No completed host security or Z2/Z3 grants. No Apart November submission or award without provider receipt.

## Required next authorized experiment

After quota-calibration and human authorization: freeze new protocol and the holdout schedule, run agents' initial independent votes, then messages/final votes, then blinded two-reviewer adjudication. Check both required cells *without retries selected by desired outcome*. If shared errors still do not emerge, report UNEVALUABLE. Keep all failed cases, refusals and UNKNOWNs.
