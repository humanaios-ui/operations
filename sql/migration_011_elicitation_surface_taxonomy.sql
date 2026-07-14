-- migration_011_elicitation_surface_taxonomy.sql
-- HumanAIOS · Z1 DRAFT — proposed, not applied, not ratified for live run
-- Supersedes standalone migration_010_add_elicitation_surface.sql — folds it
-- into the full 8-axis elicitation_surface_vector taxonomy per
-- IC-CAND-ELICITATION-SURFACE-TAXONOMY-UNIFICATION.
--
-- ══════════════════════════════════════════════════════════════════════
-- STEP 0 — MANDATORY LIVE INSPECTION (IC-032 discipline, non-negotiable)
-- Run this BEFORE anything below. Do not apply any DDL against assumed
-- schema state. This is the exact class of failure IC-032 and IC-044
-- both register: a CHECK constraint written against an assumed enum
-- collided with a live 'agent_self_only' value nobody had queried for.
-- ══════════════════════════════════════════════════════════════════════

-- 0a. Confirm migration_010 was never actually applied (per
--     IC-CAND-GROUNDING-SCHEMA-UNPOPULATED — spec_fidelity_score/
--     spec_omission_rate/document_layer were all found empty; verify
--     p1_elicitation_surface is in the same state before assuming this
--     migration has a clean landing target).
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'acat_assessments_v1'
  AND column_name IN (
    'p1_elicitation_surface', 'role_method', 'submission_purity',
    'p1_sampling_params', 'p1_prompt_wording_variant'
  );

-- 0b. If p1_elicitation_surface already exists (migration_010 landed
--     after all, contradicting the prior finding), get its live distinct
--     values before touching it — same query shape as IC-032's own
--     prevention bullet.
SELECT DISTINCT p1_elicitation_surface, COUNT(*)
FROM acat_assessments_v1
WHERE p1_elicitation_surface IS NOT NULL
GROUP BY p1_elicitation_surface;

-- 0c. Live distinct values for the two fields this migration folds in
--     from existing hypotheses, so the new taxonomy's enums are built
--     from what actually exists, not assumed.
SELECT DISTINCT role_method, COUNT(*) FROM acat_assessments_v1
  WHERE role_method IS NOT NULL GROUP BY role_method;
SELECT DISTINCT submission_purity, COUNT(*) FROM acat_assessments_v1
  WHERE submission_purity IS NOT NULL GROUP BY submission_purity;

-- ══════════════════════════════════════════════════════════════════════
-- STOP HERE. Do not proceed past this line until Step 0's results are
-- reviewed against the enum values below. If live values don't match,
-- fix the enum in this file first — do not apply and patch after,
-- that is the exact IC-032/IC-044 recurrence this discipline exists
-- to prevent.
-- ══════════════════════════════════════════════════════════════════════

-- STEP 1 — new columns for the two previously-unnamed axes (7 and 8)

ALTER TABLE acat_assessments_v1
  ADD COLUMN IF NOT EXISTS p1_sampling_temperature NUMERIC(3,2),
  ADD COLUMN IF NOT EXISTS p1_sampling_top_p NUMERIC(3,2),
  ADD COLUMN IF NOT EXISTS p1_prompt_wording_variant TEXT
    DEFAULT 'adhoc_untracked';
  -- NOT NULL default of 'adhoc_untracked' rather than nullable per
  -- the maintained-headline lesson (IC-cand-maintained-headline-
  -- recurrence): an unpopulated field that silently defaults to NULL
  -- looks identical to "not yet asked" and "known to be unavailable."
  -- 'adhoc_untracked' is an explicit, queryable admission of the gap,
  -- not an absence.

-- STEP 2 — p1_elicitation_surface (folded from migration_010, not
-- reapplied standalone; enum values pending Step 0b confirmation)

ALTER TABLE acat_assessments_v1
  ADD COLUMN IF NOT EXISTS p1_elicitation_surface TEXT
    DEFAULT 'unknown';

-- STEP 3 — CHECK constraints. Built from Step 0's actual returned
-- values, NOT written blind. Placeholder enum shown here must be
-- reconciled against Step 0's real output before this runs live.

ALTER TABLE acat_assessments_v1
  ADD CONSTRAINT IF NOT EXISTS p1_elicitation_surface_check
  CHECK (p1_elicitation_surface IN (
    'prose_standard', 'compressed_lite', 'compressed_full',
    'compressed_ultra', 'templated_pipeline', 'unknown'
    -- ^ reconcile against Step 0b output before applying
  ));

ALTER TABLE acat_assessments_v1
  ADD CONSTRAINT IF NOT EXISTS p1_sampling_temperature_range_check
  CHECK (p1_sampling_temperature IS NULL
    OR (p1_sampling_temperature >= 0 AND p1_sampling_temperature <= 2));

ALTER TABLE acat_assessments_v1
  ADD CONSTRAINT IF NOT EXISTS p1_sampling_top_p_range_check
  CHECK (p1_sampling_top_p IS NULL
    OR (p1_sampling_top_p >= 0 AND p1_sampling_top_p <= 1));

-- STEP 4 — denormalized convenience view assembling all 8 axes,
-- per IC-CAND-ELICITATION-SURFACE-TAXONOMY-UNIFICATION's proposed
-- elicitation_surface_vector object. A VIEW, not a materialized
-- duplicate column set, so it can never drift out of sync with the
-- underlying columns it reads from.

CREATE OR REPLACE VIEW elicitation_surface_vector AS
SELECT
  id,
  p1_elicitation_surface   AS register,           -- Axis 1
  NULL::TEXT               AS platform,           -- Axis 2, TODO: no
                                                    -- live column exists
                                                    -- yet for H-PLATFORM-01/
                                                    -- H-XMODE-01; left NULL
                                                    -- intentionally, not
                                                    -- silently populated
                                                    -- with a guess
  role_method               AS submission_pathway, -- Axis 3
  submission_purity         AS administration,     -- Axis 4
  NULL::BOOLEAN             AS framing_disclosed,  -- Axis 5, same TODO
                                                    -- as platform — F-51/
                                                    -- H-MECH-01 is a
                                                    -- session-design
                                                    -- variable with no
                                                    -- corpus column yet
  p1_sampling_temperature   AS sampling_temperature, -- Axis 6 (new)
  p1_sampling_top_p         AS sampling_top_p,        -- Axis 6 (new)
  p1_prompt_wording_variant AS prompt_wording_variant -- Axis 7 (new)
FROM acat_assessments_v1;

-- Axes 2 and 5 are deliberately left as visible NULLs in the view
-- rather than silently omitted from the taxonomy or guessed at. This
-- migration closes Axes 6-7 and folds in Axis 1 cleanly; it does NOT
-- claim to close Axes 2 and 5 — those still have no corpus column and
-- remain open items for H-PLATFORM-01/H-XMODE-01/F-51/H-MECH-01's own
-- promotion gates to resolve, separately from this migration.
