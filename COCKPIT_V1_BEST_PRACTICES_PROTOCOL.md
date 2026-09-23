# COCKPIT v1.0 Best-Practices Research Protocol

**Status:** CANDIDATE (awaiting Z2 ratification)  
**Created:** 2026-09-23  
**Authority:** Q-COCKPIT-V1-PROTOCOL-01 (Z1 proposal)  
**Falsifier doctrine:** All RQs include measurable falsifiers (conditions that prove hypothesis wrong)

---

## Executive Summary

This document defines how HumanAIOS will **research and validate best practices for Z2 governance cockpit design** during a 4-week reverse-waterfall build (test during build, not after). Five research questions (RQs) with 22 falsifiers guide weekly validation gates. Each gate must pass to proceed to next week; if a falsifier trips, the team iterates same week or escalates to Z2.

**Key constraint:** All work must be observable, measurable, and falsifiable. Vague goals ("users like it") are not acceptable. Falsifiers are conditions under which we declare the hypothesis *wrong* and iterate.

---

## Research Questions & Hypotheses

### **RQ-Auth-01: Does PKCE + Supabase OAuth + httpOnly cookies = secure token storage + frictionless auth?**

**Hypothesis:** Using PKCE + Supabase authentication + server-side httpOnly cookies for session storage (via BFF/middleware) enables both security (tokens cannot be stolen by script injection) and UX fluency (minimal friction, <15s login flow).

**Design:** 
- OAuth 2.0 PKCE flow (no client secret in browser)
- Supabase Auth as IdP (JWT + refresh token model)
- httpOnly, secure, sameSite=strict cookies for tokens
- 15-minute access token window; 4-hour refresh token window
- Silent token refresh in background; re-auth triggered at 4h

**Falsifiers (any one triggers iteration):**
1. **Token stored in JavaScript memory** — If token accessible to JavaScript XSS payload, storage is not secure
2. **SUS score <70** — System Usability Scale below 70 = unacceptable UX (below industry standard)
3. **Login takes >15 seconds** — Timed flow shows login >15s = friction too high
4. **Token refresh causes visible UI block** — Silent refresh causes >500ms UI freeze = UX failure
5. **Re-auth abandonment >50%** — If >50% of users abandon on forced re-auth after 4h = retention risk

**Test subjects:** Night (Z2) + 1 empirica team member  
**Duration:** 1 day (Week 1, Day 1)  
**Method:** Automated phishing simulation + task timing + SUS survey (5-point Likert)

---

### **RQ-Auth-02: Does the token timing window (15-min access / 4-hr refresh) balance security and user retention?**

**Hypothesis:** A 15-minute access token window + 4-hour refresh window strikes the right balance between reducing the window of compromise if a token leaks, and avoiding excessive re-auth friction that causes user abandonment.

**Design:**
- Access token: 15 minutes (short window limits blast radius if leaked)
- Refresh token: 4 hours (balances session length vs. forced re-auth)
- Compromise detection: If a token is used from 2+ IP addresses within 5 min, force re-auth
- Timeout: Absolute session timeout at 8h regardless of refresh (hard boundary)

**Falsifiers (any one triggers iteration):**
1. **Refresh token stored in JavaScript accessible** — If refresh token reachable by XSS = window too long
2. **Re-auth abandonment >50%** — If >50% abandon at 4h forced re-auth = window too aggressive
3. **Access token compromise detection takes >5 min** — If server cannot detect stolen access token within 5 min = window too long
4. **Silent refresh failure rate >5%** — If >5% of refreshes fail in field = reliability risk

**Test subjects:** Night + 1 test user  
**Duration:** 1 day (Week 1, Day 2)  
**Method:** Behavioral observation (screen recording) + token leak simulation + log inspection

---

### **RQ-UX-01: Does a 4-section dashboard design (Findings | Queue | Molts | Audit) enable Z2 to find "next action" in <5 seconds?**

**Hypothesis:** A dashboard with 4 primary sections (REGISTERED findings feed, PRIORITY_QUEUE with ranking, molt cycle tracker, audit log) enables Night to quickly find what action to take next, with <5s task completion time and <50% scrolling overhead.

**Design:**
- **Section 1 (Findings):** Live feed of REGISTERED.md entries, newest first; drill-down to full entry
- **Section 2 (Queue):** PRIORITY_QUEUE.md with sortable impact/cost/benefit; highlight GATING items
- **Section 3 (Molts):** Current molts with cycle status (prediction | window open | closed | reverted); visual countdown
- **Section 4 (Audit):** Time-series log of all Z2 decisions + Z3 executions; filterable by actor/action

