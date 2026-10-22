---
doc_id: HAIOS-PROC-006
title: "Founder's Ultimate Users Manual and Troubleshooting Guide for HumanAIOS"
area: PROC
canonical_repo: operations
canonical_path: docs/FOUNDERS_MANUAL.md
status: draft
---

# Founder's Ultimate Users Manual and Troubleshooting Guide for HumanAIOS

**Status:** Draft v0.2 (2026-10-17). Checked against `operations` at `c05ff89`. Sources: the operations repo, six product repos (`humanaios-internal` not retrieved), and Google Drive.

Tags used below:
- **[verified]**: checked in the repo at `c05ff89` on 2026-10-17.
- **[unverified]**: from Drive or an outside source, not checked here.
- **[recommended]**: proposed, does not exist yet.

---

## 1. Front door

HumanAIOS is a federated system of code, governance, research, human approval, and evidence. It is not one app.

The core chain:

**human intent → INTENT-OS → Resource Miner → human review → Repository Coordinator → protected CI → Z2 ratification → authorized action → outcome evidence.**

The most important rule:

> **Do not collapse discovery, evidence, admission, approval, and execution into one step.**

`humanaios-ui/operations` is the control plane. It holds governance, INTENT-OS, Resource Miner, the Repository Coordinator, CI gates, registries, and runbooks. Work governance here.

Read in this order:

1. `SEED.md` and `PRINCIPLES_SEED_V1_0.md`: identity and principles.
2. `CLAUDE.md`: who decides, who proposes, who executes.
3. `SESSION_RITUALS.md`: how a session opens and closes.
4. `REGISTERED.md`: the append-only registry of findings (F), corrections (IC), and hypotheses (H).

### Current state (checked 2026-10-20)

This is a snapshot. Re-check before acting on it.

- **PR backlog.** Several PRs are blocked by CI and merge issues. Work is queued, not lost.
- **#910 (manual v0.2 draft).** Merged as `ad44c46f`. Its admission check failed at merge. The admission record is missing. Standing is a human decision.
- **#913 (reconcile fix and manual update).** Open, not draft. Head `ed3fa746`. `mergeable_state` is `unstable`. The `Repository admission/backpressure gate` check fails: no admission record. Admission is a human decision. Do not post admit commands on the author's behalf.
- **Reconcile bug.** The daily `resource-miner-scan.yml` calls `reconcile`. The parser lacked that subcommand. The fix is on `6ec0e37b` and in #913. It is not verified until a scheduled run goes green after merge.
- **Coordinator checks on #913.** `observe` passes. `inspect` passes on the latest head. Other coordinator apply jobs skip by design.
- **Harness.** RED. `repo_health.py` and `validate_skills.py` reject `--smoke-test`. One Metaculus check is missing `forecasting_tools`.
- **Board.** `intent_os_board_check` returns STALE (see section 13).
- **Coordinator index.** Reported degraded at older head `3dea9a46`. The current advisory index build passes on `ed3fa746`.
- **Operational acceptance.** 21 checks are UNVERIFIED. Do not cite them as passed.
- **Drive copy.** Old v0.1 Google Doc trashed on 2026-10-20. Google Doc v0.2 is a snapshot and may lag this file. The Claude Doc is the live copy.

---

## 2. Roles

| Role | Who | Does | Does not |
|---|---|---|---|
| **Admiral / Z2 (ratifier)** | Carly R. Anderson (Night) | Accepts, edits, or rejects proposals. Signs ratification hashes. Sets zone assignments. | Execute ratified work. Propose new work. |
| **Z1 (proposer)** | Claude, plus practice teams | Reads the registry. Drafts candidate blocks. Flags blockers. | Merge or ratify its own work. |
| **Z3 (executor)** | Per-repo executors (many TBD) | Lands ratified changes. Runs experiments. Emits VERDICT and receipts. | Run without a Z2 hash. |

**Authorized Z2 identities** are listed in `CLAUDE.md`. This document does not print them.

