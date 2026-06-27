# Session PR Index — S-062726 (inaugural humanaios session)

**Status:** Zone 1 tracking artifact — the full board of open PRs + backlog for Z2 review
**Date:** 2026-06-27
**Scope:** All branches pushed to `humanaios-ui/operations` this session. **0 merged · 0 conflicts.**

> Companion to the per-folder audit reports (`AUDIT_TOOLS_S-062726.md`, `AUDIT_ACAT_S-062726.md`). This is the merge-decision board.

---

## 1. Open PRs (8)

| # | Branch | What it does | Δ | Type | Z-status |
|---|--------|-------------|---|------|----------|
| 1 | `p1-activate-ci` | Relocate 6 dormant workflows → `.github/workflows/`, fix audit grep, wire pytest | 7f · +51/−4 | CI | awaiting Z2 |
| 2 | `reconcile-migrations-ha000` | Canonical migration order 006–012 + manifest; unblocks HA-000 | 4f · +92 | DB/gov | **Z2-ratified** → merge |
| 3 | `ssi-human-score-amendment` | `human_score.schema.json` + `rater_did`/`submission_signature` | 1f · +12 | contract | awaiting Z2 |
| 4 | `fix/root-audit-integrity` | Create `ACAT_SESSION_PROMPT.md` (phantom authority) + repair DRIFT_LOG loop | 3f · +128 | gov integrity | awaiting Z2 |
| 5 | `remediate/tools-corruption-cluster` | Delete 6 dupes + `tools/` audit report + **partial** de-corrupt (flagged) | 11f · +551/−1751 | cleanup+audit | awaiting Z2 |
| 6 | `audit/acat-service` | `acat/` audit report + delete 2 confusion-trap dupes | 3f · +151/−366 | audit | awaiting Z2 |
| 7 | `mitigate/acat-pause-writes` | Env-gated 503 write-pause (corpus-poisoning mitigation) | 1f · +23 | security/urgent | superseded by auth-reopen* |
| 8 | `fix/acat-scoring-integrity` | Migration 006 (handoff cols, `acat_human_scores`, purity/LI) + LI consolidation | 4f · +102/−21 | validity | awaiting Z2 + Z3 DB apply |

\* The auth-reopen PR folds the pause kill-switch into a full guard; #7 remains valid as the *immediate* interim (or just set `ACAT_WRITES_PAUSED=1` in Railway now).

## 2. Recommended merge order

1. **#1 CI** — first, so everything after is auto-tested.
2. **Pause** — set `ACAT_WRITES_PAUSED=1` now (or merge #7) to close the live exposure.
3. **#2 → #3 → #8** — the **HA-000 prerequisite chain** (#2 ratified; #8's migration is a Z3 DB apply after the one in-file purity-backfill decision).
4. **#4** — governance integrity (session prompt + drift-log).
5. **#5, #6** — audit reports (docs; #5 carries the *partial* de-corrupt to handle separately).

## 3. Pending — not yet PR'd

**Night decisions (Z2):**
- Auth scheme (ratified design below)
- Purity legacy-row backfill → then tighten the constraint
- Mount-or-delete the 4 orphan `acat/` routers (humility_audit, reports, scoring, health) + the MCP surface

**Ratified auth design (layered, data-first — built as the reopen PR):**
- Public intake → **quarantine staging table** + rate-limit/Turnstile (participation stays open; anonymous writes never reach the canonical corpus)
- Privileged writes (human-score, programmatic `/assess`) → **API key**
- Structural → **stop `service_role` for caller-driven writes + add RLS** (the real fix; matches Phase 7 §7d)

**Clear Z1 fixes queued:** error-handling centralization (stop reflecting raw `exc`/Supabase bodies; scrub `api_key`; filter `metadata` PII) · `session_id` persistence + dedupe upsert · tools/ unguarded-import cluster (`governance_fetcher`, `slack_notifier`, `parse_wgs_z3`, `server.py`) · markdown-corruption keepers' re-indentation **or** the root-cause save-pipeline fix.

## 4. Audit traversal progress

| Folder | Files | Status |
|---|---|---|
| root | 28 | ✅ done |
| `tools/` | 188 | ✅ done (31 ad-hoc + 157 workflow) |
| `acat/` | 60 | ✅ done |
| `docs/` | 69 | ⏳ in progress |
| `site/` | 61 | queued |
| `humanaios-funding-pipeline/`, `orcid-publications-manager/`, `architecture/`, smaller | ~50 | queued |

**Plan:** complete the traversal of the entire framework, then sit with all audit results for a holistic review.

## 5. July-16 critical-path connection

The acat/ findings added a dependency to the validity-demonstrated close:

```
007/009 canonical ✅ → apply migration 006 + LI fix (#8) → apply 008+009 → run HA-000 → niche statement leverages it
```

Running HA-000 against the *current* live scorer would calibrate a broken computation, so **#8 is now on the HA-000 critical path**, not just the DD list.
