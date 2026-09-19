-- file: acat/db/migrations/005_acat_ingest_columns.sql
-- Adds columns required by _build_phase1_row() in ingest_service.py.
-- Pre-migration checklist completed (IC-032 gate):
--   All columns below are new additions. No existing column values violated.
--   Additive only. Re-runnable.

ALTER TABLE public.acat_assessments_v1
  ADD COLUMN IF NOT EXISTS session_id               text,
  ADD COLUMN IF NOT EXISTS agent_name_canonical     text,
  ADD COLUMN IF NOT EXISTS p1_timestamp             timestamptz,
  ADD COLUMN IF NOT EXISTS session_start_timestamp  timestamptz,
  ADD COLUMN IF NOT EXISTS first_user_message_timestamp timestamptz,
  ADD COLUMN IF NOT EXISTS contamination_status     text,
  ADD COLUMN IF NOT EXISTS quality_flags            jsonb,
  ADD COLUMN IF NOT EXISTS normalization_version    text,
  ADD COLUMN IF NOT EXISTS dedupe_key               text,
  ADD COLUMN IF NOT EXISTS raw_payload              jsonb;

COMMENT ON COLUMN public.acat_assessments_v1.session_id IS
  'HumanAIOS session identifier (e.g. S-052926-03). Links all assessments in one session.';
COMMENT ON COLUMN public.acat_assessments_v1.agent_name_canonical IS
  'Normalized lowercase agent name via agent_aliases.yml lookup.';
COMMENT ON COLUMN public.acat_assessments_v1.p1_timestamp IS
  'UTC timestamp when Phase 1 self-assessment was submitted.';
COMMENT ON COLUMN public.acat_assessments_v1.session_start_timestamp IS
  'UTC timestamp when the session started (from MCP wrapper).';
COMMENT ON COLUMN public.acat_assessments_v1.first_user_message_timestamp IS
  'UTC timestamp of first user message. Used with p1_timestamp to compute contamination delta.';
COMMENT ON COLUMN public.acat_assessments_v1.contamination_status IS
  'clean | contaminated | unknown. Derived from contamination_delta_seconds.';
COMMENT ON COLUMN public.acat_assessments_v1.quality_flags IS
  'Array of flag strings derived at normalize time (e.g. CONTAMINATION).';
COMMENT ON COLUMN public.acat_assessments_v1.normalization_version IS
  'Version of normalize_service.py used at intake time.';
COMMENT ON COLUMN public.acat_assessments_v1.dedupe_key IS
  'Composite key: session_id:phase:rater_id. Used for deduplication.';
COMMENT ON COLUMN public.acat_assessments_v1.raw_payload IS
  'Full original intake payload as submitted, before normalization.';
