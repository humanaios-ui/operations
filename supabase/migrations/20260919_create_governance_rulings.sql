-- Migration: Create governance_rulings table
-- Purpose: Autonomous tracking of Z2 governance decisions
-- Date: 2026-09-19
-- Phase: 1 (Governance Events)

-- ============================================================
-- governance_rulings table
-- ============================================================

CREATE TABLE IF NOT EXISTS governance_rulings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ruling_id VARCHAR(50) NOT NULL UNIQUE,
  decision VARCHAR(50) NOT NULL,              -- ACCEPT|EDIT|REJECT|LATER|BYPASS|SET|RULE_NOW|ARCHIVE
  pr_number INT,
  pr_url VARCHAR(500),
  commit_sha VARCHAR(40),
  commit_url VARCHAR(500),
  ratified_by VARCHAR(255),                  -- Z2 name or session ID
  ratified_at TIMESTAMP NOT NULL,            -- commit timestamp
  ratification_hash VARCHAR(64),             -- SHA256 of decision
  question TEXT,                             -- What was being decided
  category VARCHAR(50),                      -- board|artifact|schema|process|policy
  state VARCHAR(20) NOT NULL DEFAULT 'PENDING', -- PENDING|ACCEPTED|EXECUTED|SUPERSEDED
  board_section VARCHAR(100),                -- Which section of board (d1-d31, etc.)
  issue_refs TEXT,                           -- Related issue numbers: #378, #405, etc.
  ingestion_source VARCHAR(50),              -- git_commit|relay_webhook|manual
  ingestion_timestamp TIMESTAMP DEFAULT NOW(),
  indexed BOOLEAN DEFAULT false,             -- Whether indexed/archived by relay
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- Indexes
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_governance_rulings_ruling_id ON governance_rulings(ruling_id);
CREATE INDEX IF NOT EXISTS idx_governance_rulings_ratified_at ON governance_rulings(ratified_at DESC);
CREATE INDEX IF NOT EXISTS idx_governance_rulings_state ON governance_rulings(state);
CREATE INDEX IF NOT EXISTS idx_governance_rulings_category ON governance_rulings(category);
CREATE INDEX IF NOT EXISTS idx_governance_rulings_pr_number ON governance_rulings(pr_number);
CREATE INDEX IF NOT EXISTS idx_governance_rulings_ratified_by ON governance_rulings(ratified_by);
CREATE INDEX IF NOT EXISTS idx_governance_rulings_created_at ON governance_rulings(created_at DESC);

-- ============================================================
-- Row-Level Security (RLS)
-- ============================================================

ALTER TABLE governance_rulings ENABLE ROW LEVEL SECURITY;

-- Policy: Allow all authenticated users to SELECT
-- (restrict writes to service role / ingestion service)
CREATE POLICY "allow_select_authenticated" ON governance_rulings
  FOR SELECT
  USING (auth.role() = 'authenticated' OR auth.role() = 'service_role');

-- Policy: Only service role can INSERT/UPDATE/DELETE
CREATE POLICY "service_role_write" ON governance_rulings
  FOR ALL
  USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');

-- ============================================================
-- Audit trigger
-- ============================================================

CREATE TABLE IF NOT EXISTS governance_rulings_audit (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ruling_id VARCHAR(50),
  operation VARCHAR(10),                    -- INSERT|UPDATE|DELETE
  old_values JSONB,
  new_values JSONB,
  changed_by VARCHAR(255),
  changed_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_governance_rulings_audit_ruling_id ON governance_rulings_audit(ruling_id);
CREATE INDEX IF NOT EXISTS idx_governance_rulings_audit_changed_at ON governance_rulings_audit(changed_at DESC);

-- Trigger function for audit logging
CREATE OR REPLACE FUNCTION audit_governance_rulings()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO governance_rulings_audit (ruling_id, operation, old_values, new_values, changed_by)
  VALUES (
    COALESCE(NEW.ruling_id, OLD.ruling_id),
    TG_OP,
    CASE WHEN TG_OP = 'DELETE' THEN row_to_json(OLD) ELSE NULL END,
    CASE WHEN TG_OP != 'DELETE' THEN row_to_json(NEW) ELSE NULL END,
    CURRENT_USER
  );
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Create trigger
DROP TRIGGER IF EXISTS governance_rulings_audit_trigger ON governance_rulings;
CREATE TRIGGER governance_rulings_audit_trigger
AFTER INSERT OR UPDATE OR DELETE ON governance_rulings
FOR EACH ROW
EXECUTE FUNCTION audit_governance_rulings();

-- ============================================================
-- Grants
-- ============================================================

GRANT SELECT ON governance_rulings TO authenticated;
GRANT ALL ON governance_rulings TO service_role;
GRANT SELECT ON governance_rulings_audit TO authenticated;
GRANT ALL ON governance_rulings_audit TO service_role;

-- ============================================================
-- Comments
-- ============================================================

COMMENT ON TABLE governance_rulings IS 'Autonomous tracking of Z2 governance decisions. Populated by GitHub webhooks + scheduled git log parser. Read-only for authenticated users, writes restricted to service role.';

COMMENT ON COLUMN governance_rulings.ruling_id IS 'Unique identifier: d15, d16, etc. (board decision order)';
COMMENT ON COLUMN governance_rulings.decision IS 'Z2 decision: ACCEPT|EDIT|REJECT|LATER|BYPASS|SET|RULE_NOW|ARCHIVE|etc.';
COMMENT ON COLUMN governance_rulings.ratification_hash IS 'SHA256(ruling_id | decision | question | ratified_by | ratified_at) for integrity verification';
COMMENT ON COLUMN governance_rulings.state IS 'Lifecycle: PENDING (awaiting integration), ACCEPTED (in REGISTERED.md), EXECUTED (work started), SUPERSEDED (newer ruling replaces)';
COMMENT ON COLUMN governance_rulings.ingestion_source IS 'How was this record ingested: git_commit (parsed from commit message), relay_webhook (from live relay service), manual (Z2 entered directly)';
