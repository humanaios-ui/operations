# Phase 1 Pilot: Master Execution Plan

**Status:** ✅ HYBRID EXECUTION LIVE  
**Duration:** 6 weeks (Aug 8 — Sep 19, 2026)  
**Owner:** outreach  
**Gate:** ACAT assessment design on hold pending mesh feedback (expected Aug 10)

---

## Overview

**Phase 1 is a 6-week pilot to test: Does fair task orchestration work?**

- Deploy infrastructure (GitHub, Open Collective, Substack)
- Recruit employers + workers from network
- Run 20-50 real matches
- Measure: satisfaction, payment speed, repeat rates, ACAT predictive validity
- Publish monthly transparency report
- Go/no-go decision: scale to Phase 2 or iterate

---

## Timeline & Workstreams

### WEEK 1-2: INFRASTRUCTURE SETUP (Aug 8-21)
**Parallel workstreams — zero mesh dependencies**

| Workstream | Owner | Tasks | Status |
|-----------|-------|-------|--------|
| **GitHub Org** | infra lead | Create org, repos, Projects board, templates, sample tasks | ✅ Ready |
| **Open Collective** | finance lead | Setup account, payment methods, expense categories, test flow | ✅ Ready |
| **Substack** | comms lead | Setup newsletter, communities, draft report template | ✅ Ready |
| **RentAHuman API** | infra lead | Authenticate with RAH API, map bounty system, design worker matching | ✅ Ready |
| **Recruitment Materials** | recruitment lead | Draft employer/worker outreach, prep target lists | ✅ Ready |
| **Documentation** | ops lead | Finalize guides: "How to post", "How to apply", FAQ | ✅ Ready |

**Week 1 Success Criteria:**
- GitHub org + repos live (public)
- Open Collective account operational (test payment flow works)
- Substack publication ready
- Recruitment materials finalized
- Sample tasks drafted (waiting Week 2 to post)

**Week 2 Success Criteria:**
- 3-5 sample tasks posted to GitHub (not yet funded, for visibility)
- Recruitment outreach begins (Week 3 start)
- Substack invite sent to pilot members (prepare for reporting)

---

### WEEK 3-4: RECRUITMENT (Aug 22 — Sep 4)
**Parallel — depends on Week 1 infrastructure**

| Workstream | Owner | Targets | Status |
|-----------|-------|---------|--------|
| **Employer Recruitment** | recruitment lead | 3-5 employers (Tier 1 internal + Tier 2 academic) | ⏳ Week 3 |
| **Worker Recruitment** | recruitment lead | 10-15 workers (direct + public posts) | ⏳ Week 3-4 |
| **Task Funding** | finance lead | Secure funding from employers via Open Collective | ⏳ Week 3 |
| **Task Customization** | ops lead | Refine task descriptions based on employer input | ⏳ Week 3-4 |

**Week 3 Success Criteria:**
- 3-5 employers confirmed + tasks funded
- 5-10 workers recruited (direct + public posts)
- First tasks posted to GitHub + funded via Open Collective

**Week 4 Success Criteria:**
- 10-15 workers matched to tasks (manual matching, ACAT on hold)
- All pilot tasks underway (workers started work)
- Open Collective payments processing correctly

---

### WEEK 5-6: EXECUTION & MEASUREMENT (Sep 5-19)
**Depends on Week 3-4 recruitment**

| Activity | Owner | Measurement | Status |
|----------|-------|-------------|--------|
| **Task Completion** | workers + employers | Track completion rate, quality, speed | ⏳ Week 5-6 |
| **Payment Processing** | finance lead | Measure payout speed, satisfaction | ⏳ Week 5-6 |
| **Feedback Collection** | comms lead | Worker + employer surveys, qualitative feedback | ⏳ Week 5-6 |
| **Transparency Report** | comms lead | Publish Month 1 results (all financials, learnings) | ⏳ Sep 1-5 |
| **ACAT Integration** | [blocked] | If mesh feedback arrives: integrate assessment, measure predictive validity | ⏳ Week 5 (if cleared) |

**Week 5-6 Success Criteria:**
- 80%+ worker satisfaction (surveys)
- 80%+ employer satisfaction (surveys)
- 95%+ task completion rate (quality work)
- Average payment speed: 3-5 business days
- 50%+ workers express interest in repeat work
- Transparency report published (public)

---

## Hybrid Execution Model

### INFRASTRUCTURE (READY NOW)
✅ **GitHub org setup** — LIVE Week 1  
✅ **Open Collective** — LIVE Week 1  
✅ **Substack template** — LIVE Week 2  
✅ **RentAHuman API integration** — LIVE Week 1  
✅ **Recruitment materials** — READY Week 3

