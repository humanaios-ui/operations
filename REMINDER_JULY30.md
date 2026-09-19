# REMINDER: Area Classification Rules — Due TOMORROW (July 31)

**Send this to all 4 practices on July 30 (Wednesday)**

---

## 📋 To: All HumanAIOS Practices

**Subject: Document Control — Area Rules Due TOMORROW (July 31 EOD)**

**TL;DR:** Submit your area's classification rules by **July 31 EOD** so A4 intake pipeline activates on Aug 5. Takes 10 minutes. Template provided.

---

## What You Need to Do

1. **Copy this template:**
   ```yaml
   area_name: "YOUR_AREA"
   area_code: "YOUR"
   ownership_group: "@your-org/your-team"
   patterns:
     by_extension: []
     by_path: []
     by_name: []
   exclude: []
   ```

2. **Fill in your patterns** (file extensions, paths, names)
   - Example: `by_name: ["*METHODS*", "*VALIDATION*"]`

3. **Submit tomorrow by EOD:**
   - Comment on `AREA_RULES_COLLECTION.md` in operations repo, OR
   - Reply to your practice's notification email

**That's it.** Takes 10 minutes. Rules activate Aug 5.

---

## Why This Matters

Without rules, every new inbox file goes to ops for manual classification (slow).  
With rules, the intake pipeline (A4) auto-classifies by your patterns (fast + automated).

**Timeline:**
- July 31: Submit rules
- Aug 1-4: We validate & test on historical data
- Aug 5: A4 pipeline goes live with your rules

---

## Your Practice's Info

### lasting-light-ai (Research)
- **Rollout:** Aug 12
- **Expected area:** RES (Research)
- **Expected patterns:** Extension (.md, .html), Name (*METHODS*, *VALIDATION*, *ACAT*)
- **Submit to:** `AREA_RULES_COLLECTION.md` or `NOTIFICATION_lasting-light-ai.md`

### humanaios-internal (Ops & Leadership)
- **Rollout:** Aug 13
- **Expected area:** COLLAB (Collaboration) or OPS
- **Expected patterns:** Path (collaborators/), Name (*REPORT*, *RUNBOOK*)
- **Submit to:** `AREA_RULES_COLLECTION.md` or `NOTIFICATION_humanaios-internal.md`

### empirica-foundation (Governance)
- **Rollout:** Aug 14
- **Status:** Scope clarification needed (Aug 10) — may not need rules yet
- **Submit to:** Will send separate briefing on Aug 10

### humanaios (Core)
- **Rollout:** Aug 15
- **Expected area:** OPS (Operations)
- **Expected patterns:** Name (README*, CONTRIBUTING*), EXCLUDE (*.sql, *.py, *.js)
- **Submit to:** `AREA_RULES_COLLECTION.md` or `NOTIFICATION_humanaios-core.md`

---

## Files You Need

In humanaios/operations repo:
- `AREA_RULES_COLLECTION.md` — Full details + FAQ
- `AREA_RULES_SUBMISSION_TEMPLATE.yaml` — Template to copy/fill
- `RULES_SUBMISSION_SUMMARY.txt` — One-page ref

Or ask: `document-control/question` on humanaios-ui/operations

---

## Fallback (If You Don't Submit)

If rules don't arrive by July 31, we'll use a fallback: every new inbox file gets routed to @humanaios-ui/operations for manual triage.

✅ Safe (nothing lost)  
❌ Less efficient (manual classification each week)

**Recommendation:** Takes 10 minutes — just submit your patterns.

---

## Deadline

**July 31, 2026 EOD — That's tomorrow.**

Submit as comment on `AREA_RULES_COLLECTION.md` (operations repo) or reply to your notification.

---

**Questions?** File issue tagged `document-control/question` or comment on AREA_RULES_COLLECTION.md

**See you tomorrow!**

— mesh-support (autonomy practice)
