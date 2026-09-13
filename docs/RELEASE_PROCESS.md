# Release & Versioning Process

## Scope

This repository uses `main` as the supported branch and publishes traceable versions through tags and release notes.

## Version sources

- Python package version: `setup.py` (`version`)
- Governance/doc state: commit SHA + release tag

## Release checklist

1. Confirm CI required checks are green (quality + security + registry/doc-control gates).
2. Run local health checks:
   - `python3 tools/repo_health.py --strict`
   - `python3 .doc-control/validate.py`
3. Confirm no unresolved BLOCKER security findings.
4. Bump `setup.py` version if package behavior changed.
5. Create annotated tag:
   - `vMAJOR.MINOR.PATCH`
6. Publish GitHub release with:
   - Summary of changes
   - Risks/known limitations
   - Validation evidence
7. Record the release link in operations tracking notes.

## Versioning policy

- **PATCH**: bug fixes, workflow/doc correctness fixes, no breaking behavior changes.
- **MINOR**: additive features, new workflows/tools, backward compatible.
- **MAJOR**: breaking process or API changes requiring migration.

## Release notes minimum fields

- Release tag
- Date
- Commit SHA
- Scope (governance, CI, tools, docs, security)
- Validation results
- Rollback note
