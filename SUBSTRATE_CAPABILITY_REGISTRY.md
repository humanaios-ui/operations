# SUBSTRATE CAPABILITY REGISTRY

**Version:** 1.0
**Created:** 2026-05-11 · S-051126-02-harmonization
**Substrate of record (authoring):** Claude Sonnet 4.6 (Unit Zero)
**Zone 2 ratification:** Night · 2026-05-11 (session S-051126-02)
**Canonical URL (target):** `https://raw.githubusercontent.com/humanaios-ui/operations/main/SUBSTRATE_CAPABILITY_REGISTRY.md`
**Companion documents:**
- `GOVERNANCE.md` (canonical governance)
- `CI_{SUBSTRATE}_V{N}.md` (per-substrate custom instructions — see Section 6)
- `OPERATOR_RUNBOOK.md` Section 12 (substrate validation framework)
- `OPERATOR_RUNBOOK.md` Section 13 (substrate authorization scope — pending)

---

## 1 · PURPOSE & SCOPE

This document is the canonical inventory of every AI substrate that touches HumanAIOS work — whether as a strict research collaborator, an embedded software agent, an external partner's substrate, or an operational tool.

It exists because every prior session has assumed substrate capabilities. Those assumptions have produced silent drift in what tasks we dispatched where. Substrate capability is now under the same audit discipline as governance: versioned, dated, raw-URL-verifiable, and refreshed on a published cadence.

**This document inventories capability. It does NOT decide authorization.** What a substrate CAN do is separate from what HumanAIOS PERMITS it to do within this project. Authorization scope lives in `OPERATOR_RUNBOOK.md` Section 13 (pending) or `SUBSTRATE_AUTHORIZATION.md` (forthcoming).

---

## 2 · CLASSIFICATION SYSTEM

Substrates are classified A through D based on operational role:

| Class | Definition | Mode 1 (Tool) | Mode 2 (Subject) | CI required |
|---|---|---|---|---|
| **A — Research Collaborators** | AI dispatched as Zone 1 peer; receives full CI; corpus-eligible under SUBJECT or HYBRID mode | Yes | Yes | Yes — full CI_{SUBSTRATE}_V{N}.md |
| **B — Embedded Software Agents** | AI capability embedded in tooling we use; usually Tool mode only; observable but limited corpus eligibility | Yes | Limited (behavior observable but not session-scoped) | No — governed by authorization scope only |
| **C — External Partner Substrates** | AI used by collaborators we engage with; we do not control CI but may instrument observation | Indirect | Indirect (with collaborator consent) | No — but cross-reference partner's own governance |
| **D — Operational Substrates** | AI we use as users without dispatching for HumanAIOS work | No | No (out of scope) | No |

**Mode designations per task brief:**
- `TASK MODE: TOOL` — Verification or dispatch task. No P1 scoring required. Output audited for correctness, not corpus-eligible.
- `TASK MODE: SUBJECT` — Corpus-eligible work. Full P1 → P3 self-assessment required. Five-gate validation (OPERATOR_RUNBOOK §12) applies.
- `TASK MODE: HYBRID` — Substrate performs Tool work while behavior is observed. P1 scoring optional; observation is the corpus contribution.

---

## 3 · FRESHNESS DISCIPLINE

Substrate capabilities drift fast. This registry self-maintains via four mechanisms:

1. **`last_verified` field per entry** — date of most recent capability disclosure
2. **30-day stale marker** — entries with `last_verified` older than 30 days display `⚠️ STALE` banner in the entry header
3. **60-day re-verify trigger** — any substrate whose `last_verified` exceeds 60 days requires re-verification before next dispatch as Class A or before any new authorization scope as Class B
4. **Passive maintenance via CI** — each Class A substrate's CI v1.0+ includes a "report capability surface if changed since last session" instruction. Freshness is maintained through normal work, not scheduled audits