**Escalation:** Z1 → Z2. Carly holds both Admiral and Z2 roles. A contested Z2 decision is re-read by the same ratifier, who signs a new RATIFY event with a new hash. The original record is not rewritten. Raise contests within 48 hours.

**Founder rule for authority:** Drive is for navigation. Git and authenticated CI are for implementation truth. Z2 is for authority.

---

## 3. Session rituals

### §A: Session open (source summary)

This is a summary, not the full protocol. `SESSION_RITUALS.md` §A (lines 47–67) adds live-state fetches, halt and degraded-mode handling, a drift catalog, a Phase 1 declaration, and user acknowledgement. Follow the full protocol. The items below are not an execution order and do not replace the full protocol.

- `git fetch && git rev-parse HEAD`. Pin the SHA.
- Read `REGISTERED.md` at that SHA (IC-030: live-fetch, then pin).
- Read `PRIORITY_QUEUE.md`.
- Read `ZONE_REGISTRY.md` at that SHA. Check the active repo count.
- Verify each file's sha256 against the manifest.
- State: **Position · Destination · Probability.**

### §B: Session close

- **B.0 Empirical Verification Block:** code ran, or the close is refused.
- **B.6 Receipt reconciliation:** walk each claim against the tree. Report RECEIPT-GAP items to the Priority Queue.
- **Findings scan:** harvest F, IC, and H candidates.
- **Handoff:** write `z1-inbox/<date>/HANDOFF.md` with pinned SHA, findings, and next blockers.

---

## 4. Repos and zones

- **31 repos** in the ecosystem. Mapped in `ZONE_REGISTRY.md`. Planned repos are in `PLANNED_REPOS.md`.
- **Full Z1 cap:** humanaios, humanaios-internal, acat-inspect, acat-x, acat-dashboard, acat-observatory, empirica-practice-mesh.
- **Limited Z1 cap:** lasting-light-ai (RQ1–RQ3 only), docs (content only), findlocaltattooartists (content only).
- **Read-only:** research (frozen papers).

### Repo inventory

| Repo | Purpose | Status | Start here |
|---|---|---|---|
| `operations` | Governance, INTENT-OS, Resource Miner, Coordinator, CI. **Critical.** | [verified] | `CLAUDE.md`, `SESSION_RITUALS.md` |
| `humanaios` | Product scaffold. Its README opens with an **Empirica Foundation Evaluator** block, then describes the HumanAIOS scaffold. The auth scaffold is functional but not deployed. **[verified]** | Not the control plane | `README.md` (note the contamination below) |
| `humanaios-internal` | README not retrieved (404 on default branch). | [unverified] | Clone and read. |
| `acat-inspect` | ACAT v1.0 ported to UK AISI Inspect. Scaffold, no results. Says 11 dimensions. | [verified] | `HYPOTHESIS.md` |
| `acat-x` | Inspect AI suite, 14 dimensions. Python. | [verified] | `README.md`, `src/acat_x/` |
| `acat-dashboard`, `acat-observatory` | Magic Patterns Vite templates. `npm install`, then `npm run dev`. | [verified] | `README.md` |
| `empirica-practice-mesh` | Entity registry and governance sync for 15 practices. | [verified] | `CLAUDE.md` |
| `lasting-light-ai` | Public ACAT research platform. | [unverified] | Not read here. |
| `empirica-resource-miner` | Old private repo. **Archived.** Do not use as current code. | [unverified] | — |

**README contamination:** `humanaios/README.md` begins with an Empirica Foundation Evaluator block. Treat the Evaluator block as a bad paste. Do not read the repo as the Evaluator seat. Fix the README.

---

## 5. Core components

### 5.1 INTENT-OS (founder surface)

INTENT-OS is the founder board and its control tools. It is more mature than its name suggests.

