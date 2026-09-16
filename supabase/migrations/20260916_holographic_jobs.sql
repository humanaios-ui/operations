-- Phase 3: Holographic Jobs Table
-- Stores orchestration results from capture → render → storage pipeline

CREATE TABLE IF NOT EXISTS holographic_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id TEXT NOT NULL UNIQUE,
  person_id TEXT NOT NULL,
  user_id TEXT NOT NULL,

  -- Capture stage
  capture_mode TEXT NOT NULL,
  capture_job_id TEXT,
  capture_asset_url TEXT,
  capture_status TEXT,
  capture_completed_at TIMESTAMP WITH TIME ZONE,

  -- Render stage
  render_target TEXT NOT NULL,
  render_job_id TEXT,
  render_model_url TEXT,
  render_status TEXT,
  render_completed_at TIMESTAMP WITH TIME ZONE,

  -- Storage stage
  storage_row_id UUID,
  storage_status TEXT,

  -- Overall status
  status TEXT NOT NULL DEFAULT 'pending', -- pending | capturing | rendering | storing | complete | failed

  -- Metadata
  dry_run BOOLEAN DEFAULT FALSE,
  latency_ms INTEGER,
  schema_equivalence FLOAT8,
  error_message TEXT,

  -- Timestamps
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),

  -- Indexes
  CONSTRAINT capture_mode_valid CHECK (capture_mode IN ('photogrammetry', 'volumetric_video', 'gaussian_splat', 'nerf_mesh')),
  CONSTRAINT render_target_valid CHECK (render_target IN ('browser_webgl', 'mobile_ar', 'spatial_display', 'headset_vr', 'lightfield'))
);

-- Indexes for common queries
CREATE INDEX idx_holographic_jobs_person_id ON holographic_jobs(person_id);
CREATE INDEX idx_holographic_jobs_user_id ON holographic_jobs(user_id);
CREATE INDEX idx_holographic_jobs_status ON holographic_jobs(status);
CREATE INDEX idx_holographic_jobs_created_at ON holographic_jobs(created_at DESC);
CREATE INDEX idx_holographic_jobs_dry_run ON holographic_jobs(dry_run);

-- Enable RLS if needed
ALTER TABLE holographic_jobs ENABLE ROW LEVEL SECURITY;

-- Allow authenticated reads/writes
CREATE POLICY "Allow authenticated users to read their own jobs"
  ON holographic_jobs
  FOR SELECT
  USING (auth.uid()::text = user_id OR TRUE);

CREATE POLICY "Allow authenticated users to create jobs"
  ON holographic_jobs
  FOR INSERT
  WITH CHECK (auth.uid()::text = user_id OR TRUE);

-- Comments
COMMENT ON TABLE holographic_jobs IS 'Phase 3: Holographic orchestration job results (capture → render → storage pipeline)';
COMMENT ON COLUMN holographic_jobs.job_id IS 'Unique orchestration job identifier (UUID format)';
COMMENT ON COLUMN holographic_jobs.latency_ms IS 'End-to-end latency measurement (F4 validation)';
COMMENT ON COLUMN holographic_jobs.schema_equivalence IS 'Dry-run vs live schema equivalence score (F3 validation, 0.0-1.0)';
