# Tool Gap List — Research Threads to Scaffold

Current tool inventory in `/tools`:

- `governance_mapper_v1_0.py`
- `haios_collab_scanner_v1_0.py`
- `repo_discovery_v1_0.py`

All current tools follow Builder v1.7 structure. The following gaps are mapped to active research/governance threads.

## Proposed scaffold files

| Proposed file | Thread | One-line purpose |
|---|---|---|
| `tools/acat_psychometric_validator_v1_0.py` | ACAT psychometrics | Recompute reliability, PCA/bi-factor summary metrics, and produce reproducible method report artifacts. |
| `tools/acat_phase_shift_analyzer_v1_0.py` | Phase 1/2/3 dynamics | Compute per-agent and per-provider shift metrics including Learning Index distributions and stress-response deltas. |
| `tools/bpl_signal_extractor_v1_0.py` | H-BPL-01 | Extract candidate behavioral-language tokens/patterns from response corpora under perturbation sets. |
| `tools/harm_independence_monitor_v1_0.py` | Harm Independence Metric | Track PC2-linked harm-awareness signal behavior separately from PC1 movement across runs. |
| `tools/molting_protocol_diff_v1_0.py` | Molting hypothesis | Compare SESSION_RITUALS protocol versions and classify additive patching vs clean-layer replacement patterns. |
| `tools/mhr_question_trace_v1_0.py` | Market Harmonization Research | Trace question-source → method-design → data-output chain for auditability of MHR execution claims. |
| `tools/hawkins_acat_mapper_v1_0.py` | Hawkins cross-map | Generate explicit, evidence-tagged crosswalk reports between ACAT dimensions and Hawkins calibration mappings. |
| `tools/fibonacci_scaling_probe_v1_0.py` | Fibonacci frame | Test whether observed corpus growth/variance patterns match or diverge from Fibonacci-like scaling assumptions. |
| `tools/aa_principle_audit_v1_0.py` | AA / 12-step frame | Evaluate whether protocol artifacts satisfy declared honesty/humility/service operational markers. |
| `tools/zone_boundary_audit_v1_0.py` | Zone safety model | Detect and report Zone 1/2/3 boundary violations in workflow artifacts and operator logs. |

## Suggested implementation order

1. `acat_psychometric_validator_v1_0.py`
2. `acat_phase_shift_analyzer_v1_0.py`
3. `harm_independence_monitor_v1_0.py`
4. `molting_protocol_diff_v1_0.py`
5. remaining thread tools

## Zone 2 decisions required

1. Confirm which metrics are authoritative for first release of each scaffolded tool.
2. Approve input data contracts for corpus access and privacy boundaries.
3. Approve output destinations (local report, docs artifact, dashboard feed, or all).
