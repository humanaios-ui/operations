# acat/tools — ACAT program analysis tooling

Landed from `docs/_inbox_` (S-071426). Standalone analysis/validation tools of the
HumanAIOS/ACAT program. Most run self-contained (`--smoke-test`); all were compat-fixed
for Python 3.9 → 3.13 (PEP 604 union annotations).

| Tool | What it does | Notes |
|---|---|---|
| `learner_growth_classifier.py` | GROWTH/PLATEAU/REGRESSION over learner phase scores | stdlib; `--smoke-test` |
| `cross_substrate_blind_discriminator_v1_0.py` | forbids a substrate scoring its own output | library (inject callables); `--smoke-test` |
| `elicitation_surface_autocapture_v1_0.py` | auto-captures sampling params + wording variant | companion to `sql/migration_011` |
| `tier1_logprob_capability_probe_v1_0.py` | probes provider logprob reachability | needs API key + egress for a live run |
| `registration_validator_v1_0.py` | pre-merge REGISTERED.md entry gate | needs `outcome_symmetry_checker` (in `autonomy/gates/`) for full run; `z2_queue_v1_1.py` not present |
| `university_module_test.py` | exploratory demo (NOT a real test) | **imports `kambhampati_tracker`**, which lives in `autonomy/gates/`; run from there or add it to path. Low-value spike — kept for provenance. |

All Z1-DRAFT, proposed, not ratified.
