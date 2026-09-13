# Codebase Boundaries & CI Scope Map

## Purpose

Define module boundaries to reduce cross-surface drift and align CI responsibilities.

## Primary code surfaces

1. `src/humanaios_operations/`
   - Packaged operations CLI/application modules.
   - Baseline type-check scope.

2. `acat/`
   - ACAT service, API routes, scoring, and ACAT-specific tests.
   - Service/security and behavior testing scope.

3. `tools/`
   - Governance/automation tools and tool test suites.
   - Builder/behavioral compliance scope.

4. Repository-root scripts (`*.py` in root)
   - Orchestration/legacy runtime utilities.
   - Health/smoke and targeted regression scope.

5. UI/JS/TS (`ui/`, root `*.ts`/`*.tsx`, tool JS utilities)
   - Non-Python visualization/integration surfaces.
   - Syntax/lint scope when JS/TS gates are enabled.

## CI scope alignment

- `quality-baseline.yml`
  - lint scope: `src/humanaios_operations`, `tools`, `acat`, `tests`
  - type-check scope: `src/humanaios_operations`
  - test scope: key `tools/tests` pytest suites
- `builder-lint.yml`: changed `tools/**/*.py`
- `behavioral-compliance.yml`: changed `tools/**/*.py`
- `document-control.yml`: markdown + registry surfaces
- `security-gates.yml`: secrets + dependency vulnerability scanning

## Ownership intent

- Governance-controlled markdown: CODEOWNERS doc-control/governance/research teams.
- Tooling correctness: tools maintainers + CI gates.
- Service behavior: ACAT/API maintainers.

## Boundary rules

- New Python packages should prefer `src/` or `acat/` (not root) unless intentionally standalone.
- New tests should live beside their subsystem (`tools/tests`, `acat/tests`, `tests/`).
- Workflow paths must assume repository root checkout only (no extra nested `operations/` path).
