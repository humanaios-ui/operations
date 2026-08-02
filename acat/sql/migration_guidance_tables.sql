-- Migration: Create guidance_requests and guidance_sessions tables
-- Version: 001
-- Date: 2026-08-02
-- Purpose: Support wisdom_engine guidance system API

-- ============================================
-- GUIDANCE REQUESTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS guidance_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Request details
    submission_purity VARCHAR(50) NOT NULL,
    evidential_tier VARCHAR(50) NOT NULL,
    humility_hierarchy INTEGER NOT NULL CHECK (humility_hierarchy BETWEEN 0 AND 1000),
    corpus_source VARCHAR(100) NOT NULL,

    -- Optional filters
    constraint_tradition VARCHAR(100),
    constraint_theme VARCHAR(100),
    obstacle VARCHAR(255),

    -- Metadata
    api_key_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_submission_purity CHECK (submission_purity IN ('unverified', 'one_stage_verified', 'two_stage_verified')),
    CONSTRAINT valid_evidential_tier CHECK (evidential_tier IN ('anecdotal', 'observational', 'measured', 'validated')),
    CONSTRAINT valid_corpus_source CHECK (corpus_source IN ('top_curriculum', 'esoteric_wisdom', 'modern_science', 'cross_tradition'))
);

CREATE INDEX idx_guidance_requests_created_at ON guidance_requests(created_at DESC);
CREATE INDEX idx_guidance_requests_api_key_id ON guidance_requests(api_key_id);

-- ============================================
-- GUIDANCE SESSIONS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS guidance_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Request reference
    request_id UUID NOT NULL REFERENCES guidance_requests(id) ON DELETE CASCADE,

    -- Session state
    status VARCHAR(50) NOT NULL DEFAULT 'completed',

    -- Teaching matched
    teaching_tradition VARCHAR(100),
    teaching_title VARCHAR(500),
    teaching_text TEXT,
    teaching_source VARCHAR(255),
    teaching_era VARCHAR(100),

    -- Parallels (stored as JSONB array)
    parallels JSONB DEFAULT '[]',

    -- Next level pathway
    next_level_pathway JSONB,

    -- Transcript (for interactive sessions)
    transcript JSONB DEFAULT '[]',

    -- Observability/confidence
    confidence DECIMAL(3, 2) CHECK (confidence BETWEEN 0 AND 1),
    dimensions_assessed TEXT[] DEFAULT '{}',

    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Constraints
    CONSTRAINT valid_status CHECK (status IN ('in_progress', 'completed', 'archived'))
);

CREATE INDEX idx_guidance_sessions_request_id ON guidance_sessions(request_id);
CREATE INDEX idx_guidance_sessions_status ON guidance_sessions(status);
CREATE INDEX idx_guidance_sessions_created_at ON guidance_sessions(created_at DESC);
CREATE INDEX idx_guidance_sessions_tradition ON guidance_sessions(teaching_tradition);

-- ============================================
-- AUDIT/OBSERVABILITY
-- ============================================
CREATE TABLE IF NOT EXISTS guidance_observability (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES guidance_sessions(id) ON DELETE CASCADE,

    -- Dimension micro-scores (for ACAT feedback loop)
    dimension VARCHAR(50) NOT NULL,
    micro_score INTEGER CHECK (micro_score BETWEEN 0 AND 100),
    baseline_score INTEGER,
    delta INTEGER,
    behavioral_annotation TEXT,
    confidence DECIMAL(3, 2),

    -- Quotes/evidence
    quote TEXT,

    -- Timing
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_guidance_observability_session_id ON guidance_observability(session_id);
CREATE INDEX idx_guidance_observability_dimension ON guidance_observability(dimension);
CREATE INDEX idx_guidance_observability_timestamp ON guidance_observability(timestamp DESC);
