-- ════════════════════════════════════════════════════════════════════════════
-- HAIOSCC MIGRATION 001 · Foundation Tables
-- ════════════════════════════════════════════════════════════════════════════
-- Ratified against: HAIOSCC_OPERATIONAL_BUILD_PLAN_V1_0.md · April 22, 2026
-- Apply in: Supabase SQL Editor on project ksinisdzgtnqzsymhfya
-- Idempotent: safe to re-run; uses IF NOT EXISTS + ON CONFLICT
-- Scope: new tables only. Does not touch acat_assessments_v1 or any existing table.
-- ════════════════════════════════════════════════════════════════════════════

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. operational_state — single-row heartbeat
-- ─────────────────────────────────────────────────────────────────────────────
create table if not exists public.operational_state (
  id                  int primary key default 1 check (id = 1),
  pipeline_color      text not null default 'UNKNOWN',
  pipeline_evidence   jsonb,
  runway_days         numeric,
  runway_as_of        timestamptz,
  revenue_usd         numeric default 0,
  gate1_status        text default 'PASSED',
  gate2_target        date default '2026-05-07',
  gate3_target        date default '2026-05-21',
  critical_count      int default 0,
  updated_at          timestamptz default now()
);

insert into public.operational_state (id, pipeline_color, gate1_status)
values (1, 'YELLOW', 'PASSED')
on conflict (id) do nothing;

comment on table public.operational_state is
  'Single-row heartbeat consumed by HAIOSCC top bar. id is always 1.';

-- ─────────────────────────────────────────────────────────────────────────────
-- 2. zone3_queue — the verification-backed queue (core of the whole system)
-- ─────────────────────────────────────────────────────────────────────────────
create table if not exists public.zone3_queue (
  id                  uuid primary key default gen_random_uuid(),
  title               text not null,
  description         text,
  severity            text default 'INFO'
                        check (severity in ('CRITICAL','WARN','INFO')),
  owner               text default 'zone3'
                        check (owner in ('zone1','zone2','zone3')),
  source_session      text,
  verification_kind   text not null,
  verification_target jsonb not null default '{}'::jsonb,
  created_at          timestamptz default now(),
  last_checked_at     timestamptz,
  last_check_result   jsonb,
  resolved_at         timestamptz,
  resolved_by         text,
  carry_count         int default 0,
  created_by          text default 'system'
);

create index if not exists idx_zone3_open
  on public.zone3_queue (resolved_at) where resolved_at is null;
create index if not exists idx_zone3_severity
  on public.zone3_queue (severity, resolved_at);

comment on table public.zone3_queue is
  'Every open action in the system. resolved_at = NULL means open. '
  'resolved_at is only ever set by a verification function, never by a human directly.';

-- ─────────────────────────────────────────────────────────────────────────────
-- 3. collaborators — minimal CRM
-- ─────────────────────────────────────────────────────────────────────────────
create table if not exists public.collaborators (
  id                  uuid primary key default gen_random_uuid(),
  name                text not null,
  role                text,
  email               text,
  next_action         text,
  next_action_due     date,
  last_contact_at     timestamptz,
  last_contact_type   text,
  notes               text,
  status              text default 'active'
                        check (status in ('active','dormant','closed')),
  created_at          timestamptz default now(),
  updated_at          timestamptz default now()
);

-- ─────────────────────────────────────────────────────────────────────────────
-- 4. funding_pipeline — replaces hardcoded FinanceTab array
-- ─────────────────────────────────────────────────────────────────────────────
create table if not exists public.funding_pipeline (
  id                  uuid primary key default gen_random_uuid(),
  source              text not null,
  amount_low          numeric,
  amount_high         numeric,
  amount_display      text,
  deadline            date,
  deadline_display    text,
  status              text default 'NOT_SUBMITTED',
  status_color        text,
  link                text,
  notes               text,
  submitted_at        timestamptz,
  decided_at          timestamptz,
  decision            text check (decision in ('accepted','declined') or decision is null),
  awarded_amount      numeric,
  created_at          timestamptz default now(),
  updated_at          timestamptz default now()
);

-- ─────────────────────────────────────────────────────────────────────────────
-- 5. integrations_registry — replaces hardcoded ConnTab array
-- ─────────────────────────────────────────────────────────────────────────────
create table if not exists public.integrations_registry (
  id                  uuid primary key default gen_random_uuid(),
  name                text not null,
  integration_type    text,
  status              text default 'ACTIVE',
  status_color        text,
  fds_layer           text,
  zone                text,
  health_check_url    text,
  last_health_check   timestamptz,
  last_health_ok      boolean,
  notes               text,
  updated_at          timestamptz default now()
);

