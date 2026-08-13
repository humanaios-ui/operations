# Practice Lead Training — Governance PR Workflow

**Phase:** 2 (Deployment & Training)  
**Effective Date:** 2026-08-08  
**Target Audience:** Z2 Authorities (practice leads) for all 10 foundation practices  

---

## Before You Start

You are the **Z2 Authority** for your practice. Your role:
- Review governance PRs within SLA (24h-72h depending on type)
- Answer 5 Z2 gate questions before approval
- Represent your practice in cross-practice decisions
- Merge mesh-sync-batch PRs within 24h of receipt

**Your Authority:** Carly Anderson (Admiral)  
**Your Backup:** SAB  
**Your Practice:** [your practice name]

---

## The Governance PR Workflow (5 Steps)

### Step 1: Discovery & Drafting (Z1 — Claude)

A Claude or practice lead identifies a governance need (new policy, authority update, operational change).

**What happens:**
- Decision drafted in GOVERNANCE_PR_TEMPLATE.md format
- Decision linked to a decision_id (GOV-YYYY-MM-DD-DESCRIPTION)
- PR created in operations repo
- Circulated to all 10 practices for Phase 1 feedback (if cross-practice)

**Your role:** Monitor for PRs affecting your practice.

---

### Step 2: Z2 Ratification Review (YOU — Admiral)

The Z2 Authority (Admiral) reviews the PR and answers 5 gate questions.

**Gate Questions:**
1. **Is this decision necessary?** (Y/N/DEFER)
2. **Does this align with existing authority model?** (Y/N/CONDITIONAL)
3. **What is the rollout sequence?** (All-at-once / Phased / Pilot)
4. **Are there unhandled edge cases?** (List / Address-when-encountered)
5. **What is the implementation timeline?** (Immediate / [Date])

**Your action:**
1. Read the PR completely
2. Review the GOVERNANCE_PR_TEMPLATE.md fields
3. Answer all 5 questions in the PR review
4. Approve or request changes

**SLA:**
- New Ratification: 48-72h
- Minor Update: 24h
- Breaking Change: 72h-2w (with rollback plan)
- Operational Doc: 12-24h

---

### Step 3: Merge & Registry Update

After Admiral approval, the PR is merged.

**What happens:**
- Decision recorded in GOVERNANCE_RATIFICATIONS_REGISTRY.yaml
- decision_id assigned (if not already in title)
- Merge commit links to decision_id
- mesh-sync-batch workflow triggers

**Your role:** Monitor merge + verify sync dispatch starts.

---

### Step 4: Mesh Dispatch (Automated)

The mesh-sync-batch workflow dispatches the decision to all 10 practices.

**What happens:**
- GitHub Actions dispatches repository_dispatch event to GitHub-based practices
- Local practices notified via mesh-support
- Each practice receives governance sync PR
- Sync PR links back to original decision

**Your role:** Monitor for sync PR arrival. **Merge within 24h of receipt.**

---

### Step 5: Divergence Detection (Daily)

The divergence-detect workflow runs daily at 00:00 UTC.

**What happens:**
- Checks all 10 practices for consistency
- Builds consistency matrix
- Alerts on HIGH severity (MISSING files, VALIDATION failure)
- Alerts on MEDIUM severity (STALE, NETWORK_FAILURE)

**Your role:** 
- Monitor divergence-detect reports
- Respond to alerts in your practice
- Escalate to Admiral if needed

---

## Anatomy of a Governance PR

### PR Title Format

```
TYPE(scope): BRIEF TITLE — decision_id

Example:
governance(authority): Designate Z2 Authority for website — GOV-2026-07-30-Z2-AUTHORITY
```

### Affected Docs Checklist

```markdown
- [ ] AUTHORITY_ASSIGNMENTS.yaml
- [ ] GOVERNANCE_CHANGE_PROCEDURES.md
- [ ] CONTROLLED_DOCUMENTS.md
- [ ] Operational docs (MOLT_STATE.md, SYSTEM_HEALTH.md, etc.)
```

### Z2 Gate Questions (Your Review)

```markdown
**Q1: Is this decision necessary?**
- [ ] YES
- [ ] NO
- [ ] DEFER

Comment: (explain your reasoning)

**Q2: Does this align with existing authority model?**
- [ ] YES
- [ ] CONDITIONAL (explain conditions)
- [ ] NO (explain misalignment)

Comment:

**Q3: What is the rollout sequence?**
- [ ] All at once (immediate, all 10 practices)
- [ ] Phased (explain phases)
- [ ] Pilot (explain pilot scope + graduation criteria)

Comment:

**Q4: Are there unhandled edge cases?**
- [ ] No edge cases identified
- [ ] Possible edge cases (list): [...]
- [ ] Address when encountered (document in decision body)

Comment:

**Q5: What is the implementation timeline?**
- [ ] Immediate (merge → dispatch today)
- [ ] [Specific date]
- [ ] [Milestone-dependent]

Comment:
```

---

## When to Approve vs Defer

