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

## What Z2 is asked to decide — decomposed (2026-09-19)

**Decomposed into:** `Q-BOARD-RULING-27` · `Q-BOARD-RULING-28` · `Q-BOARD-RULING-29` · `Q-BOARD-RULING-30`

This block no longer carries a decision. The four policy calls it asked on 2026-09-17 — d27 (model endpoint
policy: none / local / hosted), d28 (issue mirror), d29 (the smoke contract in the manifest) and d30 (the
squash-merge read pointer) — each live in their own board-ruling block under `z1-inbox/2026-09-19/`, with the
question, the resource-unit readings (`RESOURCE_UNITS.yaml`: `RAT-min`, `Z1-ktok`, `Z3-hr`, `CI-min`, `OP-hr`,
`RUN-day`) and the implementation layering moved there verbatim, ruled from the board by tap → PR → merge. A
red-team read of #410 (ChatGPT, 2026-09-19) found that keeping the questions here as well left two decision
objects for one call: `.z1-control/ratify.py --apply` on this block would have looked like a ruling on them.

What ratifying **this** block means, and only this: steps 1–3 of the bus plan as built on `main` (#377, #380:
the relay's `/task`, the requests reader, harness tiers T5–T7) are accepted as the bus, and predictions
C25–C28 with the bus-level falsifier below are registered against it. It resolves none of d27–d30; those stay
OPEN until their own ruling PRs merge, whatever this block's status. `tests/test_decision_decomposition.py`
checks that every child named above exists in the index as a board-ruling block and that no `dNN` decision
row remains in this file.

## Predictions (pre-registered)

Resolution is stated in resource events (sessions, requests, scans, merges), never in calendar time.

| id | text | p | resolves |
|---|---|---|---|
| C25 | a request lands on the bus and is taken by a worker other than the session that filed it, within the next five Z1 sessions that open on `main` | 0.60 | the fifth such session |
| C26 | with d28 accepted, the first three requests each have an issue whose (state, stage label) pair matches the reader's verified stage at the reader's next run — open + `stage:*` for requested/taken/pr, closed for merged, open + `inconsistent` otherwise | 0.70 | the third request's first reader run after its issue exists |
| C27 | with d29 accepted, the manifest's `smoke_test: true` count is exactly 123 on the first rescan (141 minus the 18 no-flag rows; the 17 failing flags remain claimed), and T5 still shows those 17 as FAIL | 0.85 | that rescan and the harness run after it |
| C28 | with d30 accepted, the next three squash-merges that touch a sealed path leave the board HOLDS without a hand move | 0.75 | the third such merge |

## Falsifier

Bus-level, measured over the **next ten requests** on the bus, whichever policy d27/d28 lands: if at
least half of them are taken by the same session that filed them, or are never taken, the bus is not
a bus — it is a session's private ledger — and `/task` is retired from the relay (the records stay; the
reader keeps reading them). Until ten requests exist the falsifier is VOID and the reader's `--check`
(every record verifies) is the only standing test.

Row-level, d29, both halves: if after acceptance a rescan leaves any `smoke_test: true` row whose source
carries no flag, the flag half did not land; and if any tool registered or re-registered after
acceptance is then caught by T5's tree guard (a FAIL that names the paths it wrote), the isolation rule
did not stop it at registration — either way T5 keeps the measurement and the rule is reopened.
Row-level, d30: if the tool ever moves
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
python3 tools/intent_os_board_check_v1_0.py                      → HOLDS · read.against 1b7cd96 PRESENT, 2 behind (before this block was indexed)
python3 tools/intent_os_board_reseal_v1_0.py --apply             → MECHANICAL (inbox index + rendered index) · read.against → 8124162, main's HEAD at this read (the #380 squash) · HOLDS
python3 tools/intent_os_board_check_v1_0.py                      → HOLDS · read.against 8124162 PRESENT at HEAD (the state Z2 reads)
headless Chromium: dashboard § 5 parser ≡ Python on 10 fixtures; mocked live fetch; failure path; T5 tile filters 125 rows
```

Attribution: Z1 (Claude) proposes; Z2 (Night) ratifies by hash via `.z1-control/ratify.py`; Z3 lands.
