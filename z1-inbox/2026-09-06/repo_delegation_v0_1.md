# humanaios-ui repository delegation v0.1
Z1 · 2026-09-06 · candidate for Z2 · based on live tarball read of `operations` (1,012 files) and `humanaios` (573 files)

## Principle
A practice owns *proposals* in its paths (writes via PR). Z2 stays required reviewer on every gate file. Empirica practices review and are consulted; they write only in their own directory. Tier: 0 = may change without a ruling · 1 = needs a Z2 hash · 2 = registry entry + adv_eval. CODEOWNERS enforces per path; `findings-registry-gate.yml` and `document-control.yml` already exist and enforce on the registry and controlled docs.

## Z2-only (no delegation, both repos)
`REGISTERED.md` · `GOVERNANCE_*` · `AUTHORITY_ASSIGNMENTS.yaml` · `CONTROLLED_DOCUMENTS.md` · `MOLT_STATE.md` · `SESSION_RITUALS.md` · `.github/workflows/*` · `.github/CODEOWNERS` · constants (`behavior_spec.json`, `integrity_modes.json`, rubrics, weights) · `.empirica/practice-spec.yaml` (seat identity).
Rationale: these are the gate. Whoever owns the gate owns the system. IC-REWARD-01 applies to every constant here.

## HumanAIOS practices → paths

| practice | repo · paths | owns (Tier 0) | proposes (Tier 1/2) | CI guard | receipt it must leave |
|---|---|---|---|---|---|
| **humanaios** (Tier 1) | `operations/instruments/`, `operations/architecture/`, `humanaios/src/`, `humanaios/empirica/`, `humanaios/operations/`, `humanaios/memory/`, `humanaios/hooks/`; system_graph.md | Behavior Dials scoring runs, LT-series computation, Operator Model read-backs | constants, graph edges, LT layer, molts | `behavioral-compliance.yml`, `drift-monitor.yml`, `haios-harmonizer-pulse.yml` | NF_LEDGER writes; every reply scored |
| **acat-x** | `operations/acat/` (99), `humanaios/acat/`, `humanaios/h-acat/`, `.empirica/acat_*.json` | test cases, corpus additions, cross-version runs | rubric changes (Tier 1), new dimensions (Tier 2) | `acat-pipeline-trigger.yml`, `haios-corpus-integrity.yml` | corpus hash; the 450-case claim as a file |
| **epistemology** | `operations/registry-candidates/`, `operations/audits/`, `operations/ic_archive/`, `humanaios/audits/`, `tools/falsifier_lint.py`, `tools/claim_lint.py`, VOID-CIT | candidate blocks, lint runs, evidence-tier stamps | lint rule changes (Tier 1); never writes REGISTERED.md | `findings-registry-gate.yml`, `findings-registry.yml`, `research-validation.yml` | Registry Candidate Block per session; lint pass/fail log |
| **quality-assurance** | `operations/tests/`, `operations/fuzzers/`, `.clusterfuzzlite/`, `humanaios/tests/`, `humanaios/test/`, `humanaios/load-tests/`, `tools/adv_eval_v1.py` | tests, fuzz targets, catch-rate runs | gate changes trigger ADV rerun (Tier 2 by rule) | `cflite_pr.yml`, `scorecard.yml`, `no-op-pr-guard.yml`, `builder-lint.yml` | catch-rate per gate; NO_GATE never counted as caught |
| **local-machine-optimizer** | `operations/scripts/`, `operations/bin/`, `humanaios/tools/`, `humanaios/scripts/`, `humanaios/infrastructure/`, `humanaios/packages/`, `humanaios/apps/` (54), `.claude/`, `.codex/`, `.agents/` | dev environment, harness configs, perf baselines | anything touching `.claude/settings.json` model/tool config (Tier 1 — it is a constant) | `builder-lint.yml`; proposed: perf-regression hook | benchmark file per change |
| **resource-miner** (RM) | `operations/market-research/`, `operations/data/`, `operations/humanaios-funding-pipeline/` (21), `operations/applications/` | intake batches, source lists, job-posting scans | intake criteria (prereg hash before run) | `intake-pipeline.yml` (exists — A4 spec) | the first operated cycle; batch hash |
| **Schema (SS)** — *new owner needed* | `operations/sql/` (18), `humanaios/alembic/` | — | every migration is Tier 1 (schema is a constant of the pipeline) | proposed: migration lint | migration id + rollback |
| **opportunity-aggregator** (OA) | `operations/collaborators/`, `operations/deliverables/` (42), `operations/outputs/`, `operations/orcid-publications-manager/` | pipeline status, ROI rubric runs, deliverable routing | ROI weights (Tier 1, IC-REWARD-01) | `daily-deadline-alerts.yml` | ROI rubric output with hash per opportunity |
| **collaborator-ops** | `operations/collaborator-ops/` (13), `operations/collaborators/` (shared with OA), `DEMARIUS_*`, `GITHUB_COLLABORATION_GOVERNANCE.md` | onboarding packages, workspace provisioning, team membership proposals | team membership changes (Tier 1 — CODEOWNERS is a gate) | `mesh-standard-files.yml` | onboarding log; team roster diff |
| **website** | `operations/site/` (61), `operations/ui/`, `operations/assets/`, `humanaios/frontend/`, `humanaios/assets/`, `EXTERNAL_LINK_POLICY.md` | pages, profiles, SEO | public statements about status (must cite a receipt; IC-031) | `pages.yml`, `document-control.yml` (HAIOS-WEB-*) | every status claim on the site links to a registry line |
| **humanaios-internal** | `operations/docs/` (105), `humanaios/docs/` (71), `humanaios/skills/`, session-close docs, `CURRENT.md`, `DRIFT_LOG.md`, `EXECUTION_STATUS.md` | session records, handoff blocks, z2_ledger patches | SESSION_RITUALS changes (Z2-only) | `document-control.yml`, `scheduled-audit.yml` | B.6 reconciliation per session |
| **grok-crossref** | `tools/lineage_score.py`, `tools/tension_score.py`, cross-reference indices in `docs/` | crossref runs, lineage scores | second-substrate audit results enter as DISPUTED/CONFIRM only | `divergence-detect.yml` | lineage score per evidence chain |

