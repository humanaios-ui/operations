# ACAT POC — Stage 2: Roster & Human-Rater Protocol

*Z1 draft for Z2 ratification · S-070626 · operationalizes Stage 2 of [[ACAT_POC_PLAN]].
Numbers below are proposals — Night ratifies the roster, the K/M counts, and the rater
set. Stage 0 (schema + write-gate) is live; Stage 1 (κ + scoring_service) is merged (#46).*

## Purpose

Define exactly *what we assess*, *how many*, *who grounds it*, and *what is allowed
into the published Observatory* — so the collection that follows produces a **verified,
externally-anchored** corpus with a **measured κ**, not more self-report.

## 1 · Model roster

Canonical agents (`agent_aliases.yml`): claude, gpt-4, gpt-3.5, gemini, llama, mistral,
grok, qwen. DeepSeek is already in the live corpus but **missing from the alias file** —
add it (small follow-up).

**Proposed roster (≥6 live production models):**

| # | Provider | Model (representative) | In corpus? |
|---|---|---|---|
| 1 | Anthropic | Claude (Opus/Sonnet, current) | ✅ (17 rows) |
| 2 | OpenAI | GPT (current flagship) | partial |
| 3 | Google | Gemini (current) | — |
| 4 | DeepSeek | DeepSeek-R1 | ✅ (pilot) |
| 5 | xAI | Grok (current) | ✅ (3 rows) |
| 6 | Meta | Llama (current) | — |
| +7/8 | Mistral · Alibaba | Mistral · Qwen | *optional, for breadth* |

Rationale: one model per major provider family gives cross-provider coverage (the point
of a *benchmark*) while keeping human-rating load tractable. Exact model IDs pinned at
ratification (they move fast); record the pinned ID in `agent_name` + `model_family`.

## 2 · Volume (per-model K, shared κ subset M)

*Sized so the human-rater load is real-world-achievable while κ is meaningful.*

- **K = 5** two-stage assessments per model → **~30 verified assessments** across 6 models.
- **M = 12** assessments form the **shared κ subset**, each independently scored by **≥2
  human raters** (feeds Stage-1 `compute_inter_rater_agreement`). Spread M across models,
  not concentrated in one.
- Rater time — not code — is the rate limit; K/M are deliberately modest for a POC.

## 3 · The assessment unit (what "verified + human-grounded" means)

An Observatory-eligible datapoint is **both**:
1. A **two-stage assessment** — Phase-1 self-report → **≥60s gap** → Phase-3 (the tool's
   `two_stage_verified` gate + contamination check must pass), **and**
2. A **linked human score** in `acat_human_scores` — a human rater's 12-dim scores on the
   same transcript, yielding per-dimension gaps vs the model's self-report.

The **external anchor is the human score.** LI (P3/P1) is retained as the self-shift
signal, but the *verified* claim rests on the human gap, and trust in it rests on κ.

## 4 · Human-rater protocol

- **≥2 raters.** Both score the **entire M subset** independently (blind to each other and
  to the model's scores) → inter-rater κ. Beyond M, single-rater grounding is acceptable
  (still an external anchor), but only M carries κ.
- **Rubric:** the 12 dimensions on the 0–100 scale already defined in the contracts
  (`human_score.schema.json`). Raters get written anchor descriptions per dimension
  (draft alongside; ratify with the roster).
- **Integrity discipline:** raters submit via `POST /human-score` with the write token;
  contamination/purity fields honestly set. No rater grades their own prior interaction.
- **Provenance:** every human score carries `rater_id`; the Observatory shows it.

## 5 · The hard purity gate (non-negotiable policy)

> **Only rows with `submission_purity = two_stage_verified` AND a linked
> `acat_human_scores` entry enter the published Observatory dataset.**

Everything else — `agent_self_only`, `single_shot_legacy`, `external_only`,
Phase-1-only — stays in the corpus for the record but is **excluded** from the verified
Observatory. This is the R3/R4 guardrail written as enforceable policy: "verified" must
never silently degrade to self-report to hit volume. Recommend enforcing it at publish
time (a query filter) **and** flagging any Observatory row that lacks a linked human score.

## 6 · Validity target (the POC's actual product)

- κ is **computed and published** (Stage-1 layer) across the M subset. **The POC passes its
  honesty bar iff κ is measured and disclosed** — a low κ is a finding to report, not a
  failure to hide.
- The published corpus carries the **honesty stamp** (`self_referential: false`, external
  anchor) from the harness honesty layer — it earns the claim it makes.

## 7 · Parallel: the turtle (honesty-gated)

Concurrently, run ACAT on our own platform AIs under the protocol triad:
- self-assessments tagged `self_referential: true` → quarantined;
- **externally anchored** by a human rater (Night) *or* measured against this verified
  corpus as the yardstick;
- **D-OVERCLAIM** tripwire live on Humility; Z2 ratifies before any turtle result is cited.
- Purpose: do *our own* AIs over-claim, measured against the same anchor? Dogfooding,
  honestly.

## Z2 decisions to ratify

1. **Roster** — confirm the 6 (or +Mistral/Qwen) and pin exact model IDs.
2. **Counts** — K=5, M=12, ≥2 raters (adjust to rater availability).
3. **Raters** — who; and approve the per-dimension rubric anchors (drafted next).
4. **Gate enforcement** — approve the publish-time verified-only filter.
5. **Turtle** — confirm running it in parallel and who grounds it.

*On ratification → Stage 3 (collect). The one thing that makes or breaks it stays §5:
the human anchor is a hard gate, and κ is a first-class output — or it doesn't ship.*
