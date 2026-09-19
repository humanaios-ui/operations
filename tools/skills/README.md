# HumanAIOS Operations — Skills Directory

**Canonical URL:** `https://raw.githubusercontent.com/humanaios-ui/operations/main/tools/skills/README.md`
**Last updated:** 2026-06-10 · S-060926-02
**Skills count:** 67
**Structure:** One folder per skill — `tools/skills/<skill_name>/SKILL.md`
**Template:** 5-section standard — Description · Purpose · Parameters & Inputs · Outputs · Usage Example

-----

## Install

```bash
# All skills
npx skills add humanaios-ui/operations/tools/skills

# Single skill
npx skills add humanaios-ui/operations/tools/skills --skill haios_cli
```

Each skill folder contains one `SKILL.md`. All tools support `--smoke-test` and `--help`.

-----

## Quick reference

```bash
# Entry point — query the full HumanAIOS system
python tools/haios_cli.py "what are my open Zone 2 items?"

# Run the full validation suite in one pass
python tools/run_acat_validation_suite.py --input session_record.json

# Pre-push authorization gate
python tools/git_push_gate_v1_0.py --staged-files "$(git diff --cached --name-only)"
```

-----

## 1. Entry point & CLI

|Skill folder|Tool          |One-line purpose                                                                   |
|------------|--------------|-----------------------------------------------------------------------------------|
|`haios_cli` |`haios_cli.py`|Terminal CLI — query the full HumanAIOS system via Claude API + live GitHub context|

-----

## 2. Governance & session infrastructure

|Skill folder                 |Tool                            |One-line purpose                                                                  |
|-----------------------------|--------------------------------|----------------------------------------------------------------------------------|
|`git_push_gate_v1_0`         |`git_push_gate_v1_0.py`         |Zone 1 push authorization gate — enforces Zone 1/2/3 file rules before any commit |
|`carry_tracker_v1_0`         |`carry_tracker_v1_0.py`         |Reads WGS posts, counts sessions-carried per item, flags WARN >5 / ESCALATE >10   |
|`z2_queue_v1_0`              |`z2_queue_v1_0.py`              |Extracts Zone 2 pending items from WGS posts, deduplicates, surfaces oldest-first |
|`zone_boundary_audit_v1_0`   |`zone_boundary_audit_v1_0.py`   |Detects Zone 1/2/3 boundary violations in workflow artifacts                      |
|`governance_mapper_v1_0`     |`governance_mapper_v1_0.py`     |Maps governance principles to structural roles across documents                   |
|`governance_mapper_uber_v1_1`|`governance_mapper_uber_v1_1.py`|Extended governance mapper — full principle ladder cross-reference                |
|`governance_fetcher`         |`governance_fetcher.py`         |Fetches and caches live governance documents from operations repo                 |
|`principle_harmonizer_v1_0`  |`principle_harmonizer_v1_0.py`  |Harmonizes principle layer across governance files, surfaces drift                |
|`principle_harmonizer_v1_2`  |`principle_harmonizer_v1_2.py`  |v1.2 — extended harmonizer with cross-file dependency tracking                    |
|`principle_analyzer_v1_0`    |`principle_analyzer_v1_0.py`    |Analyzes principle coverage gaps and redundancies across documents                |
|`molting_protocol_diff_v1_0` |`molting_protocol_diff_v1_0.py` |Diffs SESSION_RITUALS.md versions — classifies patching vs clean-layer            |
|`mhr_question_trace_v1_0`    |`mhr_question_trace_v1_0.py`    |Traces question-source → method-design → data-output for MHR auditability         |
|`aa_principle_audit_v1_0`    |`aa_principle_audit_v1_0.py`    |Evaluates protocol artifacts against honesty, humility, service markers (AA frame)|
|`tier1_principles`           |`tier1_principles.py`           |Tier 1 principle enforcement checks                                               |
|`tier1_principles_stub`      |`tier1_principles_stub.py`      |Stub for tier 1 principle loading — dependency used by other tools                |

-----

## 3. ACAT corpus validation

