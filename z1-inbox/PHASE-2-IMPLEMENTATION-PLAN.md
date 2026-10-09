# Phase 2: Account Hub API Integrations & Cockpit Enhancement

**Status:** PREFLIGHT → CHECK → Execution  
**Timeline:** 3 weeks (30-40 hours, ~250k tokens)  
**Z2 Authority:** Night (Ratified via Q-ACCOUNT-HUB-01)  
**Z1 Proposer:** Claude  
**Z3 Executor:** (TBD)  

---

## Work Breakdown Structure

### Track A: API Integrations (Parallel)

Each integration follows the same template:
1. Read API docs + verify auth method from ACCOUNT_REGISTRY.json
2. Build API client class (with credential supply at query time)
3. Implement query methods (list repos, commits, etc.)
4. Add to sync scheduler
5. Test + verify output format
6. Integrate into activity feed

| Integration | API Endpoints | Auth | Complexity | Status |
|-------------|---------------|------|-----------|--------|
| GitHub | 5 (repos, commits, PRs, issues, branches) | PAT | Medium | Ready |
| Gmail | 3 (profile, messages, labels) | OAuth | High | Ready |
| Cloudflare | 3 (zones, DNS, analytics) | API token | Medium | Ready |
| Supabase | 3 (tables, storage, functions) | Service role | High | Ready |
| Railway | 3 (projects, deployments, logs) | API token | Medium | Ready |
| Hugging Face | 3 (models, datasets, spaces) | API token | Low | Ready |
| arXiv | 1 (search) | None (public) | Low | Ready |

**Parallel execution:** Group 1 (GitHub, Gmail, Cloudflare) + Group 2 (Supabase, Railway, Hugging Face, arXiv)

### Track B: Cockpit UI Enhancement (Sequential, starts after UI template)

1. Create `ui/intent-os-accounts-extension.js` (tab switcher + state management)
2. Create `ui/accounts-panel.html` (account cards, sync status, actions)
3. Create `ui/activity-feed.html` (unified timeline component)
4. Integrate into `intent-os-humanaios-v3_3.html` (new "Accounts" tab)
5. Add "Sync now" button + "View dashboard" links
6. Add credential expiry alerts
7. Test responsive design + performance

### Track C: Activity Feed Unification

1. Define event schema (timestamp, service, event_type, data)
2. Normalize each service's events to schema
3. Merge all events chronologically
4. Implement search + filter (by service, date, type)
5. Cache strategy (in-memory + localStorage for offline)

### Track D: Sync Scheduler & Health Monitoring

1. Create sync scheduler (cron-like, configurable per service)
2. Implement retry logic (exponential backoff on failure)
3. Log all queries to audit trail (who, what, when, result)
4. Health dashboard (last sync, next scheduled, error count)
5. Alerts on sync failure + rate limit hit

---

## File Structure (New)

```
operations/
├── integrations/                          (NEW)
│   ├── __init__.py
│   ├── base.py                           (Abstract API client)
│   ├── github.py                         (GitHub integration)
│   ├── gmail.py                          (Gmail integration)
│   ├── cloudflare.py                     (Cloudflare integration)
│   ├── supabase.py                       (Supabase integration)
│   ├── railway.py                        (Railway integration)
│   ├── huggingface.py                    (Hugging Face integration)
│   ├── arxiv.py                          (arXiv integration)
│   └── schemas.py                        (Event + response schemas)
├── services/                              (NEW)
│   ├── __init__.py
│   ├── sync_scheduler.py                 (Cron scheduler for all integrations)
│   ├── activity_feed.py                  (Unification + normalization)
│   ├── credential_supplier.py            (Query-time credential handoff)
│   └── audit_logger.py                   (Query audit trail)
├── ui/
│   ├── intent-os-accounts-extension.js   (NEW - state management)
│   ├── accounts-panel.html               (NEW - account cards)
│   ├── activity-feed.html                (NEW - unified timeline)
│   └── intent-os-humanaios-v3_3.html    (MODIFIED - add Accounts tab)
└── data/
    └── ACCOUNT_REGISTRY.json             (already exists)
```

---

## Implementation Sequence

### Week 1: Infrastructure + First 2 Integrations

**Days 1–2:** Infrastructure (4–6 hours)
- [ ] Create base API client class (`integrations/base.py`)
- [ ] Implement credential supplier (`services/credential_supplier.py`)
- [ ] Create event schema + activity feed (`services/activity_feed.py`)
- [ ] Set up sync scheduler skeleton (`services/sync_scheduler.py`)

**Days 3–4:** GitHub Integration (6–8 hours)
- [ ] Implement GitHub API client (repos, commits, PRs, issues)
- [ ] Add credential supply at query time
- [ ] Test queries + verify response format
- [ ] Add to sync scheduler

**Days 5–7:** Gmail Integration (8–10 hours)
- [ ] Implement Gmail API client (profile, messages, labels)
- [ ] Handle OAuth credential flow
- [ ] Implement rate limiting (Gmail has strict limits)
- [ ] Test queries + verify response format
- [ ] Add to sync scheduler

**Deliverable:** GitHub + Gmail syncing, activity feed receiving events

### Week 2: More Integrations + UI Skeleton

**Days 8–10:** Cloudflare + Supabase (8–10 hours)
- [ ] Cloudflare API client (zones, DNS, analytics)
- [ ] Supabase API client (tables, storage, functions)
- [ ] Test queries + add to scheduler

