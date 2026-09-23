# COCKPIT v1.0 Implementation Roadmap

**Timeline:** 4 weeks (Weeks 1–4) + 1 week production rollout (Week 5)  
**Start date:** 2026-09-30 (proposed; subject to Z2 approval)  
**Tech stack:** React 18 + TypeScript + Supabase (PostgRES) + WebSocket (Socket.io) + Tailwind CSS  
**Deployment target:** humanaios-ui/operations repo + staging.humanaios-ui.com  

---

## High-Level Architecture

```
┌────────────────────────────────────────────────────────┐
│ Cockpit Frontend (React + TypeScript)                  │
│ • REGISTERED.md live feed (Findings section)           │
│ • PRIORITY_QUEUE.md viewer (Queue section)             │
│ • Molt cycle tracker (Molts section)                   │
│ • Audit log (Audit section)                            │
└────────────────┬─────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
┌───────v──────┐  ┌──────v────────┐
│ Supabase DB  │  │ WebSocket API  │
│ (audit_log,  │  │ (live updates) │
│  molt_state, │  │                │
│  constants)  │  └────────────────┘
└──────────────┘
        │
        └──────── Reads from GitHub (REGISTERED.md, PRIORITY_QUEUE.md)
                  via GitHub API + local cache
```

---

## Week-by-Week Breakdown

### **Week 1: Authentication + Auth UX Testing**

**Goals:**
- ✅ Supabase Auth setup (OAuth PKCE flow)
- ✅ httpOnly cookie session storage
- ✅ Login/logout flow UI
- ✅ Pass RQ-Auth-01 & RQ-Auth-02 falsifiers

**Tasks:**

| Day | Task | Owner | Hours | Deliverable |
|:----|:-----|:------|:------|:-----------|
| 1 | Set up Supabase Auth project + OAuth config (Google/GitHub) | Z3 | 2 | .env configured, auth enabled |
| 1 | Implement PKCE flow in React + httpOnly cookie storage | Z3 | 4 | Auth hook + middleware |
| 1 | Build login/logout UI (minimal, no styling yet) | Z3 | 2 | Login form component |
| 1 | **RQ-Auth-01 test:** Phishing sim + SUS survey | Night + 1 tester | 1 | Test report + results |
| 2 | Fix auth UX issues from RQ-Auth-01 (if any) | Z3 | 2 | Updated auth flow |
| 2 | Implement token refresh logic (15-min access, 4-hr refresh) | Z3 | 3 | Token manager + refresh handler |
| 2 | **RQ-Auth-02 test:** Token timing + re-auth behavior | Night + 1 tester | 1 | Test report + results |
| 2 | Fix token timing issues (if falsifier tripped) | Z3 | 2 | Updated token strategy |

**Output:** Authenticated user can log in, tokens refresh silently, session persists across page reload.

**SQL schema (Week 1):**
```sql
-- Supabase Auth tables (auto-created by Supabase)
-- (no custom tables needed yet)
```

**Gate:** Both RQ-Auth-01 and RQ-Auth-02 falsifiers must pass. If either fails, iterate same week.

---

### **Week 2: Dashboard UX + Queue/Findings Integration**

**Goals:**
- ✅ 4-section dashboard layout (Findings, Queue, Molts, Audit)
- ✅ Live feed from REGISTERED.md + PRIORITY_QUEUE.md (via GitHub API + polling)
- ✅ Search & filtering UI
- ✅ Pass RQ-UX-01 & RQ-UX-02 falsifiers

**Tasks:**

| Day | Task | Owner | Hours | Deliverable |
|:----|:-----|:------|:------|:-----------|
| 1 | Design 4-section dashboard layout (Figma or HTML) | Z3 | 2 | Layout spec + wireframe |
| 1 | Implement React layout (tabs + sections) | Z3 | 3 | Dashboard shell component |
| 1 | Build Findings feed (fetch REGISTERED.md, parse YAML frontmatter) | Z3 | 4 | Findings section + drill-down |
| 1 | **RQ-UX-01 test:** Task completion + scroll analysis | Night + lead | 1 | Test report |
| 2 | Build Queue viewer (fetch PRIORITY_QUEUE.md, sortable table) | Z3 | 3 | Queue section + sorting |
| 2 | Add search & filtering (Findings by tag/status, Queue by impact) | Z3 | 3 | Search box + filter UI |
| 2 | Build Molts section (query MOLT_STATE.md, countdown timers) | Z3 | 3 | Molts section + visual status |
| 2 | **RQ-UX-02 test:** Audit log reconstruction (start building) | Night + auditor | 1 | Partial test report |

**Output:** Dashboard displays all 4 sections, can filter/search, drill into findings, see molt windows.

