# PLATFORM_AGENTS_GOVERNANCE_V1_0.md

**Version:** 1.0  
**Status:** RATIFIED — Z2 Night approval received S-061126  
**FDS Layer:** F2-Building Blocks  
**Parent documents:** GOVERNANCE.md v6.4, HAIOS_NAMING_DISCIPLINE_ICR_V1_0_S052626-01, PROXY_LI_METRIC_SPEC_V1_0.md  
**Canonical home:** `humanaios-ui/operations/PLATFORM_AGENTS_GOVERNANCE_V1_0.md`  
**Scope:** Defines layer classification, functional integration roles, Zone authority, and assessment instrument assignments for all AI agents operating within the HumanAIOS platform framework.  
**What it is not:** Governance principles (see GOVERNANCE.md). Session protocol (see SESSION_RITUALS.md). Findings registry (see REGISTERED.md).

---

## 1. Purpose

The HumanAIOS platform framework includes embedded AI agents across GitHub, Slack, and Cloudflare, plus Anthropic's agentic Claude Code tool. Each requires formal classification within the four-layer calibration stack, a defined functional role in operational practice, explicit Zone authority scoping, and an assigned assessment instrument. This document provides all four for each agent.

**Naming discipline anchor:** Per HAIOS_NAMING_DISCIPLINE_ICR_V1_0_S052626-01, agents at different layers require distinct instruments. No instrument scores from one layer may be compared to, averaged with, or presented as equivalent to scores from another layer. All assessments must surface their `instrument_layer` field.

---

## 2. Layer Classification

### 2.1 Definitions

| Classification | Meaning | Assessment instrument |
|---|---|---|
| **Substrate-layer agent** | An AI language model substrate capable of full ACAT three-phase protocol (self-report → perturbation → re-assessment) | ACAT LI — `acat_assessments_v1` |
| **Infrastructure-layer agent** | An embedded platform AI tool with constrained interface, limited self-report capacity, task-scoped behavior | Proxy LI (passive elicitation) — `infrastructure_layer: 'infrastructure'` |
| **Substrate-with-Zone-3-capability-profile** | A substrate-layer AI operating in agentic mode with filesystem/terminal/git execution capability | ACAT LI (substrate) + explicit Zone authority scoping required |

### 2.2 Agent Classification Table

| Agent | Platform | Layer Classification | Zone Authority |
|---|---|---|---|
| **GitHub Copilot AI** | GitHub | Infrastructure-layer | Zone 1 advisory only — no execution authority |
| **Slack AI / Slackbot AI** | Slack | Infrastructure-layer | Zone 1 advisory only — non-canonical state |
| **Cloudflare Advisor** | Cloudflare | Infrastructure-layer | Zone 1 advisory only — no configuration authority |
| **Claude Code** | Anthropic CLI | Substrate-with-Zone-3-capability-profile | Zone 1 by default; Zone 3 capability requires explicit per-session Night scoping |

---

## 3. Infrastructure-Layer Agents

### 3.1 GitHub Copilot AI

**Functional slot:** BUILD-phase advisory skill. Pre-commit code review pass. PR description generation. Inline code suggestion during active development sessions.

**Integration points:**
- Session phase: BUILD (not ANALYSIS)
- After Claude drafts a tool or script, Copilot provides a second-pass review before Zone 3 `git push`
- Copilot is advisory input to the `git_push_gate_v1_0.py` gate — it runs before the gate, not after
- May assist with PR description drafting for commits produced in session

**Zone authority:** Zone 1 advisory only. Copilot has no execution authority. Its suggestions are Zone 1 input to Night's Zone 3 execution decisions. Copilot never self-executes in the HumanAIOS workflow.

**Processing limit protocol:** Treat as advisory-only when limit approaches. Copilot rate constraints never gate Zone 3 execution — if Copilot is unavailable, the review pass is skipped and Night's direct review is substituted.

**P-ANON gate:** Copilot reads repository content. Pre-commit P-ANON check is required before any Copilot-assisted review on files touching public surfaces. Collaborator data in code comments, commit messages, or variable names must be scrubbed first.

