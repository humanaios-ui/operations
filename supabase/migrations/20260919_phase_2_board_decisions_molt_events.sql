/**
 * Phase 2: Board Decisions & Molt Events Ingestion Schema
 *
 * This migration extends Phase 1 governance rulings with:
 * 1. board_decisions: Capture Z2 board meeting outcomes
 * 2. molt_events: Track constant molt cycles with prediction accuracy
 *
 * Both tables support autonomous data collection from GitHub + relay service
 * Date: 2026-09-19
 */

-- ============================================================================
-- BOARD_DECISIONS TABLE
-- ============================================================================
-- Captures Z2 board meeting decisions, agenda items, outcomes
-- Links to governance_rulings when decisions have ruling IDs

CREATE TABLE IF NOT EXISTS public.board_decisions (
  id BIGSERIAL PRIMARY KEY,
  board_id TEXT NOT NULL UNIQUE, -- e.g., "board-20260919-z2-001"
  board_name TEXT NOT NULL DEFAULT 'Z2 Board', -- "Z2 Board", "Advisory Board", etc.
  ruling_id TEXT, -- FK to governance_rulings if this decision has a ruling (nullable)
  meeting_date TIMESTAMP WITH TIME ZONE NOT NULL,

  -- Meeting metadata
  participants TEXT[] NOT NULL DEFAULT '{}', -- ["Night", "Claude", "Carly"]
  agenda_items JSONB, -- [{title: "...", status: "...", duration_min: 30}, ...]

  -- Decisions captured from meeting
  decisions_made JSONB NOT NULL DEFAULT '{}', -- {decision_key: {type, rationale, evidence, ruling_id}, ...}
  decisions_summary TEXT, -- One-paragraph summary of outcomes

  -- Board recordings & minutes
  recording_url TEXT, -- Link to meeting recording (if available)
  recording_provider TEXT, -- "zoom", "google_meet", "youtube", etc.
  minutes_url TEXT, -- Link to meeting minutes doc
  transcript_url TEXT, -- Link to transcript (if auto-generated)

  -- Decision state
  status TEXT NOT NULL DEFAULT 'PENDING_RATIFICATION',
    CHECK (status IN ('OPEN', 'CLOSED', 'PENDING_RATIFICATION', 'RATIFIED', 'SUPERSEDED')),

  -- Ratification
  ratified_at TIMESTAMP WITH TIME ZONE,
  ratified_by TEXT, -- Name or email of Z2 who ratified
  ratification_hash TEXT, -- SHA256 of decision + timestamp + signer
  ratification_notes TEXT,

  -- Governance linkage
  pr_number INTEGER, -- If decisions merged via PR
  pr_url TEXT,
  commit_sha TEXT, -- If decisions captured from commit
  commit_url TEXT,

  -- Category inference (same as governance_rulings)
  category TEXT DEFAULT 'board',
    CHECK (category IN ('schema', 'process', 'board', 'policy', 'artifact')),

  -- Related issue/epic
  epic_refs TEXT[], -- Issue links: ["#412", "#413"]

  -- Metadata
  board_section TEXT, -- "Tier-1 Decisions", "Process", "Resource Allocation", etc.
  impact_score INTEGER, -- 1-10 scale (optional)
  evidence_level TEXT DEFAULT 'CANDIDATE',
    CHECK (evidence_level IN ('CANDIDATE', 'REGISTERED', 'CONFIRMED', 'SUPERSEDED')),

  -- Tracking
  ingestion_source TEXT NOT NULL DEFAULT 'relay_webhook',
    CHECK (ingestion_source IN ('relay_webhook', 'github_webhook', 'manual', 'batch_import')),

  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_board_decisions_board_id ON public.board_decisions(board_id);
CREATE INDEX idx_board_decisions_ruling_id ON public.board_decisions(ruling_id);
CREATE INDEX idx_board_decisions_meeting_date ON public.board_decisions(meeting_date DESC);
CREATE INDEX idx_board_decisions_status ON public.board_decisions(status);
CREATE INDEX idx_board_decisions_category ON public.board_decisions(category);
CREATE INDEX idx_board_decisions_ratified_at ON public.board_decisions(ratified_at DESC);
CREATE INDEX idx_board_decisions_created_at ON public.board_decisions(created_at DESC);

-- ============================================================================
-- MOLT_EVENTS TABLE
-- ============================================================================
-- Tracks constant molt cycles: prediction, measurement, accuracy, revert

CREATE TABLE IF NOT EXISTS public.molt_events (
  id BIGSERIAL PRIMARY KEY,
  molt_id TEXT NOT NULL UNIQUE, -- e.g., "molt-20260919-RESOURCE_UNITS.yaml-001"
  constant_id TEXT NOT NULL, -- Which constant is being molted (e.g., "RESOURCE_UNITS.yaml")
  constant_path TEXT, -- File path for reference

  -- Molt metadata
  molt_type TEXT NOT NULL DEFAULT 'parameter_sweep',
    CHECK (molt_type IN ('parameter_sweep', 'ab_test', 'threshold_shift', 'rule_change', 'config_update')),

  -- Prediction (before molt)
  prediction_id TEXT, -- Link to prediction in Q-MOLT-... candidate
  prediction TEXT NOT NULL, -- The predicted change (e.g., "increase from 80 to 100 units/cycle")
  prediction_confidence DECIMAL(3, 2) NOT NULL DEFAULT 0.50, -- 0.0-1.0
  prediction_reasoning TEXT, -- Why this change was proposed
  falsifier TEXT, -- The falsifier: "if X then revert" (required per governance)

  -- Molt window
  window_start TIMESTAMP WITH TIME ZONE NOT NULL,
  window_end TIMESTAMP WITH TIME ZONE NOT NULL,
  window_duration_days INTEGER GENERATED ALWAYS AS (EXTRACT(DAY FROM (window_end - window_start))) STORED,

  -- Measurement (after window closes)
  measurement_date TIMESTAMP WITH TIME ZONE, -- When measurement was taken
  measurement_value TEXT, -- What was measured (e.g., "actual value: 95 units/cycle")
  measurement_notes TEXT,

  -- Accuracy assessment
  actual_outcome TEXT, -- What actually happened
  accuracy_score DECIMAL(3, 2), -- 0.0 (totally wrong) to 1.0 (perfect prediction)
  accuracy_assessment TEXT, -- E.g., "conservative estimate; actual growth exceeded prediction by 15%"

  -- Falsifier evaluation
  falsifier_triggered BOOLEAN NOT NULL DEFAULT FALSE,
  falsifier_evidence TEXT, -- Why falsifier tripped (if it did)
  revert_reason TEXT, -- Reason for revert (if reverted)

  -- Decision on molt
  state TEXT NOT NULL DEFAULT 'PENDING',
    CHECK (state IN ('PENDING', 'ACTIVE', 'MEASURED', 'DECISION_PENDING', 'ACCEPTED', 'REVERTED', 'SUPERSEDED')),

  decision_made_at TIMESTAMP WITH TIME ZONE,
  decision_made_by TEXT, -- Z2 who decided (Night)
  decision TEXT, -- "ACCEPT", "REVERT", "EXTEND", etc.
  decision_rationale TEXT,

  -- Governance linkage
  proposal_id TEXT, -- Link to Q-MOLT-... candidate block in REGISTERED.md
  pr_number INTEGER, -- PR that applied the molt
  pr_url TEXT,
  commit_sha TEXT,
  commit_url TEXT,

  -- Anti-cascade rules
  revert_count INTEGER NOT NULL DEFAULT 0, -- How many times this constant has been reverted
  is_frozen BOOLEAN NOT NULL DEFAULT FALSE, -- If reverted 2x, frozen until Z2 Tier-2 ruling

  -- Category
  category TEXT DEFAULT 'molt',
    CHECK (category IN ('molt', 'constant_update', 'behavior_dial', 'resource_allocation')),

  -- Tracking
  ingestion_source TEXT NOT NULL DEFAULT 'batch_import',
    CHECK (ingestion_source IN ('batch_import', 'relay_webhook', 'github_webhook', 'manual')),

  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_molt_events_molt_id ON public.molt_events(molt_id);
CREATE INDEX idx_molt_events_constant_id ON public.molt_events(constant_id);
CREATE INDEX idx_molt_events_window_start ON public.molt_events(window_start);
CREATE INDEX idx_molt_events_window_end ON public.molt_events(window_end);
CREATE INDEX idx_molt_events_state ON public.molt_events(state);
CREATE INDEX idx_molt_events_accuracy_score ON public.molt_events(accuracy_score DESC);
CREATE INDEX idx_molt_events_falsifier_triggered ON public.molt_events(falsifier_triggered);
CREATE INDEX idx_molt_events_is_frozen ON public.molt_events(is_frozen);
CREATE INDEX idx_molt_events_created_at ON public.molt_events(created_at DESC);

-- ============================================================================
-- AUDIT TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.board_decisions_audit (
  id BIGSERIAL PRIMARY KEY,
  board_decision_id BIGINT NOT NULL REFERENCES public.board_decisions(id) ON DELETE CASCADE,
  operation TEXT NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
  changed_fields JSONB,
  changed_by TEXT,
  changed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.molt_events_audit (
  id BIGSERIAL PRIMARY KEY,
  molt_event_id BIGINT NOT NULL REFERENCES public.molt_events(id) ON DELETE CASCADE,
  operation TEXT NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
  changed_fields JSONB,
  changed_by TEXT,
  changed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes on audit tables
CREATE INDEX idx_board_decisions_audit_decision_id ON public.board_decisions_audit(board_decision_id);
CREATE INDEX idx_board_decisions_audit_changed_at ON public.board_decisions_audit(changed_at DESC);
CREATE INDEX idx_molt_events_audit_molt_id ON public.molt_events_audit(molt_event_id);
CREATE INDEX idx_molt_events_audit_changed_at ON public.molt_events_audit(changed_at DESC);

-- ============================================================================
-- TRIGGER FUNCTIONS FOR AUDIT
-- ============================================================================

CREATE OR REPLACE FUNCTION public.audit_board_decisions_changes()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    INSERT INTO public.board_decisions_audit (board_decision_id, operation, changed_by, changed_at)
    VALUES (OLD.id, 'DELETE', CURRENT_USER, NOW());
    RETURN OLD;
  ELSIF TG_OP = 'UPDATE' THEN
    INSERT INTO public.board_decisions_audit (board_decision_id, operation, changed_fields, changed_by, changed_at)
    VALUES (NEW.id, 'UPDATE',
      jsonb_object_agg(key, NEW.*->key) FILTER (WHERE (OLD.*)::text <> (NEW.*)::text),
      CURRENT_USER, NOW());
    RETURN NEW;
  ELSIF TG_OP = 'INSERT' THEN
    INSERT INTO public.board_decisions_audit (board_decision_id, operation, changed_by, changed_at)
    VALUES (NEW.id, 'INSERT', CURRENT_USER, NOW());
    RETURN NEW;
  END IF;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION public.audit_molt_events_changes()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    INSERT INTO public.molt_events_audit (molt_event_id, operation, changed_by, changed_at)
    VALUES (OLD.id, 'DELETE', CURRENT_USER, NOW());
    RETURN OLD;
  ELSIF TG_OP = 'UPDATE' THEN
    INSERT INTO public.molt_events_audit (molt_event_id, operation, changed_fields, changed_by, changed_at)
    VALUES (NEW.id, 'UPDATE',
      jsonb_object_agg(key, NEW.*->key) FILTER (WHERE (OLD.*)::text <> (NEW.*)::text),
      CURRENT_USER, NOW());
    RETURN NEW;
  ELSIF TG_OP = 'INSERT' THEN
    INSERT INTO public.molt_events_audit (molt_event_id, operation, changed_by, changed_at)
    VALUES (NEW.id, 'INSERT', CURRENT_USER, NOW());
    RETURN NEW;
  END IF;
END;
$$ LANGUAGE plpgsql;

-- Create triggers
CREATE TRIGGER board_decisions_audit_trigger
AFTER INSERT OR UPDATE OR DELETE ON public.board_decisions
FOR EACH ROW EXECUTE FUNCTION public.audit_board_decisions_changes();

CREATE TRIGGER molt_events_audit_trigger
AFTER INSERT OR UPDATE OR DELETE ON public.molt_events
FOR EACH ROW EXECUTE FUNCTION public.audit_molt_events_changes();

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

ALTER TABLE public.board_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.molt_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.board_decisions_audit ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.molt_events_audit ENABLE ROW LEVEL SECURITY;

-- Restrict writes to service_role only (same as Phase 1)
CREATE POLICY board_decisions_write_service_role ON public.board_decisions
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY board_decisions_read_authenticated ON public.board_decisions
  FOR SELECT TO authenticated USING (true);

CREATE POLICY molt_events_write_service_role ON public.molt_events
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY molt_events_read_authenticated ON public.molt_events
  FOR SELECT TO authenticated USING (true);

CREATE POLICY board_decisions_audit_read_authenticated ON public.board_decisions_audit
  FOR SELECT TO authenticated USING (true);

CREATE POLICY molt_events_audit_read_authenticated ON public.molt_events_audit
  FOR SELECT TO authenticated USING (true);

-- ============================================================================
-- GRANTS
-- ============================================================================

GRANT SELECT ON public.board_decisions TO authenticated;
GRANT ALL ON public.board_decisions TO service_role;

GRANT SELECT ON public.molt_events TO authenticated;
GRANT ALL ON public.molt_events TO service_role;

GRANT SELECT ON public.board_decisions_audit TO authenticated;
GRANT SELECT ON public.molt_events_audit TO authenticated;

GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO service_role;
