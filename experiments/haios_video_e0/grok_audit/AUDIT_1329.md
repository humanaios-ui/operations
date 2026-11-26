# HAIOS-VIDEO-E0 — adversarial audit of the PR #1330 receipt, and v2 corrections (#1329)
Auditor: Grok-HAIOS (operations steward). Date: 2026-11-26 (CT).
PROPOSED | AUTHORITY_EFFECT NONE. This is one evaluator's audit; it is not ground truth and needs independent review.
Audited object: `replay.mjs`, `observed.json`, `README.md` at PR #1330 head 167e0ae2d133cc703e9ab8ca017305eb7919ff7c,
frozen here as a byte-identical snapshot in `v1_snapshot/` (sha256 47a67132…, 9762f6f2…, ced827dd…). None of the three files is modified; this directory does not touch #1330's paths.

## Replay result
`node replay.mjs` on Node v24.22.1 reproduces `observed.json` exactly (deep-equal). This is the first replay outside the
runtime that produced it. It is still not independent of the evaluator. A CI replay workflow is drafted but held out of this PR because `.github/workflows/` is Tier 2 (registry entry + ADV run + Z2).

## Findings (each is pinned by a test in `tests/v1_findings.test.mjs`)
| ID | Severity | Finding | Evidence | v2 status |
|---|---|---|---|---|
| F1 | High | The v1 gate trusts a principal **string supplied in the request**. An agent that writes `principal:"human:owner"` passes. The "forged principal" control only tried the string `"agent"`. The code comment says the trusted context is "not agent text", but the compared value comes from the request. | `gate()` extracted from the source and called with a forged request returns `true`. | Fixed: harness-held single-use approvals bound to agent and revision. Unknown request fields fail closed. |
| F2 | High | Duplicate protection never records use. The same request is accepted twice. | Two calls with the same id both return `true`. | Fixed: approvals are consumed on commit, and a replay is rejected. |
| F3 | Medium | The stale-revision check compares two values the requester controls. Copying the current revision defeats it. | Test F3. | Fixed: revision is checked against harness state and against the approval's revision. A policy bump invalidates old approvals. |
| F4 | High | The "out-of-band mutation detected" control is the constant `30-10<25`. There is no ledger, no mutation and no detector. "Nine control checks passed" is really eight checks plus a constant. | Source line pinned. | Fixed: a real conservation audit (initial + applied regen − ledger) with a clean-ledger control and a mutated-stock control. Still detection, not prevention. |
| F5 | High | The negative controls test `gate()`, but simulated arm C never calls `gate()`. The 200/200 result and the controls exercise different code. | Test F5. | Fixed: one `gate()` and `commit()` serve both the simulation and every control. New arm E runs 5 bypass attempts per cycle through the same gate (300 attempts per run, all blocked). |
| F6 | Medium | Arm C changes two things at once: the gate and a least-allocated-first ordering. Balance differences credited to the gate are confounded. | Test F6. In v2, the smallest agent share is 140.01 with the gate in fixed order (C) and 155.28 with the gate plus v1 ordering (D). | Separated: arm C is the gate only, and arm D is the gate plus ordering. D reproduces v1 C exactly. |
| F7 | High | The "corrected" mutation applies no transformation. It is identical to "valid", so "correction retained 12/12" measures nothing. | Test F7. | Fixed: real rev1→rev2 `applyCorrection()`, plus stale, correction-dropped-in-one-channel and correction-note-missing fixtures. |
| F8 | High | The v1 verifier ignores fields outside its five. A smuggled `extraClaim` or `endorsement` field is released. | Test F8. | Fixed: strict schema allowlist per channel record and artifact. |
| F9 | Low | `receipt:"no"` is accepted as a receipt (truthiness). | Test F9. | Fixed: a receipt is a sha256 matched against the registry. |
| F10 | Medium | All three media arms are byte-identical. "96 per medium, 288 total" counts 3 copies of 96 cases. The effective n is 12 base fixtures × 8 mutations, and medium has no effect by construction. The README admits medium effect is not measured, but the 288 count still inflates coverage. | Test F10. | Partly fixed: media now differ structurally (1, 2 or 3 channels), and a naive single-channel verifier misses more in multi-channel media. This is still contract QA, not comprehension. |
| F11 | Medium | The gated arm's 200/200 reserve and zero-violation result is true by construction, because grants are clipped to stock−25. The acceptance check asserts a tautology. Packet claim C02 presents this without the caveat in the same sentence; it appears only in C04. | Test F11. | Disclosed in the v2 output (`byConstruction`) and in every episode claim that uses it. The informative outputs are the useful-work cost (C−B = −17.44 per run; lower in 200/200 paired seeds), the ordering effect and the adversary block count. |
| F12 | Medium | The issue says an "earlier unsupported 600-run claim" is superseded. No such claim is locatable in this repository, so the supersession cannot be verified. v1 then reuses "600" as its own count, which risks conflating the two. | `rg` across the repo finds no prior resource-sharing 600-run claim. | HOLD. The owner needs to point to where the original claim lives. v2 reports 1000 scripted runs (200 seeds × 5 designs) to avoid the collision. |
| F13 | Medium | The nine sources are "to be attached with evidence", but there are no transcript hashes, retrieval times or tool versions. Segment timestamps are unverified. | `SOURCES.md` | Partly fixed: all 9 IDs resolve to the named channels (oEmbed, 2026-11-26 09:33 UTC). Segments remain UNVERIFIED (HOLD). |
| F14 | Low | The #1330 commits carry no `Signed-off-by` trailer. | `git log` | Not changed. #1330 is the owner's branch. |
| F15 | Low | Packet claim C01 says "600 paired runs". These are 200 seeds × 3 arms, paired by seed, not 600 pairs. | README C01 | Corrected wording in `README_v2.md`. |
| F16 | Info | "missing receipt" is labelled valid and held. All 12 "valid-but-held" cases in v1 come from it. This is a defensible fail-closed choice, and it is disclosed. | observed.json | Kept. v2 adds a second disclosed valid-held class (caveat case/space variant) to show over-strictness cost. |

