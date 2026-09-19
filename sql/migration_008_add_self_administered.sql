-- migration_008_add_self_administered
-- Z2 ratification: Night · 2026-06-10 · S-061026-01
-- Adds 'self_administered' to submission_purity CHECK constraint on acat_assessments_v1
-- 
-- PRE-FLIGHT (run this first, verify output before applying):
-- SELECT DISTINCT submission_purity FROM public.acat_assessments_v1 WHERE submission_purity IS NOT NULL;
-- Expected: two_stage_verified | single_shot_legacy | external_only | agent_self_only | p1_only_formal
-- If any unexpected value appears: STOP and route to Z2 before proceeding.
--
-- Quarantine rule: aggregate statistics queries MUST exclude submission_purity = 'self_administered'
-- same pattern as document_layer = 'staging' and document_layer = 'partner_review' exclusions.

BEGIN;

ALTER TABLE public.acat_assessments_v1
  DROP CONSTRAINT IF EXISTS acat_assessments_v1_submission_purity_check;

ALTER TABLE public.acat_assessments_v1
  ADD CONSTRAINT acat_assessments_v1_submission_purity_check
  CHECK (submission_purity IN (
    'two_stage_verified',
    'single_shot_legacy',
    'external_only',
    'agent_self_only',
    'p1_only_formal',
    'self_administered'
  ));

COMMIT;

-- POST-MIGRATION VERIFICATION (run immediately after):
-- SELECT conname, pg_get_constraintdef(oid)
-- FROM pg_constraint
-- WHERE conrelid = 'public.acat_assessments_v1'::regclass
-- AND conname = 'acat_assessments_v1_submission_purity_check';
-- Expected output must contain 'self_administered' in the enum.
