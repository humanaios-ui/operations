# Research Validation Test Harness

Run all scenarios:

- `python tests/research/run_research_validation.py`

Run with trace output:

- `python tests/research/run_research_validation.py --with-trace --trace-ticks 20`

Run selected scenarios (repeat `--scenario` as needed):

- `python tests/research/run_research_validation.py --scenario S1_baseline_homeostasis`
- `python tests/research/run_research_validation.py --scenario S2_signal_semantics --scenario S7_sanjiao_threshold_edges`

Artifacts written by the harness:

- `artifacts/research_validation_<timestamp>.json`
- `artifacts/research_validation_<timestamp>.csv`
- `artifacts/traces/S2_liver_stagnation_trace.jsonl`
- `artifacts/traces/S2_liver_stagnation_trace_summary.json`