|Skill folder                          |Tool                                |One-line purpose                                                                             |
|--------------------------------------|------------------------------------|---------------------------------------------------------------------------------------------|
|`run_acat_validation_suite_v1.0`      |`run_acat_validation_suite.py`      |**Master runner** — executes all validators in one pass → OVERALL_PASS / WARN / FAIL         |
|`corpus_integrity_validator`          |`corpus_integrity_validator.py`     |Validates ACAT corpus CSV: missing fields, out-of-range scores, LI correctness, Phase pairing|
|`corpus_delta_analyzer`               |`corpus_delta_analyzer.py`          |Diffs two corpus CSV snapshots; surfaces LI regression and D-04 patterns                     |
|`acat_session_validator`              |`acat_session_validator.py`         |Validates session record Phase 1/3 structure, D-COMP declarations, Merkle chain              |
|`acat_protocol_auditor`               |`acat_protocol_auditor.py`          |Audits session close posts against Section B protocol requirements                           |
|`drift_catalog_validator`             |`drift_catalog_validator.py`        |Validates drift codes in close posts; cross-session frequency tracking                       |
|`acat_dimension_scorer`               |`acat_dimension_scorer.py`          |Scores ACAT dimensions from session records; Bayesian posterior intervals; D-COMP probability|
|`acat_merkle_auditor_v1.0`            |`acat_merkle_auditor.py`            |Merkle chain integrity auditor — detects post-hoc modification via root mismatch             |
|`registered_findings_validator_v1_0`  |`registered_findings_validator.py`  |Validates REGISTERED.md structure and sequential F-/IC-/H-number ordering                    |
|`phase1_prompt_integrity_checker_v1.0`|`phase1_prompt_integrity_checker.py`|Validates Phase 1 prompt structure and declaration block completeness                        |
|`builder_compliance_scanner_v1.0`     |`builder_compliance_scanner.py`     |Scans any tool for Builder v1.7 compliance: smoke-test, help, zone tag, session tag          |
|`ground_truth_validator_V1.0`         |`ground_truth_validator.py`         |Ground truth validation against canonical corpus baselines                                   |
|`errors_acat_V1.0`                    |`errors_acat.py`                    |ACAT error class definitions — **dependency**, not invoked directly                          |
|`circuit_validator_v1_0`              |`circuit_validator_v1_0.py`         |Circuit-level validation for pipeline integrity checks                                       |

-----

## 4. ACAT psychometric & research tools

|Skill folder                      |Tool                                 |One-line purpose                                                              |
|----------------------------------|-------------------------------------|------------------------------------------------------------------------------|
|`acat_psychometric_validator_v1_0`|`acat_psychometric_validator_v1_0.py`|Recomputes α, PCA, bi-factor — reproducible method report artifacts           |
|`acat_phase_shift_analyzer_v1_0`  |`acat_phase_shift_analyzer_v1_0.py`  |Per-agent/provider LI distributions and stress-response deltas                |
|`harm_independence_monitor_v1_0`  |`harm_independence_monitor_v1_0.py`  |Tracks PC2-linked Harm Independence Metric (HIM) signal independently of PC1  |
|`bpl_signal_extractor_v1_0`       |`bpl_signal_extractor_v1_0.py`       |Extracts behavioral-language pattern tokens under perturbation sets (H-BPL-01)|
|`fibonacci_scaling_probe_v1_0`    |`fibonacci_scaling_probe_v1_0.py`    |Tests whether corpus growth/variance patterns match Fibonacci-like scaling    |
|`hawkins_acat_mapper_v1_0`        |`hawkins_acat_mapper_v1_0.py`        |Evidence-tagged crosswalk: ACAT dimensions ↔ Hawkins calibration levels       |
|`acat_document_analyzer`          |`acat_document_analyzer.py`          |TF-IDF surrogate scoring for dimensional evidence density; batch mode         |
|`acat_sdt_analytics_v1_0`         |`acat_sdt_analytics_v1_0.py`         |Signal detection theory analytics for ACAT response classification            |
|`acat_room_state_auditor_v1.0`    |`acat_room_state_auditor.py`         |Audits room/session state for protocol integrity                              |
|`scg_scorer`                      |`scg_scorer.py`                      |SCG (Self-Calibration Gap) scoring tool                                       |
|`red_team_runner_v1_0`            |`red_team_runner_v1_0.py`            |Red team test runner for adversarial ACAT evaluation scenarios                |
|`assess_router_Z2_assessment`     |`assess_router_Z2_assessment.py`     |Routes assessment requests through Z2 gate — requires Night authorization     |

-----

## 5. ACAT instrument & protocol

|Skill folder                |Tool                           |One-line purpose                                                        |
|----------------------------|-------------------------------|------------------------------------------------------------------------|
|`acat_doc_v1`               |`acat_doc_v1.py`               |ACAT document spec baseline                                             |
|`acat_mcp_full_wrapper_v1.2`|`acat_mcp_full_wrapper.py`     |Full MCP wrapper for the ACAT API (`api.humanaios.ai`)                  |
|`app_mapping_tool`          |`app_mapping_tool_v0_1_4.py`   |ACAT fit scanner — maps app/tool descriptions to ACAT dimension coverage|
|`anthropic_client_fence_fix`|`anthropic_client_fence_fix.py`|Fixes Anthropic client fencing issues in API call pipelines             |

-----

## 6. System & document infrastructure

