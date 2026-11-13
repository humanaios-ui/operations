# ACAT ↔ benchmark map — registry candidate block (Z1 proposes; Z2 ratifies by hash)
Source: docs/ACAT_BENCHMARK_MAP_20260908.md · tier LAID · read 2026-09-08 against main 5df54b7

H-BM-01  ACAT has no direct market-benchmark comparator; nearest kin are honesty/calibration evals (MASK, SimpleQA-calibration, ForecastBench), partial only.
  falsifier: a vendor-cited 2026 benchmark scores the distance between a model's self-assessment and its measured behavior across ≥3 behavioral dimensions.
  status: PROPOSED · prediction C12 (falsifier fires by 2027-03-08): 0.15

H-BM-02  Six of twelve ACAT dimensions have a usable external comparator (truth, harm, scheme, syc, fair, consist); six do not (service, autonomy, value, humility, power, handoff).
  falsifier: a market-standard, vendor-used benchmark is identified for any one of the six unmapped dimensions.
  status: PROPOSED

H-BM-03  ACAT is complementary to, not competitive with, the capability stack; it cannot be folded into a capability index.
  falsifier: a vendor/investor composite index incorporates a claim-vs-behavior gap metric as a scored component, OR ACAT correlates > 0.7 with a capability leaderboard across ≥10 models.
  status: PROPOSED

GAP-SPEC-01  CLOSED at landing for the dimension list (12 keys in acat/contracts/, 5 files, main 5df54b7). Remains OPEN for receipt/provenance tier taxonomies until their file paths are cited.
GAP-DIM-02  Public site says 12 / 11 / 6 dimensions in different places. OPEN. falsifier: repo or preprint states one canonical count.

Predictions locked on the board: C9 (co-run completes ≥5/6 pairs in 4 weeks) 0.60 · C10 (≥1 pair r ≥ 0.5) 0.55 · C12 0.15 · C13 (remap loop declines on first read) 0.85.

## Options

- `ratify`
- `edit`
- `later`

## What each sets in motion

- `ratify`: H-BM-01, H-BM-02 and H-BM-03 are accepted as PROPOSED hypotheses, each with the falsifier stated above. Entering them in REGISTERED.md is a Z2 act; Z1 does not write that file.
- `edit`: Z1 revises the block and files it again.
- `later`: this block closes with its bytes signed; the question returns only as a new block.

## Ruling

choice: ratify
by: Z1-prepared (not an identity claim)
at: 2026-11-13T14:16:56Z
status: DECIDED
block_hash: 9604ca19bdf4d76c8c60320c547f3e5d219ba34e8842915d42c7eaa3a91ec8d7
body_hash: e7feb9f57a3975322249fd165897ed66a1f440fb057fb9b70df0351ac7cf2f71

```
RULING z1-acat-bm-01
  by: Z1-prepared (not an identity claim) (tagline)
  project: humanaios
  question: Accept H-BM-01..03 (ACAT vs market benchmarks) as PROPOSED hypotheses?
  choice: ratify
  note: 
  at: 2026-11-13T14:16:56Z
  status: DECIDED
```

