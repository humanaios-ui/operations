-- migration_010_add_elicitation_surface.sql
-- H-ELICIT-01 promotion pathway (REGISTERED.md S-061426) + F-52
-- (pipeline-anchoring-deterministic-self-report, S-061726-01)
-- Sequenced after migration_008 (carried, Z3 queue) and migration_009
-- (p3_grounding_source / li_grounded, drafted).
-- Status: ratified Night · S-061726-01 · ready for Z3 review and application.

-- ── Step 0 — MANDATORY, do not skip (IC-032 precedent) ──────────────────
-- IC-032 occurred because a constraint was applied without first querying
-- live data for existing values outside the assumed enum. Run this first
-- and inspect the result before applying the ALTER below:
--
--   SELECT DISTINCT submission_version, role_method, behavioral_flag_final
--   FROM acat_assessments_v1;
--
-- Confirm: (a) role_method values present match expectations (standard /
-- automated / ai-self-report / unknown), (b) no existing free-text value
-- would violate the CHECK constraint below, (c) column names match —
-- 'role_method' and 'behavioral_flag_final' are inferred from the Operator
-- Field Guide and ACAT corpus v2 CSV, not confirmed against live Supabase
-- schema. Verify before applying.

ALTER TABLE acat_assessments_v1
  ADD COLUMN IF NOT EXISTS p1_elicitation_surface TEXT;

ALTER TABLE acat_assessments_v1
  ADD CONSTRAINT chk_p1_elicitation_surface
  CHECK (
    p1_elicitation_surface IS NULL
    OR p1_elicitation_surface IN (
      'prose_standard',
      'compressed_lite',
      'compressed_full',
      'compressed_ultra',
      'templated_pipeline',   -- NEW: F-52, role_method='standard' ANCHORING artifact
      'unknown'
    )
  );

-- ── Backfill (Z3 action, separate from this DDL — do not run blind) ─────
-- WHERE role_method = 'standard' AND behavioral_flag_final ILIKE '%ANCHORING%'
--   → p1_elicitation_surface = 'templated_pipeline'
-- WHERE submission_version = 'legacy' (manual web-paste era, pre-v5.2)
--   → p1_elicitation_surface = 'prose_standard'
-- All other historical rows → 'unknown' until provenance is reconstructed
-- from submission_version + user_agent fields.
