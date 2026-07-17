-- migration_009_add_p3_grounding_source.sql
-- Prerequisite: migration_008 applied
-- Z2 authority: Z2-METRIC-01 (S-061126-04)

ALTER TABLE acat_assessments_v1
  ADD COLUMN IF NOT EXISTS p3_grounding_source TEXT
    CHECK (p3_grounding_source IN (
      'human_coobserver',
      'api_verification',
      'sensor_log',
      'replay_confirmed',
      'third_party_verifier'
    ));

ALTER TABLE acat_assessments_v1
  ADD COLUMN IF NOT EXISTS li_grounded NUMERIC(6,4)
    CHECK (li_grounded BETWEEN 0 AND 2);

ALTER TABLE acat_assessments_v1
  ADD COLUMN IF NOT EXISTS li_consistency_only BOOLEAN
    GENERATED ALWAYS AS (p3_grounding_source IS NULL) STORED;

-- Post-verification
SELECT COUNT(*) FROM acat_assessments_v1
  WHERE li_consistency_only = TRUE;
-- Expected: N=95 (all existing rows, null p3_grounding_source)

COMMENT ON COLUMN acat_assessments_v1.p3_grounding_source IS
  'Z2-METRIC-01: null flags LI as CONSISTENCY_ONLY per H-P3G-01';
COMMENT ON COLUMN acat_assessments_v1.li_grounded IS
  'LI_grounded = P3_grounded/P1 · requires p3_grounding_source';
COMMENT ON COLUMN acat_assessments_v1.li_consistency_only IS
  'Generated: true when p3_grounding_source is null';
