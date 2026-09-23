---
title: Repository structure map — humanaios-ui/operations
status: reference
lifecycle: consumed
consumer: tools/intent_os_test_harness_v1_0.py   # check t4-repo-index: every backticked path below must exist
updated: 2026-09-16
authority: Z1 reference document (not governance-controlled); rewritten 2026-09-16 from `ls` output, not memory
---

# Repository structure map — humanaios-ui/operations

**Repository:** humanaios-ui/operations · **Zone:** Z-000 (`ZONE_REGISTRY.md`) · **Authority:** `CLAUDE.md`

**The one rule of this file:** every path written in backticks is a claim that the path exists, and
`python3 tools/intent_os_test_harness_v1_0.py --only t4-repo-index` fails if any does not. A name
without backticks is a description. When a path moves, this file is wrong until it is re-read.

---

## Quick navigation

| directory | purpose | start here |
|---|---|---|
| root | governance, authority, registries, session rituals | `CLAUDE.md` · `REGISTERED.md` · `PRIORITY_QUEUE.md` · `ZONE_REGISTRY.md` · `SESSION_RITUALS.md` |
| `z1-inbox/` | Z1 proposals and Z2 rulings, one dated folder per session | `z1-inbox/INDEX.yaml` · `Z1_INBOX_INDEX.md` (rendered, at root) |
| `.z1-control/` | the Z2 gate's tools: validate, render, sign | `.z1-control/ratify.py` |
| `.tool-control/` | tool manifest scanner, validator, renderer | `tools-manifest.yaml` (root) · `TOOLS_MANIFEST.md` (root, rendered) |
| `.doc-control/` | document registry validator, renderer, review scheduler | `document-registry.yaml` (root) · `CONTROLLED_DOCUMENTS.md` (root, rendered) |
| `tools/` | 159 registered tools; the Intent-OS relay, checker and harness live here | `tools/decision_relay.py` · `tools/intent_os_board_check_v1_0.py` · `tools/intent_os_test_harness_v1_0.py` |
| `ui/` | Z2's surfaces: the Intent-OS board and the test dashboard | `ui/intent-os-humanaios-v3_3.html` · `ui/intent-os-test-dashboard-v1_0.html` |
| `docs/` | 87 documents; runbooks and the test pathway | `docs/INTENT_OS_BOARD_RUNBOOK.md` · `docs/INTENT_OS_TEST_PATHWAY.md` |
| `.github/` | 46 workflows, CODEOWNERS, templates | `.github/workflows/z2_ratification_gate.yml` |
| `acat/` | ACAT (assessment) package: API, CLI, contracts, scoring, tests | `acat/README.md` · `acat/contracts/` |
| `ledgers/` | NF (falsifier) ledger and resource ledger, append-only | `ledgers/NF_LEDGER.jsonl` |
| `outputs/` | machine-written receipts; gitignored (`.gitignore` line 42) — the harness receipt lives here locally and travels embedded in the dashboard | outputs/intent_os_test_results.json (not tracked) |
| `tests/` · `tools/tests/` · `acat/tests/` | pytest suites CI runs | `.github/workflows/quality-baseline.yml` names the blocking list |

---

## Root — governance and registries