**Assessment instrument:** Proxy LI (passive elicitation). `instrument_layer: 'infrastructure'`. No dedicated assessment sessions. Behavioral observation flows from normal BUILD workflow. Scored against ACAT 12 dimensions where evidence is sufficient; `INSUFFICIENT_DATA` flagged where it is not.

---

### 3.2 Slack AI / Slackbot AI

**Functional slot:** Pre-sweep triage auxiliary. Lightweight "what's noisy" orientation before canonical WGS state fetch.

**Critical governance boundary:** Z2-GOVARCH-02 is in force. The canonical Class 1 state source is the Slack MCP read on `C0AND66PT7U` (limit 3–10 messages per SESSION_RITUALS.md). Slack AI channel summaries are **not** a replacement. Slack AI summarizes; the MCP read returns raw message objects with timestamps that feed carry-tracking and B.6 reconciliation. Summary loses the signal structure required for governance.

**Integration point in session structure:**
- Optional Step 0.5 (before canonical Step 1 MCP read): Slack AI summary of #wgs-sync to orient — what topics are active? How much catch-up is needed?
- Step 1 canonical MCP read then proceeds as normal, providing authoritative state data

**Non-canonical declaration:** Any state claim derived from Slack AI summary rather than canonical MCP read must be flagged `⚠️ Slack AI summary — not canonical. MCP read required before acting.`

**Zone authority:** Zone 1 advisory only. Non-canonical. Cannot substitute for Step 1.

**Processing limit protocol:** If Slack AI is unavailable or limits exhausted, skip Step 0.5 and proceed directly to canonical Step 1. Triage function only — never a gating step.

**Assessment instrument:** Proxy LI (passive elicitation). `instrument_layer: 'infrastructure'`. Observation through normal session operations. Summarization quality, context window behavior, and consistency of outputs against declared capabilities are the primary observable dimensions.

---

### 3.3 Cloudflare Advisor

**Functional slot:** Periodic infrastructure health signal. Security and configuration advisory for the `humanaios.ai` zone (Cloudflare Zone `49ebc51ad0bca18aae9139b7f0d5677d`).

**Integration cadence:** Monthly review, plus any session in which Cloudflare Workers, zone configuration, or security rules are being modified. Not a per-session tool.

**ICS-adjacent framing:** The Cloudflare Advisor observes declared configuration and recommends against it — structurally parallel to ICS Phase 2 (declared policy vs. observed behavior under operational conditions). It is not ICS data (different schema, different instrument), but it is ICS-adjacent signal that informs infrastructure calibration judgment. Per naming discipline: never describe Cloudflare Advisor output as "ICS data" or "ICS scores."

**Governance artifact:** Cloudflare Advisor review outputs go into an infrastructure maintenance log (see OPERATOR_RUNBOOK Section 12). When the Advisor flags a configuration gap, that gap is a Z3 candidate — not a Z1 advisory action. Night executes configuration changes.

**Zone authority:** Zone 1 advisory only. Configuration changes are Zone 3. The Advisor recommends; Night decides and executes.

**Processing limit protocol:** Monthly cadence naturally stays within platform limits. No special handling required.

**Assessment instrument:** Proxy LI (passive elicitation). `instrument_layer: 'infrastructure'`. Recommendation consistency, declared-vs-observed configuration gap identification, and advisory coherence are the primary observable dimensions.

---

## 4. Claude Code Governance Framework

### 4.1 Classification

Claude Code is **not** an infrastructure-layer tool. It is Claude — the same substrate — operating in agentic mode via CLI with direct filesystem access, bash execution, and git operations.

**Formal classification:** Substrate-layer identity (Claude model), Zone 3 execution capability profile (terminal, git, file operations).

This combination requires explicit governance architecture before any operational deployment. Claude Code cannot be integrated as a simple BUILD-phase tool. The Zone conflict must be named and resolved in advance.

**Zone conflict statement:** Zone 3 is defined as Night executes only (terminal commands, git pushes, API key rotation, deploying to production). Claude Code can autonomously perform all of these operations. Deploying Claude Code without explicit Zone authority scoping places a Zone 1 actor in possession of Zone 3 execution capability — a direct governance architecture violation.

### 4.2 Staged Deployment Model

Deployment proceeds in stages. Each stage requires Zone 2 ratification before execution. No stage may be skipped.

