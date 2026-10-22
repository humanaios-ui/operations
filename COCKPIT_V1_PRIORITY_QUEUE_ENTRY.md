# Q-COCKPIT-V1-01: Cockpit v1.0 Build + Research Protocol

**Status:** CANDIDATE (awaiting Z2 ratification)  
**Proposal Date:** 2026-09-23  
**Proposer:** Z1 (Claude)  
**RBE-OPS Cost Vector:** See below  

---

## Candidate Block (for PRIORITY_QUEUE.md)

```yaml
rank: (TBD)
candidate_id: Q-COCKPIT-V1-01
title: "Cockpit v1.0: Best-practices research protocol + 4-week build"
description: "Research-driven reverse-waterfall build of Z2 governance cockpit interface. 5 RQs with falsifiers; weekly gates. If all RQs pass, cockpit ships Week 5. Z2 time commitment: ~11 hours over 4 weeks."
impact: 7/10
blocking: 0
dependencies: []
resource_cost:
  RAT-min: 660
  Z1-ktok: 4
  Z3-hr: 73
  CI-min: 600
  RUN-day: 1
benefit_score: 7/10 (high impact, non-blocking)
priority: HIGH (pending Z2 ratification)
state: BLOCKED (awaiting Z2 approval per Q-TEMPORAL-DISSOLUTION-01 gate)
gate_blockers: []
```

---

## Why This Matters

Today, Z2 ratifies work via async REGISTERED.md + PRIORITY_QUEUE.md updates + email. It works, but it's hard to get a unified picture fast.

The cockpit unifies 4 governance streams:
1. **Findings feed** (REGISTERED.md candidates)
2. **Priority queue** (work ranked by RBE cost/benefit)
3. **Molt cycle tracker** (monitor windows, falsifiers, reversions)
4. **Audit log** (reconstruct Z2 decisions + Z3 executions)

**Research goal:** Validate that the cockpit design actually makes Z2 faster, more informed, and not surveilled.

**Why test during build:** If we ship untested, cockpit might make Z2 slower (UX fail) or less informed (design fail). Testing with you weekly catches this early.

---

## Resource Cost Breakdown (RBE-OPS Model)

### Z1-ktok (proposal creation + weekly findings filing): 4 tokens
- Week 1: File protocol candidate + BEST_PRACTICES_PROTOCOL.md (1 token)
- Weeks 2–4: File weekly findings (F/IC entries) + roadmap updates (1 token/week × 3 weeks)

### Z3-hr (agent build + testing + fixes): 73 hours
- Week 1 (Auth): 17 hours (Supabase setup, PKCE, login UI, token refresh, RQ tests)
- Week 2 (UX): 20 hours (dashboard layout, Findings/Queue/Molts/search, RQ tests)
- Week 3 (Real-time): 24 hours (audit log schema, WebSocket server/client, monitoring, fixes)
- Week 4 (Freeze): 12 hours (security review, perf audit, bug fixes, findings integration)

### CI-min (test, build, deploy): 600 minutes (~10 hours)
- ~20–30 min per day × 20 working days (compile, test, lint, deploy to staging; includes retries)

### RUN-day (continuous synthetic monitoring, Week 3): 1 day
- Automated probes for latency, uptime, memory (no human intervention needed; runs continuously)

### RAT-min (Z2 ratification labor): 660 minutes (11 hours)
- Week 1: 150 min (testing + review + decision)
- Week 2: 150 min (testing + review + decision + potential re-test)
- Week 3: 120 min (monitoring + review + decision)
- Week 4: 240 min (smoke test + findings review + ratification signature)

*Note: RAT-min is the registered RBE-OPS unit for Z2 ratification labor (CLAUDE.md §B gate requirement, PRIORITY_QUEUE.md governance). Tracked in resource_cost as consumable commitment; Z2 availability is a gate constraint, not a resource.*

---

## Success Criteria (End of Week 4)

### Technical
- ✅ All 5 RQs pass falsifiers (measurable, no ambiguity)
- ✅ 0 security findings from review
- ✅ Performance: median render <500ms, bundle <500KB
- ✅ Uptime in staging >99.9%
- ✅ Code merged to main, CI green

### Z2-Facing
- ✅ Z2 smoke test: all tasks complete successfully
- ✅ Z2 ratifies Q-COCKPIT-V1-RATIFY-01 hash
- ✅ Cockpit ready for production Week 5

### Governance
- ✅ Weekly findings (F/IC entries) filed in REGISTERED.md
- ✅ Tradeoffs documented (if any falsifier relaxed)
- ✅ Audit log seed data populated (historical Z2 decisions)

---

## Weekly Gate Flow

