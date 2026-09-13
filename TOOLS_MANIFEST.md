# HumanAIOS — Tool Manifest

> Rendered from `tools-manifest.yaml` (SSOT) by `.tool-control/render.py`.
> **Do not hand-edit — edit the manifest.** CI blocks when the two disagree.

**150 registered tools** · 2 MCP servers · 0 excluded · 120 carrying Builder v1.7 markers

**Status:** `draft` = registered, not yet reviewed · `review` = under owner review · `approved` = owner-verified (human gate) · `deprecated`/`archived` = retained, not for new use.

Approval is the owner's act and is never set by a scan — the same no-self-grant rule `document-registry.yaml` uses for documents.

## Summary

| metric | value |
|---|---|
| Registered tools | 150 |
| — status `draft` | 149 |
| — status `archived` | 1 |
| Builder v1.7 markers present | 120 |
| Uncategorized | 0 |
| MCP servers | 2 |

## ⚠️ Open Z2 items — self-declared authority without ratification

These tools declare Zone 2/3 (ratify / Night-executes) authority with no Z2 hash on record. Z1 cannot grant it. Each must either gain a `ratified_by` reference or have its declaration corrected to Zone 1.

| tool_id | path | zone | note |
|---|---|---|---|
| HAIOS-TOOL-088 | `tools/message_calibration_v1_0.py` | 2 | Self-declares TOOL_ZONE = 2 (ratify) with no Z2 ratification on record. Z1 cannot grant Zone 2; routed to Z2 as an open item. Resolve by either recording a `ratified_by` hash or correcting the declaration to zone 1. |

## Analytics — `analytics_tool` (1)

| tool_id | tool | path | ver | zone | status | flags | purpose |
|---|---|---|---|---|---|---|---|
| HAIOS-TOOL-023 | acat_sdt_analytics | `tools/acat_sdt_analytics_v1_0.py` | 1.0.0 | 1 | draft | — | ACAT SDT Analytics — v1.0 |

## Audit — `audit_tool` (19)

| tool_id | tool | path | ver | zone | status | flags | purpose |
|---|---|---|---|---|---|---|---|
| HAIOS-TOOL-001 | drift_monitor | `scripts/drift_monitor.py` | unversioned | 1 | draft | no-builder-markers, no-smoke-test | A6: Drift Monitor — Detect document divergence between registry and filesystem |
| HAIOS-TOOL-006 | aa_principle_audit | `tools/aa_principle_audit_v1_0.py` | 1.0.0 | 1 | draft | — | Evaluates protocol artifacts against honesty, humility, and service operational markers (AA frame). |
| HAIOS-TOOL-016 | acat_merkle_auditor | `tools/acat_merkle_auditor_v1.0.py` | 1.0.0 | 1 | draft | — | ⚠️ SUPERSEDED — Do NOT use this version |
| HAIOS-TOOL-017 | acat_merkle_auditor | `tools/acat_merkle_auditor_v2_0.py` | 2.0.0 | 1 | draft | — | ACAT Merkle Auditor — v2.0 |
| HAIOS-TOOL-020 | acat_protocol_auditor | `tools/acat_protocol_auditor.py` | 1.1.0 | 1 | draft | — | Audits session close posts against Section B protocol requirements (D-04, D-05, open/close tag balance). |
| HAIOS-TOOL-022 | acat_room_state_auditor | `tools/acat_room_state_auditor_v1.0.py` | 1.0.0 | 1 | draft | — | ACAT Room State Auditor — v1.0 |
| HAIOS-TOOL-031 | principle_compliance_bot_v1 | `tools/agents/principle_compliance_bot_v1.py` | 1.0.0 | 1 | draft | — | Agent 1.1: Principle Compliance Bot |
| HAIOS-TOOL-066 | governance_mapper | `tools/governance_mapper_uber_v1_1.py` | 1.0.0 | 1 | draft | — | Governance Mapper — v1.1 (Uber study edition, bugs fixed) |
| HAIOS-TOOL-067 | governance_mapper | `tools/governance_mapper_v1_0.py` | 1.1.0 | 1 | draft | — | Maps governance principles to structural roles across documents. |
| HAIOS-TOOL-074 | haios_drive_scanner | `tools/haios_drive_scanner_v1_0.py` | 1.0.0 | 1 | draft | — | Google Drive scanner for HumanAIOS document surfaces. |
| HAIOS-TOOL-080 | hawkins_acat_mapper | `tools/hawkins_acat_mapper_v1_0.py` | 1.0.0 | 1 | draft | — | Generates evidence-tagged crosswalk reports between ACAT dimensions and Hawkins calibration levels. |
| HAIOS-TOOL-082 | humulity_audit_service | `tools/humulity_audit_service.py` | 0.2.0 | 1 | draft | — | Humility Audit Service -- v0.2 (corrected) |
| HAIOS-TOOL-089 | mhr_question_trace | `tools/mhr_question_trace_v1_0.py` | 1.0.0 | 1 | draft | — | Traces question-source → method-design → data-output chain for Market-Harmonic Research auditability. |
| HAIOS-TOOL-091 | molting_protocol_diff | `tools/molting_protocol_diff_v1_0.py` | 1.0.0 | 1 | draft | — | Compares `SESSION_RITUALS.md` versions, classifies additive patching vs clean-layer replacement. |
| HAIOS-TOOL-100 | principle_analyzer | `tools/principle_analyzer_v1_0.py` | 1.0.0 | 1 | draft | — | Principle Analyzer — v1.0 |
| HAIOS-TOOL-101 | principle_harmonizer | `tools/principle_harmonizer_v1_0.py` | 1.1.0 | 1 | draft | — | Harmonizes the principle layer across governance files, surfaces drift. |
| HAIOS-TOOL-102 | principle_harmonizer | `tools/principle_harmonizer_v1_2.py` | 1.2.0 | 1 | draft | — | Principle Harmonizer — v1.2 |
| HAIOS-TOOL-115 | skill_compression_scanner_v1_0 | `tools/skill_compression_scanner_v1_0.js` | unversioned | 1 | draft | no-builder-markers, no-smoke-test | — |
| HAIOS-TOOL-143 | zone_boundary_audit | `tools/zone_boundary_audit_v1_0.py` | 1.0.0 | 1 | draft | — | Detects Zone 1/2/3 boundary violations in workflow artifacts and operator logs. |