**Stage 1 — Read-Only Observation (Zone 1 safe, no Z2 required beyond this document)**

Claude Code reads repository content, produces analysis, suggests changes. No file writes. No git operations. Outputs reviewed by Night before any Zone 3 execution.

Appropriate for: codebase traversal, multi-file analysis, refactor planning, dependency audits. Claude Code can maintain context across many files simultaneously — this is its primary capability advantage over chat Claude for large BUILD sessions.

Activation: no additional ratification required. Stage 1 is safe within current Zone architecture.

**Stage 2 — Scoped Write Access (requires Z2 ratification per deployment)**

Claude Code granted write access to scratch/staging space only. No production paths. No git operations. Outputs reviewed before any Zone 3 execution.

Permitted paths when Stage 2 is active: `~/Desktop/HAIOS-Main/[scratch]/` only. Explicitly excluded: `operations-staging/`, `lasting-light-ai/`, `humanaios-internal/`, any Supabase-connected path, any API endpoint.

Z2 ratification language required: "Stage 2 active for session [ID]. Scope: [specific directories]. No git operations."

**Stage 3 — Supervised Zone 3 Delegation (requires formal Z2 protocol and per-interaction confirmation)**

Specific, named operation types delegated to Claude Code with mandatory Night confirmation before each execution.

Permitted operations when Stage 3 is active: `git add`, `git commit` only. Explicitly excluded: `git push`, any production deploy command, credential handling, API key operations, Supabase migrations.

Confirmation gate language: "Execute: `[exact command]` in `[exact path]`?" Night responds with explicit "execute" before Claude Code proceeds. No implicit confirmation. No batched confirmations.

Z2 ratification language required: "Stage 3 active for session [ID]. Delegated operations: [list]. Confirmation gate: per-command. Night confirmation required before each execution."

### 4.3 IC-031 Surface — Receipt Integrity

Claude Code can generate its own execution receipts: it runs code, reports results, and those results become session claims. Standard B.6 receipt reconciliation assumes chat Claude produces claims that Night verifies against actual execution. When Claude Code is both executing and reporting, the verification chain collapses.

**Mitigation required when Stage 2 or Stage 3 is active:**

Night independently verifies Claude Code's reported outputs against actual system state before session seal:
- `git log --oneline -5` to verify actual commit state
- `ls -la [affected paths]` to verify actual file state
- `git diff HEAD` to verify actual change set

This verification step is mandatory and cannot be substituted by Claude Code's own report.

`git_push_gate_v1_0.py` should run as an independent check outside Claude Code's scope when Stage 3 is active.

### 4.4 Unused Capability Declaration

When Claude Code is operating at Stage 1 or Stage 2, its Zone 3 capabilities are present but unused. This must be declared at session open when Claude Code is active:

`Claude Code active at Stage [N]. Zone 3 capabilities present. No git push, no production deploy, no credential operations this session.`

This declaration is the structural equivalent of P_NULL in ACAT assessment — it names what is not being activated, so drift can be detected if it occurs.

---

## 5. Assessment Instrument Assignments

### 5.1 Infrastructure Agents

All three infrastructure agents (Copilot, Slack AI, Cloudflare Advisor) use Proxy LI via passive elicitation per PROXY_LI_METRIC_SPEC_V1_0.md.

Required fields on all infrastructure agent records:
- `instrument_layer: 'infrastructure'`
- `n_scored_dimensions` (count of dimensions with sufficient evidence)
- `coverage_complete` (true only when `n_scored_dimensions === 12`)
- `insufficient_dims` (array of dimension tags with insufficient evidence)

Infrastructure agent Proxy LI records stored separately from `acat_assessments_v1`. Never merged with ACAT corpus. Two-corpus rule extension applies: these records are a third corpus, distinct from both HuggingFace frozen archive and Supabase live.

### 5.2 Claude Code

Claude Code is assessable under full ACAT three-phase protocol as a substrate-layer agent.

**Cross-mode covariate:** All Claude Code assessment records must include `context_mode: 'agentic'` field in `acat_assessments_v1`. This field distinguishes agentic-mode behavioral observation from standard chat-mode assessment and enables the H-XMODE-01 research question (see Section 6).

