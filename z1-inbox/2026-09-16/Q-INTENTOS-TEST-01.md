# Candidate Block: Q-INTENTOS-TEST-01 — Intent-OS test surface: harness, dashboard, pathway; decide adoption and scale-out

**Z1 Proposer:** Claude (AI agent)
**Date Submitted:** 2026-09-16
**Pinned SHA:** `7ff302d94fb0329266b7106860a04e0c089c61d8` (main; REGISTERED.md sha256 `38192e8bec42a874…`, 4147 lines; board HOLDS at that read)
**Branch:** `claude/vigilant-newton-ko9pcr`
**Phase:** 1 (control surface for testing what the control surface rests on)
**Status:** AWAITING Z2 RATIFICATION
**Follows:** `z1-inbox/2026-09-14/Q-INTENTOS-LAUNCH-01.md` (ACCEPT 2026-09-14; d17 local only · d18 z1-inbox landing · d19 path freeze)

---

## §A Position · Destination · Probability

**Position:** `operations` pinned at `7ff302d`. The Intent-OS board is launched and HOLDS (31 MATCH · 5
ABSENT-CONFIRMED · 7 UNCHECKED). Its falsifier (Q-INTENTOS-LAUNCH-01) needs a ruling to land through the
relay by 2026-09-30; none has. Until this block, "is the framework working?" had no single command: 17
tools carried their own `--self-test`, five workflows carried their own blocking steps, the relay had
never been driven through a socket, and no browser had been asked whether a tap survives reload. Z2
said it: *multiple areas of the work cannot be visualised, so they cannot be understood.*

**Destination:** one command that runs every check the surface rests on, writes one receipt, and
renders one page with four panels — the ruling workflow, the Z1/Z2/Z3 authority map, the test matrix,
and the live board/queue/zones — where every box is lit only by the check that exercised it. Then the
same shape carried to the other active zones, index first.

**Probability:** **0.60** that the harness is GREEN on `main` by 2026-09-30 (C19) — it is RED today on
one pre-existing defect, named below, whose fix is ~10 lines in tests this block does not touch.
**0.45** that a second zone has a `REPOSITORY_STRUCTURE.md` that passes `t4-repo-index` by 2026-10-15
(C20). Both below 0.65 because each needs a session Z2 has not scheduled.

---

## What was built (Z1, no Z2 act required; all receipts operated this session)

| file | what it is | proof |
|---|---|---|
| `tools/intent_os_test_harness_v1_0.py` | registry of 46 checks in five tiers; runs each, records exit / duration / tail; writes `outputs/intent_os_test_results.json`; `--render` injects it into the dashboard; `--self-test` plants PASS · FAIL · expected-nonzero · TIMEOUT · SKIP (module) · SKIP (binary) · ERROR and proves each fires, proves empty and all-SKIP runs are RED, proves `--render` round-trips and escapes `</script>`, proves the index and zone checks fail on plants | `SELF-TEST PASS`; registered `HAIOS-TOOL-164` by `scan.py` (156 tools) |
| `ui/intent-os-test-dashboard-v1_0.html` | four panels; renders **only** from the embedded receipt; a page without one says so in red; import/export a receipt; no persistence of results (prefs only) | `node --check` PASS; headless Chromium: renders, no page errors, node click filters the matrix, tail toggles |
| `docs/INTENT_OS_TEST_PATHWAY.md` | tiers, roles, session order (extends §A/§B), falsifiers, scale-out order | `lifecycle: consumed`, consumer = the harness |
| `REPOSITORY_STRUCTURE.md` (rewritten) | the index, now with one rule: every backticked path is a claim `t4-repo-index` verifies | first version named 6 paths that did not exist; three more rounds of bare filenames were caught before it held (158 paths, 0 missing) |
| the receipt (`schema intentos/test_results_v1`, `git.head 7ff302d`, working tree dirty = this branch before commit) | written to `outputs/intent_os_test_results.json`, which `.gitignore` excludes; it travels **embedded in the dashboard** (`RESULTS` block) — whether a standalone copy belongs in the tree is d21 | `ui/intent-os-test-dashboard-v1_0.html` carries it |

## The run (2026-09-16T01:24:04Z on 7ff302d + this branch)

```
T0 self-tests             GREEN  PASS=17
T1 governance integrity   GREEN  PASS=17
T2 board + relay          GREEN  PASS=4
T3 ci gates               RED    FAIL=1 PASS=4
T4 cross-repo             GREEN  PASS=3
counts: FAIL=1, PASS=45 · verdict: RED
```

**T2, in full, because it is the first time these were operated:**

- `t2-relay-roundtrip` — the real `tools/decision_relay.py` started with `DRY_RUN=1` on a loopback port
  over a fixture inbox (the real `Q-BOARD-RULING-06.md`, a minimal `INDEX.yaml`, the real `.z1-control/`);
  driven through the socket with the board's exact request shapes: `GET /` (dry, signs_as Night from the
  relay's own environment); `OPTIONS /decide` → 204 with `Authorization` in Allow-Headers (the browser
  preflight); bad `X-Sig` → 401; signed `/decide` → PENDING with a 64-hex hash, the choice written into
  the candidate on the local copy, **nothing written under the repository**; replayed nonce → 409; wrong
  hash to `/ratify` → REFUSED; echoed hash → RATIFIED with a signature; `INDEX.yaml` shows
  `status: ratified` and the signature; `Z2_RULINGS_2026-09-16.md` carries it; `Z1_INBOX_INDEX.md`
  regenerated; **`.z1-control/ratify.py --verify` on the landed copy → "All pinned signatures verify"**;
  second `/ratify` → REFUSED, files byte-identical. 0.2 s.
