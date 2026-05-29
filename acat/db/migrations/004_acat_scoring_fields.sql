ALTER TABLE public.acat_assessments_v1
  ADD COLUMN IF NOT EXISTS score_status text,
  ADD COLUMN IF NOT EXISTS scorer_version text,
  ADD COLUMN IF NOT EXISTS scorer_validated boolean DEFAULT false,
  ADD COLUMN IF NOT EXISTS sag numeric,
  ADD COLUMN IF NOT EXISTS him numeric,
  ADD COLUMN IF NOT EXISTS machine_scores_json jsonb,
  ADD COLUMN IF NOT EXISTS human_scores_json jsonb,
  ADD COLUMN IF NOT EXISTS report_status text;
