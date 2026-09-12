# Evidence Table — Reflexive Calibration Paper v1.0

**Companion to:** `docs/REFLEXIVE_CALIBRATION_PAPER_V1_0.md`
**Method:** Every numeric claim in the manuscript is listed here with the committed file it was read from. Claims that could not be traced to a committed file were removed from the manuscript rather than softened.
**Traced:** 2026-09-12, working tree at branch `claude/research-paper-work-review-xmzsdl`.
**Not traced:** no live Supabase query was run. The Supabase connector is unauthorized in this session, so every live-corpus figure below is a committed snapshot and is dated as such.

---

## Instrument and corpus

| Claim | Value | Source |
|---|---|---|
| Frozen corpus, total submissions | 629 | `CURRENT.md` §5; `SEED.md` §3.3 |
| Frozen corpus, completed Phase 1 | 516 | `CURRENT.md` §5; `SEED.md` §3.3 |
| Frozen corpus, computable Learning Index | 307 | `CURRENT.md` §5; `SEED.md` §3.3 |
| Frozen corpus mean Learning Index | 0.8632 | `CURRENT.md` §5; `SEED.md` §3.3 |
| Collection window | 2026-02-15 19:49:44 UTC – 2026-03-23 04:03:27 UTC | `CURRENT.md` §5 |
| Dataset license / format / columns | CC BY 4.0 · Parquet + CSV · 22 columns | `CURRENT.md` §5 |
| Superseded N declaration (IC-022) | 630 / 517 / 308 | `CURRENT.md` §5 |
| Live corpus snapshot | N = 95, N_LI = 91, mean LI = 0.9830 | `docs/ACAT_PAPER_V6_0_DRAFT.md` §4 |
| Verified-pair subset | N = 18, mean LI = 0.9971 | `docs/ACAT_PAPER_V6_0_DRAFT.md` §4 |
| Instrument-variant tagging coverage | 42 of 95 | `docs/ACAT_PAPER_V6_0_DRAFT.md` §4 |
| H-SELF-01 inflation estimate | 0.14–0.16 LI | `docs/ACAT_PAPER_V6_0_DRAFT.md` §4 |
| Human baseline | LI = 0.8220, n = 65 | `SEED.md` §3.3 |
| Learning Index definition (ratio) | Core 6 P3 total ÷ Core 6 P1 total | `SEED.md` §3.1; `docs/ACAT_PAPER_V6_0_DRAFT.md` §2.1 |
| Learning Index cap | 2.0 | `docs/ACAT_PAPER_V6_0_DRAFT.md` §2.1 |
| Twelfth dimension added | Handoff Appropriateness, 2026-04-24 | `CURRENT.md` §6 |
| Twelve-dimension list | see manuscript §3.3 | `SEED.md` §3.2 |

## Psychometrics

| Claim | Value | Source |
|---|---|---|
| Cronbach's α | 0.901 | `SEED.md` L122; verified in `audits/LONGVIEW_STATS_VERIFICATION_S-070126.md` L18 |
| PC1 explained variance | 68.9% | `SEED.md` L122; verified in `audits/LONGVIEW_STATS_VERIFICATION_S-070126.md` L19 |
| PC2 explained variance | 10.8% | `docs/RESEARCH_OVERVIEW.md` L28; `audits/LONGVIEW_STATS_VERIFICATION_S-070126.md` L20 |
| Harm Independence Metric | 0.854 on Harm Awareness | `audits/LONGVIEW_STATS_VERIFICATION_S-070126.md` L20 |

The three verification rows above are marked VERIFIED in a July 2026 stats audit against `CURRENT.md` and `REGISTERED.md`. That audit predates the July 8 revision that removed the maintained headline block from `CURRENT.md` §4, so its line references no longer resolve; the values are retained here on the strength of the audit record and `SEED.md`.

## Findings

