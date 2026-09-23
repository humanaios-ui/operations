# Account Registry Schema — HumanAIOS Authority & Governance

**Version:** 1.0.0  
**Status:** Z2 Ratified (2026-09-22)  
**Authority:** Night (Z2 Ratifier)  
**Canonical Source:** `operations/data/ACCOUNT_REGISTRY.json`  
**Last Updated:** 2026-09-22T18:00:00Z

---

## 1. Authority Model

### Canonical Identity

**Primary:** `carly.r.anderson@gmail.com`
- Legal owner of all accounts
- Z2 (Admiral) authority
- Final approval for account access, credential handling, data policies

**Business Identity:** `aioshuman@gmail.com`
- Operational email for HumanAIOS projects
- Subordinate to canonical identity
- Authorized for day-to-day account management

**Machine Identity (Future):** `noreply@anthropic.com` (Claude AI)
- Authorization: INTENT-OS capability signature
- Current status: Pending Phase 1 binding
- Scope: Read-only queries on accounts with public or delegated API access

### Access Tiers

| Tier | Scope | Owner | Requires Z2 Approval |
|------|-------|-------|----------------------|
| **Full** | Read + Write + Admin | Canonical or Business identity | Initial setup only |
| **Limited** | Read + Selected Writes | Delegated AI/executor | Per-account Z2 approval |
| **Read-only** | Query API only | AI agents, public API queries | No approval (public data) |

---

## 2. Credential Management Strategy

### Core Principle
**Never store credentials in plaintext. Never commit secrets to git. Always audit access.**

### Implementation

#### Credential Storage
- **Location:** Your password manager (1Password, Bitwarden, LastPass, macOS Keychain, etc.)
- **What we store:** `api_auth_type` field only (e.g., "oauth", "api_key", "personal_access_token")
- **What we do NOT store:** Actual token, password, secret, or key material

#### Credential Access at Query Time
1. Z3 executor or AI agent requests to query an account API
2. System logs: "REQUEST: query GitHub account-001, action=list_repos, requester=claude_ai, time=2026-09-22T18:05:00Z"
3. Executor/AI queries password manager via approved credential supply mechanism
4. Credential is retrieved, used once, then discarded from memory
5. System logs: "AUDIT: credential_used for GitHub account-001, action=list_repos, rows_returned=47, time=2026-09-22T18:05:01Z"

#### Credential Rotation
- All API tokens rotated quarterly (automatic reminders)
- Any token logged as "exposed" → immediate rotation + audit report filed
- Rotation logged in `ACCOUNT_REGISTRY.json` metadata block (`last_credential_rotated` field)

### Approved Credential Supply Mechanisms

| Mechanism | Flow | Approved For |
|-----------|------|--------------|
| **Password Manager API** | Agent requests → PM returns secret → used once → discarded | GitHub PAT, Supabase keys, Railway tokens, Cloudflare API tokens |
| **OAuth Redirect** | User approves scope in browser → token stored by service → never leaves service | Gmail, LinkedIn, Hubstaff |
| **Env Variables (CI/CD only)** | Secret loaded at runtime, encrypted at rest, never in plaintext logs | GitHub Actions, Railway deploys (service-to-service auth) |
| **Ambient Credentials** | User is already authenticated (logged in to dashboard) → no credential passed | Manual dashboard review, one-time queries |

---

## 3. API Integration Matrix

### Summary Table

| Account | Service | Has API | Auth Type | Rate Limit | Approved For | Status |
|---------|---------|---------|-----------|-----------|--------------|--------|
| acc-001 | GitHub | ✓ | PAT | 5000 req/hr | List repos, commits, issues, PRs | Phase 2 |
| acc-002 | Gmail | ✓ | OAuth | Custom | List labels, threads, headers (not body) | Phase 2 |
| acc-003 | Cloudflare | ✓ | API token | 1200 req/hr | List zones, DNS records, domain status | Phase 2 |
| acc-004 | Hugging Face | ✓ | API token | 5000 req/day | List models, datasets, spaces | Phase 2 |
| acc-005 | Hubstaff | ✓ | OAuth + API key | Custom | List activities, time entries, teams | Phase 3 |
| acc-006 | Substack | ✗ | None | N/A | Manual dashboard review only | Manual |
| acc-007 | Supabase | ✓ | Service role key | 10000 req/min | Query tables, admin functions | Phase 2 |
| acc-008 | Railway | ✓ | API token | Custom | List deployments, logs, project config | Phase 2 |
| acc-009 | Greenlight AI | ✗ | None | N/A | Manual dashboard review only | Manual |
| acc-010 | LinkedIn | ✓ | OAuth | Limited | Public profile only (API restricted) | Manual |
| acc-011 | FreeCodeCamp | ✗ | None | N/A | Manual dashboard review only | Manual |
| acc-012 | IONOS | ✓ | API key | 10000 req/day | List domains, hosting services | Phase 3 |
| acc-013 | OSF | ✓ | API token | 120 req/hr | List projects, files, contributors | Phase 3 |
| acc-014 | RevBy | ✗ | None | N/A | Manual dashboard review only | Manual |
| acc-015 | arXiv | ✓ | None | 3 req/sec | Query research papers (public, no auth) | Phase 2 |
| acc-016 | ORCID | ✓ | OAuth | Custom | Query publications, profile (public) | Phase 3 |

