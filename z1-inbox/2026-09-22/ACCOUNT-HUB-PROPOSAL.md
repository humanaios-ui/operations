# Q-ACCOUNT-HUB-01 — HumanAIOS Account Hub & Project Manager Cockpit

**Z1 Proposal for Z2 Ratification**  
**Proposed by:** Claude Code (Z1)  
**For approval by:** Night (Z2)  
**Date:** 2026-09-22  
**Status:** Awaiting Z2 RATIFY signature

---

## Executive Summary

**What:** Converge all HumanAIOS accounts (16 services) into a unified source-of-truth registry, accessible via the Intent-OS cockpit. Add account metadata, API integrations, cross-service activity feed, and sync status dashboard.

**Why:** Carly manages 16+ accounts across disjoint platforms. No unified view of activity, no automated sync, no audit trail. Account discovery is manual. Credential management is risky. This system moves everything to a canonical registry with Z2-governed access + automated querying.

**Cost:** ~100 hours human labor + 750k AI tokens (6–8 weeks, 4 phases). Phase 1 (source of truth) is 8–12 hours + 100k tokens, completes this week.

**Outcome:** Cockpit becomes a project manager platform. Carly sees all 16 accounts, their status, recent activity, and can delegate account access to AI agents / Z3 executors with Z2 approval.

**Falsifier:** All 16 accounts listed + metadata verified + 11 API-enabled accounts syncing + activity feed live + zero credential breaches.

---

## Problem Statement

### Current State
- **16 accounts** across GitHub, Gmail, Cloudflare, Supabase, Railway, Hugging Face, Substack, LinkedIn, ORCID, arXiv, OSF, IONOS, Hubstaff, Greenlight, RevBy, FreeCodeCamp
- **Two identities:** `carly.r.anderson@gmail.com` (canonical) + `aioshuman@gmail.com` (business)
- **No unified view:** Account status, activity, and credentials scattered across 16 dashboards
- **Manual discovery:** New AI agents can't query account status without asking for a URL + credentials
- **Credential risk:** No centralized audit trail; tokens and passwords managed ad-hoc
- **No project manager:** Intent-OS is a board + decisions + metrics, but not an account hub

### Symptoms
- "Which account has this data?" → search through 16 portals manually
- "Can Claude query this API?" → Carly supplies URL + credentials ad-hoc (insecure)
- "When was the last commit?" → Open GitHub; when was the last paper uploaded? Open arXiv; when was the last payment? Open RevBy
- "Is that token still valid?" → Check password manager; if expired, manually rotate
- "Who accessed what?" → No audit log across all accounts

### Root Cause
Accounts are siloed. No canonical source of truth. No automation. No delegation framework for AI agents.

---

## Proposed Solution

### Three Layers

1. **Registry Layer** (`ACCOUNT_REGISTRY.json`)
   - Single source of truth for all 16 accounts
   - Metadata: service, URL, owner, purpose, access tier, API support, auth type, status
   - Service matrix (by type, by API support, by credential requirement)
   - Audit summary (totals, distributions)

2. **Governance Layer** (`ACCOUNT_REGISTRY_SCHEMA.md`)
   - Authority model (canonical identity, business identity, machine identity, access tiers)
   - Credential strategy (password manager only, never plaintext, access audited)
   - API integration matrix (which services, which phases, rate limits, approval gates)
   - Data classification (public, private, financial, PII)
   - Audit rules + compliance triggers
   - Account lifecycle (active, inactive, dormant, deprecated)

3. **Cockpit Layer** (Intent-OS enhancement)
   - New "Accounts" tab on the board
   - Account cards (name, service, last activity, status)
   - Sync status per account (last synced, next scheduled)
   - Cross-service activity feed (commits, posts, uploads, etc.)
   - Quick stats (repos, datasets, models, projects)
   - Credential expiry alerts
   - "Sync now" button + "View dashboard" link per account

### Key Principles

| Principle | Implementation |
|-----------|-----------------|
| **Single source of truth** | ACCOUNT_REGISTRY.json is canonical; all queries pull from it or update it |
| **Zero credential exposure** | Credentials stored ONLY in password manager; API keys never in git or logs |
| **Audit trail** | Every query logged with requester, scope, rows returned, timestamp |
| **Z2 governed** | Authority model and credential policy ratified by Z2; new accounts require Z2 approval |
| **Delegatable** | AI agents can query public APIs (GitHub repos) without credential; private APIs require credential supply at query time, logged |
| **Failure-safe** | Sync failure → log alert, reduce frequency, notify Z2; never suppress errors |

---

## Phased Roadmap

### Phase 1: Source of Truth (This Week — 8–12 hours)
- [x] Audit all 16 accounts (metadata collection)
- [x] Create ACCOUNT_REGISTRY.json (canonical registry)
- [x] Create ACCOUNT_REGISTRY_SCHEMA.md (governance + API matrix)
- [x] Create Z1 proposal (this document)
- [ ] **Z2 approves** (RATIFY signature)
- [ ] Commit to main branch

