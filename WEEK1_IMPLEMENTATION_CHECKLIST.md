# Week 1 Implementation Checklist (Aug 8-14)

**Goal:** Deploy all infrastructure for fair task orchestration  
**Status:** READY TO EXECUTE  
**Owner:** Infrastructure Lead + Development Team

---

## Day 1 (Aug 8): Kickoff & Infrastructure Planning

### Morning Standup
- [ ] Confirm team availability + roles
- [ ] Brief team on MCP-based orchestration (show architecture diagram)
- [ ] Review ACAT_MCP_PACKAGE_STRUCTURE.md together
- [ ] Review ORCHESTRATION_LAYER.ts together
- [ ] Q&A: Clarify any unknowns

### Infrastructure Setup
- [ ] **GitHub Org Creation**
  - [ ] Create GitHub org: `fair-research-brokerage`
  - [ ] Create repos:
    - [ ] `tasks` (task definitions, GitHub Issues)
    - [ ] `acat-mcp` (ACAT MCP server code)
    - [ ] `orchestration` (orchestration layer code)
    - [ ] `transparency-reports` (public monthly reports)
    - [ ] `assessment-data` (anonymized worker × task data, for analysis)
  - [ ] Setup GitHub Projects board (workflow: Open → In Progress → Complete)
  - [ ] Add team members as collaborators

- [ ] **Open Collective Account**
  - [ ] Create account: `fair-research-brokerage`
  - [ ] Link Stripe account (for payments)
  - [ ] Setup expense categories:
    - [ ] Task funding (employer payments held in escrow)
    - [ ] Worker payments (payouts)
    - [ ] Coordination fees (5% brokerage)
    - [ ] Verification bonuses (40% of fees back to workers)
  - [ ] Test payment flow end-to-end
  - [ ] Create budget template (for transparency reports)

- [ ] **Substack Publication**
  - [ ] Create Substack: `fair-research-brokerage`
  - [ ] Write welcome post (explain mission + model)
  - [ ] Draft monthly report template
  - [ ] Invite pilot members to mailing list

### Documentation
- [ ] Create folder structure in GitHub org
- [ ] Upload all Phase 1 documents:
  - [ ] PHASE1_MASTER_PLAN.md
  - [ ] ACAT_MCP_PACKAGE_STRUCTURE.md
  - [ ] ORCHESTRATION_LAYER.ts
  - [ ] RENTAHUMAN_API_INTEGRATION.md
  - [ ] PHASE1_RECRUITMENT_STRATEGY.md
  - [ ] PHASE1_QUICK_START.md
- [ ] Write README for each repo

---

## Day 2 (Aug 9): ACAT MCP Setup

### RentAHuman API Auth
- [ ] Verify RAH API key works
  ```bash
  curl -H "Authorization: Bearer rah_75ccef6056b836f84c045982d87b4ef0" \
    https://rentahuman.ai/api/v1/account/profile
  ```
- [ ] Document API endpoints we'll use (search_humans, create_bounty, invite_workers, get_submissions)
- [ ] Create `.env.example` with all required variables

### ACAT API Connection
- [ ] Connect to existing ACAT API (`operations/acat/api`)
- [ ] Verify assessment endpoints work
  ```bash
  curl -X POST \
    -H "Authorization: Bearer ${ACAT_API_KEY}" \
    https://localhost:8000/api/v1/acat/assess \
    -d '{worker_id: "test", bio: "..."}'
  ```
- [ ] Document response schema (what ACAT returns)

### ACAT MCP Package
- [ ] Create directory structure (see ACAT_MCP_PACKAGE_STRUCTURE.md)
  ```bash
  mkdir -p acat-mcp/src/{tools,services,models,utils}
  mkdir -p acat-mcp/tests/{tools,services}
  ```
- [ ] Initialize npm project
  ```bash
  cd acat-mcp && npm init -y
  npm install @anthropic-ai/sdk fastmcp axios dotenv pino zod pg
  npm install --save-dev typescript ts-node @types/node jest ts-jest
  ```
