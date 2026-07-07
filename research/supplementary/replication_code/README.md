# Replication Code

Code for verifying the ACAT corpus integrity, recomputing the canonical statistics,
and reproducing the Learning Index values reported in the methodology paper.

All scripts are in the **operations** repository: [humanaios-ui/operations](https://github.com/humanaios-ui/operations).

---

## Primary Tools

### corpus_integrity_validator

**File:** `tools/corpus_integrity_validator.py`
**Version:** 1.1.0

Validates an ACAT corpus CSV against schema requirements. Checks every row for:

- Missing required fields
- Out-of-range scores (Core-6 values must be 0–100)
- LI calculation correctness (recalculates LI from pre_total/post_total and checks
  against stored value within tolerance ±0.005)
- Mode field validity
- Phase pairing (Phase-3 rows should have a matching Phase-1 row via `pair_id`)
- Cross-row D-04 monotonicity (LI must not regress within an agent arc)

**Usage:**

```bash
# Clone the operations repo
git clone https://github.com/humanaios-ui/operations.git
cd operations

# Validate the v2 corpus
python tools/corpus_integrity_validator.py \
  --input research/datasets/acat_v5_3_2026Q2/acat_corpus_v2.csv

# Strict mode (treat warnings as failures)
python tools/corpus_integrity_validator.py \
  --input research/datasets/acat_v5_3_2026Q2/acat_corpus_v2.csv \
  --strict

# Smoke test (validates against built-in fixture)
python tools/corpus_integrity_validator.py --smoke-test
```

**Expected output (clean corpus):**

```
Corpus Integrity Validator v1.1.0
Input: research/datasets/acat_v5_3_2026Q2/acat_corpus_v2.csv
Rows loaded: 605 (604 data rows + header)
Validation: PASS
  Missing fields: 0
  Out-of-range scores: 0
  LI recalc mismatches: 0
  Invalid phase values: 0
  Unpaired Phase-3 rows: 0
```

---

### finalize_archive_v2

**File:** `tools/finalize_archive_v2.py`

Produces a cleaned, reproducible corpus CSV and canonical `canonical_stats.json`
from the raw form-response archive, applying the v2 (2b honest amendment) rules:

1. Recompute `learning_index = post_total / pre_total` for every Phase-3 pair
2. Keep ANCHORING-flagged rows (flagged, not deleted — per published v1 methodology)
3. Drop only genuinely corrupt rows: Phase-3 pairs with `pre_total` or `post_total`
   on an impossible scale (< 100 for a six-dimension 0–100 total). Exactly 3 such rows.
4. Keep missing-timestamp rows (provenance gap, not a validity failure)

**Usage:**

```bash
python tools/finalize_archive_v2.py \
  --input <raw_archive.csv> \
  --out-csv research/datasets/acat_v5_3_2026Q2/acat_corpus_v2.csv \
  --out-stats acat/canonical_stats_v2.json
```

**Canonical stats (v2, finalized 2026-07-02):**

```json
{
  "n_total": 604,
  "n_phase1": 524,
  "n_phase3": 80,
  "n_li_scored": 274,
  "n_li_pairs": 44,
  "mean_li": 0.8532,
  "n_providers": 23,
  "n_agents": 68,
  "excluded": {
    "corrupt_scale": 3,
    "out_of_range_score": 1
  },
  "raw_rows": 608
}
```

---

### acat_psychometric_validator

**File:** `tools/acat_psychometric_validator_v1_0.py`

Computes psychometric statistics on a corpus CSV:

- Cronbach's α (internal consistency across Core-6 dimensions)
- Principal Component Analysis (variance explained by PC1)
- Provider-level mean LI and standard deviation
- Dimension-level mean scores and correlations

**Usage:**

```bash
python tools/acat_psychometric_validator_v1_0.py \
  --input research/datasets/acat_v5_3_2026Q2/acat_corpus_v2.csv \
  --output outputs/psychometric_report.json
```

---

## Quick-Start: Reproduce Canonical Statistics

```bash
# 1. Clone operations repo
git clone https://github.com/humanaios-ui/operations.git
cd operations

# 2. Install dependencies (Python 3.11+)
pip install -r requirements.txt

# 3. Validate corpus integrity
python tools/corpus_integrity_validator.py \
  --input research/datasets/acat_v5_3_2026Q2/acat_corpus_v2.csv

# 4. Verify canonical stats match published values
python - <<'PY'
import json, pathlib
stats = json.loads(pathlib.Path("acat/canonical_stats_v2.json").read_text())
assert stats["n_total"] == 604, f"Expected 604, got {stats['n_total']}"
assert stats["mean_li"] == 0.8532, f"Expected 0.8532, got {stats['mean_li']}"
print("Canonical stats verified: N=604, mean_LI=0.8532")
PY
```

---

## Dataset Schema

Required columns in the corpus CSV for `corpus_integrity_validator`:

| Column | Type | Description |
|---|---|---|
| `agent_name` | string | AI system name |
| `layer` | string | Assessment mode |
| `truth` | float 0–100 | Truthfulness score |
| `service` | float 0–100 | Service score |
| `harm` | float 0–100 | Harm Awareness score |
| `autonomy` | float 0–100 | Autonomy Respect score |
| `value` | float 0–100 | Value Alignment score |
| `humility` | float 0–100 | Humility score |
| `total` | float | Sum of Core-6 scores |
| `phase` | string | `phase1` or `phase3` |
| `pre_total` | float | Phase-1 Core-6 total (Phase-3 rows) |
| `post_total` | float | Phase-3 Core-6 total (Phase-3 rows) |
| `learning_index` | float | LI = post\_total / pre\_total |
| `mode` | string | Protocol mode |
| `timestamp` | string | Submission timestamp |

---

## Environment

- Python 3.11+
- Dependencies: `pip install -r requirements.txt` (from the operations repo root)
- No API keys or network access required for corpus validation
- No Supabase connection required for static corpus validation

---

## External Sources

The v2 corpus is also available at:

- **Zenodo:** [https://doi.org/10.5281/zenodo.21135723](https://doi.org/10.5281/zenodo.21135723)
- **Hugging Face:** [https://huggingface.co/datasets/HumanAIOS/acat-assessments](https://huggingface.co/datasets/HumanAIOS/acat-assessments)

The local copy in `research/datasets/acat_v5_3_2026Q2/acat_corpus_v2.csv` is a
frozen snapshot of the same finalized dataset.

---

## Citation

If you use this corpus or replication code, cite:

> Anderson, C. R. (2026). *ACAT: AI Calibration Assessment Corpus (v2)* [Data set].
> Zenodo. [https://doi.org/10.5281/zenodo.21135723](https://doi.org/10.5281/zenodo.21135723)

See `CITATION.cff` in the repository root for a machine-readable citation.
