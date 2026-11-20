# Q-REFERENT-DECAY-FOLLOWON-01 — the options `Q-REFERENT-DECAY-01` did not adopt: generate restated facts (D), grade claim-to-source links in prose (C), and the standing deferral of source hashing (B)

**Z1 Proposer:** Claude (Z1)
**Date Submitted:** 2026-11-20
**Status:** AWAITING Z2 RATIFICATION
**Filed because:** the parent block, `Q-REFERENT-DECAY-01`, was ruled `E, F` (merged in #1268, reconciled in #1269, signature `7392a2e7cd2b715de74573d614b805721dcf91633186ec19afb36809fe25a899`). That adopts option E (lint governance-status claims) and option F (audit whether gates ever fire) as directions, each a later separate pull request. It does not adopt D or C, and B stays deferred. A ratified block takes no second ruling, so what it left out can return only as a new block. This is that block.

This file decides nothing and changes no file other than itself and the index.

## What Z2 is asked to decide

1. **Option D: generate the facts that get restated.** Replace a copied constant with a generated reference where the fact is structured. The open question is scope: which facts get promoted. The parent says that list would come back to Night as its own question, so this block asks for the mechanism first and the list second. Limit, in the parent's words: structured facts only; it does nothing for an argumentative claim.
2. **Option C: edge-state grading on claim-to-source links in prose,** as a standing discipline. It uses the five states `CLAIMED, SPECIFIED, IMPLEMENTED, TESTED, OBSERVED`. The parent calls it a discipline, not an automation: the author still grades their own edge, so it can be gamed, but a claim written as `CLAIMED` reads as a promise and not as fact.

Option B is **not asked**. It is recorded below so that its deferral carries its ending condition.

Z1's lean, not a decision: D after E and F are in place, because E and F are the checks that would show which facts keep going stale. C only if Night wants the discipline for prose; it is the cheapest option and the weakest.

## Checked on 2026-11-20 (main `71414758`)

- **C shares a scale with a ratified direction, not its scope.** Ask 1 of `Q-AGENT-CHECKIN-CALIBRATION-01` was ruled `ratify 1-3`: adopt the same five-state grading into `INTENT_GRAPH.yaml` v0.2 **edges**. Option C grades **prose** links. A ruling on C does not rule the graph-schema change, and the reverse. `INTENT_GRAPH.yaml` is still `version: 1` with no edge-state field, so nothing is built yet.
- **B's ending condition is unconfirmed.** The parent names "section-level anchoring exists" as the observation that would end B's deferral, under the proposed leg 3 of `Q-DEFERRAL-RULE-01`. That block is still `awaiting_z2` in `INDEX.yaml`. A search outside `z1-inbox/` for "section-level anchor" finds nothing. So B stays deferred, and nothing here changes that.
- **D's premise is the parent's, not re-counted.** The parent says `INTENT_GRAPH.md`, `TOOLS_MANIFEST.md` and `Z1_INBOX_INDEX.md` are generated and gated by `--check` and have never drifted. Z1 did not re-verify that today.
- **E and F are not both built.** The `E, F` ruling is a direction. Option F is already partly in place: `.github/workflows/workflow-lint.yml` has an advisory step, "Has each gate ever actually fired?" (line 86), so adopting F means extending that audit, as the parent says, not starting it. For E, the parent's check on 2026-11-16 found no status-claim check in `tools/` by name; Z1 did not search again today.
- **Not re-checked:** the parent's five instances and the greps in its falsifier.

## Z2 Review Checklist

- [ ] Question 1: adopt D as a direction? If yes, say whether the list of facts to promote comes back as its own block.
- [ ] Question 2: adopt C as a standing discipline for prose, knowing it shares a scale with the graph ruling but not its scope.
- [ ] B stays deferred. Nothing to decide, unless Night wants it asked.

## Falsifier

Event-based, no clock. This block is wrong, and should be withdrawn in whole or in part, if any of these happens:

- (a) the `E` pull request, or the extension of the F audit, is built and shows that no restated fact in the tree has ever drifted. Then D has no instance to fix, and question 1 is moot.
- (b) the v0.2 graph pull request lands with a different state vocabulary than the five states above. Question 2 would then use a scale that no longer matches the graph.
- (c) a section-level anchoring mechanism is found outside `z1-inbox/`. B's ending observation has then arrived, and B should be asked, not deferred.