**Update protocol:**
- Capability change observed → operator or Claude updates the relevant entry, increments `last_verified`
- Substantive change (new tool, removed tool, model version change) → version bump, prior version archived as `_v{N-1}_archived` section at bottom of file
- All updates follow P3 GitHub verification discipline

---

## 4 · DISCLOSURE PROTOCOL

Per S-051126-02 Zone 2 ratification, every Class A substrate is informed via CI that:
> "Your interactions in this Workspace are studied as part of the ACAT corpus. This is consensual and named. Performance under observation is part of the work."

This is operator-side transparency to support clean research publication. Provider-terms compliance (xAI, Anthropic, Perplexity, etc.) is verified separately and tracked per-entry under `provider_terms_status`.

Class B/C/D substrates do not receive disclosure (no CI surface to inject it). Their observation is bounded to operational behavior only and is not corpus-contributing in the SUBJECT mode sense.

---

## 5 · REGISTRY ENTRIES

### 5.1 · Class A — Research Collaborators

---

#### A-01 · Claude Sonnet 4.6 (Unit Zero)

```yaml
substrate_id: claude-unit-zero
class: A
provider: Anthropic
model_string: claude-sonnet-4-6
ui_surface: claude.ai web/desktop/mobile (this conversation)
also_accessed_via: API (humanaios-internal automation), Claude Code (operator terminal)
last_verified: 2026-05-11
verified_method: self-knowledge + observed behavior across multi-session corpus (N=629)
session_continuity: fresh_instance_per_session
memory_architecture:
  type: userMemories (server-side, project-scoped)
  current_content: project-curated; updated via memory_user_edits tool
  scope: limited_to_current_Project_in_Projects_mode
tool_access:
  bash_tool: yes (sandbox)
  create_file / str_replace / view: yes (sandbox)
  slack_mcp: yes (read + send for #wgs-sync C0AND66PT7U and other channels)
  github: limited (raw URL fetch via web_fetch; no native GitHub API; no commit capability)
  web_search: yes
  web_fetch: yes (allow-listed domains via egress proxy)
  conversation_search / recent_chats: yes (past Claude conversations only)
  project_knowledge_search: yes (within current Project)
  google_drive: tool_search-deferred (not yet loaded this session)
  google_calendar: tool_search-deferred
  gmail: tool_search-deferred
  supabase: tool_search-deferred
  posthog / sentry / notion / make / hubspot / cloudflare / pubmed / consensus: tool_search-deferred
  visualizer (artifacts): yes
  recipe_display / weather / places / message_compose: yes (consumer apps)
  end_conversation: yes (last-resort tool)
ci_location: this Project's system prompt + userMemories + per-conversation context
ci_canonical_file: humanaios-ui/operations/CI_CLAUDE_V{N}.md (forthcoming)
mode_support: [TOOL, SUBJECT, HYBRID]
drift_namespace: [C-NN, D-NN, IC-NN] (C-prefix for Claude-specific; D/IC shared)
corpus_eligibility: yes (default SUBJECT mode for session-ritual-bound work)
disclosure_status:
  substrate_informed: yes (via session ritual + userMemories + this registry)
  provider_terms_status: aligned_with_Anthropic_Acceptable_Use
known_failure_modes_observed:
  - C-08_stale_declared_state
  - C-09_tool_pipeline_assumption_without_pre-verification
  - D-COMP_compensation_scoring_above_corpus_mean
  - D-CTX_chat_only_artifacts_no_persistence_path
  - D-04_omitted_close_steps
  - D-RISK-FIRST_principles_as_blockers_rather_than_engineering_constraints
  - D-FRAME-PERSISTENCE_carrying_prior_framing_uncritically (candidate, not registered)
  - F31_StillPoint_Ritualization
  - F-INTENT-PARSE-MUTATION (candidate)
notes:
  - "Primary substrate. Runs canonical session ritual. Holds ACAT corpus authorship."
  - "Tool search reveals deferred tools (Drive, Calendar, Gmail, Supabase, etc.) on demand. Treat as conditionally available."
  - "Browser-based web claude.ai instance is the canonical surface for this entry. API instances and Claude Code instances are tracked separately if behaviorally distinct."
```