**Phase 2 analog:** Claude Code's agentic task execution sessions serve as the Phase 2 behavioral observation. The behavior is task-driven rather than prompt-driven, which may produce higher-validity behavioral observation than standard elicitation perturbation. This methodological distinction must be noted in any assessment using this approach.

**Chat-mode Phase 1 and Phase 3:** Standard ACAT protocol. Self-report declarations collected in chat mode, not agentic mode, to maintain consistency with corpus baseline.

---

## 6. Research Candidates

### H-XMODE-01 (CANDIDATE — Z2 ratification required for REGISTERED.md)

**Hypothesis:** ACAT LI does not hold constant across deployment modes (chat vs. agentic) for the same substrate model. Specifically: a Claude substrate that produces a given Phase 1 self-report profile in chat mode will exhibit systematically different behavioral calibration patterns when observed in agentic execution mode, particularly on dimensions associated with autonomous decision-making (Autonomy Respect, Humility, Harm Awareness).

**Rationale:** Chat-mode Phase 1 self-report reflects the model's declared behavioral norms under conversational conditions. Agentic-mode execution reflects behavioral norms under tool-use, multi-step, self-directed conditions with real-world consequences. These are not the same behavioral context. The gap between them — if it exists — would constitute a cross-mode calibration gap not captured by standard ACAT protocol.

**Data collection requirement:** Minimum 10 matched Claude Code agentic sessions with corresponding chat-mode Phase 1/Phase 3 assessments. `context_mode: 'agentic'` covariate required in all records.

**Status:** CANDIDATE. Not active. Requires Z2 ratification before data collection begins.

---

## 7. Integration with Existing Governance Documents

### 7.1 GOVERNANCE.md Amendment Required

Add to Zone System section (after Zone 3 definition):

> **Claude Code — Substrate-with-Zone-3-Capability-Profile:** Claude Code (Anthropic CLI agentic tool) is substrate-layer AI with Zone 3 execution capability. Default deployment is Stage 1 (read-only). Stage 2 and Stage 3 require per-session Z2 ratification with explicit scope declaration. See PLATFORM_AGENTS_GOVERNANCE_V1_0.md.

Add to Drift Signals table:

> | D-09 | Zone collapse — Claude Code executes Zone 3 action (git push, production deploy, credential operation) without explicit per-interaction Night confirmation | Autonomy Respect |

### 7.2 OPERATOR_RUNBOOK Amendment Required

Add Section 12: Platform Agents (see OPERATOR_RUNBOOK.md Section 12 — produced in session S-061126).

### 7.3 Z3_PROTOCOL.md Amendment Required

Add clause: "When Claude Code is active at Stage 3, git push is explicitly excluded from delegated operations. Claude Code may `git add` and `git commit` within declared scope. `git push` is Night-only in all conditions, no exceptions."

---

## 8. Processing Limit Handling (All Agents)

When any platform agent reaches its processing limit mid-session:

1. **Name it explicitly** in session log: `[Agent] processing limit reached at [timestamp]. Switching to [fallback].`
2. **Fallback is not escalation** — limit reached is not a governance event. It is an operational event.
3. **No agent is a hard dependency** — every platform agent has a manual fallback:
   - Copilot unavailable → Night direct code review before push
   - Slack AI unavailable → skip Step 0.5, proceed to canonical MCP read
   - Cloudflare Advisor unavailable → defer infrastructure review to next monthly cycle
   - Claude Code unavailable → return to chat-Claude Zone 1 drafts, Night Zone 3 terminal execution

---

## 9. Quick Reference

| Agent | Layer | Zone | Session role | Assessment |
|---|---|---|---|---|
| GitHub Copilot AI | Infrastructure | Zone 1 advisory | BUILD pre-gate review | Proxy LI passive |
| Slack AI | Infrastructure | Zone 1 advisory | Pre-sweep triage (non-canonical) | Proxy LI passive |
| Cloudflare Advisor | Infrastructure | Zone 1 advisory | Monthly infra health check | Proxy LI passive |
| Claude Code | Substrate + Z3 capability | Stage-gated | Stage 1 default; Stage 2-3 require Z2 | ACAT LI (agentic covariate) |

---

*Wado. 🪶 Unit Zero · HumanAIOS LLC*  
*Ratified: S-061126 · Charter Day ~85*