### Approve (Green Light)

- Decision is necessary and well-justified
- Aligns with existing authority model (or explicitly updates it)
- Rollout plan is clear
- Edge cases documented or explicitly deferred
- Timeline is realistic

**Action:** Answer all 5 questions with YES/SPECIFIC DATE, then approve.

### Request Changes (Yellow Light)

- Minor clarifications needed (edge case handling, timeline)
- Conditions needed (e.g., "approve only if X is true")
- Rollout sequence needs refinement

**Action:** Comment on PR with specific changes. Wait for update.

### Reject (Red Light)

- Decision conflicts with authority model
- Necessary preconditions not met
- Critical edge cases unhandled
- Insufficient justification

**Action:** Comment with veto rationale. Propose alternative approach.

---

## Your Checklist for Every Governance PR

- [ ] Read entire PR + linked documents
- [ ] Verify PR title follows format (TYPE(scope): TITLE — decision_id)
- [ ] Verify GOVERNANCE_PR_TEMPLATE.md fields are complete
- [ ] Verify decision_id format (GOV-YYYY-MM-DD-DESCRIPTION)
- [ ] Answer all 5 Z2 gate questions (no blanks)
- [ ] Verify rollout sequence is clear
- [ ] Verify edge cases documented or explicitly deferred
- [ ] Check SLA (are you within 24-72h window?)
- [ ] Approve or request specific changes
- [ ] After merge: monitor for mesh-sync-batch dispatch
- [ ] After dispatch: merge sync PR in your practice within 24h

---

## Handling Sync PRs (After Merge)

When you receive a sync PR from mesh-sync-batch:

### What You'll See

```
PR Title: [mesh-sync] GOV-2026-07-30-GOVERNANCE-UNIFICATION

PR Body:
- Sync of governance decision merged in operations repo
- Linked decision: GOV-2026-07-30-GOVERNANCE-UNIFICATION
- All 10 practices receive identical sync PR
- Merge within 24h of receipt
```

### Your Action

1. **Verify:** Check that the sync PR updates match the operations repo decision
2. **Review:** Skim the changes (should be identical across all 10)
3. **Merge:** Click "Merge" within 24h
4. **Confirm:** Verify merge completed in your practice

**SLA:** Merge within 24h of sync PR arrival.

---

## Q&A for Practice Leads

**Q: What if I disagree with a governance decision?**

A: Review the PR and voice concerns in comments before the Admiral decides. If Admiral approves despite your concerns, your practice is bound by the decision. Escalate to mesh-support if you believe a decision violates fundamental principles.

**Q: Can I reject a sync PR?**

A: No. Once the Admiral approves and merges a decision, all 10 practices receive sync PRs. Your role is to merge it, not to re-adjudicate the Admiral's decision. If you believe a sync PR is incorrect, flag it to Admiral immediately.

**Q: What if a sync PR fails to merge?**

A: Check the error message. Common issues:
- Merge conflict with local changes (contact Admiral)
- CI/CD validation failure (fix in follow-up PR)
- Permission issue (contact mesh-support)

Contact mesh-support with the sync PR link + error message.

**Q: What if divergence-detect flags my practice?**

A: Read the alert carefully:
- **MISSING:** Required governance file missing → create it
- **VALIDATION_FAILURE:** File format error → fix and commit
- **STALE:** File outdated vs. operations repo → merge latest sync PR
- **NETWORK_FAILURE:** Can't reach operations repo → retry

Contact mesh-support if you can't resolve.

**Q: Can I create a governance PR myself (not the Admiral)?**

A: No. Governance PRs are created at Z1 level (by Claude or SMEs), circulated for feedback (Phase 1), then reviewed by Admiral (Z2). As Z2 Authority, your role is to review and approve, not to author new governance decisions.

---

## Training Checklist

- [ ] Read this guide end-to-end
- [ ] Review the GOVERNANCE_PR_TEMPLATE.md format
- [ ] Review the 5 Z2 gate questions
- [ ] Understand SLA (24h-72h by change type)
- [ ] Understand sync PR workflow (merge within 24h)
- [ ] Know how to respond to divergence-detect alerts
- [ ] Know who to contact (mesh-support, Admiral)

---

## Key Dates

- **2026-08-01 to 08-07:** Phase 1 — Circulation & training
- **2026-08-08 to 08-14:** Phase 2 — Deployment & first test PR
- **2026-08-15:** Phase 3 — Go Live (synchronized across all 10)
- **2026-08-22 onwards:** Daily divergence-detect reports

---

## Support

**Questions?** Contact:
- **Admiral:** Carly Anderson (aioshuman@gmail.com)
- **Mesh Support:** empirica-mesh-support (empirica-foundation.carly.empirica-mesh-support)
- **Governance Repo:** operations/ (canonical governance records)

**First PR Help:** Ping mesh-support with the PR link for a walkthrough of the governance workflow.

---

**Congratulations!** You are now trained as a Z2 Authority for the governance unification rollout. See you at Phase 3 go-live (2026-08-15).
