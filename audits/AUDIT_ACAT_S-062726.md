# acat/ Live-Service Audit — Step-4 (S-062726)

**Status:** Zone 1 audit artifact — for Z2 (Night) review & decisions
**Scope:** `operations/acat/` — 60 files (the live FastAPI service, mounted by `acat/api/app.py`)
**Method:** 7-agent workflow, service-correctness lens (routes↔contracts, scoring/LI integrity, persistence, endpoint security, real-vs-self-referential tests)
**Date:** 2026-06-27

> **Why this matters now:** the integrity (scoring/LI) holes threaten **research-validity** — the live instrument does not compute what the corpus/papers claim — and the no-auth/corpus-poisoning holes are textbook **DD** findings. Both bear directly on the validity-demonstrated charter close and a clean HA-000 run.

---

## 1. Health snapshot

| status_class | count |
|---|---|
| STRUCTURAL | 8 |
| INTEGRATED | 27 |
| DECORATIVE | 12 |
| ASPIRATIONAL | 12 |
| TESTABLE | 1 |

**17 of 60 files are orphans** (mounted/imported by nothing), including 4 unmounted routers, the MCP surface, the broken scoring_service, and 2 byte-identical/stray duplicates.

## 2. 🔴 Research-validity: scoring integrity

The live instrument does not compute the 12 dimensions / LI as claimed:

- humility_audit_router ACATScores dimension set (truthfulness/service/harm_awareness/autonomy_respect/value_alignment/humility/consistency/handoff_appropriateness/resilience/stability/integrity/coherence) does NOT match canonical ALL_12 (truth/service/harm/autonomy/value/humility/scheme/power/syc/consist/fair/handoff) used by human_score_route + schemas -> F-21 percentile/rank computed over wrong axes (humility_audit_router.py:10-22).
- human_score_route._fetch_corpus_means requests PostgREST 'avg(p1_truth)...' and reads back by literal key row['avg(p1_truth)']; aggregate responses aren't keyed by the raw expression, so the dict comprehension never matches and the broad except returns {} -> corpus_comparison silently ships empty while endpoint returns 201 (human_score_route.py:118,130-141).
- Gap computation force-casts to int: gaps[d]=int(ai_val)-int(h_val) while schema permits float 0-100 -> e.g. AI 74.8 vs human 74.2 yields 0 instead of ~0.6; stored gap_* and receipt gap silently lossy (human_score_route.py:300-306; identical in contracts/human_score_route.py).
- elicitation_service zero-fills extended-6 (scheme/power/syc/consist/fair/handoff=0) and persists them as real rows; ingest._compute_all12_totals sums them so all12_p1_total/all12_p3_total = Core-6-sum + zeros — misleading 12-dim totals (elicitation_service.py:11-18,114,137 -> ingest_service.py:291-299).
- Duplicate, divergent LI implementations: live ingest_service._compute_learning_index (guards p1_total<=0 AND any None) vs scoring.calculators.compute_li (guards `if not p1_total`, no None/negative guard) — tested calculator is NOT the code serving real LI (calculators.py:1-4 vs ingest_service.py:260-288).
- scoring_service.score_session hardcodes p1_total=p3_total=0 so compute_li always returns None, compute_sag always 0, compute_him always None -> the 'scoring service' can never produce a real LI (scoring_service.py:5-16).
- humility_audit_router F-43 HIGH/Pride band is unreachable: humility_audit() always passes li=None but the HIGH branch requires `li and li>0.90`, yet findings narrate 'LI>0.90...' as if evaluated (humility_audit_router.py:58-66,110-112).
- prompt_templates elicit only Core-6; system/human-score path expects ALL_12, so any 12-dim AI-vs-human gap is structurally incomplete and extended-6 are never model-produced (prompt_templates.py:4-10).
- acat_dimension_scorer + calculators.compute_him are permanent stubs returning None — HIM never computed; acat_dimension_scorer returns Core-6 only (acat_dimension_scorer.py:1-11; calculators.py:11-13).
- humility rank via sorted(values).index(humility)+1 mis-ranks on ties; F-21 'CONFIRMED' fires whenever humility merely equals the minimum; also mixes corpus bases (corpus_n=630 vs n_systems=31) (humility_audit_router.py:99-104,116).
- 003 acat_learning_index_cap_check (learning_index<=2.0) rejects legitimately high-improvement rows (low P1 + high P3) -> 502, silently capping valid research data (003_acat_constraints.sql:27-30).
- test_persist_phase3 asserts learning_index==0.8958 from a planted mock echo while real _compute_learning_index = 429/480 = 0.8938 -> live Core-6 LI math never actually verified (test_persist_phase3.py:79-129).
- _compute_learning_index directly indexes phase3_scores[k] for Core-6 keys; a missing key raises KeyError -> uncaught generic 500 rather than 422 (ingest_service.py:283-286).

