# Send Checklist — July 30 (Today's Action Items)

**For:** Carly / mesh-support  
**When:** July 30, 2026 (Wednesday) — Send today  
**What:** Reminders + summary to all 4 practices (deadline is tomorrow, July 31 EOD)

---

## Documents to Share (Copy from operations repo)

### 1. Send to ALL 4 Practices (General Reminder)
**File:** `REMINDER_JULY30.md`  
**How:** Copy & paste to Slack thread OR email to all practice leads  
**Format:** Markdown (will look nice in Slack)

**Text to share:**
```
📋 REMINDER: Area Classification Rules — Due TOMORROW (July 31 EOD)

⏳ TL;DR: Submit your area's classification rules by July 31 EOD (takes 10 min)

What to do:
1. Copy AREA_RULES_SUBMISSION_TEMPLATE.yaml
2. Fill patterns (file extensions, paths, names)
3. Comment on AREA_RULES_COLLECTION.md by EOD tomorrow

Why: Without rules, every new inbox file goes to ops for manual triage.
     With rules, A4 intake pipeline auto-classifies (fast + automated).

[Link to full reminder in operations repo]
```

### 2. Send Practice-Specific Info
**File:** `ONE_PAGE_SUMMARY.txt`  
**How:** Link to in Slack OR copy entire one-page summary  
**Who:** Use this in follow-up email/thread  
**Format:** Text (easy to scan)

---

## Practice-by-Practice Checklist

### ✅ lasting-light-ai (Research)
- [ ] Send REMINDER_JULY30.md
- [ ] Include ONE_PAGE_SUMMARY.txt link
- [ ] Link to AREA_RULES_SUBMISSION_TEMPLATE.yaml
- [ ] Remind them to submit by July 31 EOD
- [ ] Expected area: RES (Research)
- [ ] Expected patterns: Extension (.md, .html), Name (*METHODS*, *VALIDATION*, *ACAT*)

**Sample message:**
```
@lasting-light-ai team,

Your rollout is Aug 12. Before that, we need your area classification rules by tomorrow (July 31 EOD).

Takes 10 minutes:
1. Copy AREA_RULES_SUBMISSION_TEMPLATE.yaml
2. Fill in patterns (extension, path, name)
3. Comment on AREA_RULES_COLLECTION.md

Expected area: RES (Research)
Expected patterns: METHODS, VALIDATION, ACAT, methodology docs

[One-page summary]
[Template]
[Full guide: AREA_RULES_COLLECTION.md]
```

### ✅ humanaios-internal (Ops & Leadership)
- [ ] Send REMINDER_JULY30.md
- [ ] Include ONE_PAGE_SUMMARY.txt link
- [ ] Link to AREA_RULES_SUBMISSION_TEMPLATE.yaml
- [ ] Remind them to submit by July 31 EOD
- [ ] Expected area: COLLAB (Collaboration)
- [ ] Expected patterns: Path (collaborators/), Name (*REPORT*, *RUNBOOK*)
- [ ] Note: They're backup maintainer (may not need separate msg)

**Sample message:**
```
@humanaios-internal team,

Your rollout is Aug 13. We need your area classification rules by tomorrow (July 31 EOD).

Takes 10 minutes:
1. Copy AREA_RULES_SUBMISSION_TEMPLATE.yaml
2. Fill patterns (path: collaborators/, name: *REPORT*, *RUNBOOK*)
3. Comment on AREA_RULES_COLLECTION.md

Expected area: COLLAB (Collaboration) or OPS (Operations)

[One-page summary]
[Template]
```

### 🟡 empirica-foundation (Governance)
- [ ] Send REMINDER_JULY30.md
- [ ] Note: Separate scope clarification email will be sent Aug 10
- [ ] This practice may not need to submit (depends on scope)
- [ ] For now: same reminder as others, but clarify scope is pending

**Sample message:**
```
@empirica-foundation team,

Your rollout is Aug 14. We're doing scope clarification Aug 10 to determine
if your docs are empirica-scoped (use empirica's control) or humanaios-scoped
(use these rules).

Hold tight on the rules submission — separate briefing coming Aug 10.

For now: same deadline applies, but you may not need to submit anything.
```

