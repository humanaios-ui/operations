# Metaculus Bot — Cost Optimization

**Practice:** empirica-outreach · **Drafted:** 2026-07-06 · **Zone:** Z1 (research; eng implements config)
**Companion to:** `metaculus-management-plan.md` (§8 cost-drift risk)
**Boundary:** outreach *recommends*; the eng seat (`humanaios-ui/operations`) owns the config + deploy.

---

## 0. Headline — you're already half-optimized; the biggest lever is free credits

The bot is **not** a single-model Claude bot. It already runs `forecasting-tools`' `GeneralLlm`, which is **LiteLLM under the hood** — every model is a swappable string, and the token-heavy work is already offloaded to free/cheap tiers:

| Role | Current model | Cost today |
|---|---|---|
| `researcher` *(the volume driver)* | `gemini/gemini-2.0-flash` | **free tier** ✅ |
| `default` *(forecast reasoning)* | `anthropic/claude-haiku-4-5` | cheap (already downgraded from Sonnet "for cost") |
| `parser` | `openai/gpt-4o-mini` | cheap, **paid** |
| `summarizer` | `openai/gpt-4o-mini` | cheap, **paid** |

So "run it for free" is a **config question, not a rewrite** — and the single highest-value move isn't going cheaper, it's getting the good models *sponsored*:

> **Metaculus's AI Benchmarking (AIB) tournament gives participating bots free API credits** — donated by **Anthropic, Google, and OpenAI**, plus a **free OpenRouter key** and free **AskNews** search. ([AIB](https://www.metaculus.com/aib/), [Spring 2026](https://www.metaculus.com/aib/2026/spring/), [Summer 2026 FutureEval](https://forum.effectivealtruism.org/posts/ZfLAN557rGWACKtmc/announcing-metaculus-summer-2026-futureeval-bot-tournament))

The bot's `tournament` mode already targets `CURRENT_AI_COMPETITION_ID` + `CURRENT_MINIBENCH_ID`. **It is built for exactly this.**

---

## 1. The levers, ranked