## 3. 🔴 Research-validity: route ↔ contract / DB mismatches

- phase1_intake.schema.json marks session_id REQUIRED, but ingest_phase1/_ensure_assessment_id never defaults session_id (only assessment_id) -> documented happy-path 422 at $.session_id (ingest_service.py vs phase1_intake.schema.json).
- phase1_intake.schema.json + phase3_submission.schema.json require the 12th dimension 'handoff' and _build_phase1_row/_build_phase3_row write p1_handoff/p3_handoff, but NO migration defines those columns -> every conformant 12-dim write 502s at PostgREST.
- human_score.schema.json requires all 12 h_ dims incl. handoff; acat_human_scores has no migration at all and no h_handoff/gap_handoff column -> live human-score submission 502s.
- scoring_service.score_session()/routes/scoring.py return a dict keyed by assessment_id with NO session_id, but score_result.schema.json lists session_id as REQUIRED -> scorer output would fail its own contract.
- score_result.schema.json field 'li' vs persisted DB column 'learning_index' (migration 004) — naming drift between scorer contract and storage.
- intake_router phase1/phase3 take untyped `payload: dict` with no pydantic model, so OpenAPI is empty and phase1_intake/phase3_submission schemas are enforced only deep in ingest, never at the route boundary (intake_router.py:15-16,27-28).
- assess_router GET /assess/{job_id} returns a free, undeclared dict (no response schema) and ships failed/running jobs as HTTP 200 — uncontracted response shape (assess_router.py:59-69).
- 003_acat_constraints.sql acat_submission_purity_check enum {clean,anchored,contaminated,unknown,agent_self_only} contradicts purity.py + both intake schemas {two_stage_verified,single_shot_legacy,external_only,agent_self_only} -> two_stage_verified/single_shot_legacy/external_only all rejected.
- 002 submission_purity COMMENT documents contamination_status vocabulary ('clean|anchored|contaminated|unknown') instead of the purity enum the app writes — seed of the 003 constraint mismatch.

## 4. 🔴 Security / DD

- No authentication/authorization on ANY mounted mutating endpoint: POST /intake/phase1, /intake/phase3, /assess, /human-score all perform Supabase service-role writes with zero auth (app.py:7-9).
- Corpus poisoning: human_score_route._fetch_corpus_means derives live corpus_comparison from the same unprotected acat_human_scores/assessments table, so an anonymous actor can poison stored assessments AND the corpus statistics returned to every subsequent caller.
- Raw str(exc) reflected to unauthenticated clients across the live surface: intake_router.py:24,36; assess_router.py:31-32 (job error body); human_score_route.py:209-211 (Supabase body as 502 detail); anthropic_client.py:74-75,83-84 (upstream body + raw model text as 502).
- api_key accepted in the JSON request body, flows through run_assessment with no scrubbing, and lives verbatim in the in-memory _JOBS dict / request_payload with no redaction (elicitation_service.py:100-110,153-154; assess_router.py:18).
- Prompt-injection vector: agent_name interpolated verbatim into the Phase-1/Phase-3 elicitation prompts with no sanitization (prompt_templates.py:13-18).
- MCP surface (unmounted but written) is a direct unauthenticated path to Supabase writes + paid provider calls via call_tool -> ingest/run_assessment (mcp_tools.py:154-172; mcp_router.py:51-74).
- MCP CORS reflection: arbitrary client Origin echoed straight into Access-Control-Allow-Origin on SSE + POST; inline comment admits 'Tighten to an allowlist before broad exposure' (mcp_router.py:41-42,66-67,71-72).
- Existence-enumeration oracle: human-score returns 404 for missing assessment vs 201 on success, letting an unauthenticated caller probe which assessment_ids exist (human_score_route.py:286-287).
- payload['metadata'] persisted verbatim with no size/content filtering — any PII/secrets a caller places there are written to Supabase as-is (ingest_service.py:215-216,351-352).
- acat_mcp_wrapper passes raw Supabase/PostgREST error body (exc.read()) straight through as `detail`, and targets an unauthenticated mutating write endpoint (acat_mcp_wrapper.py:45-52).
- Receipt integrity weakened: receipt_hash_sha256 is computed with originstamp=None, then originstamp + receipt_hash are added post-hash, so the provenance hash does not cover the final returned object (human_score_route.py:332-341).
- response_parser accepts bool as a numeric score (True/False are int subclasses) -> a model returning JSON true passes validation as 1 (response_parser.py:23-24).

