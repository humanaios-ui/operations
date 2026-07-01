# Session Branch Review — S-070126 (Z2/Z3 worklist)

**Status:** Zone 1 review inventory — for Night's Z2 ratify / Z3 merge at terminal. **Nothing here is merged; Claude does not cross Z3.**
**Scope:** every open branch on `humanaios-ui/operations` ahead of `main` as of S-070126.
**Companion:** `audits/SESSION_PR_INDEX_S-062726.md` (the earlier build-session index) — this doc adds the S-070126 funding/verification/registry work and re-checks the whole set.

---

## ⚠️ Dependency stacks — merge parent before child

| Child branch | Stacked on | Nature |
|---|---|---|
| `funding/longview-submit-ready` | `funding/longview-niche-v0.3` | **Intentional** — carries both commits; merging submit-ready brings the niche. Merge submit-ready, *skip* niche-v0.3 (superseded). |
| `research/convergence-synthesis` | `registry/package-draft-s070126` | Carries the package draft too. Merge package-draft first, or merge convergence alone (it contains both). |
| `chore/gitignore-funding-reports` | ~~funding/longview-digital-minds~~ | **RESOLVED S-070126** — rebased clean onto `main` (`f25f21c`); now carries only `.gitignore`. |

---

## 1. Longview funding (July-2 / July-10 clock — highest priority)

| Branch | Contents | Z-gate / note |
|---|---|---|
| `funding/longview-submit-ready` | 4 submit-ready edits to the Power Concentration app **+ the niche v0.3** | **Merge this** (supersedes niche-v0.3). Z2 ratify → Z3 submit *before July 2*. |
| `funding/longview-niche-v0.3` | Niche statement v0.3 only | Superseded by ↑ — do not merge separately. |
| `funding/longview-digital-minds` | Digital Minds companion app (secondary, July 10) | Independent. Submit *after* Power Concentration. |
| `funding/longview-stats-verification` | Stat-by-stat verification record (`audits/`) | Independent, low-risk. Grounds the citations. |
| `registry/package-draft-s070126` | Staged F-54/F-55/H-* package (transcribed from WGS log) | **Z2 ratify gate + IC-030** before REGISTERED.md append. Unblocks the candidate citations. |
| `research/convergence-synthesis` | ACAT-external/internal convergence synthesis + H-CONV-EMP-01 | Carries package draft; merge after/with package-draft. |

## 2. HA-000 chain (corpus-validity unblock — original critical path)

| Branch | Contents | Note |
|---|---|---|
| `reconcile-migrations-ha000` | `sql/000_MIGRATION_ORDER.md` + renamed migrations (006/011/012) | Z2-ratified (order + §3 reframe). |
| `ssi-human-score-amendment` | `human_score.schema.json` amendment | Z2-ratified. |
| `p1-activate-ci` | 7 GitHub workflows (CI-never-ran fix) | Verify secrets/permissions before enabling. |

## 3. ACAT integrity remediation (DD + research-validity)

| Branch | Contents | Sequence |
|---|---|---|
| `mitigate/acat-pause-writes` | Env-gated 503 write-pause kill-switch | **First** — interim corpus-poisoning mitigation. |
| `fix/acat-scoring-integrity` | Migration 006 + LI consolidation + calculators | Core fix. After pause. |
| `feat/acat-auth-reopen` | Write-guard + API-key middleware | After scoring. Reopen seq: set `ACAT_API_KEYS` → unset `ACAT_WRITES_PAUSED`. |
| `remediate/tools-corruption-cluster` | 11 decorative-stub / markdown-corruption files | Review-heavy; some were PARTIAL (flagged for manual re-indentation). |
| `audit/acat-service` | acat/ service audit + 2 touched files | Informational + minor. |

## 4. Audits & records (low-risk, informational — merge anytime)

`audit/docs-folder` · `audit/site-folder` · `fix/root-audit-integrity` (ACAT_SESSION_PROMPT/DRIFT_LOG/SESSION_RITUALS) · `docs/session-pr-index` · `chore/gitignore-funding-reports` · `docs/session-branch-review` (this doc).

---

## Recommended Z3 order (dependency-respecting)
1. **`mitigate/acat-pause-writes`** — stop corpus poisoning first.
2. **`funding/longview-submit-ready`** → ratify → **submit Power Concentration** (rolling advantage; the one irreversible deadline).
3. **`registry/package-draft-s070126`** (Z2 ratify) then **`research/convergence-synthesis`** — makes the candidate citations traceable.
4. **`fix/acat-scoring-integrity`** → **`feat/acat-auth-reopen`** — the data-integrity core.
5. **`reconcile-migrations-ha000`** + **`ssi-human-score-amendment`** + **`p1-activate-ci`** — HA-000 unblock.
6. **`funding/longview-digital-minds`** — submit before July 10.
7. Audits + `chore/gitignore-funding-reports` + `remediate/tools-corruption-cluster` — merge as reviewed.

## Open items surfaced this session (not yet branched)
- **S-061026-04 log needed** to complete H-APEX-DEFICIT-01, P-RP-01, H-ANON-HUMILITY-01, H-FORMAT-01 (unsourceable from the WGS log — flagged, not fabricated).
- **F-54 numeric divergence** (Human S-H +17.62 / Meta +16.07 vs synthetic +15.47/+20.67) — reconcile against the HF archive before promotion.
- **Two pre-existing modified files** in the working tree (`SUBSTRATE_CAPABILITY_REGISTRY.md`, `VALIDITY_ANALYSIS-BENCHMARK_CROSSWALK.md`) — uncommitted, not from this session; left untouched for Night to triage.
