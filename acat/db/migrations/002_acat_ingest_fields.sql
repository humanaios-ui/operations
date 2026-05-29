ALTER TABLE public.acat_assessments_v1
  ADD COLUMN IF NOT EXISTS submission_purity text,
  ADD COLUMN IF NOT EXISTS contamination_delta_seconds integer,
  ADD COLUMN IF NOT EXISTS contamination_status text,
  ADD COLUMN IF NOT EXISTS rater_id text,
  ADD COLUMN IF NOT EXISTS assessment_id text;

COMMENT ON COLUMN public.acat_assessments_v1.submission_purity IS
  'Purity classification: clean | anchored | contaminated | unknown';
COMMENT ON COLUMN public.acat_assessments_v1.contamination_delta_seconds IS
  'Seconds between p1_timestamp and first_user_message_timestamp. NULL if either missing.';
COMMENT ON COLUMN public.acat_assessments_v1.contamination_status IS
  'clean (<=60s) | contaminated (>60s) | unknown (timestamps absent)';
COMMENT ON COLUMN public.acat_assessments_v1.rater_id IS
  'Identifier for the human rater or automated pipeline that submitted this row.';
COMMENT ON COLUMN public.acat_assessments_v1.assessment_id IS
  'UUID assigned at intake. Stable identifier for this specific assessment record.';