### Lever 1 — Metaculus AIB sponsored credits *(biggest; do this first)*
Enter the AIB tournament and claim the sponsor credits: participants fill a form for a **free OpenRouter key with credits**, and can **email their bot description to have donated Anthropic/Google/OpenAI credits assigned to their chosen models** (routed via Metaculus's LLM proxy). Free AskNews search is included for the research step. ([Spring 2026 announcement](https://forum.effectivealtruism.org/posts/5EX9dz7nKthcxECTe/announcing-spring-2026-ai-forecasting-benchmark), [metac-bot-template](https://github.com/Metaculus/metac-bot-template))

**Why this is the elegant answer:** it doesn't just make the current setup free — it lets you *reverse the cost-driven Haiku downgrade* and run a **stronger forecast model for $0**. Free **and** better-calibrated. Since calibration *is* the attraction asset (see the management plan), this is the rare move that improves the asset while cutting cost to zero.

- **Bonus:** the credits arrive as an `OPENROUTER_API_KEY`, and LiteLLM speaks `openrouter/...` natively — so claiming them is, again, a one-line model-string change per role.

### Lever 2 — Local models via Ollama *(the user's resource — applied to the right layer)*
Ollama now speaks the Anthropic API format, and LiteLLM has always supported `ollama/<model>` — so `GeneralLlm(model="ollama/qwen2.5-...")` is a one-line swap. **Free, and data never leaves the machine.**

**But aim it correctly.** A small local model forecasts *worse*, and the forecast number is the whole point. So use local for the layers where reasoning quality barely matters:
- ✅ **Dev / `test_questions` iteration** — run the whole pipeline locally, free, while tuning prompts. This is the ideal home for local models.
- ✅ **`parser` / `summarizer`** — structured extraction + formatting; a local model is fine and this kills the last paid (gpt-4o-mini) surface.
- ❌ **`default` (scored forecast reasoning)** — do **not** put this on a weak local model. That trades the asset for pennies.

*(Local also needs a machine that's always-on for the cron; Railway is cloud, so local suits dev, not the 24/7 deploy — unless you self-host the runner.)*

### Lever 3 — Extend the free tiers already in use
`researcher` already rides Gemini free tier successfully. Move `parser` + `summarizer` off paid `gpt-4o-mini` to a free option — **Gemini Flash free** (already trusted here), **Groq free tier** (fast, hosts Llama), or an **OpenRouter `:free`** model. Eliminates the remaining OpenAI spend at near-zero quality risk (these are formatting roles).

### Lever 4 — Cut cost on whatever stays paid (Anthropic path)
If any Claude calls remain out-of-pocket (no sponsor credits):
- **Prompt caching** — the ACAT/calibration system-prompt scaffold repeats every question; caching it cuts input cost dramatically on repeats.
- **Batch API (~50% off)** — forecasting isn't latency-sensitive; the **daily `phase4_resolution_sweep` cron** is a perfect batch candidate.

---

## 2. The principle — free the volume, fund the forecast

> **Downgrade the plumbing, not the forecast.** Research/parsing/formatting/dev = free tiers + local. The scored forecast model = kept strong, paid for by sponsor credits. Never save money on the exact number that is the attraction asset.

The bot already half-followed this (research → free) and half-violated it (forecast → Haiku *for cost*). Lever 1 fixes the violation for free.

---

## 3. Recommended target config

```python
llms = {
    # scored forecast — kept strong, funded by AIB sponsor credits (via OpenRouter proxy)
    "default":    GeneralLlm(model="openrouter/anthropic/claude-sonnet-4-6", temperature=0.3, ...),
    # research volume — already free
    "researcher": GeneralLlm(model="gemini/gemini-2.0-flash", temperature=0.3, ...),
    # formatting roles — move off paid gpt-4o-mini to free
    "parser":     "gemini/gemini-2.0-flash",      # or ollama/… , or an openrouter :free model
    "summarizer": "gemini/gemini-2.0-flash",
}
# dev/test_questions: point ALL roles at ollama/… for free local iteration
```
Net effect: **$0 in steady state** (sponsor credits + free tiers), with the forecast model *upgraded* from Haiku, plus a free fully-local dev loop.

---

## 4. Next actions & open decisions

**Next actions**
| # | Action | Owner | Zone |
|---|---|---|---|
| 1 | Enter AIB (seasonal + MiniBench); fill the OpenRouter-credit form; email bot description to get Anthropic/Google credits assigned | Night | Z2 |
| 2 | Once credits land: switch `default` to the sponsored strong model via `openrouter/…` | eng | Z3 |
| 3 | Move `parser` + `summarizer` off `gpt-4o-mini` to a free tier | eng | Z3 |
| 4 | Stand up an Ollama-based local profile for `test_questions` dev runs | eng | — |
| 5 | Add prompt caching + Batch API for any residual paid Claude calls (esp. phase-4 sweep) | eng | — |

**Open decisions (Night)**
1. **AIB entry** — enter now? It's the free-credits gateway *and* the tournament that makes the track record an attraction asset (management plan §4). One move, both wins.
2. **Forecast model target** — with credits, which model for `default`? (Recommend the strongest the credits cover — calibration is the asset.)
3. **Local dev** — want a documented Ollama dev profile so prompt iteration is free and private?

---

*The through-line with the management plan: entering AIB is the same single action that (a) makes the bot free to run and (b) turns its track record into public, sponsor-legitimized calibration evidence. Cost and attraction point the same way.*

**Sources:** [Metaculus AIB](https://www.metaculus.com/aib/) · [AIB Spring 2026](https://www.metaculus.com/aib/2026/spring/) · [Spring 2026 announcement (EA Forum)](https://forum.effectivealtruism.org/posts/5EX9dz7nKthcxECTe/announcing-spring-2026-ai-forecasting-benchmark) · [Summer 2026 FutureEval](https://forum.effectivealtruism.org/posts/ZfLAN557rGWACKtmc/announcing-metaculus-summer-2026-futureeval-bot-tournament) · [Metaculus bot template](https://github.com/Metaculus/metac-bot-template)
