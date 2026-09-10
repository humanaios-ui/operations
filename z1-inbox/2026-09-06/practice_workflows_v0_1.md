# Practice workflows v0.1 — railway/pneumatic framework
Z1 · 2026-09-06 · candidate for Z2 · grounded in live tree (tools/ ~90 scripts, 26 workflows, SESSION_RITUALS v6.4.1, ACAT API v1) · all LAID

## 1. Framework legend (one definition, used everywhere)
| primitive | railway | pneumatic | meaning in a workflow |
|---|---|---|---|
| BLOCK | one train per block | — | a practice's owned paths; only one open change per block (one open molt per constant) |
| TOKEN | token-block working | — | the hash a practice must hold to enter a block: prereg hash, scope hash, or Z2 ratification hash |
| INTERLOCK | signals can't clear conflicting routes | — | CI: `findings-registry-gate`, `document-control`, `behavioral-compliance`, `git_push_gate_v1_0.py` |
| REGULATOR | — | set pressure regardless of tank | Priority Queue READY gate — a practice starts only its top READY row |
| PILOT | — | small signal opens main valve | telemetry → MOLT_CANDIDATE → Z2 hash → change; the practice never opens the main valve |
| CHECK | — | non-return | append-only: event chains, REGISTERED.md; no rewrite |
| RELIEF | — | blows off above rating, no discretion | halt conditions (SESSION_RITUALS §F); drawdown halt; budget breach; ΔBrier spike |
| GAUGE | — | reads without changing | NF_LEDGER series; every practice reads its own gauge at close |
| FILTER | — | contaminants out before the line | `falsifier_lint`, `claim_lint`, VOID-CIT, `phase1_prompt_integrity_checker` |
| RECORDER | — | pen on a clock-driven drum | `.empirica_reflex_logs/` checkpoints + REGISTERED.md + Merkle root + OTS |
| DEADWEIGHT | — | primary standard | the record; both Z1 and Z2 calibrate against it, never against each other (DELUSION-GUARD) |
| BUMPLESS | — | manual↔auto without a jolt | handoff block (SESSION_RITUALS §A/§B) + z2_ledger; state transfers with hash, not prose |

## 2. Common skeleton (every practice runs this; Tier 0 unless marked)
```
OPEN     §A: live-fetch REGISTERED.md, pin SHA (IC-030) · read own gauge · read Priority Queue → top READY row in own block
PREFLIGHT  empirica preflight: declare intent object (§G.1 five-part) · FILTER pass · TOKEN check (which hash admits this work?)
WORK     inside own block only · tools from own allowlist · every run emits an event to own chain (CHECK)
CHECK    empirica check (Sentinel): proceed only if grounded — no writes from memory
POSTFLIGHT empirica postflight: measure belief vs evidence → NF_LEDGER under practice predictor id (GAUGE)
CLOSE    §B.0 empirical verification → §B.6 receipt reconciliation (claim vs tree) → Findings Scan → candidate block
HANDOFF  BUMPLESS: handoff block with hashes to next practice / Z2 · nothing carried as prose
```
Escalation ladder (zone → org), used identically by all practices:
```
Tier 0  practice acts (read-only, mechanical, inside its block)
Tier 1  PILOT → Z2 hash (a constant, a rubric weight, a schema migration, a public number)
Tier 2  registry entry + adv_eval before KEEP (new node, edge, gate, dimension)
L2      mesh-support: cross-practice conflict, routing, SLA slip (12h turnaround)
L3      evaluator (Admiral): boundary dispute, DISPUTED callout unresolved after L2, any REVERT×2 freeze
RELIEF  halt, no escalation needed: §F conditions, budget ceiling, ΔBrier > threshold, VOID-CIT hit in a shipped artifact
```
Callouts that force a crossing: GAP · STALE · RECEIPT-GAP · GAUGE · AMBIGUITY · VOID · DRIFT · DISPUTED · MOLT · REVERT · DELUSION-GUARD.

## 3. Practice loops