**SQL schema (Week 2):**
```sql
CREATE TABLE IF NOT EXISTS cockpit_cache (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  resource_type TEXT NOT NULL, -- 'REGISTERED', 'PRIORITY_QUEUE', 'MOLT_STATE'
  content JSONB NOT NULL,
  fetched_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '1 hour',
  github_sha TEXT
);

CREATE TABLE IF NOT EXISTS cockpit_search_index (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  resource_id TEXT NOT NULL, -- F-XX, IC-XXX, Q-CANDIDATE-XX
  resource_type TEXT NOT NULL,
  title TEXT,
  tags TEXT[],
  body TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

**Gate:** RQ-UX-01 and RQ-UX-02 must pass. If either fails, iterate same week.

---

### **Week 3: Audit Log + WebSocket Real-Time**

**Goals:**
- ✅ Immutable audit log (all Z2 decisions + Z3 executions)
- ✅ WebSocket live updates for all 4 sections
- ✅ Pass RQ-UX-03 falsifier (latency, uptime, lag)

**Tasks:**

| Day | Task | Owner | Hours | Deliverable |
|:----|:-----|:------|:------|:-----------|
| 1 | Design audit log schema (immutable ledger) | Z3 | 2 | Schema spec |
| 1 | Create audit_log table + seed with historical data from REGISTERED.md | Z3 | 4 | Table + backfill script |
| 1 | Build audit log UI (time-series view, filterable) | Z3 | 3 | Audit section + filters |
| 1 | Implement audit reconstruction task (show all decisions on resource X) | Z3 | 2 | Query function + UI |
| 2 | Set up Socket.io server (auth guard, subscribe to channels) | Z3 | 3 | WebSocket server + auth |
| 2 | Implement client-side subscriptions (Findings, Queue, Molts channels) | Z3 | 3 | Socket client + reconnect logic |
| 2 | Add auto-refresh polling (fallback if WebSocket down) | Z3 | 2 | Polling + hybrid update logic |
| 3 | **RQ-UX-03 testing starts:** Latency probes + uptime monitoring | Z3 + synthetic | Continuous | Probe data |
| 3–4 | Monitor WebSocket metrics, fix any lags or disconnects | Z3 | 5 | Bug fixes + optimization |

**Output:** Audit log visible, all 4 sections update in real-time via WebSocket, polling fallback works.

**SQL schema (Week 3):**
```sql
CREATE TABLE IF NOT EXISTS audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  actor TEXT NOT NULL, -- 'Z2:Night', 'Z3:Claude', etc.
  action TEXT NOT NULL, -- 'ACCEPTED', 'REJECTED', 'EDITED', 'EXECUTED'
  resource_type TEXT NOT NULL, -- 'REGISTERED', 'PRIORITY_QUEUE', 'MOLT', 'CONFIG'
  resource_id TEXT NOT NULL, -- F-XX, Q-CANDIDATE-XX, etc.
  decision_rationale TEXT,
  changed_fields JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_resource (resource_type, resource_id),
  INDEX idx_actor_date (actor, created_at)
);

