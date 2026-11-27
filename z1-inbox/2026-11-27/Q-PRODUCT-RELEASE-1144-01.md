# Q-PRODUCT-RELEASE-1144-01: #1144 is the sole active product-release candidate; public-platform expansion waits until it is complete

**Z1 Proposer:** Grok (Z1)
**Date Submitted:** 2026-11-27
**Status:** AWAITING Z2 RATIFICATION. Owner-approved default (owner approved filing this record on 2026-11-27), **pending Night Z2 ratification**. Not ratified.
**AUTHORITY_EFFECT:** NONE.
- This file changes no code, workflow, label, admission or deployment.
- It closes nothing.
- Ratification (Night merging this PR) sets product sequencing only.
- The merge, admission and release of #1144 remain separate Night acts.

**Filed because:** on 2026-11-27 the owner directed: "Make #1144 the sole active product-release candidate. Complete it before expanding the public platform." That directive is already recorded on #1143 (comment 7216633455). Under GOVERNANCE.md Zone 2, strategic choices need Night's approval, so this candidate asks for it.

**Read at:** main `612d46e4`, #1144 head `098ac3b7`, GitHub API 2026-11-27 about 11:20 UTC. Deferral register: comment on #1143 (filed alongside this PR).

## What Z2 is asked to decide
1. **Sole candidate.** PR #1144 (synthetic read-only qualification card, the slice of `z2:ratified` #1143) is the only active product-release candidate.
2. **Definition of done.**
   - **Level A:** Night merges #1144 once all of these hold:
     - advancement logic is correct (required gaps or blockers come before optional practice)
     - the fixture is honest (every required predicate is mapped or marked NOT_REVIEWED; OR alternatives are kept)
     - the six deterministic cases pass with zero false ELIGIBLE
     - CI runs the qualification tests
     - the PR is rebased, says `Refs #1143`, and its body is accurate
     - exact-head checks are green, or the remaining red is explained (ACAT-R, #1184)
     - review is cross-vendor: a non-Copilot agent plus the named independent human
     - the owner has run `/coordinator admit` at the final head
   - **Level B:** one local, isolated, static synthetic demo card with usability, privacy and independent-review receipts, then Night's release choice.
   - Phases 2–3 of #1143 stay separately gated.
3. **Deferral.** Public-platform expansion and parallel INTENT-OS product implementation are DEFERRED_AFTER_1144 per the register on #1143. Nothing is closed and all work is preserved. The resume trigger is Level B released, or Night re-prioritizes.
4. **Kept active:**
   - #1184 (ACAT-R fix)
   - #1235
   - security work
   - CI hygiene PRs
   - #1338 (its own Z2)
   - #1317 trial
   - binding obligations
5. **Roles.**
   - Copilot remains the single writer on #1144.
   - Claude Code reviews the code and builds the Level-B demo in a separate PR after merge.
   - Grok replays tests offline and verifies source and CI read-only.
   - ChatGPT cross-checks the source predicates.
   - Moving the writer to Claude Code needs Night's explicit choice.

## Evidence
- Local offline replay at head and on a local merge with main: qualification tests 26/26, resource-utility 4/4, opportunity-journey 19/19.
- No workflow runs `tests/test_opportunity_surface.py`.
- The head's check runs (Nov 7) show 1 failure: `regression`, from ACAT-R source-readback tests (same family as #1184).
- With the current fixture, 2 REQUIRED items are UNKNOWN and the card still proposes optional PREFERRED practice. The defect is reproduced.

## Risk of being wrong and how it shows
- **Over-narrowing.** A time-critical external obligation could be starved. Mitigation: deadlines, security and paid commitments keep their own lanes (#1143 rule), and Night can re-prioritize at any time.
- **Stalling.** Copilot may not resume. Signal: no new #1144 head within 7 days of the work order. Then Night picks the writer.
- **Calendar kill.** #1143 says STOP if the card isn't demonstrated by about 2026-12-17 (6 weeks after the Z2 label on 2026-11-05).

## Falsifier
This decision should be revisited if, by 2026-12-17:
- #1144 has no new head addressing items 1–4 of the work order, or
- any parallel product PR merges while #1144 is still open.
