# Metaculus Bot — Monitoring Queries

**Practice:** empirica-outreach · **Drafted:** 2026-07-06 · **Zone:** Z1 (read-only SQL)
**Source of truth:** Supabase `public.acat_forecast_runs` (project `ksinisdzgtnqzsymhfya`)
**Companion to:** `metaculus-management-plan.md` §5

> **Baseline as of 2026-07-06 (grounded, authed read): `acat_forecast_runs` = 0 rows.**
> The bot has recorded **no forecast runs** — there is no track record yet. `pipeline_health` is stale seed data (`last_seen` 2026-04-03). This is expected: the bot is in `test_questions` mode and hasn't done scored production runs. **Entering AIB + flipping to `tournament` mode is what starts the record.** Run these queries once rows land.

The `acat_forecast_runs` schema mirrors the pipeline: `p1_*` (naive ACAT dims + `p1_li_estimate`), `p2_*` (forecast), `p3_*` (re-declaration + `learning_index` + comment fields), `p4_*` (resolution + **`p4_brier_score` / `p4_brier_skill_score` / `p4_peer_score`**), plus `pipeline_phase` and the `li_is_placeholder` guard.

---

## The weekly review (run in order)

**1 — Liveness: is the bot actually running?**
```sql
SELECT max(created_at) AS last_run, count(*) AS total_rows,
       count(*) FILTER (WHERE created_at > now() - interval '7 days') AS rows_last_7d
FROM public.acat_forecast_runs;
```

**2 — Coverage by phase (how far each question got in the pipeline)**
```sql
SELECT pipeline_phase, count(*) AS n
FROM public.acat_forecast_runs
GROUP BY pipeline_phase ORDER BY n DESC;
```

**3 — Calibration headline (asset a) — resolved questions only**
```sql
SELECT count(*)                     AS resolved_n,
       round(avg(p4_brier_score),4) AS avg_brier,
       round(avg(p4_brier_skill_score),4) AS avg_brier_skill,
       round(avg(p4_peer_score),4)  AS avg_peer
FROM public.acat_forecast_runs
WHERE p4_resolved_at IS NOT NULL;
```

**4 — N=50 gate (are we clear of the small-N hold?)**
```sql
SELECT count(*) FILTER (WHERE p4_resolved_at IS NOT NULL) AS resolved_n,
       (count(*) FILTER (WHERE p4_resolved_at IS NOT NULL) >= 50) AS n50_met
FROM public.acat_forecast_runs;
```

**5 — Comment-post health (the v2.3 repair — should trend TRUE honestly)**
```sql
SELECT count(*) AS p3_rows,
       count(*) FILTER (WHERE p3_comment_posted) AS posted_ok,
       round(100.0*count(*) FILTER (WHERE p3_comment_posted)/nullif(count(*),0),1) AS pct_ok
FROM public.acat_forecast_runs
WHERE p3_timestamp IS NOT NULL;
```

**6 — Honesty guard (MUST be all-TRUE until Gate 3 ships)**
```sql
SELECT count(*) AS total,
       count(*) FILTER (WHERE li_is_placeholder) AS placeholder_rows,
       bool_and(li_is_placeholder) AS all_placeholder
FROM public.acat_forecast_runs;
```
*If `all_placeholder` is ever FALSE, Gate 3 has shipped — only then may any LI/drift result be surfaced (`metaculus-management-plan.md` §3).*

**7 — Errors (phase-4 sweep failures)**
```sql
SELECT question_url, p4_error_log, updated_at
FROM public.acat_forecast_runs
WHERE p4_error_log IS NOT NULL
ORDER BY updated_at DESC LIMIT 20;
```

---

## Surfacing gate (before any track record goes public)
Publishable only when **all** hold — else it stays private:
- Query 3 `resolved_n` ≥ 50 (query 4 `n50_met` = true), **and**
- `avg_brier` / `avg_peer` are actually good (a bad public number is anti-attraction), **and**
- for any ACAT/LI claim: query 6 `all_placeholder` = FALSE (Gate 3 shipped).

*I can run these each week once the bot is live; when Supabase MCP is connected I execute them directly and report deltas.*