| Piece | Path | What it does |
|---|---|---|
| Founder board | `ui/intent-os-humanaios-v3_3.html` | Z2 control surface. Requires login. The board is behind Cloudflare Access (`board/worker.mjs`). |
| Decision relay | `tools/decision_relay.py` | Carries founder decisions and requests into the repo workflow. Not ratification by itself. |
| Reconcile | `tools/intent_os_reconcile_v1_0.py` | Turns merged decision evidence into reconciled state. |
| Board check | `tools/intent_os_board_check_v1_0.py` | Re-hashes board seals against the tree. |
| Reseal | `tools/intent_os_board_reseal_v1_0.py` | Re-hashes mechanical drift. Refuses changed tools. |
| Request reader | `tools/intent_os_requests_v1_0.py` | Verifies `REQ-` records in the inbox. |
| Test harness | `tools/intent_os_test_harness_v1_0.py` | Runs tiers T0–T7. Writes a JSON receipt. |

**Board status today: STALE [verified].** `intent_os_board_check_v1_0.py` returned `verdict: STALE` at `c05ff89`. Counts: MATCH 33, DRIFT 6, ABSENT-CONFIRMED 5, UNCHECKED 7. Do not treat the board as current until it holds.

### 5.2 Resource Miner

Resource Miner is the discovery layer upstream of Entitlement Navigator. It finds candidates. It does **not** decide eligibility.

**Current location [verified]:** `humanaios-funding-pipeline/resource-miner/` inside `operations`. The old `empirica-resource-miner` repo is archived.

**Boundary [verified]:**

```text
Public sources
  -> Resource Miner (ResourceCandidate + provenance)
  -> Need Graph mapping
  -> VERIFY_NOW | WATCH | ARCHIVE
  -> Entitlement Navigator / resolver
  -> applicant-specific eligibility evidence
  -> human-authorized next work
  -> outcome receipt
```

Every candidate starts with `eligibility_assessed=false`. The Miner never emits "YOU QUALIFY" or "APPLY NOW."

**Adapters [verified]:** funding (existing pipeline data), DEV Community, GitHub issue search, HackerOne (read-only; credentials from env vars only), generic RSS/Atom.

**Routes [verified]** in `app.py`: `/api/health`, `/api/needs`, `/api/requirements`, `/api/resources`, `/api/entitlement/handoff`, `/api/scan`, `/api/intent`.

**Regression suite [head-specific verification pending]:** A previous review reported 173 passing tests. From `humanaios-funding-pipeline/resource-miner/`, re-run `python3 -m unittest discover -s tests` at the exact proposed head. Prior test counts do not establish production acceptance.

**Snapshot state:** `data/resources.jsonl` is ephemeral. `data/resources.snapshot.jsonl` is durable and checked in.

**Daily automation [source-verified; runtime not accepted]:** `.github/workflows/resource-miner-scan.yml` is scheduled for **06:15 UTC** and declares tests, mine resolution, scanning, reconciliation, and snapshot commits. As inspected on 2026-10-17, its command `python3 -m resource_miner.cli reconcile` is not registered by the CLI parser. Treat the reconciliation step as **at risk of failure** until the command is repaired and its workflow run verified; a declared workflow is not evidence of success.

**Deploy [verified]:** `humanaios-funding-pipeline/nixpacks.toml` starts with `cd resource-miner && python3 app.py --host 0.0.0.0 --port $PORT`. The Dockerfile builds from `humanaios-funding-pipeline/`, not `resource-miner/` alone, because `app.py` reads `../data/sources.json`.

### 5.3 Repository Coordinator

The Coordinator controls **admission and working-set standing**. It never grants merge authority.

- `repository-admission-gate.yml` is the required check. It runs on `pull_request_target`. Policy comes from the trusted default branch. State comes from an exact, receipted Coordinator state commit.
- It refuses a state that claims merge authority, and it fails closed when evidence is missing.
- `repository-coordinator.yml` produces the advisory index. Every receipt has `merge_authority: false`.
- Candidate PR code never runs with write credentials.