**Deliverables:** Registry + Schema + Proposal + Z2 signature  
**AI tokens:** ~100k  
**Human labor:** 2–3 hours (audit, writing)

### Phase 2: Core Integrations (Weeks 2–4 — 30–40 hours)
- [ ] Implement GitHub API queries (repos, commits, PRs, issues)
- [ ] Implement Gmail API queries (labels, thread count, recent senders)
- [ ] Implement Cloudflare API queries (zones, DNS records, domain status)
- [ ] Implement Supabase API queries (tables, storage, function calls)
- [ ] Implement Railway API queries (deployments, services, logs)
- [ ] Implement Hugging Face API queries (models, datasets, spaces)
- [ ] Implement arXiv queries (recent papers, citations)
- [ ] Add "Accounts" tab to Intent-OS cockpit
- [ ] Display account cards with status + sync button
- [ ] Trigger API queries on schedule (every 6 hours for public, every 4 hours for private)

**Deliverables:** 7 API integrations + Cockpit UI  
**AI tokens:** ~250k  
**Human labor:** 30–40 hours (API work, UI development, testing)

### Phase 3: Extended Integrations (Weeks 5–6 — 20–30 hours)
- [ ] Implement Hubstaff API (time tracking, activity)
- [ ] Implement IONOS API (domain + hosting status)
- [ ] Implement OSF API (research projects, files)
- [ ] Implement ORCID API (publication list, profile)
- [ ] Unify activity feed across all 11 API-enabled accounts
- [ ] Add search + filter (by service, date, project)
- [ ] Add credential expiry alerts + rotation reminders

**Deliverables:** 4 more API integrations + Activity feed + Alerts  
**AI tokens:** ~200k  
**Human labor:** 20–30 hours

### Phase 4: Full Project Manager Cockpit (Weeks 7+ — 25–35 hours)
- [ ] Integrate with PRIORITY_QUEUE.md (link accounts to active projects)
- [ ] Integrate with REGISTERED.md (link activities to claims)
- [ ] Auto-generate weekly digest (who did what, where)
- [ ] Export activity reports (CSV, JSON, PDF)
- [ ] Archive historical data (30/90/365-day snapshots)
- [ ] Performance dashboard (API latency, query success rate, sync health)

**Deliverables:** Full project manager integration  
**AI tokens:** ~300k  
**Human labor:** 25–35 hours

---

## Authority & Governance

### Z2 Decision Gate

**Three-part confirmation needed:**

#### 1. Authority ✓
> "All accounts belong to carly.r.anderson@gmail.com (canonical) with aioshuman@gmail.com as business subordinate. Agreed?"
- **Carly confirmed:** ✓ AGREE (2026-09-22)
- **Z2 action:** ACCEPT or EDIT or REJECT

#### 2. Credential Strategy ✓
> "Credentials stored ONLY in password manager. Never plaintext. Every query audited. Agreed?"
- **Carly confirmed:** ✓ AGREE (2026-09-22)
- **Z2 action:** ACCEPT or EDIT or REJECT

#### 3. Privacy Boundary ✓
> "Can query public APIs (GitHub, Supabase read, arXiv, etc.). Cannot scrape private repos, email bodies, financial data. Agreed?"
- **Carly confirmed:** ✓ AGREE (2026-09-22)
- **Z2 action:** ACCEPT or EDIT or REJECT

### Z2 Signature Block

```
IF Z2 approves all three gates:

RATIFY: Q-ACCOUNT-HUB-01 (Account Registry + Schema + Cockpit Enhancement)
Signed by: Night (Z2)
Date: 2026-09-22T<time>Z
Authority: Governance + Credential + Privacy (all three gates: ACCEPT)
Hash: sha256(ACCOUNT_REGISTRY.json | ACCOUNT_REGISTRY_SCHEMA.md | ACCOUNT-HUB-PROPOSAL.md | decision=ACCEPT)
Reversibility: Additive only (new accounts require new Z1 proposal + Z2 RATIFY); removing accounts requires forensic audit
Next action: Commit to main; Z3 executor begins Phase 2 integrations
```

---

## Resource Estimates

| Phase | Human Hours | AI Tokens | Wall-clock | Dependencies |
|-------|-------------|-----------|-----------|--------------|
| 1 | 8–12 | 100k | 1 week | Z2 RATIFY |
| 2 | 30–40 | 250k | 3 weeks | Phase 1 complete |
| 3 | 20–30 | 200k | 2 weeks | Phase 2 complete |
| 4 | 25–35 | 300k | 2–3 weeks | Phase 3 complete |
| **TOTAL** | **~100** | **~750k** | **8–10 weeks** | Phase 0 complete |

**Contingency:** +20% on each phase if discovery issues arise (missing credentials, service auth changes, API deprecations).