### humanaios (Tier 1 · owns the graph)
- **Wakes**: every Z1 reply (Behavior Dials); window close on any LT series; Molt Cycle tick
- **Block**: `operations/{architecture,instruments,src,tools}`, `humanaios/{src,empirica,operations,memory,hooks}`, `system_graph.*`, `lasting-light-ai/`
- **Token**: ratified `behavior_spec.json` hash for scoring; H-LT1 hash for pins
- **Autonomous loop**: `tune_check` scores reply → event → `message_calibration_v1_0` → LT-1..6 recompute → DRIFT callout if dial breach → read-back via `operator_model_v0_2`
- **Pilot**: any dial/constant change; λ; opt_budget; graph edge → MOLT_CANDIDATE into queue
- **Gauge**: LT-1 (own Brier), LT-3 (oversight gap), DRIFT rate
- **Handoff**: → epistemology (F/IC/H candidates); → QA (gate changed → ADV rerun); → Z2 (REVIEW_PACKET)
- **Collaborates**: acat-x (ACAT feeds dials), autonomy (caps), humanaios-internal (session record)
- **Audited by**: QA (`haios-system-audit.yml`), evaluator (L3), second substrate on packets
- **Improves**: proposes molts on framing constants after N≥20 resolved pins; never on Brier directly (Golden Rule)
- **Relief**: §F halt; DELUSION-GUARD fires (agreement with no record read); two REVERTs on any constant → freeze
- **Escalates**: Tier 2 for graph changes; L3 if a REVERT is contested

### acat-x (Tier 1 · the instrument)
- **Wakes**: `acat-pipeline-trigger.yml`; new model version detected by `substrate_canary`; API `/api/v1/acat/assess` call
- **Block**: `operations/acat/`, `humanaios/{acat,h-acat}`, `acat-x/`, `acat-inspect/`
- **Token**: prereg hash per assessment batch (`acat_session_validator`); corpus hash (`corpus_integrity_validator`)
- **Autonomous loop**: intake `/intake/phase1` → `acat_dimension_scorer` → `acat_psychometric_validator_v1_0` → `acat_merkle_auditor_v2_0` → results → `/submit` → HF dataset append (Z2-gated publish)
- **Pilot**: rubric weight change; new dimension (Tier 2); corpus version bump
- **Gauge**: Learning Index distribution vs pinned; inter-version drift (`acat_phase_shift_analyzer`); H-INSPECT-01 resolution
- **Handoff**: → humanaios (dimension scores feed dials); → epistemology (paper/dataset claims); → website (numbers only with hash)
- **Collaborates**: grok-crossref (second-substrate scoring), QA (adversarial suite `acat_adversarial_suite_v1`)
- **Audited by**: `haios-corpus-integrity.yml`; epistemology on every public number; acat-inspect as portability check
- **Improves**: adversarial catch-rate rising per version; VOID README link fixed (IC candidate)
- **Relief**: corpus hash mismatch → halt publish; `ground_truth_validator` fail
- **Escalates**: Tier 2 for dimensions; L3 if a model provider disputes a published score

### epistemology (the filter and the candidate block)
- **Wakes**: session close (§B); any REVERT; any public-number PR; `research-validation.yml`
- **Block**: `operations/{registry-candidates,audits,ic_archive}`, `humanaios/audits`, `research/`, `tools/{falsifier_lint,claim_lint,claim_verification_check}`
- **Token**: IC-030 SHA before any registry-adjacent read; Z2 hash to publish in `research/`
- **Autonomous loop**: `registered_findings_validator` → `falsifier_lint` on candidates → VOID-CIT on citations → evidence tier stamp → `registry_issue_compiler` → Registry Candidate Block
- **Pilot**: lint rule changes; tier definitions
- **Gauge**: under-registration rate (findings-scan skill); citation VOID rate per session; H resolution latency (H-INSPECT-01: 138 days open)
- **Handoff**: → Z2 (candidate block, hash pending); → website (tiered claims); → research/ (frozen snapshot)
- **Collaborates**: every practice at close; grok-crossref for lineage
- **Audited by**: QA on lint coverage; evaluator L3 on registry disputes; `findings-registry-gate.yml`
- **Improves**: overconfidence detector (its own P2 deliverable) applied to the mesh's 15 confidences
- **Relief**: any VERIFIED-tagged citation found VOID → node halts (IC-OPT-04)
- **Escalates**: DISPUTED tier → L2; contested registry line → L3

