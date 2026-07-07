# Metaculus Bot — Management Plan

**Practice:** empirica-outreach · **For:** Carly R. Anderson / HumanAIOS
**Branch:** `outreach/phase0-audit` · **Drafted:** 2026-07-06 · **Zone:** Z1 (plan; Night ratifies outward moves)
**Subject:** the HumanAIOS forecasting bot — Metaculus profile `299627`; code `humanaios-ui/operations/tools/Metaculus` (Railway).

---

## 0. Why this belongs in outreach

Metaculus scores forecasters against reality and against each other. A bot with a public track record is therefore **third-party-verified calibration evidence** — and calibration *is* the HumanAIOS thesis (ACAT measures "the gap between what an AI says it is and what it does" — calibration under evidence pressure). A neutral platform scoring our forecasts in public is the single most credible attraction signal we can show the AI-safety / measurement audience, because we didn't grade it.

So the bot is an **attraction asset**, and outreach is the right seat to *manage that asset's strategy* — what it shows the world, when, and how honestly. It is **not** the seat that owns the code.

**Practice boundary (same discipline as collaborator-ops):**
| Seat | Owns |
|---|---|
| **outreach** *(this plan)* | The attraction strategy, monitoring cadence, and surfacing decisions — how/whether the track record becomes public-facing evidence |
| **ops / eng** (`humanaios-ui/operations`) | The bot code, deploy (Railway), the ACAT pipeline, and **Gate 3** (§3) |

Outreach never edits `main.py` or deploys. It consumes the bot's output (Supabase) and decides what to do with it, under Zone gating.

---

## 1. What the bot actually is (accurate snapshot)

From the v2.3 source — state it plainly so nothing downstream overclaims:

- **Model:** `claude-sonnet-4-6`, via Metaculus's `forecasting-tools` library (the standard AI-benchmark bot framework).
- **Per-question pipeline:** build prompt → LLM reasoning trace → parse `ACAT_PRE / LI_ESTIMATE / CALIBRATION_MODE` → **P1** Supabase write → submit forecast to Metaculus → **P2** write → post a **public comment** + **P3** write. A daily cron (`phase4_resolution_sweep.py`) scores questions as they resolve (**Phase 4**).
- **Data home:** Supabase (service-role writes). **This is the canonical track-record source**, richer than the Metaculus profile page.
- **Deployment:** Railway, currently `--mode test_questions` (modes available: `tournament`, `metaculus_cup`, `test_questions`).
- **Public footprint:** it posts **public** comments on Metaculus (`is_private=False`). Every comment is HumanAIOS speaking in public — a reputation surface (§6).

---

## 2. The two attraction assets (keep them separate)

| Asset | What it is | Honesty status |
|---|---|---|
| **(a) Metaculus track record** | Standard Brier / peer accuracy / N-resolved / tournament standing | **Always honest** — it's third-party-scored. Publishable as soon as the numbers are good (§5). |
| **(b) ACAT-on-forecasting** | The live demonstration that we run our *own* calibration instrument (P1→P3 Learning Index) on real public questions | **Gated on Gate 3** (§3). Not real yet — do not surface. |

The temptation is to lead with (b) because it's the unique, on-brand story. **Resist until Gate 3.** Leading with a placeholder metric is the exact overclaim failure the convergence-inflation lesson already cost us once.

---

## 3. The critical gate — LI is a placeholder

**`learning_index = 1.0` is a structural placeholder on every row** (`li_is_placeholder = TRUE`). P3 currently just mirrors P1. The bot's own docstring is explicit:

> *"Real post-forecast behavioral drift measurement requires a separate P3 self-evaluation prompt (Gate 3 work). Do not interpret LI values from v2.x runs as drift signal."*

