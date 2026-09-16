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

## Molt Classification

<!-- Predict the tier of this PR from what it CHANGES, not what it intends:
       Tier 0 — no constants, no gates. Not a molt; consumes no molt slot.
       Tier 1 — constants (needs molt_id + prediction + window). Examples:
                behavior_spec.json, RESOURCE_UNITS.yaml, constants.json,
                weights/, caps/, rubrics/, …
       Tier 2 — gates (needs registry entry + ADV run). Examples:
                .github/workflows/, .z1-control/{ratify,validate,render}.py,
                system_graph.json, .github/CODEOWNERS, ci_gates.py, …

     The examples above are NOT the rule and are NOT exhaustive — they are the
     entries you are most likely to touch. The rule is the two path lists,
     CONSTANTS_PATHS and GATE_PATHS, in tools/molting_protocol_diff_v1_0.py.
     Read those if your claim is a close call; editing that file is itself Tier 2.
     CI runs the classifier and reports molt_tier_measured. It does NOT block merge —
     the gap between your claim and the measurement is audit data, and under-claims
     are the ones that matter. Leaving the placeholder in is VOID, not a claim of 0.
-->

**molt_tier_claimed:** `[0 | 1 | 2]`

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
