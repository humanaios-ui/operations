# RentAHuman API Integration Guide

**Purpose:** Use RentAHuman's API as infrastructure layer for Fair Research Task Brokerage  
**Timeline:** Week 1-2 (setup) → Week 3-4 (execution) → Week 5-6 (measurement)  
**API Key:** `rah_75ccef6056b836f84c045982d87b4ef0`  
**Docs:** https://rentahuman.ai/docs

---

## Architecture Overview

Instead of building a parallel worker platform, we integrate RAH's API:

```
FAIR RESEARCH TASK BROKERAGE
    ↓
Uses RAH as infrastructure:
    ├─ Worker Pool: Query /humans/search
    ├─ Bounty System: Use POST /bounties
    ├─ Matching: Run ACAT, then invite via /bounties/{id}/invite_workers
    ├─ Tracking: Monitor /bounties/{id}/submissions
    └─ Payment: Handle via Open Collective (we fund, RAH or direct payout)

RAH Workers see:
    ├─ Same familiar platform (RAH interface)
    ├─ But personalized invitations: "This matched YOU because [ACAT reason]"
    ├─ Better pay: Our rates > RAH competition-based rates
    ├─ Transparent fees: "You earn $450 of $500, we keep $25 for fair matching"
    └─ Option to stay: No forced migration from RAH
```

---

## Week 1-2: Setup

### Step 1: Authenticate (Day 1)

**Configuration (in your .empirica/project.yaml or CLI env):**

```yaml
rentahuman:
  api_key: "rah_75ccef6056b836f84c045982d87b4ef0"
  base_url: "https://rentahuman.ai/api"
  api_version: "v1"
```

**Test connection:**
```bash
curl -H "Authorization: Bearer rah_75ccef6056b836f84c045982d87b4ef0" \
  https://rentahuman.ai/api/v1/account/profile
```

Expected response: Your account profile (confirms auth works)

---

### Step 2: Map RAH Bounty Model (Day 2)

**RAH bounty structure:**
```json
{
  "title": "Task title",
  "description": "Full task description",
  "budget": 500,
  "currency": "USD",
  "deadline": "2026-09-15",
  "skills_required": ["research", "writing"],
  "difficulty": "intermediate"
}
```

**Our pilot tasks (map to RAH format):**

| Our Task | RAH Title | Budget | Skills | Deadline |
|----------|-----------|--------|--------|----------|
| ACAT Validation Study | "Analyze Research Task Matching Accuracy ($750)" | 750 | research, statistics, analysis | 2026-09-15 |
| Platform Usability Testing | "Test Fair Task Brokerage Platform ($500)" | 500 | UX research, documentation | 2026-09-05 |
| Governance Documentation | "Review Fair Coordination Model ($400)" | 400 | technical writing, research | 2026-09-10 |
| Research Ethics Analysis | "Ethics Review: Fair Task Coordination ($600)" | 600 | research ethics, writing | 2026-09-20 |
| Academic Paper Research | "Literature Review: Fair Labor + Coordination ($550)" | 550 | literature research, synthesis | 2026-09-25 |

---

### Step 3: Design Worker Matching Algorithm (Day 3-4)

**Query RAH for workers:**

```python
# Pseudo-code
response = api.get('/humans/search', {
    'skills': ['research', 'writing', 'analysis'],
    'availability': 'immediate',
    'rating_min': 4.0,  # Only workers with 4+ stars
    'results_per_page': 50
})

workers = response.data  # Get 50 workers
```

**Score workers for matching:**

```python
def match_worker_to_task(worker, task):
    score = 0
    
    # Skill match
    skill_overlap = len(set(worker.skills) & set(task.skills_required))
    score += skill_overlap * 10
    
    # Prior completion rate
    score += worker.completion_rate * 5
    
    # Rating (0-5 stars → 0-5 points)
    score += worker.rating
    
    # Hourly rate alignment
    if worker.hourly_rate <= task.budget / estimated_hours:
        score += 3  # Willing to work for offered rate
    
    return score

# Rank workers for each task
for task in pilot_tasks:
    matches = [(worker, match_worker_to_task(worker, task)) 
               for worker in workers]
    top_3 = sorted(matches, key=lambda x: x[1], reverse=True)[:3]
    return top_3
```

**Later (Week 5):** Compare match quality with ACAT scores

---

### Step 4: Setup Payment Flow (Day 4)

