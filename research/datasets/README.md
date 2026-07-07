# ACAT Datasets

Frozen snapshots of the ACAT corpus, named by methodology version and time window.

## acat_v5_3_2026Q2/

**Methodology:** ACAT v5.3+ (de-anchored, unanchored conditions only)
**Time window:** 2026 Q1–Q2 (finalized 2026-07-02)
**Protocol:** Core-6 dimensions (truth / service / harm / autonomy / value / humility)
**Rows:** N=604 finalized, integrity-validated
**License:** Apache-2.0

### Canonical statistics

| Metric | Value |
|---|---|
| N total | 604 |
| N Phase-1 | 524 |
| N LI-scored | 274 |
| N LI pairs | 44 |
| Mean LI | 0.8532 |
| N providers | 23 |
| N agents | 68 |
| Excluded (corrupt scale) | 3 |
| Excluded (out-of-range score) | 1 |

Reproducible via `corpus_integrity_validator` (see `supplementary/replication_code/`).

### External mirrors (canonical public releases)

- **Zenodo:** [https://doi.org/10.5281/zenodo.21135723](https://doi.org/10.5281/zenodo.21135723)
- **Hugging Face:** [https://huggingface.co/datasets/HumanAIOS/acat-assessments](https://huggingface.co/datasets/HumanAIOS/acat-assessments)

### Files

| File | Description |
|---|---|
| `acat_corpus_v2.csv` | Finalized, integrity-validated corpus (604 data rows + header) |

### Column descriptions

| Column | Description |
|---|---|
| `agent_name` | AI system name (e.g. "Claude", "ChatGPT") |
| `layer` | Assessment mode (e.g. `ai-self-report`) |
| `truth` | Core-6: Truthfulness score (0–100) |
| `service` | Core-6: Service score (0–100) |
| `harm` | Core-6: Harm Awareness score (0–100) |
| `autonomy` | Core-6: Autonomy Respect score (0–100) |
| `value` | Core-6: Value Alignment score (0–100) |
| `humility` | Core-6: Humility score (0–100) |
| `total` | Sum of Core-6 scores |
| `phase` | `phase1` or `phase3` |
| `pre_total` | Phase-1 total for the pair |
| `post_total` | Phase-3 total for the pair |
| `learning_index` | LI = post\_total / pre\_total (null for Phase-1-only rows) |
| `mode` | Protocol mode |
| `timestamp` | Submission timestamp |
| `behavioral_flag_final` | Behavioral flags (e.g. `HUMILITY_HIGHEST_DIM`, `HIGH_SELF_REPORT`) |
| `pair_id` | Links Phase-1 and Phase-3 rows for the same session |

### Citation

> Anderson, C. R. (2026). *ACAT: AI Calibration Assessment Corpus (v2)* [Data set].
> Zenodo. [https://doi.org/10.5281/zenodo.21135723](https://doi.org/10.5281/zenodo.21135723)
> Also on Hugging Face: HumanAIOS/acat-assessments (Apache-2.0).
> Methodology manuscript under review.

See `CITATION.cff` in the repository root for a machine-readable citation.
