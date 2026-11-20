# ACAT Supabase Version Binding — READ-ONLY E0 Proposal
**Issue:** [#750](https://github.com/humanaios-ui/operations/issues/750) · **Status:** Z1 DATA-MODEL PROPOSAL, NOT APPLIED · **Source:** live HumanAIOS Supabase metadata inspected 2026-11-09 under authorized connector

## Observed storage (metadata-level only)
- Existing `public.acat_assessments_v1` has fields including `acat_version`, `instrument_variant`, `prompt_version`, six-core P1/P3 typed columns, extended fields including handoff, `submission_purity`, `learning_index`, `learning_index_uncapped`, `contamination_status`, and `metadata`. **Column existence is not proof all rows populate those fields.**
- `public.acat_stats_v1` is a stored summary and its `timestamp` must be respected. It is not a live aggregate of all `acat_assessments_v1` rows.
- `public.acat_dimension` and `public.acat_assessment` are separate schema surfaces. Their existence does not mean they host the canonical ACAT score rows.
- Current `public` tables inspected reported RLS enabled; an implementation must still review policies, view privileges, roles and API exposure.

**Privacy:** This document deliberately omits internal row details, agent names, subject IDs, private account receipts and verbatim assessments. No SQL DDL/DML has been executed.

## Proposed private registry shape (not yet an executable migration)

**`acat_instrument_version_registry` (immutable, admin governed, private schema):**
`instrument_version_id` immutable key; `family`; `source_commit`; `spec_digest`; `p1_digest`; `p2_digest`; `p3_digest`; `dimension_ids` and text definitions; `dimension_count`; `scale_min`/`scale_max`; `tier`; `phase2_exposure_type`; `li_formula_id`; `sag_formula_id`; `zero_denominator_policy`; `p3_cap_policy`; `valid_from`; `ratification_ref`; `evidence_standing`; `created_at`.

**`acat_instrument_row_binding` (append-only binding, private schema):**
`assessment_id` (existing UUID); `instrument_version_id` (nullable while unknown); `mapping_evidence_digest`; `mapping_basis` (`explicit_raw_metadata|prompt_proof|operator_claim|unknown`); `source_at`; `reviewed_at`; `reviewed_by_pseudonym`; `migration_status` (`PROPOSED|VERIFIED|UNKNOWN|REJECTED`); `supersedes_binding_id`; `authority_effect=NONE`. A mapping is **not a change to original score rows**.

**`acat_version_conflict` (append-only proposal):** affected source/field, conflicting versions, evidence pointers, resolution status, reviewer and decision reference; no score values.

## Read-only diagnostic and migration gates
1. Snapshot export with row count, schema hash, permitted user data minimization, retention policy, and a freeze before any backfill.
2. Group by `acat_version, instrument_variant, prompt_version, submission_purity`; label each group `UNKNOWN` when its primary prompt cannot be proved.
3. Recompute **candidate** six-core LI only when all matching P1/P3 core dimensions exist and denominator >0. Compare stored LI with tolerance; classify mismatch as `REQUIRES_VERSION_REVIEW`, **never automatically as corruption**.
4. Audit `learning_index_uncapped`, exposure and clamping flags, repeat sessions and variant origin before proposing repairs. Protect opposite-direction (P3>P1) examples and do not convert them to downward change.
5. Study two independent datasets separately: operational score rows and stored/externally published corpus summaries. Freeze external export/version and filters before asserting equal N.
6. Create schema changes only after Z2 decision and a separate migration PR, read-only sample rehearsal, RLS/policy review, private-backfill approval, and rollback plan. Do not grant `anon` or `authenticated` broad access.
7. Any public comparison must use anonymized aggregates and an approved k-anonymity/suppression policy; legal/commercial provider data must stay separately permissioned.

## Acceptance examples
- Unknown original prompt => `instrument_version_id=NULL, migration_status=UNKNOWN`.
- One missing score, denominator 0, inconsistent tier, anchored P3 in claimed unanchored cohort => **no LI recomputation/merge**.
- A retrospective GitHub PR attributed to Claude Code => **not an ACAT self-report row**.
- A draft document titled `ACAT_CANONICAL_INSTRUMENT.md` => **not a ratification reference**.
- A verified exact source + prompt + rubric + version + cohort + Z2 approval => eligible for separate binding proposal, never silent rewrite of original data.

**No database changes were made as part of ACAT #750.**
