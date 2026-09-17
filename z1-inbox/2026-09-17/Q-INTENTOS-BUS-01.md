# Candidate Block: Q-INTENTOS-BUS-01 — the agent bus: model endpoint, issue mirror, the smoke contract, the squash pointer

**Z1 Proposer:** Claude (AI agent)
**Date Submitted:** 2026-09-17
**Pinned SHA:** `8124162` (main; board HOLDS there · read.against `1b7cd96` PRESENT, 2 behind · 31 MATCH · 5 ABSENT-CONFIRMED · 7 UNCHECKED)
**Branch:** `claude/vigilant-newton-ko9pcr`
**Phase:** 1 (the board becomes a project board: requests in, work out, every step a receipt)
**Status:** AWAITING Z2 RATIFICATION
**Follows:** `Q-INTENTOS-LAUNCH-01` (ACCEPT 09-14) · `Q-INTENTOS-TEST-01` (ACCEPT 09-16) · `Q-INTENTOS-REFRESH-01` (awaiting; d23–d26) · #377 (the bus, merged 09-17) · #380 (tiers T5–T7, merged 09-17)

---

## §A Position · Destination · Probability

**Position:** Z2 approved, on 2026-09-17, the four-step plan for making the Intent-OS a complete,
expandable project board under three constraints: *open-source, minimise cost, maximise collaboration;
a new user enters with a clean board that grows with their work, grounded in our research and ground
truths; our board is the beta run.* Steps 1–3 are on `main`:

| step | what is on `main` | receipt |
|---|---|---|
| 1 · the bus | `tools/decision_relay.py` v0.4.0 `/task`: a signed request lands as a `REQ-` record in `z1-inbox`, hashed, indexed, rendered, on a `req/` branch with a PR labelled `agent-request`; any worker takes it by filling `## Fulfilment` in its own PR; nothing is signed, nothing asked of Z2 | relay self-test PASS on both index formats; harness `t2-relay-roundtrip` |
| 2 · seeing it | `tools/intent_os_requests_v1_0.py` (HAIOS-TOOL-167) + dashboard § 5: stage from the Fulfilment fields alone (`requested → taken → pr → merged`), hashes and header↔block recomputed; *Fetch live from main* re-hashes each record in the browser | reader self-test PASS (16 checks); JS parser ≡ Python on 10 fixtures |
| 3 · measuring the rest | harness v1.1: T5 one row per manifest `smoke_test` claim (tree-guarded), T6 the ACAT API boots, T7 a key-gated live call | 177 rows · 140 PASS · 18 FAIL · 19 SKIP |

The bus carries **zero requests** so far. Step 3 measured two things the plan did not predict:
`tools-manifest.yaml`'s `smoke_test: true` is a text match, not a runnable flag (141 claimed · 106
pass · 17 fail · 18 no flag), and one passing smoke test wrote three files at the repository root.
Both are filed in the 09-17 handoff as IC-candidates. And twice this session a squash-merge left the
board's `read.against` pointing at a commit outside `main`'s history, which the re-seal tool refuses
by design and a session had to move by hand.

**Destination:** the four policy choices below, each stated in resource terms, so the bus can carry its
first real requests — starting with our own (the beta run) — and so the two measurements become rules
rather than findings that recur.

**Probability:** **0.60** that a request lands on the bus and is taken by a worker that is not the
session that filed it within the next five Z1 sessions (C25). **0.80** that, with d29 accepted, the
manifest's `smoke_test: true` count falls to at most 110 on the first rescan (C27).

---

## What Z2 is asked to decide

Costs are named in the ratified units of `RESOURCE_UNITS.yaml` (`RAT-min`, `Z1-ktok`, `Z3-hr`, `CI-min`,
`OP-hr`, `RUN-day`). No option carries a date. Nothing below is chosen by Z1; the readings are what each
option consumes and yields.

