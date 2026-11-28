# KG v0.2 proposal: exact-head evidence report

**Status:** Z1 proposal. `authority_effect` NONE. Not ratified. Not merged. No Z2 label. No canonical promotion. No agent activation.
**PR:** humanaios-ui/operations#1310 (draft) · **Branch:** `claude/kg-v0-2-proposal-rlla8q`
**Audit date:** 2026-11-23

## 1. What was audited (exact pins)

| Item | Pin |
|:--|:--|
| Audited input head | `7426e6bdcef72eea5a7f192b0a894a3e471017e2` (first commit of the PR) |
| Proposal file | `kg/humanaios_kg_v0_2_proposal.json` |
| Proposal git blob | `aec9d323c8d1c4fe198f809c99fbc9a92377f323` |
| Proposal sha256 | `b842f692c3f56f4649747c671e752a7d000c1abf226b114c62cec6bf6a96a5e3` |
| Upload sha256 (same value) | `b842f692c3f56f4649747c671e752a7d000c1abf226b114c62cec6bf6a96a5e3` |
| Main when audited | `e0e43053a45acc7f259ef564e6aff27de487a311` |
| Report-bearing head | The PR head after this report is pushed. A file cannot hold its own commit hash, so that SHA is stated in the PR, not here. |

The uploaded proposal is unchanged. Nothing in this commit edits it. `tests/test_kg_v0_2_check.py` pins its bytes.

Later commits on the branch are not part of this audit. They were pushed under the Carly R. Anderson account: a second structural checker and its tests (`2ed90f29`, `20aa7c5d`), the 358-node receipt (`4e647ace`), a second opinion (`962d7a22`), and the removal of that second checker (`758011a9`, `5a6cc6b9`). Only the receipt and the second opinion remain. The audit covers `7426e6bd` and my own files. The PR head moves as commits land; read the head SHA from the PR.

## 2. Confirmed

- 19 new construct nodes (C01 to C19).
- 73 edges, ids 17 to 89.
- 56 `recorded`, 17 `candidate`.
- All 73 are `unratified`.
- Commit `2e51c50f10751cd93b6e3bc386d5a985eea10562` exists (2026-09-28). Its full history was fetched; the first clone was shallow.
- v0.1 has 22 nodes and 16 edges. The live Supabase tables `kg_nodes` and `kg_edges` hold 22 and 16 rows. They match.

## 3. Corrections asked for, and what was done

| # | Ask | Result |
|:--|:--|:--|
| 1 | Keep IC-065 as registry id. Keep IC-064 in the commit. Overwrite neither. | Done. See section 4. |
| 2 | Audit the 56 recorded links. Separate four things. | Done. See section 5. File: `kg/humanaios_kg_v0_2_recorded_link_audit.json`. |
| 3 | A registered hypothesis is not an outcome. | One violation found (edge 77). Proposed fix in the overlay. Section 6. |
| 4 | Validate external reference targets. | 38 of 56 verified. 18 cannot be checked from here. Section 7. |
| 5 | Keep the GitHub graph apart from the 358-node research graph. Propose a pinned crosswalk. | Crosswalk written, zero rows. A later commit by Carly supplies a receipt with digests for the private files. This audit could not read them. Section 8. |
| 6 | Keep C19's unknown date. Keep A02 and A06 without evidence. | Kept. A test enforces it. |
| 7 | Offline tests. | 26 tests. Section 9. |

## 4. IC-064 and IC-065

- Commit subject, quoted exactly: `Z2: ratify IC-064 evidence-ledger-gap-pr465 from comparison-engine-v1.0-analysis`.
- The commit adds `REGISTERED.md` and `z1-inbox/2026-09-28/IC-064-EVIDENCE-LEDGER-GAP-PR465.md`. Its author is Claude.
- `REGISTERED.md` at this head has an `IC-065` entry for the PR #465 evidence-ledger gap. It has no `IC-064` entry.
- The registry note says IC-064 was already claimed by PR #482 ("still-open, separately-ratified"). This audit did not read PR #482. That claim is unchecked.
- Recommendation: **IC-065 is the registry id. IC-064 stays as history in the commit.** Edge 70 keeps the commit. Edge 80 points to IC-065.
- One small defect: the note on edge 70 paraphrases the subject. The overlay quotes it exactly.
- The IC-065 entry has `zone2_ratification: null` in its front matter. Its body says Night ratified on 2026-09-28 and was confirmed in conversation. The ratification is stated in prose, not in the field.

