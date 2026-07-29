---
doc_id: HAIOS-OPS-010
title: Area Rules Collection Status Tracker
revision: 1
status: draft
owner: "@humanaios-ui/operations"
created_at: 2026-07-29
---

# Area Rules Collection Status (July 29 - July 31)

**Deadline:** July 31, 2026 EOD  
**Purpose:** Collect area classification rules for A4 intake pipeline  
**Next step:** Validate + test Aug 1-4, activate Aug 5

---

## Submission Checklist

### lasting-light-ai (Research)
- **Rollout:** Aug 12
- **Docs in registry:** 16 (METHODS, VALIDATION, ACAT*, methodology.html, etc.)
- **Status:** 📋 AWAITING SUBMISSION
- **Expected patterns:** Extension (.md, .html), Name (*METHODS*, *VALIDATION*, *ACAT*), Path (public/)
- **Submission method:** Comment on NOTIFICATION_lasting-light-ai.md OR AREA_RULES_COLLECTION.md
- **Contact:** @lasting-light-ai/research

### humanaios-internal (Ops & Leadership)
- **Rollout:** Aug 13
- **Docs in registry:** 9 (OPERATOR_RUNBOOK, collaboration reports, partnership docs)
- **Status:** 📋 AWAITING SUBMISSION
- **Expected patterns:** Path (collaborators/), Name (*REPORT*, *RUNBOOK*), Header (collaborator, partnership)
- **Submission method:** Comment on NOTIFICATION_humanaios-internal.md OR AREA_RULES_COLLECTION.md
- **Contact:** @humanaios-internal/ops

### empirica-foundation (Governance)
- **Rollout:** Aug 14
- **Docs in registry:** 4 (cross-org artifacts, evaluation data)
- **Status:** 🟡 SCOPE CLARIFICATION NEEDED (Aug 10)
- **Note:** Some docs may be empirica-scoped (use empirica's control system, not humanaios)
- **Action:** Will send scope briefing Aug 10; rules may not be needed if empirica-scoped
- **Contact:** @empirica-foundation/gov

### humanaios (Core)
- **Rollout:** Aug 15
- **Docs in registry:** 5 (README, CONTRIBUTING, API docs)
- **Status:** 📋 AWAITING SUBMISSION
- **Expected patterns:** Name (README*, CONTRIBUTING*), EXCLUDE (*.sql, *.py, *.js, src/)
- **Submission method:** Comment on NOTIFICATION_humanaios-core.md OR AREA_RULES_COLLECTION.md
- **Contact:** @humanaios/core

---

## Submission Instructions (Quick)

**1. Find your notification:**
- lasting-light-ai: `NOTIFICATION_lasting-light-ai.md`
- humanaios-internal: `NOTIFICATION_humanaios-internal.md`
- humanaios: `NOTIFICATION_humanaios-core.md`

**2. Copy template from `AREA_RULES_SUBMISSION_TEMPLATE.yaml`**

**3. Fill in your patterns:**
```yaml
area_name: "Research"
area_code: "RES"
ownership_group: "@lasting-light-ai/research"
patterns:
  by_extension: [".md", ".html"]
  by_name: ["*METHODS*", "*VALIDATION*"]
  # ... etc
```

**4. Submit as:**
- Comment on your notification file, OR
- Comment on `AREA_RULES_COLLECTION.md`, OR
- Reply to email notification with filled template

**5. Deadline:** July 31 EOD

---

## Timeline

| Date | Milestone |
|------|-----------|
| **July 29 (Tue)** | Collection documents created; notifications sent |
| **July 30 (Wed)** | Practices submit rules (24-hr reminder) |
| **July 31 (Thu)** | Submission deadline EOD |
| **Aug 1 (Fri)** | Validation begins (check patterns, test conflicts) |
| **Aug 2-4 (Sat-Mon)** | Test on historical data, publish final rules |
| **Aug 5 (Tue)** | A4 intake pipeline activates with rules |

---

## If No Submission

**Fallback for missing areas:** `fallback_action: "escalate_to_ops"`

Every new file will be routed to @humanaios-ui/operations for manual triage.

- ✅ Safe (nothing lost)
- ❌ Time-consuming (ops team does manual classification each week)

**Recommendation:** Submit rules by July 31 to avoid manual triage burden.

---

## Submitted Rules (Real-Time)

### ✅ lasting-light-ai
Status: PENDING  
Submitted: —  
Patterns: (awaiting)

### ✅ humanaios-internal
Status: PENDING  
Submitted: —  
Patterns: (awaiting)

### 🟡 empirica-foundation
Status: PENDING SCOPE CLARIFICATION  
Submitted: —  
Patterns: (depends on scope)

### ✅ humanaios
Status: PENDING  
Submitted: —  
Patterns: (awaiting)

---

## Questions?

**File an issue:** Tag `document-control/question` on humanaios-ui/operations

**Or comment here:** This document (AREA_RULES_COLLECTION_STATUS.md)

**Contact:** @empirica-mesh-support (primary maintainer)

---

## For mesh-support

### Validation Checklist (Aug 1-4)
- [ ] All submissions received by July 31
- [ ] Patterns parsed (check YAML syntax)
- [ ] No conflicts (same file matched by multiple areas)
- [ ] Test on historical `_inbox_files*/` data
- [ ] Publish final `area_rules.yaml`
- [ ] Notify practices: "Rules active as of Aug 5"

### Testing Script
```bash
python3 scripts/intake_pipeline.py --scan \
  --rules .doc-control/area_rules.yaml \
  --test-on-historical-data
```

### Deployment (Aug 5)
- Activate A4 intake workflow
- Monitor first run (check for misclassifications)
- Be ready to adjust rules if needed (low-cost update)