## Calibration — `calibration_tool` (16)

| tool_id | tool | path | ver | zone | status | flags | purpose |
|---|---|---|---|---|---|---|---|
| HAIOS-TOOL-043 | ci_predict_consolidate | `tools/ci_predict_consolidate_v1_0.py` | 1.0.0 | 1 | draft | — | ci_predict_consolidate_v1_0.py |
| HAIOS-TOOL-044 | ci_predict_pin | `tools/ci_predict_pin_v1_0.py` | 1.0.0 | 1 | draft | — | ci_predict_pin_v1_0.py |
| HAIOS-TOOL-045 | ci_predict_resolve | `tools/ci_predict_resolve_v1_0.py` | 1.0.0 | 1 | draft | — | ci_predict_resolve_v1_0.py |
| HAIOS-TOOL-052 | dimension_attribution | `tools/dimension_attribution_v1_0.py` | 1.0.0 | 1 | draft | — | dimension_attribution_v1_0.py |
| HAIOS-TOOL-057 | echoes_copilot_acat_scanner | `tools/echoes_copilot_acat_scanner_v0_1.py` | 1.0.0 | 1 | draft | — | echoes_copilot_acat_scanner_v0_1.py |
| HAIOS-TOOL-087 | lifecycle_predict | `tools/lifecycle_predict_v1_0.py` | 1.0.0 | 1 | draft | — | lifecycle_predict_v1_0.py |
| HAIOS-TOOL-093 | nf_ledger_cli | `tools/nf_ledger_cli_v1_0.py` | 1.0.0 | 1 | draft | — | nf_ledger_cli_v1_0.py |
| HAIOS-TOOL-094 | nf_ledger_v0_1 | `tools/nf_ledger_v0_1.py` | unversioned | 1 | draft | no-builder-markers, no-smoke-test | nf_ledger_v0_1.py — NF_LEDGER (calibration ledger, Brier) for the Phase 2 mesh pins. |
| HAIOS-TOOL-111 | scg_scorer | `tools/scg_scorer.py` | 1.0.0 | 1 | draft | — | scg_scorer.py — Shadow Calibration Gap Scoring Tool |
| HAIOS-TOOL-117 | smag_consolidate | `tools/smag_consolidate_v1_0.py` | 1.0.0 | 1 | draft | — | smag_consolidate — drain SMAG rows from the #103 tracking issue into the ledger. |
| HAIOS-TOOL-118 | smag_gap_analysis | `tools/smag_gap_analysis_v1_0.py` | 1.0.0 | 1 | draft | — | smag_gap_analysis — the ANALYZE step of the recursive-learning loop. |
| HAIOS-TOOL-119 | smag_gap_analyzer | `tools/smag_gap_analyzer.py` | 1.0.0 | 1 | draft | — | smag_gap_analyzer — LLM-enriched ACAT Core-6 gap classification and prediction. |
| HAIOS-TOOL-120 | smag_pilot_capture | `tools/smag_pilot_capture_v1_0.py` | 1.0.0 | 1 | draft | — | smag_pilot_capture_v1_0.py |
| HAIOS-TOOL-121 | smag_pr_autocapture | `tools/smag_pr_autocapture_v1_0.py` | 1.0.0 | 1 | draft | — | smag_pr_autocapture_v1_0 — auto-capture a SMAG pilot row from a merged PR |
| HAIOS-TOOL-123 | smag_resolve | `tools/smag_resolve_v1_0.py` | 1.0.0 | 1 | draft | — | smag_resolve — fix SMAG capture timing by recording CI outcome AFTER checks resolve. |
| HAIOS-TOOL-144 | copilot_acat_scanner | `tools/copilot_acat_scanner_v1_0.py` | 1.0.0 | 1 | draft | — | copilot_acat_scanner_v1_0.py |

## Connectors — `connector_tool` (11)

