# Standing Practice Note: Constraint-Before-Inspection Discipline

**Date:** June 17, 2026
**Reference:** IC-032 (registered May 29, 2026) → migration_010 (drafted June 17, 2026)
**Status:** Internal operational note, HumanAIOS / ACAT program

## The incident

On May 29, 2026, a database migration (`003_acat_constraints.sql`) added a CHECK constraint to a corpus table without first querying the live table for existing values. The constraint's enum did not include a value (`agent_self_only`) already present in over 50 live rows. The migration failed on application (Postgres error 23514), caught when it was run and the violation surfaced directly. This was registered as IC-032 — the fourth occurrence of the same root pattern of applying a constraint or schema change without inspecting live data first (see also IC-001/002/003).

## The fix

The corrective principle established at the time: before any constraint, migration, or schema-state declaration, query and inspect the live table directly. Do not infer the existing value set from documentation, prior assumptions, or memory.

## The recent artifact

On June 17, 2026 — roughly three weeks later, on an unrelated piece of work — a separate migration (`migration_010_add_elicitation_surface.sql`) was drafted to extend a different enum field on the same corpus table. The migration's first instruction, written before any `ALTER` statement, is a mandatory inspection query, with an explicit comment naming IC-032 as the reason it is required:

```sql
-- Step 0 — MANDATORY, do not skip (IC-032 precedent)
SELECT DISTINCT submission_version, role_method, behavioral_flag_final
FROM acat_assessments_v1;
```

The migration also explicitly flags, rather than assumes, that the column names it references have not yet been confirmed against the live Supabase schema — the same category of unverified-state risk IC-032 was about, named again on sight before it could recur.

## Why it matters

The claim worth making here is narrower than "an error was avoided," and more defensible for it: a documented incident produced a specific corrective practice, and a separate, later piece of work — on an unrelated feature, weeks afterward — shows that practice being applied as a default rather than a one-off promise. This is the kind of paper trail — incident, named fix, recurrence of the fix in unrelated later work — that supports operational-maturity claims in audit deliverables and funder-facing documentation, without requiring any framing beyond the dates and the artifacts themselves.
