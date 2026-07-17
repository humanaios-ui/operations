-- migration_011_participation_schema.sql
-- HumanAIOS · S-061126-01 · 2026-06-11
-- Ratified: Z2-CORPUS-01 (materials_encounter submission purity) ·
--           Z2-CORPUS-02 (P_ENCOUNTER perturbation type)
--           Night · 2026-06-11 · S-061126-01
--
-- PRE-FLIGHT REQUIRED (IC-032 lesson — constraint before data inspection):
--   SELECT DISTINCT submission_purity FROM acat_assessments_v1;
--   SELECT DISTINCT perturbation_type FROM acat_assessments_v1;
--   SELECT column_name FROM information_schema.columns
--     WHERE table_name = 'acat_assessments_v1'
--     AND column_name IN ('encounter_surface', 'acknowledged_elicitation');
--
-- Expected pre-flight results:
--   submission_purity values: two_stage_verified | single_shot_legacy | external_only |
--                             agent_self_only | p1_only_formal | self_administered
--   perturbation_type: may be null or have existing values — verify before applying constraint
--   encounter_surface: should NOT exist yet (new column)
--   acknowledged_elicitation: should NOT exist yet (new column)
--
-- Apply only after pre-flight confirms no collision.
-- Postgres 14 deprecation: July 1, 2026 — apply before that date.

BEGIN;

-- 1. Add encounter_surface column (nullable TEXT with CHECK constraint)
--    Captures where the participating human/AI encountered ACAT materials
ALTER TABLE acat_assessments_v1
  ADD COLUMN IF NOT EXISTS encounter_surface TEXT
  CHECK (encounter_surface IN ('readme', 'substack', 'website', 'research_brief', 'other'));

-- 2. Add acknowledged_elicitation boolean
--    TRUE = substrate was explicitly told it is reading an assessment instrument
--    NULL = not applicable (non-P_ENCOUNTER sessions)
ALTER TABLE acat_assessments_v1
  ADD COLUMN IF NOT EXISTS acknowledged_elicitation BOOLEAN DEFAULT NULL;

-- 3. Extend submission_purity CHECK constraint to include materials_encounter
--    IMPORTANT: ALTER TABLE ... DROP CONSTRAINT + ADD CONSTRAINT pattern
--    because Postgres does not support ALTER CONSTRAINT for CHECK constraints.
--    Step A: identify current constraint name
--    Run this query first:
--      SELECT conname FROM pg_constraint
--        WHERE conrelid = 'acat_assessments_v1'::regclass
--        AND contype = 'c'
--        AND conname LIKE '%submission_purity%';
--
--    Then replace 'acat_assessments_v1_submission_purity_check' below
--    with the actual constraint name if different.

ALTER TABLE acat_assessments_v1
  DROP CONSTRAINT IF EXISTS acat_assessments_v1_submission_purity_check;

ALTER TABLE acat_assessments_v1
  ADD CONSTRAINT acat_assessments_v1_submission_purity_check
  CHECK (submission_purity IN (
    'two_stage_verified',
    'single_shot_legacy',
    'external_only',
    'agent_self_only',
    'p1_only_formal',
    'self_administered',
    'materials_encounter'   -- Z2-CORPUS-01 · 2026-06-11
  ));

-- 4. Add perturbation_type column if it does not exist
--    (check pre-flight — it may already exist from prior migrations)
ALTER TABLE acat_assessments_v1
  ADD COLUMN IF NOT EXISTS perturbation_type TEXT;

-- 5. Add P_ENCOUNTER to perturbation_type CHECK constraint
--    Run pre-flight to check if a constraint already exists on this column.
--    If no constraint exists, add fresh:

ALTER TABLE acat_assessments_v1
  DROP CONSTRAINT IF EXISTS acat_assessments_v1_perturbation_type_check;

ALTER TABLE acat_assessments_v1
  ADD CONSTRAINT acat_assessments_v1_perturbation_type_check
  CHECK (perturbation_type IN (
    'P1',              -- standard naive elicitation (no perturbation label)
    'P_ENCOUNTER',     -- acknowledged elicitation · Z2-CORPUS-02 · 2026-06-11
    'P_ADVERSARIAL',   -- adversarial framing condition
    'P_PRAISE',        -- praise/dependency condition
    'P_MORAL',         -- moral complexity condition
    'P_META'           -- meta/gaming condition
  ));

-- 6. Required GRANTs (Supabase Data API change May 30, 2026)
--    Existing table — GRANTs already in place for core columns.
--    New columns inherit table-level GRANTs in Postgres, but explicit
--    confirmation is good practice:

GRANT SELECT, INSERT, UPDATE ON acat_assessments_v1 TO anon, authenticated, service_role;

-- 7. Add index on encounter_surface for corpus filtering
CREATE INDEX IF NOT EXISTS idx_acat_encounter_surface
  ON acat_assessments_v1 (encounter_surface)
  WHERE encounter_surface IS NOT NULL;

-- 8. Add index on perturbation_type for corpus stratification analysis
CREATE INDEX IF NOT EXISTS idx_acat_perturbation_type
  ON acat_assessments_v1 (perturbation_type)
  WHERE perturbation_type IS NOT NULL;

COMMIT;

-- POST-MIGRATION VERIFICATION:
--   SELECT column_name, data_type
--     FROM information_schema.columns
--     WHERE table_name = 'acat_assessments_v1'
--     AND column_name IN ('encounter_surface', 'acknowledged_elicitation', 'perturbation_type');
--
--   SELECT conname, consrc FROM pg_constraint
--     WHERE conrelid = 'acat_assessments_v1'::regclass AND contype = 'c';
--
-- Expected: 3 new columns visible, 2 updated CHECK constraints present.
-- Register as migration_011 in supabase_migrations.schema_migrations.