| tool_id | tool | path | ver | zone | status | flags | purpose |
|---|---|---|---|---|---|---|---|
| HAIOS-TOOL-014 | acat_mcp_full_wrapper | `tools/acat_mcp_full_wrapper_v1.2.py` | 1.0.0 | 1 | draft | — | ⚠️ SUPERSEDED — Do NOT use this version |
| HAIOS-TOOL-015 | acat_mcp_full_wrapper_v1_2_patched | `tools/acat_mcp_full_wrapper_v1_2_patched.py` | 1.0.0 | 1 | draft | — | acat_mcp_full_wrapper_v1.2.py |
| HAIOS-TOOL-065 | governance_fetcher | `tools/governance_fetcher.py` | 1.1.0 | 1 | draft | — | Fetches GOVERNANCE.md and SESSION_RITUALS.md from GitHub raw content. |
| HAIOS-TOOL-070 | haios_cli | `tools/haios_cli.py` | 1.0.0 | 1 | draft | — | Terminal CLI — query the full HumanAIOS system using live GitHub context + Claude API. Modes: `ask` (default), `run`, `check`, `chat`. |
| HAIOS-TOOL-076 | haios_notify_dispatcher | `tools/haios_notify_dispatcher_v1_0.py` | 1.0.0 | 1 | draft | — | HAIOS Notify Dispatcher — v1.0 |
| HAIOS-TOOL-092 | multi_provider_elicitation_client | `tools/multi_provider_elicitation_client_v0_1.py` | 1.0.0 | 1 | draft | — | multi_provider_elicitation_client_v0_1.py |
| HAIOS-TOOL-097 | parse_wgs_z3 | `tools/parse_wgs_z3.py` | 1.0.0 | 1 | draft | — | parse_wgs_z3.py |
| HAIOS-TOOL-116 | slack_notifier | `tools/slack_notifier.py` | 1.1.0 | 1 | draft | — | Dispatches Slack notifications via incoming webhook using stdlib urllib. |
| HAIOS-TOOL-124 | smag_to_empirica_connector | `tools/smag_to_empirica_connector.py` | unversioned | 1 | draft | no-builder-markers, no-smoke-test | smag_to_empirica_connector — wire SMAG rows to empirica CLI for trajectory generation. |
| HAIOS-TOOL-126 | supabase_corpus_connector | `tools/supabase_corpus_connector_v1_0.py` | 1.0.0 | 1 | draft | — | Supabase Corpus Connector — v1.0 |
| HAIOS-TOOL-127 | supabase_logger | `tools/supabase_logger.py` | 1.1.0 | 1 | draft | — | Logs notifications to Supabase with idempotent upsert (claim-then-act pattern). |

## Dependencies (imported, not invoked) — `dependency` (6)

| tool_id | tool | path | ver | zone | status | flags | purpose |
|---|---|---|---|---|---|---|---|
| HAIOS-TOOL-004 | acat_conversational_keywords | `tools/ACAT_CONVERSATIONAL_KEYWORDS_V1_0_S072126-01.py` | 1.0.0 | 1 | draft | — | ACAT Conversational Register Keyword Set — v1.0 |
| HAIOS-TOOL-059 | errors_acat | `tools/errors_acat_V1.0.py` | 1.0.0 | 1 | draft | — | ACAT Error Taxonomy — v1.0 |
| HAIOS-TOOL-106 | registry_loader | `tools/registry_loader.py` | 1.0.0 | 1 | draft | — | ACAT Registry Loader |
| HAIOS-TOOL-132 | tier1_principles | `tools/tier1_principles.py` | 1.0.0 | 1 | draft | — | tier1_principles.py — HumanAIOS Tier 1 Principle Library |
| HAIOS-TOOL-133 | tier1_principles_stub | `tools/tier1_principles_stub.py` | 1.0.0 | 1 | draft | — | tier1_principles.py — stub for smoke test execution. |
| HAIOS-TOOL-152 | strict_yaml | `.doc-control/strict_yaml.py` | unversioned | 1 | draft | no-builder-markers | A YAML loader that refuses duplicate mapping keys, for registry consumers. |

## Diagnostics — `diagnostic_tool` (14)

