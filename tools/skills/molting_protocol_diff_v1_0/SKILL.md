# SKILL: molting_protocol_diff_v1_0

## 1. Description

**What does this tool do?**  
Classifies a molt's tier (0/1/2) from the filepaths its diff touches, and measures the gap between that measurement and the author's claimed tier.

| Tier | Rule | Obligation |
|---|---|---|
| 0 | No constants and no gates touched | Not a molt; consumes no slot |
| 1 | Touches ≥1 `CONSTANTS_PATHS` entry | Needs `molt_id`, prediction, window |
| 2 | Touches ≥1 `GATE_PATHS` entry | Needs registry entry + ADV run before KEEP |

The tier is the maximum over every path in the diff. The two path tuples at the top of the module are the published rule; editing them is itself a Tier 2 change, because the module lists itself in `GATE_PATHS`.

---

## 2. Purpose

**Why does this tool exist?**  
Molt tier used to be decided by opinion and recorded as prose, which made it something to negotiate. This tool makes it a measurement: the classifier is the signal, `molt_tier_claimed` in the PR body is the hypothesis, and the gap is audit data. `.github/workflows/molt-tier-check.yml` runs it on every PR — advisory, never blocking.

---

## 3. Parameters and Inputs

**What are the required inputs for this tool?**  
The table below lists command-line parameters discovered for this tool. Use `--help` for the complete interface.

Exactly one of `--input` or `--files` is required.

| Parameter Name | Type | Required | Default Value | Description |
|---|---|---|---|---|
| `--input` / `-i` | `string` | No | `None` | Path to a JSON file, or inline JSON. Object keys: `filepaths` (required), `molt_tier_claimed`, `pr_body`, `pr_number`. |
| `--files` / `-f` | `string[]` | No | `None` | Diff filepaths to classify. With no values, reads one path per line from stdin. |
| `--claimed` | `0\|1\|2` | No | `None` | The author's claimed tier, for gap measurement. |
| `--pr` | `int` | No | `None` | PR number to stamp on the gap record. |
| `--tier-only` | `boolean` | No | `false` | Print just the measured tier and exit. For CI. |
| `--output` / `-o` | `string` | No | `"outputs/"` | Directory for the JSON report. |
| `--no-report` | `boolean` | No | `false` | Skip writing the report file. |
| `--smoke-test` | `boolean` | No | `false` | Run the self-test and exit. |

**Exit codes.** `0` on any successful classification — a tier gap is data, not a failure, so this tool does not signal one through its exit status. `2` is `SPEC_LOAD_FAILED`: input that could not be read. Reporting Tier 0 on an unreadable diff would be a silent false negative, so it refuses instead.

---

## 4. Outputs

**What does this tool return?**  
This tool returns command-line output and, depending on flags, may emit report files.

| Output Name | Type | Description |
|---|---|---|
| `stdout` | `log` | Console summary and status information. |
| `output artifacts` | `file` | Generated files when output/report flags are provided. |

---

## 5. Usage Example

**How is this tool invoked?**  

```bash
# Classify a set of paths, with a claim to measure against
python3 tools/molting_protocol_diff_v1_0.py \
  --files behavior_spec.json docs/design.md --claimed 0 --no-report
# -> WARN  under-claim: claimed Tier 0, diff measures Tier 1

# Just the number, for a CI step
git diff --name-only origin/main...HEAD \
  | python3 tools/molting_protocol_diff_v1_0.py --tier-only --files

# Full input, including a PR body the claim is parsed out of
python3 tools/molting_protocol_diff_v1_0.py --input data/input.json

# Self-test
python3 tools/molting_protocol_diff_v1_0.py --smoke-test
```
