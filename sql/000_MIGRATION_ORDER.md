# Canonical Migration Order

**Status:** Zone 1 draft — for Z2 (Night) ratification. Z3 executes any live `apply`.
**Resolves:** IC-043 (phantom/colliding migration references) · unblocks **HA-000** (P-IMPROVE-01).
**Created:** 2026-06-26 (inaugural humanaios session).

---

## 0. Why this file exists

Migration numbers `007` and `009` were each claimed by multiple unreconciled Zone 1
drafts (`007` ×3, `009` ×2), and `006` was never drafted. The drafts were never
landed, never ordered against each other, and were referenced across governance docs
as a contiguous `006→010` prerequisite chain that did not actually exist as files.
That phantom chain is the root cause of HA-000/SSI Phase 0's multi-session
`STANDING BLOCKED` status (IC-043).

This file is the **single source of truth for migration apply order**. There is no
migration runner in the repo; migrations are applied by hand against Supabase. This
manifest is what makes that deterministic. The drafts are all additive and idempotent
(`ADD COLUMN IF NOT EXISTS`, `CREATE TABLE IF NOT EXISTS`, guarded `DO` blocks), so
applying in this order against the live N=95 corpus is safe even where columns already
exist.

## 1. The one hard ordering constraint

```
migration_006_document_engine_tables   (creates public.operational_state)
        ──must precede──▶
migration_007_operational_state_fix     (ALTERs public.operational_state; column guards only,
                                         does NOT create the table — requires it to pre-exist)
```

Every other migration below is an additive, independent `ALTER` on the corpus table
`acat_assessments_v1` and may be applied in any order **after** `acat_assessments_v1`
exists (from the foundation migration). The only other relative rule is the standing
one: **009 requires 008** (p3-grounding builds on self-administered).

## 2. Canonical order

| # | File | Target | Adds / creates | On HA-000 path? |
|---|------|--------|----------------|-----------------|
| 006 | `migration_006_document_engine_tables.sql` | new infra tables | `operational_state`, `zone3_queue`, `collaborators`, `funding_pipeline` (+ guard fns) | no — ops infra |
| 007 | `migration_007_operational_state_fix.sql` | `operational_state` | ~16 columns (gate_status, runway_days, corpus_n_*, …) | no — **must follow 006** |
| 008 | `migration_008_add_self_administered.sql` | `acat_assessments_v1` | `submission_purity` / self-administered flag | **YES** |
| 009 | `migration_009_add_p3_grounding_source.sql` | `acat_assessments_v1` | `p3_grounding_source`, `li_grounded`, `li_consistency_only` (+ GRANTs) | **YES** — requires 008 |
| 010 | `migration_010_add_elicitation_surface.sql` | `acat_assessments_v1` | elicitation-surface columns (Phase 1+) | no — post-Phase-0 |
| 011 | `migration_011_participation_schema.sql` | `acat_assessments_v1` | `encounter_surface`, `acknowledged_elicitation`, `perturbation_type` (+ indexes) | no |
| 012 | `migration_012_document_layers.sql` | `acat_assessments_v1` | `document_layer`, `provider_canonical`, `model_family` (+ index) | no |

`009` stays canonical (bound by Z2-SSI-02, `H-OVG-CHAIN-01`, `CURRENT.md` — all reference
`migration_009` = the `p3_grounding_source` columns). `008` and `010` are unchanged.

## 3. HA-000 dependency — reframed (resolves IC-043)

**Old (phantom) framing:** HA-000 / SSI Phase 0 depends on a contiguous `006→010`
migration chain. — This is what kept it standing-blocked; that chain never existed as files.

**Corrected framing (verified against `docs/SSI_INTEGRATION_OPS_PLAN_V1_0_S061626.md`
Phase 0):** HA-000's actual schema prerequisite is **corpus-table only**:

```
migration_008_add_self_administered   →   migration_009_add_p3_grounding_source
        (both ALTER acat_assessments_v1, additive)
        + amend acat/contracts/human_score.schema.json (Z2-SSI-01)
        + GRANTs verified on acat_assessments_v1
```

The `operational_state` tables (006, 007), `participation_schema` (011), `document_layers`
(012), and `elicitation_surface` (010) are **real, retained work but NOT HA-000
prerequisites.** They can land independently, post-charter, without blocking the
founding run. With this reframe, HA-000 is runnable as soon as 008 + 009 are applied
and `human_score.schema.json` is amended — which is the existing SSI Phase 0 completion
gate, not a phantom chain.

## 4. What this PR changes

- Renamed 3 colliding drafts into unique numbers (history preserved):
  - `migration_007_document_engine_tables.sql` → `migration_006_…`
  - `migration_009_participation_schema.sql` → `migration_011_…`
  - `007_document_layers.sql` → `migration_012_…` (also standardizes the filename convention)
- `migration_007_operational_state_fix.sql` and `migration_009_add_p3_grounding_source.sql`
  keep their numbers (collisions are now resolved).
- Adds this manifest.
- **No `.sql` content changed; no migration applied to live Supabase.**

## 5. Follow-ups for Z2/Z3 (not in this PR)

- [ ] **Decision (Night):** ratify this order + the §3 reframe. On ratify, close IC-043 and P-IMPROVE-01's schema blocker.
- [ ] Update stale references to old filenames/“files do not exist” notes: `CURRENT.md` (≈L136 pending-migrations line), `SEED.md`, `OPS_ROADMAP_V1.2.md`, and the provenance comment in `tools/acat_merkle_auditor_v2_0.py` L21. (Auditor hashing is unaffected — it hashes P1/P3/state data blocks, not filenames.)
- [ ] Proposed `REGISTERED.md` edit (paste on ratify): *IC-043 resolved — 007/009 collisions reconciled into unique sequence 006–012 (see `sql/000_MIGRATION_ORDER.md`); HA-000 prerequisite reframed to corpus-only 008→009(p3); 006 now exists (document_engine_tables). P-IMPROVE-02 (migration verify) → the post-charter full-convention cleanup.*
- [ ] **Post-charter (P-IMPROVE-02):** optional full renumber of the entire line into a gapless sequence + one filename convention — reproducibility polish, off the July-16 path.