### ✅ humanaios (Core)
- [ ] Send REMINDER_JULY30.md
- [ ] Include ONE_PAGE_SUMMARY.txt link
- [ ] Link to AREA_RULES_SUBMISSION_TEMPLATE.yaml
- [ ] Remind them to submit by July 31 EOD
- [ ] Expected area: OPS (Operations)
- [ ] Expected patterns: Name (README*, CONTRIBUTING*), EXCLUDE (*.sql, *.py, *.js)

**Sample message:**
```
@humanaios core team,

Your rollout is Aug 15. We need your area classification rules by tomorrow (July 31 EOD).

Takes 10 minutes:
1. Copy AREA_RULES_SUBMISSION_TEMPLATE.yaml
2. Fill patterns: README*, CONTRIBUTING* (but EXCLUDE source code: .sql, .py, .js)
3. Comment on AREA_RULES_COLLECTION.md

Expected area: OPS (Operations)

[One-page summary]
[Template]
```

---

## Send Sequence (Recommended)

**Step 1:** Create a Slack thread or email to all 4 practice leads
- Post REMINDER_JULY30.md (full text or link)
- Post ONE_PAGE_SUMMARY.txt link
- Mention deadline is TOMORROW, July 31 EOD

**Step 2:** Follow up with practice-specific messages
- Mention their rollout date (Aug 12-15)
- Highlight their expected area code (RES, COLLAB, OPS)
- Show example patterns for their area

**Step 3:** Provide links to templates + guides
- AREA_RULES_SUBMISSION_TEMPLATE.yaml (to fill and submit)
- AREA_RULES_COLLECTION.md (full guide if they have questions)
- ONE_PAGE_SUMMARY.txt (quick ref)

**Step 4:** Set up a submission monitor
- Create a comment thread in AREA_RULES_COLLECTION.md with a "Submissions" section
- Ask practices to leave their filled template as a reply
- Keep it visible in the operations repo

---

## What to Expect (Tomorrow, July 31)

### Ideal Scenario (All Submit)
- All 4 practices submit rules by EOD
- Comments appear in AREA_RULES_COLLECTION.md or as email replies
- mesh-support collects + validates (Aug 1)

### Likely Scenario (Some Submit Late)
- 2-3 practices submit on time
- 1 practice submits by end of day (last minute)
- Last-minute submissions still count (we validate all together)

### Fallback Scenario (Some Miss Deadline)
- If rules don't arrive for a practice, we use "escalate_to_ops" fallback
- That practice's files still get classified (manual, less efficient)
- Rules can be submitted later; A4 re-runs weekly

---

## After July 31 (mesh-support's job)

**Aug 1 (Fri):**
- Collect all submissions from comments/emails
- Parse YAML (syntax check)
- Note any missing practices

**Aug 2-4 (Weekend/Mon):**
- Test rules on historical _inbox_files*/ data
- Resolve any conflicts (file matches multiple areas)
- Publish final `.doc-control/area_rules.yaml`

**Aug 5 (Tue):**
- Activate A4 intake pipeline with rules
- Monitor first automated run

---

## Files Ready to Share (Just Copy-Paste)

| File | Purpose | Where | Size |
|------|---------|-------|------|
| REMINDER_JULY30.md | Today's message to all practices | Slack/email | ~500 words |
| ONE_PAGE_SUMMARY.txt | Quick reference (can link or paste) | Reply/thread | ~400 words |
| AREA_RULES_SUBMISSION_TEMPLATE.yaml | Template to fill | Link to repo | ~30 lines |
| AREA_RULES_COLLECTION.md | Full guide (if they ask questions) | Link to repo | ~400 lines |

All in humanaios/operations repo — just copy & paste!

---

## Confirmation Checklist

After sending, check:
- [ ] All 4 practices received the reminder
- [ ] They know deadline is tomorrow (July 31 EOD)
- [ ] They have the template + examples
- [ ] They know where to submit (comment on AREA_RULES_COLLECTION.md)
- [ ] Clarified: empirica-foundation scope pending (Aug 10)
- [ ] Optional: Slack thread pinned for easy reference

---

## Next Check-in (July 31 EOD)

**Tomorrow evening:**
- Monitor AREA_RULES_COLLECTION.md for comments
- Monitor email for submissions
- Note any missing practices (will use fallback)
- Send quick thank-you + next steps to those who submitted

---

**Ready to send?** All documents are in the operations repo. Copy, paste, send! 🚀
