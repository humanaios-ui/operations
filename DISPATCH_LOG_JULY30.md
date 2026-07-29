# Dispatch Log — July 30 Reminders to All Practices

**Date:** 2026-07-29 EOD (July 30 day-of dispatch)  
**Status:** Ready to send  
**Deadline:** July 31, 2026 EOD  

---

## Reminder Message (Send to All 4 Practices)

Copy the message below to Slack/email for each practice:

```
📋 REMINDER: Area Classification Rules — Due TOMORROW (July 31 EOD)

⏳ TL;DR: Submit your area's classification rules by July 31 EOD (takes 10 min)

**What to do:**
1. Copy AREA_RULES_SUBMISSION_TEMPLATE.yaml from operations repo
2. Fill patterns: extension, path, name, header (5 min)
3. Comment on AREA_RULES_COLLECTION.md by EOD tomorrow

**Why:** Without rules, A4 intake pipeline can't auto-classify new inbox files.
        With rules, auto-classification saves weeks of manual triage.

**Timeline:**
- July 31: SUBMIT rules (deadline)
- Aug 1-4: validation + testing
- Aug 5: A4 intake pipeline LIVE with your rules

**Links:**
- REMINDER_JULY30.md (full details)
- AREA_RULES_COLLECTION.md (submission guide)
- ONE_PAGE_SUMMARY.txt (quick ref)

Submit: Comment on AREA_RULES_COLLECTION.md or reply to your notification

That's it — 10 minutes, saves weeks for ops. See you at EOD tomorrow! 🚀
```

---

## Practice-Specific Dispatch

### Target 1: lasting-light-ai (Research)
- **Practice:** lasting-light-ai
- **Rollout Date:** Aug 12
- **Expected Area:** RES (Research)
- **Expected Patterns:** Extension (.md, .html), Name (*METHODS*, *VALIDATION*, *ACAT*)
- **Channels:** Slack #lasting-light-ai, or email to research-team@
- **Status:** ⏳ READY TO SEND

**Pre-send checklist:**
- [ ] Verify Slack channel exists: #lasting-light-ai
- [ ] Copy reminder message above
- [ ] Include link to AREA_RULES_SUBMISSION_TEMPLATE.yaml
- [ ] Mention their rollout date (Aug 12)

---

### Target 2: humanaios-internal (Ops & Leadership)
- **Practice:** humanaios-internal
- **Rollout Date:** Aug 13
- **Expected Area:** COLLAB (Collaboration) or OPS (Operations)
- **Expected Patterns:** Path (collaborators/), Name (*REPORT*, *RUNBOOK*)
- **Channels:** Slack #humanaios-internal, or email to ops-team@
- **Status:** ⏳ READY TO SEND
- **Note:** They're also backup maintainer (acknowledge in separate note if desired)

**Pre-send checklist:**
- [ ] Verify Slack channel exists
- [ ] Copy reminder message above
- [ ] Include link to AREA_RULES_SUBMISSION_TEMPLATE.yaml
- [ ] Mention their rollout date (Aug 13)
- [ ] Optional: Note their backup maintainer role

---

### Target 3: empirica-foundation (Governance)
- **Practice:** empirica-foundation
- **Rollout Date:** Aug 14
- **Status:** 🟡 SCOPE CLARIFICATION PENDING (Aug 10)
- **Channels:** Slack #empirica-foundation, or email to governance@
- **Status:** ⏳ READY TO SEND (modified message)

**Pre-send checklist:**
- [ ] Send different message (see below)
- [ ] Clarify: scope clarification coming Aug 10, may not need to submit

**Modified message for empirica-foundation:**
```
📋 UPDATE: Document Control — Scope Clarification Pending (Aug 10)

Your rollout is Aug 14. However, scope clarification is pending Aug 10 
to determine if your docs are empirica-scoped (use empirica's control) 
or humanaios-scoped (use these rules).

**Hold tight:** Separate briefing coming Aug 10. Rules submission may not 
be needed for your practice.

For now, same deadline applies (July 31) but you may not need to submit anything.

Full context: empirica-foundation practices are cross-org governance; 
empirica docs use empirica's own control system (separate).

Stay tuned for clarification by Aug 10.
```

