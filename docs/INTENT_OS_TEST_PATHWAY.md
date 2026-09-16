---
title: Intent-OS test pathway — T0 to T4, from this repository outward
status: draft
lifecycle: consumed
consumer: tools/intent_os_test_harness_v1_0.py   # the harness runs the registry this pathway describes
dashboard: ui/intent-os-test-dashboard-v1_0.html
board: ui/intent-os-humanaios-v3_3.html
index: REPOSITORY_STRUCTURE.md
written: 2026-09-16
authority: Z1 draft; the launch of the test surface is asked in z1-inbox/2026-09-16/Q-INTENTOS-TEST-01.md and is Z2's
---

# Intent-OS test pathway

The board's rule — **green means a fetch verified it, not that someone said so** — applied to the whole
control surface, in tiers, so that "is the framework working?" has one command and one answer.

```
python3 tools/intent_os_test_harness_v1_0.py --render     # run T0–T4, write the receipt, render the dashboard
open ui/intent-os-test-dashboard-v1_0.html                 # local only (d17); nothing is published
```

Exit 0 = GREEN, exit 2 = RED. The receipt is written to `outputs/intent_os_test_results.json` (a gitignored
directory) and embedded in the dashboard by `--render`; the dashboard renders from that embedded receipt
and from nothing else, so a dashboard opened without a run says so in red.

## 1. The tiers

| tier | what it proves | how | passes when |
|---|---|---|---|
| **T0 self-tests** | every tool can tell a plant from a pass | `--self-test` / `--smoke-test` on 17 tools (board checker, relay, the three control layers, lints, gates) | each exits 0 |
| **T1 governance integrity** | the tree is internally consistent *right now* | the z2 gate's ERROR steps, signature re-verification, manifest/doc-control `--check`s, YAML parses, graph endpoints, board seals HOLD, fail-closed refusals | each exits as expected (`ic_scope_check` must exit 2) |
| **T2 board + relay** | a Z2 session can open, tap, land and ratify | `node --check` on both pages; the real relay on a loopback port answering a signed `/decide` → PENDING hash → `/ratify` → signature that `.z1-control/ratify.py --verify` accepts; headless Chromium keeps a tap across reload | every step OK; nothing written under the repo |
| **T3 ci gates** | what `quality-baseline.yml` blocks on, plus the suites it does not run | its exact pytest list, its Ruff step (`--select=E9,F63,F7,F82` over `src/`, `acat/api/services`, `tools/tests`, `tests`), its mypy step; and `tests/`, `tools/tests/`, `acat/tests/` in full | each exits 0; SKIP (never green) when pytest, mypy or ruff is absent locally |
| **T4 cross-repo** | the scale-out surface is real | `ZONE_REGISTRY.md` tables populated and `operations` ACTIVE; `PLANNED_REPOS.md` present; every path `REPOSITORY_STRUCTURE.md` names exists | each check OK |

A tier is GREEN only if it has at least one PASS and no FAIL/TIMEOUT/ERROR. A SKIP is listed and never
counted. The whole run is GREEN only if every tier that ran is GREEN.

## 2. Beta-test roles

| role | who | runs | reads | owes |
|---|---|---|---|---|
| **operator** | Z1 (Claude) in any session | the harness, before citing the board or the dashboard | the table; the FAIL tails | a RECEIPT-GAP row in the handoff for any FAIL it cannot fix in-session |
| **owner** | Z2 (Night) | the harness with `--tier T2` before ruling through the relay | the dashboard's four panels | rulings on d2, d3, d5–d16; the launch decision on the test surface |
| **lander** | Z3 (relay machine) | `--tier T1 T2` after every landing | T1 signatures, T2 round trip | nothing lands on a RED T1 |
| **scale-out tester** | a session in any other of the 12 active zones | `--tier T4` against that repo (see §5) | R1/R2 on the dashboard | a per-repo `REPOSITORY_STRUCTURE.md` that passes `t4-repo-index` |

## 3. Session order (extends SESSION_RITUALS §A / §B)

