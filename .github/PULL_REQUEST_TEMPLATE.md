<!-- START_HERE.md has the map; CONTRIBUTING.md has the rules. This checklist keeps a PR honest. -->

## What & why

<!-- One or two sentences: what this changes and the reason. -->

## Zone

<!-- See GOVERNANCE.md. Delete the lines that don't apply. -->

- [ ] **Z1** — AI-executable, no ratification needed
- [ ] **Z2** — needs operator ratification (canonical record / finding registration)
- [ ] **Z3** — involves credentials / billing / deploy (operator-run)

## Checklist

- [ ] **Claim matches behavior** — the description reflects what the diff actually does
- [ ] **Document control** — if this adds/changes a controlled document, `document-registry.yaml` and frontmatter are updated (the CI gate will check)
- [ ] **Immune memory** — if this fixes or reveals a failure mode, it's registered in `REGISTERED.md` (F / H / IC) — link it: <!-- IC-000 -->
- [ ] **No secrets** — no credentials, tokens, or keys added (even placeholders)
- [ ] **Health** — ran `python3 tools/repo_health.py`; vitality not regressed

## Notes

<!-- Anything a reviewer should know: risks, follow-ups, open questions. -->