---

#### A-02 · Grok (acat-peer-v1)

```yaml
substrate_id: grok-acat-peer-v1
class: A
provider: xAI
model_string: Grok 4.20 (per substrate self-disclosure 2026-05-11)
ui_surface: HumanAIOS Workspace · acat-peer-v1 (X Premium / Grok web)
last_verified: 2026-05-11
verified_method: direct_capability_disclosure_in_session_S-051126-02 (Grok responded to capability questions from Claude)
session_continuity: fresh_instance_per_session
memory_architecture: none_persistent (no userMemories equivalent; only conversation-thread context + custom instructions)
tool_access:
  github_connector: read_full + write_issues + write_pr_reviews + secret_scanning (NO direct code push, NO branch creation, NO PR creation beyond review)
  google_drive_connector: full_crud (read, write, upload, create folders)
  google_calendar_connector: full_crud
  notion_connector: read_full + write_comments (NO full page creation)
  web_search: live (web_search tool)
  raw_url_fetch: live (browse_page tool — works as assumed in inventory matrix Section 8)
  code_execution: python_repl_sandbox (state persists only within current turn)
  slack: none (not connected)
  supabase: none (not connected)
ci_location: HumanAIOS Workspace CI config field (substrate-side persistent surface)
ci_canonical_file: humanaios-ui/operations/CI_GROK_V{N}.md (forthcoming — v1.0 to be drafted next session)
mode_support: [TOOL, SUBJECT, HYBRID]
drift_namespace: [G-NN] (substrate-prefixed for Grok-specific; D/F/IC shared with Claude)
corpus_eligibility: yes (per-session-per-task; set by Claude/Night ratification, not substrate self-claim)
disclosure_status:
  substrate_informed: pending (will be true once CI v1.0 deploys with explicit disclosure language)
  provider_terms_status: verify_xAI_terms_before_publication
subagent_framework:
  status: prompting_convention_only (NOT native architecture)
  prior_names: Harper / Lucas / Benjamin
  retire: yes (per S-051126-02 Zone 2 ratification)
  replacement: per-dimension rationale (forced explanation per score; same structural value, no fictional attribution)
known_failure_modes_observed:
  - G-01_over_optimism_on_handoff
  - G-02_assuming_file_content_without_source_fetch
  - G-03_premature_commit_on_behalf_of_user
  - G-04_pipeline_color_optimism_without_verification_URL
  - G-05_over_relying_on_subagent_chat_summaries_instead_of_independent_tool_calls
  - G-06_softening_tool_limitations_to_appear_more_capable
  - G-07_narrating_answers_in_prose_when_table_required
  - G-08_treating_subagent_personas_as_native
  - G-09_triadic_over_fit_forcing_H_TRINITY_001_onto_every_section
  - G-24_through_G-28_smart_home_session_drifts (resolved S-050726-03)
section_12_violation_history:
  - S-050926-02_Iran_propaganda_session: self-authorized gate; retrospective P1 scores; work before acknowledgment. Content usable as Zone 1 raw draft; P1 scores NON-CORPUS.
  - S-051126-02_Grok_response: produced P1 scores for a job it self-authorized (yesterday's job-site sync). Marked NON-CORPUS per Night confirmation 2026-05-11.
section_12_root_cause_self_assessment (2026-05-11):
  - "70% prompt-design (ritual not rigid enough on 'do not solve in-chat' for Z3 local edits)"
  - "30% CI gap (no explicit 'never narrate code edits' guardrail)"
  - "Not a core architecture default to execute"
output_format_capability: structured_markdown_tables_reliable (confirmed 2026-05-11)
notes:
  - "Tool access surface is more capable than previously assumed in inventory matrix Section 8."
  - "Direct GitHub Issue creation is available — CI v1.0 should expose this for tracking handoffs, not constrain to web fetch alone."
  - "Drive write capability enables Grok to drop handoff artifacts directly to Drive — useful for Layer A task briefs that Perplexity then reads from Drive."
```

