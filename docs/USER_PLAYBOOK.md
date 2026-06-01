# HumanAIOS Operations User Playbook

_Last updated: 2026-06-01_

## What this repository is for

This repository appears to serve two closely related purposes:

1. **Canonical operating-process documentation for HumanAIOS** — governance, rituals, runbooks, registries, and operating state documents.
2. **Operational research and automation assets** — ACAT dataset documentation, ACAT automation guidance, Python tooling, SQL schema/migration files, workflow automation, and deployment configuration.

In plain language: this is not just a codebase and not just a docs repo. It is a **source-of-truth operations repository** that mixes governance documents, research artifacts, automation tools, and deployment/support files.

## Who it is intended for

This repo appears to be useful for several audiences:

- **Maintainers / operators** who manage HumanAIOS process, governance, and operational state.
- **Developers** working on ACAT-related tooling, MCP tooling, automations, and integrations.
- **Researchers** using the ACAT dataset and related methodology documents.
- **Collaborators / reviewers** who need to understand what is canonical, what is experimental, and how the repository is organized.
- **AI assistants working in the repo** that need a safe mental model of what files are operationally sensitive.

## How the major folders and files are organized

### Top-level canonical documents

These files look like repository-defining or governance-defining documents:

- `CURRENT.md` — current operating state / session-open reference.
- `REGISTERED.md` — registry of findings, hypotheses, and corrections.
- `SESSION_RITUALS.md` — session open/close protocols.
- `GOVERNANCE.md` — governance reference.
- `OPERATOR_RUNBOOK.md` — operator-oriented guidance.
- `DRIFT_LOG.md` — drift tracking.
- `SEED.md`, `Z3_PROTOCOL.md`, `SUBSTRATE_CAPABILITY_REGISTRY.md` — process/protocol/capability references.

These appear to be high-sensitivity files because they likely define the operating model.

### `docs/`

Documentation for collaborators, implementation, and reference material.

Observed examples:

- `docs/README.md` — docs entry point.
- `docs/INTEGRATION_MAP_V1_S-051126-01.md` — engineering/integration map.
- `docs/G-01/` — rendered implementation/reference HTML.

This folder is the best place for user-facing orientation documents like this playbook and repository recommendation reports.

### `acat/`

ACAT-specific module documentation and likely code/assets for the ACAT automation system.

Observed example:

- `acat/README.md` — ACAT automation quickstart and live request validation steps.

The repository README currently presents the repo heavily through the lens of the ACAT dataset, while other repository files position the repo as broader operating-process infrastructure.

### `tools/`

Python and related operational tools.

Observed examples include:

- pipeline/orchestration tools
- governance fetchers/mappers
- report writers
- auditing tools
- Slack/Supabase integration tools
- `server.py` for unified MCP serving
- `repo_discovery_v1_0.py` for GitHub repository discovery

This is currently the main code/tooling area of the repository.

### `workflows/`

Automation definitions, including YAML and JSON workflow/orchestration artifacts.

Observed examples:

- `workflows/haios_audit.yml`
- `workflows/research_agent.yml`
- `workflows/acat_pipeline_trigger.yml`
- `workflows/n8n_acat_claude_runner.json`

These appear to define operational automation and may have secret/env dependencies.

### `sql/`

Database foundation, schema, and migration files.

Observed examples:

- foundation SQL
- migration SQL
- pipeline health schema

These are operationally sensitive because changes may affect persistence and reporting.

### `architecture/`

Design and systems-reference artifacts.

Observed examples:

- `SYSTEM_MAP.mermaid`
- ACAT automation planning docs
- architecture notes

### `applications/`

Application-related materials, currently split into:

- `applications/draft/`
- `applications/submitted/`

### Other observed content

- `railway.toml` and `railway_smoke_test.sh` — deployment and smoke test support.
- HTML dashboard/doc files in the repo root.
- `DashboardTab.tsx` — standalone TSX file at root; this should be treated carefully because its role is not obvious from structure alone.
- `audits/`, `ic_archive/` — likely archival/audit materials.

## How a new user should start using the repository

Recommended order:

1. Read `docs/README.md`.
2. Read `CURRENT.md`.
3. Read `REGISTERED.md`.
4. Read `SESSION_RITUALS.md`.
5. Read `OPERATOR_RUNBOOK.md` if you will operate the system.
6. Read `acat/README.md` if you need ACAT API / ingestion workflow details.
7. Inspect `tools/`, `workflows/`, and `sql/` only after you understand the canonical docs.

If your goal is specifically code execution, also review:

- `requirements.txt`
- `railway.toml`
- `railway_smoke_test.sh`
- `tools/server.py`

## How developers should contribute

Recommended developer workflow:

1. **Read the canonical docs first** so code changes do not drift from the operating model.
2. Work in feature branches.
3. Treat governance/process documents as controlled surfaces.
4. Make the smallest possible change set.
5. Update docs when tool behavior changes.
6. Run local smoke checks where possible.
7. Ask for human review before changing governance, workflow, SQL, or deployment files.

For code contributions specifically:

- Add new operational scripts/tools under `tools/` or `scripts/` depending on purpose.
- Keep user-facing docs in `docs/`.
- Keep deployment assumptions explicit; do not hide them in code.
- Prefer opt-in and confirmation-based behavior for GitHub/network actions.

## How researchers or collaborators should use the documents

Researchers and collaborators should mainly consume:

- `README.md`
- `docs/README.md`
- `CURRENT.md`
- `REGISTERED.md`
- `SESSION_RITUALS.md`
- `docs/INTEGRATION_MAP_V1_S-051126-01.md`
- `acat/README.md`