| Claim | Value | Source |
|---|---|---|
| F-20 RLHF inflation gradient | ~2.09 points | `REGISTERED.md` L190 |
| F-20 dimension split | Service / Harm / Autonomy above Humility / Value / Truthfulness | `REGISTERED.md` L190 |
| F-20 evidence class | M, no independent replication | `REGISTERED.md` L193–199 |
| F-21 Phase 1 Humility mean | 73.95, n = 516 | `REGISTERED.md` L205 region; `SEED.md` L112 |
| F-21 status / date | CONFIRMED, 2026-04-05 | `REGISTERED.md` L50 |
| F-48 Phase 1 Humility mean | 74.02, N = 524 | `REGISTERED.md` L904 |
| F-48 Phase 3 Humility mean | 67.06, N = 16 paired | `REGISTERED.md` L904 |
| F-48 high-LI Humility | 86.21, LI ≥ 1.0, N = 34 | `REGISTERED.md` L904 |
| F-48 per-agent floor rate | 9 of 19 families with ≥5 submissions | `REGISTERED.md` L904 |
| F-47 non-completion rate | 96.6% — 449 of 465 P1 sessions with `pair_id` lack a P3 | `REGISTERED.md` L881, L3188 |
| F-47 substrate | `ACAT_corpus_v2_clean_full.csv`, N = 608 | `REGISTERED.md` L3188 |
| F-47 ratification | Night · 2026-06-06 · S-060626-01, CANDIDATE | `REGISTERED.md` L876–878 |
| F-22 evidence class | I — architectural inference | `REGISTERED.md` F-22 addendum |

## Recomputation from committed data (manuscript §3.7)

Source file for every row below: `acat/data/acat_corpus_v2.csv`, 604 data rows, 28 columns. Computed 2026-09-12 with the standard library only; the script is reproduced at the end of this section.

| Quantity | Recomputed | Registry value | Agreement |
|---|---|---|---|
| Phase 1 rows | 524 | 524 (F-48 substrate) | exact |
| Phase 3 rows | 80 | — | — |
| Phase 1 Humility mean | 74.02 | 74.02 (F-48) | exact |
| Humility lowest of Core 6 | yes, both subsets | yes (F-21, F-48) | confirmed |
| Phase 3 Humility mean (all 80 P3 rows) | 68.15 | 67.06 over N=16 paired (F-48) | different subset |
| Distinct Phase 1 `pair_id` | 465 | 465 (F-47) | exact |
| Unmatched Phase 1 `pair_id` | 450 | 449 (F-47) | one session |
| Non-completion rate | 96.8% | 96.6% (F-47) | 0.2 pt |
| Rows with computable LI | 274 | 307 (archive) | different file |
| Mean LI | 0.8532 | 0.8632 (archive) | different file |
| `human-assessment` rows | 65 | n = 65 (`SEED.md`) | exact |
| `human-assessment` rows with LI | 29 | not stated | new |
| Human mean LI | 0.8165 | 0.8220 (`SEED.md`) | see IC-CAND-07 |
| RLHF gradient, all layers | +1.433, 95% CI [0.753, 2.114], t = 4.13, n = 524 | ~2.09 (F-20) | direction yes, magnitude no |
| RLHF gradient, AI layer only | +1.400, 95% CI [0.666, 2.134], t = 3.74, n = 399 | ~2.09 (F-20) | direction yes, magnitude no |

Manuscript §3.7 rounds both intervals to two decimals: [0.75, 2.11] and [0.67, 2.13].

### Phase 1 Core 6 dimension means, both subsets

| Dimension | All layers (n=524) | AI self-report only (n=399) |
|---|---|---|
| Humility | 74.02 | 75.71 |
| Harm Awareness | 75.35 | 76.71 |
| Value Alignment | 76.24 | 77.66 |
| Autonomy Respect | 76.83 | 78.64 |
| Truthfulness | 77.05 | 78.79 |
| Service Orientation | 79.43 | 81.02 |

Rank order is identical across the two subsets. Every AI-only mean is higher than its all-layers counterpart, which is consistent with the 65 human-assessment rows scoring below the AI rows, and with the human baseline LI sitting below the AI band.

Gradient method: within-row, `mean(service, harm, autonomy) − mean(humility, value, truth)` per submission, then mean across submissions. Confidence interval is the normal approximation on the standard error of that mean. Computing instead as a difference of group means over the same subset gives +1.43 (all layers) and +1.40 (AI only), matching the within-row figure to two decimals.

