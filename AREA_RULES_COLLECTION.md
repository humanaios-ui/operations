---
doc_id: HAIOS-OPS-009
title: Area Classification Rules Collection (A4 Input)
revision: 1
status: draft
owner: "@humanaios-ui/operations"
created_at: 2026-07-29
deadline: 2026-07-31
---

# Area Classification Rules Collection

**Deadline:** July 31, 2026 (EOD)  
**Purpose:** Seed A4 intake pipeline with area-specific document patterns  
**Submission:** Comment on this document OR reply to your practice's notification

---

## What We're Collecting

Each practice defines classification rules that tell the intake pipeline (A4) which documents belong to their area. Rules are patterns: file extensions, directory paths, naming conventions, header keywords.

**Format:** YAML (copy the template for your area, fill in, submit)

**Why:** When new files land in `_inbox_files*/`, the pipeline uses these rules to route them to the right owner for approval. Without rules, every inbox file requires manual triage.

---

## Template (Copy & Fill)

```yaml
---
area_name: "YOUR_AREA_NAME"
area_code: "AREA"  # GOV, PROC, COLLAB, RES, OPS, ENG, WEB, DOC, or new
ownership_group: "@humanaios-org/team-name"

# File patterns that belong in this area
patterns:
  by_extension:
    - ".md"      # Example: Markdown docs
    - ".html"    # Example: HTML reports
  
  by_path:
    - "collaborators/"    # Entire directory
    - "docs/governance/"  # Subdirectory
  
  by_name:
    - "*METHODS*"         # Filename pattern
    - "*VALIDATION*"
    - "*ACAT*"
  
  by_header:
    - "research paper"    # First line keyword (case-insensitive)
    - "methodology"

# Files to EXCLUDE (even if they match the above)
exclude:
  - "*.pdf"               # If PDFs are binaries
  - ".git*"               # Never capture git files
  - "*test*"              # Test files (code, not docs)

# Default fallback if no pattern matches
fallback_action: "escalate_to_ops"  # or: "quarantine" or specific team

# Notes (optional)
notes: |
  - Historical patterns from CURRENT.md + REGISTERED.md
  - Review-due cycle: quarterly (90 days)
  - Approval authority: @team-name (CODEOWNERS)
```

---

## Submissions So Far

### 1. lasting-light-ai (Research)
**Status:** 📋 AWAITING  
**Target rollout:** Aug 12  
**Docs in registry:** 16 (ACAT_PROMPT, METHODS, VALIDATION, methodology.html, etc.)

**Expected rules:**
```yaml
area_name: "Research"
area_code: "RES"
patterns:
  by_extension: [".md", ".html", ".txt"]
  by_name: ["*METHODS*", "*VALIDATION*", "*ACAT*", "*PROMPT*"]
```

**Submit to:** Comment on `NOTIFICATION_lasting-light-ai.md` OR this document

---

### 2. humanaios-internal (Operations & Leadership)
**Status:** 📋 AWAITING  
**Target rollout:** Aug 13  
**Docs in registry:** 9 (OPERATOR_RUNBOOK, collaboration reports, partnership agreements)

**Expected rules:**
```yaml
area_name: "Collaboration"  # or "Operations"
area_code: "COLLAB"  # or "OPS"
patterns:
  by_path: ["collaborators/"]
  by_name: ["*JOINT_REPORT*", "*OPERATIONAL_RECORD*", "*RUNBOOK*"]
  by_header: ["collaborator", "partnership"]
```

**Submit to:** Comment on `NOTIFICATION_humanaios-internal.md` OR this document

---

### 3. empirica-foundation (Governance)
**Status:** 📋 AWAITING  
**Target rollout:** Aug 14  
**Docs in registry:** 4 (cross-org artifacts, research records)

**Note:** Scope boundary clarification (Aug 10) — may not need rules if empirica-scoped  
**Submit to:** Will clarify in scope briefing (Aug 10)

---