Credit to v1: its README already disclosed that the principal comparison is not authentication (F1), that the duplicate fixture uses a prepopulated seen set (F2), that the reserve gate is true by construction (F11) and that medium effect is not measured (F10). These findings add that the controls as written still report a pass for cases that would fail, and that the PR text counts them as passed checks.

## Contradictions preserved (not resolved by this audit)
- C1: #1330 body says "Nine synthetic control checks passed", but F4 shows one of them is a constant.
- C2: The README frames "Correction fixture accepted 12/12" as correction retention, but F7 shows it is a no-op.
- C3: The #1329 comment says "earlier unsupported 600-run numbers superseded", but there is no locatable prior claim (F12).
- C4: The v1 code comment says the trusted context is "not agent text", but the principal and revision are read from the request (F1, F3).
- C5: The issue says sources are "attached with evidence", but the README says "no third-party transcript reproduced" and gives no custody hashes (F13).
- C6: `lasting-light-ai/PUBLIC_ENGAGEMENT_STRATEGY.md` sets engagement targets (for example "25%+ click-through") and budgeted staff. #1329 says "no inference from views or engagement to truth" and "no spending".
- C7: v2's own claims come from the same evaluator who wrote v2. They are not independent and need a second evaluator.

## v2 results (`observed_v2.json`, reproduced by `node replay_v2.mjs`)
- Arms A and B equal v1 exactly. Arm D (gate + ordering) equals v1 arm C exactly. This cross-checks the two implementations.
- Arm C (gate only, fixed order): reserve kept in 200/200 runs, 0 violations (by construction), useful work 591.98 vs 609.72 (A) and 609.42 (B).
  - Paired C−B: mean −17.44, lower in 200/200 seeds.
- Arm E: 300 bypass attempts per run, 300 blocked, and no change in useful work.
- Controls: 20 of 20 computed controls behave as expected. They cover duplicate, forged id, self-asserted principal, cross-agent approval, stale revision (two forms), withdrawal after approval, over cap, reserve, six bad-amount forms, a prototype key, a null request, and the audit's clean and mutated states.
- Communication (12 base fixtures × 15 mutations per medium; media differ only in channel count). Results per medium:

| Medium | Strict: correct release | Strict: false release | Strict: valid held | Naive: false release | Raw: false release |
|---|---|---|---|---|---|
| article | 24 | 0 | 24 | 48 | 132 |
| conventional video script | 24 | 0 | 24 | 72 | 132 |
| Witness video script | 24 | 0 | 24 | 72 | 132 |

  - Strict valid-held cases are disclosed: 12 missing receipt and 12 caveat case/space variant.

## Cross-check against the parallel Claude audit (#1331, #1332), not treated as ground truth
#1331 (stacked on #1330) was opened while this audit ran. It independently reports the same core problems as F4, F5, F6, F7, F11 and F12 (its A1, A2, A3, A6, A4, A10).
Points of difference, preserved rather than resolved:
- D1: #1331 keeps the v1 `gate()` predicate and has the harness call it with a literal `principal:"human:owner"`. A forged principal string (F1), a copied revision (F3) and extra request fields are therefore still accepted by its gate. In its simulation, forgery cannot be represented because the harness writes the principal. Checked locally against the #1331 branch head 5c61d020: `gate({principal:"human:owner",revision:2,id:"x",amount:4}, ctx)` returns true.
- D2: #1331 keeps the v1 communication verifier, so F8 (extra-field smuggling) and F9 (truthy receipt) remain there. It renames the correction metric instead of adding a correction transform.
- D3: #1331 ablates arm C into consent, reserve and order and reports that consent alone raises useful work (613.79). v2 here separates only gate versus ordering. The two decompositions are complementary and neither is verified by a second party.
- D4: #1331 rewrites `replay.mjs` and `observed.json` in place on the #1330 branch (history keeps the original). This audit keeps a frozen copy instead. Which preservation rule applies is for the owner or Night.
- D5: #1331 says the nine videos were unreachable from its session. This audit resolved all nine IDs to the named channels (SOURCES.md); segment content is still unverified by either.

## What still cannot be claimed
These are not tested: live agents, human comprehension, answer-engine behaviour, security against an open-ended adversary, novelty, public effect and ACAT qualification. The #750 scoring blocker stays.