## 5. Test coverage — false assurance

The suite behind "22 tests passing" substantially tests dead/stub/duplicate code:

- test_emit.py is self-referential: emit_service.emit_assessment_result is a non-wired stub returning {'status':'emitted'}; its only caller is this test asserting the stub's own literal — false assurance of an emit capability that does not exist.
- test_scoring.py tests scoring.calculators (compute_li(100,80)==0.8), a duplicate calculator divorced from the live LI written to Supabase (ingest_service._compute_learning_index) and reachable only via the unmounted scoring router.
- test_assess_endpoint.py asserts the OLD synchronous /assess contract (body['status']=='completed', HTTP 502 on AnthropicClientError) that survives only in the dead extensionless assess_router file; the LIVE async job route returns {job_id,status:'running'} HTTP 200, so all three tests fail against live code and the real async route + GET poll have zero coverage.
- test_app_routes.py is genuine but only two trivial assertions (root lists human_score_url; POST /human-score {} -> 422); no test of /intake/phase1, /intake/phase3, /assess job lifecycle, live LI math, human-score success/receipt shape, or 404/502/500 mapping.
- GET /assess/{job_id} poll route, the in-memory _JOBS store, 404-on-missing, and completed/failed job retrieval are entirely untested (assess_router.py:59-69).
- No test anywhere asserts authentication on the mutating Supabase-write endpoints, so an absent-auth regression is invisible.
- test_persist_phase3 LI assertion reads the planted server-echo (0.8958), not the computed value (0.8938) — the 'computed LI -> persisted LI' edge is unverified; test_two_stage_verified verifies the math in isolation but not the PATCH transmission.
- test_ingest always monkeypatches _persist_phase1, so the _build_phase1_row column mapping (incl. extended-6 columns) is exercised only by test_persist_phase1; Supabase column drift would be missed here.
- test_normalize asserts quality_flags stays empty for valid purity — passes only because derive_quality_flags' CONTAMINATION branch is unreachable dead code, masking a real bug.

## 6. Top bugs (ranked)