**Falsifiers (any one triggers iteration):**
1. **Can't find "next action" in <5 seconds** — Task: "Show me the highest-priority candidate to ratify." If >5s, UX fails
2. **>50% of interactions require scrolling** — If user scrolls on >50% of tasks, layout is broken
3. **Drill-down latency >2 seconds** — Click entry → see full context takes >2s = interactive lag
4. **Search doesn't work** — Can't search findings by tag/status = critical UX gap

**Test subjects:** Night + empirica lead (1 hour)  
**Duration:** 1 hour (Week 2, Day 1)  
**Method:** Screen recording + task timing + event logging (click/scroll/search actions)

---

### **RQ-UX-02: Does an immutable audit log enable accountability without creating surveillance?**

**Hypothesis:** An append-only audit log that records all Z2 decisions (accept/reject/edit) and Z3 executions, with timestamps and rationale, enables Night to audit past decisions without creating a surveillance system that feels intrusive.

**Design:**
- **Immutable ledger:** All entries append-only (no deletion, only forward pointers to superseding entries)
- **Entry content:** Actor, action, timestamp, decision/rationale, affected resource ID
- **Query model:** Filter by actor/date/action type; reconstruct decision history
- **Retention:** Full audit trail kept; no auto-purge
- **Visibility:** Only visible to Z2 + assigned Z3; no external access

**Falsifiers (any one triggers iteration):**
1. **Can't reconstruct a decision chain** — Task: "Show me all decisions on Q-CANDIDATE-X." If impossible = audit fail
2. **Noise >10 events per user action** — If 1 user click generates >10 log events = noise too high (obscures signal)
3. **Audit log latency >10 seconds** — Events don't appear in log until >10s after action = not real-time
4. **False positives in automated detection** — If automated "suspicious activity" detector flags >20% false positives = unusable

**Test subjects:** Night + 1 auditor from governance team (1 hour)  
**Duration:** 1 hour (Week 2, Day 2)  
**Method:** Task-based reconstruction + event counting + timing measurement

---

### **RQ-UX-03: Does WebSocket real-time update keep Z2 informed without overloading?**

**Hypothesis:** A WebSocket-based live-update channel for REGISTERED.md, PRIORITY_QUEUE.md, and molt status enables Night to stay informed about changes without polling, with latency <30s, uptime >99.9%, and message lag <100ms.