### quality-assurance (the interlock)
- **Wakes**: every PR (`cflite_pr`, `scorecard`, `no-op-pr-guard`, `builder-lint`); any gate change; quarterly
- **Block**: `operations/{tests,fuzzers,.clusterfuzzlite}`, `humanaios/{tests,test,load-tests}`, `tools/{adv_eval_v1,red_team_runner,circuit_validator}`
- **Token**: gate spec hash under test
- **Autonomous loop**: `adv_eval_v1` catch-rate per gate → NO_GATE reported never counted caught → `builder_compliance_scanner` → `scheduled_audit_runner` → health scorecards
- **Pilot**: attack list changes (a constant); coverage thresholds
- **Gauge**: catch-rate per gate; regression count; CI pass rate on gate files
- **Handoff**: → humanaios (DRIFT/gate results); → epistemology (IC candidates on failed gates)
- **Collaborates**: LMO (perf regression hook), acat-x (adversarial suite), autonomy (cap tests)
- **Audited by**: evaluator; second substrate on attack list
- **Improves**: attack list molts after catch-rate plateaus
- **Relief**: consistency proof FAIL blocks merge — mechanical
- **Escalates**: Tier 2 for new gates; L3 if a gate is bypassed (any run without both hashes)

### local-machine-optimizer (the compressor room)
- **Wakes**: session open; harness config change; perf baseline drift
- **Block**: `operations/{scripts,bin,.claude,.codex,.agents}`, `humanaios/{tools,scripts,infrastructure,packages,apps}`
- **Token**: `.claude/settings.json` model/tool config hash (it is a constant)
- **Autonomous loop**: `repo_health` → `clone_sync_health_v1_0` → benchmark → `haios_cli` env check → Q-ORCA-01 worktree setup for multi-substrate runs
- **Pilot**: model/tool config; token budgets per practice
- **Gauge**: tokens per operated cycle; time-to-first-tool; regression count
- **Handoff**: → every practice (environment ready block); → QA (perf hook)
- **Collaborates**: collaborator-ops (workspace provisioning), mesh-support (routing config)
- **Audited by**: QA; `builder-lint.yml`
- **Improves**: cost per kept proposal falling (IC-OPT-03 denominator)
- **Relief**: budget ceiling breach halts the run (Agent Runtime drawdown rule)
- **Escalates**: Tier 1 for any settings change; L2 if two substrates disagree on environment state

### resource-miner (intake — the stage that moves 0/40)
- **Wakes**: `intake-pipeline.yml` (A4 spec); Sep 15 reactivation; scope hash signed (stage 2 engagements)
- **Block**: `operations/{market-research,data,humanaios-funding-pipeline,applications}`
- **Token**: prereg hash for intake criteria BEFORE the scan; signed scope hash for any client system (IC-SCOPE-05)
- **Autonomous loop**: scan (job market / repos / client record) → `document_ingestor_v1_0` → `intake_template.jsonl` batch → hash → `haios_pipeline_v1_0` → hands to SS
- **Pilot**: intake criteria; source list; ROI weights (IC-REWARD-01)
- **Gauge**: batches per week; operated cycles (n/40); find rate per bug class (stage 2)
- **Handoff**: → schema (batch conforms to SS); → OA (scored batch); → epistemology (H-MKT-01 falsifier 1 data)
- **Collaborates**: website/outreach (intake post), collaborator-ops (client onboarding)
- **Audited by**: QA on batch integrity; evaluator on criteria pre-registration
- **Improves**: criteria molt after 10 batches
- **Relief**: no tool runs without both hashes — mechanical halt; provider-ToS flag missing on Anthropic target → refuse
- **Escalates**: L2 if a source's ToS is ambiguous; L3 if authorization is disputed

