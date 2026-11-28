# Q-STALE-QUEUE-SORT-01 — Sort of the 37 candidates waiting since September

**Z1 Proposer:** Claude (Z1)
**Date Submitted:** 2026-11-28
**Asked for by:** Night (Z2), in session on 2026-11-28: a decision table on the 37 old proposals, then "File the draft PR".
**Status:** AWAITING Z2 RATIFICATION. The merge of the pull request that adds this file is the ruling (Z2, 2026-11-25).
**Amends:** W6 of `Q-AGENT-WORKFLOWS-01`, which proposed lapsing all 37 at once.

## What this decides

All 37 candidates submitted 2026-09-08 to 09-19 have sat `awaiting_z2` for 67 to 80 days. W6 proposed lapsing all of them. Each row was read against `main` at 6924123: 14 of them describe things that are already built and running, and lapsing those would record a falsehood. This candidate sorts them instead.

| Decision | Count | What the merge does |
|---|---|---|
| RECORD | 14 | Ratified as in effect. Ten plain candidates gain a `## Disposition` section, so the reconcile job signs them on merge. Four board blocks get their in-effect option written in their `## Ruling` section. |
| LAPSE | 18 | Closed without deciding the question. Eight plain candidates move to `withdrawn` in the index. Ten board blocks take their own `later` option, which each block defines as a ruling that closes it: reconcile signs that `later` choice, so those ten end `ratified` with `choice: later`. Any can be refiled. |
| REJECT | 2 | Moved to `superseded` in the index, with the reason. `rejected` needs a Z2 signature, which a merge alone cannot write. |
| LEFT FOR Z2 | 3 | Untouched; still `awaiting_z2`. |

### RECORD (14)

| Candidate | Evidence it is in effect | Left over (not decided here) |
|---|---|---|
| Q-FRAMEWORK-MAPPING-01 | `CLAUDE.md` records it ratified 2026-10-02; `FRAMEWORK_MAPPING.md` hash matches; A8 in `haios-standing-audit.yml` | Its falsifier waiver is accepted with it |
| Q-RFM-01 | PR #312; blocking step in `findings-registry.yml` | `--enforce` was answered "turn on now" and not done; stays open under Q-RFM-01 |
| Q-TOOLCONTROL-01 | PR #304; `tool-manifest.yml` | Two MCP servers unscoped; root `CODEOWNERS` duplicate |
| Q-TOOLCONTROL-02 | PR #306; all tools categorized | — |
| Q-TOOLCONTROL-03 | `tool-manifest.yml` runs `.tool-control/selftest.py` | — |
| Q-GOVGATE-01 | `z2_ratification_gate.yml` runs real jobs; `.z1-control/validate.py` | `KNOWN_RATIFIERS` holds Night only |
| Q-RBE-01 | `RESOURCE_UNITS.yaml` RATIFIED; CAP event in `ledgers/RESOURCE_LEDGER.jsonl`; F-62/63/64 | Units file hash matches nothing |
| Q-REGISTRY-AUDIT-01 | Option B, `PLANNED_REPOS.md` | `ZONE_REGISTRY.md` title and counts drift |
| Q-REGISTRY-AUDIT-02 | Seven repos in `ZONE_REGISTRY.md` (Z-004 to Z-011), flat layout | — |
| Q-IC-BOARD-SEALS-01 | PRs #323, #325; seal check in `intent-os-refresh.yml` | IC not yet registered (own entry or fold into IC-030 is Z2's call); §A line not added |
| Q-BOARD-RULING-21 (d21) | Rendered dashboard committed with its receipt | Receipt dates from 2026-09-18 |
| Q-BOARD-RULING-23 (d23) | Refresh job opens no PR or issue (inferred from no bot output; the repo variable could not be read) | — |
| Q-BOARD-RULING-25 (d25) | Runbook §5 step 4: re-download after each merge | — |
| Q-BOARD-RULING-26 (d26) | Refresh job is push and dispatch only, no cron | — |