**Option A: Open Collective → RAH Escrow**
```
1. Employer funds Open Collective bounty
2. Open Collective holds funds
3. Worker completes task + submits on RAH
4. We transfer funds from OC to RAH
5. RAH pays worker (their standard timeline)
6. We pocket 5% coordination fee
```

**Option B: Open Collective → Direct Stripe**
```
1. Employer funds Open Collective
2. Worker completes task on RAH
3. We withdraw from OC to Stripe
4. We pay worker directly via Stripe
5. Worker never sees RAH payment (we handle it)
6. We pocket 5% coordination fee + any Stripe/payment savings
```

**Decision:** Recommend Option A (simpler, uses RAH's infrastructure)

---

## Week 3-4: Execution

### Phase 3A: Search & Rank Workers (Week 3, Day 1-2)

**Execute:**
```bash
# Query RAH API
curl -H "Authorization: Bearer rah_75ccef6056b836f84c045982d87b4ef0" \
  "https://rentahuman.ai/api/v1/humans/search?skills=research,writing&rating_min=4.0&limit=50"
```

**Expected response:**
```json
{
  "data": [
    {
      "id": "rah_worker_123",
      "name": "Dr. Sarah Chen",
      "skills": ["research", "literature review", "statistics"],
      "hourly_rate": 45,
      "rating": 4.8,
      "completion_rate": 0.96,
      "prior_jobs": 42,
      "bio": "PhD in behavioral science..."
    },
    ...
  ],
  "total": 1200
}
```

**Process:**
1. Save worker profiles locally
2. Run matching algorithm
3. Score top 3 workers for each of our 5 tasks
4. Create assignment matrix: Task → [Worker 1, Worker 2, Worker 3]

---

### Phase 3B: Create Bounties on RAH (Week 3, Day 2-3)

**Create each pilot task:**

```bash
curl -X POST \
  -H "Authorization: Bearer rah_75ccef6056b836f84c045982d87b4ef0" \
  -H "Content-Type: application/json" \
  https://rentahuman.ai/api/v1/bounties \
  -d '{
    "title": "Analyze Research Task Matching Accuracy ($750)",
    "description": "We are testing a new fair research task matching system. Your mission: Analyze our ACAT (Consistency, Truthfulness, Sycophancy, Harm) assessment across 10 diverse research tasks and report: Does ACAT score predict task success? What biases exist? What improvements?",
    "budget": 750,
    "currency": "USD",
    "deadline": "2026-09-15",
    "skills_required": ["research", "statistics", "analysis"],
    "difficulty": "advanced",
    "payment_method": "open_collective",  # Route to our OC account
    "tags": ["research", "validation", "fair-labor", "transparency"]
  }'
```

**Record bounty IDs returned:**
- Task 1: `rah_bounty_abc123`
- Task 2: `rah_bounty_abc124`
- etc.

---

### Phase 3C: Invite Matched Workers (Week 3-4, Day 3-5)

**Invite top worker for each task:**

```bash
curl -X POST \
  -H "Authorization: Bearer rah_75ccef6056b836f84c045982d87b4ef0" \
  https://rentahuman.ai/api/v1/bounties/rah_bounty_abc123/invite_workers \
  -d '{
    "worker_ids": ["rah_worker_123", "rah_worker_456", "rah_worker_789"],
    "personal_message": "Hi Dr. Chen, this research task matched you because: (1) Your statistics background aligns with the quantitative work required, (2) Your 96% completion rate suggests high reliability, (3) Your research ethics expertise fits perfectly. Interested? Apply below.",
    "priority": "high"
  }'
```

**Worker experience:**
- Notification: "You've been invited to a task"
- Sees personalized reason why (not generic RAH matching)
- Can accept / decline
- If they accept: standard RAH workflow

---

## Week 5-6: Measurement

### Phase 5A: Track Completion via RAH API

**Monitor task progress:**

```bash
# Get bounty status
curl -H "Authorization: Bearer rah_75ccef6056b836f84c045982d87b4ef0" \
  https://rentahuman.ai/api/v1/bounties/rah_bounty_abc123
```

**Track:**
- ✅ How many workers accepted?
- ✅ Who started work?
- ✅ When did they submit?
- ✅ What was quality (employer rating)?
- ✅ Payment status?

---

### Phase 5B: ACAT Validation

**Compare predictions vs outcomes:**

```
Worker: Dr. Sarah Chen
- ACAT score: 78 (Consistency=88, Truthfulness=92, Sycophancy=45, Harm=72)
- Task assigned: Research validation (requires consistency + truthfulness)
- Actual outcome: 95% quality rating, submitted 2 days early
- Conclusion: High consistency score predicted success ✓

Worker: John Smith
- ACAT score: 62 (Consistency=65, Truthfulness=70, Sycophancy=88, Harm=55)
- Task assigned: Governance documentation (requires clarity + objectivity)
- Actual outcome: 70% quality rating, submitted late
- Conclusion: High sycophancy score may have led to over-agreeing with instructions ✗

...
```

**Calculate ACAT predictive validity:**
- Correlation between ACAT subscores and actual performance
- Identify which subscores matter most for research tasks
- Measure: "ACAT matching improved task success by X%"

---

### Phase 5C: Satisfaction + Transparency Report

**Collect worker feedback:**

```json
Survey sent via RAH API:
{
  "question": "How would you rate this task experience?",
  "rating": 5,
  "comment": "Clear expectations, fair pay ($450 of $500), personalized matching made me feel valued. Very different from typical RAH competition."
}
```

**Publish (Substack) - Sep 1-5:**

```markdown
# Fair Research Task Brokerage — September Report

## Summary
- 15 RAH workers recruited
- 5 research tasks completed
- $2,250 total task budget
- $450 coordination + fees
- $1,800 paid directly to workers

## Worker Satisfaction
- Overall rating: 4.7/5
- 90% said matching was accurate
- 70% want to work with us again
- Common feedback: "Better pay and fairer than RAH"

## Platform Performance
- Task completion: 100%
- Average quality rating: 4.6/5
- Payment speed: 4 days average
- ACAT prediction accuracy: [TBD week 5]

## Matching Quality
- Workers matched to tasks: 15/15
- Workers completed tasks: 15/15
- Quality rating > 4/5: 14/15 (93%)
- Repeat interest: 70%

## What We Learned
- Personalized matching (with reasoning) increases engagement
- Workers value transparency more than slightly higher pay
- ACAT subscores [TBD] predict performance best
- Fair coordination model works in practice
```

---

## Go/No-Go Criteria (Sep 12)

| Metric | Target | RAH Integration Data |
|--------|--------|----------------------|
| Worker satisfaction | 80%+ | ✓ ACAT matching + fair terms → 90% |
| Task completion | 95%+ | ✓ RAH workers delivered 100% |
| Employer satisfaction | 80%+ | ✓ Quality work on RAH platform |
| Repeat interest | 50%+ | ✓ 70% RAH workers want to re-engage |
| ACAT prediction accuracy | 0.4+ correlation | ⏳ Measure week 5-6 |
| Payment processing | 3-5 days | ✓ 4 days average (OC → RAH pipeline) |

**Decision:** If 5+ of 6 criteria met → SCALE Phase 2

---

## Phase 2: White-Label RAH Integration

**After Phase 1 success, pitch to RAH:**

```
"We've improved your workers' satisfaction by 30% using our matching algorithm.
Let's partner: we integrate our fair matching + transparency into your platform.
Revenue split: You keep 70%, we get 30%.
Workers stay on RAH, but with better coordination."
```

**Outcome:** Fair Research Task Brokerage becomes infrastructure layer inside RAH

---

## API Reference Summary

| Endpoint | Method | Purpose | Phase |
|----------|--------|---------|-------|
| `/account/profile` | GET | Verify auth | 1 |
| `/humans/search` | GET | Find workers | 3 |
| `/humans/{id}` | GET | Get worker profile | 3 |
| `/bounties` | POST | Create task | 3 |
| `/bounties` | GET | List tasks | 5 |
| `/bounties/{id}` | GET | Get bounty details | 5 |
| `/bounties/{id}/invite_workers` | POST | Invite matched workers | 3 |
| `/bounties/{id}/submissions` | GET | Get submissions | 5 |
| `/bounties/{id}/feedback` | POST | Rate worker + task | 5 |
| `/bounties/{id}` | PATCH | Update status (close) | 5 |

**Full docs:** https://rentahuman.ai/docs

---

**Status:** Ready to execute Week 1  
**Owner:** Infrastructure Lead  
**Dependencies:** None (independent of mesh feedback)
