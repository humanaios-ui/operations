---
name: langfuse-cli
description: Langfuse CLI usage reference — install, resource/action discovery, credentials, and common usage tips for `langfuse-cli`. Use for further tips on using the Langfuse CLI.
---

# Langfuse CLI Reference

Documentation: https://langfuse.com/docs/api-and-data-platform/features/cli

## Install

Use the exact `1.2.4` pin below for both runners. Review the package source, provenance, and integrity before credentialed use; review updates separately. Install or populate caches without `LANGFUSE_SECRET_KEY` or other credentials in the environment, then expose credentials only to the reviewed CLI. A controlled installation must use a reviewed lockfile and frozen dependency installation. Do not use unversioned packages, tags, or version ranges with either `npx` or `bunx`.

```bash
# Run directly (recommended)
npx langfuse-cli@1.2.4 api <resource> <action>
bunx langfuse-cli@1.2.4 api <resource> <action>

# Or install globally
npm i -g langfuse-cli@1.2.4
langfuse api <resource> <action>
```

## Discovery

```bash
# List all resources and auth info
langfuse api __schema

# List actions for a resource
langfuse api <resource> --help

# Show args/options for a specific action
langfuse api <resource> <action> --help

# Preview the curl command without executing
langfuse api <resource> <action> --curl
```

## Credentials

Set environment variables:

```bash
export LANGFUSE_PUBLIC_KEY=pk-lf-...
export LANGFUSE_SECRET_KEY=sk-lf-...
export LANGFUSE_BASE_URL=https://cloud.langfuse.com  
```

## Tips

- Use `--json` for machine-readable JSON output
- Use `--curl` to preview the HTTP request without executing
- All list commands support filtering — check `<resource> <action> --help` for available options
- Check the Langfuse deployment version before selecting read endpoints (use deployment metadata or ask the administrator; do not infer it from the CLI version). On Cloud and self-hosted v4+, prefer `observations` (`GET /api/public/v2/observations`, cursor pagination and selective field groups). For pre-v4 self-hosted deployments, use the supported v1 Observations API (`GET /api/public/observations`, exposed as `legacy-observations-v1s` where available); confirm the operation in that deployment's API reference and CLI schema/help.
- On Cloud and self-hosted v4+, prefer `metrics` over `legacy-metrics-v1s`; on earlier deployments, use the supported endpoint in the deployment's API reference.
- Prefer `scores` over `legacy-score-v1s` for list/get operations
- For trace reads on Cloud and self-hosted v4+, query via `observations` (add `--trace-id` to scope to a known trace). For pre-v4 self-hosted deployments, use the supported v1 observations or traces endpoint documented by that deployment. See the [Observations API docs](https://langfuse.com/docs/api-and-data-platform/features/observations-api) for compatibility and the v1 → v2 mapping.
- Pagination: legacy v1 endpoints use `--limit` and `--page`; modern endpoints (`observations`, `metrics`, `scores`) use cursor-based pagination — pass `--limit`, then thread `meta.cursor` from the response into the next request's `--cursor`
