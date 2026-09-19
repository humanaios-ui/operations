-- Migration: acat_triage_log
-- Purpose: persist humanaios-triage-finding TRIAGE_BLOCK outputs going
-- forward, including STOPped ones. REGISTERED.md only ever contains
-- observations that already passed the triage gate (Q1-Q4) and were routed
-- to Zone 2 -- STOPped observations go to session notes today and leave no
-- queryable trace. This table is what makes Advance Pass Rate computable;
-- without it, "Advance Pass Rate" has no denominator (no record of
-- attempts, only of survivors).
--
-- registered_id is intentionally nullable and unlinked at write time: a
-- triage run logs immediately, the F-/H-/IC- number (if any) only exists
-- later, if and when Night ratifies it in REGISTERED.md. Backfilling
-- registered_id once that happens is what turns this table + registry_loader
-- into an actual end-to-end Advance -> Validate trace per observation,
-- not just two separate ratios that happen to rhyme.

create table if not exists acat_triage_log (
    id                  uuid primary key default gen_random_uuid(),
    session_id          text,
    observation_summary text not null,
    proposed_class       text check (proposed_class in ('F', 'IC', 'H')),
    proposed_dimensions  text[],

    -- Full Q1-Q7 results as produced by the TRIAGE_BLOCK, e.g.:
    --   {"q1": {"result": "PASS"}, "q4": {"result": "PARTIAL", "n": 1}, ...}
    -- Stored as jsonb rather than 7 fragile columns since each question's
    -- result shape differs (PASS/STOP vs PASS/EXTENDS/REPLICATES/STOP vs
    -- COMPLETE/INCOMPLETE) and the gate's own question wording is allowed
    -- to evolve without a schema migration every time.
    gate_results        jsonb not null,

    gate_verdict        text not null check (gate_verdict in ('ROUTE_TO_Z2', 'HOLD', 'STOP')),
    evidence_package    jsonb,
    proposed_entry_draft text,
    gaps_to_address     text[],

    -- Filled in later, manually, once/if Zone 2 ratifies and REGISTERED.md
    -- assigns an actual id. NULL until then. This is the join key back to
    -- registry_loader's parsed entries.
    registered_id        text,

    created_at          timestamptz not null default now()
);

create index if not exists idx_acat_triage_log_verdict on acat_triage_log (gate_verdict);
create index if not exists idx_acat_triage_log_created_at on acat_triage_log (created_at);
create index if not exists idx_acat_triage_log_registered_id on acat_triage_log (registered_id);

comment on table acat_triage_log is
    'Persisted humanaios-triage-finding TRIAGE_BLOCK outputs (S-061726). '
    'Source of the Advance Pass Rate numerator/denominator -- not computable '
    'from REGISTERED.md alone, since STOPped observations never reach it.';