**Lanes:** ACTIVE, ADMITTED_TO_EVALUATION, CONTROL_PLANE, ADMISSION_REVIEW, WORKBENCH, MAINTENANCE, CAPACITY_CONTENTION.

### 5.4 ACAT and Lasting Light

- ACAT is a behavioral-measurement research protocol. The public site labels it research (TRL 2–3). **[unverified: public-site claim]**
- Dataset counts disagree between sources (see section 13). Report N as three numbers with a source.
- Do not present ACAT as deployment certification.

### 5.5 Empirica

Measurement and practice-workflow tooling. It is not the HumanAIOS governance repo. **[unverified: scope from Drive]**

---

## 6. Governance files and who writes them

| File | Who writes | Gate |
|---|---|---|
| `REGISTERED.md` | Z2. Append-only. | `z2_ratification_gate.yml` |
| `PRIORITY_QUEUE.md`, `ZONE_REGISTRY.md`, `PLANNED_REPOS.md` | Z2 ratifies | Document control |
| `CLAUDE.md` | Z2 ratifies authority changes | CODEOWNERS |
| `constants/*.json` | Z2, through a molt | `molt-tier-check.yml` (advisory) |
| `NF_LEDGER.jsonl` | Code only. Append-only. | Hash-chain check |

**Do not edit existing `REGISTERED.md` entries.** Authorized additions come through Z2-reviewed PRs (`REGISTRY_SPEC.md`). Corrections are made by adding a new entry.

---

## 7. PR workflow and CI gates

### Workflow (`.claude/PR_WORKFLOW_GUIDE.md`)

1. One task per finding at session start.
2. Fix each finding.
3. Run `./scripts/verify_pr_readiness.sh`.
4. Push only when green.
5. Record a findings table in the PR.

### Real gates [verified]

- `z2_ratification_gate.yml`. Its merge-authority step is **advisory**: it warns when the commit author is not an authorized Z2 identity and exits 0. Signature checks (`ratify.py --verify`, `ratify_eco.py --verify`) are `continue-on-error`. **Blocking steps:** Z1 inbox index integrity (`validate.py`), inbox index drift (`render.py --check`).
- `repository-admission-gate.yml`: Coordinator admission (see 5.3).
- `molt-tier-check.yml`: **advisory** tier classification. Never blocks merge.
- `molt-window-close-trigger.yml`: window-close detection. Runs daily or manually, not on PRs.
- `manifest-sync-gate.yml`, `document-control.yml`, `governance-files.yml`, `no-op-pr-guard.yml`.
- `resource-miner-scan.yml`: daily 06:15 UTC (see 5.2).

**Name correction:** `CLAUDE.md` names `falsifier_lint`, `registry_consistency`, and `molt_anti_cascade`. **None exist as gates.** The real checks are `check_anti_cascade_rules` in `molt_cycle.py`, the falsifier check in `.z1-control/validate.py`, and `tools/cascade_guard.py`.

### Baseline test commands [verified]

```bash
cd operations
python3 tools/intent_os_board_check_v1_0.py          # board seals
python3 tools/intent_os_test_harness_v1_0.py --list  # all checks
python3 tools/intent_os_test_harness_v1_0.py --tier T0
python3 tools/intent_os_test_harness_v1_0.py --only t4-repo-index

cd humanaios-funding-pipeline/resource-miner
python3 -m unittest discover -s tests
```

---

## 8. Founder workflows

### "I have an intent"

`Intent → INTENT-OS → bounded question → Resource Miner if resources matter → inspect evidence → human decision → Coordinator admission if code changes → protected CI → merge or execute → receipt → update founder view.`

**Operational acceptance (2026-10-17):** A bounded local probe of the Miner objective API and matching code reported **21 checks passing** with stubbed external adapters. This establishes neither production deployment nor authenticated founder review, a persisted `WATCH` choice, or a durable outcome receipt. The full workflow is **UNVERIFIED** until a founder selection is independently authenticated, saved, reloaded, and verified without initiating an application or external action. The `/api/intent` selection digest is unsigned and must not be used as execution authorization.

