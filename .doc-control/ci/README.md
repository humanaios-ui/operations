# CI workflow (staged — relocate to activate)

`document-control.yml` here is the Phase-2 gate. It is parked under `.doc-control/ci/`
rather than `.github/workflows/` because the PR was pushed with a token lacking the
GitHub `workflow` scope (GitHub blocks workflow-file writes without it).

**To activate:** move it into place with a workflow-scoped push:

```bash
git mv .doc-control/ci/document-control.yml .github/workflows/document-control.yml
git commit -m "ci: activate document-control gate"
git push   # requires: gh auth refresh -s workflow   (or a PAT with workflow scope)
```

Until moved, the validator still runs locally: `python3 .doc-control/validate.py`.