| tool_id | tool | path | ver | zone | status | flags | purpose |
|---|---|---|---|---|---|---|---|
| HAIOS-TOOL-009 | acat_dimension_scorer | `tools/acat_dimension_scorer.py` | 1.2.0 | 1 | draft | — | Scores ACAT dimensions from session records; Bayesian posterior intervals per dimension; D-COMP probability. |
| HAIOS-TOOL-011 | acat_document_analyzer | `tools/acat_document_analyzer.py` | 1.1.0 | 1 | draft | — | Keyword-vector scoring (TF-IDF surrogate) for dimensional evidence density; batch mode for corpora. |
| HAIOS-TOOL-012 | acat_document_analyzer | `tools/acat_document_analyzer_v1_2_ARCHIVED_2026-07-16.py` | 1.3.0 | 1 | archived | no-builder-markers | ⚠️  **DO NOT USE** — ARCHIVED (2026-07-16) |
| HAIOS-TOOL-018 | acat_phase_shift_analyzer | `tools/acat_phase_shift_analyzer_v1_0.py` | 1.0.0 | 1 | draft | — | Computes per-agent and per-provider phase shift metrics: LI distributions, stress-response deltas. |
| HAIOS-TOOL-039 | bpl_signal_extractor | `tools/bpl_signal_extractor_v1_0.py` | 1.0.0 | 1 | draft | — | Extracts candidate behavioral-language pattern tokens from response corpora under perturbation sets (H-BPL-01). |
| HAIOS-TOOL-041 | carry_tracker | `tools/carry_tracker_v1_0.py` | 1.1.0 | 1 | draft | — | Reads WGS posts, counts sessions-carried per item, flags WARN at N>5 and ESCALATE at N>10. |
| HAIOS-TOOL-049 | corpus_delta_analyzer | `tools/corpus_delta_analyzer.py` | 1.0.0 | 1 | draft | — | Diffs two corpus CSV snapshots; surfaces LI regression, D-04 patterns, and population change trajectories. |
| HAIOS-TOOL-061 | fibonacci_scaling_probe | `tools/fibonacci_scaling_probe_v1_0.py` | 1.0.0 | 1 | draft | — | Tests whether corpus growth and variance patterns match or diverge from Fibonacci-like scaling assumptions. |
| HAIOS-TOOL-079 | harm_independence_monitor | `tools/harm_independence_monitor_v1_0.py` | 1.0.0 | 1 | draft | — | Tracks PC2-linked Harm Independence Metric (HIM) signal independently of PC1 movement. |
| HAIOS-TOOL-108 | repo_discovery | `tools/repo_discovery_v1_0.py` | 1.0.0 | 1 | draft | — | Repository discovery and mapping across humanaios-ui and LastingLightAI orgs. |
| HAIOS-TOOL-109 | repo_health | `tools/repo_health.py` | 1.0.0 | 1 | draft | — | repo_health.py — a basic, offline, deterministic self-diagnostic for a HumanAIOS repo. |
| HAIOS-TOOL-138 | tool_trace_reader | `tools/tool_trace_reader_v1_0.py` | 1.0.0 | 1 | draft | — | tool_trace_reader_v1_0.py |
| HAIOS-TOOL-142 | z2_queue | `tools/z2_queue_v1_0.py` | 1.1.0 | 1 | draft | — | Extracts Zone 2 pending items from WGS posts, deduplicates, surfaces oldest-first, flags ≥3 sessions unresolved. |
| HAIOS-TOOL-156 | resource_census | `tools/resource_census_v0_1.py` | 0.1.0 | 1 | draft | — | resource_census_v0_1.py — measure the resource state of the operations tree. |

## Governance — `governance_tool` (7)

| tool_id | tool | path | ver | zone | status | flags | purpose |
|---|---|---|---|---|---|---|---|
| HAIOS-TOOL-051 | decision_relay | `tools/decision_relay.py` | unversioned | 1 | draft | no-builder-markers, no-smoke-test | decision_relay.py — routes Z2 decisions from the Intent-OS board to a GitHub PR, behind ngrok. |
| HAIOS-TOOL-090 | molt_cycle | `tools/molt_cycle.py` | unversioned | 1 | draft | no-builder-markers, no-smoke-test | molt_cycle.py — READ + PROPOSE phases only (Tier 0). Never applies. |
| HAIOS-TOOL-151 | doc_review_scheduler | `.doc-control/review.py` | 1.0.0 | 1 | draft | no-builder-markers | Document review scheduler — record a review, derive the next one, triage the backlog. |
| HAIOS-TOOL-153 | z1_ratify | `.z1-control/ratify.py` | 1.1.0 | 2 | draft | no-builder-markers | Record a Z2 decision on a candidate block. Run by Z2, not by Z1. |
| HAIOS-TOOL-154 | z1_inbox_renderer | `.z1-control/render.py` | 1.0.0 | 1 | draft | no-builder-markers | Render Z1_INBOX_INDEX.md from z1-inbox/INDEX.yaml. |
| HAIOS-TOOL-155 | z1_inbox_validator | `.z1-control/validate.py` | 1.0.0 | 1 | draft | no-builder-markers | z1-inbox/ is where Z1 stages proposals for Z2. Until now nothing said which of |
| HAIOS-TOOL-157 | resource_ledger | `tools/resource_ledger_v0_1.py` | 0.1.0 | 1 | draft | — | resource_ledger_v0_1.py — append-only, hash-chained ledger of resource claims, |

## Infrastructure — `infrastructure_tool` (20)

