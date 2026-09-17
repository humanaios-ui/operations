# Candidate Block: Q-INTENTOS-REFRESH-01 — automated Intent-OS refresh: re-seal what a job may, file what a human must

**Z1 Proposer:** Claude (AI agent)
**Date Submitted:** 2026-09-17
**Pinned SHA:** `e2b9a7a` (main; board re-read there: HOLDS · 31 MATCH · 5 ABSENT-CONFIRMED · 7 UNCHECKED)
**Branch:** `claude/vigilant-newton-ko9pcr`
**Phase:** 1 (the control surface keeps itself honest between sessions)
**Status:** AWAITING Z2 RATIFICATION
**Follows:** `Q-INTENTOS-LAUNCH-01` (ACCEPT 09-14) · `Q-INTENTOS-TEST-01` (ACCEPT 09-16, `eb568ab4…`; its d20–d22 are accepted-as-asked and not yet recorded as choices)

---

## §A Position · Destination · Probability

**Position:** Z2 asked, on 2026-09-17: *the inbox keeps growing — is there a mechanism for automated
updates to the Intent-OS?* There was not. Between the 09-16 run and this one, `main` took nine commits
(#343, #347–#353, the ACCEPT commit) and the board went STALE with four drifted seals:

| seal | why it drifted | kind |
|---|---|---|
| `z1-inbox/INDEX.yaml` | three candidates filed, three ratified, records added | mechanical — bytes change by construction |
| `REGISTERED.md` | Z2 appended | mechanical |
| `ledgers/NF_LEDGER.jsonl` | append-only ledger grew | mechanical |
| `.z1-control/ratify.py` | **1.2.0 landed in #343** — the signature tool now writes the index fields, the records entry and the counts in one act; Ruling 6 on it is awaiting signature | **a change of meaning — a human must say what the new bytes mean** |

Nothing noticed. The dashboard on `main` still showed the 09-16 receipt. A Z1 session had to open,
re-seal, rerun, commit. That is the gap: the board's rule is *green means a fetch verified it*, and
between sessions nobody fetched.

**Destination:** a job that runs the fetch on every merge that touches a sealed file and daily; that
re-hashes only the seals whose drift is mechanical and says so on each row; that refuses to touch a
seal whose meaning changed and instead opens one issue naming it; that publishes the receipt and the
rendered pages as run artifacts; and that stays **report-only** until Z2 turns the PR/issue half on
with one repository variable. Built in this PR. Turned on by d23.

**Probability:** **0.70** that, with d23 enabled, no session in the following 14 days opens on a STALE
board (C22). **0.55** that the STALE issue fires at least once on a genuine NEEDS-HUMAN change by
2026-10-07 (C23) — tools do change; the 09-16 → 09-17 window alone produced one.

---

## What was built (Z1; all receipts operated this session)

| file | what it is | proof |
|---|---|---|
| `tools/intent_os_board_reseal_v1_0.py` | classifies the checker's drift: **MECHANICAL** (a hash-to-hash DRIFT on `z1-inbox/INDEX.yaml`, `REGISTERED.md`, `PRIORITY_QUEUE.md`, `ledgers/NF_LEDGER.jsonl`, `ledgers/RESOURCE_LEDGER.jsonl`, `Z1_INBOX_INDEX.md`, `TOOLS_MANIFEST.md`, `CONTROLLED_DOCUMENTS.md`) vs **NEEDS-HUMAN** (everything else; any MISSING / NOT-IN-HISTORY row; a seal that said ABSENT and now finds a file). `--apply` re-hashes only mechanical rows, rewrites each description to *"(re-sealed <date> at <head>; content changed, description not re-read)"*, moves `read.against` to HEAD (the old sha joins the prior-reads list), advances `rev` strictly (ISO stamp to the second, with a zero-padded ordinal if the clock has not moved past the current rev — so an open browser copy always loads the new data on restore and keeps its taps), leaves `read.date` alone (it records the last *human* read), and refuses outright if any NEEDS-HUMAN row exists. Exit 0 HOLDS · 1 mechanical · 2 human. | `--self-test` plants: clean → HOLDS; inbox+registry → MECHANICAL, applied, HOLDS, notes replaced not stacked, prior read kept, rev advanced, read.date untouched; apply on HOLDS → no-op; rev already ahead of the clock → `+001`, `+002`, each lexically greater; ABSENT seal now present on a mechanical path → NEEDS-HUMAN, refused; a tool changed alongside the inbox → NEEDS-HUMAN, refused, board byte-identical; a mechanical path MISSING → NEEDS-HUMAN. Registered `HAIOS-TOOL-166`. Row `t0-board-reseal` in the harness. |
| `.github/workflows/intent-os-refresh.yml` | on every push to `main` (the seal set changes as the board is re-read, so no path filter stays complete), daily 05:41 UTC, and by hand — the job is pinned to `main`, so a dispatch against another ref is skipped and modified code never runs with its write token: tool self-tests first (a job that cannot tell a plant from a pass does not judge); seal check; drift classification; harness `--render`; job summary; receipt + board report + rendered pages as a 30-day run artifact (reports live under gitignored `outputs/`, excluded from the receipt's `tree_hash`). Step outputs derived from the checkout reach the shell through `env` and are quoted as data; row ids are restricted to `[a-z0-9-]` before they become outputs. **Gated on `vars.INTENT_OS_REFRESH_AUTOPR == 'true'`:** MECHANICAL → `--apply`, re-render, one PR `intent-os/refresh` (updated in place, `audit:auto`, `smag_p: 0.90`, `molt_tier_claimed: 0`); NEEDS-HUMAN or a red harness row not in `INTENT_OS_KNOWN_RED` → one `intent-os-stale` issue (commented in place). It never signs, never touches `z1-inbox/`, never publishes the board (d17). | parses under `workflow-lint.yml`'s strict duplicate-key loader; `on: push · schedule · workflow_dispatch`; `if: github.ref == 'refs/heads/main'`; permissions `contents · pull-requests · issues: write` (same as `smag-consolidate.yml`) |
| the board, re-read at `e2b9a7a` | three mechanical rows re-hashed by the tool; the `ratify.py` row re-read by hand (description now says what 1.2.0 does and that Ruling 6 is pending); `read.against` → `e2b9a7a`; `rev` advanced to the ISO stamp of the last apply (the committed board carries the exact value); `read.date` stays `2026-09-17` from this session's human read | checker HOLDS at HEAD, 0 behind |
| the dashboard, re-rendered | receipt of the run below | 48 rows |
| `docs/INTENT_OS_BOARD_RUNBOOK.md` §6 · `docs/INTENT_OS_TEST_PATHWAY.md` §3 · `REPOSITORY_STRUCTURE.md` | the cadence now names the job and the tool; a session opens by checking for the `intent-os-stale` issue | `t4-repo-index` PASS |

## The run (2026-09-17T00:30:00Z on `e2b9a7a` + this branch)

```
T0 self-tests             GREEN  PASS=18
T1 governance integrity   GREEN  PASS=17
T2 board + relay          GREEN  PASS=4
T3 ci gates               RED    FAIL=1 PASS=5     ← t3-pytest-acat, the F-CAND registered in Q-INTENTOS-TEST-01
T4 cross-repo             GREEN  PASS=3
counts: FAIL=1, PASS=47 · verdict: RED
board: HOLDS · queue: 46 candidates (this block included) · 39 awaiting Z2 · 38 past the 2-day window
```

(The receipt embedded in the dashboard is the final run on this branch, after this block was
indexed; the numbers above are that receipt's.)

The re-seal, as operated on the real drift:

```
python3 tools/intent_os_board_reseal_v1_0.py --check     → NEEDS-HUMAN (3 mechanical rows · .z1-control/ratify.py DRIFT) · exit 2
  (Z1 re-read the ratify.py row by hand: description rewritten, sha b401a26ba824346f)
python3 tools/intent_os_board_reseal_v1_0.py --apply     → MECHANICAL · written — REGISTERED.md, ledgers/NF_LEDGER.jsonl, z1-inbox/INDEX.yaml, read.against · verdict after: HOLDS · exit 0
```

That is the whole design in one session: the job would have re-hashed three rows and stopped on the
fourth with an issue; the fourth took a human sentence.

## What Z2 is asked to decide

| id | question | Z1 reading (no preference encoded) |
|---|---|---|
| **d23** | Enable the PR/issue half: set repository variable `INTENT_OS_REFRESH_AUTOPR=true`, or keep the job report-only (summary + artifacts, nothing opened)? | Report-only already ends the silence — every merge produces a summary line reading HOLDS / MECHANICAL / NEEDS-HUMAN. Enabling adds one bot PR per drift that a human still merges, and one issue that a human still closes. Nothing is signed either way. |
| **d24** | An automated re-seal advances `rev`, so a copy of the board open in a browser is superseded by the new data on its next restore (taps kept, as the board's own rule says). Accept that a *job's* read may supersede an open copy, or reserve `rev` advances for human re-reads? | If reserved, an open copy keeps showing hashes the tree no longer has until a session re-reads; if accepted, an open copy's narrative fields (readline, gauges) can age while its hashes stay true — which the re-sealed descriptions say out loud. |
| **d25** | Local copies (e.g. one in `~/Downloads`): coordinate by re-downloading `ui/intent-os-humanaios-v3_3.html` from the repository after each refresh (no new surface), or publish a rolling release asset `intent-os-latest` on this repository so a copy has one stable URL to refresh from? | d17 ruled *local only, no `site/`, no Pages*. A release asset is repository-scoped (the same access as the file) but it is a new surface; Z2's read whether it is inside d17. Path freeze (d19) already makes the filename stable, so the localStorage key, and the taps, survive a replace either way. |
| **KNOWN_RED** | The job carries `INTENT_OS_KNOWN_RED: t3-pytest-acat` so the registered F-CAND does not open a STALE issue on every run. Accept that list as the place a registered-but-unfixed red row is named, or require the list to be empty (every red row files)? | The list is in the workflow file, so adding to it is a reviewed change; it is not a way to hide a row (the row stays RED on the dashboard and in the receipt). |

Also on the table, from `Q-INTENTOS-TEST-01`'s ACCEPT: **d20 · d21 · d22** were accepted as asked but
no choice is recorded in a ruling file. This block assumes the status quo for d21 (the dashboard
carries the receipt; nothing standalone in the tree) — the refresh PR commits only the board and the
dashboard.

## Predictions (pre-registered)

| id | text | p | resolves |
|---|---|---|---|
| C22 | with d23 enabled, no Z1 session in the following 14 days opens on a STALE board | 0.70 | d23 + 14 days |
| C23 | the `intent-os-stale` issue fires at least once on a genuine NEEDS-HUMAN change | 0.55 | 2026-10-07 |
| C24 | at least one refresh PR is merged without a human editing it | 0.65 | 2026-10-07 |

## Falsifier

Row-level: if the tool ever re-hashes a NEEDS-HUMAN row — any re-sealed description on a path outside
the MECHANICAL list — it is laundering drift, and it is pulled from the manifest. `--self-test` plants
exactly that case (a tool change beside an inbox change) and proves the refusal.

Surface-level, by **2026-10-07**: with d23 enabled, if (a) a merge to `main` that drifts only mechanical
seals leaves the board STALE for more than 24 hours with no refresh PR open, or (b) a NEEDS-HUMAN drift
sits for more than 24 hours with no `intent-os-stale` issue, the job is not doing its work: disable it
and return the cadence to runbook §6 as it was. If d23 is not ruled by then, (a) and (b) are VOID and
only the row-level falsifier stands.

## Receipts (operated this session)

```
python3 tools/intent_os_board_reseal_v1_0.py --self-test      → SELF-TEST PASS (6 plants)
python3 tools/intent_os_board_reseal_v1_0.py --check          → NEEDS-HUMAN · exit 2 (before the ratify.py re-read)
python3 tools/intent_os_board_reseal_v1_0.py --apply          → MECHANICAL · 3 rows + read.against · HOLDS · exit 0 (after)
python3 tools/intent_os_board_check_v1_0.py                   → HOLDS · read.against e2b9a7a at HEAD
python3 tools/intent_os_test_harness_v1_0.py --render         → 47 PASS · 1 FAIL · RED (t3-pytest-acat) · 48 rows
python3 .tool-control/scan.py --check && python3 .tool-control/validate.py && python3 .tool-control/render.py --check → 158 tools, in sync
strict YAML load of .github/workflows/intent-os-refresh.yml   → parses; on: push · schedule · workflow_dispatch; 12 steps
```

Attribution: Z1 (Claude) proposes; Z2 (Night) ratifies by hash via `.z1-control/ratify.py`; Z3 lands.
