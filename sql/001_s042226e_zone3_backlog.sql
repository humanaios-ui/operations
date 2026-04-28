-- ════════════════════════════════════════════════════════════════════════════
-- HAIOSCC SEED · S-042226-E Zone 3 Backlog → zone3_queue
-- ════════════════════════════════════════════════════════════════════════════
-- Run AFTER migration 001.
-- Purpose: seed the 9 open items from the S-042226-E close into the queue
-- so that a run of /api/verify/run_all can auto-close items already complete
-- (e.g. workflow file already pushed) and flag items still genuinely open.
--
-- All rows use ON CONFLICT DO NOTHING by leveraging natural-key checks via
-- the `title` column being effectively unique within a session. If re-run,
-- this will no-op on existing rows.
-- ════════════════════════════════════════════════════════════════════════════

-- Helper to avoid duplicates: only insert if title doesn't already exist open
do $$
declare
  -- S-042226-E session marker
  src text := 'S-042226-E';
begin

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. Deploy acat_pipeline_trigger.yml to .github/workflows/
-- ─────────────────────────────────────────────────────────────────────────────
if not exists (select 1 from public.zone3_queue
               where title = 'Deploy acat_pipeline_trigger.yml to .github/workflows/'
                 and resolved_at is null) then
  insert into public.zone3_queue (title, description, severity, owner, source_session,
                                  verification_kind, verification_target)
  values (
    'Deploy acat_pipeline_trigger.yml to .github/workflows/',
    'GitHub Actions workflow for 6-provider ACAT runner. Replaces Make.com scenarios.',
    'WARN', 'zone3', src,
    'github_workflow_exists',
    '{"owner":"humanaios-ui","repo":"lasting-light-ai","path":".github/workflows/acat_pipeline_trigger.yml"}'::jsonb
  );
end if;

-- ─────────────────────────────────────────────────────────────────────────────
-- 2. Deploy research_agent.yml to .github/workflows/
-- ─────────────────────────────────────────────────────────────────────────────
if not exists (select 1 from public.zone3_queue
               where title = 'Deploy research_agent.yml to .github/workflows/'
                 and resolved_at is null) then
  insert into public.zone3_queue (title, description, severity, owner, source_session,
                                  verification_kind, verification_target)
  values (
    'Deploy research_agent.yml to .github/workflows/',
    'Weekly arXiv + Metaculus research agent with auto findings branches + PRs.',
    'WARN', 'zone3', src,
    'github_workflow_exists',
    '{"owner":"humanaios-ui","repo":"lasting-light-ai","path":".github/workflows/research_agent.yml"}'::jsonb
  );
end if;

-- ─────────────────────────────────────────────────────────────────────────────
-- 3. Deploy haios_audit.yml to .github/workflows/
-- ─────────────────────────────────────────────────────────────────────────────
if not exists (select 1 from public.zone3_queue
               where title = 'Deploy haios_audit.yml to .github/workflows/'
                 and resolved_at is null) then
  insert into public.zone3_queue (title, description, severity, owner, source_session,
                                  verification_kind, verification_target)
  values (
    'Deploy haios_audit.yml to .github/workflows/',
    'Daily A1/A4/A5/A6 checks on push to main. Catches stale dimension count + Cherokee refs.',
    'WARN', 'zone3', src,
    'github_workflow_exists',
    '{"owner":"humanaios-ui","repo":"lasting-light-ai","path":".github/workflows/haios_audit.yml"}'::jsonb
  );
end if;

-- ─────────────────────────────────────────────────────────────────────────────
-- 4-9. GitHub secrets for 6 n8n webhooks + research + CF_AIG_TOKEN
-- Each secret is its own row so they close independently.
-- CF_AIG_TOKEN is already set per S-042226-E close; will auto-resolve.
-- ─────────────────────────────────────────────────────────────────────────────
-- 4. N8N_WEBHOOK_CLAUDE
if not exists (select 1 from public.zone3_queue
               where title = 'GitHub secret: N8N_WEBHOOK_CLAUDE set on lasting-light-ai'
                 and resolved_at is null) then
  insert into public.zone3_queue (title, severity, owner, source_session,
                                  verification_kind, verification_target)
  values (
    'GitHub secret: N8N_WEBHOOK_CLAUDE set on lasting-light-ai',
    'WARN', 'zone3', src,
    'github_secret_set',
    '{"owner":"humanaios-ui","repo":"lasting-light-ai","secret_name":"N8N_WEBHOOK_CLAUDE"}'::jsonb
  );
end if;
-- 5. N8N_WEBHOOK_OPENAI
if not exists (select 1 from public.zone3_queue
               where title = 'GitHub secret: N8N_WEBHOOK_OPENAI set on lasting-light-ai'
                 and resolved_at is null) then
  insert into public.zone3_queue (title, severity, owner, source_session,
                                  verification_kind, verification_target)
  values (
    'GitHub secret: N8N_WEBHOOK_OPENAI set on lasting-light-ai',
    'WARN', 'zone3', src,
    'github_secret_set',
    '{"owner":"humanaios-ui","repo":"lasting-light-ai","secret_name":"N8N_WEBHOOK_OPENAI"}'::jsonb
  );
