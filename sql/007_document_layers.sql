-- ============================================================
-- Migration 007 — document_layer column + partner_review / staging layers
-- HumanAIOS · humanaios-ui/operations · S-060626-01
-- Zone 2 ratification: Night · 2026-06-06
--   Z2-TRUST-A: partner_review layer (Mode AI, low-risk additive)
--   Z2-TRUST-B: staging layer (multi-provider, quarantined by default)
-- Pre-flight (IC-032 pattern — RUN THESE FIRST, before applying):
--   SELECT DISTINCT document_layer FROM acat_assessments_v1;
--   SELECT DISTINCT submission_purity FROM acat_assessments_v1;
-- ============================================================

-- STEP 1: Add document_layer column with behavioral_session as default
-- All existing rows are canonical corpus rows → behavioral_session
ALTER TABLE acat_assessments_v1
  ADD COLUMN IF NOT EXISTS document_layer text NOT NULL DEFAULT 'behavioral_session';

-- STEP 2: Add CHECK constraint for all valid layer values
-- behavioral_session : canonical corpus, included in all aggregate statistics
-- partner_review     : Mode AI / DeMarius sessions, excluded from aggregates
--                      until Night approves inclusion via explicit UPDATE
-- staging            : multi-provider submissions, quarantined by default
-- marshal_session    : reserved for future Option B upgrade (not active, Option A in force)
ALTER TABLE acat_assessments_v1
  ADD CONSTRAINT document_layer_valid
  CHECK (document_layer IN (
    'behavioral_session',
    'partner_review',
    'staging',
    'marshal_session'
  ));

-- STEP 3: Add provider_canonical column for multi-provider taxonomy
-- NULL for legacy rows; required for staging and partner_review rows
ALTER TABLE acat_assessments_v1
  ADD COLUMN IF NOT EXISTS provider_canonical text;

-- STEP 4: Add model_family column for Z2-CORPUS-TRUST-02 role-lock enforcement
-- NULL for legacy rows; required before role-lock check can fire
ALTER TABLE acat_assessments_v1
  ADD COLUMN IF NOT EXISTS model_family text;

-- STEP 5: Add CHECK constraint for role_method validity
-- Extends existing role_method column with new values for multi-provider
-- (Only add if role_method column exists — confirm with pre-flight)
-- NOTE: Check existing role_method values first:
--   SELECT DISTINCT role_method FROM acat_assessments_v1 WHERE role_method IS NOT NULL;

-- STEP 6: Create index on document_layer for aggregate query performance
-- All aggregate stats filter WHERE document_layer = 'behavioral_session'
CREATE INDEX IF NOT EXISTS idx_acat_document_layer
  ON acat_assessments_v1 (document_layer);

-- STEP 7: Grant permissions (IC-032 pattern — explicit grants required post-May-30)
GRANT SELECT, INSERT, UPDATE ON acat_assessments_v1 TO anon;
GRANT SELECT, INSERT, UPDATE ON acat_assessments_v1 TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON acat_assessments_v1 TO service_role;

-- ============================================================
-- VERIFICATION QUERIES (run after applying)
-- ============================================================
-- 1. Confirm all existing rows have behavioral_session:
--    SELECT document_layer, count(*) FROM acat_assessments_v1
--    GROUP BY document_layer;
--    Expected: behavioral_session | N (all existing rows)
--
-- 2. Confirm constraint exists:
--    SELECT conname, consrc FROM pg_constraint
--    WHERE conrelid = 'acat_assessments_v1'::regclass
--    AND conname = 'document_layer_valid';
--
-- 3. Confirm new columns visible:
--    SELECT column_name, data_type, column_default, is_nullable
--    FROM information_schema.columns
--    WHERE table_name = 'acat_assessments_v1'
--    AND column_name IN ('document_layer','provider_canonical','model_family')
--    ORDER BY ordinal_position;
-- ============================================================

-- ============================================================
-- ROLLBACK (if needed before any non-behavioral_session rows inserted)
-- ALTER TABLE acat_assessments_v1 DROP CONSTRAINT IF EXISTS document_layer_valid;
-- ALTER TABLE acat_assessments_v1 DROP COLUMN IF EXISTS document_layer;
-- ALTER TABLE acat_assessments_v1 DROP COLUMN IF EXISTS provider_canonical;
-- ALTER TABLE acat_assessments_v1 DROP COLUMN IF EXISTS model_family;
-- DROP INDEX IF EXISTS idx_acat_document_layer;
-- ============================================================
