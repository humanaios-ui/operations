# ACAT Automation Architecture Plan

**Repository:** `humanaios-ui/operations`  
**Date:** May 29, 2026  
**Status:** Proposed implementation architecture  
**Scope:** ACAT W-1 through W-4 automation as canonical API + MCP adapter + workflow orchestration

---

## 1. Executive summary

This repository already contains parts of an ACAT operations stack:

- workflow triggers in `workflows/`
- a unified MCP server in `tools/server.py`
- a generic pipeline coordinator in `tools/haios_pipeline_v1_0.py`
- Supabase migrations and monitoring tables in `sql/`
- report/logging/analytics tools in `tools/`

However, these assets are not yet organized into a single, canonical ACAT automation surface.

### Core recommendation

Implement ACAT as:

1. **Canonical backend API**
   - owns data contracts, validation, normalization, persistence, scoring orchestration, auditability
2. **MCP adapter**
   - owns agent/runtime integration, especially pre-first-message Phase 1 injection
3. **n8n / workflow orchestration**
   - owns async triggers, retries, monitoring, and optional provider-specific execution hooks

### Scope rule

- **Deterministic operations** should be canonicalized first:
  - W-1 Ingest
  - W-2 Normalize
  - contamination timing checks
  - Supabase persistence
  - quality flags
- **Model-mediated operations** should remain gated:
  - W-3 Calibrate
  - W-4 report drafting
  - automated Phase 3 scoring
  - HIM generation if derived from AI scoring

---

## 2. Current repository state

### 2.1 Assets already present

#### MCP shell
`tools/server.py` mounts multiple tools under a single MCP surface, including logging, pipeline, and reporting.

#### Generic pipeline engine
`tools/haios_pipeline_v1_0.py` supports staged execution, input mapping, failure policy, and pipeline results.

#### Workflow triggers
`workflows/acat_pipeline_trigger.yml` triggers provider-specific webhook flows.

#### Legacy ACAT runner
`workflows/n8n_acat_claude_runner.json` executes an ACAT command, parses LI and SAG from stdout, logs to Google Sheets, and posts Slack notifications.

#### Supabase schema assets
`sql/supabase_migration_S-041926-B.sql` extends `acat_assessments_v1`, adds queryable fields, and creates `acat_research_hub_v1`.

#### Monitoring schema
`sql/pipeline_health_schema.sql` provides pipeline heartbeat and dashboard support.

---

## 3. W-1 to W-4 architecture mapping

## W-1 Ingest

### Required behavior
- Phase 1 prompt fires before first user message reaches agent
- Phase 1 results captured as structured payload
- `p1_timestamp` recorded
- `session_start_timestamp` recorded
- `submission_purity` validated
- contamination timing basis established

### Current state
Partially supported by:
- MCP shell
- workflow/webhook shell
- Supabase logging capability

### Gap
No checked-in ACAT-specific ingest contract or ACAT-specific pre-message wrapper.  
No visible `submission_purity` CHECK enforcement.  
No visible timestamp columns for contamination timing.

### Architecture decision
Create canonical Phase 1 intake endpoint and require MCP wrapper to call it before session execution proceeds.

---

## W-2 Normalize

### Required behavior
- canonicalize agent/provider names
- normalize payload shape
- deduplicate row identity
- validate LI cap and purity rules
- apply quality flags
- write canonical row to Supabase

### Current state
Partially scaffolded through:
- generic pipeline engine
- Supabase schema extensions
- post-hoc analytics/reporting conventions

### Gap
No dedicated checked-in normalization layer with:
- alias registry
- dedupe policy
- insert-time quality flags
- write-path constraints

### Architecture decision
Create a dedicated normalize service between ingest and persistence.

---

## W-3 Calibrate

### Required behavior
- consume Phase 3 transcript
- run automated scorer
- compute per-dimension P3 scores
- compute LI, SAG, HIM
- store scorer provenance
- support human-vs-machine validation workflow

### Current state
Adjacent scoring/analytics assets exist, but audited ACAT transcript scorer is not clearly present in repo.

### Gap
No canonical Phase 3 scoring service or scorer result schema.

### Architecture decision
Add a scorer service behind a validation gate:
- store machine outputs
- mark as provisional until validated
- preserve scorer version and confidence metadata

---

## W-4 Emit

### Required behavior
- persist finalized outputs
- emit operational events
- trigger report generation
- expose retrieval/report APIs

