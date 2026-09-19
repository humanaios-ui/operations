# Shared-Memory Census Findings

Generated from a fresh repository scan of the five mandated unit populations: tools/*.py, docs/**, .github/workflows/*, .agents/skills/**, and root *.md.

## Summary

| Population | Units | Isolation | Spine | Dangling | Chain coverage |
|---|---:|---:|---:|---:|---:|
| tools/*.py | 110 | 27.27% | 21.82% | 74.55% | 4.55% |
| docs/** | 104 | 45.19% | 34.62% | 49.04% | 0.0% |
| .github/workflows/* | 35 | 94.29% | 5.71% | 45.71% | 0.0% |
| .agents/skills/** | 2 | 100.0% | 0.0% | 50.0% | 0.0% |
| root *.md | 146 | 21.92% | 23.29% | 45.21% | 0.0% |

## Findings

### 1. tools/*.py units remain isolated from shared stores

- Metric: isolation_rate=27.27% (30/110)
- Finding: A measurable fraction of units never touch a store that is referenced by more than one unit, which means the repo's shared memory is not the default operating substrate for this population.
- Falsifier: This finding would be falsified if the unshared population is actually consumed through repo-level side channels that the file-reference grep cannot observe, such as runtime-generated state or sibling repository files.

### 2. Dangling references point at absent artifacts

- Metric: dangling_rate=54.41% (top targets: tools/TOOL_NAME}_{ts}.json (22), nonexistent/path/that/cannot/exist.json (14), acat_corpus_session.py (10))
- Finding: The repo contains references to files that do not exist in the checked-out tree, which weakens traceability and can silently break operational hand-offs.
- Falsifier: This would be falsified if the missing references resolve successfully in a sibling repository, alternate branch, or generated artifact directory outside the checked-out tree.

### 3. Spine attachment is concentrated in governance and session anchors

- Metric: spine_attachment=tools/*.py=21.82%; docs/**=34.62%; .github/workflows/*=5.71%; root *.md=23.29%
- Finding: The repository repeatedly points at governance and session anchors, indicating that the canonical spine is serving as a coordination substrate even when the surrounding units are otherwise fragmented.
- Falsifier: This finding would be falsified if the referenced spine files are only incidental citations and not actually read or acted on by the units that mention them.
