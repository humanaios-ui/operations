# ENG TICKET — Metaculus bot: `test_questions` → `tournament` (live AIB)

**Repo:** `humanaios-ui/operations` → `tools/Metaculus/` · **Owner:** eng/ops (Z3) · **Filed by:** outreach (Z1)
**Blocks:** the bot's public track record — it has **0 forecast runs today**; this deploy is what starts it.
**Companion docs:** `metaculus-management-plan.md` · `-cost-optimization.md` · `-aib-entry-runbook.md` · `-monitoring-queries.md`

---

## Goal
Move the HumanAIOS bot (Metaculus profile `299627`) from safe `test_questions` mode to **live AIB tournament + MiniBench**, funded by **sponsor credits** (so it runs free) and running the **stronger forecast model** those credits unlock. Ship safely: verify IDs, smoke-test on the unscored area, then go live.

## Preconditions (must be true before this ticket starts)
- [ ] **AIB registered** for the current season; a valid **`METACULUS_TOKEN`** exists (Night — `futureeval/participate/`).
- [ ] **`OPENROUTER_API_KEY` with sponsor credits** obtained (Night — `forms.gle/aQdYMq9Pisrf1v7d8`).
- [ ] Supabase reachable (`SUPABASE_URL` + service-role `SUPABASE_KEY`) — confirmed live this session.

---

## Tasks

### 1. Secrets (Railway → Variables)
Set/confirm as Railway env vars (LiteLLM + forecasting-tools read the standard names):
- [ ] `OPENROUTER_API_KEY` — **new**, the sponsor key.
- [ ] `METACULUS_TOKEN` — the season's token.
- [ ] `GEMINI_API_KEY` — researcher (free tier) already relies on it.
- [ ] `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` — keep until the model swap (§3) removes the need.
- [ ] `SUPABASE_URL`, `SUPABASE_KEY` (service_role — bypasses RLS so writes land).

### 2. Mode flip — `railway.toml`
```diff
[deploy]
- startCommand = "python main.py --mode test_questions"
+ startCommand = "python main.py --mode tournament"
```
In `tournament` mode `main.py` forecasts on **`client.CURRENT_AI_COMPETITION_ID`** *and* **`client.CURRENT_MINIBENCH_ID`** (main.py ~L1189/L1194).

### 3. Model config — `main.py` `llms={}` block (~L1171) *(the cost + calibration win)*
Sponsor credits let us reverse the cost-driven Haiku downgrade for $0:
```diff
- "default": GeneralLlm(model="anthropic/claude-haiku-4-5", ...)   # downgraded "for cost"
+ "default": GeneralLlm(model="openrouter/anthropic/claude-sonnet-4-6", ...)  # sponsor-funded, stronger
  "researcher": GeneralLlm(model="gemini/gemini-2.0-flash", ...)   # keep (free)
- "parser":     "openai/gpt-4o-mini"                               # optional: move off paid
- "summarizer": "openai/gpt-4o-mini"
+ "parser":     "gemini/gemini-2.0-flash"     # or an openrouter :free model
+ "summarizer": "gemini/gemini-2.0-flash"
```
Pick the strongest `default` the sponsor credits cover. (Rationale + options: `-cost-optimization.md`.)

### 4. ⚠️ Competition-ID verification — the stale-season trap
`client.CURRENT_*_ID` are **constants baked into `forecasting-tools` (pinned `0.2.92` in `requirements.txt`)**. A pinned library can point at a **closed/previous season** → the bot would forecast the wrong or a dead tournament.
- [ ] Confirm `client.CURRENT_AI_COMPETITION_ID` + `client.CURRENT_MINIBENCH_ID` resolve to the **currently open** season (cross-check against `futureeval/participate/` / the AIB resources page).
- [ ] If stale: **bump `forecasting-tools`** to the version for this season, **or** override the IDs explicitly in `main.py`. Re-pin `requirements.txt` and re-import-smoke-test (per the v2.3 requirements note).

### 5. Smoke-test on the **unscored** area first
- [ ] Point one run at the **bot-testing-area** tournament (unscored) — *do not* go straight to the scored tournament.
- [ ] Confirm end-to-end: forecast submits → **comment posts** (validates the v2.3 comment-path repair) → **Supabase rows land** in `acat_forecast_runs` with `pipeline_phase` advancing → no `p4_error_log`.
- [ ] Ping outreach — **I'll run the monitoring queries** (`-monitoring-queries.md` Q1/Q2/Q5/Q6) to confirm rows, comment health, and that `li_is_placeholder` is still all-TRUE.

### 6. Go live
- [ ] Only after §5 is clean **and** calibration looks sane on the test set, let the live `tournament` schedule run (match cadence to the existing Railway cron; template reference is ~every 20 min).

---

## Acceptance criteria
- [ ] Rows appear in `public.acat_forecast_runs` from a live `bot_run_id`, `pipeline_phase` progressing P1→P2→P3(→P4 on resolution).
- [ ] `p3_comment_posted = TRUE` on new rows (repair holds); forecasts visible on Metaculus profile `299627`.
- [ ] `li_is_placeholder = TRUE` on every row (honesty guard intact — Gate 3 not in scope here).
- [ ] LLM spend draws on **sponsor credits** (OpenRouter), not a personal Anthropic key.
- [ ] No unexpected `p4_error_log` entries.

## Rollback
Revert `railway.toml` `startCommand` to `--mode test_questions` and redeploy (or disable the Railway service/cron). No data cleanup needed — rows are append/progress-only.

## Out of scope (do NOT do here)
- **Gate 3** (real P3 self-eval prompt → live Learning Index). Until it ships, `li_is_placeholder` stays TRUE and **no LI/ACAT result is surfaced** (`-management-plan.md` §3).
- Any **public attraction surfacing** of the track record — that's gated on N≥50 + good numbers + Night's Z2 (`-monitoring-queries.md` surfacing gate).
- Comment-template changes — flag to outreach if the template needs a Tradition-11 pass before comment volume scales.

---
*Zone: outreach filed this (Z1). Secrets + registration are Night (Z2). Code/deploy is eng (Z3). Nothing here surfaces anything publicly beyond the forecasts+comments the bot already posts by design — confirm that footprint is intended before go-live.*
