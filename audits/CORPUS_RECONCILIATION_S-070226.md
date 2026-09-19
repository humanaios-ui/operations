# Corpus Reconciliation — Archive vs. Cited Canonical (S-070226)

**Status:** Zone 1 — **submission-blocking finding.** Resolve before any funder submission.
**Source analyzed:** `_inbox_files3/ACAT Assessment (Responses) - Form Responses 1_Archive.csv` (= the file published live at [HuggingFace/HumanAIOS/acat-assessments](https://huggingface.co/datasets/HumanAIOS/acat-assessments), 608 rows).
**Tools used (both verified functional, not stubs):** `operations/tools/corpus_integrity_validator.py` (v1.1) + a direct `csv` parse.

---

## The finding: the cited canonical numbers are NOT reproducible from the published dataset

| Metric | **Cited everywhere** (CV, both apps, REGISTERED/CURRENT) | **Actual archive** (parsed + validated) |
|---|---|---|
| Total records | 629 | **608** |
| Phase 1 | 516 | **524** |
| LI-scored | 307 | **278** raw numeric · ~**80–84** proper Phase-3 pairs |
| Mean LI | 0.8632 | **0.8431** raw · **0.8572** cleaned |
| Providers | 18 | **23** provider families (68 distinct agents) |
| Integrity | (implied clean) | **FAIL** — 31 `LI_RECALC_MISMATCH`, 86 warnings, 12 `ANCHORING`, 87 `MISSING_TIMESTAMP` |

**Not one of the five headline numbers matches**, and the dataset fails its own integrity validator. A Longview reviewer who downloads the 608-row HuggingFace dataset and computes the mean LI gets **0.8431**, not the cited 0.8632 — and finds **608** rows, not 629, and **no** way to reach N_LI=307.

### Why this matters more for HumanAIOS than for anyone else
Your entire thesis is **measuring the gap between what a system claims about itself and what it actually does.** If a reviewer finds exactly that gap in your own headline statistics, it doesn't just cost one number — it undercuts the credibility of the instrument. This is the one issue I would not let go out the door.

### Concrete integrity failures (examples from the validator)
- `row_183_Anonymous`: declared LI 0.6796 but pre_total=45 → recomputes to **7.7778** (garbage pre_total; a 6-dimension P1 total of 45 is impossible if dimensions are ~0–100).
- `row_235_Claude-Sonnet-4-6`: declared 0.8311 → recomputes 1.0388.
- 29 more `LI_RECALC_MISMATCH` rows where stored `learning_index` ≠ `post_total / pre_total`.
- 12 rows flagged `ANCHORING`; 87 `MISSING_TIMESTAMP`.

---

## Finalization options (pick one — I'll then correct every document + the dataset)

**Option A — Make the numbers true to the archive (recommended; on-brand + fastest honest path).**
1. Clean the 608 set: recompute `learning_index = post_total/pre_total` for all Phase-3 pairs (fixes the 31 mismatches); drop the garbage-pre row and the 12 anchoring rows; decide keep/drop for missing-timestamp.
2. Recompute canonical stats from the cleaned set (preliminary: **~596 records, ~80 clean Phase-3 LI pairs, mean LI ≈ 0.857**).
3. Re-publish the cleaned CSV to HuggingFace; upload the dataset card.
4. Correct **every** cited number (CV, fellowship app, grant app, dataset card, CURRENT.md, REGISTERED.md) to the reproducible figures.
→ Result: a dataset that passes its own validator and numbers any reviewer can reproduce.

**Option B — If a real 629-record corpus exists elsewhere** (e.g., a Supabase live export or an HF archive with `canonical_stats.json`): produce it, confirm it reproduces 516/307/0.8632, and **publish THAT** as the HF dataset (replacing the 608). The public artifact must match the claims either way.

**Minimum for an honest submission TODAY:** cite numbers that match the publicly-downloadable dataset. That means correcting 629→608, 516→524, dropping/curing the unsupported N_LI=307, and using the archive-true mean LI. Everything else (full clean + re-publish) can follow.

---

## Decisions needed from you
1. **Which corpus is canonical** — the 608 archive (Option A), or is there a real 629 elsewhere (Option B)?
2. **Cleaning rules** — recompute LI + drop anchoring/garbage/missing-timestamp? (my recommended default)
3. **12 vs Core-6** — this archive scores only Core-6 (truth/service/harm/autonomy/value/humility) in its columns. Confirm where the Extended-6 live, or soften "12 dimensions" to "6 core dimensions (12-dimension rubric)" so the claim matches the downloadable data.