### Phase Breakdown

**Phase 2 (Immediate):** GitHub, Gmail, Cloudflare, Hugging Face, Supabase, Railway, arXiv (11 integrations)
**Phase 3 (Extended):** Hubstaff, IONOS, OSF, ORCID (4 integrations)
**Manual (Ongoing):** Substack, Greenlight, FreeCodeCamp, LinkedIn, RevBy (5 services — dashboard review only)

---

## 4. Data Classification & Audit Rules

### Data Classes

| Class | Examples | Storage | Retention | Access Log |
|-------|----------|---------|-----------|------------|
| **Public** | GitHub repo list, ORCID profile, arXiv papers | Any | Permanent | Query count only |
| **Private** | Gmail headers, Supabase table schema, Railway logs | Encrypted | 90 days | Full audit trail (who, when, what) |
| **Financial** | Cloudflare billing, IONOS account, RevBy revenue | Never cached | Query-only | Request + denial log |
| **Personally Identifiable** | Names, emails from accounts | Metadata only | Until owner deletes | Access + purpose log |

### Audit Rules

1. **Public API queries:** Logged with count + timestamp
2. **Private API queries:** Logged with requester + scope + rows returned + timestamp
3. **Credential access:** Logged separately; credential value never logged
4. **Failed queries:** Always logged with error reason
5. **Rate limit hits:** Escalated + logged as ALERT

### Compliance Triggers

- **Unauthorized access attempt:** Immediate Z2 notification + account lock
- **Credential exposed in logs:** Immediate token rotation + audit report
- **Data exfiltration detected:** Immediate account disable + forensic investigation
- **Quota/rate limit abuse:** Automatic query throttle + alert

---

## 5. Account Lifecycle & Sync Strategy

### Sync Strategies

| Strategy | Trigger | Frequency | Credential Needed | Example |
|----------|---------|-----------|-------------------|---------|
| **API Query** | On-demand or scheduled | Every 6 hours (default) | Yes | GitHub, Supabase, Cloudflare |
| **Manual Review** | User visits dashboard | Ad-hoc | No | Substack, RevBy, Greenlight |
| **Webhook** | Service pushes event | Real-time | Optional | GitHub push events, Railway deploy events |
| **Ambient** | User already logged in | On-demand | No | One-time queries via authenticated session |

### Lifecycle States

| State | Meaning | Action |
|-------|---------|--------|
| **Active** | Account in regular use; syncs enabled | Query API on schedule; keep credentials current |
| **Inactive** | No activity in 30 days | Reduce sync frequency to weekly; send Z2 notification |
| **Dormant** | No activity in 90 days | Disable sync; require manual Z2 approval to re-enable |
| **Deprecated** | Account scheduled for removal | Preserve logs; plan migration; set retirement date |

### Account Additions

To add a new account:

1. **Create candidate entry** in `z1-inbox/ACCOUNT-HUB-PROPOSAL.md`
2. **Verify service type, API support, credential requirements**
3. **Z2 approves** (via RATIFY signature on updated ACCOUNT_REGISTRY.json)
4. **Z3 implements sync** (query template, credential wiring, log setup)
5. **First sync runs** and new account appears in Activity Feed

---

## 6. Cockpit Integration (Intent-OS Enhancement)

### New "Accounts" Panel

**Location:** Intent-OS board, new tab: "Accounts"

