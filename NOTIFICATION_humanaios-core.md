# To: humanaios Core Team

**Subject: Document Control Activation — Your Repo Rollout: Aug 15**

---

Dear Core Team,

HumanAIOS document control system is **live as of today** (2026-07-29). Your repo, humanaios, is scheduled to onboard **August 15** (Thursday) — last in the multi-repo rollout.

## What's Active Now

- Registry: 34 controlled documents registered
- CI gate: Operations repo only (your repo unaffected until Aug 15)
- Scaffolding: Ready for new docs

## Your Action Required by July 31

**Comment on this document** with your area's classification rules:

```
Area: Core Infrastructure (or your team name)
Patterns: schema.sql (exclude), README.md (if exists), CONTRIBUTING.md
CODEOWNERS: @humanaios/core
```

Note: Source code (schema.sql, .py, .js) is **excluded** from control (code governance is separate). Only documentation is registered.

**Location:** `/operations/A4_INTAKE_PIPELINE_SPEC.md` (end of document, "Rules Template" section)

## Your Repo's Rollout (Aug 15)

On **Thursday, Aug 15, 2026:**

1. **9 AM:** mesh-support deploys document-control CI to humanaios
2. **9:30 AM:** Notification + summary
3. **9:30 AM - 5 PM:** First doc-touching PRs may hit CI validation
4. **Fri (Aug 16):** You review docs, add frontmatter if needed

**Docs in your registry (5 total):**
- schema.sql (→ **excluded**, stays with code governance)
- Possible: README, CONTRIBUTING, or API docs

**Your role:** Verify which docs are truly "controlled documents" (governance/readme) vs. source code (excluded).

## Timeline

| Date | Milestone |
|------|-----------|
| **July 31** | Deadline: submit area rules |
| **Aug 5-11** | A4: Intake pipeline automated |
| **Aug 12-14** | A5: lasting-light-ai, humanaios-internal, empirica-foundation rollout |
| **Aug 15 (Thu)** | **Your repo rollout** — CI gate deployed |
| **Aug 16** | You: verify docs + approve if needed |
| **Aug 19+** | A6: Drift monitor live (all 5 repos watched) |

## Special Notes for humanaios

- **Source code excluded:** schema.sql, .py, .js etc. are NOT registered — stay in code governance
- **Documentation only:** README.md, CONTRIBUTING.md, API docs etc. are registered
- **Registry link:** You'll be able to reference other humanaios docs via HAIOS-* doc_id (cross-repo traceability)

## Questions

- **"Is schema.sql a controlled document?"** → No; it's source code. Exclude it from registry.
- **"What if we have an API spec?"** → If markdown (.md) — register it. If generated from code (OpenAPI YAML) — exclude it.

**File an issue:** Tag `document-control/question` on humanaios-ui/operations

## Links

- Activation brief: `operations/DOCUMENT_CONTROL_ACTIVATION_BRIEF.md`
- Rollout plan: `operations/A5_MULTIrepo_ROLLOUT_PLAN.md` (find "humanaios")
- Full method: `operations/DOCUMENT_CONTROL_PLAN.md`

---

**Ready?** Submit area rules by July 31. On Aug 15, we deploy; you verify + approve.

— mesh-support (autonomy practice)
