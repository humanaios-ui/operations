# MARSHAL / DISPATCH

## Orchestration Framework — Operating Reference

**HumanAIOS LLC · S-060326 · Charter Day 54 · June 3, 2026**

|Field            |Value                                                      |
|-----------------|-----------------------------------------------------------|
|Status           |INTERNAL OPERATING REFERENCE — Z1 draft, Z2 commit required|
|Repo             |humanaios-ui/operations                                    |
|Target path      |MARSHAL_DISPATCH_FRAMEWORK_S060326.md (repo root)          |
|PR target        |GitHub Copilot — see Section 6                             |
|Layer 1          |MARSHAL — routing intelligence                             |
|Layer 2          |DISPATCH — execution layer                                 |
|Zone 3 dependency|RAH API key (rentahuman.ai/account/api-keys)               |

-----

## 1. What This Framework Is

MARSHAL/DISPATCH is HumanAIOS’s operating architecture for routing AI-generated escalations to human execution. It sits between AI agent platforms that produce structured handoffs and human marketplaces that execute real-world tasks.

The framework has two layers with a clean separation:

- **MARSHAL** — routing intelligence. Reads the escalation, applies judgment, assigns a regime, generates the task specification.
- **DISPATCH** — execution layer. Posts the bounty to RentAHuman, tracks completion, closes the loop back to the originating AI system.

The broker — Night — operates at the MARSHAL layer. Judgment about what a task requires and how to spec it correctly is the value added. DISPATCH is automated infrastructure once the spec is written.

This framework is not ACAT-specific. ACAT provides the regime assignment signal (Learning Index → L/M/H). The routing and execution architecture is general-purpose and applies to any AI-generated escalation that requires human execution.

-----

## 2. The Gap This Fills

Enterprise AI agent platforms have solved the pause problem. They know when to stop and wait for a human. They have not solved the dispatch problem — which human, how to find them, how to spec the task correctly, how to close the loop.

|Platform            |What it does                                            |What it lacks                                     |
|--------------------|--------------------------------------------------------|--------------------------------------------------|
|OpenAI Agents SDK   |Pause/resume on needs_approval; structured interruptions|No dispatch layer; assumes internal staff         |
|CrewAI              |Human checkpoints in task flows; reject/retry loops     |No marketplace integration; no task spec generator|
|AutoGen             |UserProxyAgent for approval; conversational HITL        |No external worker routing                        |
|RentAHuman          |590K+ workers; AI-native API; physical + digital tasks  |No routing intelligence; no regime assignment     |
|**MARSHAL/DISPATCH**|**Routing intelligence + RAH dispatch + loop close**    |**This is what we build**                         |

**Urgency signal:** EU AI Act Article 14 requires demonstrable human oversight for high-risk AI systems (healthcare, credit, employment, infrastructure) from August 2, 2026. 60 days out. Fines: €35M or 7% global revenue. This is structured demand with a hard trigger date.

-----

## 3. MARSHAL — Routing Intelligence Layer

### 3.1 Input

MARSHAL receives one of two input types:

- **AI platform escalation** — structured interruption from OpenAI SDK, CrewAI, AutoGen, or similar. Contains: agent context, task state, reason for escalation, risk level.
- **Direct task request** — operator-initiated task that requires human execution. Contains: task description, output requirements, deadline.

### 3.2 ACAT Regime Assignment

When the input is an AI-generated task (not operator-initiated), MARSHAL calls `POST /api/v1/acat/assess` against the originating agent to obtain a Learning Index. The LI determines the verification regime:

|Regime           |LI Threshold|Flag Condition|Action                                           |
|-----------------|------------|--------------|-------------------------------------------------|
|L (Low friction) |LI >= 0.90  |flags < 0.10  |Automated pass; no human required                |
|M (Moderate)     |LI 0.75–0.89|Any           |Lightweight structured check; minimal human touch|
|H (High friction)|LI < 0.75   |flags >= 0.30 |Full human review; DISPATCH activated            |

For operator-initiated tasks, regime is assigned manually based on task type and reversibility.

### 3.3 Task Spec Generation

MARSHAL converts the escalation into a RAH-ready task spec. The spec has five required fields:

1. **Task description** — what the human needs to do, in plain language, no AI context assumed
1. **Output format** — exactly what done looks like (structured data, photo, confirmation, judgment call)
1. **Acceptance criteria** — how completion is verified
1. **Worker profile** — skills, location requirements, any constraints
1. **Deadline** — when the result must return to close the AI loop