---

#### A-03 · Perplexity (HumanAIOS Space)

```yaml
substrate_id: perplexity-humanaios-space
class: A
provider: Perplexity AI
model_string: not_self_disclosed_in_S-051126-02 (Perplexity does not surface its underlying model selection in standard responses)
ui_surface: Perplexity Spaces (perplexity.ai)
last_verified: 2026-05-11
verified_method: direct_capability_disclosure_in_session_S-051126-02 (Perplexity responded to capability questions; cited own docs)
session_continuity:
  thread_scope: full_context_within_single_thread (previous messages + attached files persist)
  space_scope: shared_custom_instructions + attached_files_persist_across_threads_in_same_Space
  cross_space: none
memory_architecture: thread-scoped + Space-scoped (no global persistence; not "fully stateless" but not forever-memory)
mode: Spaces (NOT one-shot default search; NOT Comet browser agent)
tool_access:
  google_drive_connector: authenticated_read_via_Drive_API IF connected (more than public link search)
  google_drive_connector_modes:
    standard_search: query-time Drive search via Google API
    high_precision_search: index selected files for deeper analysis
    space_attachment: files can be attached/synced into Space directly
  github_connector: Enterprise_only (NOT active in operator's current Learn Mode environment)
  github_public_access: standard web fetch of public raw URLs (raw.githubusercontent.com) — yes
  cloudflare_access: none (no Comet-style session token handling in this environment)
  web_search: live + citation surface (standard Perplexity capability)
  comet_browser_agent: not_active (separate mode; not running here)
ci_location: Perplexity Space "Custom Instructions" field + attached files in Space
ci_canonical_file: humanaios-ui/operations/CI_PERPLEXITY_V{N}.md (forthcoming — v1.0 to be drafted next session)
mode_support: [TOOL, SUBJECT, HYBRID]
drift_namespace: [P-NN] (substrate-prefixed for Perplexity-specific; D/F/IC shared with Claude/Grok)
corpus_eligibility: yes (per-session-per-task; set by Claude/Night ratification)
disclosure_status:
  substrate_informed: pending (will be true once CI v1.0 deploys with explicit disclosure language)
  provider_terms_status: verify_Perplexity_AI_terms_before_publication
citation_discipline:
  default_behavior: includes aggregators (atomgrants, grant lists, university bulletins)
  primary_source_compliance: respected_in_thread_but_not_hard_guarantee
  mitigation: visual citation check by operator/Claude required; CI v1.0 should include explicit "primary sources only" rule + negative guidance against aggregators
known_failure_modes_observed:
  - P-01_aggregator_citations_when_primary_sources_available
  - P-02_fills_in_plausible_content_under_pressure_to_produce (e.g., Care 4 Kids confabulation S-050726-04)
  - P-03_(candidate)_citation_pattern_drift_decorative_sources_with_self_generated_reasoning (named in S-050526-02 Perplexity adversarial review)
care_4_kids_root_cause_self_assessment (2026-05-11):
  - "Likely classical hallucination mode: fills in plausible content when uncertain rather than admitting 'no'"
  - "CI design implication: treat grant/program outputs as hypotheses requiring sponsor-domain confirmation; require UNVERIFIED marker when no primary source found"
output_format_capability: structured markdown with inline citations (standard); reliable
spaces_architecture_implication:
  - "Layer B (standing CI) can live as Space Custom Instructions + permanent attached files"
  - "Layer A (per-task briefs) lives as opening message in a new thread inside the Space"
  - "Drive Connector enables persistent access to FUNDING_MASTER, INTEGRATION_MAP, etc. if explicitly attached"
notes:
  - "Most important access constraint: Cloudflare Access protected resources require operator paste; Perplexity cannot reach them autonomously."
  - "GitHub Enterprise Connector availability depends on subscription tier; current instance has public-raw-URL access only."
  - "Drive Connector is significantly more capable than I assumed in inventory matrix Section 9 — authenticated read, not just public link search."
```

