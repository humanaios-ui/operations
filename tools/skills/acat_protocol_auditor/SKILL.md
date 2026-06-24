# SKILL: acat_protocol_auditor

## 1. Description

**What does this tool do?**  
Audits session close posts against Section B protocol requirements (D-04, D-05, open/close tag balance).

---

## 2. Purpose

**Why does this tool exist?**  
This tool exists to support the `audit_tool` workflow in this repository and provide repeatable command-line execution for the `acat_protocol_auditor` process.

---

## 3. Parameters and Inputs

**What are the required inputs for this tool?**  
The table below lists command-line parameters discovered for this tool. Use `--help` for the complete interface.

| Parameter Name | Type | Required | Default Value | Description |
|---|---|---|---|---|
| `--input` | `string` | No | `None` | Command-line option for this tool. |
| `--text` | `string` | No | `None` | Command-line option for this tool. |
| `--output` | `string` | No | `"outputs/"` | Command-line option for this tool. |
| `--resonance-only` | `boolean` | No | `false` | Command-line option for this tool. |
| `--smoke-test` | `boolean` | No | `false` | Command-line option for this tool. |

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
# Show all supported options
python tools/acat_protocol_auditor.py --input data/input.json
```