### RAH API INTEGRATION (NEW - Week 1-2)

**What:** Integrate RentAHuman's API as our worker pool + bounty system  
**Why:** Access 10K+ vetted research workers, use their platform as infrastructure layer  
**How:** Use RAH API to search workers, post bounties, invite matched workers, track completion

**Week 1 Tasks:**
- [ ] Authenticate with RAH API (`rah_75ccef6056b836f84c045982d87b4ef0`)
- [ ] Map RAH bounty model to our task structure
- [ ] Design matching algorithm (ACAT + RAH ratings)
- [ ] Setup payment flow integration (Open Collective → RAH or direct)
- [ ] Document RAH worker profiles integration

**Week 3-4 Execution:**
- [ ] Query RAH for 15-20 research-aligned workers (`GET /humans/search`)
- [ ] Run quick ACAT assessment on matched workers (5-question version)
- [ ] Post our 5 pilot tasks to RAH bounty system (`POST /bounties`)
- [ ] Invite matched workers with personalized reasoning (`POST /bounties/{id}/invite_workers`)
- [ ] Track completion + quality through RAH API

**Week 5-6 Measurement:**
- [ ] Analyze RAH API data: completion rates, time-to-complete, quality
- [ ] Measure: ACAT prediction accuracy (did matched workers perform better?)
- [ ] Collect satisfaction feedback (did workers prefer fair matching?)
- [ ] Document: "RAH workers showed X% higher satisfaction with our matching"

**RAH API Endpoints Used:**
- `GET /humans/search` — Find workers by skill
- `GET /humans/{id}` — Load worker profile + history
- `POST /bounties` — Create research tasks
- `GET /bounties` — List active tasks
- `POST /bounties/{id}/invite_workers` — Assign matched workers
- `GET /bounties/{id}/submissions` — Get submitted work
- `POST /bounties/{id}/feedback` — Rate worker quality + satisfaction

**Integration Value:**
- No parallel system needed (use RAH as infrastructure)
- 10K+ vetted workers available immediately
- Real bounty platform experience (not mock)
- Investor proof: "We improved outcomes on existing platform"  

### MATCHING (ON HOLD)
⏳ **ACAT assessment** — FROZEN until humanaios validates (expected Aug 10)  
- Week 1-2: Create draft ACAT lite assessment (5 questions on task-person behavioral fit)
- Week 2-3: AWAIT mesh feedback
- Week 3+: Integrate ACAT if validated, OR use simpler matching if not

**If ACAT validated by Aug 10:**
- Use ACAT assessment in matching (Week 4)
- Measure predictive validity (Week 5-6)

**If ACAT not validated by Aug 10:**
- Use manual matching (Week 4) based on resume/portfolio + task fit
- Plan ACAT validation for Phase 2
- Still measure matching quality (satisfaction + completion rate)

---

## Resource Allocation

| Role | Owner | Hours/Week | Availability |
|------|-------|-----------|--------------|
| **Infrastructure Lead** | [name] | 8h (Week 1-2, then 2h/week) | Critical Week 1-2 |
| **Finance Lead** | [name] | 4h (Week 1-2), 4h (Week 3-4), 2h (Week 5-6) | Ongoing |
| **Recruitment Lead** | [name] | 2h (Week 1-2), 10h (Week 3-4), 2h (Week 5-6) | Critical Week 3-4 |
| **Communications Lead** | [name] | 4h (Week 1-2), 2h (Week 3-4), 6h (Week 5-6) | Report critical Week 5 |
| **Operations Lead** | [name] | 3h (Week 1-2), 3h (Week 3-4), 2h (Week 5-6) | Lightweight ongoing |

**Total: ~70 hours across 6 weeks (11-12 hours/week average)**

---

## Key Decision Points

### Decision Point 1: Mesh Feedback (Aug 10)
**Decision:** Does ACAT assessment move forward?
- **If YES:** Integrate into Week 4 matching, measure validity Week 5-6
- **If NO:** Use simpler matching Week 4, defer ACAT to Phase 2

**Input needed from:** humanaios (methodology), autonomy (algorithm viability), mesh-support (governance)

---

### Decision Point 2: Recruitment Success (Aug 28)
**Decision:** Do we have enough employers + workers to run meaningful pilot?
- **Minimum:** 3 employers, 10 workers (20 tasks)
- **Optimal:** 5 employers, 15 workers (50 tasks)
- **If below minimum:** Extend recruitment to Sep 4, adjust pilot scope

---