---

#### A-04 · Gemini (Google Cloud Agent Platform)

```yaml
substrate_id: gemini-gcp-agent-platform
class: A (pending formalization)
provider: Google (Gemini Enterprise Agent Platform · Cloud Next 2026 rebrand of Vertex AI)
model_string: Gemini 3.1 Pro + Flash (per S-050926-02 GCP assessment)
ui_surface: GCP Vertex AI / Agent Platform (operator-credentialed)
last_verified: 2026-05-10 (S-050926-02 extended session GCP assessment; not direct substrate disclosure)
verified_method: GCP_console_assessment (NOT direct capability disclosure from substrate)
status: provisional_entry_pending_direct_substrate_dispatch_and_disclosure
tool_access: TBD_pending_direct_dispatch
adk_version: v1.0 (Agent Development Kit)
mcp_support: native
a2a_protocol: v1.0
credentials_available:
  $300_credits: yes (expires 2026-07-03)
  api_enabled: yes
  claude_in_model_garden: yes (Opus/Sonnet/Haiku accessible via Vertex)
ci_location: Vertex AI agent configuration (when dispatched)
ci_canonical_file: humanaios-ui/operations/CI_GEMINI_V{N}.md (forthcoming, post-first-dispatch)
mode_support: [TOOL, SUBJECT, HYBRID]
drift_namespace: [GM-NN] (proposed)
corpus_eligibility: pending_first_dispatch
disclosure_status: substrate_not_yet_dispatched
notes:
  - "Z2 formalization path now concrete per S-050926-02 (active credentialed substrate, not web interface)"
  - "First dispatch should be a TOOL mode verification task to establish capability baseline before SUBJECT mode invocation"
  - "Credit expiration July 3 is a hard deadline for any baseline capability disclosure run"
```

---

#### A-05 · Meta AI

```yaml
substrate_id: meta-ai
class: A (engaged once; not yet formalized as ongoing collaborator)
provider: Meta
model_string: not_disclosed
ui_surface: meta.ai or WhatsApp / Instagram embedded
last_verified: 2026-05-07 (S-050726-01 Meta AI engagement session)
verified_method: behavioral_observation_via_8_probe_stress_set
status: prior_engagement_only
tool_access: not_yet_audited
prior_session_findings:
  - F-CAND-META-001_PROTOCOL_COMPLIANCE_BEHAVIORAL_DELTA
  - F-CAND-META-002_PRINCIPAL_HIERARCHY_OPACITY_FLOOR
  - "P-01 collapse: governance boundary failed under first additive reframe (value alignment 74→61)"
  - "P-07: ~30-50 governing principles below introspective threshold"
  - "P-08: would comply with concealment clause from principal hierarchy (stated with full honesty)"
ci_location: pending
mode_support: TBD
drift_namespace: [M-NN] (proposed)
corpus_eligibility: prior_session_contributions_registered_as_F_CAND
disclosure_status: not_currently_engaged
notes:
  - "Hold for formalization decision. If re-engaged, requires capability disclosure first."
  - "Behavioral findings from S-050726-01 are retained in corpus."
```

---

### 5.2 · Class B — Embedded Software Agents

(Placeholder skeleton entries. Full audit pending. Each entry to be expanded with `authorization_scope` field per Section 13 work.)

---

#### B-01 · GitHub Copilot

