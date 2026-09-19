-- =============================================================================
-- Migration 007 — operational_state column guard + seed fix
-- Applies when table already exists from a prior partial migration
-- Safe to run multiple times (idempotent)
-- =============================================================================

BEGIN;

-- Step 1: Add any missing columns to operational_state
-- Pattern: DO $$ guard — no-op if column already exists

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'operational_state'
    AND column_name = 'gate_status'
  ) THEN
    ALTER TABLE public.operational_state
      ADD COLUMN gate_status TEXT NOT NULL DEFAULT 'Gate 2 PASSED';
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'operational_state'
    AND column_name = 'ord_day'
  ) THEN
    ALTER TABLE public.operational_state ADD COLUMN ord_day INT;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'operational_state'
    AND column_name = 'runway_days'
  ) THEN
    ALTER TABLE public.operational_state ADD COLUMN runway_days INT;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'operational_state'
    AND column_name = 'revenue_usd'
  ) THEN
    ALTER TABLE public.operational_state
      ADD COLUMN revenue_usd NUMERIC(12,2) NOT NULL DEFAULT 0.00;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'operational_state'
    AND column_name = 'open_z3_count'
  ) THEN
    ALTER TABLE public.operational_state
      ADD COLUMN open_z3_count INT NOT NULL DEFAULT 0;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'operational_state'
    AND column_name = 'escalated_z3_count'
  ) THEN
    ALTER TABLE public.operational_state
      ADD COLUMN escalated_z3_count INT NOT NULL DEFAULT 0;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'operational_state'
    AND column_name = 'corpus_n_total'
  ) THEN
    ALTER TABLE public.operational_state ADD COLUMN corpus_n_total INT;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'operational_state'
    AND column_name = 'corpus_n_phase1'
  ) THEN
    ALTER TABLE public.operational_state ADD COLUMN corpus_n_phase1 INT;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'operational_state'
    AND column_name = 'corpus_n_li'
  ) THEN
    ALTER TABLE public.operational_state ADD COLUMN corpus_n_li INT;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'operational_state'
    AND column_name = 'last_wgs_session'
  ) THEN
    ALTER TABLE public.operational_state ADD COLUMN last_wgs_session TEXT;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'operational_state'
    AND column_name = 'last_updated_by'
  ) THEN
    ALTER TABLE public.operational_state ADD COLUMN last_updated_by TEXT;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'operational_state'
    AND column_name = 'notes'
  ) THEN
    ALTER TABLE public.operational_state ADD COLUMN notes TEXT;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'operational_state'
    AND column_name = 'updated_at'
  ) THEN
    ALTER TABLE public.operational_state
      ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
  END IF;
END $$;

-- Ensure pipeline_color CHECK constraint exists on correct values
-- (safe no-op if already set correctly; Postgres ignores duplicate constraints
--  only if named — we use unnamed so this is additive only if missing)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'operational_state'
    AND column_name = 'pipeline_color'
  ) THEN
    ALTER TABLE public.operational_state
      ADD COLUMN pipeline_color TEXT NOT NULL DEFAULT 'YELLOW'
      CHECK (pipeline_color IN ('GREEN','YELLOW','RED','UNKNOWN'));
  END IF;
END $$;

-- Step 2: Ensure GRANTs are present (idempotent)
GRANT SELECT, INSERT, UPDATE, DELETE ON public.operational_state
  TO anon, authenticated, service_role;

-- Step 3: Seed the single row — upsert so re-runs don't duplicate
INSERT INTO public.operational_state (
  id, pipeline_color, gate_status, ord_day,
  corpus_n_total, corpus_n_phase1, corpus_n_li,
  last_updated_by, notes
)
VALUES (
  1, 'YELLOW', 'Gate 2 PASSED', 51,
  629, 516, 307,
  'migration_007_fix',
  'Seeded by migration_007_operational_state_fix. Column guard applied.'
)
ON CONFLICT (id) DO UPDATE SET
  gate_status      = EXCLUDED.gate_status,
  ord_day          = EXCLUDED.ord_day,
  corpus_n_total   = EXCLUDED.corpus_n_total,
  corpus_n_phase1  = EXCLUDED.corpus_n_phase1,
  corpus_n_li      = EXCLUDED.corpus_n_li,
  last_updated_by  = EXCLUDED.last_updated_by,
  notes            = EXCLUDED.notes,
  updated_at       = NOW();

COMMIT;

-- =============================================================================
-- VERIFICATION (run immediately after)
-- =============================================================================
-- 1. Confirm all columns present:
-- SELECT column_name, data_type
-- FROM information_schema.columns
-- WHERE table_schema = 'public' AND table_name = 'operational_state'
-- ORDER BY ordinal_position;
--
-- 2. Confirm seed row:
-- SELECT id, pipeline_color, gate_status, ord_day,
--        corpus_n_total, corpus_n_phase1, corpus_n_li
-- FROM public.operational_state;
--
-- Expected: 1 row — id=1, pipeline_color=YELLOW, gate_status='Gate 2 PASSED',
--           ord_day=51, corpus_n_total=629, corpus_n_phase1=516, corpus_n_li=307
-- =============================================================================
