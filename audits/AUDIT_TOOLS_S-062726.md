# Tools Folder Audit — Step-4 Inventory (S-062726)

**Status:** Zone 1 audit artifact — for Z2 (Night) review
**Scope:** `operations/tools/` — 157 files (the 31 covered in the prior ad-hoc pass excluded)
**Method:** 12-agent workflow fan-out (deep bug-review on code, light inventory on skill docs) → synthesis
**Date:** 2026-06-27 · inaugural humanaios session
**Corpus baseline:** SEED 629 / 516 / 307 / 0.8632

> Companion to the root-file audit. Applies the org's own STRUCTURAL / INTEGRATED / ASPIRATIONAL / DECORATIVE / TESTABLE taxonomy to every file. A file tracing to no principle and referenced by nothing is "operating without grounding."

---

## 1. Health snapshot

| status_class | count |
|---|---|
| STRUCTURAL | 43 |
| INTEGRATED | 61 |
| DECORATIVE | 23 |
| ASPIRATIONAL | 11 |
| TESTABLE | 19 |

## 2. THE SYSTEMIC FINDING — markdown round-trip corruption

The dominant defect is **one root cause, not many bugs.** ~10 Python/JS files were saved through a **markdown renderer that mangled the source**: ASCII quotes → curly quotes, `__future__`/`__name__`/`__main__` → bold `**future**`/`**name**`/`**main**`, leading underscores eaten by markdown-italic (`_fetch` → `*fetch`), literal ```` ``` ```` fence lines embedded, and — most damagingly — **indentation flattened in places** (function/class bodies dedented to column 0). All now SyntaxError on parse. Several have live importers.

**Primary remediation is to fix the save/round-trip pipeline that corrupts code through markdown** — otherwise new files keep getting corrupted. The corrupted files are casualties; some are better regenerated from original source than reconstructed.

## 3. Top bugs (ranked)

| sev | file:loc | defect |
|---|---|---|
| CRITICAL | `governance_fetcher.py:395` | Unguarded `from fastmcp import FastMCP` at module top; fastmcp not installed. Breaks EVERY import path including the pure-stdlib --smoke/run() CLI and server.py's `import governance_fetcher` -> Module |
| CRITICAL | `server.py:28-29,60-61` | Unified MCP entrypoint imports `haios_pipeline` and `haios_report_writer`, which do not exist in tools/. ModuleNotFoundError on import, so neither `--serve` nor `--smoke` can start. Shipped entrypoint |
| CRITICAL | `registry_loader.py:1` | Markdown-round-trip corruption (curly quotes, `from **future**`, `if **name**==**main**`, literal ``` fence lines). SyntaxError on ast.parse. Also breaks triage_log_service.py and humulity_audit_servi |
| CRITICAL | `triage_log_service.py:1,15,57` | Unicode curly quotes for every string + `from **future** import annotations` + embedded ``` fence lines. SyntaxError on import; the Advance-Pass-Rate row source is entirely dead. |
| CRITICAL | `parse_wgs_z3.py:9-10,12-103` | Unguarded `import slack_sdk`/`supabase` (not in requirements) + all work at module-top with no main() guard: client construction and live conversations_history()/upsert fire on import, plus KeyError o |
| CRITICAL | `app_mapping_tool.py:2,118-122` | Entire source uses Unicode curly quotes for string AND dict literals (e.g. TOOL_NAME and curly docstrings) plus embedded ``` markers; ast.parse SyntaxError. The most elaborate file in the batch can ne |
| CRITICAL | `humility_audit_router.py:1,20,24` | `from **future** import annotations` + curly triple-quote docstrings + literal ``` fences with flattened indentation. Immediate SyntaxError; broken out-of-package dup of live acat/api/routes/humility_ |
| CRITICAL | `humulity_audit_service.py:205,274` | `def *fetch_dimension_column`/`def *extract_dim_scores` (markdown-italic ate the leading underscore) plus `from **future**` and curly docstrings. SyntaxError; also builds Supabase column names as `p1* |
| CRITICAL | `assess_router_Z2_assessment.py:1,24-35` | `from **future** import annotations`, curly-quote strings, and function/try bodies dedented to column 0. Unimportable; would crash app startup if wired. Corrupted orphan dup of the canonical assess_ro |
| CRITICAL | `haios_github_inspector.jsx:1-655` | Smart/curly quotes replace ASCII quotes throughout (from line 1 import onward) plus embedded literal ``` code-fence lines; every string/import is invalid JS. Will not parse or transpile. (Even fixed,  |
| CRITICAL | `skills/haios_compressor_v1_0/haios_compressor_v1_0.js:37` | Curly/smart quotes used as JS string delimiters and typographic ellipsis as spread operator; node --check fails, module cannot be require()'d. Orphan duplicate of the clean canonical tools/haios_compr |
| CRITICAL | `skills/skill_compression_scanner_v1_0/skill_compression_scanner_v1_0.js:18,20` | Curly-quote SyntaxError from line 18 AND require('./haios_compressor_v1_0') resolves to its own dir which has no such file. Doubly broken orphan dup of canonical tools/skill_compression_scanner_v1_0.j |
| HIGH | `Metaculus/main.py:1171,1176,373` | Hardcoded nonexistent model id 'anthropic/claude-sonnet-4-6' (no such Claude model). Every researcher + default LLM call 404s at the provider, so all live forecasts fail unless forecasting_tools silen |
| HIGH | `builder_compliance_scanner_v1.0.py:43-53` | The merge gate under-enforces its own standard: _CHECKS_RAW verifies only TOOL_NAME and TOOL_VERSION, not the TOOL_CATEGORY/TOOL_SESSION/TOOL_ZONE that README sec.8 mandates. Every header-incomplete t |
| HIGH | `errors_acat_V1.0.py:5-8,39-46,1` | Self-contradicting dead dependency: docstring asserts 'all 8 other tools import from this module' and that SpecLoadFailed was consolidated here, but grep `import errors_acat` = 0 and each validator st |
| HIGH | `haios_cli.py:339-340 vs run_acat_validation_suite_v1.0.py:1` | Broken dispatch path: haios_cli maps 'validation'/'validate' to run_acat_validation_suite_v1_0.py (underscore) but the file is _v1.0 (dot); README references the unversioned name. CLI 'validate' alway |
| HIGH | `test_acat_core.py:20,103,115` | Self-referential tests / false assurance: compute_li, validate_score_bounds and the Z3RedactionEngine are defined INSIDE the test file; it imports no production code, so every assertion passes regardl |
| HIGH | `README.md (sections 3/5/6)` | STALE catalog (last-updated 2026-06-09): documents/invokes ~10 unversioned filenames that do not exist on disk (run_acat_validation_suite.py, acat_merkle_auditor.py, phase1_prompt_integrity_checker.py |
| HIGH | `haios-corpus-integrity.yml / haios-harmonizer-pulse.yml / haios-system-audit.yml` | Placement defect across all three scheduled-governance workflows: headers declare .github/workflows/ paths but the files live in tools/ and NO .github/workflows/ directory exists. GitHub Actions only  |
| HIGH | `molting_protocol_diff_v1_0.py:62-104 / zone_boundary_audit_v1_0.py:62-104` | Phantom tools: run() is an unfilled scaffold (TODO/'YOUR LOGIC HERE'), always returns empty items/warnings, so per the 'FAIL if not items and not warnings' rule every real input deterministically FAIL |
| HIGH | `slack_notifier.py:409` | Unguarded `from fastmcp import FastMCP` at module top on every import/CLI invocation (not lazy inside --serve); fastmcp is in no requirements file. If absent, even --smoke and the pure-dispatch run()/ |
| MEDIUM | `acat_merkle_auditor_v2_0.py:525-526,528` | On the HMAC fallback path the raw secret key is serialized into the audit dict as _hmac_key_material_hex_DO_NOT_COMMIT and written to disk by write_report(outputs/). The HMAC proof's security depends  |

## 4. Dead-duplicate tools (keep / delete)

- acat_merkle_auditor: KEEP acat_merkle_auditor_v2_0.py (superset + SSI/VC layer, re-embeds v1.0 checks verbatim); DELETE acat_merkle_auditor_v1.0.py — both share TOOL_NAME 'acat_merkle_auditor'.
- principle_harmonizer: KEEP principle_harmonizer_v1_2.py (adds master_key_system framework); DELETE principle_harmonizer_v1_0.py (mislabeled v1.1, identical TOOL_NAME) and its skills/principle_harmonizer_v1_0 doc.
- system_audit: KEEP system_audit_v1_1.py (live pre-ratification gate); RETIRE/DELETE system_audit_v1_0.py — both declare TOOL_NAME='system_audit' TOOL_VERSION='1.1.0', so the version string cannot distinguish them. Drop its SKILL.md.
- governance_mapper: COLLISION not pure dup — governance_mapper_v1_0.py (lane taxonomy) and governance_mapper_uber_v1_1.py (Uber case study) both claim TOOL_NAME='governance_mapper' v1.1.0 but are DIFFERENT tools; RENAME the Uber variant to a distinct TOOL_NAME rather than delete.
- anthropic_client_fence_fix.py: DELETE tools/ staging copy; KEEP canonical acat/api/services/provider_clients/anthropic_client.py (the byte-identical version actually imported).
- assess_router: DELETE BOTH tools/ copies — assess_router_Z2_assessment.py (broken/corrupted) and assess_router_new_Z2-ASSESS-01.py (clean but orphan, hyphenated non-importable name); KEEP canonical acat/api/routes/assess_router.py mounted by app.py.
- humility_audit_router.py: DELETE tools/ copy (markdown-corrupted, unimportable); KEEP canonical acat/api/routes/humility_audit_router.py.
- humulity_audit_service.py: DELETE — misspelled 'humulity', markdown-corrupted, referenced by nothing; canonical consumer expects humility_audit_service.
- skills/haios_compressor_v1_0/haios_compressor_v1_0.js: DELETE (smart-quote-broken orphan fork); KEEP canonical tools/haios_compressor_v1_0.js (the one actually require()'d).
- skills/skill_compression_scanner_v1_0/skill_compression_scanner_v1_0.js: DELETE (broken + missing require target, orphan); KEEP canonical tools/skill_compression_scanner_v1_0.js.
- tier1_principles_stub.py: DELETE — orphan, never imported, and interface-incompatible (TIER1 as dict vs canonical list) so it is not the drop-in fallback it claims; KEEP tier1_principles.py.

## 5. README taxonomy mismatches

- governance_mapper_v1_0.py — README taxonomy says governance_tool, but docstring (line 4) and TOOL_CATEGORY (line 40) declare audit_tool.
- governance_mapper_uber_v1_1.py — actual TOOL_CATEGORY audit_tool, but README only lists a single 'governance_mapper' under governance_tool (and the wrong filename).
- haios_drive_scanner_v1_0.py — README lists diagnostic_tool, but TOOL_CATEGORY and docstring declare audit_tool.
- principle_harmonizer_v1_0.py — README governance_tool vs TOOL_CATEGORY audit_tool.
- principle_harmonizer_v1_2.py — README governance_tool vs TOOL_CATEGORY audit_tool.
- phase1_prompt_integrity_checker_v1.0.py — docstring asserts security_gate_tool, README classifies it validation_tool.
- system_audit_v1_0.py — README/skill present it as orchestrator_tool while sharing TOOL_NAME+VERSION with the security_gate_tool system_audit_v1_1.py.
- red_team_runner_v1_0.py — self-described validation_tool/audit_tool with no TOOL_CATEGORY constant, so the README label cannot be verified against the file.

## 6. Priority admin actions

1. Restore-or-delete the 9 markdown/mojibake-corrupted files that fail to parse: registry_loader.py (breaks its two importers), triage_log_service.py, humility_audit_router.py, humulity_audit_service.py, app_mapping_tool.py, haios_github_inspector.jsx, assess_router_Z2_assessment.py, and the two skills/*.js copies. These are CRITICAL parse failures, several with live importers.
2. Fix unguarded hard dependencies so CLI/--smoke works deps-free: lazy-import fastmcp in governance_fetcher.py:395 and slack_notifier.py:409; guard slack_sdk/supabase + add a main() guard in parse_wgs_z3.py; restore (or stop importing) the missing haios_pipeline / haios_report_writer modules in server.py.
3. Resolve the TOOL_NAME/TOOL_VERSION collisions: delete the superseded siblings (acat_merkle_auditor_v1.0.py, principle_harmonizer_v1_0.py, system_audit_v1_0.py) plus their skills, and rename governance_mapper_uber_v1_1.py to a distinct TOOL_NAME. Right now multiple files share one identity and write to the same report filename.
4. Update the two STALE indexes (tools/README.md, skills/README.md) to point at versioned filenames that exist on disk, fix the run-command examples and skill->tool mapping table, and correct the skill count.
5. Repair or hard-gate the validation surfaces that give a false green signal: builder_compliance_scanner under-enforcement (add TOOL_CATEGORY/SESSION/ZONE checks), drift_catalog_validator always-PASS, red_team_runner default self-scoring, test_acat_core self-referential tests, and the ~7 unfilled scaffold tools whose SKILL.md documents working behavior they do not implement.
6. Deploy the three GitHub Actions workflows to .github/workflows/ (currently inert in tools/ so corpus-integrity, harmonizer-pulse and system-audit crons never fire), and fix the haios_cli 'validate' dispatch path (underscore-vs-dot filename mismatch).
7. Fix the live Metaculus bot before next deploy: the hardcoded nonexistent model id 'claude-sonnet-4-6' makes every forecast fail, and railway.toml deploys it in --mode test_questions.
8. Remove the secret-key-to-disk leak in acat_merkle_auditor_v2_0.py (HMAC fallback writes _hmac_key_material_hex into the report file, defeating the proof).

## 7. Remediation in this PR (corruption cluster)

**Deleted (6 — corrupted/orphan dupes, canonical versions retained):**
`tools/humility_audit_router.py` (→ canonical `acat/api/routes/humility_audit_router.py`), `tools/assess_router_Z2_assessment.py` + `tools/assess_router_new_Z2-ASSESS-01.py` (→ `acat/api/routes/assess_router.py`), `tools/humulity_audit_service.py` (broken orphan, misspelled, no canonical, unreferenced), `tools/skills/haios_compressor_v1_0/haios_compressor_v1_0.js` + `tools/skills/skill_compression_scanner_v1_0/skill_compression_scanner_v1_0.js` (→ canonical `tools/*.js`).

**Character-de-corrupted but NOT yet parse-clean (4 — flagged, do not consider fixed):**
`registry_loader.py`, `triage_log_service.py`, `app_mapping_tool.py`, `haios_github_inspector.jsx`. Smart quotes / bold-dunders / fence lines removed (deterministic, safe), but **indentation was lossily flattened** and requires manual re-indentation or regeneration from original source. Not blind-reconstructed here because several have importers and `app_mapping_tool.py` is 1562 lines — guessing nesting depth risks silent bugs.

**Out of scope (flagged, separate follow-up):** the unguarded-import cluster (`governance_fetcher.py:395`, `slack_notifier.py:409`, `parse_wgs_z3.py`, `server.py`), the merkle-auditor secret-to-disk leak, the false-green validators, and the 11 dead-duplicate / 8 taxonomy items above.

*Note: one agent claim corrected during review — `Metaculus/main.py`'s `claude-sonnet-4-6` is a VALID current model; the concern is only the `anthropic/` routing prefix, not the model name.*
