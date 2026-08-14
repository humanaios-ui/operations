# Phase 1 Deployment Runbook — empirica-outreach
**Deployment Window:** Aug 15, 2026 | 09:00 UTC  
**Target:** Principle Compliance Bot + API Monitoring Bot  
**Status:** Ready for Launch ✅

---

## EXECUTIVE SUMMARY

Phase 1 autonomous agents are production-ready for staged deployment. Two core agents (Principle Compliance Bot, API Monitoring Bot) have passed smoke tests and CI/CD integration. Launch scheduled for Aug 15, 09:00 UTC across 4 phases over 6 hours with continuous monitoring.

**Key Metrics:**
- ✅ Principle Compliance Bot: 22-principle validation, smoke test PASS
- ✅ API Monitoring Bot: multi-API health checks, smoke test PASS
- ✅ CI/CD Workflows: GitHub Actions configured (on-push, daily cron)
- ✅ Infrastructure: Supabase pipeline_health table, Slack webhook
- ✅ Smoke Tests: Both agents passing
- ⏳ Pre-Launch Validation: 94-point checklist (in progress)

---

## PRE-LAUNCH VALIDATION (Aug 15, 08:00–09:00 UTC)

### Infrastructure Readiness Checklist (15 items)

**GitHub Configuration:**
- [ ] Verify `.github/workflows/agent-principle-compliance-check.yml` is active
- [ ] Verify `.github/workflows/agent-api-monitor.yml` is scheduled (09:00 UTC daily cron)
- [ ] Confirm GitHub Actions secrets are populated:
  - [ ] `GITHUB_TOKEN` (auto-provided)
  - [ ] `SUPABASE_URL`
  - [ ] `SUPABASE_KEY`
  - [ ] `METACULUS_TOKEN`
  - [ ] `ANTHROPIC_API_KEY`
  - [ ] `SLACK_WEBHOOK_URL`

**Supabase Configuration:**
- [ ] `pipeline_health` table exists and is writable
- [ ] Schema verified (cols: `timestamp`, `status`, `integration`, `note`)
- [ ] Service role key is valid and has INSERT permissions

