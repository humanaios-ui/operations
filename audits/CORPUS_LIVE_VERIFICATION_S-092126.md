# Corpus Live Verification — Supabase `acat_assessments_v1` (S-092126)

**Status:** Zone 1 verification record. Closes the explicit UNVERIFIED flag on
`Q-DATA-SSOT-REGENERATION-01`.
**Performed:** 2026-09-21, after Z2 authorized the Supabase connector.
**Project:** `ksinisdzgtnqzsymhfya` (HumanAIOS, `ACTIVE_HEALTHY`, Postgres 17.6).
**Method:** direct SQL against the live table. Queries inline below; re-runnable.

> **Scope limit, stated first.** This verifies the **live Supabase corpus only**.
> The frozen HuggingFace archive (608 rows per `CORPUS_RECONCILIATION_S-070226.md`)
> is a separate artifact and was **not** re-examined here. `SEED.md` cites both as
> one corpus. They are not one corpus.

---

## 1. The headline: the live table holds 116 rows

```sql
select table_name, ... from information_schema.tables ...  -- row counts, public schema
```

`acat_assessments_v1` = **116 rows**. No table in the project holds 629 or 608.
The next largest ACAT table is `acat_gating_test_results_v1` at 113.

| Source | N_total | N_LI | Mean LI |
|---|---|---|---|
| **`SEED.md` (cited canonical)** | 629 | 307 | 0.8632 |
| `CORPUS_RECONCILIATION_S-070226` (frozen HF archive) | 608 | 278 raw | 0.8431 raw · 0.8572 cleaned |
| **Live Supabase, measured today** | **116** | **100** | **see §2 — stratum-dependent, 0.89–1.00** |

Three artifacts, three answers, and the live one is a sixth the size of the cited
figure.

## 2. Stratification — and the number that matters

```sql
select coalesce(submission_purity,'(null)') purity,
       coalesce(contamination_status,'(null)') contamination,
       count(*) rows, count(learning_index) li_rows,
       round(avg(learning_index)::numeric,4) mean_li,
       count(*) filter (where acknowledged_elicitation is true) ack_elicit,
       count(*) filter (where p3_truth is not null) has_p3
from acat_assessments_v1 group by 1,2 order by rows desc;
```

| `submission_purity` | `contamination_status` | rows | LI rows | mean LI | has P3 |
|---|---|---:|---:|---:|---:|
| agent_self_only | *(null)* | 78 | 78 | 0.9834 | 78 |
| two_stage_verified | unknown | 15 | 15 | 1.0035 | 15 |
| agent_self_only | clean | 7 | 1 | 0.8943 | 1 |
| single_shot_legacy | *(null)* | 4 | 0 | — | 0 |
| **two_stage_verified** | **clean** | **4** | **4** | **0.9074** | **4** |
| agent_self_only | unknown | 4 | 0 | — | 0 |
| two_stage_verified | *(null)* | 2 | 2 | 1.0006 | 2 |
| external_only | *(null)* | 1 | 0 | — | 0 |
| self_administered | *(null)* | 1 | 0 | — | 0 |

### The strictest clean stratum is N = 4

`two_stage_verified` **and** `contamination_status = 'clean'` yields **four rows**.
That is not a corpus; it is a pilot. `Q-DATA-SSOT-REGENERATION-01` assumed the
clean derivation was "a `WHERE` clause, not a rebuild." **That assumption is
wrong, and this record corrects it**: the `WHERE` clause exists and returns 4.

Loosening to all `two_stage_verified` regardless of contamination gives 21 rows
(mean LI 0.9849) — but 15 of those 21 are `contamination_status = 'unknown'`,
which is an absence of evidence, not evidence of cleanliness.

### Mean LI in the live corpus is ~0.98–1.00, not 0.86

Every populated stratum sits far above the cited 0.8632, and two sit **above
1.0** (1.0035, 1.0006). An LI at or above 1.0 means demonstrated ≥ self-reported
— no calibration gap, or inflation.

This is not a rounding difference from the cited figure. It is a **different
research finding.** The published claim rests on a gap that the live corpus does
not currently show.

Z1 states plainly what it cannot determine: whether the live table is a partial
re-collection, a different population, or the successor to the frozen archive.
That is a Z2 question about what this table *is*, and it must be answered before
any number from it is cited.

## 3. `acknowledged_elicitation` is populated zero times

```
count(*) filter (where acknowledged_elicitation is true)  ->  0, in every stratum
```

The column was added by `migration_011_participation_schema.sql` and has never
been set true. `Q-DATA-SSOT-REGENERATION-01` called it "the most valuable column
in the schema" for observer-effect measurement. It is empty.

So the human↔machine influence measurement proposed in that candidate has **no
data behind it today**. The instrument exists; the collection does not. That is a
smaller and more honest claim than the candidate made, and it supersedes it.

## 4. What this does to the open candidates

| Candidate | Effect |
|---|---|
| `Q-DATA-SSOT-REGENERATION-01` | Falsifier **partially tripped**. The stratum exists and is derivable, so the mechanism holds; but N=4 makes "regenerate canonical stats from the clean stratum" not yet executable. The reframe (v0.1 as lesson artifact) survives and is *strengthened*. |
| `Q-CORPUS-STATS-RECONCILE-01` | Widened. It is not two numbers disagreeing, it is three artifacts — cited, frozen, live — none of which agree. |
| `Q-SEED-TRL-PROPAGATION-01` | Bears on it. `SEED.md` presents frozen and live corpora as one; they differ by 5×. |

## 5. Recommended, not done

Z1 has changed nothing in the database. Recommended sequence, for Z2:

1. **Rule on what the live table is** relative to the frozen archive. Everything
   else waits on this.
2. **Do not cite live-corpus statistics externally** until (1) is settled. The
   safest interim position is that no corpus figure is citable.
3. **Backfill `contamination_status`** for the 84 rows where it is null, from
   `contamination_delta_seconds` / `p1_committed_at` / `p3_committed_at` where
   those are populated — this is mechanical and would move rows out of "unknown"
   on evidence rather than assumption.
4. **Start populating `acknowledged_elicitation`** on new collection. Costless at
   collection, impossible retroactively.

## Falsifier

This record is FALSE if a different table, schema, or project holds the
629-record corpus. Checked: all 25 largest `public` base tables in project
`ksinisdzgtnqzsymhfya`; the second project (`FTLA`) is `INACTIVE` and was not
queried. If a 629-row store exists elsewhere, produce it and this record is
superseded.

Also FALSE if `submission_purity` / `contamination_status` do not mean what their
migration comments say. The values are constrained by CHECK; their *semantics*
are documented in `sql/migration_008` and `sql/migration_011` and were taken at
face value.