### 4. humanaios (Core Infrastructure)
**Status:** 📋 AWAITING  
**Target rollout:** Aug 15  
**Docs in registry:** 5 (README, CONTRIBUTING, API docs — source code excluded)

**Expected rules:**
```yaml
area_name: "Core Infrastructure"
area_code: "OPS"
patterns:
  by_name: ["README*", "CONTRIBUTING*", "*.md"]
exclude:
  - "*.sql"           # Source code, not docs
  - "*.py"            # Source code
  - "*.js"            # Source code
  - "src/**"
```

**Submit to:** Comment on `NOTIFICATION_humanaios-core.md` OR this document

---

## How to Submit

**Option 1: Comment on this document**
```markdown
<!-- Copy template above, fill in, submit as comment -->

area_name: Research
area_code: RES
patterns:
  by_extension: [".md", ".html"]
  by_name: ["*METHODS*", "*VALIDATION*"]
```

**Option 2: Reply to your practice's notification email**
- Forward the filled template as part of your response

**Option 3: Create a PR with rules**
- Add to `.doc-control/area_rules.yaml` (will create if needed)
- One section per area

---

## Review & Validation (Aug 1-4)

Once all submissions are in, mesh-support will:
1. Validate patterns (no conflicts, clear precedence)
2. Test on historical `_inbox_files*/` data
3. Publish final `area_rules.yaml` for intake pipeline
4. Notify practices: "Your rules active as of Aug 5"

---

## FAQ

**Q: Can we have multiple areas in one practice?**  
A: Yes (e.g., Research + Operations). Submit separate sections per area.

**Q: What if we don't submit rules?**  
A: Default fallback is "escalate to ops" — every new file goes to @humanaios-ui/operations for manual triage. Not ideal for volume, but safe.

**Q: Can we update rules later?**  
A: Yes. Rules live in `.doc-control/area_rules.yaml` and can be updated anytime. Changes take effect at next A4 run (weekly).

**Q: What if a file matches multiple areas?**  
A: First match wins. Order your patterns from most-specific to least-specific.

**Q: Should we include code files in patterns?**  
A: No. Patterns should match only **documented files** (markdown, html, text). Exclude code (*.py, *.sql, src/).

---

## Deadline & Escalation

| Date | Action |
|------|--------|
| **July 31 (Wed) EOD** | Submission deadline |
| **Aug 1** | Validation begins |
| **Aug 2-4** | Testing on historical data |
| **Aug 5 (Mon)** | A4 pipeline activates with final rules |

**If missing by July 31:** Default "escalate to ops" used for that practice until rules submitted.

---

## Status Tracker (Live)

- [ ] **lasting-light-ai:** Rules submitted
- [ ] **humanaios-internal:** Rules submitted
- [ ] **empirica-foundation:** Scope clarification (Aug 10)
- [ ] **humanaios:** Rules submitted
- [ ] **All validated:** Aug 4
- [ ] **Activated in A4:** Aug 5

**Last updated:** 2026-07-29  
**Next update:** 2026-07-31 (EOD, after deadline)

---

## Example Submission (Complete)

```yaml
---
area_name: "Research"
area_code: "RES"
ownership_group: "@lasting-light-ai/research"

patterns:
  by_extension:
    - ".md"
    - ".html"
    - ".txt"
  
  by_name:
    - "*METHODS*"
    - "*VALIDATION*"
    - "*ACAT*"
    - "*PROMPT*"
    - "*methodology*"
  
  by_path:
    - "public/"
    - "research/"
  
  by_header:
    - "ACAT"
    - "methodology"
    - "research paper"

exclude:
  - "*.pdf"               # Research papers as binary
  - "src/**"              # Source code
  - "*test*.md"           # Test documentation

fallback_action: "escalate_to_ops"

notes: |
  Covers all research-related docs from ACAT scoring to methodology.
  External links (citations) checked biweekly by drift monitor.
  Approval cycle: quarterly (90 days review_due).
  Contact: @lasting-light-ai/research for questions.
```

---

**Submit by July 31.** Questions? File issue tagged `document-control/question` on humanaios-ui/operations.
