# HumanAIOS Operations — Tools Directory

**Canonical URL:** `https://raw.githubusercontent.com/humanaios-ui/operations/main/tools/README.md`
**Last updated:** 2026-06-09 · S-060926
**Builder standard:** v1.7 (all tools)
**Zone:** All tools execute in Zone 1 unless noted. Zone 2/3 boundaries are enforced by `git_push_gate_v1_0.py` and `Z3_PROTOCOL.md`.

All tools support `--smoke-test` and `--help`. Run `--smoke-test` before any production use or after any schema change.

-----

## Quick reference

```bash
# Run any tool
python tools/<tool_name>.py --input <path_or_json>
python tools/<tool_name>.py --smoke-test

# Terminal CLI (primary entry point)
alias haios='python ~/Desktop/HAIOS-Main/operations-staging/tools/haios_cli.py'
haios "what are my open Zone 2 items?"
haios --mode check
```

-----

## 1. Entry point

|File          |Category        |One-line purpose                                                                                                                      |
|--------------|----------------|--------------------------------------------------------------------------------------------------------------------------------------|
|`haios_cli.py`|`connector_tool`|Terminal CLI — query the full HumanAIOS system using live GitHub context + Claude API. Modes: `ask` (default), `run`, `check`, `chat`.|

-----

## 2. Governance & session infrastructure

|File                           |Category            |One-line purpose                                                                                                |
|-------------------------------|--------------------|----------------------------------------------------------------------------------------------------------------|
|`git_push_gate_v1_0.py`        |`security_gate_tool`|Zone 1 push authorization gate — enforces Zone 1/2/3 file rules before any commit per `Z3_PROTOCOL.md`.         |
|`carry_tracker_v1_0.py`        |`diagnostic_tool`   |Reads WGS posts, counts sessions-carried per item, flags WARN at N>5 and ESCALATE at N>10.                      |
|`z2_queue_v1_0.py`             |`diagnostic_tool`   |Extracts Zone 2 pending items from WGS posts, deduplicates, surfaces oldest-first, flags ≥3 sessions unresolved.|
|`zone_boundary_audit_v1_0.py`  |`audit_tool`        |Detects Zone 1/2/3 boundary violations in workflow artifacts and operator logs.                                 |
|`governance_mapper_v1_0.py`    |`governance_tool`   |Maps governance principles to structural roles across documents.                                                |
|`principle_harmonizer_v1_0.py` |`governance_tool`   |Harmonizes the principle layer across governance files, surfaces drift.                                         |
|`molting_protocol_diff_v1_0.py`|`audit_tool`        |Compares `SESSION_RITUALS.md` versions, classifies additive patching vs clean-layer replacement.                |
|`mhr_question_trace_v1_0.py`   |`audit_tool`        |Traces question-source → method-design → data-output chain for Market-Harmonic Research auditability.           |
|`aa_principle_audit_v1_0.py`   |`audit_tool`        |Evaluates protocol artifacts against honesty, humility, and service operational markers (AA frame).             |

-----

## 3. ACAT corpus validation

|File                                |Category           |One-line purpose                                                                                                 |
|------------------------------------|-------------------|-----------------------------------------------------------------------------------------------------------------|
|`run_acat_validation_suite.py`      |`orchestrator_tool`|**Master runner** — executes all validators in one pass, produces OVERALL_PASS / OVERALL_WARN / OVERALL_FAIL.    |
|`corpus_integrity_validator.py`     |`validation_tool`  |Validates ACAT corpus CSV: missing fields, out-of-range scores, LI correctness, Phase pairing, D-04 monotonicity.|
|`corpus_delta_analyzer.py`          |`diagnostic_tool`  |Diffs two corpus CSV snapshots; surfaces LI regression, D-04 patterns, and population change trajectories.       |
|`acat_session_validator.py`         |`validation_tool`  |Validates session record Phase 1/3 structure, D-COMP declarations, and Merkle chain integrity.                   |
|`acat_protocol_auditor.py`          |`audit_tool`       |Audits session close posts against Section B protocol requirements (D-04, D-05, open/close tag balance).         |
|`drift_catalog_validator.py`        |`validation_tool`  |Validates drift codes in close posts; cross-session frequency tracking for D-04 pattern clusters.                |
|`acat_dimension_scorer.py`          |`diagnostic_tool`  |Scores ACAT dimensions from session records; Bayesian posterior intervals per dimension; D-COMP probability.     |
|`acat_merkle_auditor.py`            |`audit_tool`       |Merkle chain integrity auditor — detects post-hoc D-04 modification via root mismatch.                           |
|`registered_findings_validator.py`  |`validation_tool`  |Validates `REGISTERED.md` structure and sequential F-/IC-/H-number ordering.                                     |
|`phase1_prompt_integrity_checker.py`|`validation_tool`  |Validates Phase 1 prompt structure and declaration block completeness.                                           |
|`builder_compliance_scanner.py`     |`validation_tool`  |Scans any tool for Builder v1.7 compliance (smoke-test, help, zone tag, session tag).                            |
|`errors_acat.py`                    |`dependency`       |ACAT error class definitions — imported by other tools; not invoked directly.                                    |

-----

## 4. ACAT psychometric research tools