| sev | file:loc | defect |
|---|---|---|
| CRITICAL | `acat_submission_purity_check (lines 8-16)` | CHECK enum {clean,anchored,contaminated,unknown,agent_self_only} matches neither purity.py nor the intake schemas {two_stage_verified,single_shot_legacy,external_only,agent_self_only}; the README Phas |
| CRITICAL | `whole file (no p1_handoff/p3_handoff added)` | Instrument extended to 12 dims and _build_phase1_row/_build_phase3_row write p1_handoff/p3_handoff, but no migration ever adds handoff columns -> every conformant 12-dim Phase 1/Phase 3 write 502s (Po |
| CRITICAL | `scores.required[].handoff` | Schema requires 'handoff'; _build_phase3_row writes p3_handoff with no DB column, so the PATCH in _persist_phase3 fails at Supabase — documented Phase-3 success (LI=0.8943) is not runnable. |
| CRITICAL | `whole schema / acat_human_scores target` | Route persists to public.acat_human_scores (assessment_uuid, h_truth..h_handoff, gap_*), but NO CREATE TABLE migration for acat_human_scores exists anywhere in the repo -> any live human-score submiss |
| CRITICAL | `lines 36,52-58,199-209,317` | Documents 'collects all 12 dimensions' and lists handoff columns/payloads as runnable, but no handoff columns exist and the purity constraint rejects two_stage_verified -> all three documented happy-p |
| CRITICAL | `mcp_tools.py:24,63,67,104,112,133` | Module uses JSON literals false/true (undefined Python names) in inputSchema dicts at module level -> `import mcp_tools` raises NameError; cascades to mcp_services and mcp_router, so adding include_ro |
| CRITICAL | `mcp_router.py:9` | Imports from non-existent acat.api.services.mcp_service (actual module is mcp_services.py, plural) -> ModuleNotFoundError; the router cannot be imported. |
| CRITICAL | `humility_audit_router.py:104 (no import math)` | calls math.erf(...) but 'math' is never imported -> NameError -> unhandled 500 on every invocation of the F-21 Humility Audit endpoint (latent: router is also unmounted). |
| HIGH | `ingest_service.py:182-218 vs 134-135,363-368` | session_id is required + used as phase3 lookup fallback key, but _build_phase1_row NEVER includes session_id in the INSERT -> phase3 lookup-by-session_id raises 'assessment row not found', existing_ro |
| HIGH | `app.py:3-9` | humility_audit_router is never include_router'd; the entire F-21 Humility Audit endpoint (POST /humility-audit) exists in the tree but is unreachable in the live service (only intake/assess/human_scor |
| HIGH | `required[].session_id` | Schema makes session_id REQUIRED but ingest_phase1 only defaults assessment_id, never session_id; README's documented Phase-1 payload omits it -> documented happy path 422s at $.session_id. |
| HIGH | `humility_audit_router.py:10-22,98-100` | Audit's 12-dimension set contradicts the canonical ALL_12 used by human_score_route + schemas, so F-21 status/percentile are computed over the wrong axes (scoring validity defect). |
| HIGH | `scoring_service.py:5-16` | p1_total/p3_total hardcoded to 0 (TODO never done); compute_li(0,0) returns None, compute_sag=0, compute_him=None -> the scoring service can never produce a real Learning Index while reporting score_s |
| HIGH | `dedupe.py:1-5 (consumer ingest_service._persist_phase1:221-257)` | dedupe_key is computed but never written to a column or used in any ON CONFLICT/upsert; _persist_phase1 does a plain POST insert, so duplicate phase1 submissions create duplicate acat_assessments_v1 r |
| HIGH | `flags.py:4` | derive_quality_flags appends CONTAMINATION only when submission_purity=='contaminated', which is not a valid purity value (rejected upstream), so quality_flags is ALWAYS [] and contaminated submission |
| HIGH | `mcp_tools.py:154-172,69,114,135` | call_tool routes intake_phase1/phase3/assess to ingest/run_assessment with no auth or rate limiting — a direct unauthenticated path to Supabase writes + paid provider calls (mitigated only by the modu |
| HIGH | `test_assess_endpoint.py:62-83 vs assess_router.py:35-69` | Happy-path asserts body['status']=='completed' but the live route is async (returns job_id, runs in daemon thread); monkeypatch only affects the background thread, so the test FAILS against live code  |
| MEDIUM | `human_score_route.py:118,130-141` | _fetch_corpus_means reads PostgREST aggregate response by the literal key row['avg(p1_truth)'] which never matches (aggregates keyed by alias), so the broad except returns {} and corpus_comparison shi |
| MEDIUM | `assess_router.py:18,64-68` | _JOBS is an unbounded in-process dict with no eviction/TTL -> memory growth for container lifetime; 404 message claims 'expired' but nothing ever expires, and jobs vanish only on restart (in-flight re |
| MEDIUM | `acat_learning_index_cap_check (lines 27-30)` | CHECK learning_index <= 2.0 but LI = P3total/P1total is unbounded above; a legitimately high-improvement row is rejected -> 502, silently capping valid research data. |

## 7. Orphans (mounted/imported by nothing)

- acat/api/routes/assess_router (stray extensionless duplicate, not importable)
- acat/api/routes/health.py
- acat/api/routes/humility_audit_router.py
- acat/api/routes/reports.py
- acat/api/routes/scoring.py
- acat/api/services/emit_service.py
- acat/api/services/mcp_router.py
- acat/api/services/mcp_services.py
- acat/api/services/mcp_tools.py
- acat/api/services/report_service.py
- acat/api/services/scoring_service.py
- acat/contracts/human_score_route.py (byte-identical duplicate of live route, misplaced in contracts/)
- acat/mcp/server.py
- acat/mcp/wrappers/acat_mcp_wrapper.py
- acat/scoring/acat_dimension_scorer.py
- acat/scoring/validation/inter_rater_eval.py
- acat/contracts/score_result.schema.json

## 8. Priority admin actions

1. Add a migration creating the handoff columns (p1_handoff, p3_handoff, and the entire acat_human_scores table with h_*/gap_* incl. h_handoff/gap_handoff) — unblocks every 12-dimension Phase 1 / Phase 3 / human-score write currently 502ing.
2. Fix 003_acat_constraints.sql acat_submission_purity_check to the real purity enum {two_stage_verified, single_shot_legacy, external_only, agent_self_only} (and follow the IC-032 checklist) — unblocks the two-stage Phase 3 happy path.
3. Add authentication/authorization to all mounted mutating endpoints (/intake/phase1, /intake/phase3, /assess, /human-score); without it anonymous callers poison stored assessments AND the live corpus statistics returned to every caller.
4. Persist session_id in _build_phase1_row (and stop dropping dedupe_key/quality_flags/agent_name_canonical); add an upsert/on-conflict so phase3 lookup-by-session_id works and duplicate submissions don't create duplicate rows.
5. Fix human_score_route._fetch_corpus_means PostgREST aggregate key handling (alias the avg() columns) so corpus_comparison stops silently shipping empty, and stop force-casting gaps to int (preserve float precision).
6. Centralize error handling / middleware to stop reflecting raw str(exc) and Supabase/upstream bodies to clients (intake_router, assess_router, human_score_route, anthropic_client), and scrub api_key out of the _JOBS store and error wrappers.
7. Relax or remove the learning_index <= 2.0 cap (003) so legitimately high-improvement assessments aren't rejected/502'd.
8. Delete the two confusion traps — the stray extensionless acat/api/routes/assess_router and the byte-identical acat/contracts/human_score_route.py duplicate (false-fix risk) — and either mount or delete the orphan routers (humility_audit, reports, scoring, health) and broken MCP surface.

## 9. Zone triage — who decides / executes

| Priority | Item | Type | Z-level |
|---|---|---|---|
| **P0-URGENT** | No-auth on live mutating endpoints + corpus poisoning (anyone can write the corpus AND the stats returned to all callers) | security/DD | **Z2 decision** (auth model) + interim mitigation (gate/pause public writes) |
| **P0** | 12-dim collection 502s: add migration for `p1_handoff`/`p3_handoff` + the whole `acat_human_scores` table; fix `003` purity enum + LI≤2.0 cap | validity | **Z2 approve → Z3 execute** (live DB; slot into the canonical 006–012 order) |
| **P0** | LI broken/duplicated/untested: consolidate to one verified `compute_li`; remove `scoring_service` hardcoded 0s; stop zero-filling extended-6 | validity | **Z2 approve** (changes live scoring) |
| **P1** | Persist `session_id` in `_build_phase1_row`; wire `dedupe_key` upsert | correctness | Z1 PR → Z2 |
| **P1** | Centralize error handling (stop reflecting raw `str(exc)`/Supabase bodies; scrub `api_key`; filter `metadata` PII) | security | Z1 PR → Z2 |
| **P1** | Mount-or-delete the 4 orphan routers (humility_audit, reports, scoring, health) + the broken MCP surface | architecture | **Z2 decision** |
| **P2 (this PR)** | Delete 2 confusion-trap dupes (stray extensionless `assess_router`, byte-identical `contracts/human_score_route.py`) | cleanup | **Z1 — done here** |

*Verification note: an agent claim that `claude-sonnet-4-6` is a nonexistent model was incorrect — it is valid; concern is the routing prefix only.*