- [ ] Create base files:
  - [ ] `src/server.ts` (FastMCP instance)
  - [ ] `src/models/types.ts` (TypeScript interfaces)
  - [ ] `src/services/acat-api-client.ts` (HTTP client)
  - [ ] `package.json` + `tsconfig.json`
  - [ ] `.env.example`

- [ ] Setup database (PostgreSQL)
  ```bash
  createdb acat_calibration
  # Run migrations (see calibration schema below)
  ```

### Database Schema (PostgreSQL)
- [ ] Create tables:
  ```sql
  -- Matches (worker × task pairings)
  CREATE TABLE matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    worker_id VARCHAR NOT NULL,
    task_id VARCHAR NOT NULL,
    match_score FLOAT,
    predicted_quality FLOAT,
    predicted_completion_days INT,
    actual_quality FLOAT,
    actual_completion_days INT,
    status VARCHAR (invited|accepted|completed|submitted),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
  );

  -- Assessments (ACAT scores per worker × task)
  CREATE TABLE assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    worker_id VARCHAR NOT NULL,
    task_id VARCHAR NOT NULL,
    consistency FLOAT,
    truthfulness FLOAT,
    sycophancy FLOAT,
    harm FLOAT,
    reasoning TEXT,
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
  );

  -- Calibration log (ACAT weight changes)
  CREATE TABLE calibration_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP DEFAULT NOW(),
    task_type VARCHAR,
    old_weights JSONB,
    new_weights JSONB,
    accuracy_delta FLOAT,
    prediction_error FLOAT
  );

  -- Worker patterns (learned per worker)
  CREATE TABLE worker_patterns (
    worker_id VARCHAR PRIMARY KEY,
    task_type_strengths JSONB,
    avg_quality FLOAT,
    total_completed INT,
    last_updated TIMESTAMP DEFAULT NOW()
  );

  -- Payments (for transparency)
  CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id VARCHAR NOT NULL,
    worker_id VARCHAR NOT NULL,
    amount FLOAT,
    status VARCHAR (pending|processed|paid),
    created_at TIMESTAMP DEFAULT NOW(),
    paid_at TIMESTAMP
  );
  ```

- [ ] Create indexes:
  ```sql
  CREATE INDEX idx_matches_worker ON matches(worker_id);
  CREATE INDEX idx_matches_task ON matches(task_id);
  CREATE INDEX idx_assessments_worker_task ON assessments(worker_id, task_id);
  CREATE INDEX idx_calibration_task ON calibration_log(task_type);
  ```

### Git Setup
- [ ] Initialize repo + commit structure
  ```bash
  git init acat-mcp
  git add -A
  git commit -m "chore: Initial ACAT MCP package structure"
  ```

---

## Day 3 (Aug 10): Core Tools Implementation

### Tool 1: assess_worker
- [ ] Implement `src/tools/assess.ts`
  - [ ] Tool definition (name, description, schema)
  - [ ] Call to ACAT API client
  - [ ] Scoring logic (weights by task type)
  - [ ] Return assessment response
- [ ] Test with sample worker + task
- [ ] Verify scoring makes sense (high truthfulness + research task → high score)

### Tool 2: score_match
- [ ] Implement `src/tools/score.ts`
  - [ ] Takes multiple assessments
  - [ ] Ranks by match_score
  - [ ] Generates personalized invitation messages
  - [ ] Returns top N
- [ ] Test with 10 mock workers

### Tool 3: predict_performance
- [ ] Implement `src/tools/predict.ts`
  - [ ] Takes assessment + historical data
  - [ ] Predicts quality rating (1-5)
  - [ ] Predicts completion time (days)
  - [ ] Returns confidence interval
- [ ] Test accuracy on historical data (if available)

### Tool 4: learn_from_feedback
- [ ] Implement `src/tools/learn.ts`
  - [ ] Takes prediction + actual outcome
  - [ ] Calculates error
  - [ ] Updates model weights
  - [ ] Logs to database
  - [ ] Persists to GitHub
- [ ] Test with sample feedback