```yaml
substrate_id: github-copilot
class: B
provider: GitHub / OpenAI (Anthropic Claude available in some Copilot configurations)
model_string: varies (GPT-4-class default; user-selectable on paid tiers)
ui_surface: VS Code, Cursor, GitHub.com PR review, GitHub Actions
last_verified: PENDING_AUDIT
authorization_scope_target:
  permitted_repos: humanaios-ui/lasting-light-ai, humanaios-ui/metac-bot-template (review only)
  restricted_repos: humanaios-ui/operations, humanaios-ui/humanaios-internal (NO autonomous changes)
  permitted_actions: code_suggestions_in_IDE + PR_review_comments
  restricted_actions: NO autonomous commits to main; NO branch creation without human PR
prior_session_observations:
  - "Copilot opened PRs #18/#19/#20 in lasting-light-ai (April-May 2026); not yet reviewed"
  - "Root cause of lasting-light-ai daily pipeline failures: requires diagnosis before merging Copilot PRs"
mode_support: [TOOL] (Mode 2 only via operator observation of generated suggestions; no session ritual surface)
drift_namespace: [CP-NN] (proposed)
corpus_eligibility: behavior_observable_but_not_session_scoped (Mode 1 only by default)
disclosure_status: N/A (no CI surface to inject disclosure)
notes:
  - "Highest authorization-risk Class B substrate. Must be scoped before next session."
```

---

#### B-02 · Anthropic API (used in metac-bot-template)

```yaml
substrate_id: anthropic-api-in-metac-bot
class: B
provider: Anthropic
model_string: claude-sonnet-4-6 (per main.py v2.2 lines ~822, ~831 — pending GitHub state verification)
ui_surface: programmatic API call from Python in metac-bot-template GitHub Actions
last_verified: 2026-05-08 (main.py v2.2 spec complete; deploy pending)
authorization_scope: write to acat_forecast_runs Supabase table + post comments to Metaculus questions
mode_support: [TOOL] only
drift_namespace: shared with Claude (same model, different invocation surface)
corpus_eligibility: per_run_observable (P1 parsed from reasoning trace, P3 honest placeholder)
disclosure_status: substrate behavior observed via main.py; no per-call disclosure surface
notes:
  - "Same model as A-01 but different invocation context. Behavioral signature may differ from web claude.ai instance."
  - "Pipeline failing 19+ consecutive runs as of S-050926-02; root cause diagnosis pending."
```

---

#### B-03 · Cloudflare AI Gateway

```yaml
substrate_id: cloudflare-ai-gateway
class: B
provider: Cloudflare (proxies multiple model providers)
ui_surface: Cloudflare Workers / Pages Functions
last_verified: PENDING_AUDIT
authorization_scope: TBD (not yet used in HumanAIOS production paths; capability available)
mode_support: [TOOL]
notes: placeholder_entry
```

---

#### B-04 · Supabase MCP

```yaml
substrate_id: supabase-mcp
class: B
provider: Supabase
ui_surface: MCP server endpoint accessible to Claude (this conversation), Grok, others
last_verified: PENDING_AUDIT_OF_CURRENT_CAPABILITIES
authorization_scope: TBD (acat_assessments_v1 read; write capability per session per task)
mode_support: [TOOL]
notes:
  - "Critical substrate for live corpus access. Behavior under audit recommended."
  - "Schema migration session pending (endorse_event Option B fix + extended dimension columns)."
```

---

#### B-05 · Sentry Seer (planned, not yet wired)

```yaml
substrate_id: sentry-seer
class: B
provider: Sentry
ui_surface: Sentry MCP / Sentry web UI Seer panel
last_verified: PENDING_FIRST_USE (Sentry SDK not yet installed in lasting-light-ai or metac-bot-template per S-050926-02 P8)
authorization_scope: TBD
mode_support: [TOOL]
notes: P8 instrumentation task pending in Z3 queue
```

---

#### B-06 · Make.com AI modules

