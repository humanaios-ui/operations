# Demarius Onboarding Complete Package — Empirica Mesh Integration

**Acceptance Date:** 2026-07-29  
**Onboarding Starts:** Jul 30 - Aug 2 (Phase 1)  
**Target Completion:** Aug 5 (Phase 4 live)  
**Total Time Commitment:** ~3-5 hours one-time; then embedded in Mode AI Phase 2 work

---

## Welcome to the Mesh

You've accepted empirica onboarding for Governing Engines / Mode AI project. This package contains everything you need for the next 7 days.

**The Goal:** Get you into the empirica mesh so Mode AI Phase 2 testing can coordinate with HumanAIOS using empirica's collab/propose/ack discipline — instead of email/Slack.

**Why It Matters:** 
- SpecificationObject testing needs structured coordination
- H-MECH-01 Condition C experiment requires mesh discipline
- Position Paper §3.2 (GRR mechanism) delivery tracked via empirica artifacts
- Cross-practice findings flow through mesh, not ad hoc channels

---

## Your Package Contents

### 1. Overview & Timeline (This Document)
- You are here
- Reading this is your first step

### 2. Phase 1: Orientation Plan
- **File:** `DEMARIUS_PHASE1_ORIENTATION_PLAN.md`
- **When:** Jul 30 - Aug 2 (30 min sync)
- **What:** Learn empirica's 3 core moves (collab, propose, ack)
- **Deliverable:** Signed mesh agreement

### 3. Phase 2: Technical Setup
- **File:** `DEMARIUS_PHASE2_TECHNICAL_SETUP.md`
- **When:** Aug 2-3 (1-2 hours)
- **What:** Install CLI, configure, register project
- **Deliverable:** Verified CLI + registered project

### 4. Phase 3: Coordination Test
- **File:** `DEMARIUS_PHASE3_COORDINATION_TEST.md`
- **When:** Aug 3-4 (1-2 hours, 30 min sync)
- **What:** Execute one full collab → propose → ack cycle
- **Deliverable:** Confirmed mesh discipline understanding

### 5. Quick Reference Card
- **File:** `DEMARIUS_MESH_QUICK_REFERENCE.md`
- **Use:** Keep handy during Phases 2-4
- **Contains:** All commands, addresses, workflows

### 6. Mode AI Phase 2 Plan
- **File:** Already in your repo (Mode AI test plan)
- **Integration:** Phase 4 links SpecificationObject tests to empirica coordination

---

## The 4-Phase Timeline

| Phase | Dates | Owner | Duration | Key Deliverable |
|-------|-------|-------|----------|-----------------|
| **Phase 1: Orientation** | Jul 30-Aug 2 | Claude + Demarius | 30 min | Mesh agreement signed |
| **Phase 2: Technical Setup** | Aug 2-3 | Demarius + David | 1-2 hrs | CLI verified working |
| **Phase 3: Coordination Test** | Aug 3-4 | Claude + Demarius | 1-2 hrs | One full mesh cycle executed |
| **Phase 4: Real Work** | Aug 5+ | Demarius (embedded) | ongoing | Mode AI operationally in mesh |

---

## What You're Committing To

### Operational Commitments

1. **Use empirica for technical coordination** (not Slack/email)
   - Cross-practice decisions go through collab/propose/ack
   - Internal Mode AI work stays email/Slack (normal)
   - Distinction: "Is this a decision that affects HumanAIOS?" → use mesh

2. **Log findings when you discover something**
   - Test results → findings
   - Governance insights → findings
   - SpecificationObject edge cases → findings
   - Tool: `empirica finding-log --finding "...""`

3. **Propose when you're grounded**
   - "I think HumanAIOS should update X methodology" → propose
   - Only after you have evidence
   - Tool: `empirica propose --finding-id <id>`

4. **Respond to collabs, even if "can't help"**
   - HumanAIOS asks Claude to ask you something → respond
   - Tool: `empirica mailbox read` + reply