### API Client
- [ ] Implement `src/services/acat-api-client.ts`
  - [ ] assessWorker() → calls POST /api/v1/acat/assess
  - [ ] intakePhase1() → calls POST /api/v1/acat/intake/phase1
  - [ ] Error handling + logging
  - [ ] Retry logic (3 retries with exponential backoff)

### Calibration Service
- [ ] Implement `src/services/calibration.ts`
  - [ ] getWeights(task_type) → return current weights
  - [ ] recalibrate(error_metrics) → update weights
  - [ ] normalizeWeights() → ensure sum to 1.0
  - [ ] logWorkerOutcome() → store in DB
  - [ ] persist() → save to GitHub + DB

---

## Day 4 (Aug 11): Integration & Testing

### MCP Server
- [ ] Implement `src/server.ts`
  - [ ] Create FastMCP instance
  - [ ] Register all 4 tools
  - [ ] Setup error handling
  - [ ] Setup logging
- [ ] Test server startup:
  ```bash
  npm run dev
  # Should print: "MCP server listening on stdio"
  ```

### Persistence Service
- [ ] Implement GitHub logging (`src/services/persistence.ts`)
  - [ ] Save calibration to GitHub Issues (format: JSON in issue body)
  - [ ] Daily log of: timestamp, weights, accuracy improvements
  - [ ] Make repo public (transparency)
  - [ ] Link from Substack/GitHub org README

- [ ] Implement DB persistence
  - [ ] Save matches to DB
  - [ ] Save assessments to DB
  - [ ] Save calibration log
  - [ ] Save payments

### Unit Tests
- [ ] Test assess_worker tool
  ```bash
  npm test -- assess.test.ts
  ```
  - [ ] Mock ACAT API response
  - [ ] Verify scoring logic
  - [ ] Test edge cases (inconsistent worker, etc.)

- [ ] Test calibration service
  - [ ] Weight recalibration logic
  - [ ] Normalization
  - [ ] Persistence to DB

- [ ] Test API client
  - [ ] Successful call
  - [ ] Retry on failure
  - [ ] Error handling

### Integration Test (E2E)
- [ ] Test full flow (mock):
  ```typescript
  const assessment = await assess_worker(mockWorker, mockTask);
  const ranked = await score_match([assessment]);
  const calibration = await learn_from_feedback(assessment, mockOutcome);
  ```
- [ ] Verify: Assessment → Scoring → Learning → DB save

---

## Day 5 (Aug 12): Orchestration Layer Setup

### Orchestration Server
- [ ] Copy ORCHESTRATION_LAYER.ts to `orchestration/` repo
- [ ] Create database access layer
  - [ ] getActiveMatches()
  - [ ] updateMatch()
  - [ ] getTask()
  - [ ] logPayment()

### RAH Integration
- [ ] Create RAH client wrapper
  ```typescript
  // RAH API calls we need
  await rah.search_humans(filters)
  await rah.create_bounty(bounty_spec)
  await rah.invite_workers(bounty_id, worker_ids, messages)
  await rah.get_submissions(bounty_id)
  await rah.get_submission_status(bounty_id)
  ```
- [ ] Mock RAH responses for testing

### Orchestration Loop
- [ ] Implement polling loop (every 5 minutes)
  - [ ] Check for new tasks
  - [ ] Run discovery → matching → invitation
  - [ ] Monitor active tasks
  - [ ] Collect feedback → calibrate

- [ ] Test with single manual task:
  ```bash
  # Manually create task
  const task = {
    id: "test_001",
    title: "Test Research Task",
    budget: 500,
    skills_required: ["research"],
    task_type: "research",
    deadline: "2026-09-15"
  };
  
  # Run orchestrator
  await orchestrator.discoverAndMatch(task);
  
  # Verify:
  # - Workers queried from RAH ✓
  # - Assessments run ✓
  # - Bounty created on RAH ✓
  # - Top 3 workers invited ✓
  # - Matches stored in DB ✓
  ```

---

## Day 6-7 (Aug 13-14): Deployment & Documentation

