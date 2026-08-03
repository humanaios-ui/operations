# To: lasting-light-ai Research Team

**Subject: Document Control Activation — Your Repo Rollout: Aug 12**

---

Dear Research Team,

HumanAIOS document control system is **live as of today** (2026-07-29). Your repo, lasting-light-ai, is scheduled to onboard **August 12** (Monday).

## What's Active Now

- Registry: 34 controlled documents registered with unique IDs (HAIOS-AREA-###)
- CI gate: Operations repo only (your repo not yet affected)
- Template + scaffolding: Ready for new documents

## Your Action Required by July 31

**Comment on this document** with your area's classification rules:

```
Area: Research
Patterns: METHODS.*, VALIDATION.*, ACAT*, methodology.html, openai-activity.html
CODEOWNERS: @lasting-light-ai/research
```

These rules tell the intake pipeline (A4) which documents belong to your area.

**Location:** `/operations/A4_INTAKE_PIPELINE_SPEC.md` (end of document, "Rules Template" section)

## Your Repo's Rollout (Aug 12)

On **Monday, Aug 12, 2026:**

1. **9 AM:** mesh-support deploys document-control CI to lasting-light-ai
2. **9:30 AM:** You get a Slack notification with summary
3. **9:30 AM - 5 PM:** First PRs may fail CI (schema errors) — this is expected
4. **Tue-Wed (Aug 13-14):** You review docs, add/fix frontmatter, get CODEOWNERS approval

**Docs in your registry (16 total):**
- ACAT_PROMPT_V5_0.txt (core)
- METHODS.md (needs reconciliation — inbox copy larger)
- VALIDATION_PLAN.md (needs reconciliation)
- methodology.html, openai-activity.html, etc.

**Action:** Review each doc, add frontmatter header (copy template), approve.

## Timeline

| Date | Milestone |
|------|-----------|
| **July 31** | Deadline: submit area rules (comment on A4 spec) |
| **Aug 5-11** | A4: Intake pipeline automated (doesn't affect your repo yet) |
| **Aug 12 (Mon)** | **Your repo rollout** — CI gate + scaffolding deployed |
| **Aug 13-14** | You: review docs + add frontmatter |
| **Aug 15+** | A6: Drift monitor starts (biweekly link-rot + staleness checks) |

## Questions

- **"What if a doc fails CI validation?"** → See DOCUMENT_CONTROL_ACTIVATION_BRIEF.md FAQ
- **"Can we delete old versions?"** → Mark `superseded` instead (never delete)
- **"What about binary research papers?"** → Registry metadata only; binary excluded from CI

**File an issue:** Tag `document-control/question` on humanaios-ui/operations

## Links

- Activation brief: `operations/DOCUMENT_CONTROL_ACTIVATION_BRIEF.md`
- Rollout plan: `operations/A5_MULTIrepo_ROLLOUT_PLAN.md` (find "lasting-light-ai")
- Full method: `operations/DOCUMENT_CONTROL_PLAN.md`

---

**Ready?** Submit your area rules by July 31. We'll handle the infrastructure; you handle approval.

— mesh-support (autonomy practice)
