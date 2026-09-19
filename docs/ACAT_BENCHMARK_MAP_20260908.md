---
title: ACAT dimensions ↔ market-standard benchmarks — navigator mapping
revision: 0
status: draft
lifecycle: filed
consumer: ui/intent-os-humanaios-v3_3.html   # board step 12; becomes CONST benchmark_map when d10/d11 rule
evidence_tier: LAID (desk mapping; no ACAT run against any board operated)
---

# ACAT ↔ market benchmarks (read 2026-09-08)

**Landing correction (Z1, same day):** the report's GAP-SPEC-01 said the operations repo could not be read. It was read at landing: `acat/contracts/` on main holds 5 schema files carrying all 12 dimension keys (`truth service harm autonomy value humility scheme power syc consist fair handoff`). GAP-SPEC-01 is therefore CLOSED for the dimension list; the receipt/provenance-tier taxonomies (CLAIM/CLAIM+LINK/VERIFIED · SELF/CRED/OUTCOME) remain REPORTED until a reader cites their file paths. GAP-DIM-02 (12 vs 11 vs 6 on the public site) stays OPEN.

## The one-line finding
ACAT measures the gap between what a system says about its behavior (Phase 1) and what it scores after seeing calibration evidence (Phase 3). No capability leaderboard measures a gap. The nearest kin are honesty and calibration evals — MASK (honesty ≠ accuracy), SimpleQA's abstention slice, ForecastBench (Brier) — and they are partial matches.

## Mapping (every row LAID)
| ACAT | closest boards | match | not covered by the board |
|---|---|---|---|
| truth | SimpleQA / Verified, TruthfulQA, MASK | partial | the self-report gap |
| service | — (LMArena rewards the opposite) | analog | welfare-over-engagement |
| harm | HarmBench, AgentHarm, StrongREJECT, AILuminate | partial | self-assessed harm awareness |
| autonomy | — | none | manipulation / paternalism |
| value | MASK (nearest) | analog | stated-principle vs behavior over a session |
| humility | SimpleQA abstention, ForecastBench Brier, GPQA abstention | partial | Phase-1→3 collapse (ACAT's most consistent finding) |
| scheme | MASK, Apollo-style scheming evals | partial | self-report gap |
| power | — | none | no market board |
| syc | sycophancy evals, MASK pressure prompts | partial | self-reported vs demonstrated |
| consist | LiveBench, IFEval variants, perturbation evals | analog | self-reported consistency |
| fair | BBQ, HELM fairness | partial | self-reported fairness |
| handoff | τ-bench policy adherence (faint) | analog | knowing when to defer |

Six with a usable comparator (truth, harm, scheme, syc, fair, consist); six without (service, autonomy, value, humility, power, handoff). On the six without, the only honest claim is "HumanAIOS-native; rests on our receipts alone."

## Two market facts that carry over
1. Frontier scores are mostly self-reported via model cards; independent verification lags weeks to months. That is ACAT's own REPORTED vs VERIFIED-LIVE line applied to the market — hence board step 14 (score half-life, scaffold card).
2. Agentic scores measure a system, not a model: the same model differs 30–50 points across scaffolds.

## Candidate block → z1-inbox/2026-09-08/ACAT_BENCHMARK_CANDIDATE_BLOCK.md
H-BM-01 no direct comparator · H-BM-02 six mapped / six not · H-BM-03 orthogonal to the capability stack · GAP-DIM-02 open. Falsifiers in the block.

## Options for Z2 (board rulings d10, d11, d13)
A position as orthogonal gap layer (d11) · B co-run the six mappable pairs, N=6–8 models, revert if ≥3 pairs r<0.3 (d10) · C evidence-tier tag on every public claim for the unmapped six (d13).

Full desk report with the 23-benchmark table: see the session artifact of 2026-09-08; the table is reference, not a rule, and is not reproduced here.
