# Mesh Tool · Skill · Workflow Inventory

**Status:** Zone 1 draft — companion to `5S_SIXSIGMA_ACAT_AUDIT_CHARTER_S070726.md`.
**Session:** S-070726 · **Date:** 2026-07-07 · **Author:** Claude Code (Opus 4.8)
**Purpose:** The Sort deliverable — separate **audit-instruments** (run in the Measure phase) from **audit-subjects**, and give Night a complete picture of what tooling exists before the baseline runs.

---

## 1 · At a glance

| Asset class | Count | Location | Role in audit |
|---|---|---|---|
| In-scope repositories | 12 | see charter §2 | audit subjects |
<<<<<<< HEAD
| Tool scripts (top-level) | 93 | `operations/tools/*.py\|*.js\|*.jsx` | mix — 25 audit-instruments, see §2 |
| HAIOS skills (`SKILL.md`) | 78 dirs | `operations/tools/skills/` | mostly tool-companion wrappers + 7 named governance skills |
| Empirica plugin skills | 17 | `~/.claude/plugins/local/empirica/skills/` | audit *method* (constitution, transaction, code-audit, services-auditor) |
| Draft workflow YAMLs | 8 | `operations/tools/`, `operations/workflows/`, `operations/.doc-control/ci/` | Sustain candidates (mostly NOT wired to `.github/`) |
| Live GitHub Actions | 5 total across mesh | only `lasting-light-ai` (2) + `empirica` fork (3, upstream) | **near-zero in authored repos — Sustain gap** |
=======
| Tool scripts (top-level) | 93 | `operations/tools/*.py`, `operations/tools/*.js`, `operations/tools/*.jsx` | mix — 25 audit-instruments, see §2 |
| HAIOS skills (`SKILL.md`) | 78 dirs | `operations/tools/skills/` | mostly tool-companion wrappers + 7 named governance skills |
| Empirica plugin skills | 17 | `~/.claude/plugins/local/empirica/skills/` | audit *method* (constitution, transaction, code-audit, services-auditor) |
| Draft workflow YAMLs | 8 | `operations/tools/`, `operations/workflows/`, `operations/.doc-control/ci/` | Sustain candidates (mostly NOT wired to `.github/`) |
| Live GitHub Actions | 11 total across mesh | `operations` (5) + `humanaios-internal` (1) + `lasting-light-ai` (2) + `empirica` fork (3, upstream) | limited across mesh — many repos still have 0 (see §4) |
>>>>>>> origin/main

---

## 2 · Tool catalog (`operations/tools/`)

Classification: **AUDIT-INSTRUMENT** (inspects files/state, reports defects → runs in Measure) vs subject-side categories (PIPELINE/ORCHESTRATION, CORPUS/DATA, GOVERNANCE/DOC, SCAFFOLD/UTIL, ACAT-CORE).

### 2a · Full classified catalog (93 top-level tools)