If the goal is research methodology or dataset usage, prioritize ACAT and registry materials over infrastructure code.

If the goal is operational understanding, prioritize governance/runbook/integration-map files.

## How to run, test, or deploy the project if applicable

### Python environment

The repository includes `requirements.txt` with:

- `fastapi`
- `uvicorn[standard]`
- `jsonschema`
- `PyYAML`
- `python-dotenv`
- `certifi`

Basic setup likely looks like:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### MCP server

`tools/server.py` indicates a unified MCP server entrypoint.

Likely usage:

```bash
cd tools
python server.py --smoke
python server.py --serve
```

Note: because `server.py` imports sibling modules directly, running it from the `tools/` directory may be the safest assumption unless packaging is improved.

### ACAT API / local validation

`acat/README.md` describes a live paired-session quickstart involving:

- `GET /api/v1/acat/health`
- `POST /api/v1/acat/intake/phase1`
- `POST /api/v1/acat/intake/phase3`
- verification in Supabase

### Deployment

`railway.toml` indicates Railway deployment via:

```bash
python3 -m uvicorn acat.api.app:app --host 0.0.0.0 --port $PORT
```

This implies a deployable ASGI app exists at `acat.api.app:app`.

### Smoke testing

`railway_smoke_test.sh` provides an HTTP smoke test for deployed environments.

Usage:

```bash
bash railway_smoke_test.sh
bash railway_smoke_test.sh https://your-deployment-url
```

### Workflows

The repo also contains workflow/orchestration files in `workflows/`, but they appear to depend on secrets and external systems such as n8n and possibly GitHub Actions-style execution environments.

## What files are safe to edit

Usually safer to edit:

- New files in `docs/` that add orientation or non-canonical supporting documentation.
- New scripts in `scripts/` that are clearly additive and do not auto-execute.
- Existing developer utilities in `tools/` if you understand their role and keep behavior backward compatible.
- Non-canonical explanatory docs in `architecture/` or `docs/`, with review.

Examples of relatively safe additive work:

- playbooks
- recommendation reports
- helper scripts
- CLI wrappers that require confirmation before action

## What files should not be changed without review

Human review strongly recommended before changing:

- `CURRENT.md`
- `REGISTERED.md`
- `SESSION_RITUALS.md`
- `GOVERNANCE.md`
- `OPERATOR_RUNBOOK.md`
- `Z3_PROTOCOL.md`
- `SUBSTRATE_CAPABILITY_REGISTRY.md`
- anything in `sql/`
- anything in `workflows/`
- deployment files like `railway.toml`
- workflow-triggering shell scripts
- root HTML dashboards or presentation artifacts when public-facing behavior matters

These files appear to define canonical process, production behavior, persistence, or public/operational state.

## Recommended workflows

### First-time users

1. Read `docs/README.md`.
2. Read `CURRENT.md` and `REGISTERED.md`.
3. Decide whether your path is:
   - governance/process
   - research/dataset
   - developer/tooling
4. If developer/tooling, install Python dependencies and review `tools/server.py` and `acat/README.md`.

### Contributors

1. Read canonical docs first.
2. Confirm whether your target file is canonical, operational, or additive.
3. Prefer additive documentation/scripts before modifying sensitive files.
4. Open small, reviewable changes.
5. Document assumptions and gaps explicitly.

### Maintainers

1. Treat root governance documents and registries as protected surfaces.
2. Review workflow, SQL, deployment, and automation changes carefully.
3. Keep the docs index current when adding major repo capabilities.
4. Ensure public claims in docs match actual code/workflow behavior.

### Research collaborators

1. Start with the ACAT dataset README and integration/governance context docs.
2. Use the repository as a source-of-truth reference, not as proof that every planned system element is production-live.
3. Check for explicit status language before citing implementation maturity.

### AI assistants working in the repo

1. Read `docs/README.md`, `CURRENT.md`, and `REGISTERED.md` first.
2. Do not infer production behavior from filenames alone.
3. Do not change canonical governance/process files without explicit instruction and review.
4. Prefer additive outputs in `docs/` and `scripts/`.
5. Be explicit about unknowns, missing tests, or missing environment assumptions.
6. Never automate destructive or external actions without confirmation.

## Known Gaps / Needs Human Review

The current repository has several usability gaps that should be acknowledged directly:

1. **README ambiguity**
   - The top-level `README.md` is currently ACAT-dataset-centric.
   - The rest of the repository presents a broader operations/governance/tooling system.
   - A new user may not immediately understand that both are present in one repository.

2. **No unified contributor guide observed**
   - No top-level `CONTRIBUTING.md` was identified in the audited materials.

3. **No clear test inventory observed**
   - There are smoke tests and self-tests, but no obvious dedicated `tests/` directory was identified in the repository snapshot reviewed.

4. **Workflow location is nonstandard**
   - Workflows are under `workflows/` rather than the usual `.github/workflows/` location.
   - This may be intentional, but new contributors could misread these as automatically active GitHub Actions workflows.

5. **Tool execution assumptions are implicit**
   - `tools/server.py` imports sibling modules directly, which can make execution context sensitive.

6. **Deployment assumptions are only partially documented**
   - Railway deployment is visible, and Supabase is referenced, but complete env-var documentation was not found in the files reviewed.

7. **Operational sensitivity is not clearly labeled throughout the repo**
   - Some files are obviously canonical, but there is not yet a single short guide explaining safe vs. sensitive edit zones.

This playbook is intended to reduce those gaps, but maintainers should validate it against live operational expectations.
