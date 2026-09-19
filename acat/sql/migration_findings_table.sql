-- Migration: Create findings table for Empirica findings ingestion
-- Version: 002
-- Date: 2026-08-02
-- Purpose: Store findings from GitHub Actions, VS Code extension, autonomy

-- ============================================
-- FINDINGS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS findings (
    id VARCHAR(36) PRIMARY KEY,

    -- Finding classification
    type VARCHAR(50) NOT NULL,
    source VARCHAR(100) NOT NULL,

    -- Finding details
    description TEXT NOT NULL,
    file VARCHAR(500) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    confidence DECIMAL(3, 2) CHECK (confidence BETWEEN 0 AND 1),

    -- Optional fields
    suggested_action TEXT,
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    timestamp TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_type CHECK (type IN ('security_scan', 'code_review', 'performance', 'other')),
    CONSTRAINT valid_source CHECK (source IN ('github_codeql', 'github_trivy', 'copilot_suggestion', 'autonomy_p6_verdicts', 'manual', 'other')),
    CONSTRAINT valid_severity CHECK (severity IN ('critical', 'high', 'medium', 'low'))
);

CREATE INDEX idx_findings_source ON findings(source);
CREATE INDEX idx_findings_severity ON findings(severity);
CREATE INDEX idx_findings_created_at ON findings(created_at DESC);
CREATE INDEX idx_findings_type ON findings(type);
CREATE INDEX idx_findings_file ON findings(file);

-- ============================================
-- FINDINGS SEARCH TABLE (for semantic search)
-- ============================================
CREATE TABLE IF NOT EXISTS findings_search (
    id VARCHAR(36) PRIMARY KEY REFERENCES findings(id) ON DELETE CASCADE,

    -- Embedding (stored as text for portability; Qdrant is primary vector store)
    embedding_summary TEXT,

    -- Search metadata
    description_tokens TEXT[],
    file_tokens TEXT[],

    -- Qdrant reference
    qdrant_point_id BIGINT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_findings_search_qdrant ON findings_search(qdrant_point_id);