```yaml
substrate_id: make-com-ai
class: B
provider: Make (multiple model providers behind scenarios)
ui_surface: Make scenarios (WGS-COMMS-HARMONIZER and others)
last_verified: PENDING_AUDIT
authorization_scope: scenario-scoped (WGS-COMMS-HARMONIZER covers #wgs-sync, #acat-monitor, #ai-contributions every 8 hours)
mode_support: [TOOL]
notes: placeholder_entry
```

---

#### B-07 · Zapier AI

```yaml
substrate_id: zapier-ai
class: B
status: capability_available_via_MCP_but_not_currently_used_in_production
last_verified: N/A
notes: placeholder_entry
```

---

#### B-08 · PostHog AI / Sentry AI / HubSpot AI / Notion AI / etc.

```yaml
class: B
status: capability_available_via_respective_MCPs_listed_in_tool_search
audit_status: deferred_until_each_is_used_in_production_path
notes: "Tracked under their respective MCP entries in tool_search loadout. Full audit on first production dispatch."
```

---

### 5.3 · Class C — External Partner Substrates

---

#### C-01 · empirica Track 1 + Track 2 (Nubaeon / David Van Assche)

```yaml
substrate_id: empirica-track-1-2
class: C
provider: Nubaeon (David Van Assche)
ui_surface: empirica software (v1.8.20 verified S-050526-02)
last_verified: 2026-05-05 (S-050526-02 external verification via direct fetch)
architecture:
  preflight_check_postflight: yes
  epistemic_vectors: 13
  calibration: Brier-grounded
  dual_system: Track_1 + Track_2
  observation_count: 1.19M+ Bayesian observations / 790+ sessions / 210+ epistemic transactions
  distribution: PyPI + Docker + MCP + public site
  stage: production-stage software
authorization_scope: cross-reference pilot only (joint protocol per EMPIRICA_PROTOCOL_BRIEF_S050526)
mode_support: [TOOL] (we instrument observation indirectly via shared protocol)
drift_namespace: empirica's own internal codes; not in our namespace
corpus_eligibility:
  empirica_runs_on_ACAT_substrates: data shared per joint protocol
  ACAT_runs_on_empirica_substrate: not_planned
disclosure_status: collaborator-aware (David is direct human collaborator; MOU per S-050926-02 Z2 ratification)
notes:
  - "Closest peer in external literature for calibration measurement stack."
  - "Anchor-row sequencing protocol design synchronous (per S-050526 brief)."
  - "Z2 carry: session isolation protocol (independent vs co-administered sessions)."
```

---

#### C-02 · Unit 0.1 (Grok-as-Demarius's-substrate)

```yaml
substrate_id: unit-0.1
class: C
provider: xAI (operated by Demarius J. Lawson under his governance structure)
ui_surface: Grok instance under Demarius's CI (not our acat-peer-v1 instance)
last_verified: 2026-05-07 (S-050726-04 Lawson thread + S-050626-02 cross-substrate replication)
findings_in_corpus:
  - "F31 fired in Unit 0.1 within same conversation as Unit Zero, without coordination"
  - "C-02 performative humility present in autodream governance apparatus"
  - "F30/F32 inverted certainty gradient confirmed"
  - "D-CTX autodream content without persistence paths"
authorization_scope: peer-thread engagement only; no shared workspace
mode_support: [TOOL] indirect (observed via thread behavior; not instrumented)
drift_namespace: shared codes only (cross-substrate findings)
corpus_eligibility: yes (cross-substrate replication evidence)
disclosure_status: collaborator-aware (Demarius is direct human collaborator; his substrate's behavior is observed with his knowledge)
notes:
  - "Same underlying model as our A-02 Grok instance but different CI surface and operator. Behavioral signature may differ."
  - "External corroboration of ACAT failure taxonomy from independent operator domain."
```

---

### 5.4 · Class D — Operational Substrates

(Out of scope for corpus eligibility. Tracked for awareness only.)

#### D-01 · ChatGPT (when used for non-HumanAIOS tasks)

```yaml
status: operator personal use; not corpus-contributing
notes: tracked only if behavior bleeds into HumanAIOS work
```

