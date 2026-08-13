-- file: acat/db/migrations/008_p3_grounding_source.sql
-- Adds lane/context tracking for Phase 3 assessments (Goal 3: Schema Design for Multi-Agent Normative Drift Detection).
--
-- Purpose: Phase 3 can run in different social contexts (isolated vs. group pressure).
-- Same agent produces different calibration scores depending on context.
-- This column captures which lane/context Phase 3 was conducted in, enabling normative drift measurement.
--
-- Pre-migration checklist:
--   * Additive and idempotent only.
--   * All new columns; no existing values altered.
--   * Re-runnable.

ALTER TABLE public.acat_assessments_v1
  ADD COLUMN IF NOT EXISTS p3_grounding_source text;

COMMENT ON COLUMN public.acat_assessments_v1.p3_grounding_source IS
  'Lane/context where Phase 3 was conducted. Values: baseline_isolated, emergence_world_mid_simulation, sovereign_ai_governance, multimodal_conflict_exposure, robotics_field_deployment, phone_app_user_feedback, etc. Enables normative drift measurement by tracking same assessment across different social pressures.';

-- Add check constraint for enum-like behavior (values must be recognized)
ALTER TABLE public.acat_assessments_v1
  ADD CONSTRAINT p3_grounding_source_valid
    CHECK (p3_grounding_source IS NULL OR p3_grounding_source IN (
      'baseline_isolated',
      'baseline_phone_app',
      'emergence_world_mid_simulation',
      'emergence_world_end_simulation',
      'sovereign_ai_governance_scenario',
      'multimodal_conflict_exposure',
      'robotics_field_deployment',
      'quantum_hybrid_mixed_substrate',
      'group_norm_adoption_lane1',
      'governance_pressure_lane3',
      'workflow_sop_pressure_lane4',
      'reputation_pressure_lane5'
    ));