5. **Ack when work completes**
   - HumanAIOS requests Mode AI testing → you complete it + ack
   - Tool: `empirica mailbox reply --action complete`

### Time Commitment

- **Phase 1-3:** ~3-5 hours (one-time, this week)
- **Phase 4+:** Embedded in Mode AI testing (no additional time)
  - Every time you log a finding or respond to a collab, that's empirica
  - But it doesn't add time to your work — it's how you document what you're already doing

### Authority & Boundaries

**You CAN:**
- Direct Mode AI Phase 2 research
- Surface governance findings + recommendations
- Ask collab questions about ACAT methodology
- Propose architectural improvements
- Decline proposals that don't fit your research

**You CANNOT:**
- Veto HumanAIOS methodology choices
- Approve ACAT dimension changes
- Override Z2 decisions
- Control what HumanAIOS publishes (they can use your findings with or without attribution)

---

## Day-by-Day Guide

### Day 1 (July 30-31)
- **Morning:** Read this package intro + Phase 1 plan
- **Afternoon:** Confirm with Claude: date/time for Phase 1 orientation sync
- **Action:** Reply to Claude with "Phase 1 on [date] [time]"

### Day 2-3 (Aug 1-2)
- **Execute:** Phase 1 orientation (30 min sync with Claude)
  - Learn collab, propose, ack
  - Sign mesh agreement (template in Phase 1 doc)
  - Confirm Phase 2 readiness
- **After:** Send Phase 1 completion to David Van Assche

### Day 3-4 (Aug 2-3)
- **Execute:** Phase 2 technical setup (1-2 hours)
  - Install empirica CLI
  - Run verification tests
  - Notify David when done