| tool_id | tool | path | ver | zone | status | flags | purpose |
|---|---|---|---|---|---|---|---|
| HAIOS-TOOL-010 | acat_doc | `tools/acat_doc_v1.py` | 1.0.0 | 1 | draft | — | ACAT document spec baseline. |
| HAIOS-TOOL-034 | anthropic_client_fence_fix | `tools/anthropic_client_fence_fix.py` | 1.0.0 | 1 | draft | — | — |
| HAIOS-TOOL-036 | assess_router_Z2_assessment | `tools/assess_router_Z2_assessment.py` | 1.0.0 | 1 | draft | — | assess_router_Z2_assessment.py — FastAPI router for Z2 assessment endpoint. |
| HAIOS-TOOL-037 | assess_router_new_z2_assess_01 | `tools/assess_router_new_Z2-ASSESS-01.py` | 1.0.0 | 1 | draft | — | — |
| HAIOS-TOOL-054 | document_ingestor | `tools/document_ingestor_v1_0.py` | 1.0.0 | 1 | draft | — | Base document ingestion layer. |
| HAIOS-TOOL-055 | document_ingestor | `tools/document_ingestor_v1_0_patched.py` | 1.0.0 | 1 | draft | — | TOOL_NAME = "document_ingestor" |
| HAIOS-TOOL-062 | finalize_archive_v1 | `tools/finalize_archive_v1.py` | 1.0.0 | 1 | draft | — | ⚠️ SUPERSEDED — Do NOT use this version |
| HAIOS-TOOL-063 | finalize_archive_v2 | `tools/finalize_archive_v2.py` | 1.0.0 | 1 | draft | — | finalize_archive_v2 — ACAT archive finalizer v2 (2b honest amendment, S-070226) |
| HAIOS-TOOL-069 | haios_agent_orchestrator_v1_0_patched | `tools/haios_agent_orchestrator_v1_0_patched.py` | 1.0.0 | 1 | draft | — | Agent orchestration layer for multi-tool dispatch. |
| HAIOS-TOOL-072 | haios_compressor_v1_0 | `tools/haios_compressor_v1_0.js` | unversioned | 1 | draft | no-builder-markers, no-smoke-test | — |
| HAIOS-TOOL-081 | humility_audit_router | `tools/humility_audit_router.py` | 0.1.0 | 1 | draft | — | humility_audit_router.py — FastAPI router for the humility audit endpoint. |
| HAIOS-TOOL-085 | intent_object_population_v1_0 | `tools/intent_object_population_V1.0.py` | 1.0.0 | 1 | draft | — | intent_object_population_v1_0.py |
| HAIOS-TOOL-113 | seed_org_defaults | `tools/seed_org_defaults.py` | 1.0 | 1 | draft | — | seed_org_defaults.py — seed standard community-health files to mesh repos. |
| HAIOS-TOOL-114 | server | `tools/server.py` | 1.0.0 | 1 | draft | — | Mounts all Zone 1 tools with prefixed names so the agent sees one server: |
| HAIOS-TOOL-137 | tool_trace_hook | `tools/tool_trace_hook_v1_0.py` | 1.0.0 | 1 | draft | — | tool_trace_hook_v1_0.py |
| HAIOS-TOOL-139 | triage_log_service | `tools/triage_log_service.py` | 1.0.0 | 1 | draft | — | Triage Log Service |
| HAIOS-TOOL-141 | wgs_draft_compressor_v1_0 | `tools/wgs_draft_compressor_v1_0.js` | unversioned | 1 | draft | no-builder-markers, no-smoke-test | — |
| HAIOS-TOOL-145 | doc_registry_renderer | `.doc-control/render.py` | 1.0.0 | 1 | draft | no-builder-markers | Render CONTROLLED_DOCUMENTS.md from document-registry.yaml. |
| HAIOS-TOOL-147 | tool_manifest_renderer | `.tool-control/render.py` | 1.0.0 | 1 | draft | no-builder-markers | Render TOOLS_MANIFEST.md from tools-manifest.yaml. |
| HAIOS-TOOL-148 | tool_manifest_scanner | `.tool-control/scan.py` | 1.1.0 | 1 | draft | no-builder-markers | Walks the registered tool roots, extracts each tool's declared metadata, and |

## Monitoring — `monitoring_tool` (3)

| tool_id | tool | path | ver | zone | status | flags | purpose |
|---|---|---|---|---|---|---|---|
| HAIOS-TOOL-029 | api_monitoring_bot_v1 | `tools/agents/api_monitoring_bot_v1.py` | 1.0.0 | 1 | draft | — | Agent 1.2: API Monitoring Bot |
| HAIOS-TOOL-030 | monitor_stability_v1 | `tools/agents/monitor_stability_v1.py` | 1.0.0 | 1 | draft | — | Monitoring Dashboard: Phase 1/2 Stability |
| HAIOS-TOOL-048 | clone_sync_health | `tools/clone_sync_health_v1_0.py` | 1.0.0 | 1 | draft | — | Clone Sync Health — v1.0 |

## Orchestration — `orchestrator_tool` (6)

| tool_id | tool | path | ver | zone | status | flags | purpose |
|---|---|---|---|---|---|---|---|
| HAIOS-TOOL-071 | haios_collab_scanner | `tools/haios_collab_scanner_v1_0.py` | 1.0.0 | 1 | draft | — | Scans for collaboration signals across repositories and documents. |
| HAIOS-TOOL-075 | haios_harmonizer | `tools/haios_harmonizer_v1_0.py` | 1.0.0 | 1 | draft | — | System-level harmonization across governance surfaces. |
| HAIOS-TOOL-077 | haios_pipeline | `tools/haios_pipeline_v1_0.py` | 1.0.0 | 1 | draft | — | HAIOS Pipeline Coordinator — v1.0 |
| HAIOS-TOOL-110 | run_acat_validation_suite | `tools/run_acat_validation_suite_v1.0.py` | 1.0.0 | 1 | draft | — | ACAT Validation Suite Orchestrator — v1.0 |
| HAIOS-TOOL-112 | scheduled_audit_runner | `tools/scheduled_audit_runner_v1_0.py` | 1.0.0 | 1 | draft | — | scheduled_audit_runner_v1_0 — Measure+Issue automated audit loop orchestrator |
| HAIOS-TOOL-128 | system_audit | `tools/system_audit_v1_0.py` | 1.1.0 | 1 | draft | — | ⚠️ SUPERSEDED — Do NOT use this version |

