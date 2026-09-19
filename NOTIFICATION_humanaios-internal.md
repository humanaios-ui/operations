# To: humanaios-internal Operations & Leadership

**Subject: Document Control Activation — Your Repo Rollout: Aug 13**

---

Dear Operations & Leadership Team,

HumanAIOS document control system is **live as of today** (2026-07-29). Your repo, humanaios-internal, is scheduled to onboard **August 13** (Tuesday).

## What's Active Now

- Registry: 34 controlled documents registered with unique IDs (HAIOS-AREA-###)
- CI gate: Operations repo only (your repo not yet affected)
- Governance: CODEOWNERS, maintainer assignment, external-link policy

## Your Action Required by July 31

**Comment on this document** with your area's classification rules:

```
Area: Collaboration (or Operations)
Patterns: collaborators/*.html, OPERATOR_RUNBOOK.md, partnership agreements
CODEOWNERS: @humanaios-internal/leadership (or your group)
```

These rules help the intake pipeline (A4) classify new docs in your workflow.

**Location:** `/operations/A4_INTAKE_PIPELINE_SPEC.md` (end of document, "Rules Template" section)

## Your Repo's Rollout (Aug 13)

On **Tuesday, Aug 13, 2026:**

1. **9 AM:** mesh-support deploys document-control CI to humanaios-internal
2. **9:30 AM:** Notification + summary
3. **9:30 AM - 5 PM:** First PRs may hit schema validation — expected
4. **Wed (Aug 14):** You review docs, add frontmatter, approve

**Docs in your registry (9 total):**
- OPERATOR_RUNBOOK.md (core operations)
- Collaborator reports (EMPIRICA_JOINT_REPORT_S-051426-02.html, etc.)

**Your role:** Approve docs by adding frontmatter header + setting `status: approved`.

## Timeline

| Date | Milestone |
|------|-----------|
| **July 31** | Deadline: submit area rules |
| **Aug 5-11** | A4: Intake pipeline automated |
| **Aug 13 (Tue)** | **Your repo rollout** — CI gate deployed |
| **Aug 14** | You: review + approve docs |
| **Aug 15+** | A6: Drift monitor (link-rot + staleness detection) |

## Special Notes for humanaios-internal

- **Backup maintainer:** Your team is the fallback if mesh-support is unavailable (see MAINTAINER_ASSIGNMENT.md)
- **Collaborator reports:** These are governed by confidentiality + partnership terms — registry respects that (frontmatter includes `sensitivity: confidential` option if needed)
- **External-link policy:** Partnership docs often link to external partners — broken links will be flagged by drift monitor; you decide fix/defer/supersede

## Questions

- **"How do I approve a confidential document?"** → Same process; frontmatter includes `sensitivity` field
- **"What if a collaborator partner name should be hidden?"** → Mark as `sensitive: true` in frontmatter; registry shows it but masks external visibility
- **"Backup maintainer duties?"** → See .doc-control/MAINTAINER_ASSIGNMENT.md (escalation trigger + role)

**File an issue:** Tag `document-control/question` on humanaios-ui/operations

## Links

- Activation brief: `operations/DOCUMENT_CONTROL_ACTIVATION_BRIEF.md`
- Rollout plan: `operations/A5_MULTIrepo_ROLLOUT_PLAN.md` (find "humanaios-internal")
- Maintainer assignment: `operations/.doc-control/MAINTAINER_ASSIGNMENT.md`

---

**Ready?** Submit area rules by July 31. On Aug 13, we deploy; you approve.

— mesh-support (autonomy practice)