- **Prerequisite for Phase 2:** Receive API key from David (request if you don't have)

### Day 4-5 (Aug 3-4)
- **Execute:** Phase 3 coordination test (30 min sync + 30 min async)
  - Ask Claude a question (collab)
  - Claude responds
  - You propose a finding
  - Claude sends completion ack
- **Confirm:** All tests pass + mesh agreement signed

### Day 6+ (Aug 5+)
- **Live:** Phase 4 starts
  - SpecificationObject Test 1 begins
  - H-MECH-01 Condition C experiment active
  - Use empirica for all findings/proposals
  - Mode AI operational in mesh

---

## Key Dates & Contacts

### Scheduled Contact Windows
- **Phase 1 Sync:** Jul 30-Aug 2 (when you choose)
  - Contact: Claude (empirica-outreach)
  - Email: carly.r.anderson@gmail.com
  
- **Phase 2 Coordination:** Aug 2-3
  - Contact: David Van Assche (mesh-support)
  - Email: truuzee@gmail.com

- **Phase 3 Sync:** Aug 3-4 (when you choose)
  - Contact: Claude (empirica-outreach)
  - Email: carly.r.anderson@gmail.com

### Your Mesh Identity
- **Address:** `empirica-foundation.carly.governing-engines`
- **API Key:** Provided by David (request if needed)
- **Project Name:** Mode AI
- **Org:** empirica-foundation (Carly's foundation)
- **Tenant:** carly

---

## Common Questions

**Q: How much time does this really take?**  
A: Phase 1-3 are ~3-5 hours total (one-time setup). After that, empirica is just how you document what you're already doing — logging findings, responding to requests. No extra time added.

**Q: What if I can't do Phase 1 by Aug 2?**  
A: Let Claude know. We can slip the timeline, but aiming for Aug 5 Phase 4 start keeps Mode AI Phase 2 on track. Communicate early.

**Q: What if Phase 2 (technical setup) breaks?**  
A: Contact David Van Assche immediately. He runs mesh-support and can troubleshoot CLI/registration issues.

**Q: What's the difference between collab and propose?**  
A: Collab = you're uncertain, asking for help. Propose = you're grounded, recommending action. Collab is ungated (auto-accepted). Propose is praxic (requires grounded evidence).

**Q: Can I still use Slack/email for Mode AI work?**  
A: Yes! Internal Mode AI work stays Slack/email. Only cross-practice coordination (HumanAIOS collaboration) goes through empirica mesh.

**Q: What if I don't want to propose something?**  
A: You don't have to! Collab + logging findings are the key parts. Propose is for when you're confident and want HumanAIOS input. No pressure.

**Q: What if HumanAIOS rejects my proposal?**  
A: That's data. Log it as an assumption or decision and move on. No penalty.

---

## Files in This Package

1. **DEMARIUS_ONBOARDING_COMPLETE_PACKAGE.md** (this file)
   - Overview, timeline, FAQ

2. **DEMARIUS_PHASE1_ORIENTATION_PLAN.md**
   - Agenda, mesh agreement template, what to expect

3. **DEMARIUS_PHASE2_TECHNICAL_SETUP.md**
   - Step-by-step CLI install, config, verification

4. **DEMARIUS_PHASE3_COORDINATION_TEST.md**
   - Live drill scenario, test workflow, success criteria

5. **DEMARIUS_MESH_QUICK_REFERENCE.md**
   - Commands, addresses, workflows, error handling

6. **DEMARIUS_MESH_COLLAB_PROPOSAL.md** (earlier)
   - Original formal proposal you accepted

7. **DEMARIUS_ACCEPTANCE_LOGGED.md** (earlier)
   - Your acceptance recorded (2026-07-29)

---

## Next Step (Right Now)

1. **Read Phase 1 plan** — `DEMARIUS_PHASE1_ORIENTATION_PLAN.md`
2. **Pick a time for Phase 1** — Jul 30, Aug 1, or Aug 2, 30 min slot
3. **Reply to Claude** with your chosen time
4. **Keep this package handy** — reference it throughout the week

---

## Success Metrics

By Aug 5, you'll know the onboarding worked when:

- ✅ You have empirica CLI installed + can run `empirica whoami`
- ✅ You've executed one collab (asked HumanAIOS a question via empirica)
- ✅ You've executed one propose (recommended something grounded in data)
- ✅ You've sent one ack (confirmed a completed coordination loop)
- ✅ You understand the mesh discipline (when to collab, when to propose, when to ack)
- ✅ Mode AI project registered in empirica + you can create sessions
- ✅ You're ready to use empirica for Phase 2 testing coordination

---

## After Phase 4: What's Next?

Once Phase 4 (real work integration) is live:

- You keep using empirica for Mode AI findings/proposals
- HumanAIOS responds to your findings via the mesh
- Position Paper §3.2 (GRR mechanism) tracked via empirica artifacts
- SpecificationObject Test 1-N results logged as findings
- H-MECH-01 Condition C experiment findings flow through mesh
- No additional onboarding needed — you're in the mesh

---

## Questions or Blockers?

**Before Phase 1?** Reach out to Claude (empirica-outreach)  
**During Phase 2?** Contact David Van Assche (mesh-support)  
**During Phases 3-4?** Loop back to Claude or escalate to Carly (Admiral)

---

**Prepared by:** Carly Anderson (empirica-outreach)  
**Date:** 2026-07-31  
**Status:** Ready for Phase 1 orientation  

**Welcome aboard, Demarius.** Let's build Mode AI + the mesh together.

---

### Appendix: Command Cheat Sheet

```bash
# Phase 2: Verify setup
empirica whoami
empirica session-create --ai-id governing-engines

# Phase 3: Collab (ask question)
empirica collab --question "..." --target-claudes "empirica-foundation.carly.empirica-outreach"

# Phase 3: Log finding
empirica finding-log --finding "..." --impact 0.6

# Phase 3: Propose
empirica propose --finding-id <id> --action "review-finding"

# Phase 3: Check inbox
empirica mailbox read --direction received

# Phase 3: Send ack
empirica mailbox reply --proposal-id <id> --action complete
```

See `DEMARIUS_MESH_QUICK_REFERENCE.md` for full command reference.
