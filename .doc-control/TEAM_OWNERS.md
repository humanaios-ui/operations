# Document-Control Team Ownership

> Source of truth for **who owns what** in the controlled-document system.
> `CODEOWNERS` references these GitHub teams; this file records their membership +
> the area→team mapping. Seeded 2026-07-02 — fill in the `TODO` members.

## Teams (create in the org, then add members)

| Team (`@humanaios-ui/…`) | Purpose | Members (initial) |
|---|---|---|
| `doc-control` | Owns the registry, schema, validator, CI, drift monitor. The **control maintainer**. | `@carly` *(maintainer)* · **TODO:** mesh-support operator |
| `governance` | Owns `GOV`-area docs (GOVERNANCE, principles, traditions, charters). | `@carly` · **TODO:** governance lead |
| `research` | Owns `RES`-area docs (ACAT, methods, validation, findings, `REGISTERED.md`). | `@carly` · **TODO:** research lead |

> Only `@carly` is confirmed. Others are `TODO` — a CODEOWNERS group with one member
> still enforces (that member's review is required); add more as roles are assigned.

## Area → team → doc_id prefix

| Area | doc_id prefix | Owning team | Notes |
|---|---|---|---|
| Governance | `HAIOS-GOV-*` | `governance` | non-negotiable / policy docs |
| Research | `HAIOS-RES-*` | `research` | figures/claims gated by content-accuracy audit |
| Process | `HAIOS-PROC-*` | `doc-control` | runbooks, templates, checklists |
| Operations | `HAIOS-OPS-*` | `doc-control` | state/roadmap/drift docs |
| Collaborator | `HAIOS-COLLAB-*` | `doc-control` | external reports — DD-sensitive, review carefully |
| Site pages | `HAIOS-WEB-*` | `doc-control` | public site; coordinate with the `website` practice |

## Membership commands (run once teams exist)

```bash
ORG=humanaios-ui
for t in doc-control governance research; do
  gh api orgs/$ORG/teams -f name=$t -f privacy=closed 2>/dev/null || true
  gh api -X PUT orgs/$ORG/teams/$t/memberships/carly -f role=maintainer
done
# add real members as roles are assigned:
# gh api -X PUT orgs/$ORG/teams/governance/memberships/<gh-username> -f role=member
```

## Cross-repo note (activation phase A5)

`CODEOWNERS` is **per-repo**. When extending doc-control to the other 4 repos,
copy the operations `CODEOWNERS` pattern into each repo, pointing at these same
org teams so ownership stays consistent across the ecosystem.