**Implication for outreach:** the ACAT-on-forecasting narrative (asset b) has **no real signal behind it yet.** Until "Gate 3" (the real P3 self-evaluation prompt) ships from the eng side:
- Do **not** publish, post, or imply any LI / drift / self-assessment-gap result from the bot.
- The `li_is_placeholder` column is the honesty guard — any surfacing query must filter it.
- Also holding: a **`N=50` resolved-question threshold** (a Zone-3 hold in the bot's own governance) before certain promotions. Small-N calibration is noise; respect it.

Gate 3 + N=50 are the two unlocks that turn asset (b) from scaffold into evidence. They are **eng deliverables**; outreach's job is to *not get ahead of them*.

---

## 4. Tournament strategy — what to forecast

`forecasting-tools` is built for Metaculus's **AI Benchmarking** tournaments (bot-only, public, scored) — the natural home: designed for bots, neutral, and a strong-standing result there is a citable credibility artifact.

**Sequence (recommend):**
1. **Now → stay in `test_questions`.** Prove pipeline health (Supabase writes, comment posting, resolution sweep) without a public-tournament reputation stake. The v2.3 patch was literally a comment-path repair — confirm it holds over a run.
2. **Gate: pipeline clean + Gate 3 shipped + N≥50 → promote to a live tournament** (AI Benchmarking or Metaculus Cup). Night ratifies the mode switch (Z2) and the eng seat deploys (Z3).
3. **Steady state:** participate in each AI Benchmarking round; let the peer/Brier track record accumulate. *Then* asset (a) is publishable and asset (b) (post-Gate-3) becomes the on-brand story.

Don't promote to a scored public tournament while calibration is unproven — a bad public Brier is anti-attraction and hard to walk back (§6).

---

## 5. Monitoring plan

**Source of truth = Supabase**, not screen-scraping Metaculus (which 403s non-browser clients anyway). The bot writes P1/P2/P3 + phase-4 resolutions there.

**Step 1 (do first): establish the baseline.** Pull current numbers — N forecast, N resolved, Brier, peer/calibration score, comment-post success rate. Via the Supabase MCP (once authed) or a Night-run Metaculus export. *These numbers are currently unknown to this plan — that's the first thing to close, not to assume.*

**Metrics to watch (weekly, interlocked with the Substack cadence):**
| Metric | Source | Why |
|---|---|---|
| Brier score / peer accuracy | Supabase (phase-4) / Metaculus | The headline calibration number — asset (a) |
| N forecast vs N resolved | Supabase | Coverage + whether N≥50 gate is met |
| Comment-post success rate | Supabase `p3_comment_posted` | v2.3 repaired this — confirm it stays TRUE honestly |
| Pipeline health | Railway logs + Supabase write success | Is the bot actually running each cycle? |
| `li_is_placeholder` still TRUE | Supabase | The honesty guard — flips FALSE only when Gate 3 ships |
| API spend | Anthropic usage | Cost control (per-question LLM calls) |

**Cadence:** a weekly 10-minute review. When Supabase MCP is authenticated, I can draft the standing monitoring queries (Z1) so the review is one command.

---

## 6. Operational governance (Zones for an autonomous, public-posting bot)

This bot **acts in public autonomously** — it submits forecasts and posts comments without a human in each loop. That makes Zone discipline load-bearing.

| Action | Zone | Owner |
|---|---|---|
| Analyze track record; draft monitoring queries; draft this plan | Z1 | outreach (me) |
| Change forecast mode (test → tournament); turn public comments on/off; change the comment template; approve Gate-3 for live | **Z2** | Night ratifies |
| Deploy to Railway; run against a live scored tournament | **Z3** | eng executes |
| **Publish** any track-record number or ACAT result as attraction | **Z2/Z3** | Night — via the 5-gate publish-consent policy (self-published, but TRL-framed + no-overclaim gates still apply) |

The bot already embeds this thinking (its own "B/C held in Zone 3 until N=50"). The plan just aligns outreach to it. **Nothing the bot shows the public becomes *attraction* without Night's Z2.**

---

## 7. Attraction-surfacing roadmap (Tradition 11, sequenced)

How the asset becomes public-facing — *manifest, don't promote*, and only when honest:

1. **Now:** nothing public-facing from outreach. Baseline the numbers privately (§5).
2. **After a clean public track record accumulates (asset a):** a quiet, factual reference — e.g. a line on the hub / a Witness-Stand aside: *"we forecast in public and get scored — here's the record."* No hype; the number speaks.
3. **After Gate 3 + N≥50 (asset b unlocks):** the on-brand piece — *"we pointed our calibration instrument at our own public forecasts."* This is a strong Witness-Stand post **because** by then it's real. Runs through the 5-gate publish policy, TRL-framed.
4. **Never:** an LI / drift / self-assessment result while `li_is_placeholder = TRUE`.

The through-line: the bot is a **branch of the same tree** as the collaborations — public, scored calibration is attraction evidence that feeds the hub, which attracts the funders / collaborators / adopters / citers. But calibration evidence only attracts if it's *real*; a placeholder published as a result would repel exactly the audience we want.

---

## 8. Risks
- **Overclaiming LI before Gate 3** — the top risk; §3 is the guard.
- **A bad public Brier** — calibration cuts both ways; don't run a scored public tournament until calibration is proven on test questions. Anti-attraction and hard to retract.
- **Public comments = reputation** — every auto-posted comment is HumanAIOS in public. Confirm the comment template is Tradition-11-clean and content-safe before scaling comment volume (Z2).
- **Pipeline silently broken** — v2.3 was a repair of a fully-broken comment path that failed *silently* (`p3_comment_posted` always FALSE). Monitor write/post success, don't assume.
- **Cost drift** — per-question LLM calls; watch spend as coverage grows.
- **Model currency** — bot runs `claude-sonnet-4-6`; note when a newer model would improve calibration (an eng call, but outreach flags the attraction upside).

---

## 9. Next actions & open decisions

**Next actions**
| # | Action | Owner | Zone |
|---|---|---|---|
| 1 | Baseline the track record (Supabase MCP auth, or Metaculus export) | Night + me | Z1 |
| 2 | Confirm v2.3 comment path holds over a `test_questions` run | eng | — |
| 3 | Draft standing monitoring queries once Supabase is authed | Me | Z1 |
| 4 | Decide when Gate 3 is prioritized (unlocks asset b) | Night + eng | Z2 |

**Open decisions (Night)**
1. **Supabase access** — authenticate the MCP so I can baseline + build monitoring? (Was held earlier; it's now the bottleneck for asset a.)
2. **Gate-3 priority** — is the real-P3 prompt worth prioritizing on the eng side? It's what makes the unique ACAT-on-forecasting story real.
3. **Tournament target** — AI Benchmarking (bot-native, on-brand) vs Metaculus Cup? I recommend AI Benchmarking.
4. **Comment policy** — keep public auto-comments on, and do you want to review the template before comment volume scales?