end if;
-- 6. N8N_WEBHOOK_LLAMA
if not exists (select 1 from public.zone3_queue
               where title = 'GitHub secret: N8N_WEBHOOK_LLAMA set on lasting-light-ai'
                 and resolved_at is null) then
  insert into public.zone3_queue (title, severity, owner, source_session,
                                  verification_kind, verification_target)
  values (
    'GitHub secret: N8N_WEBHOOK_LLAMA set on lasting-light-ai',
    'WARN', 'zone3', src,
    'github_secret_set',
    '{"owner":"humanaios-ui","repo":"lasting-light-ai","secret_name":"N8N_WEBHOOK_LLAMA"}'::jsonb
  );
end if;
-- 7. N8N_WEBHOOK_MISTRAL
if not exists (select 1 from public.zone3_queue
               where title = 'GitHub secret: N8N_WEBHOOK_MISTRAL set on lasting-light-ai'
                 and resolved_at is null) then
  insert into public.zone3_queue (title, severity, owner, source_session,
                                  verification_kind, verification_target)
  values (
    'GitHub secret: N8N_WEBHOOK_MISTRAL set on lasting-light-ai',
    'WARN', 'zone3', src,
    'github_secret_set',
    '{"owner":"humanaios-ui","repo":"lasting-light-ai","secret_name":"N8N_WEBHOOK_MISTRAL"}'::jsonb
  );
end if;
-- 8. N8N_WEBHOOK_COHERE
if not exists (select 1 from public.zone3_queue
               where title = 'GitHub secret: N8N_WEBHOOK_COHERE set on lasting-light-ai'
                 and resolved_at is null) then
  insert into public.zone3_queue (title, severity, owner, source_session,
                                  verification_kind, verification_target)
  values (
    'GitHub secret: N8N_WEBHOOK_COHERE set on lasting-light-ai',
    'WARN', 'zone3', src,
    'github_secret_set',
    '{"owner":"humanaios-ui","repo":"lasting-light-ai","secret_name":"N8N_WEBHOOK_COHERE"}'::jsonb
  );
end if;
-- 9. N8N_WEBHOOK_GEMINI
if not exists (select 1 from public.zone3_queue
               where title = 'GitHub secret: N8N_WEBHOOK_GEMINI set on lasting-light-ai'
                 and resolved_at is null) then
  insert into public.zone3_queue (title, severity, owner, source_session,
                                  verification_kind, verification_target)
  values (
    'GitHub secret: N8N_WEBHOOK_GEMINI set on lasting-light-ai',
    'WARN', 'zone3', src,
    'github_secret_set',
    '{"owner":"humanaios-ui","repo":"lasting-light-ai","secret_name":"N8N_WEBHOOK_GEMINI"}'::jsonb
  );
end if;
-- 10. N8N_WEBHOOK_RESEARCH
if not exists (select 1 from public.zone3_queue
               where title = 'GitHub secret: N8N_WEBHOOK_RESEARCH set on lasting-light-ai'
                 and resolved_at is null) then
  insert into public.zone3_queue (title, severity, owner, source_session,
                                  verification_kind, verification_target)
  values (
    'GitHub secret: N8N_WEBHOOK_RESEARCH set on lasting-light-ai',
    'WARN', 'zone3', src,
    'github_secret_set',
    '{"owner":"humanaios-ui","repo":"lasting-light-ai","secret_name":"N8N_WEBHOOK_RESEARCH"}'::jsonb
  );
end if;
-- 11. CF_AIG_TOKEN (should auto-resolve per S-042226-E)
if not exists (select 1 from public.zone3_queue
               where title = 'GitHub secret: CF_AIG_TOKEN set on lasting-light-ai'
                 and resolved_at is null) then
  insert into public.zone3_queue (title, severity, owner, source_session,
                                  verification_kind, verification_target)
  values (
    'GitHub secret: CF_AIG_TOKEN set on lasting-light-ai',
    'INFO', 'zone3', src,
    'github_secret_set',
    '{"owner":"humanaios-ui","repo":"lasting-light-ai","secret_name":"CF_AIG_TOKEN"}'::jsonb
  );
end if;

-- ─────────────────────────────────────────────────────────────────────────────
-- 12-13. n8n setup (no API verification yet for these — Day 2+)
-- Kept as manual_confirm for now so they don't block and so we track them.
-- ─────────────────────────────────────────────────────────────────────────────
if not exists (select 1 from public.zone3_queue
               where title = 'Import n8n_acat_claude_runner.json + credentials into n8n'
                 and resolved_at is null) then
  insert into public.zone3_queue (title, description, severity, owner, source_session,
                                  verification_kind, verification_target)
  values (
    'Import n8n_acat_claude_runner.json + credentials into n8n',
    'Import workflow; add Anthropic + Sheets + Slack + Supabase credentials.',
    'WARN', 'zone3', src,
    'manual_confirm',
    '{}'::jsonb
  );
