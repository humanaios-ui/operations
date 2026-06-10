# SKILL: document_ingestor_v1_0

## 1. Description

**What does this tool do?**  
Base document ingestion layer.

---

## 2. Purpose

**Why does this tool exist?**  
This tool exists to support the `infrastructure_tool` workflow in this repository and provide repeatable command-line execution for the `document_ingestor_v1_0` process.

---

## 3. Parameters and Inputs

**What are the required inputs for this tool?**  
The table below lists command-line parameters discovered for this tool. Use `--help` for the complete interface.

| Parameter Name | Type | Required | Default Value | Description |
|---|---|---|---|---|
| `--analyzer-output` | `string` | No | `None` | Command-line option for this tool. |
| `--document-layer` | `string` | No | `"governance_document"` | Command-line option for this tool. |
| `--document-title` | `string` | No | `""` | Command-line option for this tool. |
| `--document-version` | `string` | No | `""` | Command-line option for this tool. |
| `--document-source-url` | `string` | No | `""` | Command-line option for this tool. |
| `--document-authors` | `string` | No | `""` | Command-line option for this tool. |
| `--document-type` | `string` | No | `""` | Command-line option for this tool. |
| `--arch-dims` | `string` | No | `""` | Command-line option for this tool. |
| `--session` | `string` | No | `""` | Command-line option for this tool. |
| `--output` | `string` | No | `"/home/claude/work/doc_corpus/staged"` | Command-line option for this tool. |
| `--manifest` | `string` | No | `"/home/claude/work/doc_corpus/document_corpus_manifest.json"` | Command-line option for this tool. |
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
python tools/document_ingestor_v1_0.py --help
```