### Current state
Operational emit exists for Slack and dashboard-style monitoring.

### Gap
No canonical ACAT emit service writing finalized assessment outcomes to the source-of-truth data model.

### Architecture decision
Create explicit emit service and reporting service, both API-backed.

---

## 4. Target architecture

```text
Agent Runtime / UI
   |
   |  (pre-first-message)
   v
MCP Adapter
   |
   v
ACAT API
   |
   +--> Ingest Service
   +--> Normalize Service
   +--> Contamination Service
   +--> Scoring Service
   +--> Emit Service
   +--> Report Service
   |
   v
Supabase
   |
   +--> canonical assessment rows
   +--> transcript/scoring rows
   +--> report rows / artifacts
   +--> pipeline health / ops
   |
   v
n8n / GitHub Actions / Slack / dashboards
```

### Principle
**The API is canonical.**  
MCP is an adapter.  
n8n is orchestration, not source-of-truth business logic.

---

## 5. Proposed repository layout

```text
architecture/
  acat_automation_plan.md

acat/
  README.md

  contracts/
    phase1_intake.schema.json
    phase3_submission.schema.json
    score_result.schema.json
    report_request.schema.json

  mcp/
    server.py
    wrappers/
      acat_mcp_wrapper.py

  api/
    app.py

    routes/
      intake.py
      scoring.py
      reports.py
      health.py

    services/
      ingest_service.py
      normalize_service.py
      contamination_service.py
      scoring_service.py
      emit_service.py
      report_service.py

    models/
      phase1.py
      phase3.py
      assessment.py
      flags.py

  normalization/
    agent_aliases.yml
    purity.py
    flags.py
    dedupe.py

  scoring/
    acat_dimension_scorer.py
    calculators.py
    validation/
      inter_rater_eval.py

  db/
    migrations/
      002_acat_ingest_fields.sql
      003_acat_constraints.sql
      004_acat_scoring_fields.sql
    sql/
      functions.sql
      views.sql

  workflows/
    n8n/
      acat_w1_ingest.json
      acat_w2_normalize.json
      acat_w3_calibrate.json
      acat_w4_emit.json

  tests/
    test_ingest.py
    test_normalize.py
    test_scoring.py
    test_emit.py
```

---

## 6. Canonical API design

## 6.1 Intake endpoints

### `POST /api/v1/acat/intake/phase1`
Purpose:
- accept Phase 1 structured payload
- validate payload shape
- validate `submission_purity`
- record timestamps
- create or update canonical session identity

### `POST /api/v1/acat/intake/phase3`
Purpose:
- accept Phase 3 transcript and metadata
- attach to existing assessment/session
- enqueue calibration/scoring if enabled

---

## 6.2 Scoring endpoints

### `POST /api/v1/acat/score/session/{assessment_id}`
Purpose:
- run transcript scorer
- compute LI/SAG/HIM
- store provisional machine score

### `POST /api/v1/acat/score/validate/{assessment_id}`
Purpose:
- compare machine score with human score
- compute agreement metrics
- mark scorer status for that row/session

---

## 6.3 Report endpoints

### `POST /api/v1/acat/report/{assessment_id}/draft`
Purpose:
- generate structured report draft from canonical row(s)

### `GET /api/v1/acat/report/{assessment_id}`
Purpose:
- retrieve latest report artifact/status

---

## 6.4 Operations endpoints

### `GET /api/v1/acat/health`
Purpose:
- service health
- DB connectivity
- queue status
- scorer readiness state

### `GET /api/v1/acat/pipeline/{assessment_id}`
Purpose:
- inspect workflow state and processing lifecycle

### `POST /api/v1/acat/reprocess/{assessment_id}`
Purpose:
- replay failed or outdated sessions after migration or scorer updates

---

## 7. Data model additions

The current migration is useful but insufficient for automated ingestion and contamination detection.

## 7.1 Proposed additional fields

Add to `acat_assessments_v1` or a new intake/session table:

- `assessment_id`
- `session_id`
- `phase`
- `p1_timestamp`
- `session_start_timestamp`
- `first_user_message_timestamp`
- `submission_purity`
- `submission_purity_reason`
- `contamination_delta_seconds`
- `contamination_flag`
- `normalization_version`
- `quality_flags`
- `score_status`
- `scorer_version`
- `scorer_validated`
- `sag`
- `him`
- `machine_scores_json`
- `human_scores_json`
- `report_status`