## Pipelines — `pipeline_tool` (4)

| tool_id | tool | path | ver | zone | status | flags | purpose |
|---|---|---|---|---|---|---|---|
| HAIOS-TOOL-002 | intake_pipeline | `scripts/intake_pipeline.py` | unversioned | 1 | draft | no-builder-markers, no-smoke-test | A4: Intake Pipeline Processor |
| HAIOS-TOOL-019 | acat_pipeline | `tools/acat_pipeline_v0_1.py` | 1.0.0 | 1 | draft | — | acat_pipeline_v0_1.py |
| HAIOS-TOOL-073 | haios_doc_ingestor | `tools/haios_doc_ingestor_v1_0.py` | 1.0.0 | 1 | draft | — | Document ingestion pipeline for HumanAIOS surfaces. |
| HAIOS-TOOL-105 | registry_issue_compiler | `tools/registry_issue_compiler_v1_0.py` | 1.0.0 | 1 | draft | — | Registry Issue Compiler - v1.0 |

## Reporting — `reporting_tool` (5)

| tool_id | tool | path | ver | zone | status | flags | purpose |
|---|---|---|---|---|---|---|---|
| HAIOS-TOOL-003 | repurpose | `scripts/repurpose.py` | unversioned | 1 | draft | no-builder-markers, no-smoke-test | repurpose.py — one Witness Stand markdown post -> four channel drafts. |
| HAIOS-TOOL-032 | rentahuman_validation_bot_v1 | `tools/agents/rentahuman_validation_bot_v1.py` | 1.0.0 | 1 | draft | — | Agent 2.2: RentAHuman Validation Bot |
| HAIOS-TOOL-033 | substack_content_agent_v1 | `tools/agents/substack_content_agent_v1.py` | 1.0.0 | 1 | draft | — | Agent 2.1: Substack Content Agent |
| HAIOS-TOOL-078 | haios_report_writer | `tools/haios_report_writer_v1_0.py` | 1.0.0 | 1 | draft | — | HAIOS Report Writer — v1.0 |
| HAIOS-TOOL-107 | registry_site_generator | `tools/registry_site_generator_v1_0.py` | 1.0.0 | 1 | draft | — | Reads REGISTERED.md, parses F-class / IC-class / H-class entries, |

## Research — `research_tool` (9)

| tool_id | tool | path | ver | zone | status | flags | purpose |
|---|---|---|---|---|---|---|---|
| HAIOS-TOOL-005 | main | `tools/Metaculus/main.py` | 1.0.0 | 1 | draft | — | Session: S-060526-NN-forecast-bot-comment-fix |
| HAIOS-TOOL-007 | acat_adversarial_execution | `tools/acat_adversarial_execution_v1.py` | 1.0.0 | 1 | draft | no-builder-markers, no-smoke-test | ACAT Adversarial Test Execution v1.0 — Execute against Live Scorer |
| HAIOS-TOOL-008 | acat_adversarial_suite | `tools/acat_adversarial_suite_v1.py` | 1.0.0 | 1 | draft | no-builder-markers, no-smoke-test | ACAT Adversarial Test Suite v1.0 — Priority 6 EU AI Act Compliance |
| HAIOS-TOOL-013 | acat_full_adversarial_suite_execution | `tools/acat_full_adversarial_suite_execution.py` | 1.0.0 | 1 | draft | no-builder-markers, no-smoke-test | Full 27-Test Adversarial Suite Execution Against Patched ACAT Scorer |
| HAIOS-TOOL-035 | app_mapping_tool | `tools/app_mapping_tool.py` | 0.1.4 | 1 | draft | — | App Mapping Tool — v0.1.4 |
| HAIOS-TOOL-058 | elicitation_surface_scanner | `tools/elicitation_surface_scanner_v1_0.py` | 1.0.0 | 1 | draft | — | Elicitation Surface Scanner — v1.0 |
| HAIOS-TOOL-095 | p3_record_generator | `tools/p3_record_generator_v1_0.py` | 1.0.0 | 1 | draft | — | p3_record_generator_v1_0.py |
| HAIOS-TOOL-103 | red_team_runner | `tools/red_team_runner_v1_0.py` | 1.0.0 | 1 | draft | — | Red Team Runner — v1.0 |
| HAIOS-TOOL-125 | smc_census_copilot_v0_1 | `tools/smc_census_copilot_v0_1.py` | unversioned | 1 | draft | no-builder-markers, no-smoke-test | Shared-Memory Census (SMC) v0.1. |

## Security gates — `security_gate_tool` (10)

