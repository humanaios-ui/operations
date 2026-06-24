# SKILL: haios_cli

## 1. Description

**What does this tool do?**  
Terminal CLI — query the full HumanAIOS system using live GitHub context + Claude API. Modes: `ask` (default), `run`, `check`, `chat`.

---

## 2. Purpose

**Why does this tool exist?**  
This tool exists to support the `connector_tool` workflow in this repository and provide repeatable command-line execution for the `haios_cli` process.

---

## 3. Parameters and Inputs

**What are the required inputs for this tool?**  
The table below lists command-line parameters discovered for this tool. Use `--help` for the complete interface.

| Parameter Name | Type | Required | Default Value | Description |
|---|---|---|---|---|
| `--mode` | `string` | No | `"ask"` | Command-line option for this tool. |
| `--repo` | `string` | No | `None` | Command-line option for this tool. |
| `--output` | `string` | No | `None` | Command-line option for this tool. |
| `--no-stream` | `boolean` | No | `false` | Command-line option for this tool. |
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
python tools/haios_cli.py --help
```