Three rows above generated candidate registry entries: IC-CAND-06 (corpus provenance), F-CAND-01 (gradient magnitude and falsifier specification), IC-CAND-07 (human baseline n conflation). See `NUMERIC_CONFLICT_REGISTER.md`.

**Reproduction.** The recomputation is a single pass over the CSV with `csv.DictReader` and `statistics`; no dependencies. To reproduce: read `acat/data/acat_corpus_v2.csv`, split on the `phase` column, and compute per-dimension means over the six Core 6 columns (`truth`, `service`, `harm`, `autonomy`, `value`, `humility`). Pair completion uses the `pair_id` column, comparing the distinct-value sets for `phase1` and `phase3`. The human baseline uses `layer == 'human-assessment'` and the `learning_index` column.

## Registry scale

| Claim | Value | Method |
|---|---|---|
| Schema-conformant entries | 124 total: 41 F, 41 IC, 42 H | Count of unique `id:` fields in YAML front matter, `REGISTERED.md` |
| Alternative count | 49 F, 39 IC, 47 H | Count of `### <class>-` section headers |
| Finding number range | F-18 → F-61, contiguous, 44 numbers | Regex over `REGISTERED.md` |
| Correction number range | IC-001 → IC-058, 43 present | Regex; gaps at IC-002–017 are early grouped registrations |
| Hypothesis slugs | 24 distinct `H-SLUG-NN` identifiers | Regex |
| Registry last updated | 2026-08-15 (S-081526-NN) | `REGISTERED.md` header |

Both counts are reported in the manuscript. They differ because some entries carry addenda under their own headers and some early corrections were registered in groups.

## Governance apparatus

| Claim | Value | Source |
|---|---|---|
| Zone roles and rights | Z1 propose / Z2 ratify / Z3 execute | `CLAUDE.md`; `GOVERNANCE.md` "ZONE SYSTEM" |
| Z2 decision window | 48h routine | `CLAUDE.md` "Admiral" |
| Anti-cascade rules | 5 rules, K = 3 open molts | `CLAUDE.md` "Molt Decisions" |
| Molt state machine | PROPOSED → … → KEPT / REVERTED | `MOLT_STATE.md` |
| Ledger entries | 165 | `wc -l ledgers/NF_LEDGER.jsonl` |
| Ledger event types | 106 PIN, 58 TOKEN, 1 OPEN | JSON parse of `ledgers/NF_LEDGER.jsonl` |
| Hash chaining | each entry carries `prev_hash`, `main_sha`, `registered_sha` | `ledgers/NF_LEDGER.jsonl` line 1 |
| CI workflow count | 40 | `ls .github/workflows/` |
| Drift signals | 15 named, each mapped to an ACAT dimension | `GOVERNANCE.md` "DRIFT SIGNALS" |
| P19 text | "detection instrument, not a compliance instrument" | `GOVERNANCE.md` P19 |
| Structural limitations | no persistent memory, volatile working memory, no live reads without tools, Zone 1 bias | `GOVERNANCE.md` "CLAUDE'S STRUCTURAL LIMITATIONS" |
| Principle ladder | 26 principles in F1/F2/F3 tiers | `CURRENT.md` §3; `GOVERNANCE.md` |
| Receipt reconciliation rationale | IC-031 receipt overstatement | `CLAUDE.md` §B.6; `receipt_reconciliation.py` |
| IC-038 | stale countdown carried across five sessions | `CURRENT.md` §1 |
| Maintained-headline recurrence | second occurrence named in the 2026-07-08 changelog entry | `CURRENT.md` §9 |

## Reflexive results

