# Autonomous Agents — empirica-outreach

Multi-phase autonomous agent deployment system for governance, monitoring, and content generation.

## Architecture

```
Phase 1 (Foundation)     → Governance + Monitoring
  ├─ principle_compliance_bot_v1.py
  └─ api_monitoring_bot_v1.py

Phase 2 (Revenue + Content)
  ├─ substack_content_agent_v1.py (PLANNED)
  └─ rentahuman_validation_bot_v1.py (PLANNED)

Phase 3 (Transparency + Funding)
  ├─ moltbook_agent_v1.py (PLANNED)
  ├─ financial_investor_bot_v1.py (PLANNED)
  └─ moltbook_platform_sync_v1.py (PLANNED)
```

## Phase 1: Foundation

### Agent: Principle Compliance Bot

**Purpose:** Validate decisions/artifacts against 22-principle constitution (P19: Detection beats compliance)

**File:** `principle_compliance_bot_v1.py`

**Usage:**
```bash
python3 tools/agents/principle_compliance_bot_v1.py --check-commit "commit msg" --files file1.py,file2.py
python3 tools/agents/principle_compliance_bot_v1.py --smoke-test
```

**Trigger:** GitHub Actions on-commit (`.github/workflows/agent-principle-compliance-check.yml`)

**Output:** GitHub issues with violation reports

### Agent: API Monitoring Bot

**Purpose:** Daily health checks for critical APIs (Metaculus, Supabase, Railway, Anthropic)

**File:** `api_monitoring_bot_v1.py`

**Usage:**
```bash
python3 tools/agents/api_monitoring_bot_v1.py --check-all
python3 tools/agents/api_monitoring_bot_v1.py --smoke-test
```

**Trigger:** GitHub Actions daily at 09:00 UTC (`.github/workflows/agent-api-monitor.yml`)

**Output:** `pipeline_health` Supabase table + Slack notifications

## Shared Infrastructure

### `_shared/constitution_checker.py`

Validates work against 22-principle constitution (loaded from `constitution.json`).

**Classes:**
- `ConstitutionChecker` — Main validator

**Methods:**
- `check_commit(msg, files)` — Check commit message and changed files
- `check_decision_log(decision)` — Check decision artifact
- `check_finding_log(finding)` — Check finding artifact
- `check_artifact_graph(artifacts)` — Check artifact connectivity (P-GRAPH)
- `check_principle(plan_step)` — Generic principle check

### `_shared/supabase_client.py`

Supabase connection utilities.

**Functions:**
- `get_supabase_client()` — Get authenticated client (non-blocking)
- `write_to_pipeline_health(status, integration, note)` — Write status

### `_shared/github_client.py`

GitHub API wrapper.

**Classes:**
- `GitHubClient` — API wrapper

**Methods:**
- `create_issue(title, body, labels)` — Create GitHub issue
- `get_recent_commits(limit)` — Fetch recent commits

## Environment Variables

### Required (for production)
- `GITHUB_TOKEN` — GitHub Actions token (auto-provided)
- `SUPABASE_URL` — Supabase project URL
- `SUPABASE_KEY` — Supabase service role key

### Optional (for specific agents)
- `METACULUS_TOKEN` — Metaculus API token
- `ANTHROPIC_API_KEY` — Anthropic API key
- `SLACK_WEBHOOK_URL` — Slack webhook for alerts

## Testing

### Smoke Tests

All agents include `--smoke-test` flag for quick validation:

```bash
python3 tools/agents/principle_compliance_bot_v1.py --smoke-test
python3 tools/agents/api_monitoring_bot_v1.py --smoke-test
python3 tools/agents/_shared/constitution_checker.py --smoke-test
```

### Unit Tests

Tests in `tools/tests/`:
- `test_principle_compliance_bot.py`
- `test_api_monitoring_bot.py`
- `test_constitution_checker.py`

Run all tests:
```bash
python3 -m unittest discover -s tools/tests -p "test_*.py" -v
```

## Builder v1.7 Compliance

All agents follow Builder v1.7 standards:
- `TOOL_NAME` and `TOOL_VERSION` constants
- `--smoke-test` flag support
- Docstrings on all classes/methods
- Error handling for missing dependencies

## Principles Framework

Constitution defined in `constitution.json` with 22 principles:

| Framework | Principles | Purpose |
|-----------|-----------|---------|
| 12 Steps | P1–P5 | Recovery/correction process |
| 12 Traditions | P8, P16, P-ANON, P-T2, P-T7, P-T10 | Group conduct |
| Hawkins | P-HUMILITY, P-HAWKINS-MIN | Calibration floor |
| Governance | P19, P-TRANSPARENCY, P-MESH-ACK | Detection + collaboration |
| Epistemic | P-ARTIFACT-BREADTH, P-GRAPH | Measurement discipline |
| Praxic | P-COMMIT-DISCIPLINE | Git hygiene |
| Collaboration | P-PULL-FIRST, P-SOURCE-SHARING | Mesh discipline |

## Deployment

### To Production

1. **Merge to main:** `git push origin main`
2. **Workflows activate:** GitHub Actions automatically triggered
3. **Monitor:** Check `.github/workflows/` logs for execution

### Daily Monitoring

```bash
# View API monitor results (Supabase)
empirica investigate --query "Recent API monitoring from pipeline_health table"

# View compliance violations (GitHub)
gh issue list --label "governance" --label "principle-compliance"
```

## Non-Blocking Design

Both Phase 1 agents are designed to fail gracefully:
- Missing API credentials → agent skips that check, continues
- API timeout → agent reports status, does not crash workflow
- Supabase write failure → logged, does not block deployment
- GitHub issue creation failure → reported, agent continues

This ensures autonomous agents enhance observability without becoming critical paths.

## Next Steps

See Phase 2 roadmap in deployment plan:
- Substack Content Agent (weekly research posts)
- RentAHuman Validation Bot (monthly cohort reports)
- (Phase 3: Moltbook + Financial agents)