---

### Target 4: humanaios (Core)
- **Practice:** humanaios
- **Rollout Date:** Aug 15
- **Expected Area:** OPS (Operations)
- **Expected Patterns:** Name (README*, CONTRIBUTING*), EXCLUDE (*.sql, *.py, *.js)
- **Channels:** Slack #humanaios, or email to core-team@
- **Status:** ⏳ READY TO SEND

**Pre-send checklist:**
- [ ] Verify Slack channel exists: #humanaios
- [ ] Copy reminder message above (with OPS area note)
- [ ] Include link to AREA_RULES_SUBMISSION_TEMPLATE.yaml
- [ ] Mention their rollout date (Aug 15)
- [ ] Highlight: EXCLUDE source code (*.sql, *.py, *.js)

---

## Dispatch Process

### Step 1: Prepare (Now)
- [ ] Copy `REMINDER_JULY30.md` (full reminder)
- [ ] Copy `ONE_PAGE_SUMMARY.txt` (quick ref)
- [ ] Copy `AREA_RULES_SUBMISSION_TEMPLATE.yaml` (template)
- [ ] Prepare 4 Slack/email messages (or 1 for all, with practice-specific notes)

### Step 2: Send (Today, July 30)
- [ ] Send to lasting-light-ai (Research) — Slack or email
- [ ] Send to humanaios-internal (Ops) — Slack or email
- [ ] Send to empirica-foundation (Governance) — modified message, scope pending
- [ ] Send to humanaios (Core) — Slack or email

### Step 3: Monitor (July 31 EOD)
- [ ] Check AREA_RULES_COLLECTION.md for comments
- [ ] Monitor email for submissions
- [ ] Note any missing practices (will use fallback "escalate_to_ops")
- [ ] Send thank-you + next steps to those who submitted

---

## Fallback (If Not Submitted by July 31 EOD)

For any practice that doesn't submit by deadline:
- **Fallback rule:** `fallback_action: "escalate_to_ops"`
- **Effect:** Every new inbox file → ops team for manual triage
- **Safe:** Nothing lost, but less efficient
- **Recovery:** Rules can be submitted anytime; A4 re-runs weekly

**Recommendation:** Send gentle reminder July 31 afternoon (4-6 PM) if any practice hasn't submitted yet.

---

## Next Steps (Post-Dispatch)

**Aug 1 (Fri):** mesh-support begins validation
- Collect all submissions
- Parse YAML (syntax check)
- Note any missing practices

**Aug 2-4 (Weekend/Mon):** Testing
- Test rules on historical _inbox_files*/ data
- Resolve conflicts (if file matches multiple areas)
- Publish final `.doc-control/area_rules.yaml`

**Aug 5 (Tue):** A4 ACTIVATION
- Deploy A4 intake pipeline with finalized rules
- First automated run classifies historical inbox

---

## Communication Checklist

**Before sending:**
- [ ] All 4 practices have their notifications on file
- [ ] Links to all documents verified (operations repo)
- [ ] Deadline emphasized (July 31 EOD tomorrow)
- [ ] Examples/templates included in message
- [ ] Practice-specific rollout dates mentioned

**After sending:**
- [ ] Confirm receipt (ask for thumbs-up or comment in Slack)
- [ ] Note send time + targets in this log
- [ ] Monitor for early submissions (likely same day or next morning)

---

## Dispatch Authority

**Approved by:** Carly  
**Sent by:** [To be filled in after dispatch]  
**Date/Time sent:** [To be filled in after dispatch]  
**Confirmation:** [To be filled in after receipt confirmations]

---

**Status:** 🟢 **READY TO SEND** — All messages prepared, all targets identified, no blockers.

