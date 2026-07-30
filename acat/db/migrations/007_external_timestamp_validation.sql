-- file: acat/db/migrations/007_external_timestamp_validation.sql
-- Adds timestamp fraud detection column required by ingest_service.py (S-071726-01).
-- Pre-migration checklist (IC-032 gate):
--   All columns below are new additions. No existing column values violated.
--   Additive only. Re-runnable.

ALTER TABLE public.acat_assessments_v1
  ADD COLUMN IF NOT EXISTS received_at timestamptz,
  ADD COLUMN IF NOT EXISTS external_timestamp_validation jsonb;

COMMENT ON COLUMN public.acat_assessments_v1.received_at IS
  'Server timestamp when intake payload was received (fraud detection reference).';

COMMENT ON COLUMN public.acat_assessments_v1.external_timestamp_validation IS
  'Timestamp validation state: {status: "pass"|"fail"|"unknown", details: {...}}. Fraud detection for S-071726-01.';
