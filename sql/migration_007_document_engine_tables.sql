-- =============================================================================
-- Migration 007: Document Engine Tables
-- Project: ksinisdzgtnqzsymhfya
-- Session: current
-- Zone: Z3 — Night executes
-- Author: Unit Zero (Claude) — Zone 1 draft
-- Supabase API change notice: All new tables require explicit GRANTs
-- (per CURRENT.md §5 — breaking change May 30, 2026)
-- =============================================================================
-- Apply with:
--   supabase db push  (from local CLI)
--   OR paste into Supabase SQL editor as a single transaction
-- Verify after apply:
--   SELECT table_name FROM information_schema.tables
--   WHERE table_schema = 'public'
--   AND table_name IN (
--     'zone3_queue','operational_state','collaborators','funding_pipeline'
--   );
-- =============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- TABLE 1: zone3_queue
-- Purpose: Self-closing Zone 3 task queue, verification-driven
-- Source spec: CURRENT.md §6.2 Layer 2 component list
-- Verification model: item is OPEN until evidence_url is populated by Night
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.zone3_queue (
  id                BIGSERIAL PRIMARY KEY,
  item_id           TEXT NOT NULL UNIQUE,          -- human-readable slug, e.g. "Z3-2026-06-07-001"
  title             TEXT NOT NULL,
  description       TEXT,
  zone              TEXT NOT NULL DEFAULT 'Z3',
  status            TEXT NOT NULL DEFAULT 'open'
                    CHECK (status IN ('open','in_progress','closed','archived')),
  priority          TEXT NOT NULL DEFAULT 'normal'
                    CHECK (priority IN ('critical','high','normal','low')),
  session_origin    TEXT,                          -- session ID where item was raised
  raised_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  closed_at         TIMESTAMPTZ,
  evidence_url      TEXT,                          -- required for status → 'closed'
  evidence_note     TEXT,                          -- human-readable verification note
  carry_count       INT NOT NULL DEFAULT 0,        -- incremented each session item remains open
  carry_escalated   BOOLEAN NOT NULL DEFAULT FALSE,-- TRUE when carry_count >= 3
  wgs_post_ts       TEXT,                          -- Slack message ts of originating WGS post
  related_finding   TEXT,                          -- F-class / IC-class reference if applicable
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Prevent closing without evidence
CREATE OR REPLACE FUNCTION public.zone3_queue_close_guard()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.status = 'closed' AND (NEW.evidence_url IS NULL OR trim(NEW.evidence_url) = '') THEN
    RAISE EXCEPTION 'zone3_queue: cannot set status=closed without evidence_url';
  END IF;
  IF NEW.status = 'closed' AND NEW.closed_at IS NULL THEN
    NEW.closed_at := NOW();
  END IF;
  NEW.updated_at := NOW();
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS zone3_queue_close_guard_trigger ON public.zone3_queue;
CREATE TRIGGER zone3_queue_close_guard_trigger
  BEFORE UPDATE ON public.zone3_queue
  FOR EACH ROW EXECUTE FUNCTION public.zone3_queue_close_guard();

-- Carry escalation: auto-flag items open >= 3 sessions
CREATE OR REPLACE FUNCTION public.zone3_queue_carry_escalate()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.carry_count >= 3 AND NOT NEW.carry_escalated THEN
    NEW.carry_escalated := TRUE;
  END IF;
  NEW.updated_at := NOW();
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS zone3_queue_carry_escalate_trigger ON public.zone3_queue;
CREATE TRIGGER zone3_queue_carry_escalate_trigger
  BEFORE UPDATE OF carry_count ON public.zone3_queue
  FOR EACH ROW EXECUTE FUNCTION public.zone3_queue_carry_escalate();

-- ---------------------------------------------------------------------------
-- TABLE 2: operational_state
-- Purpose: Single-row heartbeat — pipeline color, runway, revenue, gate status
-- Source spec: CURRENT.md §6.2 Layer 2 + haioscc.pages.dev /api/state/operational
-- Design: enforce single-row via constraint; UPDATE only, no multi-row inserts
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.operational_state (
  id                INT PRIMARY KEY DEFAULT 1
                    CHECK (id = 1),               -- enforces single-row
  pipeline_color    TEXT NOT NULL DEFAULT 'YELLOW'
                    CHECK (pipeline_color IN ('GREEN','YELLOW','RED','UNKNOWN')),
  gate_status       TEXT NOT NULL DEFAULT 'Gate 2 PASSED',
  ord_day           INT,                           -- charter day number (1-90)
  runway_days       INT,                           -- days of runway remaining
  revenue_usd       NUMERIC(12,2) NOT NULL DEFAULT 0.00,
  open_z3_count     INT NOT NULL DEFAULT 0,
  escalated_z3_count INT NOT NULL DEFAULT 0,
  corpus_n_total    INT,                           -- mirrors CURRENT.md §5 frozen archive
  corpus_n_phase1   INT,
  corpus_n_li       INT,
  last_wgs_session  TEXT,                          -- session ID of most recent WGS close
  last_updated_by   TEXT,                          -- substrate or 'night'
  notes             TEXT,
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seed the single row
INSERT INTO public.operational_state (id, pipeline_color, gate_status, ord_day,
  corpus_n_total, corpus_n_phase1, corpus_n_li, last_updated_by, notes)
VALUES (1, 'YELLOW', 'Gate 2 PASSED', 51,
  629, 516, 307, 'migration_007',
  'Seeded by migration_007. Update via Supabase MCP or Night terminal.')
ON CONFLICT (id) DO NOTHING;

-- ---------------------------------------------------------------------------
-- TABLE 3: collaborators
-- Purpose: CRM layer — contact state, next actions, tier, zone gates
-- Source spec: CURRENT.md §5 collaborations table; SEED.md §5
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.collaborators (
  id                BIGSERIAL PRIMARY KEY,
  slug              TEXT NOT NULL UNIQUE,          -- e.g. 'demarius-lawson', 'david-van-assche'
  display_name      TEXT NOT NULL,
  org               TEXT,
  tier              TEXT CHECK (tier IN ('T1','T2','T3','T4','T5','advisory','client','pending')),
  type              TEXT NOT NULL DEFAULT 'collaborator'
                    CHECK (type IN ('research','governance','comms','capital','platform','client','pending')),
  status            TEXT NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active','paused','closed','prospect')),
  contact_email     TEXT,
  contact_channel   TEXT,                          -- 'email' | 'slack' | 'github' | 'whatsapp' etc.
  zone_gate         TEXT,                          -- blocking Z2 gate if any, e.g. 'Z2-CORPUS-TRUST-01'
  last_contact_at   TIMESTAMPTZ,
  next_action       TEXT,
  next_action_due   DATE,
  attribution_class TEXT CHECK (attribution_class IN ('A','B','C',NULL)),
                                                   -- Class A = 50/50 joint findings
  p_anon_cleared    BOOLEAN NOT NULL DEFAULT FALSE,-- P-ANON: self-attributed publicly?
  notes             TEXT,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seed known collaborators from SEED.md §5 (P-ANON: all public-record names)
INSERT INTO public.collaborators
  (slug, display_name, org, tier, type, status, contact_email, contact_channel,
   zone_gate, attribution_class, p_anon_cleared, next_action, notes)
VALUES
  ('demarius-lawson', 'DeMarius J. Lawson', 'Governing Engines / Mode AI',
   'T1', 'governance', 'active', NULL, 'github',
   'Z2-CORPUS-TRUST-01', 'A', TRUE,
   'Resolve Z2-CORPUS-TRUST-01 to unblock Mode AI onboarding and all eight-provider work',
   'Convergent independent discovery of F-INTENT-PARSE-MUTATION. G1 and G2 gates open.'),
  ('david-van-assche', 'David Van Assche', 'Nubaeon / empirica',
   'T2', 'research', 'active', 'soulentheo@gmail.com', 'email',
   NULL, 'B', TRUE,
   'Schedule empirica Run 1 after ACAT Phase 1 prompt sharing (Z2 gate: Night confirms artifact sharing clearance)',
   'Joint pilot confirmed 2026-05-08. Cross-instrument: empirica=Brier epistemic, ACAT=behavioral drift.'),
  ('moni-pereira', 'Mónica Pereira Di Mella', 'Sydän Studio',
   'T5', 'comms', 'active', 'sydanstudio@gmail.com', 'email',
   NULL, 'C', TRUE,
   'Await read of status brief sent 2026-05-08. Key question: unified narrative for dual audience.',
   'Strategic narrative + positioning review. 6 dimensions. Schmidt branch closed.'),
  ('alex-berlin', 'Alex Berlin', 'Revby',
   NULL, 'capital', 'active', NULL, 'email',
   NULL, NULL, TRUE,
   'NSF SBIR / funding strategy — ongoing.',
   'Capital advisory.'),
  ('alex-liteplo', 'Alex Liteplo', 'RentAHuman',
   NULL, 'platform', 'active', NULL, 'email',
   NULL, NULL, TRUE,
   'Human data collection pathway — scope next session.',
   'Platform integration for human baseline ACAT data.')
ON CONFLICT (slug) DO NOTHING;

-- ---------------------------------------------------------------------------
-- TABLE 4: funding_pipeline
-- Purpose: Grant and funding pipeline state
-- Source spec: CURRENT.md §10 priorities; FUNDING_PIPELINE_MASTER_V2_0.md
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.funding_pipeline (
  id                BIGSERIAL PRIMARY KEY,
  slug              TEXT NOT NULL UNIQUE,          -- e.g. 'nsf-sbir-2026', 'mozilla-2026'
  funder            TEXT NOT NULL,
  program           TEXT,
  amount_usd        NUMERIC(12,2),
  status            TEXT NOT NULL DEFAULT 'prospect'
                    CHECK (status IN (
                      'prospect','researching','drafting','submitted',
                      'under_review','awarded','rejected','deferred','archived'
                    )),
  deadline          DATE,
  gate_requirement  TEXT,                          -- what must be true before submission
  submission_url    TEXT,
  submitted_at      TIMESTAMPTZ,
  decision_at       TIMESTAMPTZ,
  decision_note     TEXT,
  p5_pass           BOOLEAN NOT NULL DEFAULT TRUE, -- passes OR&D decision filter
  arxiv_required    BOOLEAN NOT NULL DEFAULT FALSE,-- blocks on arXiv clearance?
  lead_contact      TEXT,                          -- collaborator slug or name
  notes             TEXT,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seed highest-priority funders from CURRENT.md §10 and FUNDING_PIPELINE_MASTER_V2_0.md
INSERT INTO public.funding_pipeline
  (slug, funder, program, status, gate_requirement, arxiv_required, p5_pass, notes)
VALUES
  ('nsf-sbir-2026', 'NSF', 'SBIR Project Pitch',
   'drafting',
   'arXiv preprint public; pipeline GREEN; 2-3 paragraph pitch ready',
   TRUE, TRUE,
   'Highest-leverage near-term funding per CURRENT.md §10. Expected window Apr-May 2026 (now overdue — reassess timing).'),
  ('mozilla-2026', 'Mozilla Foundation', 'Mozilla Technology Fund',
   'prospect',
   'arXiv preprint public',
   TRUE, TRUE,
   'Application unlocks after arXiv hold clears.'),
  ('nimhd-2026', 'NIH / NIMHD', 'Research Grant',
   'prospect',
   'arXiv preprint public',
   TRUE, TRUE,
   'Application unlocks after arXiv hold clears.')
ON CONFLICT (slug) DO NOTHING;

-- ---------------------------------------------------------------------------
-- EXPLICIT GRANTS — required for all new tables (Supabase breaking change May 30)
-- Source: CURRENT.md §5 API change notice
-- ---------------------------------------------------------------------------
GRANT SELECT, INSERT, UPDATE, DELETE ON public.zone3_queue       TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.operational_state TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.collaborators      TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.funding_pipeline   TO anon, authenticated, service_role;

-- Grant sequence access for BIGSERIAL columns
GRANT USAGE, SELECT ON SEQUENCE public.zone3_queue_id_seq        TO anon, authenticated, service_role;
GRANT USAGE, SELECT ON SEQUENCE public.collaborators_id_seq      TO anon, authenticated, service_role;
GRANT USAGE, SELECT ON SEQUENCE public.funding_pipeline_id_seq   TO anon, authenticated, service_role;

-- ---------------------------------------------------------------------------
-- VERIFICATION QUERIES (run immediately after applying)
-- ---------------------------------------------------------------------------
-- SELECT table_name, COUNT(*) as row_count
-- FROM (
--   SELECT 'zone3_queue' as table_name FROM public.zone3_queue
--   UNION ALL
--   SELECT 'operational_state' FROM public.operational_state
--   UNION ALL
--   SELECT 'collaborators' FROM public.collaborators
--   UNION ALL
--   SELECT 'funding_pipeline' FROM public.funding_pipeline
-- ) t GROUP BY table_name;
--
-- Expected: zone3_queue=0, operational_state=1, collaborators=5, funding_pipeline=3

COMMIT;

-- =============================================================================
-- POST-MIGRATION CHECKLIST (Zone 3)
-- =============================================================================
-- [ ] Run verification query above — confirm row counts match expected
-- [ ] Verify GRANTs via: SELECT grantee, privilege_type
--     FROM information_schema.role_table_grants
--     WHERE table_name = 'zone3_queue';
-- [ ] Confirm operational_state seed row exists:
--     SELECT pipeline_color, gate_status, ord_day FROM public.operational_state;
-- [ ] Update CURRENT.md §9 changelog with migration_007 applied date
-- [ ] Test anon key read access from humanaios.ai frontend
-- =============================================================================