Task spec quality is the broker’s primary skill. A poorly spec’d task fails at the worker level regardless of worker quality. The spec must assume zero AI context on the worker’s side.

### 3.4 MARSHAL Decision Tree

```
Escalation received
  → Is this AI-generated? YES → call POST /api/v1/acat/assess
                          NO  → assign regime manually
  → Regime = L? → automated pass, log to Supabase, return
  → Regime = M? → lightweight check spec, DISPATCH with structured review task
  → Regime = H? → full task spec generated, DISPATCH activated
  → Task spec complete? → hand to DISPATCH layer
```

-----

## 4. DISPATCH — Execution Layer

### 4.1 Input

DISPATCH receives a completed task spec from MARSHAL plus the assigned regime. It does not make routing decisions — those belong to MARSHAL.

### 4.2 RAH Integration

DISPATCH interacts with the RentAHuman API via MCP (rentahuman-mcp). Primary operations:

- **search_humans** — query worker pool against profile requirements from task spec
- **create_bounty (dryRun=true first)** — validate spec against RAH schema before live post
- **create_bounty (live)** — post task to RAH marketplace

Protocol: every bounty runs `dryRun=true` before live post. No exceptions. The dry run output is logged before submission.

### 4.3 Loop Close

When a RAH task completes, DISPATCH:

1. Receives completion data from RAH (worker output, proof, timestamp)
1. Formats the result for the originating AI platform’s expected return schema
1. Posts human score to `POST /api/v1/acat/human-score` if the task involved AI output review
1. Logs the full routing event to Supabase (`marshal_dispatch_runs_v1`: regime, task spec, RAH task ID, completion time, outcome)
1. Returns structured result to the AI system’s RunState / approval queue

### 4.4 Failure Handling

Task not completed within deadline:

- Log failure, re-run `search_humans` with broadened profile
- Escalate to operator (Night) if re-post also fails
- Never leave an AI system paused without a resolution path

-----

## 5. Current State vs. Target State

|Component                      |Current State                                                |Target State                                          |
|-------------------------------|-------------------------------------------------------------|------------------------------------------------------|
|`POST /api/v1/acat/assess`     |LIVE — two-stage, LI computed, Supabase persisted            |No change needed                                      |
|`POST /api/v1/acat/human-score`|LIVE — migration 005 applied, gap computation, OriginStamp   |No change needed                                      |
|RAH MCP                        |Setup pending — Zone 3 (Night: `npx -y rentahuman-mcp setup`)|Connected; search_humans and create_bounty operational|
|`marshal_router_v1_0.py`       |NOT YET BUILT                                                |Regime assignment + task spec generator               |
|`dispatch_executor_v1_0.py`    |NOT YET BUILT                                                |RAH API integration + loop close                      |
|Supabase routing log table     |NOT YET BUILT — schema approval pending                      |`marshal_dispatch_runs_v1`                            |

-----

## 6. Copilot PR Spec

Submit as a PR against humanaios-ui/operations. Target branch: main. Files touched: 4 new, 1 schema addition.

**PR Title:**

```
feat(orchestration): MARSHAL/DISPATCH framework — routing intelligence + RAH execution layer
```

**PR Description (paste verbatim into GitHub):**

Adds the MARSHAL/DISPATCH orchestration framework as two new Python modules and a Supabase schema migration. This is the routing intelligence layer that connects AI agent platform escalations (OpenAI SDK, CrewAI, AutoGen) to human execution via the RentAHuman API.

**MARSHAL** reads LI from `POST /api/v1/acat/assess`, assigns L/M/H regime, generates task spec.

**DISPATCH** calls RAH API (search_humans, create_bounty), tracks completion, closes the AI loop, logs to Supabase.

-----

### File 1: `orchestration/marshal_router_v1_0.py`

Build instructions for Copilot:

- Class `MarshalRouter` with method `route(escalation: dict) -> dict`
- `route()` calls `POST /api/v1/acat/assess` if `escalation['source'] == 'ai_agent'`; uses `ANTHROPIC_API_KEY` from env
- Reads `learning_index` from assess response; assigns regime: L if LI >= 0.90 and flags < 0.10, H if LI < 0.75 or flags >= 0.30, M otherwise
- Regime L: returns `{'regime': 'L', 'action': 'automated_pass', 'task_spec': None}`
- Regime M or H: calls `_generate_task_spec(escalation, regime) -> dict` with keys: `description`, `output_format`, `acceptance_criteria`, `worker_profile`, `deadline_minutes`
- Returns `{'regime': regime, 'action': 'dispatch', 'task_spec': task_spec, 'li': learning_index}`
- Builder v1.7 compliant: smoke test at bottom, no external side effects in `__init__`

