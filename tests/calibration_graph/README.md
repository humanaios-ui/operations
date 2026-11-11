# Calibration Graph Validation Stage

This directory is the first executable validation stage for the bidirectional calibration evidence graph.

## Run

```bash
python -m pip install -r tools/calibration_graph/requirements.txt
python tools/calibration_graph/validate_graph.py
```

## Expected result

- `reference-valid.ttl` MUST conform.
- `reference-invalid.ttl` MUST fail.

The invalid fixture intentionally violates three graph constraints. A validator that accepts it is itself a failed validation stage.

## Why this stage exists

The stage tests whether the graph representation can reject malformed evidence before a design delta is promoted. It does not validate the truth of cognitive claims and does not replace runtime enforcement of pre-freeze answer suppression.

## Promotion rule under test

`OBSERVATION -> FROZEN EVIDENCE -> GRAPH VALIDATION -> RETEST -> PROMOTION/WITHDRAWAL`

This staging remains provisional until it demonstrates practical benefit over the unstaged process.