## Empirica practices → what they touch here
| practice | writes | reviews | note |
|---|---|---|---|
| evaluator (Admiral) | nothing in humanaios-ui | all Tier 2 PRs, registry candidates | Z2 seat mirror; SR 11-7 says it must not author what it validates — its audits go in `operations/audits/` under epistemology's ownership, not its own |
| autonomy | `operations/autonomy/` (20) only | Agent Runtime caps, `AUTONOMY_INTEGRATION_COORDINATION.md` | caps are constants → IC-REWARD-01 |
| outreach | `.empirica/practice-spec.yaml` on `operations` currently names it — **ruling needed** | `site/`, public statements | if intentional, outreach owns the seat and website owns the pages; if misfiled, respec the seat as `humanaios` |
| mesh-support | `mesh-sync-batch.yml`, `mesh-standard-files.yml` (Z2-reviewed) | routing, callouts, SER state | already the only non-Z2 name on any workflow |

## CODEOWNERS draft — operations (replaces the all-Z2 default; teams must exist first)
```
# gate — Z2 only
REGISTERED.md GOVERNANCE_* AUTHORITY_ASSIGNMENTS.yaml CONTROLLED_DOCUMENTS.md MOLT_STATE.md SESSION_RITUALS.md .empirica/practice-spec.yaml @carly-r-anderson @sab-backup
.github/ @carly-r-anderson
# practices (team = @humanaios-ui/<practice>; Z2 stays on every line until teams have a second member)
/acat/ /instruments/ @humanaios-ui/acat-x @carly-r-anderson
/registry-candidates/ /audits/ /ic_archive/ /tools/falsifier_lint.py /tools/claim_lint.py @humanaios-ui/epistemology @carly-r-anderson
/tests/ /fuzzers/ /.clusterfuzzlite/ /tools/adv_eval_v1.py @humanaios-ui/quality-assurance @carly-r-anderson
/scripts/ /bin/ /.claude/ /.codex/ /.agents/ @humanaios-ui/local-machine-optimizer @carly-r-anderson
/market-research/ /data/ /humanaios-funding-pipeline/ /applications/ @humanaios-ui/resource-miner @carly-r-anderson
/sql/ @humanaios-ui/schema @carly-r-anderson
/collaborators/ /deliverables/ /outputs/ /orcid-publications-manager/ @humanaios-ui/opportunity-aggregator @carly-r-anderson
/collaborator-ops/ DEMARIUS_* GITHUB_COLLABORATION_GOVERNANCE.md @humanaios-ui/collaborator-ops @carly-r-anderson
/site/ /ui/ /assets/ EXTERNAL_LINK_POLICY.md @humanaios-ui/website @carly-r-anderson
/docs/ CURRENT.md DRIFT_LOG.md EXECUTION_STATUS.md @humanaios-ui/humanaios-internal @carly-r-anderson
/autonomy/ @humanaios-ui/autonomy @carly-r-anderson
/architecture/ /src/ /tools/ @humanaios-ui/humanaios @carly-r-anderson
* @carly-r-anderson @sab-backup
```
`humanaios` repo: same shape (`/src/ /empirica/ /operations/ /memory/ /hooks/` → humanaios; `/acat/ /h-acat/` → acat-x; `/tests/ /test/ /load-tests/` → QA; `/tools/ /scripts/ /infrastructure/ /packages/ /apps/` → LMO; `/alembic/` → schema; `/frontend/ /assets/` → website; `/docs/ /skills/` → humanaios-internal; `/audits/` → epistemology). It currently has none — that's the first file to land.

## Sequencing
1. Create the 12 org teams (`gh api` commands are already in `.doc-control/TEAM_OWNERS.md`; extend the loop). One member each is enough to enforce.
2. Land `humanaios/.github/CODEOWNERS` — no gate exists there today.
3. Replace the operations CODEOWNERS. Z2 stays on every line; delegation is real once a second human sits on any team.
4. Rule on the outreach/operations seat mismatch.
5. Name a schema owner (SS) — the only pipeline stage with no practice.

## Falsifier for this delegation
If, 30 days after landing, every PR still requires Z2 review because no team has a second member, the delegation is a map and not a delegation — LAID, and the second-human question (Z2b) is the real blocker.