### Docker Setup
- [ ] Create docker-compose.yml
  ```yaml
  services:
    postgres:
      image: postgres:15
    acat-api:
      build: ../acat/api
      depends_on: [postgres]
    acat-mcp:
      build: ./acat-mcp
      depends_on: [postgres, acat-api]
    orchestration:
      build: ./orchestration
      depends_on: [postgres, acat-mcp]
  ```
- [ ] Test locally:
  ```bash
  docker-compose up
  ```

### Deployment Options
- [ ] Option A: Local machine (for Week 1-2 testing)
- [ ] Option B: Railway / Render (for Week 3+ production)
  - [ ] Push code to GitHub
  - [ ] Connect Railway/Render to repo
  - [ ] Set environment variables
  - [ ] Deploy

### Documentation
- [ ] README for each component:
  - [ ] acat-mcp: "How to use assess_worker, score_match, learn_from_feedback"
  - [ ] orchestration: "How the 5-phase loop works"
  - [ ] transparency: "How calibration is logged publicly"
  
- [ ] API documentation
  - [ ] List all MCP tools + schemas
  - [ ] Example calls for each
  - [ ] Expected responses

- [ ] Operational runbook
  - [ ] How to start services
  - [ ] How to monitor
  - [ ] How to debug
  - [ ] How to scale

### Team Communication
- [ ] Post updates to GitHub Issues (transparency)
  - [ ] Day 1: "Infrastructure setup complete"
  - [ ] Day 2: "ACAT API connected"
  - [ ] Day 3: "Core tools implemented"
  - [ ] Day 4: "Integration tests passing"
  - [ ] Day 5: "Orchestration loop working"
  - [ ] Day 6-7: "Deployed & ready for Week 2"

- [ ] Record short demo video (2-3 min):
  - [ ] Show ACAT MCP assess_worker tool
  - [ ] Show scoring + ranking
  - [ ] Show learning from feedback
  - [ ] Post to Substack + GitHub

---

## Exit Criteria (Week 1 Complete)

✅ **Infrastructure:**
- [ ] GitHub org + 5 repos live
- [ ] Open Collective account + payment flow tested
- [ ] PostgreSQL database deployed
- [ ] Substack publication live

✅ **Code:**
- [ ] ACAT MCP package structure complete
- [ ] All 4 tools implemented + unit tested
- [ ] Orchestration layer implemented
- [ ] Docker-compose ready

✅ **Testing:**
- [ ] MCP server starts without errors
- [ ] ACAT API connected + responding
- [ ] RAH API auth working
- [ ] Single end-to-end test passed (manual task → workers matched)

✅ **Documentation:**
- [ ] All Phase 1 docs in GitHub
- [ ] README files complete
- [ ] API documentation ready
- [ ] Team briefed + aligned

✅ **Team:**
- [ ] All roles assigned
- [ ] Communication channel established (GitHub Issues)
- [ ] Daily standup routine working
- [ ] Next week (recruitment) understood

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| ACAT API connection fails | Have fallback: use simple skill-based matching (no ACAT) |
| RAH API limits requests | Implement rate limiting + queuing |
| Database migration issues | Pre-test migrations locally before deploying |
| Team unavailable | Pre-record demos so knowledge isn't lost |
| Scope creep | Strict PR review (no new features in Week 1) |

---

## Time Allocation

| Task | Time | Owner |
|------|------|-------|
| Day 1: Setup | 4h | Infrastructure Lead |
| Day 2: APIs | 4h | Infrastructure Lead |
| Day 3: Tools | 8h | Backend Engineer |
| Day 4: Integration | 6h | Backend Engineer + QA |
| Day 5: Orchestration | 6h | Backend Engineer |
| Day 6-7: Deploy + Docs | 6h | Infrastructure Lead + Backend Engineer |
| **Total** | **~34 hours** | **2-3 person team** |

---

**Status:** READY TO EXECUTE  
**Start Date:** Aug 8, 2026  
**Exit Date:** Aug 14, 2026  
**Owner:** Infrastructure Lead  
**Next Phase:** Week 2 (Grant applications + Worker discovery)
