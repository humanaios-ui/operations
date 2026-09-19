# ACAT Live-Service Audit — Zone 2 Response Ledger (S-070226)

**Responds to:** `audits/AUDIT_ACAT_S-062726.md` (Zone 1 audit of `operations/acat/`)
**Status:** Zone 1 artifact — **proposal for Zone 2 (Night) ratification**. Not committed (Zone 3 = Night).
**Molt context:** This is a health-check response for the **Metabolism** organ (`acat/`, `MOLT_STATE.md`). The audit is the molt/immune mechanism (F-41 *Audit Protocol as Molt Mechanism*); this ledger is the "needs a check-up → human decides" step. Layer 2 is MID-MOLT; the findings below are chitin that hasn't hardened.
**Method:** Every disposition below was **verified against the live code** (file:line) this session, not accepted on the audit's word — per GOVERNANCE §165 articulation discipline (what / evidence / risk-of-being-wrong).

---

## 0 · Articulation (GOVERNANCE §165)

- **What this is:** A per-item Zone 2 decision ledger recommending disposition + zone-routing for each P0–P2 item in the audit's §9 triage.
- **Evidence:** Direct code reads of the cited `acat/` files this session (verification ledger §1). 11 of the audit's load-bearing findings independently CONFIRMED; 0 refuted.
- **Risk of being wrong + detection:** Low for CONFIRMED items (code quoted). The residual risk is *runtime* behaviour I did not execute (no live DB / server run) — detectable by the migration + smoke-test steps each disposition names. Where I did not independently verify, the item is marked **[audit-trusted]**.

---

## 1 · Verification ledger (independently confirmed this session)

| # | Finding | Verified evidence | Verdict |
|---|---------|-------------------|:-------:|
| V1 | No auth on any mounted mutating endpoint | `api/app.py` mounts intake/assess/human_score with zero `Depends`/middleware | ✅ CONFIRMED |
| V2 | `humility_audit_router` unmounted (F-21 unreachable) | not in `app.py` includes | ✅ CONFIRMED |
| V3 | `math.erf` with no `import math` (latent 500) | `humility_audit_router.py:104` uses `math.erf`; imports lack `math` | ✅ CONFIRMED |
| V4 | `scoring_service` hardcodes `p1_total=p3_total=0` | `scoring_service.py:5-7` (TODO stub) → `compute_li` always None | ✅ CONFIRMED |
| V5 | Divergent duplicate LI | `calculators.compute_li` guard `if not p1_total` (no None/neg guard) ≠ ingest version | ✅ CONFIRMED |
| V6 | No `handoff` columns / `acat_human_scores` table | migrations stop at `005`; zero `handoff`/`acat_human_scores` refs | ✅ CONFIRMED |
| V7 | App writes `p1_handoff` anyway → 502 | `_build_phase1_row:203` writes `p1_handoff` into a non-existent column | ✅ CONFIRMED |
| V8 | `session_id` not persisted in phase-1 row | `_build_phase1_row:184-205` omits `session_id` → phase-3 lookup breaks | ✅ CONFIRMED |
| V9 | Purity enum mismatch rejects valid submissions | `003:10-15` allows `clean/anchored/contaminated/…`; `purity.py:3-7` requires `two_stage_verified/single_shot_legacy/external_only/…` | ✅ CONFIRMED |
| V10 | `learning_index <= 2.0` cap rejects high-improvement rows | `003:28-29` `CHECK (… <= 2.0)` | ✅ CONFIRMED |
| V11 | Raw `str(exc)` reflected to clients | `intake_router.py:20-36` returns `str(exc)`/`{exc}` in HTTP detail | ✅ CONFIRMED |

> The audit's own self-correction (the `claude-sonnet-4-6` model claim was wrong — model is valid, only the routing prefix was at issue) is accepted; no disposition rests on it.

---

## 2 · Zone 2 decision ledger (per §9 triage)

Legend — Disposition: **RATIFY-FIX** (approve the fix), **MITIGATE-NOW** (interim guard before full fix), **DEFER** (accept-risk, revisit), **CLEANUP** (low-risk hygiene). Zone routing per GOVERNANCE (Z1 drafts PR · Z2 ratifies · Z3 commits/deploys).

### 🔴 P0-URGENT — security (the check-up trigger)
| Item | Verdict | Recommended disposition | Zone |
|------|:------:|-------------------------|------|
| No-auth on live mutating endpoints + corpus poisoning (anon writes poison stored assessments **and** the corpus stats returned to all callers) | V1 ✅ | **MITIGATE-NOW then RATIFY-FIX.** Interim: pause/gate public writes to `/intake/*`, `/assess`, `/human-score` (env flag or edge rule) until an auth model is chosen. This is a **research-validity** risk, not just security — poisoned corpus contaminates N and every downstream LI/percentile. Then Z2 chooses auth model (API-key vs signed) → Z1 PR → Z3 deploy. | **Z2 decision + Z3 mitigation now** |