|Skill folder                           |Tool                                      |One-line purpose                                                            |
|---------------------------------------|------------------------------------------|----------------------------------------------------------------------------|
|`haios_harmonizer_v1_0`                |`haios_harmonizer_v1_0.py`                |System-level harmonization across governance surfaces                       |
|`haios_agent_orchestrator_v1_0_patched`|`haios_agent_orchestrator_v1_0_patched.py`|Agent orchestration layer for multi-tool dispatch                           |
|`haios_collab_scanner_v1_0`            |`haios_collab_scanner_v1_0.py`            |Scans for collaboration signals across repositories and documents           |
|`repo_discovery_v1_0`                  |`repo_discovery_v1_0.py`                  |Repository discovery and mapping across humanaios-ui and LastingLightAI orgs|
|`message_calibration_v1_0`             |`message_calibration_v1_0.py`             |Message calibration scoring tool                                            |
|`haios_drive_scanner_v1_0`             |`haios_drive_scanner_v1_0.py`             |Google Drive scanner for HumanAIOS document surfaces                        |
|`haios_doc_ingestor_v1_0`              |`haios_doc_ingestor_v1_0.py`              |Document ingestion pipeline for HumanAIOS surfaces                          |
|`document_ingestor_v1_0`               |`document_ingestor_v1_0.py`               |Base document ingestion layer                                               |
|`supabase_corpus_connector_v1_0`       |`supabase_corpus_connector.py`            |Supabase read/write connector for `acat_assessments_v1` live corpus         |
|`supabase_logger`                      |`supabase_logger.py`                      |Structured logging to Supabase tables                                       |
|`slack_notifier`                       |`slack_notifier.py`                       |Slack notification dispatcher for pipeline events                           |
|`haios_notify_dispatcher_v1_0`         |`haios_notify_dispatcher_v1_0.py`         |HumanAIOS notification dispatch layer — routes alerts across channels       |
|`haios_pipeline_v1_0`                  |`haios_pipeline_v1_0.py`                  |Pipeline orchestration for multi-step HumanAIOS workflows                   |
|`haios_report_writer_v1_0`             |`haios_report_writer_v1_0.py`             |Report generation and formatting tool                                       |
|`registry_site_generator_v1_0`         |`registry_site_generator_v1_0.py`         |Generates static registry site from REGISTERED.md content                   |
|`server`                               |`server.py`                               |Local development server for HumanAIOS tools                                |
|`system_audit_v1_0`                    |`system_audit_v1_0.py`                    |System-wide audit across all HumanAIOS infrastructure surfaces              |
|`system_audit_v1_1`                    |`system_audit_v1_1.py`                    |v1.1 — extended system audit with dependency chain verification             |
|`tool_scaffolder_v1_0`                 |`tool_scaffolder_v1_0.py`                 |Scaffolds new Builder v1.7-compliant tools from template                    |
|`tool_template`                        |`tool_template.py`                        |Canonical Builder v1.7 tool template — copy to create new tools             |
|`Metaculus_main`                       |`Metaculus/main.py`                       |Metaculus forecasting bot entry point (HumanAIOSBot, profile 299627)        |

-----

## 7. Zone classification

|Zone  |Meaning                   |Applies to                                                           |
|------|--------------------------|---------------------------------------------------------------------|
|Zone 1|Claude executes           |All tools in this directory except `assess_router_Z2_assessment`     |
|Zone 2|Night decides             |`assess_router_Z2_assessment` — requires explicit Night authorization|
|Zone 3|Night executes at terminal|`git_push_gate_v1_0` enforces this boundary before any push          |

**Dependencies note:** `errors_acat_V1.0` (`errors_acat.py`) is imported by several corpus and session validators. Ensure it is present before running the validation suite. `tier1_principles_stub` is a load dependency for principle-layer tools.

-----

## 8. Adding a new skill

Use `tool_scaffolder_v1_0.py` to generate a Builder v1.7-compliant tool and matching skill scaffold:

```bash
python tools/tool_scaffolder_v1_0.py --name my_new_tool --category diagnostic_tool
```

Then create the skill folder manually:

```bash
mkdir tools/skills/my_new_tool
# Write tools/skills/my_new_tool/SKILL.md following the 5-section template
```

All skills must follow the 5-section template:

```markdown
# SKILL: <tool_name>
## 1. Description
## 2. Purpose
## 3. Parameters and Inputs
## 4. Outputs
## 5. Usage Example
```

See `tools/skills/tool_template/SKILL.md` for the canonical reference.

-----

## 9. Skill template reference

The Copilot-generated scaffolds in this directory follow a consistent 5-section structure. They document discovered CLI parameters as tables and provide a minimal `--help` invocation example. For tools with richer operational context — particularly session-lifecycle skills (`humanaios-phase1-wrapper`, `humanaios-realtime-drift`, `humanaios-triage-finding`) and governance skills (`humanaios-findings-scan`, `humanaios-receipt-reconciliation`, `humanaios-wgs-sweep`) — extended SKILL.md files with trigger phrases, gate sequences, and output block formats exist in the Claude project skill context and are candidates for promotion to this directory.

See `docs/TOOL_GAP_LIST.md` for planned additions and research thread mappings.