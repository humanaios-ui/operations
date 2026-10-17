# Founder's Ultimate Users Manual and Troubleshooting Guide for HumanAIOS

**Status:** Draft v0.1 (2026-10-17). Built from the operations repo, seven product repos, and Google Drive. Unverified items are marked **[unverified]**.

---

## 1. Front door

HumanAIOS is a governance system for AI practices. It has three parts:

- **operations** (this repo): the authority map, session rituals, registry, and CI gates.
- **Product repos:** the ACAT assessment tools and the empirica practice mesh.
- **Google Drive:** older manuals and playbooks. Treat them as history, not current fact.

Start here, in this order:

1. `SEED.md` and `PRINCIPLES_SEED_V1_0.md`: identity and principles.
2. `CLAUDE.md`: who decides, who proposes, who executes.
3. `SESSION_RITUALS.md`: how a session opens and closes.
4. `REGISTERED.md`: the append-only registry of findings (F), corrections (IC), and hypotheses (H).

---

## 2. Roles

| Role | Who | Does | Does not |
|---|---|---|---|
| **Admiral / Z2 (ratifier)** | Carly R. Anderson (Night) | Accepts, edits, or rejects proposals. Signs ratification hashes. Sets zone assignments. | Execute ratified work. Propose new work. |
| **Z1 (proposer)** | Claude, plus practice teams | Reads the registry. Drafts candidate blocks. Flags blockers. | Merge or ratify its own work. |
| **Z3 (executor)** | Per-repo executors (many TBD) | Lands ratified changes. Runs experiments. Emits VERDICT and receipts. | Run without a Z2 hash. |

**Authorized Z2 identities** are listed in `CLAUDE.md`. The rule: the commit author on a ratification must be an authorized Z2 identity. This document does not print those addresses.

**Escalation:** Z1 → Z2 → Admiral. A Z2 decision can be contested within 48 hours. Contested decisions are re-read and re-signed.

---

## 3. Session rituals

### §A: Session open (mandatory before work)

1. `git fetch && git rev-parse HEAD`. Pin the SHA.
2. Read `REGISTERED.md` at that SHA (IC-030: live-fetch, then pin).
3. Read `PRIORITY_QUEUE.md`.
4. Read `ZONE_REGISTRY.md` at that SHA. Check the active repo count.
5. Verify each file's sha256 against the manifest.
6. State: **Position · Destination · Probability.**

### §B: Session close

- **B.0 Empirical Verification Block:** code ran, or the close is refused. Prereg hash is confirmed in `REGISTERED.md`.
- **B.6 Receipt reconciliation:** walk each claim against the tree. Report RECEIPT-GAP items to the Priority Queue.
- **Findings scan:** harvest F, IC, and H candidates. Emit candidate blocks.
- **Handoff:** write `z1-inbox/<date>/HANDOFF.md` with the pinned SHA, findings, and next blockers.

---

## 4. Repos and zones

- **31 repos** in the ecosystem, mapped in `ZONE_REGISTRY.md`. Planned (not yet active) repos are in `PLANNED_REPOS.md`.
- **Full Z1 cap:** humanaios, humanaios-internal, acat-inspect, acat-x, acat-dashboard, acat-observatory, empirica-practice-mesh.
- **Limited Z1 cap:** lasting-light-ai (RQ1–RQ3 only), docs (content only), findlocaltattooartists (content only).
- **Read-only:** research (frozen papers).

### Core product repos (read at this SHA)

| Repo | What it is | Start |
|---|---|---|
| `humanaios` | README describes an **Empirica Foundation Evaluator** seat, not a product. | Read `README.md` first. |
| `humanaios-internal` | README not retrieved (404 on default branch) **[unverified]**. | Clone and read. |
| `acat-inspect` | ACAT v1.0 ported to UK AISI Inspect. Scaffold. No results yet. Admits 11 dimensions. | `HYPOTHESIS.md` |
| `acat-x` | Inspect AI suite, 14 dimensions. Python. `pyproject.toml`. | `README.md`, `src/acat_x/` |
| `acat-dashboard` | Magic Patterns Vite template. | `npm install`, `npm run dev` |
| `acat-observatory` | Magic Patterns Vite template. | `npm install`, `npm run dev` |
| `empirica-practice-mesh` | Entity registry and governance sync for 15 practices. | `CLAUDE.md`, then `scripts/sync_entity_registry.py` |

---

## 5. Governance files and who writes them

| File | Who writes | Gate |
|---|---|---|
| `REGISTERED.md` | Z2 only. Append-only. | `z2_ratification_gate.yml` |
| `PRIORITY_QUEUE.md` | Z2 ratifies scores | Document control |
| `ZONE_REGISTRY.md` | Z2 ratifies repo changes | Document control |
| `PLANNED_REPOS.md` | Z2 ratifies roadmap | Document control |
| `CLAUDE.md` | Z2 ratifies authority changes | CODEOWNERS |
| `constants/*.json` | Z2, through a molt | `molt-tier-check.yml` |
| `NF_LEDGER.jsonl` | Code only. Append-only. | Hash-chain check |

**Do not hand-edit `REGISTERED.md`.** Hand edits break the append-only rule, and CI fails.

---

## 6. PR workflow and CI gates

### The workflow (`.claude/PR_WORKFLOW_GUIDE.md`)

1. Make one task per finding at session start.
2. Fix each finding.
3. Run `./scripts/verify_pr_readiness.sh`.
4. Push only when green.
5. Record a findings table in the PR.

### Real gates

These names exist in `.github/workflows/`:

- `z2_ratification_gate.yml`: the main gate. Checks the commit author is an authorized Z2 identity, runs the `.z1-control/` smoke tests, verifies ratification signatures, and blocks on inbox index drift.
- `molt-tier-check.yml` and `molt-window-close-trigger.yml`: molt tier and window checks.
- `manifest-sync-gate.yml`: tool manifest sync.
- `document-control.yml`, `governance-files.yml`: governance file rules.
- `repository-admission-gate.yml`: repo admission state.
- `no-op-pr-guard.yml`: blocks empty PRs.

**Name correction:** `CLAUDE.md` names `falsifier_lint`, `registry_consistency`, and `molt_anti_cascade` as gates. **None of these exist in the repo.** The nearest real code is `tools/cascade_guard.py` (cascade rules) and `tests/adversarial/test_falsifiers_t1_t7.py` (falsifier tests). Treat the `CLAUDE.md` names as a known conflict until Z2 ratifies a fix.

---

## 7. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Commit rejected at merge authority step | Commit author is not an authorized Z2 identity | Commit as an authorized identity, or have Z2 land it. Do not change the author to get past the check. |
| `render.py --check` fails | `Z1_INBOX_INDEX.md` out of sync with inbox files | Re-render with `python3 .z1-control/render.py`, then commit. |
| `ratify.py --verify` fails | A ratified candidate or ledger row changed | Restore the ratified content. Ratify a new hash if the change is needed. |
| `ratify_eco.py --verify` fails | Same as above, for the ecosystem ledger | Same fix. |
| `scan.py --check` fails | Tool manifest stale after a tool change | Re-run `.tool-control/scan.py`, then commit the manifest. |
| Push refused: branch behind | Remote has commits you lack | Fetch and merge or rebase per `OPERATOR_RUNBOOK.md` §5 (IC-026). HALT if behind. |
| `REGISTERED.md` gate fails | Hand edit or deleted line | Revert the edit. Append a new entry instead. |
| `verify_pr_readiness.sh` fails | Local lint or manifest check failure | Read the first failing line. Fix it. Re-run. |
| Dashboard pipeline shows YELLOW with no rows **[unverified for current pipeline]** | No rows arrived | Check the n8n runner. Older manual says Make.com; verify before acting. |
| Session close refused | Missing B.0 block or code did not run | Run the code. Add the B.0 block. |
| Stale `QUICKSTART.md` install steps | Install path is from an older machine | Do not follow. Verify the install path first **[unverified]**. |

---

## 8. Key incidents (from REGISTERED.md)

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

## 9. Glossary

- **F:** finding. **IC:** integrity correction. **H:** hypothesis.
- **RATIFY:** a Z2 signed decision. Identified by hash.
- **MOLT:** a constant change, pinned with a window and a falsifier.
- **VERDICT / CYCLE / MEASURE:** Z3 outputs.
- **Callouts:** GAP, STALE, RECEIPT-GAP, GAUGE, AMBIGUITY, VOID, DRIFT, DISPUTED, MOLT, REVERT.
- **B.0 / B.6:** close-session verification and receipt reconciliation.
- **Falsifier:** the test that would show a claim is wrong. Required on every hypothesis.

---

## 10. Known conflicts and open items

1. **Zone definitions.** The April Drive manual says Z2 approves and Z3 executes only. The September `CLAUDE.md` makes Z3 per-repo executors. This manual uses `CLAUDE.md`.
2. **Gate names.** `falsifier_lint`, `registry_consistency`, and `molt_anti_cascade` do not exist. See section 6.
3. **Dataset counts.** Canonical N is 630 in one doc and 629 in another. N_LI is 308 in CI and 113 in an older CSV. Mean LI is 0.8632 in current docs, 0.84 and 0.867 in older ones. Always report N as three numbers with a source.
4. **ACAT dimensions.** `acat-inspect` says 11. `acat-x` says 14. Confirm which is current.
5. **Legal entity.** The April manual says "HumanAIOS LLC". The March overview says a different entity name, not yet accepted. **Unconfirmed.** Do not state a legal entity in founder-facing text.
6. **Repo roles.** `humanaios` describes itself as the Empirica Foundation Evaluator seat, not a product. Confirm the intended role.
7. **Exposed key.** The April manual says a RentAHuman API key was flagged as exposed. **Rotate it.** Do not paste its value anywhere.
8. **Unverified:** IC-044 and IC-050 (no heading found). IC-023 Drive file (too large to read in full). `humanaios-internal` README.

---

## 11. Sources

**Repo (operations):** `CLAUDE.md`, `SEED.md`, `SESSION_RITUALS.md`, `OPERATOR_RUNBOOK.md`, `REGISTERED.md`, `PRIORITY_QUEUE.md`, `ZONE_REGISTRY.md`, `.claude/PR_WORKFLOW_GUIDE.md`, `.github/workflows/z2_ratification_gate.yml`, `scripts/verify_pr_readiness.sh`.

**Product repos:** `humanaios-ui/humanaios`, `humanaios-ui/acat-inspect`, `humanaios-ui/acat-x`, `humanaios-ui/acat-dashboard`, `humanaios-ui/acat-observatory`, `humanaios-ui/empirica-practice-mesh`.

**Google Drive (history only):** HAIOSCC_USER_MANUAL_S041226; WEBSITE_USER_MANUAL_S041226; PLAYBOOK (Aug 31); SESSION_PLAYBOOK (Aug 27–28); PLAYBOOK_2026-09-01; PHASE_0_GOVERNANCE_FILES_20260909; night_command_center_S051726-02; HumanAIOS Systems Operations Overview; KNOWLEDGE_TRANSFER_GUIDE_V2.

---

_This draft is a guide, not authority. Governance decisions are made by Z2 under `CLAUDE.md`._