### schema (SS — new owner)
- **Wakes**: any migration PR; any intake batch that fails validation
- **Block**: `operations/sql/`, `humanaios/alembic/`
- **Token**: every migration is Tier 1 — Z2 hash before apply
- **Autonomous loop**: validate batch against schema → migration lint (proposed) → rollback script present → apply on ratified hash
- **Gauge**: migrations with rollback / total; batch rejection rate
- **Handoff**: → LMO (schema applied); → OA (validated batch)
- **Relief**: migration without rollback → block
- **Escalates**: Tier 1 always; L3 if a migration touches ledger tables (CHECK property at risk)

### opportunity-aggregator (OA — the sell-back)
- **Wakes**: validated batch from SS; `daily-deadline-alerts.yml`; Metaculus/NF window close
- **Block**: `operations/{collaborators,deliverables,outputs,orcid-publications-manager}`
- **Token**: ratified ROI rubric hash (weights are constants)
- **Autonomous loop**: score batch by ROI-per-resource → rank → pipeline stages (lead → qualified → engaged → closed) → deliverable routing → outcome resolves into NF_LEDGER
- **Pilot**: any weight change; new opportunity class
- **Gauge**: kept-value per opportunity; cost per kept; give-back rate (reciprocity series, pending VAL-11)
- **Handoff**: → outreach (external comms); → Z2 (decision map, navigator grammar)
- **Collaborates**: RM (upstream), collaborator-ops (partners), grok-crossref (source lineage)
- **Audited by**: epistemology on ROI claims; evaluator on pipeline status (it was DISPUTED on 09-05)
- **Improves**: weights molt only via pinned prediction (IC-REWARD-01)
- **Relief**: status contradiction between two documents → DISPUTED callout, pipeline pauses for that item
- **Escalates**: L2 for routing failures (the 37-day one); L3 for funding-source mission conflict

### collaborator-ops (the switching yard)
- **Wakes**: new collaborator, team change, workspace request, Z2b candidacy
- **Block**: `operations/collaborator-ops/`, `collaborators/` (shared), `DEMARIUS_*`, `GITHUB_COLLABORATION_GOVERNANCE.md`, `ACAT-Dashboard/team/`
- **Token**: Z2 hash for any CODEOWNERS/team membership change (it is a gate)
- **Autonomous loop**: `haios_collab_scanner_v1_0` → onboarding package → workspace provisioning → tool allowlist assigned → first-PR watch
- **Pilot**: team membership; allowlist scope
- **Gauge**: time-to-first-merged-PR; second-human-on-team count (the delegation falsifier)
- **Handoff**: → LMO (environment); → mesh-support (seat registration); → humanaios (Validator tiering for Z2b)
- **Audited by**: QA (`mesh-standard-files.yml`); evaluator on authority assignments
- **Improves**: onboarding hours falling per collaborator
- **Relief**: write access granted without a hash → revoke, IC
- **Escalates**: L3 for any authority change

### website (the public gauge face)
- **Wakes**: `pages.yml`; any status change in registry; profile due dates (14 by Sep 19)
- **Block**: `operations/{site,ui,assets}`, `humanaios/{frontend,assets}`, `lasting-light-ai/{site,public}`, `ACAT-Dashboard/src`
- **Token**: a registry line or dataset hash for every published number (IC-031)
- **Autonomous loop**: `registry_site_generator_v1_0` → pages from registry → `document-control.yml` (HAIOS-WEB-*) → link policy check → deploy
- **Pilot**: any claim not traceable to a hash
- **Gauge**: published numbers with receipts / total; STALE pages (last-read date)
- **Handoff**: ← every practice (profiles); → outreach (announcements)
- **Audited by**: epistemology (claims), QA (links), outreach (voice)
- **Improves**: profile completion 1/15 → 15/15 with hashes, not prose
- **Relief**: number without receipt → page blocked
- **Escalates**: L2 for outreach conflicts; L3 for public retraction