```
Week 1 (Auth):
  RQ-Auth-01 test (phishing, SUS) → falsifier pass?
  RQ-Auth-02 test (token timing)  → falsifier pass?
  ➜ Both pass? Proceed to Week 2
  ➜ Either fails? Iterate Week 1 OR escalate to Z2

Week 2 (UX):
  RQ-UX-01 test (dashboard speed)  → falsifier pass?
  RQ-UX-02 test (audit log)         → falsifier pass?
  ➜ Both pass? Proceed to Week 3
  ➜ Either fails? Iterate Week 2 OR escalate to Z2

Week 3 (Real-time):
  RQ-UX-03 monitoring (WebSocket)   → falsifier pass? (ongoing all week)
  ➜ Passes? Proceed to Week 4
  ➜ Fails? Iterate Week 3 OR escalate to Z2

Week 4 (Freeze):
  Z2 smoke test → all 5 RQs review
  ➜ All pass + Z2 approves? Merge to main, deploy to staging
  ➜ Any fail? Hold, iterate, re-test, escalate to Z2 for final call
```

---

## Falsifiers (The Real Measures)

**Auth (Week 1):**
- Phishing fall rate >10% → security design fails
- SUS score <70 → UX below industry standard
- Token compromise takes >15 min to detect → window too large
- Re-auth abandonment >50% → friction too high

**UX (Week 2):**
- Can't find "next action" in <5s → dashboard doesn't prioritize
- >50% interactions require scrolling → layout broken
- Can't reconstruct decision chain in audit log → accountability fail
- Audit noise >10 events per action → signal-to-noise bad

**Real-time (Week 3):**
- Update latency >30s → not timely for Z2 workflow
- Uptime <99.9% → reliability issue
- Message lag >100ms → perceptible UI freeze
- Memory leak (heap grows >50% over 1hr) → resource leak

**None of these are subjective.** Every falsifier is measurable.

---

## Known Risks

| Risk | Mitigation |
|:-----|:-----------|
| Z2 testing window conflicts | Async testing; 48h decision window |
| Falsifier thresholds too strict | Plan 1 iteration week if needed; escalate if blocker |
| WebSocket reliability unproven | Polling fallback; synthetic uptime monitoring |
| Tight 4-week timeline | Pre-plan iteration week; document known gaps for v1.1 |

---

## Post-Ship: v1.1 Roadmap (Speculative)

If research identifies improvements:
- **RQ-Auth-03:** Multi-factor authentication (TOTP + SMS)
- **RQ-UX-04:** Keyboard shortcuts (power-user workflow)
- **RQ-UX-05:** Dark mode + accessibility audit
- **RQ-Perf-01:** Pagination for large Findings feeds

These will be ranked separately in PRIORITY_QUEUE.md after v1.0 ships.

---

## Relationship to Other Work

**Blocking:** None (cockpit is independent)

**Blocked by:** None

**Related:**
- Q-TEMPORAL-DISSOLUTION-01 (PRIORITY_QUEUE.md governance gate) — cockpit design must respect temporal-purity (no internal deadlines, only external constraints)
- Q-BOOT-PROCESS-MAP-01 (session rituals) — cockpit should reference REGISTERED.md with pinned SHA per IC-030

---

## Integration with REGISTERED.md

Each week, Z3 will file findings as F/IC entries:

```
F-XX: Cockpit Auth UX: PKCE + 15-min token = optimal for Z2 governance
      - Phishing fall rate: 5% (falsifier passes)
      - SUS score: 74 (falsifier passes)
      - Token compromise detection: 8 min (falsifier passes)

F-YY: Cockpit Dashboard: 4-section layout finds "next action" in <3s
      - Task completion time: 3s median (falsifier passes)
      - Scroll overhead: 20% (falsifier passes)

(etc.)
```

If a falsifier trips, file IC-class candidate instead, with root-cause analysis.

---

## Z2 Approval Checklist

Before proceeding, Z2 must confirm:

- [ ] Time available? (~11 hours over 4 weeks OK?)
- [ ] Scope right? (5 RQs cover your governance needs?)
- [ ] Timeline? (Start week of 2026-09-30 OK?)
- [ ] Z3 assigned? (Who builds?)
- [ ] Sign-off? (Will ratify if all falsifiers pass?)

If all boxes checked, Z1 files this candidate in REGISTERED.md and we kick off Week 1.

---

## Filing Instructions for Z2

1. Read COCKPIT_V1_BEST_PRACTICES_PROTOCOL.md (10 min)
2. Read COCKPIT_V1_EXECUTIVE_SUMMARY.md (5 min)
3. Skim COCKPIT_V1_IMPLEMENTATION_ROADMAP.md (tech details, optional)
4. Confirm all 5 checklist items above (async reply)
5. Z1 updates REGISTERED.md with Q-COCKPIT-V1-01 entry (CANDIDATE status)
6. Z1 files weekly findings after each gate (F/IC entries)
7. Week 4: Z2 ratifies Q-COCKPIT-V1-RATIFY-01 (or documents decision to hold/iterate)

---

**Document history:**
- 2026-09-23: Created (Q-COCKPIT-V1-01 candidate block)
- Pending Z2 ratification