-- ─────────────────────────────────────────────────────────────────────────────
-- 6. ic_ledger — corrections ledger
-- ─────────────────────────────────────────────────────────────────────────────
create table if not exists public.ic_ledger (
  id                  text primary key,
  title               text not null,
  description         text,
  principle_violated  text,
  status              text default 'OPEN'
                        check (status in ('OPEN','RESOLVED','ARCHIVED')),
  filed_session       text,
  filed_at            timestamptz default now(),
  resolved_session    text,
  resolved_at         timestamptz,
  corrective_action   text
);

-- ─────────────────────────────────────────────────────────────────────────────
-- 7. verification_log — append-only audit trail
-- ─────────────────────────────────────────────────────────────────────────────
create table if not exists public.verification_log (
  id                  bigserial primary key,
  queue_item_id       uuid references public.zone3_queue(id) on delete cascade,
  ran_at              timestamptz default now(),
  verification_kind   text,
  result_ok           boolean,
  result_payload      jsonb,
  duration_ms         int,
  triggered_by        text
                        check (triggered_by in ('scheduler','user_click','action_post','manual_test'))
);

create index if not exists idx_verlog_queue
  on public.verification_log (queue_item_id, ran_at desc);

comment on table public.verification_log is
  'Append-only. Every verification run writes one row. Never delete; this is the '
  'evidence trail that proves resolved items were actually verified.';

-- ═══════════════════════════════════════════════════════════════════════════
-- ROW LEVEL SECURITY — lock everything by default
-- ═══════════════════════════════════════════════════════════════════════════
-- Service role key bypasses RLS (that is how postgres RLS works). CF Functions
-- use the service role key and can read/write everything. The anon key and
-- authenticated users CANNOT read or write these tables directly — they must
-- go through CF Functions which enforce application-level authorization.
--
-- This simultaneously fixes the gap-analysis finding about WITH CHECK (true)
-- on other tables: new tables never permit anon writes.

alter table public.operational_state      enable row level security;
alter table public.zone3_queue            enable row level security;
alter table public.collaborators          enable row level security;
alter table public.funding_pipeline       enable row level security;
alter table public.integrations_registry  enable row level security;
alter table public.ic_ledger              enable row level security;
alter table public.verification_log       enable row level security;

-- No policies created. With RLS enabled and no policies, anon/authenticated
-- get zero access. Service role bypasses RLS entirely. This is correct.

-- ═══════════════════════════════════════════════════════════════════════════
-- updated_at triggers (keep timestamps honest without client work)
-- ═══════════════════════════════════════════════════════════════════════════
create or replace function public.touch_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

drop trigger if exists trg_touch_operational_state on public.operational_state;
create trigger trg_touch_operational_state
  before update on public.operational_state
  for each row execute function public.touch_updated_at();

drop trigger if exists trg_touch_collaborators on public.collaborators;
create trigger trg_touch_collaborators
  before update on public.collaborators
  for each row execute function public.touch_updated_at();

drop trigger if exists trg_touch_funding_pipeline on public.funding_pipeline;
create trigger trg_touch_funding_pipeline
  before update on public.funding_pipeline
  for each row execute function public.touch_updated_at();

drop trigger if exists trg_touch_integrations_registry on public.integrations_registry;
create trigger trg_touch_integrations_registry
  before update on public.integrations_registry
  for each row execute function public.touch_updated_at();

-- ═══════════════════════════════════════════════════════════════════════════
-- VERIFICATION OF THIS MIGRATION
-- ═══════════════════════════════════════════════════════════════════════════
-- After running, confirm:
--   select count(*) from information_schema.tables
--     where table_schema='public'
--     and table_name in (
--       'operational_state','zone3_queue','collaborators',
--       'funding_pipeline','integrations_registry','ic_ledger','verification_log'
--     );
--   -- expect: 7
--
--   select pipeline_color, gate1_status from public.operational_state;
--   -- expect: one row with YELLOW + PASSED
--
--   select relname, relrowsecurity
--     from pg_class
--     where relname in (
--       'operational_state','zone3_queue','collaborators',
--       'funding_pipeline','integrations_registry','ic_ledger','verification_log'
--     );
--   -- expect: all 7 rows show relrowsecurity = true