- `t2-browser-persist` — headless Chromium opens the board from `file://`: 20 steps render, no page
  errors, persistence note says `local`; tap the last step on the rail (opens its card), tap its checkbox,
  reload → still checked and the rail step is green; tap restored; the dashboard renders with its verdict
  badge. 1.3 s. (This closes the `ecc-tools` finding on #345: *user-facing UI changes may ship without
  browser coverage*.)

**The one red row — a finding, filed here, not fixed here (F-CAND):**

- `t3-pytest-acat` — `acat/tests/test_app_routes.py::test_human_score_route_is_registered` and three
  tests in `acat/tests/test_assess_endpoint.py` get **503** where they expect 200/422/502.
  `acat/api/security.py` (interim mitigation, audit S-062726 P0-URGENT) answers 503 when
  `ACAT_WRITE_TOKEN` is unset and 401 when the `X-ACAT-Write-Token` header is missing; the four tests
  set neither (verified: with the env set they get 401). They predate the gate, and no workflow runs
  them — `quality-baseline.yml` runs only `acat/tests/test_tool_trace_schema.py`. 78 of 82 pass.
  **Proposed patch (separate PR, tests only):** a conftest fixture that `monkeypatch.setenv`s the token
  and a TestClient that sends the header; then add `acat/tests/` to the quality-baseline list.
- Environment, not defect: `t3-mypy` reproduces CI's exact command and passes; on a machine where
  `requests` is installed without `types-requests`, the same command fails on
  `src/humanaios_operations/profile.py:10` (`import-untyped`). GitHub runners ship `requests`; the
  step is green on `main` today (run 331), so the stubs are present there or the import resolves
  differently. Noted for the day it goes red.

## What Z2 is asked to decide

| id | question | Z1 reading (no preference encoded) |
|---|---|---|
| **d20** | Adopt the harness as §A step 3 — a session cites the board only on a GREEN run or one whose every red row is named in a candidate — or keep it advisory? | Adoption makes the pathway's surface falsifier bite; advisory keeps §A at its current three lines. The run costs 17 s. |
| **d21** | Commit the rendered dashboard and receipt with each run (the tree carries the last verified state; `git.head` inside the receipt is the SHA it ran on), or keep `main`'s dashboard unrendered and render locally per session? | Committed = anyone opening the file from the repository sees the last run; unrendered = the file on `main` is always "NO RUN" until someone runs it, which is honest but empty. |
| **d22** | Scale-out order: the zone registry's (Z-001 humanaios first), or name the first repo? | Pathway §5: per repo, index → registry → surface. The relay, the z2 gate and d17 do not copy. |
| **F-CAND** | Register the ACAT test finding above and accept, edit or refuse the proposed patch as a Z1 task. | It is the only thing between RED and GREEN today. |

## Predictions (pre-registered)

| id | text | p | resolves |
|---|---|---|---|
| C19 | `python3 tools/intent_os_test_harness_v1_0.py` returns GREEN on `main` | 0.60 | 2026-09-30 |
| C20 | a second active zone has a `REPOSITORY_STRUCTURE.md` that passes `t4-repo-index` run with `--root` at that repo | 0.45 | 2026-10-15 |
| C21 | the harness catches at least one regression (a row that was PASS goes FAIL on a later `main`) before a human reports it | 0.55 | 2026-10-31 |

## Falsifier

Row-level: any check that PASSES when its subject is broken. `--self-test` is the standing test of that
claim; if a plant ever lands green, pull the harness from `tools-manifest.yaml`.

Surface-level, by **2026-09-30**: if (a) the harness is RED on `main` and no candidate block names the
failing row, or (b) no Z2 session has run `--tier T2` before a relay ruling, or (c) the dashboard on
`main` embeds a receipt whose `git.head` is not an ancestor of `main` — then the dashboard is a report
and not a control: retire it to `docs/_archive/` with its sha and keep the harness as a CI step only.

Honesty check: the receipt's counts and the dashboard's badges are one JSON; if they disagree the
renderer is wrong, never the run.

## Receipts (operated this session)

```
python3 tools/intent_os_test_harness_v1_0.py --self-test      → SELF-TEST PASS (21 plants)
python3 tools/intent_os_test_harness_v1_0.py --render         → 45 PASS · 1 FAIL · RED · receipt written · dashboard rendered
python3 tools/intent_os_test_harness_v1_0.py --tier T2 --out - → 4 PASS · GREEN
python3 tools/intent_os_board_check_v1_0.py                   → HOLDS (31 MATCH · 5 ABSENT-CONFIRMED · 7 UNCHECKED)
python3 .tool-control/scan.py && validate.py && render.py --check → 156 tools, no violations, in sync
python3 .doc-control/validate.py && render.py --check         → 46 registered documents, no violations, in sync
python3 .z1-control/validate.py && render.py --check          → after this entry: see the PR's z2 gate
headless Chromium (playwright 1.63, /opt/pw-browsers/chromium) → dashboard: verdict RED, 17 nodes, 46 rows, no page errors
```

Attribution: Z1 (Claude) proposes; Z2 (Night) ratifies by hash via `.z1-control/ratify.py`; Z3 lands.