---

## Falsifier: Success Criteria

The account hub succeeds when:

1. ✓ All 16 accounts listed in registry with correct, verified metadata
2. ✓ At least 11 API-enabled accounts syncing (Phase 2 integrations live)
3. ✓ Activity feed shows cross-service events unified (commits + posts + uploads, etc., merged chronologically)
4. ✓ Zero credential breaches logged in audit trail (security audit passes)
5. ✓ Cockpit UI displays "Accounts" panel with:
   - Account cards (service, last activity, status)
   - Sync status (last synced, next scheduled)
   - "Sync now" button per account
   - "View dashboard" link per account
6. ✓ Z2 can view account status + adjust sync frequency + revoke access without manual intervention

**Failure scenarios (would trip falsifier and trigger revert):**
- Credential found in plaintext in repo history
- API query succeeds but activity not in feed within 2 hours
- Account marked "active" but hasn't synced in 7+ days
- UI shows data older than current sync timestamp (stale display)
- Query fails silently (no log, no alert)

---

## Anti-Cascade & Revert Rules

### If Phase Fails

1. **Phase 2 fails:** Revert to Phase 1 registry only (no integrations); keep cockpit card display placeholder ("Sync not yet available")
2. **Phase 3 fails:** Keep Phase 2 integrations; skip extended services (Hubstaff, IONOS, etc.) until next cycle
3. **Phase 4 fails:** Keep UI functional; skip PRIORITY_QUEUE + REGISTERED integration; full cockpit available in next cycle

### If Credential Breach Occurs

1. Immediate token rotation (all affected services)
2. Audit report (what was accessed, when, by whom)
3. Z2 notification + escalation
4. Sync disabled until credential remediated
5. Post-mortem + prevention plan filed as `mistake-log` entry

---

## Next Actions

### Immediate (Today)
- [ ] Z2 (Night) reviews three gates (authority, credential, privacy)
- [ ] Z2 approves or edits or rejects
- [ ] Z1 (Claude) updates proposal based on Z2 feedback

### If Z2 Approves
- [ ] Commit Phase 1 files to main branch (with Z2 signature)
- [ ] Create Phase 2 epic in PRIORITY_QUEUE.md
- [ ] Z3 executor assigned to Phase 2 integration work
- [ ] Begin Week 2 integrations (GitHub, Gmail, Cloudflare, Supabase, Railway, Hugging Face, arXiv)

### If Z2 Rejects or Requests Edits
- [ ] Z1 addresses feedback
- [ ] Re-propose in next transaction

---

## References

- **Registry:** `operations/data/ACCOUNT_REGISTRY.json` (16 accounts, metadata, service matrix)
- **Schema:** `operations/data/ACCOUNT_REGISTRY_SCHEMA.md` (authority, credentials, API matrix, compliance)
- **Authority:** `CLAUDE.md` § Authority Structure (Z1/Z2/Z3, decision routing)
- **Governance:** `ZONE_REGISTRY.md` (active repos), `REGISTERED.md` (ratified claims)
- **UI:** `ui/intent-os-humanaios-v3_3.html` (existing cockpit; Phase 2 adds Accounts tab)

---

## Appendix: Account Categories

### By Access Tier
- **Full:** 16 accounts (all owned by Carly)
- **Limited:** 0 (none delegated yet)
- **Read-only:** 0 (will add when AI agents query public APIs)

### By Service Type
| Type | Count | Examples |
|------|-------|----------|
| VCS | 1 | GitHub |
| Email | 1 | Gmail |
| Hosting | 3 | Cloudflare, Railway, IONOS |
| Database | 1 | Supabase |
| AI Platform | 2 | Hugging Face, Greenlight |
| Analytics | 1 | Hubstaff |
| Content | 1 | Substack |
| Social | 1 | LinkedIn |
| Education | 1 | FreeCodeCamp |
| Research | 2 | OSF, arXiv |
| Academic | 1 | ORCID |
| Payment | 1 | RevBy |

### By API Support
- **API available:** 11 accounts (GitHub, Gmail, Cloudflare, Hugging Face, Hubstaff, Supabase, Railway, IONOS, OSF, arXiv, ORCID)
- **No API:** 5 accounts (Substack, Greenlight, LinkedIn, FreeCodeCamp, RevBy)

### By Credential Requirement
- **Requires credential:** 8 accounts (GitHub, Gmail, Cloudflare, Hubstaff, Supabase, Railway, IONOS, RevBy)
- **Public access:** 8 accounts (Hugging Face, Substack, Greenlight, LinkedIn, FreeCodeCamp, OSF, arXiv, ORCID)

---

**Authored by:** Claude Code (Z1 Proposer)  
**Awaiting signature by:** Night (Z2 Ratifier)  
**Date created:** 2026-09-22  
**Status:** PENDING Z2 RATIFY