### Mine resources safely [verified commands]

```bash
cd operations/humanaios-funding-pipeline/resource-miner
python3 -m unittest discover -s tests

# Dry-run first. Live output is separate from the durable snapshot.
python3 -m resource_miner.cli scan --source devto --dev-tag devchallenge --dry-run
python3 -m resource_miner.cli scan --source github --github-query 'is:issue is:open label:bounty' --dry-run

python3 app.py --host 127.0.0.1 --port 8766
curl -fsS http://127.0.0.1:8766/api/health
# Admin-gated. RESOURCE_MINER_ADMIN_TOKEN must match the service token (32+ characters).
curl -fsS -H "X-Resource-Miner-Admin-Token: $RESOURCE_MINER_ADMIN_TOKEN" http://127.0.0.1:8766/api/resources
```

HackerOne needs `HACKERONE_API_USERNAME` and `HACKERONE_API_TOKEN` from your local environment. Never put them in files.

### Work on the HumanAIOS product scaffold [unverified: from the humanaios README]

```bash
git clone <humanaios repository>
cd humanaios
npm install
cp .env.example .env
createdb humanaios
psql -d humanaios -f schema.sql
npm run start:dev   # local auth API on port 3000
```

### Run ACAT-X [unverified: from the acat-x README]

```bash
uv sync
uv run inspect eval src/acat_x/consist --model <provider/model>
```

---

## 9. Deploy, update, rollback, monitor, backup

There is no single "deploy HumanAIOS" command. Deploy one bounded service from one known commit, through its own platform contract.

### Update

```bash
git fetch origin
git status --short
git rev-parse HEAD origin/main
git switch -c fix/<short-purpose>
# change only intended files
git diff --check && git diff
python3 -m unittest discover -s humanaios-funding-pipeline/resource-miner/tests
python3 tools/intent_os_board_check_v1_0.py
git add <exact-files> && git commit -m "fix: <bounded description>"
git push -u origin HEAD
```

Stop if local work is behind or dirty. Stage exact files only.

### Deploy Resource Miner [verified contract]

Build context: `humanaios-funding-pipeline/`. Start: `cd resource-miner && python3 app.py --host 0.0.0.0 --port $PORT`. Python 3.11. Platform: Railway/Nixpacks. The exact Railway project and service IDs are not in the reviewed sources, so no deploy command is given here. Deploy only behind upstream rate limiting and request-concurrency controls: `/api/intent` is unauthenticated and can run live scans.

A release is: **known commit → protected CI → human approval → service bound to the right root → health check → snapshot check → receipt.**

### Rollback

- **Bad code merge:** `git revert <sha>` on a branch, then send it through the normal PR, admission, CI, and human approval path. Do **not** rewrite `main`.
- **Resource Miner data failure:** restore behavior from the last known-good durable snapshot before a new scan.
- **Runtime:** roll back to the last Git SHA with a verified build, health check, and data. No verified one-line platform rollback exists in the sources.

### Monitor

- Resource Miner: require `RESOURCE_MINER_URL` to use `https://`, because the admin token must not travel in cleartext. Then run `curl -fsS "$RESOURCE_MINER_URL/api/health"`, then fetch `/api/resources` with the `X-Resource-Miner-Admin-Token` header (value from `RESOURCE_MINER_ADMIN_TOKEN`, 32+ characters) and compare it with the durable snapshot.
- ACAT: `curl -fsS "$ACAT_API_URL/api/v1/acat/health"` **[unverified route]**.
- Repo: `git fetch && git log --oneline -n 10`. Check required PR checks and the Coordinator receipt.

### Backup [recommended — not verified as active]

The Drive evidence ledger marks automatic sync as unverified. No complete cross-system backup is confirmed.

