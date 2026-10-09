# COCKPIT v1.0: Executive Summary for Z2 (Night)

**To:** Carly R. Anderson (Night / Z2)  
**From:** Claude (Z1)  
**Date:** 2026-09-23  
**Subject:** Cockpit v1.0 Best-Practices Research Protocol + 4-Week Build  
**Status:** AWAITING Z2 APPROVAL

---

## The Ask (What We're Requesting)

**Approve a 4-week sprint to research and validate best practices for the Z2 governance cockpit interface.**

The cockpit is a unified dashboard where you ratify REGISTERED.md candidates, manage PRIORITY_QUEUE.md, track molt cycles, and audit Z2 decisions. Instead of shipping untested, we want to **test during build** (reverse waterfall), with weekly falsifier gates that prove our design assumptions.

**Timeline:** Weeks of 2026-09-30, 2026-10-07, 2026-10-14, 2026-10-21 (+ optional Week 5 production rollout)

**Commitment from Z2:** ~11 hours over 4 weeks (see table below)

---

## Five Research Questions (RQs) to Validate

| Week | RQ | Hypothesis | Falsifier (Proves Wrong) | Time Commitment |
|:-----|:---|:----------|:---|:---|
| 1 | Auth-01 | PKCE + Supabase = secure + frictionless | Phishing fall >10% OR SUS <70 | 1 hour test + review |
| 1 | Auth-02 | 15-min token + 4-hr refresh = optimal balance | Compromise >15min undetected OR re-auth abandon >50% | 1 hour test + review |
| 2 | UX-01 | 4-section dashboard finds "next action" in <5s | Can't find action <5s OR >50% scrolling | 1 hour test + review |
| 2 | UX-02 | Audit log enables accountability w/o surveillance | Can't reconstruct decision OR noise >10 events/action | 1 hour test + review |
| 3 | UX-03 | WebSocket keeps you informed w/o overload | Latency >30s OR uptime <99.9% OR lag >100ms | Continuous monitoring + review |

**Total Z2 time: ~11 hours** (distributed as 1–2 hours/week for 4 weeks, plus decision at Week 4 end)

---

## Weekly Gates: What Happens Each Week

```
Each week ends with a FALSIFIER AUDIT:
  ✅ All falsifiers passed?   → Proceed to next week
  ❌ Any falsifier tripped?   → Options:
                                 a) Iterate same week (eat time)
                                 b) Accept tradeoff, document, proceed anyway
                                 c) Escalate to Night for decision

Week 4 (Freeze): 
  - No new features, security audit only
  - Night does smoke test (end-to-end walkthrough)
  - Night signs Q-COCKPIT-V1-RATIFY-01 hash → GO for production
  - If any falsifier still failing: hold sprint, iterate, re-test
```

---

## What You'll Be Testing

**Week 1 (Auth):** You'll log in, try to be phished, let us time your login speed, take a 5-min SUS survey  
**Week 2 (UX):** Screen recording while you use the dashboard; we time how fast you find "next action to take"  
**Week 3 (Real-time):** The dashboard auto-updates in real-time; we measure latency & uptime  
**Week 4 (Freeze):** You do a full walkthrough, we fix any bugs, you approve for production

---

## Why This Matters

Today, you ratify work via REGISTERED.md + PRIORITY_QUEUE.md files + email/Slack. It's decentralized and asynchronous, which is good, but it's also hard to get a unified picture fast.

The cockpit solves this by putting all 4 governance streams in one place (Findings | Queue | Molts | Audit) with real-time updates. The bet is:

**If we test the design with actual Z2 usage, we ship something that works for you, not against you.**

The falsifiers make sure we're not just hoping — we're measuring.

---

## What "Success" Looks Like (End of Week 4)

**All 5 RQs pass their falsifiers** (or tradeoffs are explicitly ratified):
- **Auth-01:** Token secure from XSS, SUS >70, login <15s, refresh <500ms
- **Auth-02:** Refresh token secure, re-auth abandon <50%, detect compromise <5min
- **UX-01:** Find "next action" <5s, <50% scrolling interactions
- **UX-02:** Reconstruct audit decision <1 min, event noise <10/action
- **UX-03:** WebSocket latency <30s, uptime >99.9%, UI lag <100ms

