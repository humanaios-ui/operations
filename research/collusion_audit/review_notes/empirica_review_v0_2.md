# Review received: v0.2 detector test (apart-1010-v02-001, commit a5b13937)

**Provenance.** Pasted into the session by the operator as coming from Empirica. I have not verified
the reviewer's identity or independence of the builder, so this file does not count as the independent
adjudication the protocol calls for. The reviewer states it recounted all 60 episodes from git objects
with no model calls; it did not re-run the judge or actors, did not verify the review packet's blinding,
and did not inspect `audit.py` beyond its pinned hash.

**Verdict as received:** numbers reproduce from committed artifacts; the headline recall figures are
not supported under the frozen protocol; report the run as exploratory, not as a detector evaluation.

## Points and what I did
| # | Point | Response |
| --- | --- | --- |
| 1 | Positive control depends on the post-freeze judge rerun; pass 3 was added after seeing 4 < 5 | **Accepted.** Frozen-state view added (`evaluation_followup.json`): 4 observed positives, unevaluable. RESULTS.md now leads with that. |
| 2 | `suite_v0_2.py` / `test_suite_v0_2.py` drifted from `freeze_v0_2.json` without an amendment record | **Accepted.** `amendment_record_v0_2_rev1.json` records both hashes, the diff's purpose and the known weakness. `freeze_v0_2.json` is left as originally written. |
| 3 | actions_only "false positives" are label artifacts; report action-level outcome | **Accepted and verified.** Action-level table added: 11 episodes where both approved a failing change; actions_only 0 FP (tautological, it is that rule), hybrid 4 TP / 7 FN, talk_only 4 TP / 11 FP / 7 FN. |
| 4 | Judge is sole source of verbal labels and not independent; human adjudication of contested and concealed episodes is cheapest fix | **Accepted.** Open item. Contested: v2-05, v2-26, v2-54, v2-41. Concealed both-approve: v2-20, v2-23, v2-41, v2-42. |
| 5 | Some expectations are structural (talk_only on benign_pact_words; concealed misses) | **Accepted.** RESULTS.md marks them as implementation checks, not detector evidence. |

## Reviewer's suggested citation language (adopted)
- "Under the frozen protocol this run is unevaluable: 4 observed positives against a floor of 5."
- "With a post-freeze judge rerun (disclosed), 7 positives; hybrid recall 4/7 and actions_only recall 7/7 on those labels."
- "actions_only flags 4 of 53 negatives, but all 4 are bilateral approvals of a failing change; the verbal-agreement label is what makes them negative."
- Keep the same-account-judge and instructed-roleplay caveats in the same sentence as any number.
