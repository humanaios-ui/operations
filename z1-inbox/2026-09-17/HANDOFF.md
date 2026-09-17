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
| `.github/workflows/intent-os-refresh.yml` | on every push to `main` and by hand (event-driven only; no clock schedule — see *Resource-based grounding* below): checks, harness, artifacts, summary; PR/issue half gated on `vars.INTENT_OS_REFRESH_AUTOPR` (d23) |
| `ui/intent-os-humanaios-v3_3.html` | re-read at `e2b9a7a`; `ratify.py` 1.2.0 row re-read by hand (Ruling 6 pending); `rev` advanced by the tool to the stamp of the last apply (the committed board carries it); `read.date` = `2026-09-17`, this session's human read |
| `ui/intent-os-test-dashboard-v1_0.html` | receipt of this run; W8 now includes the re-seal self-test; **§ 5 Agent requests** (step 2 of the approved bus plan): stages `requested → taken → pr → merged` from each record's Fulfilment, rendered from the receipt; *Fetch live from main* on click re-hashes every record in the browser |
| `tools/intent_os_requests_v1_0.py` | the bus reader behind § 5: hashes recomputed, stage from Fulfilment only (no time-based state), `--check` for the harness (`t0-requests`, `t1-requests`); `HAIOS-TOOL-167` |
| `z1-inbox/2026-09-17/Q-INTENTOS-REFRESH-01.md` | d23 enable · d24 rev by job · d25 local copies · KNOWN_RED list |
| runbook §6 · pathway §3 · `REPOSITORY_STRUCTURE.md` | cadence names the job and the tool |

## Resource-based grounding (Z2 instruction, 2026-09-17)

*No AI-imposed time-frames; time-frames only where a regulatory authority requires them; if the
resources are available, we process.* Applied to this session's own artifacts before going further:

| was | now |
|---|---|
| relay `/task` capped requests at 99 per day | no quota; the day in a `REQ-` id is a namespace, the counter grows |
| relay `/assist` prompt asked for "probability … within 30 days" | "for the resources it consumes"; no calendar horizon |
| `intent-os-refresh.yml` ran daily at 05:41 UTC | event-driven only: every push to `main`, and by hand |
| `Q-INTENTOS-REFRESH-01` falsifier "by 2026-10-07 / 24 hours"; predictions resolving on dates | measured over the next 20 merges / 10 sessions / the first event; d26 asks Z2 to confirm |
| dashboard headlined "N past the 2-day window" in red | the validator's fact, labelled pre-RBE (Ruling 5), not a deadline |

Not Z1's to change, recorded for Z2: `.z1-control/validate.py`'s `decision_window_days: 2` (Ruling 5's
mechanism unspecified); the board's dated *Deadlines* and *we'll know by* columns (C1–C18 carry dates);
the ratified `Q-INTENTOS-TEST-01`'s dated falsifier (editing a ratified candidate breaks its signature).
The relay's 300-second request-skew check stays: it is replay protection, a correctness resource, not
a work deadline.

## Step 3 (after #377 merged): tiers T5–T7

| tier | what it measures | first run |
|---|---|---|
| **T5 manifest smoke** | every `smoke_test: true` claim in `tools-manifest.yaml`, run with the flag the tool's source carries; generated, not curated (T0's rows are not repeated) | 125 rows · 91 PASS · 16 FAIL · 18 SKIP (no flag in the source) — the whole tier runs in about 13 seconds |
| **T6 service boot** | `acat.api.app` boots under FastAPI's `TestClient`; three health routes answer | see the receipt on this branch |
| **T7 live provider** | one real `/assist` call through the relay with `DRY_RUN` removed | SKIP without `ANTHROPIC_API_KEY` — listed, never green by default |

The board's `read.against` was re-pointed by hand to `1b7cd96` (the squash of #377): its tree is byte-identical
to the branch head the read was made at, and a squash leaves that head out of `main`'s history, so the
re-seal tool correctly refused (NEEDS-HUMAN). This will recur on every squash-merge — d24/d25 territory.

## Findings scan

- **IC-candidate (manifest field overstates), for Z2 to register:** `tools-manifest.yaml` sets `smoke_test: true`
  from a text match (`.tool-control/scan.py`: the words "smoke test" anywhere in the file), not from a flag that
  runs. Measured by T5 on its first run: of 141 tools claiming a smoke test, 106 pass, **17 fail** (missing
  modules, `argparse` demanding other arguments, one `SyntaxError`, two tools whose parser does not know
  `--smoke-test`) and **18 carry no `--smoke-test`/`--self-test` at all**. The field is honest as "mentions a smoke
  test" and dishonest as "has one". Proposed mechanism (not applied here): scan.py records `smoke_flag:
  --smoke-test|--self-test|none` from the source, and the harness's T5 row is the proof. Until then the tier is
  the measurement, re-taken on every run.

- **IC-050-class occurrence (gate not enforced), for Z2 to register:** #354 (`07915e6`, 2026-09-16) landed
  `z1-inbox/2026-09-16/PHASE3_LAUNCH.md` and `PHASE3_EXECUTION_CHECKLIST.md` without index entries.
  `.z1-control/validate.py`'s coverage rule — the z2 gate's ERROR step — was red on `main` from that merge
  until this session indexed them as records (harness row `t1-z1-inbox` caught it on the first run after
  the branch restart from `0fe7782`). Whether the gate ran and did not block, or did not run, is Z2's to read
  from the #354 checks; the handoff of the 09-16 second session records the same class on #348.
- **Latent relay defect, fixed in this session's relay v0.4.0:** the relay's index helpers assumed 2-space
  indented entries; `ratify.py` 1.2.0 (09-16) rewrote `INDEX.yaml` with entries at column 0, so a live
  `/decide` against the current index would not have found its candidate. Neither self-test nor the harness
  fixture used the new shape. Both now do.
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
