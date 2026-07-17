# SKILL: haios_agent_orchestrator_v1_0_patched

## 1. Description

**What does this tool do?**  
Agent orchestration layer for multi-tool dispatch.

---

## 2. Purpose

**Why does this tool exist?**  
This tool exists to support the `infrastructure_tool` workflow in this repository and provide repeatable command-line execution for the `haios_agent_orchestrator_v1_0_patched` process.

---

## 3. Parameters and Inputs

**What are the required inputs for this tool?**  
The table below lists command-line parameters discovered for this tool. Use `--help` for the complete interface.

| Parameter Name | Type | Required | Default Value | Description |
|---|---|---|---|---|
| `--help` | `boolean` | No | `false` | Command-line option for this tool. |

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
python tools/haios_agent_orchestrator_v1_0_patched.py --help
```