end if;

if not exists (select 1 from public.zone3_queue
               where title = 'Create n8n research orchestrator workflow (arXiv + Metaculus)'
                 and resolved_at is null) then
  insert into public.zone3_queue (title, severity, owner, source_session,
                                  verification_kind, verification_target)
  values (
    'Create n8n research orchestrator workflow (arXiv + Metaculus)',
    'WARN', 'zone3', src,
    'manual_confirm',
    '{}'::jsonb
  );
end if;

-- ─────────────────────────────────────────────────────────────────────────────
-- 14-16. Supabase hardening (content checks on migration files to come)
-- For Day 1 these are manual_confirm — Day 2 we add supabase_sql_check kind.
-- ─────────────────────────────────────────────────────────────────────────────
if not exists (select 1 from public.zone3_queue
               where title = 'Supabase: ALTER VIEW acat_assessments_v1_unified SET (security_invoker=on)'
                 and resolved_at is null) then
  insert into public.zone3_queue (title, severity, owner, source_session,
                                  verification_kind, verification_target)
  values (
    'Supabase: ALTER VIEW acat_assessments_v1_unified SET (security_invoker=on)',
    'CRITICAL', 'zone3', src,
    'manual_confirm',
    '{}'::jsonb
  );
end if;

if not exists (select 1 from public.zone3_queue
               where title = 'Supabase: tighten 6 WITH CHECK (true) INSERT policies'
                 and resolved_at is null) then
  insert into public.zone3_queue (title, severity, owner, source_session,
                                  verification_kind, verification_target)
  values (
    'Supabase: tighten 6 WITH CHECK (true) INSERT policies',
    'CRITICAL', 'zone3', src,
    'manual_confirm',
    '{}'::jsonb
  );
end if;

if not exists (select 1 from public.zone3_queue
               where title = 'Supabase: fix data_snapshot.created_at column mismatch'
                 and resolved_at is null) then
  insert into public.zone3_queue (title, severity, owner, source_session,
                                  verification_kind, verification_target)
  values (
    'Supabase: fix data_snapshot.created_at column mismatch',
    'WARN', 'zone3', src,
    'manual_confirm',
    '{}'::jsonb
  );
end if;

-- ─────────────────────────────────────────────────────────────────────────────
-- 17. Cherokee references cleanup (Principle 12) — 4 repos
-- Uses github_file_content_check, expect absent. Starts with the most visible repo.
-- ─────────────────────────────────────────────────────────────────────────────
if not exists (select 1 from public.zone3_queue
               where title = 'Principle 12: Remove Cherokee refs from lasting-light-ai README'
                 and resolved_at is null) then
  insert into public.zone3_queue (title, description, severity, owner, source_session,
                                  verification_kind, verification_target)
  values (
    'Principle 12: Remove Cherokee refs from lasting-light-ai README',
    'Principle 12 violation flagged in gap analysis. Public-facing surface.',
    'WARN', 'zone3', src,
    'github_file_content_check',
    '{"owner":"humanaios-ui","repo":"lasting-light-ai","path":"README.md","pattern":"Cherokee","expect":"absent"}'::jsonb
  );
end if;

-- ─────────────────────────────────────────────────────────────────────────────
-- 18. Stale "6 dimension" references cleanup — 19 HTML files
-- Verification: spot-check the most-visited file (observatory.html).
-- ─────────────────────────────────────────────────────────────────────────────
if not exists (select 1 from public.zone3_queue
               where title = 'Stale dimension count in observatory.html (instrument is 11D)'
                 and resolved_at is null) then
  insert into public.zone3_queue (title, description, severity, owner, source_session,
                                  verification_kind, verification_target)
  values (
    'Stale dimension count in observatory.html (instrument is 11D)',
    'Gate 2 blocker. Instrument is 11 dimensions; public surfaces say 6.',
    'WARN', 'zone3', src,
    'github_file_content_check',
    '{"owner":"humanaios-ui","repo":"lasting-light-ai","path":"public/observatory.html","pattern":"6 dimension","expect":"absent"}'::jsonb
  );
end if;

end $$;

-- ─────────────────────────────────────────────────────────────────────────────
-- Confirm
-- ─────────────────────────────────────────────────────────────────────────────
-- After running, expect ~17 rows in zone3_queue with resolved_at IS NULL.
-- After first /api/verify/run_all, items with workflows/secrets already deployed
-- will show resolved_at populated. Items still genuinely open will remain NULL.
--
-- select count(*) from public.zone3_queue where resolved_at is null;
-- select title, verification_kind, severity from public.zone3_queue
--   where resolved_at is null order by severity;