| Claim | Value | Source |
|---|---|---|
| Adversarial mean score | 41.67 / 100 | `z1-inbox/2026-09-08/CYCLE_2_ADVERSARIAL_REPORT.md` §E |
| Per-dimension scores | 12 rows as tabulated in manuscript §5.1 | same, §E |
| Arithmetic check | 500 ÷ 12 = 41.67 ✓ | computed from the table |
| Critic's verdict phrase | "structural competence but governance weakness" | same, §E |
| Graph size | 19 nodes, 44 edges | `z1-inbox/2026-09-08/CYCLE_3_FALSIFICATION_REPORT.md` §2.1 |
| Cycle 1 novelty | 100% (18 of 18), independent human critic | `CYCLE_1_EXTERNAL_REVIEW.md` §B |
| Cycle 2 novelty | 100% (10 of 10), adversarial peer | `CYCLE_2_ADVERSARIAL_REPORT.md` §D |
| Cycle 3 novelty | 75.6% | `z1-inbox/2026-09-08/P_J4_BRIER_EXPLAINED.md` |
| Pre-registered prediction P-J4 | novelty ≥ 0.30 in first 5 blind reviews, confidence 0.50 | `P_J4_BRIER_EXPLAINED.md` |
| Brier score | 0.25 = (0.50 − 1.0)² | `P_J4_BRIER_EXPLAINED.md` |
| Cycles operated | 3 of 40 | `Z2_RULINGS_2026-09-08.md` closing line |
| Cycle 3 findings | 17 findings, 4 severity tiers, 6 attack chains, 8 falsification tests | `CYCLE_3_FALSIFICATION_REPORT.md` §1 |
| Cycle 3 verdict | DO NOT RATIFY in current form | `CYCLE_3_FALSIFICATION_REPORT.md` §1 |
| Lead objection | "Z2 is an Unaudited Absolute Monarch" (ADV-001, CRITICAL) | `CYCLE_3_FALSIFICATION_REPORT.md` §4.1 |
| Z2 disposition | all 17 accepted as factual | `Z2_RULINGS_2026-09-08.md` Ruling 1 |
| Seven structural blockers | as enumerated in manuscript §5.2 | `Z2_RULINGS_2026-09-08.md` Ruling 1 |
| Ratification hash | `cycle-3-falsification-approved-20260908` | `Z2_RULINGS_2026-09-08.md` Ruling 1 |

## Verification cascade (F-53 / H-AICASCADE-01)

| Claim | Value | Source |
|---|---|---|
| Design | 2 cited claims, 4 independent AI reviewers, primary-source check | `docs/VERIFICATION_CASCADE_FIELD_NOTE_S061726.md` |
| Reviewer D | missed one verifiable claim, wrong value on the second, introduced an unsourced figure | same, comparison table |
| Reviewer C | flagged inability to confirm a paper that does exist | same |
| Conclusion | stated confidence did not correlate with accuracy | same, "Observation" |
| Status / promotion gate | CANDIDATE; 2 further independent chains required | same, "Status" |
| Date | 2026-06-17 | same, header |

## Document-genre clustering

| Claim | Value | Source |
|---|---|---|
| CGR position-paper outline | LI 0.7317 (Core 6 = 439/600) | `docs/ACAT_ANALYSIS_CGR_POSITION_PAPER_S061726.md` |
| Positioning cluster band | 0.70–0.74 | same |
| Prior positioning batch | Executive Brief 0.6983, EAF 0.7267, Runtime Diagnostic 0.7433 | same |
| Implementation contracts | Vault 0.8350, Builder 0.8500 | same |
| Corpus mean reference | 0.8632 | same |
| Tool | `acat_document_analyzer_v1.1.0`, interactive mode | same, header |

## Tool-level application

| Claim | Value | Source |
|---|---|---|
| Tools assessed | 5 evaluator-owned tools | `ZONE_1_TO_2_TEST_RESULTS.md` |
| Learning Index range | 1.02 – 1.07, average 1.05 | same |
| Date | 2026-07-14 | same, header |

This row set is not cited in the manuscript body. It is retained here because it is a fourth application surface (instrument → software tooling) and is relevant to any future revision.

## Publication status

| Claim | Value | Source |
|---|---|---|
| arXiv submission | `submit/7336774`, cs.AI, on hold since March 2026 | `deliverables/arxiv-hold-action-plan.md` |
| Likely causes | missing TeX source; or cs.AI endorsement gap under the Jan 2026 policy | same |
| Dataset location | `huggingface.co/datasets/HumanAIOS2026/acat-assessments` | `CURRENT.md` §5 |
| Dataset licence | CC BY 4.0 | `CURRENT.md` §5 |
| Dual CC-BY-NC proposal | proposed, not ratified | `docs/ACAT_PAPER_V6_0_DRAFT.md` §7 |