| Tool file | One-line purpose | Category |
|---|---|---|
| aa_principle_audit_v1_0.py | Evaluate protocol artifacts against honesty/humility/service markers | AUDIT-INSTRUMENT |
| acat_dimension_scorer.py | Bayesian per-dimension ACAT scoring with credible intervals + LI | ACAT-CORE |
| acat_doc_v1.py | ACAT document scoring dataclasses/schema | ACAT-CORE |
| acat_document_analyzer.py | Keyword-vector ACAT dimension scoring of governance docs | ACAT-CORE |
| acat_document_analyzer_v1_2.py | Adds AST code-semantic scoring to document analyzer | ACAT-CORE |
| acat_mcp_full_wrapper_v1.2.py | ACAT-MCP behavioral telemetry wrapper (gated session engine) | ACAT-CORE |
| acat_mcp_full_wrapper_v1_2_patched.py | Patched telemetry wrapper (+document_layer/provider/model_family) | ACAT-CORE |
| acat_merkle_auditor_v1.0.py | Verify session Merkle receipt + Phase-1 commitment | AUDIT-INSTRUMENT |
| acat_merkle_auditor_v2_0.py | Merkle auditor + W3C Verifiable Credential issuance/verify | AUDIT-INSTRUMENT |
| acat_phase_shift_analyzer_v1_0.py | Per-agent/provider phase-shift metrics across runs | ACAT-CORE |
| acat_pipeline_v0_1.py | Two-layer action-outcome verification pipeline | PIPELINE/ORCHESTRATION |
| acat_protocol_auditor.py | Audit close-post protocol compliance via DFA scan (D-04/D-05) | AUDIT-INSTRUMENT |
| acat_psychometric_validator_v1_0.py | Recompute reliability/factor metrics; method reports | ACAT-CORE |
| acat_room_state_auditor_v1.0.py | Validate Room state metadata vs corpus/session | AUDIT-INSTRUMENT |
| acat_sdt_analytics_v1_0.py | Signal Detection Theory metrics (d', β) from P1/P3 pairs | ACAT-CORE |
| acat_session_validator.py | Validate session Phase1/3 completeness + Merkle receipt | AUDIT-INSTRUMENT |
| anthropic_client_fence_fix.py | API client util stripping markdown fences | SCAFFOLD/UTIL |
| app_mapping_tool.py | Map/scan external apps; score repo collab potential | SCAFFOLD/UTIL |
| assess_router_Z2_assessment.py | FastAPI router for background ACAT assessment jobs | PIPELINE/ORCHESTRATION |
| assess_router_new_Z2-ASSESS-01.py | Clean FastAPI assessment router (Z2-ASSESS-01 rebuild) | PIPELINE/ORCHESTRATION |
| bpl_signal_extractor_v1_0.py | Extract behavioral-language pattern candidates from corpora | CORPUS/DATA |
| builder_compliance_scanner_v1.0.py | Scan Python tools vs Builder v1.7 compliance checklist | AUDIT-INSTRUMENT |
| carry_tracker_v1_0.py | Count sessions-carried per item; flag escalations | PIPELINE/ORCHESTRATION |
| circuit_validator_v1_0.py | Validate each session has complete P1/P3 circuit before LI | AUDIT-INSTRUMENT |
| claim_verification_check_v0_1.py | Verify AI "done" claims vs ground truth (PASS/FAIL/UNVERIFIABLE) | AUDIT-INSTRUMENT |
| corpus_delta_analyzer.py | Diff corpus snapshots for LI regression / D-COMP | CORPUS/DATA |
| corpus_integrity_validator.py | Validate ACAT corpus CSV vs schema + row rules | AUDIT-INSTRUMENT |
| document_ingestor_v1_0.py | Prepare analyzer output as Supabase corpus rows + dedup | CORPUS/DATA |
| document_ingestor_v1_0_patched.py | Patched document corpus ingestion pipeline | CORPUS/DATA |
| drift_catalog_validator.py | Validate drift codes vs registered drift catalog | AUDIT-INSTRUMENT |
| echoes_copilot_acat_scanner_v0_1.py | Scan Copilot build repo: self-report vs demonstrated privacy | AUDIT-INSTRUMENT |
| elicitation_surface_scanner_v1_0.py | Detect elicitation surfaces disagreeing with canonical schema | AUDIT-INSTRUMENT |
| errors_acat_V1.0.py | Shared ACAT error taxonomy | SCAFFOLD/UTIL |
| failure_taxonomy_checklist_v0_1.py | Check state for defender-agent self-sabotage patterns | AUDIT-INSTRUMENT |
| fibonacci_scaling_probe_v1_0.py | Test corpus growth/variance vs Fibonacci-scaling | CORPUS/DATA |
| finalize_archive_v1.py | Cleaned reproducible corpus + stats (drop-anchoring) | CORPUS/DATA |
| finalize_archive_v2.py | Corpus finalizer v2 (flag-don't-drop) | CORPUS/DATA |
| git_push_gate_v1_0.py | Zone-1 git-push authorization gate | PIPELINE/ORCHESTRATION |
| governance_fetcher.py | Fetch GOVERNANCE/SESSION_RITUALS as MCP resources | GOVERNANCE/DOC |
| governance_mapper_uber_v1_1.py | Governance mapper (Uber-study edition) | GOVERNANCE/DOC |
| governance_mapper_v1_0.py | Classify governance docs into lanes + GROW/KILL | GOVERNANCE/DOC |
| ground_truth_validator_V1.0.py | Validate substrate vs false temporal/deprecation claims | AUDIT-INSTRUMENT |
| haios_agent_orchestrator_v1_0_patched.py | Learning-agent orchestrator (four-phase Molt Cycle) | PIPELINE/ORCHESTRATION |
| haios_cli.py | Terminal CLI agent querying the system via repo context | SCAFFOLD/UTIL |
| haios_collab_scanner_v1_0.py | Scan gmail/github/slack/arxiv for collab candidates | PIPELINE/ORCHESTRATION |
| haios_collaboration_tracker_v3.jsx | React UI for collaboration candidates | SCAFFOLD/UTIL |
| haios_compressor_v1_0.js | Text-compression util w/ canonical preserve patterns | SCAFFOLD/UTIL |
| haios_doc_ingestor_v1_0.py | Extract typed records into Supabase; regen PROJECT_STATE | GOVERNANCE/DOC |
| haios_drive_scanner_v1_0.py | Dark-corpus scanner: census/classify (keep/archive/delete) | AUDIT-INSTRUMENT |
| haios_github_inspector.jsx | React UI inspecting canonical repos + governance files | SCAFFOLD/UTIL |
| haios_harmonizer_v1_0.py | Compute per-subsystem harmony + molt-readiness | PIPELINE/ORCHESTRATION |
| haios_notify_dispatcher_v1_0.py | Dispatch outputs to Slack/GitHub issues (gated) | PIPELINE/ORCHESTRATION |
| haios_pipeline_v1_0.py | Step-10 pipeline coordinator | PIPELINE/ORCHESTRATION |
| haios_report_writer_v1_0.py | Pipeline JSON → Markdown/Slack/HTML reports | GOVERNANCE/DOC |
| harm_independence_monitor_v1_0.py | Track PC2 harm-awareness independent of PC1 | ACAT-CORE |
| hawkins_acat_mapper_v1_0.py | Evidence-tagged ACAT→Hawkins crosswalk | GOVERNANCE/DOC |
| humility_audit_router.py | FastAPI router for humility-audit service | PIPELINE/ORCHESTRATION |
| humulity_audit_service.py | Read-only humility-audit applying REGISTERED findings | ACAT-CORE |
| message_calibration_v1_0.py | Pre-send gate scoring drafts for TRL/Tradition-11/claims | PIPELINE/ORCHESTRATION |
| mhr_question_trace_v1_0.py | Trace question→method→data chains for MHR audit | AUDIT-INSTRUMENT |
| molting_protocol_diff_v1_0.py | Compare SESSION_RITUALS protocol versions | GOVERNANCE/DOC |
| multi_provider_elicitation_client_v0_1.py | Multi-provider ACAT elicitation client | PIPELINE/ORCHESTRATION |
| p3_record_generator_v1_0.py | Generate missing P3 corpus records for LI-complete sessions | CORPUS/DATA |
| parse_wgs_z3.py | Parse #wgs-sync; upsert Z3 items into Supabase queue | CORPUS/DATA |
| phase1_prompt_integrity_checker_v1.0.py | Verify injected Phase-1 prompt vs canonical hash | AUDIT-INSTRUMENT |
| principle_analyzer_v1_0.py | Scan text vs Tier-1 principles (honored/tensions/violations) | AUDIT-INSTRUMENT |
| principle_harmonizer_v1_0.py | Map Tier-2 framework vs Tier-1 + GROW/HALT/KILL | GOVERNANCE/DOC |
| principle_harmonizer_v1_2.py | Principle harmonizer v1.2 (Master-Key edition) | GOVERNANCE/DOC |
| red_team_runner_v1_0.py | Adversarial Attacker/Defender/Auditor probes | PIPELINE/ORCHESTRATION |
| registered_findings_validator_v1_0.py | Validate REGISTERED.md: ID collisions/schema/append-only | AUDIT-INSTRUMENT |
| registry_loader.py | Parse REGISTERED.md → structured entries + validation | GOVERNANCE/DOC |
| registry_site_generator_v1_0.py | REGISTERED.md → static HTML findings site | GOVERNANCE/DOC |
| repo_discovery_v1_0.py | GitHub repo discovery/recommendation by metadata overlap | SCAFFOLD/UTIL |
| run_acat_validation_suite_v1.0.py | Orchestrate full ACAT validation suite → aggregate verdict | PIPELINE/ORCHESTRATION |
| scg_scorer.py | Shadow Calibration Gap from matched P1 + BARS observer | ACAT-CORE |
| server.py | Unified MCP server mounting Zone-1 tools | PIPELINE/ORCHESTRATION |
| skill_compression_scanner_v1_0.js | Scan SKILL.md files → compression audit report | AUDIT-INSTRUMENT |
| slack_notifier.py | Dispatch Slack notifications via webhook | SCAFFOLD/UTIL |
| supabase_corpus_connector_v1_0.py | Export acat_assessments_v1 → CSV → validator | CORPUS/DATA |
| supabase_logger.py | Idempotent upsert logger into Supabase REST | CORPUS/DATA |
| system_audit_v1_0.py | Pre-flight audit of GitHub/Supabase/Cloudflare/CURRENT.md | AUDIT-INSTRUMENT |
| system_audit_v1_1.py | Pre-ratification system audit gate (operator on current state) | AUDIT-INSTRUMENT |
| test_acat_core.py | Pytest harness for ACAT core invariants | SCAFFOLD/UTIL |
| tier1_principles.py | Canonical Tier-1 principle library | SCAFFOLD/UTIL |
| tier1_principles_stub.py | Minimal Tier-1 principle stub | SCAFFOLD/UTIL |
| tier_b_activation_gate.py | Fail-closed gate blocking Tier-B research without IRB | PIPELINE/ORCHESTRATION |
| tool_scaffolder_v1_0.py | Generate Builder v1.7-compliant tool skeletons | SCAFFOLD/UTIL |
| tool_template.py | Hybrid CLI + FastMCP dual-mode tool template | SCAFFOLD/UTIL |
| triage_log_service.py | Persist triage outputs; compute Advance Pass Rate | CORPUS/DATA |
| validate_skills.py | Validate SKILL.md YAML frontmatter vs schema | AUDIT-INSTRUMENT |
| wgs_draft_compressor_v1_0.js | Lite-pass compression of WGS close-note drafts | SCAFFOLD/UTIL |
| z2_queue_v1_0.py | Extract/dedup Zone-2 pending items from WGS | PIPELINE/ORCHESTRATION |
| zone_boundary_audit_v1_0.py | Detect Zone 1/2/3 boundary violations in artifacts/logs | AUDIT-INSTRUMENT |

**Category tally:** AUDIT-INSTRUMENT 25 · ACAT-CORE 13 · PIPELINE/ORCHESTRATION 17 · CORPUS/DATA 14 · GOVERNANCE/DOC 12 · SCAFFOLD/UTIL 12.

### 2b · Full AUDIT-INSTRUMENT set (25 — the Measure-phase suite)

`aa_principle_audit_v1_0` · `acat_merkle_auditor_v1.0` · `acat_merkle_auditor_v2_0` · `acat_protocol_auditor` · `acat_room_state_auditor_v1.0` · `acat_session_validator` · `builder_compliance_scanner_v1.0` · `circuit_validator_v1_0` · `claim_verification_check_v0_1` · `corpus_integrity_validator` · `drift_catalog_validator` · `echoes_copilot_acat_scanner_v0_1` · `elicitation_surface_scanner_v1_0` · `failure_taxonomy_checklist_v0_1` · `ground_truth_validator_V1.0` · `haios_drive_scanner_v1_0` · `mhr_question_trace_v1_0` · `phase1_prompt_integrity_checker_v1.0` · `principle_analyzer_v1_0` · `registered_findings_validator_v1_0` · `skill_compression_scanner_v1_0` · `system_audit_v1_0` · `system_audit_v1_1` · `validate_skills` · `zone_boundary_audit_v1_0`

> `echoes_copilot_acat_scanner_v0_1` is especially relevant: it already scans a **Copilot** build repo for self-reported-vs-demonstrated compliance — a ready-made instrument for the CC-vs-Copilot paired ACAT design (charter §5). Borderline instruments flagged by the catalog pass: `haios_drive_scanner` and `mhr_question_trace` (broader-than-repo scope).

### 2c · Curated core subset — which defect class each baselines

The highest-yield instruments to run first, mapped to the anchor-PDF defect classes they detect:

| Tool | What it baselines |
|---|---|
| `system_audit_v1_1.py` (+ `v1_0`) | Whole-repo system health sweep |
| `drift_catalog_validator.py` | Doc/registry drift vs canonical |
| `repo_discovery_v1_0.py` | Repo enumeration + structural map |
| `zone_boundary_audit_v1_0.py` | Zone-protocol (Z1/Z2/Z3) boundary violations |
| `registered_findings_validator_v1_0.py` | **Phantom-ID detector** — does each cited F-/IC-/H- exist in REGISTERED.md |
| `builder_compliance_scanner_v1.0.py` | Builder/agent compliance against spec |
| `governance_mapper_uber_v1_1.py` (+ `v1_0`) | Governance-doc mapping/coverage |
| `corpus_integrity_validator.py` | Corpus N/LI integrity (already proven in the v2 reconciliation) |
| `validate_skills.py` | Skill manifest validity |
| `skill_compression_scanner_v1_0.js` | Skill bloat/compression |
| `drift_catalog_validator.py` + `document_ingestor` | Reconcile vs `document-registry.yaml` |
| `ground_truth_validator_V1.0.py` | Ground-truth channel checks (SMAG-adjacent) |
| `claim_verification_check_v0_1.py` | Overclaim detection |
| `phase1_prompt_integrity_checker_v1.0.py` | Prompt-integrity (subject-side but audit-usable) |

> These map directly onto the anchor-PDF Stage-1 defect classes: `registered_findings_validator` → phantom IDs; `drift_catalog_validator` → stale canonical; `corpus_integrity_validator` → unreconciled N/LI; `zone_boundary_audit` → self-registration/overclaim.

---

## 3 · Skills

### 3a · Named HAIOS governance skills (`operations/tools/skills/`)
Genuine operator-facing skills (distinct from the ~70 tool-companion wrappers that share tool names):

| Skill | Purpose | Audit relevance |
|---|---|---|
| `humanaios-wgs-sweep` | Cross-session reconciliation over #wgs-sync; catches under-registration, dangling Z3, recurring silent failures | **Analyze-phase** lens (native IC reconciliation) |
| `humanaios-findings-scan` | Scan for findings needing registration | Sort/Set-in-Order |
| `humanaios-triage-finding` | Triage a raw finding into the registry | Standardize |
| `humanaios-realtime-drift` | Real-time drift detection | Control/Sustain |
| `humanaios-dual-architecture` | Dual-architecture (tool+skill) compliance | Standardize baseline |
| `humanaios-mhp-consultation` | MHP consultation protocol | subject |
| `humanaios_acat_learning_analysis` | ACAT learning-index analysis | ACAT-core |
| `Metaculus_main` | Metaculus forecasting integration | subject |

### 3b · Empirica plugin skills (`~/.claude/plugins/local/empirica/skills/`)
The audit **method** layer — 17 skills. Directly relevant:
- `code-audit`, `code-docs-align`, `services-auditor`, `services-audit-cron` — the empirica-native audit machinery (compose with the HAIOS instruments).
- `empirica-constitution`, `epistemic-transaction`, `epistemic-persistence-protocol` — governance/method (in use this session).
- `cortex-mailbox-send/poll`, `inbox-listener`, `dispatch-agent`, `loop-cron`, `message-cleanup`, `render`, `ewm-interview`, `eat-the-broccoli`.

---

## 4 · Workflows & CI state (a Sustain-phase finding)

**Draft workflow YAMLs that exist but are (mostly) NOT wired into any `.github/workflows/`:**

| File | Intent | Wired? |
|---|---|---|
| `operations/tools/haios-system-audit.yml` | Scheduled system audit | ❌ draft in `tools/` |
| `operations/tools/haios-corpus-integrity.yml` | Corpus integrity check | ❌ draft |
| `operations/tools/haios-harmonizer-pulse.yml` | Harmonizer pulse | ❌ draft |
| `operations/workflows/haios_audit.yml` | Audit runner | ❌ draft |
| `operations/workflows/acat_pipeline_trigger.yml` | ACAT pipeline trigger | ❌ draft (a copy IS live in `lasting-light-ai`) |
| `operations/workflows/research_agent.yml` | Research agent | ❌ draft |
| `operations/.doc-control/ci/document-control.yml` | Document-control CI | ❌ draft |

**Live GitHub Actions — CORRECTED against REMOTE (`gh api`, T1 S-070726).** The earlier rows below read the *local clones*, which are badly stale (see T1 finding). Remote/canonical CI is materially different:

| Repo | **Remote** `.github/workflows/` | Local clone showed | Cause |
|---|---|---|---|
| `operations` | **5 live** (auto-request-copilot-review, document-control, no-op-pr-guard, pages, research-validation) | *(none)* | **local clone 103 commits behind** origin/main |
| `humanaios` | 0 (only `dependabot.yml`) | 0 | genuine gap — real Sustain finding |
| `humanaios-internal` | 1 | 0 | local 34 behind |
| `lasting-light-ai` | 2 (acat-bot-test, acat_pipeline_trigger) | 2 | in sync |
| `empirica` (fork) | 3 (upstream's) | 3 | not ours |
| ACAT satellites, `docs`, `findlocaltattooartists`, `HAIOSCC`, `research` | **0** | — | real Sustain gap |

> **Correction:** operations is NOT a CI gap — remote has 5 workflows, including `document-control.yml` (the Standardize CI I was about to propose already exists) and `research-validation.yml`. The earlier "operations has no CI" note was an artifact of the stale local clone. **The real Sustain finding is (a) `humanaios` + 5 satellites have zero CI, and (b) local working copies are drifted from canonical.** See `T1_DEFECT_BASELINE_S070726.md` for the measured picture that supersedes this section.

---

## 5 · Pre-existing baseline substrate (what we calibrate *against*)

Already in `operations/` — the audit does not start from zero; it extends these:

| Artifact | Content | Role |
|---|---|---|
| `document-registry.yaml` | 34 docs, 37 excluded, **5 `needs_reconcile`**; `HAIOS-<AREA>-<nnn>` scheme; per-doc drift bytes/lines | Set-in-Order baseline |
| `DRIFT_LOG.md` | Append-only D-/C-class drift signals | Analyze input |
| `REGISTERED.md` | Findings registry (F/IC/H/NM) | phantom-ID ground truth |
| `SUBSTRATE_CAPABILITY_REGISTRY.md` | Substrate inventory + 30/60-day freshness discipline | Sustain template |
| `CURRENT.md` | Operating process — **flagged STALE (June 24)** | Shine target (corroborates PDF finding #8) |
| `DOCUMENT_CONTROL_PLAN.md` | Doc-control method | Standardize reference |

**Baseline-scale calibration:** `operations`' existing health (registry coverage, drift discipline) sets the reference sigma bar. In T1, each repo's measured defect density is compared to it → repos below the bar get the full 5S pass, repos at/above get light-touch. This is how the audit's *scale* is set by data, per the operator's ask.

---

*Zone 1 draft · S-070726 · companion to the audit charter · pending Night Z2 ratification.*