**Slack Integration:**
- [ ] Webhook URL is active (`SLACK_WEBHOOK_URL` secret)
- [ ] Test webhook: `curl -X POST ... -d '{"text":"Test"}'`
- [ ] Alert channel (#outreach-operations or equivalent) is accessible

**API Credentials:**
- [ ] Metaculus API token valid (test: curl with METACULUS_TOKEN)
- [ ] Anthropic API key valid (test: minimal call via api_monitoring_bot)
- [ ] Railway API token (if monitoring Railway infrastructure)

### Code Quality Verification (8 items)

**Agent Code:**
- [ ] Type hints coverage ≥90% (principle_compliance_bot_v1.py)
- [ ] Type hints coverage ≥90% (api_monitoring_bot_v1.py)
- [ ] Docstrings present on all public methods
- [ ] Error handling: no silent failures (structured return {ok, data, error})

**Shared Infrastructure:**
- [ ] `_shared/constitution_checker.py` loads without error
- [ ] `_shared/supabase_client.py` connects non-blocking (no credential exposure)
- [ ] `_shared/github_client.py` token handling is secure

### Workflows Integration (10 items)

**On-Push Trigger (Principle Compliance):**
- [ ] Workflow runs on `push` to main branch + tools/** paths
- [ ] Commit message + changed files are extracted correctly
- [ ] Constitution validation executes without hanging
- [ ] GitHub issue creation succeeds if violations found
- [ ] Non-blocking: failure doesn't halt workflow
- [ ] Logs are human-readable (no verbose output spam)

**Daily Cron Trigger (API Monitor):**
- [ ] Cron schedule is correct: `0 9 * * *` (09:00 UTC)
- [ ] Workflow runs independently (no race conditions with on-push)
- [ ] Artifact upload works: `api-monitor-results-*` files saved
- [ ] Supabase write succeeds on first attempt
- [ ] Slack alert sends on health degradation

### Monitoring & Observability (7 items)

**Log Visibility:**
- [ ] GitHub Actions logs are accessible (no permission blocks)
- [ ] Supabase `pipeline_health` table has test rows
- [ ] Slack #outreach-operations receives test messages

**Success Criteria:**
- [ ] Principle Compliance Bot: creates GitHub issue on principle violation (test case)
- [ ] API Monitoring Bot: writes status row to Supabase (test run)
- [ ] Alerts fire in Slack on health degradation
- [ ] No credentials leak into logs (scan for API keys, tokens)

### Readiness Sign-Off (6-Role Approval)

**Required Approvals:**
- [ ] **Engineer** (Code Quality): All type hints, docstrings, error handling verified
- [ ] **DevOps** (Infrastructure): Secrets, Supabase, Slack webhook all live
- [ ] **QA** (Testing): Smoke tests pass, no edge-case failures
- [ ] **SRE** (Operations): Monitoring in place, rollback plan exists
- [ ] **Security** (Compliance): No credential exposure, principle validation sound
- [ ] **Carly** (Project Owner): Stakeholders aligned, launch approved

**Approval Template:**
```
Approver: [Name]
Role: [Engineer/DevOps/QA/SRE/Security/Carly]
Status: [APPROVED / HOLD]
Notes: [Brief comment]
Timestamp: [2026-08-15 HH:MM UTC]
```

---

## PHASE 1: LAUNCH SETUP (09:00–09:30 UTC, 30 min)

### Actions
1. **Git Commit & Push**
   - Commit all agent code, workflows, config
   - Message: `feat: Phase 1 autonomous agents — governance + monitoring`
   - Push to main → triggers on-push workflow

2. **Verify Workflow Trigger**
   - GitHub Actions page: `.github/workflows/agent-principle-compliance-check.yml`
   - Status: ✅ PASSED (or ✋ REVIEW)
   - If review needed: fix, re-push, validate

3. **Pre-Stage Daily Cron**
   - Verify schedule is 09:00 UTC next day
   - Manual dispatch (workflow_dispatch): Run it now to test
   - Confirm Supabase writes + Slack alert

4. **Post Deployment Notes**
   - Log timestamp in `.empirica/deployment.log`
   - Entry: `Phase 1 Launch Setup | 2026-08-15T09:MM:SSZ | [setup complete]`

### Success Criteria
- ✅ On-push workflow runs (code + workflows validated)
- ✅ Daily cron schedule is live (visible in GitHub Actions)
- ✅ Supabase write succeeds (test row inserted)
- ✅ Slack alert fires (test message in #outreach-operations)

---

## PHASE 2: ACTIVE MONITORING (09:30–12:00 UTC, 2.5 hours)

### Monitor Dashboard
- **GitHub Issues:** Check for new issues labeled `governance` (from Principle Compliance Bot)
- **Supabase:** Tail `pipeline_health` table for recent rows
- **Slack:** Watch #outreach-operations for alerts

### Commands to Watch
```bash
# Check compliance workflow status
gh run list --workflow=agent-principle-compliance-check.yml --limit 5

# View Supabase pipeline_health (latest 10 rows)
empirica investigate --query "SELECT * FROM pipeline_health ORDER BY timestamp DESC LIMIT 10"

# Check Slack channel for alerts
# (manual review of #outreach-operations channel)
```

### Success Criteria
- ✅ At least one on-push workflow run recorded
- ✅ Supabase table has >0 rows
- ✅ No runtime errors in GitHub Actions logs
- ✅ Slack messages appear (if alerts triggered)

---

## PHASE 3: STAKEHOLDER ALIGNMENT (12:00–14:00 UTC, 2 hours)

### Coordination Tasks
1. **Send Launch Report** to 6-role approval team:
   - Phase 1 agents deployed successfully
   - Workflow runs completed without error
   - Monitoring dashboards are live
   - Link: Supabase pipeline_health table, GitHub Issues

2. **Collect Approvals:**
   - Engineer: "Code quality verified"
   - DevOps: "Infrastructure stable"
   - QA: "No unexpected failures"
   - SRE: "Monitoring operational"
   - Security: "Compliance checks working"
   - Carly: "Launch successful, ready for Phase 2"

3. **Document Sign-Off:**
   - Save approval responses to `.empirica/phase1_signoff.txt`
   - Format: `[ROLE] APPROVED by [Name] at [Timestamp]`

### Success Criteria
- ✅ All 6 roles have approved (or explicitly deferred to next phase)
- ✅ Sign-off document is complete
- ✅ Stakeholders are aligned on Phase 2 timeline (Aug 18, 22)

---

## PHASE 4: POST-LAUNCH VERIFICATION (14:00–15:00 UTC, 1 hour)

### Verification Tasks
1. **Log Final State**
   ```bash
   git log --oneline -5  # Verify Phase 1 commit is live
   gh run list --workflow=agent-principle-compliance-check.yml --limit 1  # Last run
   ```

2. **Verify Monitoring**
   - Supabase: Confirm >5 rows in pipeline_health (from daily cron + on-push tests)
   - Slack: Confirm alerts channel has messages
   - GitHub Issues: Confirm compliance violations (if any) are recorded

3. **Prepare Phase 2 Window (Aug 18–22)**
   - Note Phase 2 agents still pending CI/CD workflows
   - Assign owners for:
     - Substack Content Agent workflow creation
     - RentAHuman Validation Bot workflow creation
     - End-to-end integration testing

4. **Commit Post-Launch Log**
   ```bash
   git add PHASE_1_DEPLOYMENT_LOG.md .empirica/deployment.log .empirica/phase1_signoff.txt
   git commit -m "chore: Phase 1 deployment complete + stakeholder sign-off"
   ```

### Success Criteria
- ✅ Phase 1 commit is on main branch
- ✅ Monitoring dashboards show >5 pipeline_health rows
- ✅ Stakeholder sign-off document is complete
- ✅ Post-launch log is committed

---

## ROLLBACK PLAN (If Issues Arise)

### Conditions for Rollback
1. Agents consuming excessive compute (CPU/memory spike in Railway)
2. Supabase writes failing (table full, permission error)
3. GitHub Actions workflow hanging (>30 min runtime)
4. Slack flooding with duplicate alerts (webhook misconfigured)

### Rollback Steps
1. **Disable Workflows:** Edit `.github/workflows/` to set `enabled: false`
2. **Stop Running Jobs:** `gh run cancel <run-id>` for any in-progress runs
3. **Reset Supabase:** (if data corruption) — clear pipeline_health table
4. **Alert Team:** Post to #outreach-operations: "Phase 1 rolled back due to [reason]"
5. **Post-Mortem:** Debug, fix root cause, re-test, reschedule deployment

**Rollback Approval:** SRE or Carly (either can authorize)

---

## SUCCESS CRITERIA (Overall)

✅ **All 4 Phases Complete:**
- Phase 1: Setup without errors
- Phase 2: Live monitoring confirmed (≥5 pipeline_health rows)
- Phase 3: All 6 roles approved
- Phase 4: Post-launch log committed

✅ **No Critical Issues:**
- No runtime errors in workflow logs
- No credential leaks
- No performance degradation
- Monitoring dashboards responsive

✅ **Ready for Phase 2 (Aug 18–22):**
- CI/CD workflows for Phase 2 agents designed (Substack, RentAHuman)
- Integration testing plan documented
- Stakeholders aligned on Phase 2 timeline

---

## CONTACTS & ESCALATION

| Role | Name | Contact | Approval? |
|------|------|---------|-----------|
| **Engineer** | [TBD] | [Email/Slack] | [ ] |
| **DevOps** | [TBD] | [Email/Slack] | [ ] |
| **QA** | [TBD] | [Email/Slack] | [ ] |
| **SRE** | [TBD] | [Email/Slack] | [ ] |
| **Security** | [TBD] | [Email/Slack] | [ ] |
| **Project Owner** | Carly Anderson | carly.r.anderson@gmail.com | [ ] |

**Escalation Path (if issues arise):**
1. First contact: SRE or Carly (immediate response)
2. Technical blocker: Engineer (architecture/code)
3. Infrastructure blocker: DevOps (Supabase/GitHub/Railway)
4. Approval hold: Collect remaining sign-offs

---

## DEPLOYMENT LOG

**Prepared:** 2026-08-14 (Ready for execution Aug 15)  
**Phase 1 Launch Window:** Aug 15, 09:00–15:00 UTC  
**Phase 2 Prep Window:** Aug 18–22 (4-day buffer)  
**Phase 2 Launch Window:** Aug 22, 09:00 UTC  

**Status:** ✅ PRE-LAUNCH VALIDATION READY