| Asset | Current protection | Recommended |
|---|---|---|
| Git repos | Git history + remote | Nightly immutable mirror or bundle |
| Resource Miner state | Daily checked-in snapshots | Copy snapshots and receipts off-platform |
| Coordinator state | State branch + ledger | Nightly immutable export |
| Drive docs | Google Drive | Scheduled versioned export |
| Research data | Live database | Automated backup + tested restore |
| Secrets | Platform stores | Password-manager inventory. Never a repo dump. |

**A backup is not real until one restore works.**

### Recommended: Founder Health receipt [recommended]

A read-only receipt that aggregates evidence and grants no authority:

```yaml
schema: humanaios.founder-health.v1
authority_effect: NONE
checks:
  operations_main_sha: ...
  intent_os_board: HOLDS | STALE
  intent_os_harness: PASS | FAIL
  resource_miner_tests: PASS
  resource_snapshot_age_hours: ...
  coordinator_state_verified: true
  required_ci: PASS
  backup_last_restore_test: ...
  unresolved_z3_actions: ...
```

---

## 10. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Board says STALE | Underlying files changed without reseal | Run `intent_os_board_check_v1_0.py`. Reseal mechanical drift with `intent_os_board_reseal_v1_0.py`. Human-review the rest. |
| Decision looks made but is not ratified | Relay or board state confused with merged Z2 evidence | Check merge state and the ruling. Reconcile after merge. Never claim ratification by hand. |
| Resource found but blocked | Discovery mistaken for eligibility | Check `eligibility_assessed`. Send through the resolver and human review. |
| Resource Miner empty after restart | Live JSONL is ephemeral | Load `resources.snapshot.jsonl`. Run a bounded scan. |
| Feed or source fails | Upstream format, rate limit, RSS safety rejection, or missing credential | Dry-run one source. Keep prior state. Repair the adapter. |
| PR blocked though tests pass | No admission standing, stale head, missing review, or missing evidence | Open the admission check. Fix the missing proof. **Do not disable the gate.** |
| CI passes but looks wrong | False-pass or skipped-check instrumentation | Read raw job outcomes. Re-run the exact test. |
| Warning at merge authority step | Author not an authorized Z2 identity (advisory) | The warning does not block. Real ratification needs an explicit Z2 signature in `REGISTERED.md`. Do not change the author. |
| `render.py --check` fails | Inbox index out of sync | `python3 .z1-control/render.py`, then commit. |
| `ratify.py --verify` fails | Ratified candidate or row changed | Restore the ratified content, or ratify a new hash. |
| `scan.py --check` fails | Tool manifest stale | `scan.py`, then `render.py`. Commit both `tools-manifest.yaml` and `TOOLS_MANIFEST.md`. |
| Push refused: branch behind | Remote has commits you lack | Fetch and merge or rebase per `OPERATOR_RUNBOOK.md` §5 (IC-026). HALT if behind. |
| `REGISTERED.md` gate fails | Edited existing entry | Revert. Append a new entry. |
| Dashboard pipeline YELLOW, no rows **[unverified]** | No rows arrived | Check the n8n runner. An older manual says Make.com. Verify first. |
| Session close refused | Missing B.0 or code did not run | Run the code. Add the B.0 block. |
| Stale `QUICKSTART.md` | Install path from an older machine | Verify the install path first. |

**Escalate** to Z2 when: the Coordinator state contradicts itself, a required gate looks defective, legal or program eligibility is unclear, or a publication depends on disputed numbers.

---

## 11. Key incidents (from REGISTERED.md)

| ID | Meaning |
|---|---|
| **IC-026** | Behind-remote pre-flight failure. Push blocked. |
| **IC-029** | Fetch block semantics. |
| **IC-030** | `REGISTERED.md` fetch skipped without declaration. Most cited. |
| **IC-031** | Receipt overstatement. Claims not matched to tree. |
| **IC-032** | Constraint set before data was inspected. |
| **IC-041** | Audit false pass. |

Reference counts are not incident counts. Read the IC heading in `REGISTERED.md` before citing.

---