| id | question | Z1 reading (no preference encoded) |
|---|---|---|
| **d27** | **Model endpoint policy** for the relay's `/assist` and for workers that take requests: **none** (no model in the loop; workers are Claude Code sessions and people, the relay only records), **local** (an open-weight model behind the relay on the operator's machine — `ANTHROPIC_API_KEY` unset, an OpenAI-compatible local endpoint named by one relay variable), or **hosted** (a provider key on the relay host; T7 measures it)? | *none* costs nothing new and keeps every reading human-authored; *local* costs `OP-hr` to stand up and electricity, no per-call money, and keeps the loop open-source — the constraint Z2 named; *hosted* costs money per call (`RUN-day` pressure) and is the only option T7 turns green today. The three are not exclusive over time: the relay can default to *none*, accept *local* when the variable is set, and treat *hosted* as an explicit per-request opt-in (`wants: answer` with a `provider:` field). That layering is Z1's proposal for how to implement whichever Z2 picks; the pick is Z2's. |
| **d28** | **Issue mirror:** mirror every `REQ-` record to one GitHub issue (label `agent-request`, body = the request block, closed when `merged:` is filled), so people who do not read `z1-inbox` see the bus — or keep it git-only (the `req/` PR is the notice)? | Mirroring costs a few API calls per request (`CI-min`-scale, no money) and one more thing to keep in sync (the reader would check issue ↔ record). It maximises collaboration for humans; it changes nothing for agents, which already read the index. Copilot's review of #377 made the same point from the other side: the label is the discovery channel, so a failed label must not be silent (fixed) — an issue is the human-visible form of the same channel. |
| **d29** | **The smoke contract in the manifest:** make `smoke_test: true` mean *runs*, not *mentions* — `.tool-control/scan.py` records `smoke_flag: --smoke-test / --self-test / none` from the source and sets `smoke_test` only when a flag exists; and add one validator rule, *a smoke test leaves the repository as it found it* (the tree guard T5 already enforces at run time). Accept both, one, or neither? | Accepting costs one scan (`CI-min`, seconds) and changes 34 rows of a Z2-ratified manifest, so it is Z2's to accept; the harness's T5 rows are the proof that the field then holds. Rejecting keeps the field honest as "mentions a smoke test" and leaves T5 as the standing measurement. The side-effect rule protects `REGISTERED_MD_DRAFT.md`-class writes (a test producing draft registry text) from ever reaching a branch again; the harness catches them, the rule would stop them at registration. |
| **d30** | **The squash-merge read pointer:** after a squash-merge, `read.against` names a commit outside `main`'s history and the board reads STALE (NOT-IN-HISTORY) although the tree is byte-identical. Let `intent_os_board_reseal` move the pointer **mechanically** when the tree hash at the new HEAD equals the tree hash at the read (a fetch, not a judgement; description says so), or keep it **NEEDS-HUMAN** as now? | Mechanical costs nothing per merge and removes one hand move per squash (twice this session: `1b7cd96`, then the #380 squash, which happened to keep the earlier pointer in history). It is safe exactly when the tree hashes match, which the tool can prove; when they differ, it stays NEEDS-HUMAN. Keeping it human costs `Z1-ktok` per squash and keeps every pointer move a read. Either way, d24 (a job may advance `rev`) governs whether the *job* may do it. |

## Predictions (pre-registered)

Resolution is stated in resource events (sessions, requests, scans, merges), never in calendar time.

| id | text | p | resolves |
|---|---|---|---|
| C25 | a request lands on the bus and is taken by a worker other than the session that filed it, within the next five Z1 sessions that open on `main` | 0.60 | the fifth such session |
| C26 | with d28 accepted, the first three requests each have an issue whose state matches the record's stage at the reader's next run | 0.70 | the third request's first reader run after its issue exists |
| C27 | with d29 accepted, the manifest's `smoke_test: true` count is at most 110 on the first rescan (from 141) | 0.80 | that rescan |
| C28 | with d30 accepted, the next three squash-merges that touch a sealed path leave the board HOLDS without a hand move | 0.75 | the third such merge |

## Falsifier

Bus-level, measured over the **next ten requests** on the bus, whichever policy d27/d28 lands: if at
least half of them are taken by the same session that filed them, or are never taken, the bus is not
a bus — it is a session's private ledger — and `/task` is retired from the relay (the records stay; the
reader keeps reading them). Until ten requests exist the falsifier is VOID and the reader's `--check`
(every record verifies) is the only standing test.

Row-level, d29: if after acceptance a rescan leaves any `smoke_test: true` row whose source carries no
flag, the mechanism did not land and T5 keeps the measurement. Row-level, d30: if the tool ever moves
`read.against` between commits whose tree hashes differ, it is laundering a read — the self-test must
plant that case and prove the refusal before the change is merged.

No date is attached to any of these: a request arrives when someone has one and the resources to send
it; a scan runs when the manifest changes.

## Receipts (operated this session)

```
DRY_RUN=1 python3 tools/decision_relay.py --self-test            → SELF-TEST PASS (both index formats; every refusal; the existing-path race)
python3 tools/intent_os_requests_v1_0.py --self-test             → SELF-TEST PASS (16 checks)
python3 tools/intent_os_requests_v1_0.py --check                 → 0 request(s) · verdict OK
python3 tools/intent_os_test_harness_v1_0.py --self-test         → SELF-TEST PASS (skip kind · needs_env · tree guard · T5 generator)
python3 tools/intent_os_test_harness_v1_0.py --render            → 177 rows · 140 PASS · 18 FAIL · 19 SKIP · T5 90/17/18 in ~13 s
python3 tools/intent_os_board_check_v1_0.py                      → HOLDS · read.against 1b7cd96 PRESENT
headless Chromium: dashboard § 5 parser ≡ Python on 10 fixtures; mocked live fetch; failure path; T5 tile filters 125 rows
```

Attribution: Z1 (Claude) proposes; Z2 (Night) ratifies by hash via `.z1-control/ratify.py`; Z3 lands.