1. `git fetch origin && git rev-parse HEAD` — pin.
2. `python3 tools/intent_os_board_check_v1_0.py` — the board HOLDS, or re-read first (runbook §3).
3. `python3 tools/intent_os_test_harness_v1_0.py --render` — everything else.
4. Work.
5. Before close: run 3 again. A FAIL that this session introduced is fixed or filed; a FAIL that was
   already there is cited by id in the handoff with its tail.
6. Commit the rendered dashboard with the work (it carries the receipt in its `RESULTS` block; the
   standalone `outputs/` copy is gitignored). `git.head` inside the receipt is the commit it ran on
   and `git.tree_hash` is the working tree it ran on with the dashboard and `outputs/` excluded, so a
   reader can rerun the harness on that commit and compare. Whether a standalone receipt also belongs
   in the tree is **d21**; until it rules, this step is the dashboard only.

## 4. Falsifiers (what proves this pathway is theatre)

- **Row-level.** Any check that PASSES when its subject is broken. Test: `--self-test` plants PASS,
  FAIL, expected-nonzero, TIMEOUT, SKIP, ERROR and proves each classification fires; a planted absent
  path in the repo index → FAIL; `operations` missing from the zone registry → FAIL; empty and
  all-SKIP runs → RED. If a plant lands green, the harness is pulled from the manifest.
- **Surface-level.** By **2026-09-30**: (a) the harness is RED on `main` with no candidate block naming
  the failing id, or (b) no Z2 session has run `--tier T2` before a relay ruling, or (c) the dashboard
  on `main` embeds a receipt whose `git.head` is not an ancestor of `main`. Any one → the dashboard is
  a report, not a control: retire it to `docs/_archive/` with its sha; keep the harness as a CI step
  only.
- **Honesty check.** The receipt's counts must match the dashboard's badges by construction (one JSON).
  If they ever disagree, the renderer is wrong, not the run.

## 5. Scale-out (after this repository is GREEN)

The order is the zone registry's, active zones first. Per repo, three things, in this order:

1. **Index.** A `REPOSITORY_STRUCTURE.md` written from `find`/`ls` output in that repo, never from
   memory. `t4-repo-index` is the test: every backticked path exists.
2. **Registry.** The repo's `--self-test`/`--smoke-test` tools and its CI's blocking steps, added as
   T0/T1/T3 rows in a per-repo registry (the harness takes `--root`; a per-repo registry file is the
   first change to make when the second repo lands — one registry per zone, one runner).
3. **Surface.** The repo's own board (`ui/intent-os-<zone>.html`, same data shape, same checker) once
   it has a step list and at least one seal. Until then the dashboard's R1/R2 nodes are its board.

What does **not** scale by copying: the relay (one per Z2 machine, signs as one ratifier), the z2 gate
(runs where INDEX.yaml lives), and d17 (local only) — a zone that wants a published surface asks for
its own ruling.

## 6. What is asked of Z2 (z1-inbox/2026-09-16/Q-INTENTOS-TEST-01.md)

- **d20** — adopt the harness as the §A step 3 above (a session cites the board only on a GREEN or
  explained run), or keep it advisory.
- **d21** — commit the rendered dashboard with each run (the receipt lives in the tree), or keep the
  dashboard unrendered on `main` and render locally per session.
- **d22** — scale-out order: the zone registry's order, or name the first repo.

## 7. Files

| file | role |
|---|---|
| `tools/intent_os_test_harness_v1_0.py` | registry + runner + receipt + `--render` + `--self-test` |
| `ui/intent-os-test-dashboard-v1_0.html` | four panels: ruling workflow · Z1/Z2/Z3 gates · test matrix · live board/queue/zones — renders from the embedded receipt only |
| `outputs/intent_os_test_results.json` | the last receipt on this machine (schema `intentos/test_results_v1`); gitignored — the copy in the tree is the one embedded in the dashboard (d21) |
| `docs/INTENT_OS_BOARD_RUNBOOK.md` | open · read · rule · land · re-check the board itself |
| `REPOSITORY_STRUCTURE.md` | the index T4 verifies |