**Design:**
- **Transport:** WebSocket (wss://) with automatic reconnect on disconnect
- **Channels:** 3 subscriptions (findings, queue, molts)
- **Update model:** Event-driven (push changes, not periodic poll)
- **Backoff:** Exponential backoff on reconnect (1s, 2s, 4s, 8s max)
- **Heartbeat:** Ping every 30s to detect stale connections

**Falsifiers (any one triggers iteration):**
1. **Update latency >30 seconds** — If a REGISTERED.md change takes >30s to appear in cockpit = not timely
2. **Uptime <99.9%** — If WebSocket available <99.9% of time over 1 week = reliability fail
3. **Message lag (internal) >100ms** — Processing + rendering takes >100ms = perceptible lag
4. **Reconnect takes >5s** — If network drop takes >5s to reconnect = bad UX on flaky network
5. **Memory leak under continuous updates** — Browser memory grows >50% over 1-hour continuous update stream = resource leak

**Test subjects:** Synthetic monitoring (automated probes); Night may do smoke test  
**Duration:** Continuous (Week 3, all week)  
**Method:** Automated latency probe + uptime monitoring + browser performance profiling

---

## Measurement Framework

### Weekly Gate Structure

Each week ends with a **falsifier audit**:

```
Week 1 (Auth):
  Day 1: RQ-Auth-01 test → falsifiers pass? YES → proceed to Day 2
                         → NO  → iterate, re-test same day
  Day 2: RQ-Auth-02 test → falsifiers pass? YES → Week 1 GREEN
                         → NO  → iterate, re-test same day

If any falsifier still failing by end of week → Z2 review + decision
  Decision options: 
    a) Iterate in Week 2 (eat into UX time)
    b) Accept tradeoff, document as known gap (ratify anyway)
    c) Escalate, pause roadmap pending Z2 decision
```

### Success Criteria by Week

| Week | RQs Tested | Pass Condition | Fail Path |
|:-----|:-----------|:---|:---|
| 1 | Auth-01, Auth-02 | 0 falsifiers tripped | Iterate same week or escalate to Z2 |
| 2 | UX-01, UX-02 | 0 falsifiers tripped | Iterate same week or escalate to Z2 |
| 3 | UX-03 | 0 falsifiers tripped | Iterate same week or escalate to Z2 |
| 4 | Freeze + Z2 sign | All RQs pass + Z2 ratifies | If any fail, revert to Week 3 and iterate |

### Data Collection

**Auth weeks (Weeks 1–2):**
- SUS survey (5-point Likert, N=2)
- Phishing test results (pass/fail per subject)
- Timing logs (login duration, token refresh latency, re-auth time)
- Video screen recordings (60 min per subject)

**UX weeks (Weeks 2–3):**
- Task completion time (stopwatch for "find next action")
- Scroll event counts (% interactions requiring scroll)
- Drill-down latency (network waterfall + render time)
- Search test results (pass/fail for each query)
- Audit reconstruction time (time to answer "show all decisions on X")
- Event noise count (events per user action)

**Reliability week (Week 3):**
- Latency probe (WebSocket round-trip time, recorded every 10s)
- Uptime tracking (connection state logged every 1s)
- Memory profiling (heap size at 0h, 30min, 1h)
- Disconnect/reconnect test (manually kill socket, measure reconnect time)

---

## Falsifier Interpretation

**If a falsifier trips:**
1. **Document the failure:** What condition tripped? What was the measured value?
2. **Root-cause:** Why did it fail? (Design flaw? Implementation bug? Unrealistic threshold?)
3. **Decision:**
   - **Iterate:** Fix the design, re-test same week
   - **Relax threshold:** Is the falsifier too strict? (e.g., SUS <70 → SUS <65)
   - **Accept tradeoff:** "We know this UX sucks, but time/risk tradeoff favors shipping." (Document in PR)
   - **Escalate to Z2:** "This is a blocker. Need decision from Night."

**No silent passes.** Every falsifier result must be documented in the weekly report.

---

## Z2 Ratification Gates

After Week 4, Z2 must sign off on:

1. **All 5 RQs passed falsifiers** (or tradeoffs explicitly accepted)
2. **Code quality:** No security holes, no memory leaks, no untested paths
3. **Documentation:** Protocol findings documented in F/IC entries in REGISTERED.md
4. **Deployment readiness:** Staging environment ready for v1.0 rollout

**Z2 signature:** If all gates pass, Z2 signs a Q-COCKPIT-V1-RATIFY-01 hash committing to practices discovered.

---

## Risks & Mitigations

| Risk | Severity | Mitigation |
|:-----|:---------|:-----------|
| Phishing test doesn't reflect real attack | MEDIUM | Use industry-standard simulation (Gophish or equivalent); calibrate against real phishing data |
| SUS survey bias (only 2 subjects) | MEDIUM | Supplement with qualitative feedback; don't over-rely on single score |
| Network conditions during Week 3 test | LOW | Run synthetic probes from multiple regions; use controlled test environment for uptime |
| Falsifier thresholds are wrong | HIGH | If multiple falsifiers trip, revisit thresholds before iterating; document assumption |
| Z2 unavailable during weekly gates | MEDIUM | Schedule gates async; 48h window for Z2 decision per CLAUDE.md |

---

## Success Outcome

If all 5 RQs pass their falsifiers by end of Week 4:

✅ **Best practices validated:** The cockpit design is proven to enable Z2 governance at required speed/security.  
✅ **Z2 ratified:** Night signs off on the approach, committing to rollout.  
✅ **Findings filed:** F/IC entries document what we learned (e.g., "PKCE + 15-min token = optimal for this use case").  
✅ **Ready for production:** Code merged, CI green, ready for Week 5 production deployment.

If any falsifier trips and can't be resolved in 4 weeks:

⚠️ **Known gaps:** Document tradeoffs; Z2 decides whether to ship anyway or iterate further.  
🚧 **Post-v1.0 roadmap:** Add follow-up work to improve in v1.1 (tracked in PRIORITY_QUEUE.md).

---

## Appendix: Falsifier Thresholds (Rationale)

**Why SUS <70?** Industry standard: scores 68–72 = acceptable usability. Below 70 = below average.

**Why phishing fall >10%** Real phishing fall rates in enterprise ~5–8%; >10% signals design failure.

**Why <5 seconds?** Z2 makes rapid decisions; if finding "next action" takes >5s, dashboard is failing.

**Why >99.9% uptime?** 99.9% = ~43min downtime/month; cockpit is critical governance tool.

**Why <30s update latency?** Z2 operates on fast cycles; 30s latency = acceptable delay before noticing change.

---

**Document history:**
- 2026-09-23: Created (Q-COCKPIT-V1-PROTOCOL-01 candidate)
- Pending Z2 ratification