### 🔴 P0 — research-validity (the instrument doesn't compute what the corpus claims)
| Item | Verdict | Recommended disposition | Zone |
|------|:------:|-------------------------|------|
| 12-dim writes 502: add migration for `p1_handoff`/`p3_handoff` + full `acat_human_scores` table (h_*/gap_* incl. handoff) | V6,V7 ✅ | **RATIFY-FIX** — author migration `006` in the canonical 006–012 order (aligns with `MOLT_STATE` "migrations 006–010 pending"). | Z2 approve → Z3 execute (live DB) |
| `003` purity enum mismatch (valid submissions rejected) | V9 ✅ | **RATIFY-FIX** — correct constraint to the real purity enum; follow IC-032 checklist. Pair with V6 in the same migration wave. | Z2 approve → Z3 execute |
| LI≤2.0 cap rejects legit high-improvement rows | V10 ✅ | **RATIFY-FIX** — relax/remove the cap (note: bugs ledger says a DB-side `learning_index_uncapped` column already exists — reconcile, don't duplicate). | Z2 approve → Z3 execute |
| LI broken/duplicated/untested: consolidate to one verified `compute_li`; drop `scoring_service` hardcoded 0s; stop zero-filling extended-6 | V4,V5 ✅ | **RATIFY-FIX** — pick `ingest_service._compute_learning_index` as canonical (it guards None + negatives), delete `scoring_service`'s stub path, make the tested calculator the served one. Changes live scoring → Z2 sign-off required. | Z2 approve |

### 🟠 P1 — correctness / security hardening
| Item | Verdict | Recommended disposition | Zone |
|------|:------:|-------------------------|------|
| Persist `session_id` in `_build_phase1_row`; wire `dedupe_key` upsert | V8 ✅ | **RATIFY-FIX** — Z1 PR. Low blast radius, unblocks phase-3 pairing. | Z1 PR → Z2 |
| Centralize error handling (stop reflecting `str(exc)`/Supabase bodies; scrub `api_key` from `_JOBS`; filter `metadata` PII) | V11 ✅ | **RATIFY-FIX** — Z1 PR adds an exception middleware; generic client messages, detail to logs only. | Z1 PR → Z2 |
| Mount-or-delete 4 orphan routers (humility_audit, reports, scoring, health) + broken MCP surface | V2 ✅ | **Z2 DECISION** — recommend: **delete** `scoring` (superseded by ingest LI) and the broken MCP surface; **fix+mount** `humility_audit` only after V3 (`import math`) + dimension-set fix, since F-21 is a published concept. | Z2 decision |

### 🟡 P2 — cleanup (low-risk)
| Item | Verdict | Recommended disposition | Zone |
|------|:------:|-------------------------|------|
| Delete 2 confusion-trap dupes (stray extensionless `assess_router`, byte-identical `contracts/human_score_route.py`) | [audit-trusted] | **CLEANUP** — approve; reduces false-fix risk. | Z1 (audit says done) → Z2 confirm |
| `humility_audit_router` dimension set ≠ canonical ALL_12 | V2/V3 area ✅ | **RATIFY-FIX** with the mount decision above — align to canonical ALL_12 before F-21 is ever served. | Z2 |

---

## 3 · Recommended molt sequencing (what's most beneficial + constructive next)

1. **Now (Z3, minutes):** gate public writes — stops active corpus poisoning of a live instrument. This is the single highest-value action; everything else can follow deliberately.
2. **Migration wave 006 (Z2 approve → Z3):** handoff columns + `acat_human_scores` + purity enum + LI-cap — one coherent DB pass that unblocks all 12-dim collection at once.
3. **Scoring consolidation (Z2 approve):** one canonical `compute_li`; retire the stub scorer.
4. **Z1 PRs (→ Z2):** `session_id` persistence, error-handling middleware, orphan router mount-or-delete.
5. **Update `MOLT_STATE.md`:** on completion, record the layer-2 hardening in the Molt Trigger Log; this response is the molt-cycle evidence.

## 4 · Boundary note

This ledger is a **Zone 1 proposal**. Per GOVERNANCE, finding dispositions and any live-DB / deploy actions require **Zone 2 (Night) ratification** and **Zone 3 (Night) execution** — I have not committed this file or touched the `acat/` code. Ratify, edit, or reject item-by-item; I can then draft the Z1 PRs for whatever you approve.

---
*Zone 1 · verified-before-responded · S-070226. Companion: `AUDIT_ACAT_S-062726.md`.*
