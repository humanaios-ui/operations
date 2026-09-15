<!-- START_HERE.md has the map; CONTRIBUTING.md has the rules. This checklist keeps a PR honest. -->

## What & why

<!-- One or two sentences: what this changes and the reason. -->

## Prediction (SMAG calibration)

<!-- Pin your confidence that this PR merges with all required checks passing.
     Format: smag_p: 0.XX (where 1.0 = 100% confidence, 0.0 = certain to fail)
     
     Scoring guide (see SMAG_AUTHOR_CALIBRATION_GUIDE.md):
     - 0.95+: typo/doc fix, test-only
     - 0.85-0.94: feature, straightforward refactor
     - 0.70-0.84: larger change, known optional flake possible
     - 0.50-0.69: risky change, one check might fail
     - 0.0-0.49: known failing check, intentional test
     
     Why? System measures your accuracy → learns → feeds back as gates.
     Help it learn by being honest about risk.
     Omitted lines are VOID (not scored); no penalty, but no signal either.
     
     FOR SMAG CONSOLIDATION PRs: Also pin smag_p_meta (SMAG's confidence in its own
     consolidation accuracy). Example: smag_p_meta: 0.82 (gap report regeneration is
     mechanical but ledger merges are risky). This wires SMAG's self-learning loop.
-->

## Zone

<!-- See GOVERNANCE.md. Delete the lines that don't apply. -->

- [ ] **Z1** — AI-executable, no ratification needed
- [ ] **Z2** — needs operator ratification (canonical record / finding registration)
- [ ] **Z3** — involves credentials / billing / deploy (operator-run)

## Checklist

- [ ] **Claim matches behavior** — the description reflects what the diff actually does
- [ ] **Document control** — if this adds/changes a controlled document, `document-registry.yaml` and frontmatter are updated (the CI gate will check)
- [ ] **Immune memory** — if this fixes or reveals a failure mode, it's registered in `REGISTERED.md` (F / H / IC) — link it: <!-- IC-000 -->
- [ ] **No secrets** — no credentials, tokens, or keys added (even placeholders)
- [ ] **Health** — ran `python3 tools/repo_health.py`; vitality not regressed

## Notes

<!-- Anything a reviewer should know: risks, follow-ups, open questions. -->
