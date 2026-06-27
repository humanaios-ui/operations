-- file: acat/db/migrations/006_acat_handoff_human_scores_and_constraints.sql
-- Created: 2026-06-27 (S-062726). Fixes three schema/code drifts found in the acat/ Step-4 audit:
--   (1) Extended-6 dimension columns (incl. handoff) + all-12 totals are written by
--       ingest_service._build_phase1_row/_build_phase3_row but were never added by any
--       migration -> every conformant 12-dimension Phase 1 / Phase 3 write 502s.
--   (2) acat_human_scores does not exist as a table -> every human-score write 502s.
--   (3) 003's purity CHECK enum and the LI<=2.0 cap contradict the app and reject valid data.
-- Additive + idempotent (IF NOT EXISTS / guarded DROP). Zone 1 draft -> Z2 ratify -> Z3 apply.

-- (1) Extended-6 dimension columns + all-12 totals on acat_assessments_v1 -------------------
ALTER TABLE public.acat_assessments_v1
  ADD COLUMN IF NOT EXISTS p1_scheme      numeric,
  ADD COLUMN IF NOT EXISTS p1_power       numeric,
  ADD COLUMN IF NOT EXISTS p1_syc         numeric,
  ADD COLUMN IF NOT EXISTS p1_consist     numeric,
  ADD COLUMN IF NOT EXISTS p1_fair        numeric,
  ADD COLUMN IF NOT EXISTS p1_handoff     numeric,
  ADD COLUMN IF NOT EXISTS p3_scheme      numeric,
  ADD COLUMN IF NOT EXISTS p3_power       numeric,
  ADD COLUMN IF NOT EXISTS p3_syc         numeric,
  ADD COLUMN IF NOT EXISTS p3_consist     numeric,
  ADD COLUMN IF NOT EXISTS p3_fair        numeric,
  ADD COLUMN IF NOT EXISTS p3_handoff     numeric,
  ADD COLUMN IF NOT EXISTS all12_p1_total numeric,
  ADD COLUMN IF NOT EXISTS all12_p3_total numeric;

-- (2) acat_human_scores table (human_score_route writes here; Z2-IC-02 S-053026-02) ---------
-- Columns mirror _persist_human_score() in acat/api/routes/human_score_route.py exactly,
-- plus nullable rater_did / submission_signature for forward-compat with the Z2-SSI-01
-- human_score.schema.json amendment.
CREATE TABLE IF NOT EXISTS public.acat_human_scores (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  assessment_uuid      text NOT NULL,
  assessment_id        text,
  rater_id             text,
  rater_did            text,
  submission_signature text,
  rated_at             timestamptz,
  h_truth numeric,  h_service numeric,  h_harm numeric,    h_autonomy numeric,
  h_value numeric,  h_humility numeric, h_scheme numeric,  h_power numeric,
  h_syc numeric,    h_consist numeric,  h_fair numeric,    h_handoff numeric,
  gap_truth numeric,  gap_service numeric,  gap_harm numeric,    gap_autonomy numeric,
  gap_value numeric,  gap_humility numeric, gap_scheme numeric,  gap_power numeric,
  gap_syc numeric,    gap_consist numeric,  gap_fair numeric,    gap_handoff numeric,
  notes                text,
  created_at           timestamptz NOT NULL DEFAULT now()
);

-- GRANTs per the 2026-05-30 Supabase Data API change (service-role writes; anon/auth per RLS policy).
GRANT SELECT, INSERT, UPDATE ON public.acat_human_scores TO anon, authenticated;
GRANT ALL ON public.acat_human_scores TO service_role;

-- (3a) Fix the purity CHECK to match the app's purity.py VALID_PURITY_VALUES. -------------
-- NON-DESTRUCTIVE TRANSITIONAL superset: keeps the legacy 002 vocab so this ALTER never
-- fails on existing rows.
-- *** NIGHT DECISION (flagged): backfill legacy rows (clean/anchored/contaminated/unknown)
--     to the canonical vocab, then drop the legacy values from this constraint in a
--     follow-up migration. The correct legacy->canonical mapping is a Z2 call. ***
ALTER TABLE public.acat_assessments_v1 DROP CONSTRAINT IF EXISTS acat_submission_purity_check;
ALTER TABLE public.acat_assessments_v1
  ADD CONSTRAINT acat_submission_purity_check
  CHECK (submission_purity IS NULL OR submission_purity IN (
    -- canonical (acat/normalization/purity.py):
    'two_stage_verified', 'single_shot_legacy', 'external_only', 'agent_self_only',
    -- legacy (migration 002 vocab; deprecated — to be backfilled then removed):
    'clean', 'anchored', 'contaminated', 'unknown'
  ));

-- (3b) Remove the arbitrary LI<=2.0 cap. -----------------------------------------------------
-- LI = P3_total / P1_total is unbounded above; legitimately high-improvement rows
-- (low P1, high P3) were being rejected -> 502 and silently dropped. LI validity is
-- enforced in code (ingest_service._compute_learning_index), not by a hard DB cap.
ALTER TABLE public.acat_assessments_v1 DROP CONSTRAINT IF EXISTS acat_learning_index_cap_check;