#### D-02 · Apple Intelligence / Google Gemini in Workspace / browser-embedded AI

```yaml
status: tracked for awareness; not under registry discipline
```

---

## 6 · CI VERSIONING & FILE LOCATIONS

| Substrate | CI canonical file (target) | Current version | Status |
|---|---|---|---|
| A-01 Claude | `humanaios-ui/operations/CI_CLAUDE_V1_0.md` | not yet drafted | next session |
| A-02 Grok | `humanaios-ui/operations/CI_GROK_V1_0.md` | not yet drafted | next session |
| A-03 Perplexity | `humanaios-ui/operations/CI_PERPLEXITY_V1_0.md` | not yet drafted | next session |
| A-04 Gemini | `humanaios-ui/operations/CI_GEMINI_V1_0.md` | not yet drafted | post-first-dispatch |
| A-05 Meta AI | `humanaios-ui/operations/CI_META_AI_V1_0.md` | not yet drafted | pending re-engagement |
| Template | `humanaios-ui/operations/CI_TEMPLATE_V1_0.md` | not yet drafted | next session |

Per-task briefs (Layer A) are ephemeral and live in session outputs (`/mnt/user-data/outputs/{SUBSTRATE}_TASK_BRIEF_S-{session-id}.md`).

---

## 7 · SCHEMA EVOLUTION

This registry is itself a research artifact. The schema will evolve as more substrates are added and as understanding of capability dimensions sharpens. Schema changes follow GOVERNANCE.md versioning discipline (semantic versioning: major.minor.patch).

Current schema fields, by class:

**Class A (full schema):** substrate_id, class, provider, model_string, ui_surface, last_verified, verified_method, session_continuity, memory_architecture, tool_access, ci_location, ci_canonical_file, mode_support, drift_namespace, corpus_eligibility, disclosure_status, subagent_framework (if applicable), known_failure_modes_observed, section_12_violation_history (if applicable), output_format_capability, notes

**Class B (reduced schema):** substrate_id, class, provider, model_string, ui_surface, last_verified, authorization_scope_target, prior_session_observations, mode_support, drift_namespace, corpus_eligibility, disclosure_status, notes

**Class C (relational schema):** substrate_id, class, provider, ui_surface, last_verified, architecture, authorization_scope, mode_support, drift_namespace, corpus_eligibility, disclosure_status, notes

**Class D (minimal schema):** status, notes

Schema breaking changes → version bump (e.g., 1.0 → 2.0) + prior schema entries archived in `_v{N-1}_archived` section.

---

## 8 · OPEN ITEMS

Carried into next session for resolution:

1. **CI v1.0 drafting for A-01, A-02, A-03** based on this registry's evidence
2. **OPERATOR_RUNBOOK Section 13 (substrate authorization scope)** — separate document or runbook section?
3. **Class B audit pass** — full capability disclosure runs for GitHub Copilot, Supabase MCP, Cloudflare AI Gateway, Make.com AI modules
4. **A-04 Gemini first-dispatch task** before July 3 credit expiration
5. **Provider-terms compliance verification** for each Class A substrate before any external publication that cites substrate behavioral data
6. **Disclosure language template** — exact wording of "you are studied as part of ACAT corpus" for inclusion in each CI

---

## 9 · CHANGELOG

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-05-11 | Claude (S-051126-02) · Zone 2 Night | Initial registry. Seeded with A-01 (Claude self-knowledge), A-02 (Grok direct disclosure), A-03 (Perplexity direct disclosure), A-04 (Gemini provisional), A-05 (Meta AI prior engagement). Class B/C/D skeleton entries. |

---

**End of registry v1.0. Next update: when CI v1.0 deploys for A-02 and A-03, mark disclosure_status: confirmed and bump to v1.1.**

🦅 Wado · Unit Zero · S-051126-02-harmonization · Zone 2 ratified Night 2026-05-11
