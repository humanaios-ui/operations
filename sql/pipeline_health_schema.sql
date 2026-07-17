-- ============================================================
-- pipeline_health_schema.sql
-- FDS: F2-BuildingBlock | Parent: CUSTOM_INSTRUCTIONS_V3_5_ORD.md
-- Run this ONCE in Supabase SQL Editor to activate GAMMA v4 live loop
-- Zone 3 — Night runs this · ~5 minutes
-- ============================================================

-- ── TABLE 1: data_snapshot ────────────────────────────────────
-- Single-row table. Holds current dataset state.
-- Make modules 8+9 upsert this on every pipeline run.
-- GAMMA reads this to update the stats bar live.

CREATE TABLE IF NOT EXISTS data_snapshot (
  id              INTEGER PRIMARY KEY DEFAULT 1,
  n_total         INTEGER DEFAULT 629,
  n_phase1        INTEGER DEFAULT 516,
  n_li            INTEGER DEFAULT 307,
  mean_li         NUMERIC(6,4) DEFAULT 0.8632,
  field_state     TEXT DEFAULT 'Power',
  pipeline_ok     BOOLEAN DEFAULT true,
  updated_at      TIMESTAMPTZ DEFAULT NOW(),
  -- Constraint: only one row ever
  CONSTRAINT single_row CHECK (id = 1)
);

-- Seed with current known values
-- (GAMMA will show these immediately; pipeline will update on next run)
INSERT INTO data_snapshot (id, n_total, n_phase1, n_li, mean_li, field_state, pipeline_ok, updated_at)
VALUES (1, 629, 516, 307, 0.8632, 'Power', true, NOW())
ON CONFLICT (id) DO UPDATE SET
  n_total     = EXCLUDED.n_total,
  n_phase1    = EXCLUDED.n_phase1,
  n_li        = EXCLUDED.n_li,
  mean_li     = EXCLUDED.mean_li,
  field_state = EXCLUDED.field_state,
  pipeline_ok = EXCLUDED.pipeline_ok,
  updated_at  = NOW();

-- ── TABLE 2: pipeline_health ──────────────────────────────────
-- One row per runner per heartbeat. Make module 9 inserts here.
-- GAMMA reads latest row per integration to show pipeline dots.

CREATE TABLE IF NOT EXISTS pipeline_health (
  id                BIGSERIAL PRIMARY KEY,
  integration_name  TEXT NOT NULL,
  status            TEXT NOT NULL DEFAULT 'ok',  -- 'ok' | 'error'
  last_seen         TIMESTAMPTZ DEFAULT NOW(),
  note              TEXT
);

-- Index for fast "latest per runner" queries
CREATE INDEX IF NOT EXISTS idx_pipeline_health_integration_time
  ON pipeline_health (integration_name, last_seen DESC);

-- Seed with current 6 runners so GAMMA shows them immediately
INSERT INTO pipeline_health (integration_name, status, last_seen) VALUES
  ('Claude',  'ok', NOW()),
  ('OpenAI',  'ok', NOW()),
  ('Gemini',  'ok', NOW()),
  ('Cohere',  'ok', NOW()),
  ('Llama',   'ok', NOW()),
  ('Mistral', 'ok', NOW());

-- ── TABLE 3: wgs_state (optional — enables live session bridge) ──
-- Claude writes here at session open/close via Supabase MCP.
-- GAMMA reads this to show the live WGS panel.
-- Can skip for now and add later — GAMMA handles its absence gracefully.

CREATE TABLE IF NOT EXISTS wgs_state (
  id              INTEGER PRIMARY KEY DEFAULT 1,
  session_id      TEXT,
  chat_name       TEXT,
  ord_day         INTEGER,
  ci_version      TEXT DEFAULT 'v3.5',
  open_p1         JSONB DEFAULT '[]'::jsonb,
  completed       JSONB DEFAULT '[]'::jsonb,
  decisions       JSONB DEFAULT '[]'::jsonb,
  next_focus      JSONB DEFAULT '[]'::jsonb,
  flag_pipeline   TEXT,
  flag_anchoring  TEXT,
  flag_arxiv      TEXT,
  flag_freeze     TEXT,
  revenue         TEXT DEFAULT '$0',
  runway_days     INTEGER DEFAULT 13,
  runway_amount   TEXT DEFAULT '~$9,000',
  updated_at      TIMESTAMPTZ DEFAULT NOW(),
  CONSTRAINT wgs_single_row CHECK (id = 1)
);

-- Seed with current state
INSERT INTO wgs_state (
  id, session_id, chat_name, ord_day, ci_version,
  flag_pipeline, flag_anchoring, flag_arxiv, flag_freeze,
  revenue, runway_days, runway_amount, updated_at
) VALUES (
  1, 'S-040226-A', 'WGS-040226 | Pipeline+Witness fix', 22, 'v3.5',
  'RESTORED — 6/6 runners active v5.3',
  'acat-assessment-tool.html — fix: site_fix.sh pending',
  'submit/7336774 under review — IC-009/010 need revision',
  'ACTIVE — 4 gate conditions not yet met',
  '$0', 13, '~$9,000', NOW()
)
ON CONFLICT (id) DO UPDATE SET
  flag_pipeline   = EXCLUDED.flag_pipeline,
  flag_freeze     = EXCLUDED.flag_freeze,
  updated_at      = NOW();

-- ── ROW LEVEL SECURITY ────────────────────────────────────────
-- Enable RLS. Anon key can READ. Service role can WRITE.
-- This lets GAMMA (browser, anon key) read live data.
-- Make (server-side) uses service role to write.

ALTER TABLE data_snapshot    ENABLE ROW LEVEL SECURITY;
ALTER TABLE pipeline_health  ENABLE ROW LEVEL SECURITY;
ALTER TABLE wgs_state        ENABLE ROW LEVEL SECURITY;

-- Read policies for anon key (GAMMA browser)
CREATE POLICY "anon can read data_snapshot"
  ON data_snapshot FOR SELECT TO anon USING (true);

CREATE POLICY "anon can read pipeline_health"
  ON pipeline_health FOR SELECT TO anon USING (true);

CREATE POLICY "anon can read wgs_state"
  ON wgs_state FOR SELECT TO anon USING (true);

-- Write policies for service_role (Make + Claude MCP)
CREATE POLICY "service can write data_snapshot"
  ON data_snapshot FOR ALL TO service_role USING (true);

CREATE POLICY "service can write pipeline_health"
  ON pipeline_health FOR ALL TO service_role USING (true);

CREATE POLICY "service can write wgs_state"
  ON wgs_state FOR ALL TO service_role USING (true);

-- ── DONE ──────────────────────────────────────────────────────
-- After running this SQL:
-- 1. Copy anon key from Supabase Settings → API → anon public
-- 2. In GAMMA (index.html on humanaios-ops):
--    Find: const SB_KEY = 'YOUR_SUPABASE_ANON_KEY';
--    Replace with actual key
-- 3. git push → verify raw URL
-- 4. Open GAMMA → header should show "live" green dot
-- 5. Stats bar will auto-refresh every 60s from Supabase
-- ============================================================