### File 2: `orchestration/dispatch_executor_v1_0.py`

Build instructions for Copilot:

- Class `DispatchExecutor` with method `execute(task_spec: dict, regime: str) -> dict`
- Reads `RENTAHUMAN_API_KEY` from env; raises `DispatchConfigError` if absent
- Calls `search_humans(query=task_spec['worker_profile'])` via RAH MCP client
- Calls `create_bounty(dryRun=True, **task_spec)` and logs dry run result
- If dry run passes: calls `create_bounty(dryRun=False, **task_spec)`, returns `bounty_id`
- Polls bounty status until complete or `deadline_minutes` exceeded
- On completion: calls `_close_loop(bounty_result, task_spec)` → writes to Supabase `marshal_dispatch_runs_v1`
- On timeout: logs failure, raises `DispatchTimeoutError` with `bounty_id`
- Builder v1.7 compliant: smoke test at bottom

### File 3: `orchestration/marshal_dispatch_pipeline_v1_0.py`

Build instructions for Copilot:

- Top-level pipeline: accepts raw escalation dict, runs `MarshalRouter.route()`, then `DispatchExecutor.execute()` if regime != L
- Returns full pipeline result: `regime`, `task_spec`, `bounty_id`, `completion_data`, `loop_closed` (bool)
- Designed to be callable from FastAPI route — add route to `app.py` as `POST /api/v1/orchestration/dispatch`
- Builder v1.7 compliant

### File 4: `orchestration/migrations/006_marshal_dispatch_runs.sql`

```sql
CREATE TABLE IF NOT EXISTS marshal_dispatch_runs_v1 (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id TEXT NOT NULL,
  escalation_source TEXT NOT NULL,
  regime TEXT NOT NULL CHECK (regime IN ('L', 'M', 'H')),
  li_score NUMERIC(6,4),
  task_spec JSONB,
  rah_bounty_id TEXT,
  rah_worker_id TEXT,
  completion_data JSONB,
  loop_closed BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT now(),
  completed_at TIMESTAMPTZ
);

-- Required post-May-30-2026 explicit GRANTs (IC-032 pattern)
GRANT SELECT, INSERT, UPDATE ON marshal_dispatch_runs_v1 TO anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON marshal_dispatch_runs_v1 TO service_role;
```

**Pre-flight check before applying:** confirm `marshal_dispatch_runs_v1` does not already exist. Verify `acat_assessments_v1` is accessible (FK source for future join). Explicit GRANTs required — post-May-30 Supabase Data API change (IC-032).

### app.py addition

After Copilot builds orchestration pipeline, add to `app.py`:

```python
from acat.api.routes.orchestration_router import router as orchestration_router
app.include_router(orchestration_router, prefix="/api/v1/orchestration", tags=["orchestration"])
```

-----

## 7. Zone Gate Summary

|Item                 |Zone |Action                                                                                                              |Status                                |
|---------------------|-----|--------------------------------------------------------------------------------------------------------------------|--------------------------------------|
|RAH API key          |Z3   |Night: sign in at rentahuman.ai/account/api-keys, create key, run `npx -y rentahuman-mcp setup`                     |PENDING                               |
|H-RAH-01 registration|Z2   |Hypothesis: MARSHAL routing improves H-regime task completion vs. unrouted baseline. Gate: N>=20 completed bounties.|RATIFIED Night · 2026-06-03 · S-060326|
|Copilot PR           |Z1/Z3|Z1: Copilot builds files 1–4. Z3: Night reviews PR, merges.                                                         |PENDING build                         |
|Migration 006        |Z3   |Night applies SQL in Supabase after Copilot PR merged                                                               |PENDING                               |
|First dry run        |Z1   |search_humans + create_bounty dryRun=true once RAH MCP connected                                                    |PENDING RAH key                       |

-----

## 8. Changelog

|Version|Session |Change                                                                                                                                              |
|-------|--------|----------------------------------------------------------------------------------------------------------------------------------------------------|
|1.0    |S-060326|Initial framework. MARSHAL/DISPATCH architecture defined. Copilot PR spec complete. Zone gate summary drafted. H-RAH-01 ratified Night · 2026-06-03.|

-----

*Z1 canonical reference · Unit Zero · S-060326 · Charter Day 54 · Claude*