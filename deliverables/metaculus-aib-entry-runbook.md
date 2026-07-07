# Metaculus AIB — Entry Runbook

**Practice:** empirica-outreach · **Drafted:** 2026-07-06 · **Zone:** Z1 (runbook; Night executes account/form/deploy steps)
**Companion to:** `metaculus-management-plan.md`, `metaculus-cost-optimization.md`
**Why:** one entry does both jobs — makes the bot free to run *and* turns its track record into sponsor-backed public calibration evidence.

> **Who does what.** I can't enter for you — it's your Metaculus account, a Google Form, and a Railway deploy. This is the turnkey list; every outward step is yours (Z2/Z3). HumanAIOS already has a bot (profile 299627) + code in `humanaios-ui/operations`, so you're **not** forking the template — you're pointing the existing bot at the live tournament with sponsor credits.

---

## Step 1 — Register for the tournament *(Night, ~5 min)*
- Go to **https://www.metaculus.com/futureeval/participate/** and opt into the current season (seasonal + MiniBench).
- Confirm/create your **`METACULUS_TOKEN`** there (you likely already have one since the bot forecasts). Resources page: **https://www.metaculus.com/notebooks/38928/ai-benchmark-resources/**

## Step 2 — Claim the free sponsor credits *(Night, ~2 min)* ← the cost win
- Get a **free-credit `OPENROUTER_API_KEY`** via Metaculus's form: **https://forms.gle/aQdYMq9Pisrf1v7d8**
  (credits donated by Anthropic / Google / OpenAI, routed through OpenRouter).
- This is what makes the bot free to run — and lets us put the **forecast model back up to a strong one** (reverse the cost-driven Haiku downgrade) at $0. See `metaculus-cost-optimization.md`.
- Optional search sponsorship: **AskNews** free tier is available to participants (the bot's `researcher` role can use it alongside Gemini-free).

## Step 3 — Point the bot at the tournament *(eng / Z3)*
- The bot already supports `--mode tournament` (targets `CURRENT_AI_COMPETITION_ID` + `CURRENT_MINIBENCH_ID`). Railway `startCommand` is currently `--mode test_questions` — **eng flips it to `tournament`** and redeploys.
- Wire the sponsor key: set `OPENROUTER_API_KEY` as a Railway secret; switch `default` to `openrouter/anthropic/claude-sonnet-4-6` (or the strongest the credits cover) per the cost doc's target config.
- **Verify the competition IDs resolve to the live season** before the first scored run (a stale ID = forecasting the wrong/closed tournament).

## Step 4 — Smoke-test, then go live *(eng)*
- First run against the **bot-testing-area** tournament (unscored) to confirm: forecasts submit, comments post (the v2.3 repair holds), Supabase writes succeed.
- Then let the live `tournament` run proceed (the template cadence is every ~20 min; match to our Railway cron).

## Step 5 — Baseline + monitor *(me, once Supabase is authed)*
- With Supabase authenticated (initiated this session — see chat), I'll pull the baseline (N, Brier, peer score, comment success) and draft the standing monitoring queries (`metaculus-management-plan.md` §5).

---

## Guardrails (unchanged)
- **Don't surface any LI/ACAT result** — `li_is_placeholder = TRUE` until Gate 3. The track record (Brier/peer) is fine to reference once it's good; the ACAT-on-forecasting story waits.
- **Scored ≠ test.** Only go live on the scored tournament once calibration looks sound on test — a bad public Brier is anti-attraction.
- **Every public comment is HumanAIOS in public** — confirm the comment template is clean before comment volume scales.

## Optional — credits-assignment email (only if you want more than the OpenRouter free tier)
Beyond the form, Metaculus can assign donated Anthropic/Google/OpenAI credits to specific models via their LLM proxy. If the OpenRouter free credits aren't enough for the season's question volume, a 3-line note to the Metaculus AIB team (via the [Discord](https://discord.com/invite/NJgCC2nDfh) 'build a forecasting bot' channel or the resources-page contact) stating the bot name (HumanAIOS, profile 299627), the models you want funded, and expected volume is the path. Say the word and I'll draft it.

**Sources:** [FutureEval participate](https://www.metaculus.com/futureeval/participate/) · [AI Benchmark resources](https://www.metaculus.com/notebooks/38928/ai-benchmark-resources/) · [OpenRouter free-credit form](https://forms.gle/aQdYMq9Pisrf1v7d8) · [metac-bot-template](https://github.com/Metaculus/metac-bot-template)
