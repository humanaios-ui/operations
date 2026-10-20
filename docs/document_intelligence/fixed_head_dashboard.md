# Fixed-head file census

- Commit: `ad44c46f58beb5f3c7d9de1d248e7686795417dd`
- Tree paths: 2106
- Rows in this checkpoint: 2106
- Census complete: true
- Review verdict: **NOT_VERIFIED** (CodeRabbit is not called or authenticated by this tool)

## Disposition totals

| Checkpoint rows | Inspected | Evidence-mapped | Metadata-only | Excluded with reason | Blocked | Pending |
|---:|---:|---:|---:|---:|---:|---:|
| 2106 | 0 | 0 | 8 | 2 | 0 | 2096 |

Disposition counts below describe this checkpoint's rows; totals must equal the exact tree only when census is complete.

## Classification counts

| File kind | Count |
|---|---:|
| binary_media | 7 |
| generated_rendered | 4 |
| other_data_or_unknown | 142 |
| prose_document | 886 |
| secret_sensitive_candidate | 2 |
| source_code_and_comments | 517 |
| symlink | 1 |
| test_fixture_data | 166 |
| workflow_config_schema | 381 |

## Individually listed exceptions

- `.claude/skills/ai-gateway` — symlink; metadata_only: content not inspected; recorded from Git metadata only.
- `.env.example` — secret_sensitive_candidate; excluded_with_reason: potentially sensitive path; content not read or copied.
- `Archive 2.zip` — binary_media; metadata_only: content not inspected; recorded from Git metadata only.
- `Archive.zip` — binary_media; metadata_only: content not inspected; recorded from Git metadata only.
- `assets/brand/humanaios-witness.jpg` — binary_media; metadata_only: content not inspected; recorded from Git metadata only.
- `audits/REPORT_2_FINDINGS_LEDGER_S042727.docx` — binary_media; metadata_only: content not inspected; recorded from Git metadata only.
- `audits/REPORT_3_Z3_LEDGER_S042727.docx` — binary_media; metadata_only: content not inspected; recorded from Git metadata only.
- `audits/REPORT_4_BUGS_S042727.docx` — binary_media; metadata_only: content not inspected; recorded from Git metadata only.
- `audits/REPORT_5_DOCS_DISPOSITION_S042727.docx` — binary_media; metadata_only: content not inspected; recorded from Git metadata only.
- `frontend/grant-search-dashboard/.env.example` — secret_sensitive_candidate; excluded_with_reason: potentially sensitive path; content not read or copied.

## Unresolved per-path metadata

Owner, generator, document-registry identity, approval, FPCP lifecycle, references/tests, and visibility are recorded as unresolved or unassessed. No document content or private source payload was read. `PENDING` is not an exclusion or a finding of irrelevance.

