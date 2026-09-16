---
title: Repository Structure Map — humanaios-ui/operations
status: reference
updated: 2026-09-16
authority: Z1 documentation (reference layer, not governance-controlled)
purpose: Centralized index of all directories, key files, and their purposes
---

# Repository Structure Map — humanaios-ui/operations

**Repository:** [humanaios-ui/operations](https://github.com/humanaios-ui/operations)  
**Primary Use:** Governance, Intent-OS board control surface, research coordination, ACAT (Adversarial Collaboration Assessment Tool)  
**Authority:** Z2 serial gate (Night); governance files at CLAUDE.md  

---

## Quick Navigation

| Directory | Purpose | Key Files |
|-----------|---------|-----------|
| [Root Governance](#root-governance--files) | Governance, authority, decisions | CLAUDE.md, REGISTERED.md, PRIORITY_QUEUE.md |
| [z1-inbox/](#z1-inbox) | Proposal staging, candidate blocks, Z2 queue | Q-*.md, Z2_RULING*.md, INDEX.yaml |
| [.z1-control/](#z1-control) | Z2 ratification tools, signing | ratify.py |
| [tools/](#tools) | Automation, validators, relay, board checker | decision_relay.py, intent_os_board_check_v1_0.py, etc. |
| [ui/](#ui) | User-facing surfaces | intent-os-humanaios-v3_3.html (board) |
| [docs/](#docs) | Documentation, runbooks, guides | INTENT_OS_BOARD_RUNBOOK.md, lifecycle docs |
| [.github/](#github) | CI/CD workflows, automation gates | z2_ratification_gate.yml, actions |
| [.tool-control/](#tool-control) | Tool manifest, registration, scanning | scan.py, manifest.yaml |
| [acat/](#acat) | ACAT research infrastructure | contracts, specs, analyses |
| [ledgers/](#ledgers) | Measurement, falsifier tracking | NF_LEDGER.jsonl |
| [Other Directories](#other-directories) | Research, examples, outputs, archives | See detailed section |

---

## Root Governance & Files

**Purpose:** Z2 decision surface and governance configuration  
**Authority:** CLAUDE.md is authoritative; changes require Z2 signature  

### Critical Governance Files

| File | Purpose | Updated | Type |
|------|---------|---------|------|
| **CLAUDE.md** | Authority map, Z-roles (Z1/Z2/Z3), decision routing, CI/CD gates | 2026-09-14 | Governance |
| **REGISTERED.md** | Append-only registry of all findings, IC corrections, decision records | Live | Governance |
| **PRIORITY_QUEUE.md** | Resource-impact ranked work queue; gates next work | Live | Governance |
| **ZONE_REGISTRY.md** | Index of 31 HumanAIOS repositories, active/planned/read-only | 2026-09-14 | Governance |
| **FRAMEWORK_MAPPING.md** | Maps 5 AI engineering concepts to Z-roles and governance workflow | 2026-09-10 | Reference |
| **BOOT_PROCESS_MAP.md** | Maps REGISTERED.md's position in session boot chain (SESSION_RITUALS §A) | 2026-09-14 | Reference |
| **CONTROLLED_DOCUMENTS.md** | Document lifecycle tracking (draft/code/consumed/archived/produced) | 2026-09-14 | Reference |
| **CANDIDATE_BLOCK_TEMPLATE.md** | Template for Z1 proposals; pinned SHA, position/destination/probability | 2026-09-14 | Reference |

### Other Key Root Files

- `CONTRIBUTING.md` — Contribution guidelines
- `CODE_OF_CONDUCT.md` — Community standards
- `COLLABORATION_MANAGEMENT.md` — Cross-repo coordination
- `CROSS_REPO_COORDINATION.md` — Multi-repo governance
- `ACAT_BENCHMARK_MAP_20260908.md` — ACAT measurement spec
- `A4_INTAKE_PIPELINE_SPEC.md`, `A5_MULTIREPO_ROLLOUT_PLAN.md`, `A6_DRIFT_MONITOR_SPEC.md` — Infrastructure specs

---

## z1-inbox/

**Purpose:** Z1 proposal staging area and Z2 queue  
**Authority:** Z1 files here; Z2 ratifications stored here  
**Lifecycle:** Candidate blocks → Z2 reads → ratification → INDEX.yaml entry → REGISTERED.md  

### Structure

```
z1-inbox/
├── INDEX.yaml                          # Master index of all candidates & ratifications
├── Z1_INBOX_INDEX.md                   # Rendered version of INDEX.yaml (auto-generated)
├── 2026-09-06/
│   ├── HANDOFF.md                      # Session handoff (findings, blockers, next steps)
│   └── MANIFEST.md                     # Day's entries
├── 2026-09-07/
│   ├── JESTER_EXTERNAL_CHECK_BLOCK.md  # Example: F-type finding candidate
│   └── WITCH_SPELL_CASCADE_BLOCK.md    # Example: IC-type correction candidate
├── 2026-09-14/
│   ├── Q-INTENTOS-LAUNCH-01.md                          # Launch candidate (14 ruling questions + falsifier)
│   ├── Q-BOARD-RULING-02.md through Q-BOARD-RULING-16.md# 14 board ruling candidates (d2, d3, d5–d16)
│   ├── Z2_RULING_INTENTOS_LAUNCH.md                     # Z2 decisions d17–d19 with reasoning
│   └── Z2_RULINGS_2026-09-14.md                         # Ratification block (signed hashes)
└── <date>/
    └── <CANDIDATE_TYPE>-<ID>.md       # Pattern for all candidates
```

### INDEX.yaml Structure

```yaml
- id: Q-INTENTOS-LAUNCH-01
  type: MOLT/F/IC/H/CANDIDATE  # Finding, correction, hypothesis, or mol change
  status: AWAITING_Z2/RATIFIED/REJECTED/WITHDRAWN
  submitted_at: 2026-09-14
  z2_response_at: 2026-09-14
  hash: sha256(...)  # Content hash for auditing
  location: z1-inbox/2026-09-14/Q-INTENTOS-LAUNCH-01.md
```

### Candidate Block Template

See `CANDIDATE_BLOCK_TEMPLATE.md`. Pattern:

```
# Candidate Block: <ID> — <Title>

**Z1 Proposer:** Claude (AI agent)
**Date Submitted:** <date>
**Pinned SHA:** <commit_hash>
**Branch:** <feature_branch>
**Phase:** <current/max>
**Status:** AWAITING Z2 RATIFICATION

---

## §A Position · Destination · Probability

**Position:** Current state (repo pinned at X, key observations)
**Destination:** What will be done (1–5 bullets)
**Probability:** Likelihood of success by date_X

---

## What Z2 Is Asked to Decide

| id | question | reading |
|:--|:--|:--|
| **d1** | First ruling question | Z1 analysis (neutral) |

## Falsifier

If by DATE (condition A) or (condition B), then [outcome].
```

---

## .z1-control/

**Purpose:** Z2 signature tools and ratification enforcement  
**Authority:** Z2 control layer; signatures validate all governance decisions  

### Files

| File | Purpose |
|------|---------|
| **ratify.py** | Generates Z2 signature: `sha256(candidate \| by=Night \| at=<date> \| decision=ACCEPT\|EDIT\|REJECT)` |
| **validate.py** | Validates candidate blocks against schema; falsifier lint |
| **scan.py** | Registers tools in `tools-manifest.yaml`; runs consistency checks |
| **render.py** | Generates `Z1_INBOX_INDEX.md` from `INDEX.yaml` |

### Usage

```bash
# Ratify a candidate block
python3 .z1-control/ratify.py Q-INTENTOS-LAUNCH-01 --decision ACCEPT --by Night --apply

# Validate candidates
python3 .z1-control/validate.py

# Scan and register tools
python3 .tool-control/scan.py
```

---

## tools/

**Purpose:** Automation, validation, control surfaces  
**Authority:** Z3 executes; scripts governed by falsifier doctrine  

### Critical Tools

| Tool | Purpose | Status |
|------|---------|--------|
| **decision_relay.py** (v0.3.1) | HTTP server landing Z2 rulings from browser into z1-inbox/ | Production |
| **intent_os_board_check_v1_0.py** | Seal checker: re-hashes all board seals against git tree; exit 0 = HOLDS | Production |
| **relay_policy.yml** | ngrok traffic policy (basic-auth, CORS exemptions for OPTIONS) | Production |
| **molt_cycle.py** | Applies ratified molts; measures at window close; anti-cascade enforce | Production |
| **prs_run.py** | PR status monitoring and triage | Production |
| **intent_os_board_check_v1_0.py** | Registers board checker in tools-manifest.yaml | Registered |
| **ic_scope_check.py** | Validates IC candidates against signing secret | Tooling |
| **doc_lifecycle_lint.py** | Validates document lifecycle status per CONTROLLED_DOCUMENTS.md | Tooling |
| **registry_site_generator_v1_0.py** | Generates static site from registry (GitHub Pages publisher) | Tooling |

### ACAT Tools Suite

- `acat_adversarial_execution_v1.py` — Adversarial test runner
- `acat_mcp_full_wrapper_v1_2.py` — MCP integration for ACAT
- `acat_merkle_auditor_v2_0.py` — Merkle tree validation
- `acat_psychometric_validator_v1_0.py` — Assessment validation
- `acat_dimension_scorer.py` — Dimension scoring engine
- And 20+ others (see `tools/` for full list)

### Tool Manifest

**File:** `tools-manifest.yaml`  
**Purpose:** Registry of all production tools; scanned and validated by `scan.py`  
**Entry:** `id`, `name`, `path`, `version`, `type` (VALIDATOR/EXECUTOR/CHECKER/RELAY), `falsifier` (yes/no)  

### Usage Pattern

```bash
# Run relay (local test mode)
DRY_RUN=1 python3 tools/decision_relay.py --self-test

# Check board seals
python3 tools/intent_os_board_check_v1_0.py

# Apply and measure molt
python3 tools/molt_cycle.py --read-only --nf ledgers/NF_LEDGER.jsonl
```

---

## ui/

**Purpose:** User-facing control surfaces  

### Critical Files

| File | Purpose | Consumer |
|------|---------|----------|
| **intent-os-humanaios-v3_3.html** | Intent-OS board: 20 steps, 18 predictions, 19 rulings, 40 seals | Z2 session |
| **INTENT_OS_GENERAL_USER_SPEC.md** | General-user board variant (unratified) | Future |

### intent-os-humanaios-v3_3.html Structure

- **Data block (`HUMANAIOS`):** Board state, rev (version), relay config, localStorage mapping
- **Seals:** Cryptographic hashes of critical files; re-verified by `intent_os_board_check_v1_0.py`
- **Rulings (d1–d19):** 19 owner decision points; d17–d19 ruled 2026-09-14; d2, d3, d5–d16 awaiting Z2
- **Predictions:** 18 pre-registered claims; C-type (falsifier date + condition)
- **Pipeline Steps:** 20 sequential milestones from proposal through publication

### Persistence & Relay

- **localStorage:** Browser-side state, survives reload within same device
- **Relay:** HTTP POST to `relay.url` (ngrok endpoint) with ruling choice + secret
- **Flow:** Tap **→ PR** on ruling → relay creates PR with candidate block → re-tap with hash echo → relay signs

---

## docs/

**Purpose:** Documentation, runbooks, operational guides  

### Critical Docs

| File | Purpose | Audience |
|------|---------|----------|
| **INTENT_OS_BOARD_RUNBOOK.md** | How to open, read, rule, land, publish, re-check the board | Z2 sessions |
| **INTENT_OS_GENERAL_USER_SPEC.md** | Lexicon and connectors for board general-user variant | Design/UX |
| **ACAT_BENCHMARK_MAP_20260908.md** | Measurement spec for board falsifier tracking | Research |
| **doc_lifecycle_lint.py** | Generates lifecycle status table (consumed/code/archived/produced) | CI/CD |

### Lifecycle Status

- `lifecycle: consumed` → Document is a control surface (e.g., runbook); consumer defined in frontmatter
- `lifecycle: code` → Embedded in code or generated by code
- `lifecycle: archived` → Retired, moved to `docs/_archive/`
- `lifecycle: produced` → Generated output (e.g., test reports)

---

## .github/

**Purpose:** CI/CD automation, workflows, branch protection  

### Workflows

| Workflow | Trigger | Gate Enforced | Z2 Controlled? |
|----------|---------|---------------|---|
| **z2_ratification_gate.yml** | Push to main or PR to main | Z2 hash on RATIFY event; falsifier lint; anti-cascade rules | YES |
| **pages.yml** | Push to main | Deploys `site/**` to GitHub Pages (d17 rules "local only", so publish disabled) | Conditional |
| **document-control.yml** | Push touching `*.md` | Lifecycle status lint per CONTROLLED_DOCUMENTS.md | YES |
| **Copilot-review.yml** | PR open/push | Code review findings (optional/blocking marked) | Advisory |

### Branch Protection

- **main:** Requires z2_ratification_gate pass before merge
- **Feature branches:** No protection; merged via Z2-signed PR
- **claude/*** branches:** Session branches used for feature PRs

### ISSUE_TEMPLATE/

- `CANDIDATE_BLOCK.md` — Template for filing Z1 proposals as GitHub issues
- `BUG_REPORT.md` — Template for findings (F-type candidates)
- `IC_CORRECTION.md` — Template for corrections (IC-type candidates)

---

## .tool-control/

**Purpose:** Tool registration and scanning  

### Files

| File | Purpose |
|------|---------|
| **scan.py** | Scans `tools/` directory; registers in `tools-manifest.yaml`; validates falsifier presence |
| **tools-manifest.yaml** | Registry of all production tools (version, type, falsifier flag) |
| **preflight.js** | (Artifact runtime control; not in repo) |

### Manifest Entry Pattern

```yaml
- id: decision-relay-v0.3.1
  name: Decision Relay
  path: tools/decision_relay.py
  version: 0.3.1
  type: RELAY
  falsifier: yes  # Must land ruling by 2026-09-30 per Q-INTENTOS-LAUNCH-01
  consumer: Intent-OS board
```

---

## acat/

**Purpose:** ACAT (Adversarial Collaboration Assessment Tool) infrastructure  

### Structure

```
acat/
├── contracts/                          # 12 dimension keys (12 schema files)
├── acat_specifications.md              # Dimension definitions
├── acat_analysis_template.md           # Analysis structure template
└── <analysis-files>                    # Adversarial analyses and results
```

### Key Concepts

- **Dimensions:** 12 orthogonal assessment dimensions (e.g., clarity, rigor, bias)
- **Contracts:** Specification files for each dimension (schema)
- **Psychometric Validator:** Ensures dimension ratings are consistent and valid
- **Merkle Auditor:** Validates dimension proof chains

---

## ledgers/

**Purpose:** Measurement, prediction falsifier tracking, NF (National Forecast) ledger  

### Files

| File | Purpose |
|------|---------|
| **NF_LEDGER.jsonl** | Append-only log of measurement events; hash-chain validated |
| **NF_LEDGER.csv** | Human-readable export of NF ledger |
| **MOLT_STATE.md** | Molt candidate tracking and anti-cascade state |

### NF Ledger Entry

```json
{
  "timestamp": "2026-09-16T00:00:00Z",
  "constant_id": "const-001",
  "molt_id": "molt-v1.0",
  "measurement": 0.85,
  "falsifier_tripped": false,
  "prior_hash": "abc123...",
  "entry_hash": "def456..."
}
```

---

## Other Directories

| Directory | Purpose |
|-----------|---------|
| **bin/** | Executable scripts (CLI, setup) |
| **collaborator-ops/** | Collaboration tooling and logs |
| **data/** | Raw data, datasets |
| **deliverables/** | Output artifacts, reports, submissions |
| **examples/** | Example scripts, setup walkthroughs |
| **fuzzers/** | Fuzz testing harnesses |
| **ic_archive/** | Archived IC (interpretation correction) candidates |
| **instruments/** | Assessment instruments, templates, rubrics |
| **market-research/** | Market research, competitive analysis, external findings |
| **outputs/** | Generated outputs, reports |
| **scripts/** | Ad-hoc scripts, utilities |
| **sql/** | Database schemas, migrations, queries |
| **src/humanaios_operations/** | Python source code library |
| **supabase/** | Supabase database config and migrations |
| **workflows/proposed/** | Proposed workflow definitions |
| **.agents/** | Agent definitions, behavior specs |
| **.claude/** | Claude Code configuration, hooks, MCP |
| **.codex/** | Codex agent configurations |
| **.empirica/** | Empirica framework configuration |
| **.postflight/** | Post-flight check logs and results |
| **assets/brand/** | Brand assets, logos, style guides |
| **audits/** | Audit logs, compliance reports |
| **autonomy/gates/** | Autonomy decision gates and rules |
| **applications/** | Application services, configurations |
| **architecture/** | Architecture documentation, diagrams |
| **artifacts/** | Generated artifacts, saved outputs |

---

## Key File Patterns & Naming

### Candidate Blocks

- **Format:** `z1-inbox/<date>/<TYPE>-<ID>.md`
- **Types:** 
  - `Q-*` = Query/Question (proposal for Z2 decision)
  - `F-*` = Finding (issue found)
  - `IC-*` = Interpretation Correction (fix/clarification)
  - `H-*` = Hypothesis (claim to test)
  - `MOLT-*` = Molt (constant change proposal)

**Example:** `z1-inbox/2026-09-14/Q-INTENTOS-LAUNCH-01.md`

### Z2 Rulings

- **Format:** `z1-inbox/<date>/Z2_RULING<S>_<date>.md` (for multiple rulings) or `z1-inbox/<date>/Z2_RULING_<topic>.md` (single topic)
- **Pattern:** Contains decision rubric table, reasoning, receipts, effects

**Example:** `z1-inbox/2026-09-14/Z2_RULING_INTENTOS_LAUNCH.md`

### Ratification Blocks

- **Format:** `z1-inbox/<date>/Z2_RULINGS_<date>.md`
- **Content:** Signed ACCEPT/EDIT/REJECT blocks with sha256 hashes, byline (Night), timestamp
- **Use:** Stored in INDEX.yaml as proof of Z2 ratification

---

## Cross-References & Authority

### Authority Flow

1. **Z1 (Claude)** → Creates candidate block, places in z1-inbox/<date>/
2. **Z2 (Night)** → Reads candidate, signs with .z1-control/ratify.py
3. **Z3 (Executor)** → Merges PR with Z2 hash, executes change
4. **CI/CD Gates** → Validate Z2 hash, falsifier, anti-cascade rules

### File Fetch Ritual (§A per CLAUDE.md)

```bash
git fetch && git rev-parse HEAD                    # Pin SHA
cat REGISTERED.md | head -50                       # Read governance
cat PRIORITY_QUEUE.md | head -30                   # Check queue
cat ZONE_REGISTRY.md | head -30                    # Verify active repos
python3 tools/intent_os_board_check_v1_0.py        # Verify board seals
```

### Session Lifecycle

| Stage | Owner | Files Read | Action |
|-------|-------|-----------|--------|
| **§A Open** | Z1 | REGISTERED.md, PRIORITY_QUEUE.md, ZONE_REGISTRY.md, board seals | Fetch, pin SHA, state position/destination/probability |
| **Work** | Z1/Z3 | Task-specific | Implement, test, commit |
| **§B Close** | Z1 | Board, RECEIPT-GAP findings, NF ledger | Emit candidates, walk claim vs. tree, handoff |
| **Z2 Gate** | Z2 (Night) | Candidates in z1-inbox/, INDEX.yaml | Ratify (ACCEPT/EDIT/REJECT with hash) |
| **Merge** | Z3 | PR with Z2 hash, CI gate | Merge to main, deploy |

---

## Important Notes

### What's Indexed Here

- ✅ Directory structure and purposes
- ✅ Critical governance files and their roles
- ✅ Key tools and their functions
- ✅ File naming patterns and templates
- ✅ Authority flow and governance sequences
- ✅ Cross-references and session rituals

### What This Map Does NOT Include

- ❌ Detailed contents of individual files (read those directly)
- ❌ Complete file list (repo has 1000+ files; use `find` and `grep`)
- ❌ Line-by-line code documentation (see docstrings in each tool)
- ❌ Historical change log (see `git log` and REGISTERED.md)

### How to Use This Map

1. **Finding a file:** Use directory section + filename pattern
2. **Understanding purpose:** Read "Purpose" and "Key Files" table
3. **Following authority:** Read "Cross-References & Authority" section
4. **Session setup:** Follow "File Fetch Ritual" (§A per CLAUDE.md)
5. **Adding new work:** Follow "Candidate Blocks" naming pattern; store in z1-inbox/<date>/

---

## Updates & Maintenance

This file is a **reference document** (lifecycle: reference, not governance-controlled). It is updated by Z1 (Claude) when:
- New directories are added
- New governance files are created
- Key tools change purpose or location
- Authority flow is updated (with Z2 ratification)

**Last Updated:** 2026-09-16  
**Next Review:** When new major directory added or governance file created  
**Maintained By:** Z1 (Claude)