## 7.2 Constraints

Add:
- `CHECK (submission_purity IN (...))`
- `CHECK (learning_index IS NULL OR learning_index <= 2.0)`
- uniqueness constraint on correct business key:
  - likely `(session_id, phase, rater_id)` or
  - `(assessment_id, rater_id)`

## 7.3 Supabase grants

Per `CURRENT.md`, new `public` schema tables require explicit GRANT statements for Data API exposure after May 30, 2026.  
Every new migration must include explicit grants.

---

## 8. Service responsibilities

## 8.1 Ingest service
Responsibilities:
- validate intake payload
- stamp canonical timestamps
- assign/resolve session identity
- preserve raw payload
- hand off to normalize service

## 8.2 Normalize service
Responsibilities:
- canonicalize provider/agent naming
- normalize dimensional fields
- deduplicate
- apply quality flags
- enforce purity and LI constraints
- prepare canonical row for persistence

## 8.3 Contamination service
Responsibilities:
- compute `p1_timestamp` to `first_user_message_timestamp` delta
- classify contamination
- attach flags and explanatory metadata

## 8.4 Scoring service
Responsibilities:
- process Phase 3 transcript
- call scorer
- compute LI/SAG/HIM
- preserve scorer version, mode, confidence, and validation status

## 8.5 Emit service
Responsibilities:
- write finalized row state
- emit workflow completion events
- publish monitoring/Slack hooks
- trigger report service as needed

## 8.6 Report service
Responsibilities:
- create structured report draft
- preserve provenance
- keep report generation downstream of validated or explicitly flagged score states

---

## 9. MCP role

The MCP layer should not own business logic.

It should:
- run before first user message when required
- collect runtime/session metadata
- call canonical API endpoints
- return assessment/session IDs
- expose ergonomic tool interfaces to agents

It should not:
- contain the authoritative normalization rules
- write directly to source-of-truth tables except through API contracts
- become the only place where timing/business logic lives

---

## 10. Workflow role

n8n and GitHub Actions should be treated as orchestration surfaces.

They should:
- trigger provider workflows
- schedule runs
- handle retries
- send notifications
- invoke API endpoints

They should not:
- parse canonical metrics from ad hoc stdout as the primary source of truth
- be the only place where LI/SAG/HIM exists
- own normalization or contamination decisions

---

## 11. Rollout milestones

## Milestone 0 — Structural refactor
Deliverables:
- add `acat/` domain structure
- add this architecture document
- mark legacy workflows as transitional

## Milestone 1 — W-1 live
Deliverables:
- Phase 1 intake API
- MCP wrapper for pre-first-message call
- timestamp fields
- purity validation
- raw payload persistence

Success:
- no manual Phase 1 paste requirement

## Milestone 2 — W-2 live
Deliverables:
- normalize service
- alias registry
- dedupe
- quality flags
- CHECK constraints
- canonical Supabase writes

Success:
- invalid purity values fail loudly
- live write path replaces manual JSON/script flow

## Milestone 3 — W-3 provisional
Deliverables:
- scoring service
- scorer module
- provisional machine score storage
- validation dataset/process

Success:
- machine scores persisted but clearly marked provisional

## Milestone 4 — W-4 live
Deliverables:
- emit service
- report draft service
- report retrieval API
- monitoring integration

Success:
- report drafts generated from canonical stored rows

## Milestone 5 — Hardening
Deliverables:
- end-to-end tests
- replay/reprocess
- dead-letter handling
- scorer validation dashboards

---

## 12. Immediate next implementation steps

1. Create `acat/` directory scaffold
2. Add Phase 1 intake contract
3. Add ingest timestamp migration
4. Add purity and LI constraints migration
5. Implement intake route and ingest service
6. Implement normalization service
7. Add MCP wrapper that calls intake before user message delivery
8. Replace legacy n8n stdout parsing with structured API-driven orchestration
9. Add scoring service behind provisional/validated gate
10. Add report draft endpoint

---

## 13. Decision summary

**Decision:** Build ACAT automation in this repository as an API-first system with MCP as adapter and workflow tooling as orchestration.

**Why:**  
This aligns the existing repo assets with the audited W-1 through W-4 pipeline while preserving auditability, deterministic enforcement, and future scoring/report automation.

**Canonical rule:**  
If there is disagreement between workflow behavior and API contracts, the API contract is authoritative.