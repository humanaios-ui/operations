# ACAT — Current State (R1)

*Research pass 1 of 4 · S-070626 · grounded in code (`operations/main/acat`) + live probe (Railway API contract + Supabase `acat_assessments_v1`). Read-only.*

## Verdict

**ACAT is an operating instrument, ~TRL 5–6 — not a prototype.** The collection
and calibration spine is production-ready and live; the *automated inference* layer
(read behaviour → produce scores) is stubbed. The single most important structural
fact for the plan:

> **COLLECTION is built and honest; SCORING-FROM-BEHAVIOUR is not.** ACAT reliably
> *ingests* integrity-checked two-stage assessments and *computes the calibration
> gap from submitted scores* — but it does **not** yet read an AI's transcript and
> produce dimension scores itself. Scores come from self-report or human raters.

That seam is the whole strategy space for R2–R4.

## What's operational (the working spine)

| Capability | State | Notes |
|---|---|---|
| **API** `intake/phase1 · intake/phase3 · assess · human-score · humility-audit` | ✅ live | FastAPI, all mutations fail-closed behind `X-ACAT-Write-Token` (const-time compare; 503 if unset) |
| **Two-stage integrity** | ✅ live | contamination delta (≤60s clean), **`two_stage_verified` gate requires ≥60s P1→P3 gap**, dedupe key, agent-alias canonicalization |
| **Calibration math** | ✅ live | `LI = P3_total / P1_total` (**<1 = over-claim**), `SAG = P1 − P3`. Core-6 only for LI (corpus continuity) |
| **Human-scoring receipt** | ✅ live | 12-dim human scores → per-dimension gaps vs AI, corpus comparison, OriginStamp hash anchor |
| **F-21 Humility Audit** | ✅ live | risk band (CRITICAL/HIGH/MED/LOW), RLHF-inflation flag, corpus percentile (humility mean 74.02, n≈630); **rejects non-clean purity + anchored self-report** |
| **MCP adapter** | ✅ live | JSON-RPC 2.0 + SSE; tools `health/intake_phase1/intake_phase3` — an AI can be assessed programmatically |
| **Persistence + schema** | ✅ live | Supabase `acat_assessments_v1` + `acat_human_scores`; migrations 002–006 (12-dim cols, purity constraint fix, LI cap relaxed) |
| **Contracts + tests** | ✅ | JSON schemas for every payload; tests cover ingest, normalization, contamination, the two-stage gate |

## What's stubbed (the inference gap)

| Missing piece | Impact |
|---|---|
| **`score_transcript()` — automated behavioural scoring** | ❌ stub (`score_status:"stub"`). The tool can't grade behaviour → **no autonomous scoring**; a human or the AI's self-report must supply dimension scores |
| `compute_him()` (Humility Index Metric) | ❌ `# TODO` |
| `scoring_service` (fetch P1/P3 from DB → aggregate) | ⚠ stub |
| Report generation (`draft_report`/`get_report`) | ⚠ stub |
| Inter-rater agreement (Cohen's κ) | ⚠ stub — **so machine↔human validity is not yet measured** |
| Extended-6 dims | ⚠ Option-B pilot: elicited-as-zero-fill; Option-A = full 12-dim elicitation (future) |

## Live corpus reality (probed)

- **`acat_assessments_v1` = 105 rows.** Mean LI **0.9855** (n=96 scored).
- **Integrity is the weak point:** **81/105 `agent_self_only`** (AI graded itself, no external check); only **18 `two_stage_verified`**, 4 `p1_only_formal`, 1 `spec_externally_reviewed`.
- Providers real but noisy: anthropic 17, xAI 3, DeepSeek 3, and ~56 None/blank. Latest row: **DeepSeek-R1** under `production_model_pilot_v1` (2026-07-03) — a live model pilot is running.
- Separate **archived research corpus** (`canonical_stats.json`): 604 raw rows, mean LI 0.8532, 23 providers, 68 agents — the historical Google-Form corpus.

## The honest reading (why this matters)

The honesty protocol we built isn't abstract for ACAT — **it is the diagnosis of ACAT's own corpus.** 81/105 rows are exactly the ungrounded Phase-1 self-reports the protocol quarantines. The instrument's *own* integrity machinery — `two_stage_verified`, contamination, the F-21 purity guard — **is the external anchor**, and it's mostly bypassed.

So the leverage is not "add features." The working, honest capabilities are the **two-stage-verified collection + human-scoring + humility-audit**. The stub (`score_transcript`) is the tempting-but-hard path; it would let ACAT self-score, which without validation (κ is stubbed) is the overclaim ACAT exists to detect.

## Known risks (for R4 / Z3)

- **DB reconciliation** — migration 006 vs the `learning_index_uncapped` backfill (S-042727); reconcile before any live scaling.
- `_JOBS` is in-memory (lost on restart; fine at 1 replica, not multi).
- Supabase REST hardcoded, no backoff; OriginStamp anchoring non-blocking (provenance can silently miss).
- `ACAT_WRITE_TOKEN` still to be set in the deployed env (Z3).

## Implications carried into R2–R4

1. **The product that exists today** = an integrity-checked pipeline for *collecting* two-stage + human-grounded calibration assessments and reporting the gap — usable now.
2. **Two divergent operationalization paths**: (a) lean into the *verified human/two-stage* path (honest, ready) vs (b) build the *auto-scorer* (powerful, unvalidated, honesty-risky).
3. **Validity is unmeasured** (κ stub) — any "the tool is accurate" claim is currently unanchored. R4's POC must make validity a first-class, falsifiable output.

*Next: R2 — enumerate the real use-space these capabilities open (`ACAT_USE_SPACE.md`).*