### LAPSE (18)

| Candidate | Why |
|---|---|
| Q-DOC-LIFECYCLE-01 | 108-file snapshot; `docs/` now holds 158 entries |
| Q-FRAMEWORK-MAPPING-INTEGRATION-01 | Deadline 2026-09-17 passed; replaced by Q-FRAMEWORK-AUDIT-DEPLOY-01 |
| Q-PHASE1-2-ROLLOUT-01 | All its dates passed; same replacement |
| Q-ADVREVIEW-CALIB-01 | No stage started in 77 days |
| Q-CGBG-PILOT-01 | Reviews a document not in this repository; window closed 2026-10-13 |
| Q-CGBG-BASELINE-01 | Tied to the pilot; no activity |
| Q-REGISTRY-AUDIT-03 | Gate never built; the count drift could return as a small check |
| Q-BOOT-STATE-MACHINE-01 | Unused prototype; open items carried by Q-BOOT-FINDINGS-SCAN-01 |
| Q-BOARD-PUBLISH-01 (d31) | `board/worker.mjs` now serves more than the block describes; deployment unverified |
| Q-BOARD-RULING-20 (d20) | §A step 3 is now PRIORITY_QUEUE |
| Q-BOARD-RULING-22 (d22) | No test scale-out since September |
| Q-BOARD-RULING-24 (d24) | Matters only if d23 turns auto-PR on |
| Q-BOARD-RULING-27 (d27) | One REQ record ever |
| Q-BOARD-RULING-28 (d28) | Nothing to mirror |
| Q-BOARD-RULING-29 (d29) | Counts stale (196 `smoke_test: true`, not 141) |
| Q-BOARD-RULING-30 (d30) | Board not re-read since 2026-09-27 |
| Q-BOARD-RULING-32 (d32) | No effect while the job only reports |
| Q-BOARD-RULING-33 (d33) | Held on d31, which lapses |

### REJECT (2)

| Candidate | Why |
|---|---|
| Q-NF-SCHEMA-01 | Z2 chose its rival Q-NF-ADAPTER-01 on 2026-11-15 |
| Q-RESEARCH-OPS-LOOP-AND-AUDITOR-01 | Auto-filing and auto-applying contradict Q-AGENT-WORKFLOWS-01 |

### Left for Z2 (3)

| Candidate | The live question |
|---|---|
| Q-DOCREVIEW-01 | Retire the nine HAIOS-COLLAB reports; name a document owner |
| Q-DOCREVIEW-02 | Write `DOCUMENT_CONTROL_PLAN.md` or remove the references to it |
| Q-BOOT-FINDINGS-SCAN-01 | Register two defects: `SESSION_RITUALS.md` claims a Section F spec with no body; `GOVERNANCE.md` cites a Section B Step 0 that does not exist |

## Limits

- The four RECORD board options and the ten `later` options are written by Z1, not tapped on the board. The `by:` line says so; the merge is the act.
- This sorts 37 candidates in one pull request instead of one per ruling file. The relay's one-file pull request is the tap route, not a limit on what one merge ratifies (Z2, 2026-11-25: the merge of any pull request that carries an `awaiting_z2` candidate ratifies it). Merging this pull request accepts the bulk form.
- `withdrawn` and `superseded` are the index's open statuses; neither carries a signature. There is no `lapsed` status, and adding one is a `.z1-control/` change this candidate does not make.
- The "left over" items are not decided here. Each can be filed as its own small candidate.

## Falsifier

This sort is wrong if, after the merge and the next reconcile run, any of these hold: a RECORD row's evidence path does not exist on `main`; a lapsed or rejected candidate is shown to be in active use (a workflow, tool or merged PR after 2026-11-28 that depends on it); or the reconcile job signs a plain candidate this file moves to `withdrawn` or `superseded`, or signs a board block with an option other than the one written here. Any one sends the matching row back to Z2.