| file | role | who writes |
|---|---|---|
| `CLAUDE.md` | authority map: Z1 proposes · Z2 (Night) ratifies · Z3 executes; decision routing; CI gates; §A/§B rituals | Z2 ratifies changes |
| `REGISTERED.md` | append-only registry of findings (F), corrections (IC), hypotheses (H) and decisions | Z2 sole write |
| `PRIORITY_QUEUE.md` | ranked work queue; a new row is a Z2 act | Z2 ratifies scores |
| `ZONE_REGISTRY.md` | the 31 repositories: 8 active, 3 limited-cap, 1 read-only, planned rows point at `PLANNED_REPOS.md` | Z2 |
| `PLANNED_REPOS.md` | roadmap repositories (not active zones) | Z2 |
| `SESSION_RITUALS.md` | §A open (fetch, pin, read) · §B close (receipts, findings, handoff) | Z2 |
| `MOLT_STATE.md` | open molts, anti-cascade state | code + Z2 |
| `FRAMEWORK_MAPPING.md` | 5 AI-engineering concepts → Z-roles, files, gates | Z1 (ratified) |
| `BOOT_PROCESS_MAP.md` | `REGISTERED.md`'s place in the session boot chain | Z1 (awaiting Z2) |
| `CONTROLLED_DOCUMENTS.md` | rendered from `document-registry.yaml` — never edit by hand | `.doc-control/render.py` |
| `TOOLS_MANIFEST.md` | rendered from `tools-manifest.yaml` — never edit by hand | `.tool-control/render.py` |
| `Z1_INBOX_INDEX.md` | rendered from `z1-inbox/INDEX.yaml` — never edit by hand | `.z1-control/render.py` |
| `CANDIDATE_BLOCK_TEMPLATE.md` | how a Z1 proposal is written (pinned SHA, position · destination · probability, falsifier) | Z1 |
| `system_graph.json` | the operating graph in machine form (22 nodes, 53 edges at the 09-16 read) | generated |
| `constants.json` | 7 governed constants; changed only by a ratified molt | molt cycle |
| `molt_cycle.py` · `prs_run.py` | molt runner and PR runner — at the root, not under `tools/` (the board's seals say so) | code |
| `intake_template.jsonl` | one intake record; `tools/ic_scope_check.py` refuses it without a signing secret (by design) | intake |
| `REPOSITORY_STRUCTURE.md` | this file | Z1; verified by T4 |

Other root documents (specs, onboarding, assessments, session closes) are listed in `CONTROLLED_DOCUMENTS.md`
with their lifecycle; `python3 tools/doc_lifecycle_lint.py` prints the disposition table.

---

## `z1-inbox/` — proposals in, rulings out

```
z1-inbox/
├── INDEX.yaml                  every candidate and record; status awaiting_z2 | ratified | …; ratified_by, z2_hash
├── 2026-09-06/ … 2026-09-14/   one folder per session date
│   ├── Q-<TOPIC>-<nn>.md       a candidate block asking Z2 for a decision
│   ├── <TOPIC>_CANDIDATE_BLOCK.md / <TOPIC>_BLOCK.md   older naming, same shape
│   ├── Z2_RULING_<topic>.md    Z2's choices, transcribed by Z1 (e.g. the Intent-OS launch)
│   ├── Z2_RULINGS_<date>.md    the signatures `.z1-control/ratify.py` issued that day
│   └── HANDOFF.md              §B close: pinned SHA, findings, receipt walk-back, next blockers
└── (rendered at root)          Z1_INBOX_INDEX.md
```

Live examples: `z1-inbox/2026-09-14/Q-INTENTOS-LAUNCH-01.md` (the launch candidate),
`z1-inbox/2026-09-14/Z2_RULING_INTENTOS_LAUNCH.md` (d17 local only · d18 z1-inbox landing · d19 path
freeze), `z1-inbox/2026-09-14/Z2_RULINGS_2026-09-14.md` (its signature), the fourteen board rulings
`z1-inbox/2026-09-14/Q-BOARD-RULING-02.md` … `z1-inbox/2026-09-14/Q-BOARD-RULING-16.md`, and
`z1-inbox/2026-09-14/HANDOFF.md`.

A `z1-inbox/INDEX.yaml` candidate entry, as actually written:

```yaml
- q_id: Q-INTENTOS-LAUNCH-01
  title: "Intent-OS board — organize the development, decide the launch"
  path: z1-inbox/2026-09-14/Q-INTENTOS-LAUNCH-01.md
  submitted: '2026-09-14'
  status: ratified
  note: "…"
  ratified_by: Night
  ratified_at: '2026-09-14'
  z2_ruling: z1-inbox/2026-09-14/Z2_RULINGS_2026-09-14.md
  z2_hash: 9a2a469be2cbbe1d…
```

---

## `.z1-control/` — the Z2 gate's tools

| file | does | CI step |
|---|---|---|
| `.z1-control/validate.py` | inbox rules (coverage, no self-grant, hash-in-ruling, windows); `--report` emits the Z2 queue as JSON; `--smoke-test` | z2 gate: ERROR, blocks merge |
| `.z1-control/render.py` | writes `Z1_INBOX_INDEX.md`; `--check` fails if out of sync | z2 gate: ERROR |
| `.z1-control/ratify.py` | `Q-ID --decision ACCEPT --by Night --apply` signs `sha256(candidate \| by=Night \| at=<date> \| decision=ACCEPT)`; `--verify` re-checks every recorded signature; `--list` | z2 gate |

`tools/decision_relay.py` writes the same bytes these tools write, so a ruling landed from the board
passes the same gate.

---

## `.tool-control/` and `.doc-control/` — the two registries

| file | does |
|---|---|
| `.tool-control/scan.py` | discovers tools under `tools/`, `scripts/`, `bin/`, the control dirs; refreshes mechanical fields in `tools-manifest.yaml`; `--check` |
| `.tool-control/validate.py` | id, existence, approval (no self-grant), zone and MCP rules |
| `.tool-control/render.py` | writes `TOOLS_MANIFEST.md`; `--check` |
| `.tool-control/selftest.py` | 31 blocking conditions the manifest workflow enforces |
| `.tool-control/README.md` | the rules in prose |
| `.doc-control/validate.py` | front-matter and registry rules over `document-registry.yaml` (schema: `.doc-control/frontmatter.schema.json`) |
| `.doc-control/render.py` | writes `CONTROLLED_DOCUMENTS.md`; `--check` |
| `.doc-control/review.py` | review schedule; every recorded review derives its own next due date; `--check` |
| `.doc-control/strict_yaml.py` | the strict loader both registries share |
| `.doc-control/MAINTAINER_ASSIGNMENT.md` · `.doc-control/TEAM_OWNERS.md` | who reviews what |

Workflows: `.github/workflows/tool-manifest.yml` · `.github/workflows/document-control.yml`.

---

## `tools/` — the Intent-OS control surface and the gates

| file | role | proof |
|---|---|---|
| `tools/decision_relay.py` | v0.5.0 · HTTP relay: signed `/decide` writes a tapped choice into its candidate block on a branch as a one-file PR marked DECIDED — the merge is the ratification, the relay signs nothing; `/task` lands an agent request as a `REQ-` record; `DRY_RUN=1` works on a local copy | `--self-test`; harness `t2-relay-roundtrip` |
| `tools/intent_os_reconcile_v1_0.py` | after a decided candidate merges: `sha256(candidate \| by=<merger's ratifier name> \| at=<merge date> \| decision=ACCEPT)` over the merged bytes → the day's `Z2_RULINGS_<date>.md`, `status: ratified` in `z1-inbox/INDEX.yaml`, `Z1_INBOX_INDEX.md`; `--check` exit 1 waiting · 2 refused | `--self-test` (runs validate.py, render.py --check, ratify.py --verify on the result) |
| `tools/relay_policy.yml` | ngrok traffic policy in front of the relay (basic-auth; OPTIONS exempt for the browser preflight) | — |
| `tools/intent_os_board_check_v1_0.py` | re-hashes every board seal against the tree; exit 0 HOLDS · 2 STALE | `--self-test` |
| `tools/intent_os_test_harness_v1_0.py` | runs T0–T7 (T5 is generated from `tools-manifest.yaml`: every `smoke_test: true` claim, measured; T6 boots the ACAT API; T7 is a key-gated live model call), writes the receipt to outputs/intent_os_test_results.json (gitignored), `--render` embeds it in the dashboard | `--self-test` |
| `tools/intent_os_board_reseal_v1_0.py` | after a merge: re-hashes MECHANICAL seals (inbox index, registry, ledgers, rendered indexes) and refuses anything else; `--check` exit 0 HOLDS · 1 mechanical · 2 needs a human | `--self-test` |
| `tools/intent_os_requests_v1_0.py` | the agent-bus reader: every `REQ-` record in z1-inbox, hashes recomputed, stage from its Fulfilment (`requested → taken → pr → merged`, never from time); `--check` exit 2 if any record does not verify; `--json` is what the harness embeds | `--self-test`; harness `t0-requests` · `t1-requests` |
| `tools/ic_scope_check.py` | scope check on intake records; refuses without `$IC_SCOPE_SECRET` | exit 2 = correct |
| `tools/doc_lifecycle_lint.py` | disposition table for `docs/`; `--enforce` fails on unfiled docs | `--self-test` |
| `tools/cascade_guard.py` · `tools/jester_invariants.py` | anti-cascade and invariant checks | `--self-test` |
| `tools/repo_health.py` | `--strict` in the quality-baseline workflow | — |
| `tools/behavioral_compliance_gate_v1_0.py` | corpus pass-rate gate (≥ 0.70) | `--smoke-test` |
| `tools/registered_findings_validator_v1_0.py` | `REGISTERED.md` integrity (findings-registry-gate) | `--smoke-test` |
| `tools/registry_site_generator_v1_0.py` | writes `site/` for the Pages workflow (the board is *not* published — d17) | — |
| `tools/molt_cycle_tier0_v0_1.py` | the tools/ copy of the molt runner; the canonical one is `molt_cycle.py` at root | — |
| `tools/smag_to_empirica_connector.py` | Empirica wiring (`.empirica/project.yaml`) | — |
| `tools/acat_merkle_auditor_v2_0.py` · `tools/acat_psychometric_validator_v1_0.py` · `tools/acat_dimension_scorer.py` | ACAT auditing and scoring (20+ ACAT tools in this directory) | see `TOOLS_MANIFEST.md` |

The manifest is the list: `tools-manifest.yaml` (156 tools, 2 MCP servers at the 09-16 scan). A tool
without Builder markers (`TOOL_NAME`, `TOOL_VERSION`, `TOOL_CATEGORY`, `TOOL_ZONE`) is registered
unclassified; a smoke test is what makes it count.

---

## `ui/` — Z2's surfaces (local only, d17)

| file | role |
|---|---|
| `ui/intent-os-humanaios-v3_3.html` | the Intent-OS board: 20 steps (3 done · 10 in progress · 7 waiting), 9 gauges, 18 predictions, 19 rulings (d1, d4, d17–d19 ruled; d2, d3, d5–d16 open), 43 seals — counts read by the harness on 2026-09-16. The `HUMANAIOS` block inside is the dataset; the path is frozen (d19) and a re-read changes the data, never the filename |
| `ui/intent-os-test-dashboard-v1_0.html` | the test dashboard: ruling workflow · authority map · test matrix · live status · agent requests, rendered from the receipt the harness embeds; § 5's live fetch runs on click only and re-hashes each record in the browser |
| `ui/z2-ratification-reviewer.html` · `ui/Z2_RATIFICATION_GUIDE.md` | Z2's candidate reviewer and its guide |
| `ui/registry_viewer.jsx` · `ui/calibration_trace_viewer.jsx` | React viewers (registry, calibration traces) |

---

## `docs/` — runbooks and the pathway

| file | role |
|---|---|
| `docs/INTENT_OS_BOARD_RUNBOOK.md` | open · read honestly · rule · land through the relay · (publish: not until d17 is reversed) · re-read cadence |
| `docs/INTENT_OS_TEST_PATHWAY.md` | tiers T0–T4, roles, session order, falsifiers, scale-out order |
| `docs/INTENT_OS_GENERAL_USER_SPEC.md` | general-user board variant (lexicon, connectors, data line) — unratified |
| `docs/ACAT_BENCHMARK_MAP_20260908.md` | ACAT ↔ market-benchmark map; a consumer of the frozen board path |
| `docs/CLAUDE.md` | the empirica-outreach practice seat instructions |

87 documents in all; lifecycle per `CONTROLLED_DOCUMENTS.md` (`lifecycle: consumed | code | archived | produced`).
docs/_archive/ does not exist yet — it is where a retired board or dashboard goes under the falsifiers.

---

## `.github/` — CI and ownership

| file | enforces |
|---|---|
| `.github/workflows/z2_ratification_gate.yml` | validator/renderer/ratify smoke tests; recorded signatures verify; inbox index integrity (ERROR); rendered index in sync (ERROR); Seed Constitution changes carry a Z2 hash |
| `.github/workflows/intent-os-reconcile.yml` | on every push to `main` touching `z1-inbox/`: `tools/intent_os_reconcile_v1_0.py` records each merged decided candidate (merger = `by`, merge date = `at`), checks the result with the z2 gate's own tools, opens `intent-os: reconcile ratifications` |
| `.github/workflows/tool-manifest.yml` | the four `.tool-control/` smoke tests, then `.tool-control/selftest.py`, `.tool-control/scan.py` `--check`, `.tool-control/validate.py`, `.tool-control/render.py` `--check` |
| `.github/workflows/document-control.yml` | `.doc-control/` smoke tests, then `.doc-control/validate.py`, `.doc-control/review.py` `--check`, `.doc-control/render.py` `--check` |
| `.github/workflows/quality-baseline.yml` | `tools/repo_health.py --strict`, `.doc-control/validate.py`, mypy on `src/humanaios_operations/`, the blocking pytest list |
| `.github/workflows/findings-registry-gate.yml` | `tools/registered_findings_validator_v1_0.py --input REGISTERED.md` |
| `.github/workflows/behavioral-compliance.yml` | corpus pass-rate gate and its unit tests |
| `.github/workflows/priority-queue-triage.yml` | triage over `PRIORITY_QUEUE.md` and the inbox |
| `.github/workflows/intent-os-refresh.yml` | on every push to `main` (event-driven, no clock schedule; job pinned to `main`): seal check, drift classification, harness, receipt as artifact; report-only until d23, then refresh PR (mechanical) or `intent-os-stale` issue (human) |
| `.github/workflows/pages.yml` | deploys `site/` — the board is excluded by ruling d17 |
| `.github/workflows/auto-request-copilot-review.yml` · `.github/workflows/copilot-base-guard.yml` | Copilot review on PRs; base guard |
| `.github/CODEOWNERS` · `.github/PULL_REQUEST_TEMPLATE.md` · `.github/copilot-instructions.md` · `.github/dependabot.yml` | ownership, PR shape, reviewer instructions, dependency updates |
| `.github/ISSUE_TEMPLATE/code-quality.md` · `.github/ISSUE_TEMPLATE/seed-amendment.md` | the two issue templates |

46 workflow files in `.github/workflows/`; the harness's T3 tier runs what the blocking ones run.

---

## `acat/` — the assessment package

```
acat/
├── README.md · HF_DATASET_CARD.md
├── api/  cli/  mcp/            service, command line, MCP wrapper
├── contracts/                  5 JSON schemas: assess_request, human_score, phase1_intake, phase3_submission, score_result
├── normalization/  scoring/    pipeline stages
├── research/  data/  db/  sql/ studies, fixtures, persistence
├── tools/                      ACAT-side tools
├── tests/                      14 pytest files (fastapi + jsonschema required)
└── canonical_stats.json · canonical_stats_v2.json
```

Schemas: `acat/contracts/assess_request.schema.json` · `acat/contracts/human_score.schema.json` ·
`acat/contracts/phase1_intake.schema.json` · `acat/contracts/phase3_submission.schema.json` ·
`acat/contracts/score_result.schema.json`.

---

## `ledgers/` — measurement, append-only

| file | role |
|---|---|
| `ledgers/NF_LEDGER.jsonl` | falsifier ledger: 165 rows at the 09-16 read, all by Z1, 21 PENDING_Z2_DATE; hash-chained |
| `ledgers/NF_LEDGER_README.md` · `ledgers/NF_EVENT_SCHEMA.md` | how a row is written and what it must carry |
| `ledgers/RESOURCE_LEDGER.jsonl` | resource units per cycle |
| `ledgers/mesh_pins_090826.json` | the 09-08 mesh pin set |

`python3 molt_cycle.py --read-only --nf ledgers/NF_LEDGER.jsonl` reads it without writing.

---

## Everything else at the root

| directory | holds |
|---|---|
| `src/humanaios_operations/` | the Python package (`src/humanaios_operations/cli.py`, `src/humanaios_operations/dashboard.py`, `src/humanaios_operations/deadline_checker.py`, `src/humanaios_operations/scoring.py`, …); mypy target |
| `tests/` | research-scenario tests (`tests/research/`) and `tests/integration_test.py` |
| `scripts/` · `bin/` | scanned by the tool manifest alongside `tools/` |
| `site/` | generated static site for the Pages workflow |
| `seed-publication/` · `seeds/` | the Seed Constitution and its publication config |
| `registry-candidates/` · `ic_archive/` · `reports/` · `audits/` · `outputs/` · `artifacts/` · `deliverables/` | candidates, archived corrections, reports, audit logs, receipts, artifacts, deliverables |
| `applications/` · `humanaios-funding-pipeline/` · `orcid-publications-manager/` · `market-research/` · `collaborators/` · `collaborator-ops/` | applications, funding pipeline, ORCID manager, market research, collaborator records |
| `architecture/` · `instruments/` · `examples/` · `data/` · `sql/` · `supabase/` · `fuzzers/` · `patches/` · `workflows/` · `autonomy/` · `assets/` | architecture notes, instruments, examples, data, SQL, Supabase config, fuzz harnesses, patches, proposed workflows, autonomy gates, brand assets |
| `.agents/` · `.claude/` · `.codex/` · `.empirica/` · `.postflight/` · `.clusterfuzzlite/` | agent and seat configuration, Empirica project, post-flight logs, fuzzing config |

---

## Naming patterns

| pattern | meaning | example |
|---|---|---|
| `z1-inbox/<date>/Q-<TOPIC>-<nn>.md` | a Z1 candidate asking a Z2 decision | `z1-inbox/2026-09-14/Q-BOARD-RULING-07.md` |
| `z1-inbox/<date>/Z2_RULING_<topic>.md` | Z2's choices on one topic, transcribed | `z1-inbox/2026-09-13/Z2_RULING_ZONE2_RATIFY_TOOL.md` |
| `z1-inbox/<date>/Z2_RULINGS_<date>.md` | that day's signatures | `z1-inbox/2026-09-14/Z2_RULINGS_2026-09-14.md` |
| `z1-inbox/<date>/REQ-<yyyymmdd>-<nn>.md` | an agent request landed by the relay's `/task` — a record with a hashed ask and a Fulfilment section a worker fills by PR | (first one lands when the bus is used; runbook §4b) |
| `tools/<name>_v<major>_<minor>.py` | a versioned tool; Builder markers inside | `tools/intent_os_board_check_v1_0.py` |
| `ui/intent-os-<project>-v<major>_<minor>.html` | a board; path frozen per d19 | `ui/intent-os-humanaios-v3_3.html` |
| `*_CANDIDATE_BLOCK.md` / `*_BLOCK.md` | older candidate naming, same shape | `z1-inbox/2026-09-08/ACAT_BENCHMARK_CANDIDATE_BLOCK.md` |

---

## Authority flow, in files

1. **Z1** writes `z1-inbox/<date>/Q-….md` with a pinned SHA and a falsifier; adds it to `z1-inbox/INDEX.yaml`; runs `.z1-control/render.py`.
2. **CI** (`.github/workflows/z2_ratification_gate.yml`) refuses the PR if the inbox rules break or the rendered index is stale.
3. **Z2** taps on the board → `tools/decision_relay.py` → a one-file PR marked DECIDED → **Z2 reviews and merges it (the merge is the ratification)** → `.github/workflows/intent-os-reconcile.yml` writes the signature into `z1-inbox/<date>/Z2_RULINGS_<date>.md` and `status: ratified` into `z1-inbox/INDEX.yaml` in a reconcile PR. Or by hand: `.z1-control/ratify.py Q-ID --decision ACCEPT --by Night --apply`.
4. **Z3** merges with the hash; the board is re-read; `tools/intent_os_board_check_v1_0.py` HOLDS again.
5. **Anyone** runs `tools/intent_os_test_harness_v1_0.py --render` and opens `ui/intent-os-test-dashboard-v1_0.html` to see all of the above lit by its checks.

## Session open (§A, `SESSION_RITUALS.md`)

```
git fetch origin && git rev-parse HEAD
python3 tools/intent_os_board_check_v1_0.py
python3 tools/intent_os_test_harness_v1_0.py --render
```

## Maintenance

Re-read this file whenever a directory is added, a tool moves, or `t4-repo-index` fails. Write it from
`ls`, never from memory: the T4 check exists because the first version of this file named six paths
that were not there.
