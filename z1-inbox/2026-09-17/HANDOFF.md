# Handoff — 2026-09-17 (Intent-OS refresh: the mechanism for automated updates)

**Session:** `session_01CePrSjPSB8Epbpq3Lj8oKj` (continued) · **Branch:** `claude/vigilant-newton-ko9pcr` · **Pinned:** `main` at `e2b9a7a`
**Position at close:** board HOLDS at HEAD (re-sealed: 3 mechanical rows by tool, 1 row by hand); harness 47 PASS · 1 FAIL of 48 (the registered ACAT finding); queue 46 candidates (this block included), 39 awaiting Z2, 38 past the 2-day window.

## What Z2 asked

*The inbox keeps growing — is there a mechanism for automated updates to the Intent-OS?* No. Between
09-16 and this session `main` moved nine commits and the board went STALE on four seals; nothing
noticed. This session builds the noticing and the mechanical half of the fixing, and asks Z2 to turn
the PR/issue half on.

## On this branch (awaiting merge)

| file | what |
|---|---|
| `tools/intent_os_board_reseal_v1_0.py` | MECHANICAL vs NEEDS-HUMAN drift; `--apply` re-hashes only the former; refuses otherwise; `--self-test` (8 plants); `HAIOS-TOOL-166` |
| `.github/workflows/intent-os-refresh.yml` | on sealed-path merges + daily: checks, harness, artifacts, summary; PR/issue half gated on `vars.INTENT_OS_REFRESH_AUTOPR` (d23) |
| `ui/intent-os-humanaios-v3_3.html` | re-read at `e2b9a7a`; `ratify.py` 1.2.0 row re-read by hand (Ruling 6 pending); `rev` advanced by the tool to the stamp of the last apply (the committed board carries it); `read.date` = `2026-09-17`, this session's human read |
| `ui/intent-os-test-dashboard-v1_0.html` | receipt of this run; W8 now includes the re-seal self-test |
| `z1-inbox/2026-09-17/Q-INTENTOS-REFRESH-01.md` | d23 enable · d24 rev by job · d25 local copies · KNOWN_RED list |
| runbook §6 · pathway §3 · `REPOSITORY_STRUCTURE.md` | cadence names the job and the tool |

## Findings scan

- **Observation (not a new class):** `.z1-control/ratify.py` 1.2.0 landed in #343 while its seal on the
  board still described 1.1; the board's own rule caught it as DRIFT, and the re-seal tool correctly
  classed it NEEDS-HUMAN. Ruling 6 (2026-09-16) on 1.2.0 is awaiting Z2 signature — nothing here
  decides it; the seal description says so.
- **Observation:** the queue's 2-day window now catches 38 of 38 awaiting candidates. The dashboard
  shows it; the number is Z2's.

## Receipt walk-back (claim → tree)

| claim | where |
|---|---|
| the tool re-hashed 3 rows and refused the 4th | receipt row `t0-board-reseal` (plants); this block's *The run* section; `git diff` of the board on this branch |
| the workflow parses and is report-only by default | strict-load receipt in the block; `if: vars.INTENT_OS_REFRESH_AUTOPR == 'true'` on both acting steps |
| board HOLDS at HEAD | `python3 tools/intent_os_board_check_v1_0.py` |

RECEIPT-GAP: none known.

## Next blockers

1. Z2: d23–d25 + KNOWN_RED (this block); d20–d22 choices (accepted, unrecorded); Ruling 6; d2, d3, d5–d16.
2. `Q-INTENTOS-LAUNCH-01` falsifier: a ruling through the relay by **2026-09-30**.
3. Local copies: until d25, refresh a `~/Downloads` copy by replacing the file with the repository's after each merge — the filename is frozen (d19), so the browser's saved taps survive and the new `rev` loads on restore.