| tool_id | tool | path | ver | zone | status | flags | purpose |
|---|---|---|---|---|---|---|---|
| HAIOS-TOOL-038 | behavioral_compliance_gate | `tools/behavioral_compliance_gate_v1_0.py` | 1.0.0 | 1 | draft | — | behavioral_compliance_gate_v1_0.py |
| HAIOS-TOOL-042 | cascade_guard | `tools/cascade_guard.py` | unversioned | 1 | draft | no-builder-markers, no-smoke-test | cascade_guard.py — the witch-hunt failure mode as two executable invariants. |
| HAIOS-TOOL-064 | git_push_gate | `tools/git_push_gate_v1_0.py` | 1.0.0 | 1 | draft | — | Zone 1 push authorization gate — enforces Zone 1/2/3 file rules before any commit per `Z3_PROTOCOL.md`. |
| HAIOS-TOOL-083 | ic_scope_check | `tools/ic_scope_check.py` | unversioned | 1 | draft | no-builder-markers, no-smoke-test | IC-SCOPE-05 gate — no tool touches a client system without a signed |
| HAIOS-TOOL-086 | jester_invariants | `tools/jester_invariants.py` | unversioned | 1 | draft | no-builder-markers, no-smoke-test | jester_invariants.py — JESTER-01..07 as executable invariants over the |
| HAIOS-TOOL-088 | message_calibration | `tools/message_calibration_v1_0.py` | 1.0.0 | 2 | draft | **pending-Z2** | Message calibration scoring tool. |
| HAIOS-TOOL-099 | pre_push_gate | `tools/pre_push_gate.py` | 1.1.0 | 1 | draft | — | Pre-Push Gate — v1.1 |
| HAIOS-TOOL-122 | smag_predict_lint | `tools/smag_predict_lint.py` | 1.0.0 | 1 | draft | — | smag_predict_lint.py |
| HAIOS-TOOL-129 | system_audit | `tools/system_audit_v1_1.py` | 1.1.0 | 1 | draft | — | System Audit — v1.1 |
| HAIOS-TOOL-134 | tier_b_activation_gate | `tools/tier_b_activation_gate.py` | 1.0.0 | 1 | draft | — | tier_b_activation_gate.py |

## Templates — `template_tool` (2)

| tool_id | tool | path | ver | zone | status | flags | purpose |
|---|---|---|---|---|---|---|---|
| HAIOS-TOOL-135 | tool_scaffolder | `tools/tool_scaffolder_v1_0.py` | 1.0.0 | 1 | draft | — | Scaffolds new Builder v1.7-compliant tools from template. |
| HAIOS-TOOL-136 | tool_template | `tools/tool_template.py` | 1.1.0 | 1 | draft | — | Single Python module with two entrypoints: |

## Validation — `validation_tool` (17)

| tool_id | tool | path | ver | zone | status | flags | purpose |
|---|---|---|---|---|---|---|---|
| HAIOS-TOOL-021 | acat_psychometric_validator | `tools/acat_psychometric_validator_v1_0.py` | 1.0.0 | 1 | draft | — | Recomputes reliability (α), PCA, and bi-factor metrics; produces reproducible method report artifacts. |
| HAIOS-TOOL-024 | acat_session_validator | `tools/acat_session_validator.py` | 1.1.0 | 1 | draft | — | Validates session record Phase 1/3 structure, D-COMP declarations, and Merkle chain integrity. |
| HAIOS-TOOL-040 | builder_compliance_scanner | `tools/builder_compliance_scanner_v1.0.py` | 1.0.0 | 1 | draft | — | Builder Compliance Scanner - v1.0 |
| HAIOS-TOOL-046 | circuit_validator | `tools/circuit_validator_v1_0.py` | 1.0.0 | 1 | draft | — | Circuit Validator — v1.0 |
| HAIOS-TOOL-047 | claim_verification_check | `tools/claim_verification_check_v0_1.py` | 1.0.0 | 1 | draft | — | claim_verification_check_v0_1.py |
| HAIOS-TOOL-050 | corpus_integrity_validator | `tools/corpus_integrity_validator.py` | 1.1.0 | 1 | draft | — | Validates ACAT corpus CSV: missing fields, out-of-range scores, LI correctness, Phase pairing, D-04 monotonicity. |
| HAIOS-TOOL-053 | doc_lifecycle_lint | `tools/doc_lifecycle_lint.py` | unversioned | 1 | draft | no-builder-markers, no-smoke-test | doc_lifecycle_lint.py — Filing / Processing / Consumption / Production (FPCP) for docs/. |
| HAIOS-TOOL-056 | drift_catalog_validator | `tools/drift_catalog_validator.py` | 1.1.0 | 1 | draft | — | Validates drift codes in close posts; cross-session frequency tracking for D-04 pattern clusters. |
| HAIOS-TOOL-060 | failure_taxonomy_checklist | `tools/failure_taxonomy_checklist_v0_1.py` | 1.0.0 | 1 | draft | — | failure_taxonomy_checklist_v0_1.py |
| HAIOS-TOOL-068 | ground_truth_validator | `tools/ground_truth_validator_V1.0.py` | 1.0.0 | 1 | draft | — | ACAT Ground Truth Validator — v0.6 |
| HAIOS-TOOL-084 | intake_schema_v0_2 | `tools/intake_schema_v0_2.py` | 1.0.0 | 1 | draft | — | Intake Schema v0.2 |
| HAIOS-TOOL-098 | phase1_prompt_integrity_checker | `tools/phase1_prompt_integrity_checker_v1.0.py` | 1.0.0 | 1 | draft | — | Phase 1 Prompt Integrity Checker - v1.0 |
| HAIOS-TOOL-104 | registered_findings_validator | `tools/registered_findings_validator_v1_0.py` | 1.0.0 | 1 | draft | — | Registered Findings Validator — v1.0 |
| HAIOS-TOOL-140 | validate_skills | `tools/validate_skills.py` | 1.0.0 | 1 | draft | — | validate_skills.py |
| HAIOS-TOOL-146 | doc_control_validator | `.doc-control/validate.py` | 1.1.0 | 1 | draft | no-builder-markers, no-smoke-test | Enforces the mechanical controlled-document rules from DOCUMENT_CONTROL_PLAN.md: |
| HAIOS-TOOL-149 | tool_control_selftest | `.tool-control/selftest.py` | 1.1.0 | 1 | draft | no-builder-markers | Adversarial self-test for the tool-control gate: prove every rule can FAIL. |
| HAIOS-TOOL-150 | tool_manifest_validator | `.tool-control/validate.py` | 1.1.0 | 1 | draft | no-builder-markers | The merge gate for `tools-manifest.yaml`, built to the same contract as |

