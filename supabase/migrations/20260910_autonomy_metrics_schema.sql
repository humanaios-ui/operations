-- Autonomy Metrics Schema — PostgreSQL Tables for Decision Telemetry, Escalations, Metrics Aggregation
-- Session: S-090926-NN
-- Status: DEPLOYED

CREATE SCHEMA IF NOT EXISTS autonomy;

-- ────────────────────────────────────────────────────────────────
-- Table 1: autonomy_events (core event log)
-- ────────────────────────────────────────────────────────────────
-- Captures every autonomy decision, escalation, or system event.
-- Enables per-event tracing and debugging.

CREATE TABLE IF NOT EXISTS autonomy.events (
  id BIGSERIAL PRIMARY KEY,
  event_id TEXT NOT NULL UNIQUE,  -- Globally unique event identifier (evt-XXX)
  timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  practice_id TEXT NOT NULL,  -- Which practice emitted this event (e.g., empirica-autonomy)

  -- Event classification
  event_type TEXT NOT NULL,  -- 'decision', 'escalation', 'gate_transition', 'blocker'
  dimension TEXT,  -- Optional: which dimension (truth, service, harm, autonomy, value, humility)
  channel TEXT,  -- Event channel (decision_proposal, escalation_alert, gate_change)

  -- Payload & metrics (structured JSON)
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,  -- Event-specific data
  metrics JSONB DEFAULT '{}'::jsonb,  -- Computed metrics (counts, rates, etc.)

  -- Metadata for tracking
  source_gate TEXT,  -- Which gate/module emitted (mason_gate, verified_tacit_gate, etc.)
  parent_event_id TEXT REFERENCES autonomy.events(event_id) ON DELETE SET NULL,  -- Chaining related events
  tags TEXT[] DEFAULT ARRAY[]::TEXT[],  -- Event tags (high-impact, critical, routine)

  -- Audit & governance
  created_by TEXT,  -- AI identity or system user
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ────────────────────────────────────────────────────────────────
-- Table 2: autonomy_decisions (decision metadata & outcomes)
-- ────────────────────────────────────────────────────────────────
-- Tracks decision proposals, approval/rejection, and outcomes.
-- Linked to events via decision_id.

CREATE TABLE IF NOT EXISTS autonomy.decisions (
  id BIGSERIAL PRIMARY KEY,
  decision_id TEXT NOT NULL UNIQUE,  -- Unique ID (dec-XXX)
  event_id TEXT REFERENCES autonomy.events(event_id) ON DELETE SET NULL,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  practice_id TEXT NOT NULL,  -- Where decision was made

  -- Decision context
  proposal_title TEXT,  -- Short description of the decision
  proposal_body TEXT,  -- Full justification/reasoning
  dimensions_affected TEXT[],  -- Which dimensions this decision impacts

  -- Decision lifecycle
  status TEXT NOT NULL,  -- 'proposed', 'approved', 'rejected', 'escalated', 'executed'
  status_timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

  -- Approval authority
  approved_by TEXT,  -- Who approved (ECO actor, AI identity, etc.)
  approval_note TEXT,  -- Why approved/rejected

  -- Outcome tracking
  executed BOOLEAN DEFAULT FALSE,
  execution_timestamp TIMESTAMPTZ,
  execution_sha TEXT,  -- Git commit SHA if code-based decision
  outcome_impact NUMERIC(3,2),  -- Impact score (0.0 - 1.0)

  -- Related artifacts
  parent_decision_id TEXT REFERENCES autonomy.decisions(decision_id) ON DELETE SET NULL,
  related_escalations BIGINT[] DEFAULT ARRAY[]::BIGINT[],  -- Related escalation IDs

  created_by TEXT,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ────────────────────────────────────────────────────────────────
-- Table 3: autonomy_escalations (escalation tracking)
-- ────────────────────────────────────────────────────────────────
-- Records when decisions escalate, why, who they escalate to, and resolution.

CREATE TABLE IF NOT EXISTS autonomy.escalations (
  id BIGSERIAL PRIMARY KEY,
  escalation_id TEXT NOT NULL UNIQUE,  -- Unique ID (esc-XXX)
  event_id TEXT REFERENCES autonomy.events(event_id) ON DELETE SET NULL,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  practice_id TEXT NOT NULL,  -- Originating practice

  -- Escalation context
  reason TEXT NOT NULL,  -- Why escalation occurred (ambiguity, cross-practice impact, trust_level_needed)
  severity TEXT,  -- 'low', 'medium', 'high', 'critical'

  -- Source (what triggered escalation)
  source_decision_id TEXT REFERENCES autonomy.decisions(decision_id) ON DELETE SET NULL,
  source_event_id TEXT REFERENCES autonomy.events(event_id) ON DELETE SET NULL,

  -- Escalation target & routing
  escalated_to TEXT NOT NULL,  -- Target practice or role (mesh-support, admiral, ECO)
  escalation_path TEXT[],  -- Breadcrumb of who it passed through

  -- Resolution
  status TEXT NOT NULL,  -- 'open', 'acknowledged', 'in_review', 'resolved'
  status_timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  resolved_by TEXT,  -- Who resolved
  resolution_note TEXT,
  resolved_at TIMESTAMPTZ,

  -- SLA tracking
  sla_seconds INTEGER,  -- Target resolution time in seconds
  actual_seconds INTEGER,  -- Actual resolution time
  sla_met BOOLEAN,

  created_by TEXT,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ────────────────────────────────────────────────────────────────
-- Table 4: autonomy_metrics (aggregated metrics for dashboard)
-- ────────────────────────────────────────────────────────────────
-- Materialized summary for dashboard queries (computed hourly/daily).
-- Enables fast aggregation without scanning raw event tables.

CREATE TABLE IF NOT EXISTS autonomy.metrics (
  id BIGSERIAL PRIMARY KEY,
  metric_date DATE NOT NULL,  -- Which date this metric covers
  metric_hour SMALLINT,  -- Which hour (0-23), NULL for daily

  -- Scope
  practice_id TEXT,  -- NULL = system-wide, specific = one practice
  dimension TEXT,  -- NULL = all dimensions, specific = one dimension

  -- Counts
  events_total BIGINT DEFAULT 0,
  decisions_proposed BIGINT DEFAULT 0,
  decisions_approved BIGINT DEFAULT 0,
  decisions_rejected BIGINT DEFAULT 0,
  decisions_executed BIGINT DEFAULT 0,

  escalations_open BIGINT DEFAULT 0,
  escalations_resolved BIGINT DEFAULT 0,
  escalations_critical BIGINT DEFAULT 0,

  -- Rates (per 1000 decisions)
  escalation_rate_per_1k NUMERIC(5,2) DEFAULT 0,
  approval_rate NUMERIC(3,2) DEFAULT 0,  -- (approved / proposed)
  execution_rate NUMERIC(3,2) DEFAULT 0,  -- (executed / approved)

  -- SLA metrics
  escalation_sla_met_count BIGINT DEFAULT 0,
  escalation_sla_missed_count BIGINT DEFAULT 0,
  avg_sla_response_seconds NUMERIC(10,2),

  -- Dimension-specific (if dimension is set)
  top_dimension_dimension TEXT,
  top_dimension_event_count BIGINT,

  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

  UNIQUE(metric_date, metric_hour, practice_id, dimension)
);

-- ────────────────────────────────────────────────────────────────
-- Table 5: autonomy_decision_audit (audit trail for decisions)
-- ────────────────────────────────────────────────────────────────
-- Immutable log of every change to a decision's status/outcome.

CREATE TABLE IF NOT EXISTS autonomy.decision_audit (
  id BIGSERIAL PRIMARY KEY,
  decision_id TEXT NOT NULL REFERENCES autonomy.decisions(decision_id) ON DELETE CASCADE,

  timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actor TEXT,  -- Who made the change

  action TEXT NOT NULL,  -- 'created', 'approved', 'rejected', 'executed', 'escalated'
  old_status TEXT,
  new_status TEXT,

  note TEXT,  -- Why the change
  metadata JSONB DEFAULT '{}'::jsonb
);

-- ────────────────────────────────────────────────────────────────
-- Indexes (for performance)
-- ────────────────────────────────────────────────────────────────

-- autonomy.events indexes
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON autonomy.events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_practice ON autonomy.events(practice_id);
CREATE INDEX IF NOT EXISTS idx_events_type ON autonomy.events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_dimension ON autonomy.events(dimension);
CREATE INDEX IF NOT EXISTS idx_events_parent ON autonomy.events(parent_event_id);
CREATE INDEX IF NOT EXISTS idx_events_event_id ON autonomy.events(event_id);

-- autonomy.decisions indexes
CREATE INDEX IF NOT EXISTS idx_decisions_timestamp ON autonomy.decisions(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_decisions_status ON autonomy.decisions(status);
CREATE INDEX IF NOT EXISTS idx_decisions_practice ON autonomy.decisions(practice_id);
CREATE INDEX IF NOT EXISTS idx_decisions_executed ON autonomy.decisions(executed);
CREATE INDEX IF NOT EXISTS idx_decisions_decision_id ON autonomy.decisions(decision_id);

-- autonomy.escalations indexes
CREATE INDEX IF NOT EXISTS idx_escalations_timestamp ON autonomy.escalations(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_escalations_status ON autonomy.escalations(status);
CREATE INDEX IF NOT EXISTS idx_escalations_severity ON autonomy.escalations(severity);
CREATE INDEX IF NOT EXISTS idx_escalations_practice ON autonomy.escalations(practice_id);
CREATE INDEX IF NOT EXISTS idx_escalations_sla ON autonomy.escalations(sla_met);
CREATE INDEX IF NOT EXISTS idx_escalations_escalation_id ON autonomy.escalations(escalation_id);

-- autonomy.metrics indexes
CREATE INDEX IF NOT EXISTS idx_metrics_date ON autonomy.metrics(metric_date DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_practice ON autonomy.metrics(practice_id);
CREATE INDEX IF NOT EXISTS idx_metrics_dimension ON autonomy.metrics(dimension);

-- autonomy.decision_audit indexes
CREATE INDEX IF NOT EXISTS idx_audit_decision ON autonomy.decision_audit(decision_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON autonomy.decision_audit(timestamp DESC);

-- ────────────────────────────────────────────────────────────────
-- Permissions (RLS enabled for safety)
-- ────────────────────────────────────────────────────────────────

ALTER TABLE autonomy.events ENABLE ROW LEVEL SECURITY;
ALTER TABLE autonomy.decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE autonomy.escalations ENABLE ROW LEVEL SECURITY;
ALTER TABLE autonomy.metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE autonomy.decision_audit ENABLE ROW LEVEL SECURITY;

-- Policy: authenticated users can read their own practice's data
CREATE POLICY read_own_practice ON autonomy.events
  FOR SELECT
  USING (auth.uid()::text IS NOT NULL);  -- Requires auth

CREATE POLICY read_own_practice_decisions ON autonomy.decisions
  FOR SELECT
  USING (auth.uid()::text IS NOT NULL);

CREATE POLICY read_own_practice_escalations ON autonomy.escalations
  FOR SELECT
  USING (auth.uid()::text IS NOT NULL);

-- Policy: service role (backend) can insert/update
CREATE POLICY insert_events ON autonomy.events
  FOR INSERT
  WITH CHECK (auth.uid()::text IS NOT NULL);

-- ────────────────────────────────────────────────────────────────
-- Views for common queries
-- ────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW autonomy.escalations_open AS
SELECT * FROM autonomy.escalations
WHERE status IN ('open', 'acknowledged', 'in_review')
ORDER BY timestamp DESC;

CREATE OR REPLACE VIEW autonomy.decisions_pending_approval AS
SELECT * FROM autonomy.decisions
WHERE status = 'proposed'
ORDER BY timestamp ASC;

-- ────────────────────────────────────────────────────────────────
-- Comments & Documentation
-- ────────────────────────────────────────────────────────────────

COMMENT ON SCHEMA autonomy IS 'Autonomy protocol metrics and decision tracking for HumanAIOS';
COMMENT ON TABLE autonomy.events IS 'Core event log for all autonomy decision events';
COMMENT ON TABLE autonomy.decisions IS 'Decision proposals and outcomes tracking';
COMMENT ON TABLE autonomy.escalations IS 'Escalation log with SLA tracking';
COMMENT ON TABLE autonomy.metrics IS 'Aggregated metrics for dashboard queries (materialized hourly/daily)';
COMMENT ON TABLE autonomy.decision_audit IS 'Immutable audit trail of decision changes';

COMMENT ON COLUMN autonomy.events.event_id IS 'Globally unique event identifier (evt-XXX format)';
COMMENT ON COLUMN autonomy.events.payload IS 'Event-specific data (JSONB)';
COMMENT ON COLUMN autonomy.decisions.status IS 'Lifecycle status: proposed→approved→executed';
COMMENT ON COLUMN autonomy.escalations.sla_met IS 'Whether escalation was resolved within SLA';