Plus:
- ✅ Code is secure (RLS policies, no leaked secrets), performant (render <500ms), no memory leaks
- ✅ Z2 smoke test passes all tasks
- ✅ Z2 signs off → ready for staging deployment Week 5

---

## What Happens If a Falsifier Trips

**Example:** RQ-UX-01 falsifier: "Can't find 'next action' in <5 seconds"

If Night takes >5s to find the next candidate to ratify:

1. **We document it:** "Finding took 8s; search wasn't obvious."
2. **We decide:** 
   - a) Fix UX, re-test same week (lost time, stays on Week 2)
   - b) Relax falsifier to <8s (maybe 5s was too strict?)
   - c) Accept tradeoff (ship anyway with known gap, mark as v1.1 work)
   - d) Escalate (Night decides if this blocks shipping)

**We don't hide it.** Every result goes in the weekly report to Night.

---

## Resource Cost (Your End)

| Week | Hours | Activity |
|:-----|:----:|:---------|
| Week 1 | 2.5 | Login testing (30 min) + SUS survey (15 min) + review report (45 min) + decision (30 min) |
| Week 2 | 2.5 | UX testing on dashboard (60 min) + review report (45 min) + decision (30 min) + re-test if needed (15 min) |
| Week 3 | 2 | Monitoring + review report (60 min) + decision (30 min) |
| Week 4 | 4 | Smoke test (60 min) + review findings (90 min) + ratification decision & signature (90 min) |
| **Total** | **11** | **(spread over 4 weeks; ~2.75 hrs/week avg)** |

**Not continuous.** Most weeks are 1–2 focused sessions, then async review.

---

## Resource Cost (Z3 Builder Side)

**Est. 73 Z3-hours + 600 CI-minutes over 4 weeks** (see COCKPIT_V1_IMPLEMENTATION_ROADMAP.md for detail)

Assumes 1 FTE builder; adjust if split across team.

---

## Risks & Mitigations

| Risk | Mitigation |
|:-----|:-----------|
| Z2 unavailable for testing | Async testing; 48h decision window per CLAUDE.md |
| Falsifier thresholds too strict | Plan for 1 iteration week if needed; escalate if blocker |
| WebSocket reliability | Polling fallback; synthetic monitoring |
| Tight timeline if falsifier trips | Pre-plan iteration week; document known gaps |

---

## Timeline (Proposed Start: Week of 2026-09-30)

- **Week 1 (Sep 30–Oct 4):** Auth testing
- **Week 2 (Oct 7–11):** UX testing  
- **Week 3 (Oct 14–18):** WebSocket monitoring
- **Week 4 (Oct 21–25):** Freeze + Z2 ratification
- **Week 5 (Oct 28–Nov 1, optional):** Production rollout

---

## Approval Needed

**Upon Z1 ratification of candidates in REGISTERED.md**, please confirm:

1. ✅ **Time available?** Can you commit ~11 hours over 4 weeks to testing/decision-making?
2. ✅ **Scope approved?** The 5 RQs capture the right governance use cases?
3. ✅ **Timeline OK?** Week of 2026-09-30 start date works?
4. ✅ **Z3 executor assigned?** Who builds? (Currently TBD in ZONE_REGISTRY.md)
5. ✅ **Sign off scope?** Will you ratify Q-COCKPIT-V1-RATIFY-01 at end if all falsifiers pass?

If all five are approved, Z1 files candidates in REGISTERED.md and we kick off Week 1.

---

## Next Steps

1. **You review** this summary + COCKPIT_V1_BEST_PRACTICES_PROTOCOL.md (15 min read)
2. **You approve** all five questions above (async reply)
3. **We file candidates** in REGISTERED.md (Q-COCKPIT-V1-PROTOCOL-01, Q-COCKPIT-V1-IMPLEMENTATION-01)
4. **Z3 starts Week 1** on 2026-09-30
5. **Weekly gates** (every Friday) with you + Z3

---

**Questions?** Ping Z1 or Z3 in `#operations` channel.

---

**Document history:**
- 2026-09-23: Created (Q-COCKPIT-V1-EXECUTIVE-01 candidate)
- Pending Z2 approval
