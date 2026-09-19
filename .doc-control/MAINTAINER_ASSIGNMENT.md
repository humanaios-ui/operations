# Document Control Maintainer Assignment

**Activated 2026-07-29**

## Primary Maintainer
- **Practice:** empirica-mesh-support (cross-practice plumbing expertise)
- **Role:** Owns registry, CI, drift monitor, cross-repo rollout coordination
- **Scope:** All 5 humanaios repos + operations control hub

## Backup Maintainer (Contingency)
- **Team:** humanaios-ui/operations
- **Rationale:** Operations repo is the control hub; team has natural ownership + access
- **Activation trigger:** When primary maintainer is unavailable (vacation, context switch, capacity constraint)
- **Duties:** Keep the registry current, monitor CI gate health, triage drift alerts

## Escalation Path
1. **First escalation (backup unavailable):** File a GitHub issue on operations repo tagged `document-control/critical`
2. **Org escalation (both unavailable):** Reach out to Carly (@carly) — operations control is a governance blocker if unmaintained

## Ownership By Area (Document-Level)
Document-level ownership is distributed per CODEOWNERS (in `.github/CODEOWNERS`). Maintainers are responsible for *infrastructure* (registry, CI, monitor); document owners are responsible for *content* (accuracy, review-due compliance, frontmatter correctness).
