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
| **d27** | **Model endpoint policy** for the relay's `/assist` and for workers that take requests: **none** (no model in the loop; workers are Claude Code sessions and people, the relay only records), **local** (an open-weight model behind the relay on the operator's machine — `ANTHROPIC_API_KEY` unset, an OpenAI-compatible local endpoint named by one relay variable), or **hosted** (a provider key on the relay host; T7 measures it)? | *none* costs nothing new and keeps every reading human-authored; *local* costs `OP-hr` to stand up and electricity, no per-call money, and keeps the loop open-source — the constraint Z2 named; *hosted* costs money per call (`RUN-day` pressure) and is the only option T7 turns green today. The three are not exclusive over time: the relay can default to *none*, accept *local* when the variable is set, and treat *hosted* as an explicit per-request opt-in. **None of that exists on `main` today** — relay v0.4 hashes only `title · lane · wants · tagline · ask_sha256 · at`, and `/assist` picks Anthropic from `ANTHROPIC_API_KEY` alone with a hard-coded URL. What it would take (relay v0.5, built only after d27 rules): `/task` accepts optional `provider: none \| local \| hosted` and `model:`, both written into the hashed request block (so a worker's choice of model is part of what was asked); `/assist` reads `RELAY_MODEL_ENDPOINT` (an OpenAI-compatible base URL, no key) for *local* and `ANTHROPIC_API_KEY` for *hosted*, refuses `provider: hosted` when no key is present and `provider: local` when no endpoint is set, and records which endpoint answered in the reading it returns; auth stays the relay's HMAC — the endpoint's own credential never enters a request. That layering is Z1's proposal for how to implement whichever Z2 picks; the pick is Z2's. |
| **d28** | **Issue mirror:** mirror every `REQ-` record to one GitHub issue, so people who do not read `z1-inbox` see the bus — or keep it git-only (the `req/` PR is the notice)? The mirror, if chosen: body = the record's `## Ask` text verbatim plus the request block and a link to the record's path (the block alone carries only `ask_sha256`, which shows a hash, not the ask); labels `agent-request` and one stage label `stage:requested \| stage:taken \| stage:pr`, set from the **reader's verified stage**, never from a raw field; the issue is closed only when the reader's stage is `merged`; a record the reader calls `inconsistent` keeps its issue open with label `inconsistent` (a hidden invalid record is worse than a visible one). | Mirroring costs a few API calls per request (`CI-min`-scale, no money) and one more thing to keep in sync (the reader would check issue ↔ record: state and stage label against its own verdict). It maximises collaboration for humans; it changes nothing for agents, which already read the index. Copilot's review of #377 made the same point from the other side: the label is the discovery channel, so a failed label must not be silent (fixed) — an issue is the human-visible form of the same channel. |
| **d29** | **The smoke contract in the manifest:** make `smoke_test: true` mean *carries a flag*, not *mentions* — `.tool-control/scan.py` records `smoke_flag: --smoke-test \| --self-test \| none` from the source and sets `smoke_test` only when a flag exists (141 → 123 rows: the 18 no-flag rows drop; the 17 whose flag exists but fails stay claimed and stay red in T5 — a flag that fails is a bug to fix, not a claim to erase); and add one validator rule, **git-visible tree isolation**: a smoke test modifies no tracked file and creates no untracked, non-ignored file (exactly what T5's tree guard measures — gitignored paths such as `outputs/` are the sanctioned scratch area and are not seen by it; a sandbox that also catches ignored writes is a separate, later proposal). Accept both, one, or neither? | Accepting costs one scan (`CI-min`, seconds) and changes 18 rows of a Z2-ratified manifest, so it is Z2's to accept; the harness's T5 rows are the proof that the field then holds. Rejecting keeps the field honest as "mentions a smoke test" and leaves T5 as the standing measurement. The isolation rule keeps `REGISTERED_MD_DRAFT.md`-class writes (a test producing draft registry text) from ever reaching a branch again; the harness catches them at run time, the rule would name them at registration. |
| **d30** | **The squash-merge read pointer:** after a squash-merge, `read.against` names a commit outside `main`'s history and the board reads STALE (NOT-IN-HISTORY) although the tree is byte-identical. Let `intent_os_board_reseal` move the pointer **mechanically** when the tree hash at the new HEAD equals the tree hash at the read (a fetch, not a judgement; description says so), or keep it **NEEDS-HUMAN** as now? | Mechanical costs nothing per merge and removes one hand move per squash (twice this session: `1b7cd96`, then the #380 squash, which happened to keep the earlier pointer in history). It is safe exactly when the tree hashes match, which the tool can prove; when they differ, it stays NEEDS-HUMAN. Keeping it human costs `Z1-ktok` per squash and keeps every pointer move a read. Either way, d24 (a job may advance `rev`) governs whether the *job* may do it. |

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