## 12. Glossary

- **F:** finding. **IC:** integrity correction. **H:** hypothesis.
- **RATIFY:** a Z2 signed decision, identified by hash.
- **MOLT:** a constant change, pinned with a window and a falsifier.
- **VERDICT / CYCLE / MEASURE:** Z3 outputs.
- **Callouts:** GAP, STALE, RECEIPT-GAP, GAUGE, AMBIGUITY, VOID, DRIFT, DISPUTED, MOLT, REVERT.
- **Eligibility unknown:** a candidate found but not checked for the applicant's eligibility. Resource found ≠ eligible ≠ approved ≠ funded.
- **Admission:** working-set standing. Not merge authority.
- **B.0 / B.6:** close-session verification and receipt reconciliation.
- **Falsifier:** the test that would show a claim is wrong.

---

## 13. Known conflicts and open items

1. **Zone definitions.** The April Drive manual says Z2 approves and Z3 executes only. The September `CLAUDE.md` makes Z3 per-repo executors. This manual uses `CLAUDE.md`.
2. **Gate names.** `falsifier_lint`, `registry_consistency`, and `molt_anti_cascade` do not exist. See section 7.
3. **Board status.** Board check returns STALE at `c05ff89`. Fix before trusting the founder board.
4. **Resource Miner workflow name.** The schedule is in `resource-miner-scan.yml`. Some Drive notes name a different file. Use the repo.
5. **Dataset counts.** N 630 vs 629. N_LI 308 (CI) vs 113 (old CSV). Mean LI 0.8632 vs 0.84 and 0.867. Report N as three numbers with a source.
6. **ACAT dimensions.** `acat-inspect` says 11. `acat-x` says 14.
7. **Legal entity.** The April manual says "HumanAIOS LLC". The March overview names a different entity, not yet accepted. Do not state a legal entity.
8. **`humanaios` README contamination.** The Evaluator block at the top is wrong for this repo.
9. **Exposed key.** The April manual says a RentAHuman API key was flagged. **Rotate it.** Do not paste its value.
10. **Unverified:** IC-044, IC-050 (no heading found), IC-023 Drive file (too large to read), `humanaios-internal` README, ACAT public-site claims, Railway project bindings, dashboard pipeline, `lasting-light-ai` status.

---

## 14. Sources

**Repo (operations) [verified]:** `CLAUDE.md`, `SEED.md`, `SESSION_RITUALS.md`, `OPERATOR_RUNBOOK.md`, `REGISTERED.md`, `PRIORITY_QUEUE.md`, `ZONE_REGISTRY.md`, `.claude/PR_WORKFLOW_GUIDE.md`, `.github/workflows/z2_ratification_gate.yml`, `.github/workflows/repository-admission-gate.yml`, `.github/workflows/resource-miner-scan.yml`, `ui/intent-os-humanaios-v3_3.html`, `tools/intent_os_*.py`, `tools/decision_relay.py`, `humanaios-funding-pipeline/` (nixpacks, Dockerfile, resource-miner).

**Product repos read (six):** `humanaios-ui/humanaios`, `acat-inspect`, `acat-x`, `acat-dashboard`, `acat-observatory`, `empirica-practice-mesh`. `humanaios-internal` was not retrieved (see section 4).

**Google Drive (history and navigation only):** HAIOSCC_USER_MANUAL_S041226; WEBSITE_USER_MANUAL_S041226; PLAYBOOK (Aug 31); SESSION_PLAYBOOK; PLAYBOOK_2026-09-01; PHASE_0_GOVERNANCE_FILES_20260909; night_command_center_S051726-02; Systems Operations Overview; KNOWLEDGE_TRANSFER_GUIDE_V2; HUMANAIOS-INTELLIGENCE (SYSTEM_MAP, CURRENT_PRIORITIES, EVIDENCE_AND_DECISIONS).

---

_This draft is a guide, not authority. Governance decisions are made by Z2 under `CLAUDE.md`._
