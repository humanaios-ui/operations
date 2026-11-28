# Independent Z1 second opinion — KG v0.2 proposal, 2026-11-23

**Scope:** [PR #1310](https://github.com/humanaios-ui/operations/pull/1310), `kg/humanaios_kg_v0_2_proposal.json`. **Authority:** NONE; no Z2 act, merge or deployment.

## 1. Exact inputs and boundaries

- v0.1 graph blob: `1a1e2aa2693724ba4803d2bf5961e18fcc6b3acb`; 22 declared nodes, 16 edges.
- v0.2 uploaded/committed graph blob: `aec9d323c8d1c4fe198f809c99fbc9a92377f323`; 19 additional constructs, 73 edges (56 `recorded`, 17 `candidate`), all `unratified`.
- The **separate 358-node research graph** was located in the conversation working container, not in the repository. Read-only metadata and SHA-256 are in `kg/KG_RESEARCH_GRAPH_358_BOUNDARY_RECEIPT.json`. No source rows have been published or mapped. Claude's crosswalk proposal correctly has **zero admitted crosswalk rows**.
- A separate **temporary local** structural review exercised 15 synthetic negative cases. Its duplicate checker and tests were removed from this PR after CI surfaced Builder/tool-manifest failures; the maintained repository checker is Claude's `kg/kg_v0_2_check.py` with its 26-case suite. No second validation tool is installed or claimed.

## 2. Independent cross-repository source check

From the 56 links marked `recorded`, **18** cite commit references beyond the operations repository. On 2026-11-23, connected GitHub commit-read checks could resolve **16/18** references to full commit objects; **2/18 returned 404**. A 404 here means *not verified through this connector*, not proof the commit never existed. These checks establish the *existence of commits*, not whether the prose interpretation or dependency/outcome relation is true.

The existence check improves on the earlier audit's `UNVERIFIABLE_OUT_OF_SCOPE` classification for these 16 references, but it does not change their ratification status. For privacy, this public report intentionally omits repository names, full commit hashes, private file paths and nonpublic source payloads.

## 3. Review findings

| ID | Observation | Disposition |
|---|---|---|
| R01 | Source existence does not prove a dependency, cause, independent endorsement or measured benefit | Retain separate evidence classes; do not auto-promote `recorded` |
| R02 | The v0.2 proposal has 14 `resulted_in` edges. A registry entry or planned study is not proof of real-world benefit | All 14 need outcome-specific checks; no human-benefit receipt established here |
| R03 | Edge 77 describes a registered hypothesis as an outcome | Preserve original draft; review Claude's correction overlay before any successor version |
| R04 | IC-064 is the historical September 28 commit wording. IC-065 is the index entry for PR #465 | Retain both as distinct provenance; no renumbering without Z2 action |
| R05 | The other research graph has 358 nodes and 83 edges in the E0 variant. It is a different provenance/namespace than the 22+19-node GitHub graph | No merge; no crosswalk rows until the source has passed privacy review |
| R06 | The public PR currently contains pointers into repositories classified PRIVATE by GitHub. Existing exposure needs a public/private data-boundary review | **PRIVACY HOLD**. Avoid further public disclosure. Human owner decides whether sanitization and commit-history repair are needed |

## 4. Reproducible checks

The maintained repository tests can be invoked in a checkout as follows:

```bash
python3 -m unittest tests.test_kg_v0_2_check -v
```

Claude's checker and its fixtures are the retained implementation. The independent temporary local exercise passed **15/15** synthetic structural tests, but the duplicate source was removed from the PR and does not provide a second maintained validation system. That exercise does not establish a verified human outcome. Exact-head CI and the retained 26-test suite remain the controlling code evidence.

The semantic checker and its separate overlay may surface additional evidence defects. Neither checker authorizes agent action, canonical graph promotion or a GitHub merge.

## 5. Decision boundary

**RECOMMENDATION: KEEP DRAFT / HOLD PROMOTION.** Preserve the two knowledge graphs independently; safeguard private sources; reconcile the documented semantic corrections; and obtain an independent review on the current final head. Only Night/Z2 controls ratification, acceptance and issue closure.