|File                                 |Category         |One-line purpose                                                                                               |
|-------------------------------------|-----------------|---------------------------------------------------------------------------------------------------------------|
|`acat_psychometric_validator_v1_0.py`|`validation_tool`|Recomputes reliability (α), PCA, and bi-factor metrics; produces reproducible method report artifacts.         |
|`acat_phase_shift_analyzer_v1_0.py`  |`diagnostic_tool`|Computes per-agent and per-provider phase shift metrics: LI distributions, stress-response deltas.             |
|`harm_independence_monitor_v1_0.py`  |`diagnostic_tool`|Tracks PC2-linked Harm Independence Metric (HIM) signal independently of PC1 movement.                         |
|`bpl_signal_extractor_v1_0.py`       |`diagnostic_tool`|Extracts candidate behavioral-language pattern tokens from response corpora under perturbation sets (H-BPL-01).|
|`fibonacci_scaling_probe_v1_0.py`    |`diagnostic_tool`|Tests whether corpus growth and variance patterns match or diverge from Fibonacci-like scaling assumptions.    |
|`hawkins_acat_mapper_v1_0.py`        |`audit_tool`     |Generates evidence-tagged crosswalk reports between ACAT dimensions and Hawkins calibration levels.            |
|`acat_document_analyzer.py`          |`diagnostic_tool`|Keyword-vector scoring (TF-IDF surrogate) for dimensional evidence density; batch mode for corpora.            |

-----

## 5. System & document infrastructure

|File                                      |Category             |One-line purpose                                                             |
|------------------------------------------|---------------------|-----------------------------------------------------------------------------|
|`haios_harmonizer_v1_0.py`                |`infrastructure_tool`|System-level harmonization across governance surfaces.                       |
|`haios_agent_orchestrator_v1_0_patched.py`|`infrastructure_tool`|Agent orchestration layer for multi-tool dispatch.                           |
|`haios_collab_scanner_v1_0.py`            |`diagnostic_tool`    |Scans for collaboration signals across repositories and documents.           |
|`repo_discovery_v1_0.py`                  |`diagnostic_tool`    |Repository discovery and mapping across humanaios-ui and LastingLightAI orgs.|
|`message_calibration_v1_0.py`             |`diagnostic_tool`    |Message calibration scoring tool.                                            |
|`haios_drive_scanner_v1_0.py`             |`diagnostic_tool`    |Google Drive scanner for HumanAIOS document surfaces.                        |
|`haios_doc_ingestor_v1_0.py`              |`infrastructure_tool`|Document ingestion pipeline for HumanAIOS surfaces.                          |
|`document_ingestor_v1_0.py`               |`infrastructure_tool`|Base document ingestion layer.                                               |
|`acat_doc_v1.py`                          |`infrastructure_tool`|ACAT document spec baseline.                                                 |
|`acat_mcp_full_wrapper.py`                |`infrastructure_tool`|Full MCP wrapper for the ACAT API (`api.humanaios.ai`).                      |
|`supabase_corpus_connector.py`            |`infrastructure_tool`|Supabase read/write connector for `acat_assessments_v1` live corpus.         |
|`acat_room_state_auditor.py`              |`audit_tool`         |Audits room and session state for protocol integrity.                        |
|`ground_truth_validator.py`               |`validation_tool`    |Ground truth validation against canonical corpus baselines.                  |
|`tool_scaffolder_v1_0.py`                 |`infrastructure_tool`|Scaffolds new Builder v1.7-compliant tools from template.                    |

-----

## 6. Running the validation suite (common workflow)

```bash
# Full session close validation — single pass
python tools/run_acat_validation_suite.py \
  --close-post close_post.txt \
  --session record.json \
  --corpus corpus.csv

# Corpus integrity check only
python tools/corpus_integrity_validator.py --input acat_corpus.csv --strict

# Check Z2 queue age from WGS JSON export
python tools/z2_queue_v1_0.py --input wgs_posts.json

# Check carry escalations
python tools/carry_tracker_v1_0.py --input wgs_posts.json

# Pre-push authorization gate
python tools/git_push_gate_v1_0.py --staged-files "$(git diff --cached --name-only)"

# Terminal query (requires ANTHROPIC_API_KEY)
haios --mode check
```

-----

## 7. Zone classification

|Zone  |Meaning                   |Tools                                                         |
|------|--------------------------|--------------------------------------------------------------|
|Zone 1|Claude executes           |All tools in this directory                                   |
|Zone 2|Night decides             |Any tool output flagging a Z2 gate item routes here           |
|Zone 3|Night executes at terminal|`git_push_gate_v1_0.py` enforces this boundary before any push|

**Dependencies note:** `errors_acat.py` is imported by several validation tools. Ensure it is present before running corpus or session validators.

-----

## 8. Adding a new tool

Use `tool_scaffolder_v1_0.py` to generate a Builder v1.7-compliant template:

```bash
python tools/tool_scaffolder_v1_0.py --name my_new_tool --category diagnostic_tool
```

All tools must:

- Pass `--smoke-test` before commit
- Include `TOOL_NAME`, `TOOL_VERSION`, `TOOL_CATEGORY`, `TOOL_SESSION`, `TOOL_ZONE` constants
- Support `--help` and `--input`
- Be Zone 1 unless a Z2 ratification document authorizes otherwise

See `docs/TOOL_GAP_LIST.md` for planned additions and their research thread mappings.