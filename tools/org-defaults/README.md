# org-defaults — standard community-health file templates

This directory holds the canonical org-wide templates for the four
**required** community-health files identified in the S-070726 mesh audit
(28 structural gaps across 10 repos):

| File | Purpose | Repos missing |
|---|---|---|
| `CODEOWNERS` | Code-review ownership map | 10 |
| `SECURITY.md` | Vulnerability-reporting policy | 8 |
| `CONTRIBUTING.md` | Contribution guidelines | 6 |
| `LICENSE` | Apache 2.0 (org default) | 4 |

## Using these templates

### Manual (one repo at a time)
Copy the relevant files into the target repo's root (or `.github/` for
CODEOWNERS/SECURITY.md if you prefer), then commit and open a PR.

**CODEOWNERS**: the default assigns `*` to `@humanaios-ui/doc-control`.
Customize the patterns for the repo's actual ownership structure before merging.

### Automated (batch seeding via script)

```bash
# Check which repos are missing standard files (Z1 — read-only)
python3 tools/seed_org_defaults.py --org humanaios-ui

# Check a specific subset
python3 tools/seed_org_defaults.py --org humanaios-ui --repos humanaios docs research

# Create PRs to add missing files (Z3 — requires PAT with repo write scope)
python3 tools/seed_org_defaults.py --org humanaios-ui --create-prs --token $MESH_SYNC_TOKEN

# Full help
python3 tools/seed_org_defaults.py --help
```

The `mesh-standard-files` GitHub workflow in `.github/workflows/` runs the check
automatically every Monday at 06:00 UTC and can be dispatched manually to trigger PR
creation (requires `MESH_SYNC_TOKEN` secret).

## Source of truth

The `operations` repo holds these templates as the org reference bar. When you
update an org-wide policy (e.g. the security contact or Zone-model description),
update it here first, then re-run the seed script with `--create-prs` to propagate
the change to other repos.

## Relationship to GitHub's org-level `.github` repo

GitHub's native "community health files" fallback uses a special `.github` repo at
the org level (`humanaios-ui/.github`). That repo would provide SECURITY.md and
CONTRIBUTING.md as org-level defaults visible to repos that don't have their own.
The templates here are the source content for that repo if/when it is created.
`CODEOWNERS` and `LICENSE` do **not** work via the org-level `.github` repo —
they must be in each individual repo.