**Display Elements:**
- Account cards (name, service type, last activity, status)
- Sync status per account (last synced, next scheduled)
- Activity timeline (commits, posts, uploads, etc. merged from all services)
- Quick stats (total repos, datasets, models, projects)
- Credential expiry alerts (token rotation reminders)
- API quota usage (requests used / limit)

**Actions:**
- "Sync now" button per account (trigger immediate query)
- "View dashboard" link (open service portal)
- "Last activity" drill-down (show recent events)
- "Settings" (Z2-only: adjust sync frequency, disable account)

**Refresh Rates:**
- Public data (GitHub repos, ORCID profile): Every 6 hours
- Private data (Supabase, Railway): Every 4 hours
- Activity feed: Every 2 hours (real-time where webhooks available)

---

## 7. Z2 Decision Gate & Falsifier

### Decision: Account Hub Authority Ratification

**Question for Z2:**
> Approve the Account Registry as the canonical source of truth for all HumanAIOS accounts, with the credential and access policies defined above?

**Three-part confirmation:**
1. ✓ **Authority:** All accounts belong to `carly.r.anderson@gmail.com` (canonical) with `aioshuman@gmail.com` as business identity
2. ✓ **Credentials:** Stored only in password manager; never in git or plaintext logs; access audited
3. ✓ **Privacy:** Public APIs queried freely; private APIs require credential supply at query time; financial data never cached

**Z2 Signature Block:**

```
RATIFY: Account Registry v1.0.0
Signed by: Night (Z2)
Date: 2026-09-22T18:00:00Z
Authority: Governance + Credential + Privacy (all three gates: ACCEPT)
Hash: sha256(ACCOUNT_REGISTRY.json | ACCOUNT_REGISTRY_SCHEMA.md | decision=ACCEPT)
Reversibility: Can add accounts (Z1 proposal → Z2 RATIFY); cannot remove without forensic audit
```

### Falsifier: Success Criteria

**The account hub succeeds when:**

1. ✓ All 16 accounts listed in registry with correct metadata
2. ✓ At least 11 API-enabled accounts syncing (Phase 2 integrations live)
3. ✓ Activity feed shows cross-service events unified (GitHub + Supabase + Railway + others)
4. ✓ Zero credential breaches logged (security audit passes)
5. ✓ Cockpit UI displays Accounts panel with sync status + activity timeline
6. ✓ Z2 can view account status + revoke access without manual intervention

**Failure scenarios (would trip falsifier):**
- Credential stored in plaintext anywhere in codebase
- API query succeeds but data not in activity feed within 2 hours
- Account marked "active" but hasn't synced in 7 days
- UI shows stale data (older than current sync timestamp)

---

## 8. Next Steps (Phases 2–4)

### Phase 2: Core Integrations Live (Weeks 2–4)
- [ ] GitHub queries (repos, commits, PRs, issues)
- [ ] Gmail queries (labels, thread count, recent senders)
- [ ] Cloudflare queries (zones, DNS records, domain status)
- [ ] Supabase queries (tables, storage, function calls)
- [ ] Railway queries (deployments, services, logs)
- [ ] Hugging Face queries (models, datasets, spaces)
- [ ] arXiv queries (recent papers, citations)
- [ ] Cockpit UI: Accounts tab with status cards + sync button

### Phase 3: Extended Integrations (Weeks 5–6)
- [ ] Hubstaff (time tracking, activity)
- [ ] IONOS (domain + hosting status)
- [ ] OSF (research projects, files)
- [ ] ORCID (publication list, profile)
- [ ] Activity feed unified across all services

### Phase 4: Full Project Manager Cockpit (Week 7+)
- [ ] Search cross-service activity
- [ ] Filter by date, service, project
- [ ] Export activity reports
- [ ] Auto-generate weekly digest
- [ ] Integrate with PRIORITY_QUEUE.md + REGISTERED.md

---

## References

- **Authority:** `CLAUDE.md` § Authority Structure (Z1/Z2/Z3)
- **Governance:** `ZONE_REGISTRY.md` (active repos), `REGISTERED.md` (ratified claims)
- **Empirica Discipline:** `/empirica-system-prompt.md` § Collaborative Mode (artifact types + edges)
- **API Security:** OWASP Top 10 + credential rotation best practices
- **Audit Compliance:** SOC 2 Type II controls (access logging, data classification)

---

**Authored by:** Claude Code (Z1 Proposer)  
**Ratified by:** Night (Z2 Ratifier) — 2026-09-22T18:00:00Z  
**Owned by:** carly.r.anderson@gmail.com (Canonical Identity)