## MCP servers (2)

External tool surfaces the agent may call. Registered here because an MCP server is a tool with a network boundary: `scope` and `data_classification` must be set by an owner before a server can reach `approved`.

| server_id | server | transport | endpoint | zone | status | scope | data classification |
|---|---|---|---|---|---|---|---|
| HAIOS-MCP-001 | rentahuman | stdio | `npx -y rentahuman-mcp` | 1 | draft | unscoped — set before approval | UNCLASSIFIED — set before approval |
| HAIOS-MCP-002 | supabase | http | `https://mcp.supabase.com/mcp?project_ref=ksinisdzgtnqzsymhfya` | 1 | draft | unscoped — set before approval | UNCLASSIFIED — set before approval |

---

**Scan roots:** `tools`, `scripts`, `bin`, `.tool-control`, `.doc-control`, `.z1-control` · **excluded dirs:** `.git`, `__pycache__`, `node_modules`, `skills`, `tests` (`tools/skills/` is governed by `SKILL_REGISTRY.md`). Also not tools, mirroring `_skip_reason` in `tools/builder_compliance_scanner_v1.0.py`: `test_*`/`*_test` modules, `__init__.py`, and `_`-prefixed private/shared helper directories. Archived tools stay registered at `status: archived`.

## Category vocabulary

A category says what a tool **does to the system**, not what subject it concerns — "ACAT" is a subject, `audit_tool` is a role. The set is closed: an entry outside it, or left `unclassified`, fails the gate. Extending it is a reviewed change to `CATEGORIES` in `.tool-control/scan.py`.

| category | meaning | count |
|---|---|---|
| `analytics_tool` | Statistical or psychometric computation over collected data. | 1 |
| `audit_tool` | Audits artifacts or state against rules and reports findings. | 19 |
| `calibration_tool` | Pins, resolves or scores predictions against outcomes. | 16 |
| `connector_tool` | Talks to an external service (Supabase, Slack, GitHub, LLM APIs). | 11 |
| `dependency` | Imported by other tools; not invoked directly. | 6 |
| `diagnostic_tool` | Measures and surfaces signals without gating anything. | 14 |
| `governance_tool` | Operates the governance machinery: registries, molts, routing. | 7 |
| `infrastructure_tool` | Internal plumbing: servers, routers, hooks, ingestion, scaffolding. | 20 |
| `monitoring_tool` | Watches a surface over time and raises alerts. | 3 |
| `orchestrator_tool` | Runs other tools or agents in sequence. | 6 |
| `pipeline_tool` | Multi-stage processing of a corpus or record set. | 4 |
| `reporting_tool` | Produces human-facing output: reports, sites, drafts. | 5 |
| `research_tool` | A research instrument: adversarial suites, elicitation, experiments. | 9 |
| `security_gate_tool` | Blocks an action (push, send, activation) on policy. | 10 |
| `template_tool` | A scaffold or template for producing new tools. | 2 |
| `validation_tool` | Validates the structure or content of an input; pass/fail. | 17 |

**Builder v1.7 markers** is a cheap presence heuristic (header, `TOOL_NAME`, `TOOL_VERSION`, main guard, smoke test) computed over every registered tool, including the `.js`/`.sh` and `scripts/`/`bin/` files. It is **not** the compliance verdict: the authoritative check is `tools/builder_compliance_scanner_v1.0.py`, gated by `.github/workflows/builder-lint.yml` over its own corpus (`tools/**`, excluding tests, archived and private modules). Where the two differ, the scanner is right.

**Adding a tool:** write it to the Builder v1.7 standard (`TOOLS_TEMPLATE.md`), run `python3 .tool-control/scan.py` to register it, then set its curated fields (owner, purpose, category) in `tools-manifest.yaml`. CI blocks an unregistered tool.