**Days 11–12:** Railway + Hugging Face (6–8 hours)
- [ ] Railway API client (projects, deployments, logs)
- [ ] Hugging Face API client (models, datasets, spaces)
- [ ] Test queries + add to scheduler

**Days 13–14:** Cockpit UI Skeleton (6–8 hours)
- [ ] Create account cards component
- [ ] Create sync status display
- [ ] Create activity feed display (static mockup)
- [ ] Add to Intent-OS as new tab

**Deliverable:** 5 integrations syncing + Cockpit UI skeleton live

### Week 3: Final Integration + Polish

**Days 15–16:** arXiv Integration + Activity Feed Unification (6–8 hours)
- [ ] arXiv API client (search, papers)
- [ ] Unify activity feed (normalize events from all 7 services)
- [ ] Implement search + filter
- [ ] Test end-to-end

**Days 17–19:** UI Polish + Health Monitoring (8–10 hours)
- [ ] Add "Sync now" button (trigger manual refresh)
- [ ] Add "View dashboard" links
- [ ] Add credential expiry alerts
- [ ] Implement health dashboard (last sync, errors, next scheduled)
- [ ] Test responsive design

**Days 20–21:** Testing + Verification (6–8 hours)
- [ ] Integration tests (each API client)
- [ ] End-to-end test (full sync cycle)
- [ ] Security audit (no credential leaks in logs)
- [ ] Performance test (sync time, memory usage, UI responsiveness)

**Deliverable:** All 7 integrations live + Cockpit UI complete + activity feed unified

---

## API Integration Template

Every integration follows this pattern:

```python
# integrations/service_name.py

from integrations.base import BaseAPIClient
from integrations.schemas import Event

class ServiceNameClient(BaseAPIClient):
    """Query service_name API for account activity."""
    
    SERVICE = "service_name"
    AUTH_TYPE = "api_key" | "oauth" | "pat" | "none"
    API_ENDPOINTS = ["...", "..."]
    RATE_LIMIT = "X requests per Y"
    
    def get_credential(self):
        """Query password manager for credential (at query time, never store)."""
        return credential_supplier.get(self.SERVICE)
    
    def query_resource(self, resource_type, **kwargs) -> List[Event]:
        """Query API and return normalized Event objects."""
        cred = self.get_credential()
        # Make API call
        response = self._api_call(resource_type, cred, **kwargs)
        # Normalize to Event schema
        events = [Event(
            timestamp=...,
            service=self.SERVICE,
            event_type=resource_type,
            data={...}
        ) for item in response]
        return events
    
    def health_check(self) -> bool:
        """Verify API access works."""
        try:
            self.query_resource("health")
            return True
        except Exception as e:
            logger.error(f"{self.SERVICE} health check failed: {e}")
            return False
```

---

## Falsifier: Phase 2 Success

Phase 2 succeeds when:

1. ✓ All 7 API integrations syncing + queries working
2. ✓ Activity feed shows events from all 7 services (merged chronologically)
3. ✓ Cockpit UI displays "Accounts" tab with:
   - Account cards (service, status, last activity)
   - "Sync now" button per account
   - "View dashboard" link per account
   - Credential expiry alerts
4. ✓ Sync health dashboard shows:
   - Last sync time per service
   - Next scheduled sync
   - Error count + last error message
5. ✓ Zero credential leaks in logs (audit trail review passes)
6. ✓ Performance: sync cycle completes in <30 seconds, UI responsive (<100ms interaction lag)

**Failure scenarios (would trigger revert to Phase 1 UI only):**
- Any integration fails more than 3 consecutive times
- Credential found in logs or error messages
- Activity feed shows stale data (older than current sync timestamp)
- Cockpit UI crashes or becomes unresponsive

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| API deprecation | Low | High | Start with stable services (GitHub, Supabase); monitor docs |
| Auth edge case (e.g., OAuth token expired) | Medium | Medium | Implement retry logic + credential refresh |
| Rate limit hit | Medium | Low | Implement exponential backoff + quota tracking |
| Credential leak in error message | Low | Critical | Log sanitization + automated audit check |
| Performance (sync takes >1 min) | Low | Medium | Implement caching + lazy loading |
| UI regression (breaks existing board) | Low | High | Test in isolation before integration |

---

## References

- **Registry:** `data/ACCOUNT_REGISTRY.json` (account metadata + API endpoints)
- **Schema:** `data/ACCOUNT_REGISTRY_SCHEMA.md` (governance + auth types)
- **UI Mockup:** `ui/intent-os-accounts-panel-mockup.html` (design reference)
- **Cockpit:** `ui/intent-os-humanaios-v3_3.html` (existing board to extend)

---

## Dependencies & Blockers

**Required before Phase 2 execution:**
- ✓ ACCOUNT_REGISTRY.json (provides account metadata + endpoints)
- ✓ Z2 RATIFY (provides authority to access credentials + audit logs)
- ? Z3 executor assignment (who implements + maintains)
- ? Credential supplier availability (password manager API or OAuth flow)

**Blockers (currently none; all "ready" status)**

---

## Next Steps

1. **CHECK gate:** Verify above four claims before proceeding
2. **Z3 assignment:** Who will execute Phase 2?
3. **Week 1 kickoff:** Begin infrastructure + GitHub/Gmail integrations
4. **Weekly sync:** Review progress, blockers, any API changes

---

**Authored by:** Claude (Z1)  
**Awaiting:** CHECK gate + Z3 assignment  
**Status:** Ready to execute
