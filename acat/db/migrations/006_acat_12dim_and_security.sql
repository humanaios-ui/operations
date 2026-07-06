-- file: acat/db/migrations/006_acat_12dim_and_security.sql
-- Audit S-062726 P0 remediation (Zone 1 proposal; Zone 3/Night applies to live DB).
--
-- Pre-migration checklist (IC-032 gate):
--   * Additive and idempotent only (ADD COLUMN IF NOT EXISTS / CREATE TABLE IF NOT EXISTS).
--   * Re-runnable. No existing column values altered or dropped.
--   * DROP CONSTRAINT ... IF EXISTS before re-adding, so purity/LI-cap fixes are re-runnable.
--
-- ⚠ VERIFY-AGAINST-LIVE-SCHEMA BEFORE APPLYING (Z3):
--   Migrations 002–005 do NOT create the base p1_/p3_ dimension columns; the base
--   table + Core/Extended-6 columns were created out-of-band (Supabase console), so
--   this file cannot see the full live schema. The IF NOT EXISTS guards make it safe
--   to run regardless, but confirm the p3_* set exists on the live table first.

-- 1. 12th-dimension (handoff) write columns — the direct cause of 12-dim 502s.
--    _build_phase1_row writes p1_handoff; _build_phase3_row writes p3_handoff.
--    Extended-6 added defensively (IF NOT EXISTS) in case any are also missing.
ALTER TABLE public.acat_assessments_v1
  ADD COLUMN IF NOT EXISTS p1_scheme   numeric,
  ADD COLUMN IF NOT EXISTS p1_power    numeric,
  ADD COLUMN IF NOT EXISTS p1_syc      numeric,
  ADD COLUMN IF NOT EXISTS p1_consist  numeric,
  ADD COLUMN IF NOT EXISTS p1_fair     numeric,
  ADD COLUMN IF NOT EXISTS p1_handoff  numeric,
  ADD COLUMN IF NOT EXISTS p3_scheme   numeric,
  ADD COLUMN IF NOT EXISTS p3_power    numeric,
  ADD COLUMN IF NOT EXISTS p3_syc      numeric,
  ADD COLUMN IF NOT EXISTS p3_consist  numeric,
  ADD COLUMN IF NOT EXISTS p3_fair     numeric,
  ADD COLUMN IF NOT EXISTS p3_handoff  numeric;

-- 2. acat_human_scores table (human_score.schema.json requires all 12 h_ dims
--    incl. handoff, plus gap_* per dimension). No migration defined it -> live
--    human-score submissions 502. Created here.
CREATE TABLE IF NOT EXISTS public.acat_human_scores (
  id             bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  assessment_id  text,
  session_id     text,
  rater_id       text,
  -- human scores, all 12 dimensions
  h_truth numeric, h_service numeric, h_harm numeric, h_autonomy numeric,
  h_value numeric, h_humility numeric, h_scheme numeric, h_power numeric,
  h_syc numeric, h_consist numeric, h_fair numeric, h_handoff numeric,
  -- ai-vs-human gaps, all 12 dimensions (float precision — no int cast)
  gap_truth numeric, gap_service numeric, gap_harm numeric, gap_autonomy numeric,
  gap_value numeric, gap_humility numeric, gap_scheme numeric, gap_power numeric,
  gap_syc numeric, gap_consist numeric, gap_fair numeric, gap_handoff numeric,
  created_at     timestamptz DEFAULT now()
);

-- 3. Fix the purity CHECK constraint — 003 used the wrong vocabulary
--    {clean,anchored,contaminated,unknown,agent_self_only} which rejects the real
--    purity enum the app writes. Replace with purity.py VALID_PURITY_VALUES.
ALTER TABLE public.acat_assessments_v1
  DROP CONSTRAINT IF EXISTS acat_submission_purity_check;

-- 3a. Reconcile LEGACY purity vocabulary before re-adding the constraint.
--     Live probe (S-070626) found 6 rows on pre-canonical values that would violate
--     the CHECK (this is the "constraint violated by some row" error):
--       self_administered (1), spec_externally_reviewed (1), p1_only_formal (4).
--     Idempotent: only rewrites rows whose value is not already canonical; re-running
--     is a no-op once mapped. This is a DELIBERATE, minimal data reconciliation (the
--     one place this file mutates existing values) — required for the purity fix.
--     ⚠ Z2 DECISION (Night ratifies the mapping before Z3 apply):
--       self_administered      -> agent_self_only   (a self-run assessment is self-only)
--       spec_externally_reviewed -> external_only    (external review = external grounding)
--       p1_only_formal         -> single_shot_legacy (formal Phase-1-only submission;
--                                 alternative: agent_self_only — Night's call)
--     None of these are `two_stage_verified`, so the POC's verified-gate is unaffected
--     by the exact mapping.
UPDATE public.acat_assessments_v1 SET submission_purity = 'agent_self_only'
  WHERE submission_purity = 'self_administered';
UPDATE public.acat_assessments_v1 SET submission_purity = 'external_only'
  WHERE submission_purity = 'spec_externally_reviewed';
UPDATE public.acat_assessments_v1 SET submission_purity = 'single_shot_legacy'
  WHERE submission_purity = 'p1_only_formal';

ALTER TABLE public.acat_assessments_v1
  ADD CONSTRAINT acat_submission_purity_check
  CHECK (submission_purity IS NULL OR submission_purity IN (
    'two_stage_verified',
    'single_shot_legacy',
    'external_only',
    'agent_self_only'
  ));

-- 4. Relax the learning_index <= 2.0 cap — it rejected legitimately high-improvement
--    rows (low P1 + high P3). Keep a sane non-negative floor instead of an upper cap.
--    NOTE: bugs ledger (S-042727) mentions a DB-side 'learning_index_uncapped' column
--    already added + 65 rows backfilled — reconcile with that before applying.
ALTER TABLE public.acat_assessments_v1
  DROP CONSTRAINT IF EXISTS acat_learning_index_cap_check;
-- Re-runnability: drop the constraint we are about to add. A prior partial apply of
-- this migration already created acat_learning_index_nonneg_check, so re-adding it
-- without a DROP fails with 42710 "constraint already exists". (Step-3 above drops the
-- matching name before ADD; step-4 originally dropped only the OLD cap name — this line
-- fixes that asymmetry so the whole file is idempotent per the IC-032 gate.)
ALTER TABLE public.acat_assessments_v1
  DROP CONSTRAINT IF EXISTS acat_learning_index_nonneg_check;
ALTER TABLE public.acat_assessments_v1
  ADD CONSTRAINT acat_learning_index_nonneg_check
  CHECK (learning_index IS NULL OR learning_index >= 0);