## 5. The 56 recorded links, four ways

None of the four rows below is independent evidence. Every commit that records a Z2 decision was written by Claude. Nothing here is a signed or authenticated approval.

| Dimension | Result |
|:--|:--|
| **Source exists** | 38 verified. 18 unverifiable (repository outside this session's scope). 0 broken. |
| **Intended dependency** (10 recorded `depends_on` edges) | 3 stated in the record. 3 name or path only. 1 rationale, not a dependency (edge 18). 1 count not reproduced (edge 20). 2 unverifiable (edges 22, 23). The other 46 edges are not `depends_on`. |
| **Approval evidence** (5 `approved_by`) | 3 registry field, written by the filing session. 2 commits transcribed by Claude. 0 authenticated. |
| **Observed outcome** (10 `resulted_in`) | 1 documented fix. 1 hypothesis (not an outcome). 6 findings about the source. 2 registered corrections. 0 independently observed. |

Details that matter:

- **Edge 20.** It says "64 of 139 parsed entries" carry a ratification field and cites IC-031. IC-031 has no such count. A naive parse of this head finds 95 of 153 front-matter blocks with a non-null field. The count is not reproduced.
- **Edge 79.** It cites IC-030 as an outcome of the findings registry. The misfile text (IC-060 and IC-061 filed under held numbers on 2026-09-20, corrected 2026-09-21) is in the `REGISTERED.md` preamble near line 40. The IC-030 entry does not contain it.
- **Edge 69.** The ruling file says "Recorded by: Claude (Z1), as transcription of Z2's decision." Its hash `z1-ratify-zone2-approved-20260913` is a label, not a signature.
- **Edge 38.** The ledger row at seq 0 is a hash-chained ACCEPT by Night, but for a different candidate (`Q-MOLT-PRACTICES-COLLAPSE-01`). It shows the mechanism exists. It does not approve this graph.
- **Self-corroboration.** Four sources cite one registry entry under several relations. C01 cites IC-031 four ways (depends, supported, approved, resulted). C03, C04 and C14 do it twice. One record should count once. The checker warns.
- **Edge 71.** IC-058's field names "Carly (operator)", not "Night".
- **Edge 72.** F-50's ratification approves the finding, not the registry file.

## 6. Hypothesis classed as outcome

Edge 77 says C01 `resulted_in` `registry:H-RCO-01`, `recorded`. H-RCO-01 is a registered hypothesis with status CANDIDATE and no result. The registry says it tests whether the v6.4 fix cuts overstatement by 80 percent over 20 sessions. That has not been measured. The checker raises `E_FALSE_CAUSAL`. The overlay moves the edge to `candidate`.

## 7. External references

- 18 recorded edges cite commits in repositories this session may not read: `empirica-outreach`, `empirica-autonomy`, `empirica-foundation-evaluator`, `empirica-analytics`, `acat-x`, and `LastingLightAI/lastinglightai`. Edge ids: 22, 23, 35, 39, 41, 42, 43, 45, 49, 50, 51, 52, 53, 54, 55, 58, 59, 63.
- They are reported `UNVERIFIABLE_OUT_OF_SCOPE`. They are **not** counted as verified. They are left `recorded` in the proposal.
- 38 verified here: every cited commit resolves in this clone. Registry ids and file paths resolve too. Where a note names a file, the commit touches that file (checked for the six commits whose note names a file).
- Candidate edge 67 cites F-54. F-54 exists only as a heading with no structured fields. The checker accepts it as existing. It is not a pass for support.

## 8. Two graphs, kept apart

- **GitHub graph:** `kg/humanaios_kg_v0_1.json` (22 nodes, 16 edges) plus the v0.2 proposal (19 nodes, 73 edges). Namespace `kg:`.
- **358-node research graph:** namespace `rg:`. This audit first searched for it and found nothing: no file with 358 nodes in the checkout, no Supabase table, no code-search hit.
- **Update, commit `4e647ace` (pushed under the Carly R. Anderson account):** `kg/KG_RESEARCH_GRAPH_358_BOUNDARY_RECEIPT.json` records two private local files with 358 nodes. Latest: `humanaios_evidence_linked_graph_E0_2026-11-23.json`, 358 nodes, 83 edges, sha256 `2109ab9e…b253`. Earlier: `humanaios_merged_knowledge_graph_2026-11-23.json`, 358 nodes, 53 edges, sha256 `f8ddceab…dac`. The receipt says they are not published and not admitted, and that merge is not permitted.
- **What this audit can say:** the digests and counts are the receipt's claim. This audit could not read the files, so it did not check them. The crosswalk records the pin as `RECEIPT_ONLY_BYTES_NOT_AVAILABLE`.
- `chat_graph/` has 195 nodes and 213 edges. It is a third graph. It is named so nobody mistakes it for the 358-node one.
- `kg/humanaios_kg_v0_2_crosswalk_proposal.json` sets the rules: pin both sides by sha256, one row per link, no merging, a shared source never counts as independent. It has **zero rows**, which matches the receipt (`admitted_rows: 0`). A row needs the private file to be releasable or checkable by a verifier.

## 9. Tests

`python3 -m pytest tests/test_kg_v0_2_check.py` runs offline. 26 pass.

- Broken references: missing registry id, missing commit, missing file, unknown node, out-of-scope is not a pass.
- False causal links: hypothesis as outcome, inference as outcome, one record counted four ways.
- Candidate promotion: recorded on inference, candidate with no reason, nothing may be ratified, candidates never count as support.
- Missing approval: unrecorded decision, entry with no ratification field, a ratification field is not authentication.
- Pins: uploaded bytes, counts, C19 empty, A02 and A06 unlinked, IC-064 and IC-065 both kept, overlay only shrinks support.

Run as a gate: `python3 kg/kg_v0_2_check.py` exits 1 on the raw proposal (one error, edge 77). `--overlay kg/humanaios_kg_v0_2_corrections_overlay.json` exits 0.

## 10. Remaining gaps

1. 18 recorded edges cannot be checked from here. Someone with access must read those commits.
2. The 358-node research graph has a receipt (commit `4e647ace`) but its bytes are private and unreadable here. Its digests are unchecked. The crosswalk stays empty until a Z2-authorized release or a verifier can read it.
3. PR #482 was not read. The claim that it holds IC-064 is unchecked.
4. File bodies were not read except `REGISTERED.md`, the Z2 ruling file, and the graph files. Most "stated in record" judgments come from commit subjects, paths and registry fields.
5. The count in edge 20 was tested with a naive parse, not the registry's own parser.
6. No approval in the graph is authenticated. All five `approved_by` edges rest on agent-written records.
7. The overlay is proposed, not applied. The proposal still says 56 recorded. After the overlay: 53 recorded, 20 candidate.
8. The checker lives in `kg/`, not `tools/`, to avoid a tools-manifest entry. Z2 can move it.
9. `tools/repo_health.py` and the document-control gate were not run locally.

## 11. Independent review status

**None.**

- The proposal was written by a Claude chat session. This audit was written by a Claude Code session. Same model family. Not independent.
- Three commits were pushed under the Carly R. Anderson account: a second checker with 15 tests (since removed), the 358-node receipt and a second opinion. The CI provenance bot classed them `SHARED_ACCOUNT_ORIGIN_UNKNOWN`, so who or what wrote them is not established. They are not a review of the proposal, and I did not audit them. The receipt does not authorize anything.
- No human has reviewed the PR. CodeRabbit skipped it (draft). No review event was received.
- At the audited head 7426e6bd, 14 completed checks passed and 6 were skipped. That is automated evidence only. It is not review.
- Night has not seen or ratified anything here.

## 12. Files in this change

| File | Role |
|:--|:--|
| `kg/kg_v0_2_check.py` | Offline checker |
| `tests/test_kg_v0_2_check.py` | 26 offline tests |
| `kg/humanaios_kg_v0_2_recorded_link_audit.json` | Per-edge result for the 56 recorded links |
| `kg/humanaios_kg_v0_2_corrections_overlay.json` | Five proposed corrections, not applied |
| `kg/humanaios_kg_v0_2_crosswalk_proposal.json` | Pinned crosswalk proposal, zero rows |
| `docs/design/KG_V0_2_EVIDENCE_REPORT.md` | This report |

Files pushed under the Carly R. Anderson account, not audited here: `kg/KG_RESEARCH_GRAPH_358_BOUNDARY_RECEIPT.json`, `kg/KG_V0_2_SECOND_OPINION_2026-11-23.md`.

Night ratifies. This PR must not be merged until Night does.