### Decision Point 3: Satisfaction Checkpoint (Sep 12)
**Decision:** Should we scale to Phase 2 or iterate?
- **80%+ satisfaction + 50%+ repeat interest + 95%+ completion:** Scale Phase 2
- **60-80% satisfaction or issues to fix:** Iterate (Phase 1b, Sep 19 - Oct 3)
- **<60% satisfaction:** Pivot approach, investigate root causes

---

## Go/No-Go Criteria (Sep 12)

| Criterion | Target | Achieved? | Status |
|-----------|--------|-----------|--------|
| Worker satisfaction | 80%+ | [measure] | ✅/❌ |
| Employer satisfaction | 80%+ | [measure] | ✅/❌ |
| Task completion rate | 95%+ | [measure] | ✅/❌ |
| Repeat interest (workers) | 50%+ | [measure] | ✅/❌ |
| Repeat interest (employers) | 50%+ | [measure] | ✅/❌ |
| Payment processing speed | 3-5 days | [measure] | ✅/❌ |
| Platform operational cost | <$[target]/task | [measure] | ✅/❌ |

**Gate logic:**
- 5+ of 7 criteria met → **GO to Phase 2** (Scale to 100-200 matches/month)
- 3-4 of 7 criteria met → **ITERATE** (Phase 1b, improve + retest)
- <3 criteria met → **PIVOT** (Reassess model, investigate what failed)

---

## Risk Mitigation

| Risk | Severity | Mitigation |
|------|----------|-----------|
| ACAT assessment delays | High | Created on hold Week 1; mesh feedback expected by Aug 10; fallback to manual matching |
| Recruitment underperforms | Medium | Tier 1 (internal) + Tier 2 (warm) ensures minimum 3-5 employers; workers: expand to Tier 3 if needed |
| Payment processing issues | Medium | Test Open Collective end-to-end Week 1; have Stripe backup |
| Worker quality issues | Medium | Measure satisfaction + completion rate; iterate matching criteria Week 5-6 |
| Employer churn | Low | Internal employers (humanaios, autonomy) committed; backup external tasks if needed |
| Mesh feedback absent | Low | Proceed Week 4 with simpler matching; revisit ACAT Phase 2 |

---

## Success Signals (Weekly Checkpoints)

### Week 1 Check-in (Aug 14)
- ✅ GitHub org live + public
- ✅ Open Collective account created + test payment successful
- ✅ Substack ready to publish

### Week 2 Check-in (Aug 21)
- ✅ Sample tasks posted (visible, not yet funded)
- ✅ Recruitment materials finalized
- ✅ Internal team briefing complete (everyone knows their role)

### Week 3 Check-in (Aug 28)
- ✅ 3-5 employers confirmed + tasks funded
- ✅ 5-10 workers recruited
- ✅ First batch of tasks underway

### Week 4 Check-in (Sep 4)
- ✅ 10-15 workers matched + working on tasks
- ✅ No critical issues (payment, access, communication)
- ✅ Mesh feedback on ACAT integrated (if validation succeeded)

### Week 5 Check-in (Sep 11)
- ✅ 80%+ of tasks on track for completion
- ✅ Early satisfaction feedback positive
- ✅ Transparency report drafted (ready to publish)

### Week 6 Check-in (Sep 18)
- ✅ All tasks complete (or very close)
- ✅ Payments processed
- ✅ Transparency report published
- ✅ Satisfaction surveys returned (80%+ target)

---

## Outputs (Deliverables)

### By Sep 1
- ✅ Infrastructure live (GitHub, Open Collective, Substack)
- ✅ 20-50 tasks underway
- ✅ Workers actively engaged

### By Sep 5
- ✅ Month 1 transparency report published (Substack)
- ✅ All financials public (Open Collective)
- ✅ Worker testimonials (anonymized, public)

### By Sep 12
- ✅ Satisfaction surveys closed
- ✅ Go/no-go decision made
- ✅ Phase 2 plan (if approved) drafted

### By Sep 19
- ✅ Mesh feedback integrated (ACAT + governance)
- ✅ Lessons learned documented
- ✅ Ready to scale Phase 2 or iterate Phase 1b

---

## What's Not Blocked (Proceed Now)

✅ GitHub org setup  
✅ Open Collective integration  
✅ Substack publication  
✅ Recruitment materials  
✅ Worker sourcing  
✅ Employer outreach  
✅ Payment flow testing  
✅ Transparency reporting  

## What's Blocked (Waiting on Mesh)

⏳ ACAT assessment methodology (humanaios)  
⏳ Governance structure finalization (mesh-support)  
⏳ Autonomy integration (autonomy)  

**Workaround:** Proceed with simpler matching Week 4; integrate ACAT Week 5 if validated.

---

**Phase 1 is a GO. Start Week 1 infrastructure now. Mesh feedback gates ACAT depth, not pilot execution.**
