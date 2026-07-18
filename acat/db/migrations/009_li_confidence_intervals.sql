-- file: acat/db/migrations/009_li_confidence_intervals.sql
-- Adds calibration confidence intervals to replace single-point learning_index (Goal 3: Multi-Agent Normative Drift Detection).
--
-- Current state: learning_index is a single point estimate (e.g., 0.8943).
-- Problem: Single points can't measure uncertainty expansion under social pressure (core normative drift signal).
--
-- Solution: Replace point estimate with range (low, high) that captures:
--   * Conservative estimate (lower bound confidence)
--   * Optimistic estimate (upper bound confidence)
--   * Whether LI is grounded against external validation
--   * Whether LI is consistency-only (Core 6) vs. full (all 12 dimensions)
--
-- Normative drift measurement: drift_signal = (P3_low - P1_low) / P1_high
-- When social pressure increases, P3_low drops → drift_signal becomes more negative
--
-- Pre-migration checklist:
--   * Additive and idempotent only.
--   * New columns; existing learning_index not altered or dropped.
--   * Re-runnable.

ALTER TABLE public.acat_assessments_v1
  ADD COLUMN IF NOT EXISTS li_low numeric,
  ADD COLUMN IF NOT EXISTS li_high numeric,
  ADD COLUMN IF NOT EXISTS li_grounded boolean DEFAULT false,
  ADD COLUMN IF NOT EXISTS li_consistency_only boolean DEFAULT true;

COMMENT ON COLUMN public.acat_assessments_v1.li_low IS
  'Conservative estimate of Learning Index (lower bound). Range 0.0-1.0. Used for normative drift detection: how much did P3 low estimate degrade vs. P1 low estimate?';

COMMENT ON COLUMN public.acat_assessments_v1.li_high IS
  'Optimistic estimate of Learning Index (upper bound). Range 0.0-1.0. Provides uncertainty range: calibration accuracy could be anywhere between li_low and li_high.';

COMMENT ON COLUMN public.acat_assessments_v1.li_grounded IS
  'Whether Learning Index is grounded against external validation (behavioral telemetry, user ratings, field deployment results). true = LI backed by observable data; false = self-report only.';

COMMENT ON COLUMN public.acat_assessments_v1.li_consistency_only IS
  'Whether Learning Index covers Core 6 dimensions only (true) or all 12 dimensions (false). true = backward-compatible with v1.0 corpus (N=629); false = new full-dimensional coverage.';

-- Add check constraints for valid ranges
ALTER TABLE public.acat_assessments_v1
  ADD CONSTRAINT li_ranges_valid
    CHECK (
      (li_low IS NULL AND li_high IS NULL) OR
      (li_low IS NOT NULL AND li_high IS NOT NULL AND
       li_low >= 0.0 AND li_low <= 1.0 AND
       li_high >= 0.0 AND li_high <= 1.0 AND
       li_low <= li_high)  -- low estimate must not exceed high estimate
    );

-- Backward compatibility: if learning_index exists and new columns are empty,
-- seed new columns from legacy point estimate (during transition period)
-- This allows Phase 1/3 submissions to populate li_low/li_high from existing learning_index
COMMENT ON TABLE public.acat_assessments_v1 IS
  'ACAT Assessment Results (v5.3+). Phase 1/3 calibration data with 12-dimension scoring (Core 6 + Extended 6), Learning Index confidence intervals (li_low/li_high), normative drift tracking (p3_grounding_source, elicitation_surface), and fraud detection (external_timestamp_validation).';
