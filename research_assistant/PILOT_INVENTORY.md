# Research Assistant pilot inventory

**Inventory pinned to main:** `7ce11cfa0e5b074bbe0db34d3c28242734403b18` (2026-11-02).  
**Scope:** Z1 / WORKBENCH; authority effect NONE; issue #1116 says admission `NOT_REQUESTED`; production writes and merge/release remain on HOLD.

## Reused surfaces and findings

- **Coordination:** `agent_coordination/reflex.py` and `tests/test_agent_coordination_reflex.py` provide default-offline rendering and explicit GitHub issue/PR comment reads or writes. The merged implementation is PR #987; it is a coordination note, not a durable job queue or worker. `COORDINATION_PROTOCOL.md` lines 22–65 keeps coordination on issues/PRs and rejects a parallel board.
- **Request records:** `tools/decision_relay.py` and `tools/intent_os_requests_v1_0.py` implement existing request plumbing. The relay has write-capable paths, so this contract does not invoke it or treat a request as approval.
- **Evidence receipts:** `workspace_evidence_bus/tools/workspace_event.py` provides deterministic event envelopes, payload hashes, and idempotency-key fields; `workspace_evidence_bus/tools/workspace_lifecycle.py` projects state from validated receipts. These pure helpers are reused in the test. The existing Workspace Evidence Bus also has Google Workspace integration requirements and is not activated by this pilot.
- **Generic agent runtime:** `agent_core.py` lines 100–107 keeps cycles and task history in process memory; `agent_caps_runtime.py` lines 82–96 keeps usage and audit entries in process memory. They provide in-process task/cap patterns, but no durable checkpoint/replay or external-tool isolation, so this pilot does not invoke them as a worker.
- **Scheduled research:** `.github/workflows/research-agent.yml` lines 3–45 runs on a weekly schedule or manual dispatch, has `contents: read`, calls a configured n8n webhook, and waits 90 seconds. Lines 57–65 include a direct arXiv fallback. The workflow does not establish durable checkpoints, replay-safe delivery, browser-independent notification, or an independently enforced read-only tool boundary.
- **Existing deterministic jobs:** `.github/workflows/agent-coordination-reflex-pilot.yml` lines 26–41 grants `contents: read` and runs offline contract tests. `.github/workflows/resource-miner-pr.yml` lines 10–28 grants `contents: read` and runs Resource Miner tests. Neither is a long-lived research worker.
- **Repository role:** `ZONE_REGISTRY.md` lines 10–15 lists operations as active zone Z-000 with a full proposal cap. This repository-level role does not replace the issue/PR admission gate or grant merge authority.
- **Federated schema:** `docs/FEDERATED_EXCHANGE_SCHEMA.md` lines 1–7 identifies the #751 message schema as PREREGISTRATION and requires Z2 ratification before Phase 1; it is a cross-domain message schema, not a durable job/worker contract. This pilot neither modifies nor activates it.
- **Related audit/architecture:** `docs/audit/SYSTEM_AUDIT_PROMPT_v3_1.md` lines 15–18 identifies #974 as the audit tracker; it defines how to evaluate offline execution, not a research assistant runtime. Issue #747 is an architecture proposal; no runtime for its Translation/Research Agent was verified in the inspected main tree.
- **Nearby research work:** PR #914 is an open read-only three-source Resource Miner context pilot; PRs #1092 and #1094 are open E0/E1 source-classification workbenches. PR #1012 is an open Witness/MCP service proposal that includes an opt-in public Resource Miner adapter. These branches are not part of pinned main and are not dependencies of this contract. PR #987 is merged. They are separate candidate work, not proof of durable execution or authorization for this pilot.
- **Admission:** `REPOSITORY_COORDINATOR_POLICY.json` on pinned main says mutable admission state is separate from policy and routing status does not grant merge authority. On initial PR #1117 head `ef39e91ad6398f932b4c7d996d44dd1b6a411f69`, the repository-admission workflow run `41585471559` concluded `action_required` and exposed no job details through the Actions API. Admission is therefore unverified; this PR remains draft/HOLD.
- **Access limitation:** `python3 agent_coordination/reflex.py --subject issue:1116 --read` could not run because authenticated `gh issue view` returned exit status 4. Prior issue-thread notes are unknown here; no inference is made from the failure.

## Contract and test scope

`schemas/research_assistant_job_v0_1.schema.json` defines an allowlisted, public/synthetic-only job record, full repository commit pins, bounded call/time/cost/retry limits, explicit status/checkpoint/evidence fields, a pending-human decision card, and a bounded final receipt. It fixes authority to NONE, execution/authorization/merge flags to false, identity to self-asserted, and checkpoint durability to UNVERIFIED. Final receipt identity and payload hash align with the existing Workspace Evidence Bus event envelope.

`tests/test_research_assistant_contract_v0_1.py` uses only synthetic data and existing deterministic helpers. Passing these tests validates contract shape and envelope compatibility only. It does **not** show that any worker runs offline, persists across process death, deduplicates execution, sends a notification, blocks prompt injection at a host/tool boundary, or has human approval credentials.

## Explicit gaps / follow-on work

1. Select and independently approve a real public-source case; establish a manual/no-agent baseline before comparing outputs.
2. Separately design and test a deny-by-default host/tool boundary, source-content isolation, and real prompt-injection negatives. The schema is not an enforcement mechanism.
3. Implement no worker or queue until reuse is proven insufficient and a separate human-reviewed scope authorizes it. Any future worker must prove durable checkpoint/restart, exactly-once job effects, capped retries, and unrelated-read-only-work continuation while a decision is parked.
4. Verify an existing authorized async delivery channel or leave delivery explicitly unavailable; do not email, publish, commit, or promise offline delivery.
5. Obtain exact-head independent review, required CI, and human admission before changing draft/HOLD status. The current schema and fixture tests do not establish E1 pilot success or authorize widening permissions.
