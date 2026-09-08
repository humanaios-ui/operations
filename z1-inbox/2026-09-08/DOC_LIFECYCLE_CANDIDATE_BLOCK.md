# docs/ lifecycle — registry candidate block (Z1 proposes, Z2 rules by hash over DOC_TRIAGE_2026-09-08.md)

## Position
108 files in docs/, one bulk commit (2026-09-06). Registered in document-registry.yaml: 7. Zero inbound references: 78.
Lint result: CONSUMED 29 · CODE 20 · PRODUCED? 2 · ARCHIVE 31 · ARCHIVE? 22. Every file has a disposition; none is silent.

## Second pass on the 20 CODE candidates (Z1 judgment, tier CLAIM — read by grep, not line by line)
| doc | can it become code? | does the code improve the system? | reading |
|---|---|---|---|
| PRIMARY_CHECK_GATE_INTEGRATION.md | yes — a blocking CI step | yes, IF built. **It is not built**; the doc says it is. | → IC-DOC-01, then build or retract |
| session_rituals_step7_amendment.md | yes — a patch to SESSION_RITUALS.md | yes; ratified and never applied | → IC-DOC-02, apply the patch |
| calibration/CALIBRATION_VALIDATION_SYSTEM_PLAN_v0.3.yaml + OOO v0.1–0.3 | already became code | NF_LEDGER (#220) is its descendant | → archive with lineage `superseded_by: ledgers/NF_LEDGER.jsonl` |
| checklist_config.example.json | it IS config | for `failure_taxonomy_checklist_v0_1.py`; sits in the wrong directory | → move beside the tool; CONSUMED |
| ground_truth.json, claim_report.json, acat_doc_Echoes_*.json | outputs, not inputs | no | → archive |
| ACAT_RSI_MONITOR_PLAN.md | partly — H34/H35 thresholds | only if the RSI monitor is built; nothing on main runs it | → REGISTRY for the H lines (falsifiers present), archive the plan |
| Marshal_dispatch_framework.md, AUTOMATION_GUIDE.md, GOVERNANCE_ALIGNMENT_PHASE2.md, OPERATIONS_IMPROVEMENT_PLAN.md | plans with tables | no rule that isn't already in system_graph v0.2 or REGISTERED.md | → archive, `superseded_by: system_graph.json` |
| ARTICULATION_AS_GOVERNANCE.md, HARMONIZATION-AGI.md, acat_research_design_section11.md | research prose; numbers are citations, not thresholds | no | → ARCHIVE? (lint over-fired on numeric tables) |
| ACAT_ANALYSIS_GSS1.md, ACAT_ASSESSMENT_SEED.md, ACAT_PAPER_V6_0_DRAFT.md, COMPARABLE_FRAMEWORKS_*, AI_SPONSORSHIP_* | same | no | → ARCHIVE? |

Net: **2 real code items** (one gate to build or retract, one patch to apply), **1 config move**, **1 lineage archive**, the rest archive. The lint's CODE class over-fires on analyses; that is reported, not smoothed — the precision falsifier below covers it.

## IC candidates
IC-DOC-01  claim: docs/PRIMARY_CHECK_GATE_INTEGRATION.md states "Deployed as blocking step A7 in haios_audit.yml"; no such workflow or tool exists on main at 5df54b7. Receipt overstatement in a controlled doc (IC-031 class). falsifier: `ls .github/workflows/haios_audit.yml` succeeds on main.
IC-DOC-02  claim: session_rituals_step7_amendment.md (ratified 2026-06-11) was never applied; SESSION_RITUALS.md contains no "External signal sweep". falsifier: grep finds it.
IC-DOC-03  claim: 101 of 108 docs/ files are outside document-registry.yaml, so document-control.yml cannot see them; the validator passing was vacuous for them. falsifier: registry lists them.

## Predictions (locked)
P-DOC-1  Z2 archives ≥ 40 of the 53 ARCHIVE/ARCHIVE? rows unchanged: 0.6
P-DOC-2  lint CODE-class precision on manual read of all 20 ≥ 0.5 (≥ 10 have an enforceable rule): 0.3  ← Z1 expects the heuristic to lose
P-DOC-3  IC-DOC-01 resolves by retraction rather than build within 30 days: 0.6

## Falsifier for the process itself
If after 30 days the lint still reports any `ARCHIVE?` row with `filed(implicit)`, the process is ceremonial — docs are being filed and not ruled — and FPCP itself goes to REGISTRY as an IC.