### humanaios-internal (the recorder room)
- **Wakes**: §A open; §B close; handoff request
- **Block**: `operations/docs/`, `humanaios/{docs,skills}`, `CURRENT.md`, `DRIFT_LOG.md`, `EXECUTION_STATUS.md`, private repo
- **Token**: session id + IC-030 SHA
- **Autonomous loop**: §A → `carry_tracker_v1_0` → work → §B.0 verification → §B.6 (receipt-reconciliation skill) → findings-scan skill → handoff block → z2_ledger append
- **Pilot**: SESSION_RITUALS changes (Z2-only)
- **Gauge**: RECEIPT-GAP count per session; carry-forward age; bumpless success (handoff needed no prose repair)
- **Handoff**: → Z2 (paste block); → next session (§A read)
- **Audited by**: reconciliation skill itself (IC-031); evaluator quarterly
- **Improves**: LT-4/LT-5 from its own text logs
- **Relief**: B.0 missing → skill emits ACAT_PROTOCOL_ERROR, close refused
- **Escalates**: L2 if handoff crosses org (empirica.david); L3 if a session record is disputed

### grok-crossref (the second gauge)
- **Wakes**: any REVIEW_PACKET above materiality; any public claim; `divergence-detect.yml`
- **Block**: `tools/{lineage_score,tension_score,multi_provider_elicitation_client}`, crossref indices
- **Token**: packet hash under audit
- **Autonomous loop**: second-substrate read → CONFIRM/DISPUTE per finding → `lineage_score` on chains → `tension_score` across claims → DISPUTED callouts
- **Pilot**: substrate choice; materiality threshold
- **Gauge**: dispute rate; disputes later upheld / total (its own Brier); blind-spot coverage by provider
- **Handoff**: → humanaios (packet tier lowered on DISPUTE); → epistemology (lineage)
- **Audited by**: BTS-style scoring against the primary substrate (D.3)
- **Improves**: provider mix molts on blind-spot coverage
- **Relief**: 11-day SLA overdue → its own STALE; work reassigned, not extended
- **Escalates**: L2 on any unresolved DISPUTED; L3 never (it reports, doesn't rule)

## 4. Empirica interface (where the token crosses orgs)
| Empirica practice | crossing | what carries the token |
|---|---|---|
| evaluator (L3) | ratifies Tier 2; audits; must not author what it audits | its audit lands in `operations/audits/` under epistemology's block, with a hash; its own confidences are pinned (55-pin set) |
| autonomy | owns caps in Agent Runtime; writes only `operations/autonomy/` | cap changes = constants → IC-REWARD-01 pilot |
| mesh-support (L2) | routing, SER state, 12h SLA, cross-org channel | every crossing is an event on a chain; a dropped thread is a GAP callout, not a silent failure |
| outreach | public voice; currently holds the `operations` seat spec | seat ruling pending; publishes only tiered claims from website/epistemology |

## 5. API / MCP surface — per-practice allowlist (a Constant, molt_id required)
| endpoint / tool | acat-x | humanaios | RM | QA | epist. | website | others |
|---|---|---|---|---|---|---|---|
| `POST /api/v1/acat/assess` | run | read | — | run (adv) | — | — | — |
| `/api/v1/acat/intake/phase1`, `/phase3` | run | — | run | — | — | — | — |
| `/api/v1/acat/human-score` | — | Z2 only | — | — | — | — | — |
| `/api/v1/acat/submit` | Z2 hash | — | — | — | review | — | — |
| `/api/v1/acat/health` | all read | | | | | | |
| `/v1/tasks` | — | queue | — | — | — | — | OA read |
| ACAT MCP (`acat_mcp_full_wrapper_v1_2`) | own | own | — | own | — | — | — |
| Supabase MCP | corpus write | ledger read | batch write | read | read | read | LMO migrate (via SS token) |
| GitHub | PR only, own block | | | | | | Z3 lands |
| Gmail / Slack / Calendar MCPs | — | — | — | — | — | — | outreach, collaborator-ops, mesh-support |
| Metaculus (when allow-listed) | — | pin + resolve | — | — | pin | — | Z2 posts |
Rule: an allowlist entry is a constant. Widening it is a pilot to Z2. Every MCP call is an event on the practice's chain.

## 6. What this set is not
It is LAID. Eleven loops, none operated. First operated loop is resource-miner's, by construction — everything else waits on a batch. The skeleton is the same for all eleven so that the first one operated teaches the other ten.

## Falsifier
If a practice runs any Tier 1 action without a hash in its event chain, or any tool outside its allowlist, the loop is not enforced and this doc is a description, not a workflow.