CREATE TABLE IF NOT EXISTS molt_state (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  molt_id TEXT NOT NULL UNIQUE, -- 'f7a49f667c09f1f6', etc.
  constant_name TEXT NOT NULL,
  status TEXT NOT NULL, -- 'PREDICTION', 'WINDOW_OPEN', 'WINDOW_CLOSED', 'REVERTED'
  predicted_value JSONB,
  current_value JSONB,
  window_starts_at TIMESTAMP,
  window_ends_at TIMESTAMP,
  falsifier_condition TEXT,
  falsifier_tripped BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS websocket_metrics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id TEXT,
  event_type TEXT, -- 'CONNECT', 'DISCONNECT', 'SUBSCRIBE', 'MESSAGE'
  latency_ms INTEGER,
  timestamp TIMESTAMP DEFAULT NOW()
);
```

**Gate:** RQ-UX-03 must pass. Latency <30s, uptime >99.9%, lag <100ms. If any fails, iterate same week.

---

### **Week 4: Freeze + Z2 Ratification**

**Goals:**
- ✅ Code freeze (no new features)
- ✅ Security review + performance audit
- ✅ Z2 manual testing + sign-off
- ✅ All RQs pass falsifiers (or tradeoffs ratified)
- ✅ Ready for production rollout

**Tasks:**

| Day | Task | Owner | Hours | Deliverable |
|:----|:-----|:------|:------|:-----------|
| 1–2 | Security review (input validation, CSRF, XSS, SQL injection) | Z3 | 4 | Security report + fixes |
| 1–2 | Performance audit (bundle size, render time, memory) | Z3 | 3 | Perf report + optimizations |
| 2 | Fix any critical bugs from review | Z3 | 2 | Bug fix commits |
| 2–3 | **Z2 manual testing:** Night uses dashboard end-to-end | Night | 2 | Smoke test report |
| 3 | Integrate findings into REGISTERED.md (F/IC entries) | Z3 + Z1 | 2 | Candidate blocks filed |
| 4 | **Z2 ratification decision:** All RQs pass? Sign Q-COCKPIT-V1-RATIFY-01 | Night | 1 | Hash signature |
| 4 | Merge PR to main, CI green, staging deployed | Z3 | 1 | PR merged + staging live |

**Output:** Cockpit v1.0 staging environment live, Z2 signed off, ready for production Week 5.

**Gate:** All 5 RQs must have passing falsifiers (or tradeoffs explicitly ratified by Z2).

---

### **Week 5: Production Rollout (Optional, Post-Freeze)**

**Goals:**
- ✅ Prepare production environment
- ✅ Gradual rollout (internal only, Week 5; external optional Week 6+)
- ✅ Monitor metrics in production
- ✅ Ongoing maintenance & bug fixes

**Tasks:**
- Prod database setup (audit_log, molt_state, cache tables)
- DNS routing (cockpit.humanaios-ui.com → prod)
- Alerting setup (uptime monitoring, error tracking)
- Runbook for ops team
- gradual rollout to empirica team, then Z2

---

## Tech Stack Details

### Frontend
- **React 18** + TypeScript
- **Tailwind CSS** for styling
- **Socket.io client** for WebSocket
- **TanStack Query** for data fetching + caching
- **Octokit** for GitHub API (REGISTERED.md, PRIORITY_QUEUE.md)
- **date-fns** for time formatting
- **Zod** for schema validation

### Backend
- **Supabase** (managed PostgreSQL)
- **Node.js + Express** (if custom auth/WebSocket needed)
- **Socket.io** for WebSocket server
- **GitHub Actions** for CI/CD

### Database
- PostgreSQL (Supabase)
- Tables: `audit_log`, `molt_state`, `cockpit_cache`, `cockpit_search_index`, `websocket_metrics`

### Deployment
- **Repo:** humanaios-ui/operations
- **Env:** Staging (staging.humanaios-ui.com) + Production (cockpit.humanaios-ui.com)
- **CI/CD:** GitHub Actions (test, build, deploy on main)

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|:-----|:-----------|:-------|:-----------|
| Z2 unavailable for weekly testing | MEDIUM | HIGH | Schedule tests async; 48h window per CLAUDE.md |
| Falsifier thresholds too strict | MEDIUM | MEDIUM | Plan for 1 iteration week if needed; escalate to Z2 |
| WebSocket reliability in Week 3 | MEDIUM | HIGH | Polling fallback; synthetic uptime monitoring |
| GitHub API rate limits | LOW | MEDIUM | Cache aggressively (1-hour TTL); use GitHub app auth |
| Supabase downtime | LOW | HIGH | Plan for graceful degradation; local cache fallback |
| SQL injection in audit queries | LOW | CRITICAL | Use parameterized queries; Zod validation on inputs |

---

## Resource Allocation (RBE-OPS Model)

**Estimated cost vector:**

| Resource | Week 1 | Week 2 | Week 3 | Week 4 | Total |
|:---------|:-------|:-------|:-------|:-------|:------|
| Z1-ktok (proposal) | 2 | 0 | 0 | 2 | **4** |
| Z3-hr (agent build/testing) | 15 | 15 | 15 | 8 | **53** |
| CI-min (test/build/deploy) | 30 | 30 | 30 | 20 | **110** |
| RUN-day (continuous monitoring Week 3) | 0 | 0 | 1 | 0 | **1** |
| Z2-hr (ratification, review) | 3 | 2 | 2 | 4 | **11** |

**Total:** ~4 Z1-ktok + 53 Z3-hr + 110 CI-min + 1 RUN-day + 11 Z2-hr

*(Assumes 1 FTE Z3 builder; adjust if split across team)*

---

## Success Metrics (End of Week 4)

✅ All 5 RQs pass falsifiers (or tradeoffs ratified)  
✅ 0 security findings from review  
✅ Performance: median render <500ms, bundle <500KB  
✅ Uptime in staging: >99.9% over Week 3  
✅ Z2 smoke test: pass all tasks  
✅ CI green: all tests passing  
✅ Findings documented in REGISTERED.md (F/IC entries filed)

---

## Post-Rollout: v1.1 Roadmap (Speculative)

**If falsifiers identify improvements:**
- RQ-Auth-03: Multi-factor authentication (TOTP)
- RQ-UX-04: Keyboard shortcuts + hotkeys
- RQ-UX-05: Dark mode support
- RQ-Perf-01: Pagination for large Findings feeds

*(To be prioritized by Z2 in PRIORITY_QUEUE.md after v1.0 ships)*

---

**Document history:**
- 2026-09-23: Created (Q-COCKPIT-V1-IMPLEMENTATION-01 candidate)
- Pending Z2 ratification
