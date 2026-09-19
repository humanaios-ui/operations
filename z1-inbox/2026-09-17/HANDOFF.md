# Handoff — 2026-09-17 (Intent-OS refresh: the mechanism for automated updates)

> **Continued through 2026-09-18.** The header below records the 09-17 close (pinned `e2b9a7a`). The same
> session went on: the relay live on Railway, the first rulings through it, Z2's ruling that the merge is
> the ratification (#406), the reconcile job's first run (#407), and the board re-read (#408). The current
> state is the last dated sections and "Next blockers"; `main` is at `a23acb3` or later. A fresh handoff
> file opens at the next session close.

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
- **IC-candidate (a smoke test with side effects), for Z2 to register:** `tools/haios_agent_orchestrator_v1_0_patched.py
  --smoke-test` runs a molt cycle against the current directory and wrote three files at the repository root —
  `MOLT_LOG.json`, `node_store.json`, `REGISTERED_MD_DRAFT.md` (a NODE-CAND row with `ratification_required: false`,
  i.e. draft registry text produced by a test) — on each of T5's three first runs. They were swept into this branch's
  first commit by `git add -A` and removed in the next; the ECC taxonomy bot's changed-file list is what exposed them.
  Mechanism applied in the harness: T5 rows are **tree-guarded** — a smoke test that leaves the repository different
  from how it found it FAILS even with exit 0, and its writes are rolled back (tracked files restored, new files
  removed; pre-existing dirt is not blamed on it). The tool's own fix — write under a temp dir or `outputs/` in smoke
  mode — is its owner's.

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

## Step 4: `Q-INTENTOS-BUS-01` (this branch)

The bus plan's last step is a block, not code: **d27** model endpoint policy (none / local / hosted, in
resource units), **d28** issue mirror, **d29** the smoke contract in the manifest (the two step-3
measurements as one rule: `smoke_test` means *carries a flag*, and a smoke test leaves the git-visible tree as it found it),
**d30** the squash-merge read pointer (mechanical when the tree hashes match, or human as now).
Falsifier over the next ten requests on the bus; predictions C25–C28 in sessions, requests, scans and
merges. The bus carries zero requests at filing; the first should be ours — the beta run.

## The first request on the bus, and the relay online (Z2, in session: "file the first request on the bus and test it then let's wire it live")

`REQ-20260917-01` — *Wire the decision relay live so the board can rule and request from a browser* —
written by the relay's own `/task` in DRY_RUN (no GitHub token here) and landed by this session's PR;
taken by this session (the same one that filed it — the bus block's falsifier counts it); fulfilled by
the PR that adds the relay's own basic-auth gate and `/healthz`, honours `$PORT`, and stands the relay
up as a second Railway service beside the ACAT API (runbook §4c). d17 is untouched: the board stays a
local file; the relay was always the part meant to be online (ngrok before, a host now). Z2 directed
the hosting change in session; no ruling file records it yet — a line for the next block.

**Live:** service `intent-os-relay`, `https://intent-os-relay-production.up.railway.app`, deployed from
this branch at `c617993` (deploy `6a6050f3`, SUCCESS). The host's deploy log carries the relay's start
line (`v0.4.1 · basic-auth on · github token MISSING`) and its answer to the host's `/healthz` probe —
the deployment reaches SUCCESS only when that probe returns 200. **RECEIPT-GAP, stated:** this session's
sandbox egress policy denies `*.up.railway.app` (CONNECT 403), so Z1 did not observe `GET /` behind the
gate or a signed POST *on the live host*; those paths are proven by the local HTTP run of the same
code (healthz 200 · unauthenticated 401 text · bad signature 401 JSON · signed + gated `/task` lands ·
replay 409 · stale epoch 401). The first observation on the live host is Z2's, from a browser: open
the URL, answer the basic-auth prompt, read the status JSON. `GITHUB_TOKEN` is unset on the service
until Z2 sets it; every landing answers ERROR until then.

**RECEIPT-GAP closed (Z2, 2026-09-17T21:20:18Z, from a browser):** `GET /` behind the gate answered
`{"relay": "ok", "version": "0.4.1", "dry": false, "repo": "humanaios-ui/operations", "signs_as": "Night",
"basic_auth": true, "github_token": true, "lands_in": "z1-inbox/ (d18)", "paths": ["/decide", "/ratify",
"/assist", "/task"]}` — pasted by Z2 in session; the host's log carries the matching request line and the
redeploy's start line `github token set` (deploy `2b482ab6`). `GITHUB_TOKEN` was first staged on the
wrong service (`scintillating-playfulness`, unapplied) and then set on `intent-os-relay`. The request that
asked for this (`REQ-20260917-01`) is fulfilled and merged; what remains is the first *signed* tap from
the board, which is Z2's next act.

**First taps (Z2, 2026-09-17, from a `~/Downloads` copy of the board):** the host's proxy log shows
three `OPTIONS /assist 204` + `POST /assist 401` pairs from one Mac browser at 21:34:09Z, 21:35:03Z and
21:37:26Z — the taps reached the relay and were refused; nothing reached `/decide` or `/task`, so no
branch or PR exists from them. The relay's own log (0.4.2) recorded the method and path only, so the
tree cannot say *which* 401 it was: the gate (wrong `RELAY_BASIC_PASS`) or the signature (wrong
`RELAY_SECRET`); both are plausible, and the board made the second one sticky (a refused secret was
re-sent on every tap, never re-asked) and printed `Z1: undefined` for an `ask Z1` refusal. Fixed on
this branch: relay 0.4.3 logs `<status> [<reason>]` and the self-test proves the two 401s read
differently; the board trims both prompted values, clears a refused secret as it already cleared a
refused password, names the Railway variables in its prompts, and shows a refusal as a refusal
(runbook §4c "Reading a refusal"). One more line in the same log: `GET / 401` at 21:38:22Z from a
different address and a Windows browser — the gate held against whoever that was. The falsifier for
`Q-INTENTOS-LAUNCH-01` (one ruling through the relay) is still open; the copy in `~/Downloads` must be
replaced with this file after merge (blocker 3 below) for the fixes to reach the browser.

**First signed exchange on the live relay (Z2, 2026-09-17 22:37Z, board rev 22:01:23Z from main after
#385):** the host's log (relay 0.4.3) reads `POST /assist 401 basic-auth required` at 22:37:07Z — the
password typed at the prompt was wrong and, for the first time, the log says so — then, after the board
cleared it and asked again, `POST /assist 200` at 22:37:16Z, 22:37:22Z, 22:37:26Z and 22:37:28Z: four
signed, gated requests answered. The board fix and the log fix both did what they were shipped to do.
No `/decide` or `/task` was tapped, so nothing landed and C17 is still open. Z2's board export
(`intentos_night_1789684726942.json`, exported 22:38:46Z, kept by Z2, not in the tree) shows 14 choices
selected locally — d2 later · d3 set · d5 rule now · d6 scrape · d7 bypass + IC · d8 accept · d9 later ·
d10 ratify · d11 file as draft · d12 queue · d13 require · d14 later · d15 rule now · d16 archive as
listed — and no relay state: a selected option is not a tap; each becomes a PENDING block only when its
"→ PR" is tapped (`/decide`), and a ruling only when the hash is echoed (`/ratify`). One wording defect
seen on that surface: with no model key on the service, `/assist` answered "relay dry-run", which is
false on a live host; 0.4.4 says "no model key on this relay" and names d27 as the decision that sets one.

**First `/decide` tap (Z2, 2026-09-17 22:52:30Z, d6 → `scrape`):** the host's log reads `OPTIONS /decide 204`
then `POST /decide 500 error`; the board showed `ERROR · z1-inbox/INDEX.yaml not found`. Diagnosis from
the tree and the remote: `git ls-remote` shows no `z2/d6-2026-09-17` (and no `req/`) branch, so
GitHub refused the relay's branch create; the relay read main's ref first (so `GITHUB_TOKEN` is valid
and can read), then swallowed the create refusal in a bare `except: pass` and went on to read the
index on a branch that did not exist. The message Z2 saw was the symptom, not the cause. The cause is
on GitHub's side of the token — most likely the fine-grained token lacks **Contents: write** (and Pull
requests / Issues write), or the organisation has not approved it — and only GitHub's own message can
say which; 0.4.4 threw it away. Relay 0.4.5: `gh()` raises `GitHubError` with GitHub's message, a
branch create is never swallowed (422 "already exists" is the one benign answer), `token_hint()` turns
401/403/404 into what the token needs, and the self-test now drives `/decide`, `/ratify` and `/task`
through a stub of the GitHub API — the path had never been exercised, which is how a silent `pass`
shipped. Nothing landed; C17 is still open. Z2's next tap will show the real reason on the board.

**Z2's red-team audit of 0.4.5 (review on #387, 23:05Z) — HOLD for two P1s, both taken:** (P1) the PR
create in `/decide` and `/task` still swallowed every refusal into an open-PR lookup that could end in
`IndexError`; now `open_pr()` reuses a PR only on GitHub's 422 "already exists" (and refuses, with the
message, when none is open), and since the block or record is on the branch by then the answer is
PENDING / OPEN *with a warning*, not ERROR. (P1) `/ratify` wrote the ruling, INDEX and rendered index
and then could answer 500 if the PR comment or label was refused; now the writes are the ratification
(RATIFIED, with the refusal as a warning), and a write refused mid-way names what was written before it
("the branch is partially changed — Z2 completes or reverts it by hand"). (P2) a contents 404 is now
probed: branch ref, then repository — a missing file, a missing branch and a token that cannot see the
repository answer differently. (P2) the self-test carries a 19-case failure matrix (branch POST ·
contents GET/PUT · PR POST/PATCH · comment POST · label POST × 401/403/404/422): each answer keeps
GitHub's status and message, no fallback exception replaces it, and the status agrees with what was
written. The runbook's 403 wording is non-exclusive, as the audit asked. The board shows a warning
beside PENDING / RATIFIED. The 0.4.5 claim — a GitHub refusal is never swallowed — is now the tested one.

**Second and third `/decide` taps (Z2, 2026-09-17 23:54:52Z ×2):** both `500 error`. Railway had created
a new deployment of the same commit at 23:54:28Z — a variable change, i.e. the token — and kept the old
container serving until the new one passed its probe at 23:55:13Z; the taps at 23:54:52Z ran on the old
container with the old token. Nothing landed.

**The first ruling through the relay (Z2, 2026-09-18 01:01:02Z):** `POST /decide 200`. The relay created
`z2/d14-2026-09-18`, wrote the PENDING block into `z1-inbox/2026-09-14/Q-BOARD-RULING-14.md` (choice
`later`, by Night, at 01:00:56Z, block hash `a04583f5b839958e…`, body hash `4c783772…`) and opened
[#391](https://github.com/humanaios-ui/operations/pull/391), on which every CI check is green — the
relay's landing passes the z2 gate. Z2 reports tapping d6; the request the relay received carried `d14`
(the board sends the id of the row whose button was tapped; d6's candidate on that branch is untouched).
C17 — "one Z2 ruling lands through the relay as a PR (not typed by hand)" — resolves TRUE on this event.
The hash echo at 01:01:32Z answered `200 refused`: a local re-run of the same checks against the branch's
bytes ratifies with the full 64-character hash, so the echoed value did not match — the board's status
line shows the first 16 characters and the prompt asked for the whole hash. The board now completes a
matching prefix of 16+ characters to the full hash (the echo is Z2's act of confirmation; the board
holds the hash). Q-INTENTOS-LAUNCH-01 falsifier (b) — landed *and ratified by hash echo* [corrected 09-18 17:45Z: the signed falsifier asks for a landing only; (b) was met when #391 opened — see blocker 2] — stays open
until the echo lands; d14's choice was `later`, so ratifying it records a deferral, which is a ruling.

**Z2's #388 (KNOWN_RED, ratify partial-write recovery):** taken. `/ratify` now resumes a ratification that
GitHub refused mid-way: a candidate already RATIFIED on the branch with the echoed block hash, the same
body hash and this relay's ratifier, whose INDEX entry is still awaiting_z2, is completed by the identical
echo — signature recomputed over the bytes as they stand with the candidate's own `by`/`at`, the ruling
section appended only if absent, INDEX marked, index rendered; the candidate is not rewritten. A complete
ratification re-echoed is still REFUSED with nothing written, and a candidate RATIFIED by another name is
refused. The falsifier as filed asserted `INDEX` present after the INDEX write was refused; the ruling
file is what is present at that point — the ported case asserts that, intent unchanged. #388's other hunk
(the relay self-test wired into the tool-manifest CI job) is a workflow change, Tier 2 by the classifier,
and stays Z2's to land.

**Thirteen more taps (Z2, 2026-09-18 01:21:49–01:22:31Z):** `POST /decide 200` ×13, about three seconds
apart — d2 later · d3 set · d5 rule now · d6 scrape · d7 bypass + IC · d8 accept · d9 later · d10 ratify ·
d11 file as draft · d12 queue · d13 require · d15 rule now · d16 archive as listed — each landed as a
PENDING block on its own `z2/<id>-2026-09-18` branch with a PR (#393–#405), CI green where finished.
With d14 (#391) every choice in Z2's 22:38Z export is now a PENDING block on the tree. Z2 reports
echoing d14's hash in the same minute; the host log carries no `/ratify` after 01:01:32Z, so that echo
did not leave the browser (d14 is still PENDING on its branch, no ruling file). **Found by simulating
two ratifications from the same base (d14 and d6, DRY):** both add `records: 31` and a records: entry
for `z1-inbox/2026-09-18/Z2_RULINGS_2026-09-18.md` to INDEX.yaml and the same header to that ruling
file — the second PR cannot merge after the first. Relay 0.4.7: `/ratify` merges main into the branch
before it writes (GitHub's merge API; 409 → "the candidate changed on main since the tap; re-send"),
and the runbook states the protocol: echo, merge that PR, then the next echo; an echo made while an
earlier ratified PR is unmerged is repaired by merging it and re-echoing (0.4.6's resume finishes the
ratification on the refreshed branch).

**Second echo on d14 (Z2, 2026-09-18 01:26:37Z):** `POST /ratify 200 refused` — Z2 typed the first eight
characters, because a browser prompt's text cannot be selected or copied, and the live relay (0.4.5)
compares the whole hash. The board now pre-fills the prompt with the hash (OK is the echo), accepts a
typed prefix of 8+ matching characters, and prints the whole hash on the status line as selectable
text. Z2 also asked that every place the board or the relay names a ruling carry a short title, not the
id alone: ruling entries gain `t` ("d14 — LPCS relationship"), prompts, alerts, toasts and status lines
use it, the relay's PR title reads `Z2 ruling d14: <question> → later (Q-BOARD-RULING-14)` and its RATIFY
comment names the question and the choice from the hashed block. The fourteen PRs already open keep
their 0.4.5 titles unless re-sent.

**Two PENDING PRs merged before their echo (Z2, 2026-09-18 01:46:32Z #391 d14, 01:50:42Z #393 d2):**
main now carries both candidates with `status: PENDING` in their Ruling section and `awaiting_z2` in
INDEX.yaml; the validator accepts that (a PENDING block is not a decision); the branches still exist.
A merged PENDING PR is not a ruling, and 0.4.7's `/ratify` would have commented on a closed PR and left
the ratification on the branch with nothing to carry it to main. Relay 0.4.8: after the writes, if
the PENDING PR is no longer open the relay opens a new PR (`Z2 ratification d14: … → later`) carrying
the signature, ruling file, INDEX and rendered index, and answers with it; the board shows it. The
runbook says: echo before merging. The two merged ones are repaired by echoing them now.

**Z2 (2026-09-18, after the two merges): the merge is the ratification.** Z2's finding: the hash echo "puts
too much friction"; the pull request "acts as a governing function"; "our PRs act as the final approval and
the hash is submitted there on the merge"; every PR is reviewed and approved — with one member the author
approves their own as an override, with more than one a board ratification is approved on the PR by another
member, and "humans cannot ratify on board and merge reviewed PRs". Z1 proposed, Z2 approved and folded #406
into it: each ruling PR touches only its candidate file; a job on `main` regenerates the other three after
every merge, the way the refresh workflow regenerates derived files. Recorded as
`z1-inbox/2026-09-18/Z2_RULING_MERGE_IS_RATIFICATION.md` (a record; indexed).

What changed (#406): relay 0.5.0 — `/decide` writes `status: DECIDED`, refreshes a reused branch from main
before it rewrites the section, the PR body says the merge is the ratification; `/ratify`, its resume path,
its refresh-before-write and its new-PR-after-merge are removed with their tests (the failure matrix is 17
rows: branch, refresh, contents, PR, label). New `tools/intent_os_reconcile_v1_0.py`: for every awaiting
candidate whose file carries a relay block, verify the hashes, find the merged PR behind the file's last
commit (`git log -1 -- path` → `GET /repos/{repo}/commits/{sha}/pulls`), map the merger's login to a declared
ratifier (`RECONCILE_RATIFIERS=humanaios-ui=Night`), sign the merged bytes with that name and the merge date,
append to the day's ruling file, mark the index, render — the candidate file untouched, so `ratify.py
--verify` recomputes the same hash. Refusals are named (UNVERIFIED · NO-PR · NOT-RATIFIER) and write
nothing. Its self-test runs `validate.py`, `render.py --check` and `ratify.py --verify` on the reconciled
tree. New `.github/workflows/intent-os-reconcile.yml`: on every push to `main` touching `z1-inbox/`, plan →
apply → the gate's own checks → one PR `intent-os: reconcile ratifications` on `intent-os/reconcile`; it
dispatches the z2 gate on that branch because a push made with `GITHUB_TOKEN` starts no runs of its own.
Run against the real tree from this branch, `--check` already names d2 (#393) and d14 (#391), merged by
`humanaios-ui` → Night on 2026-09-18, single-member override: the job's first run on `main` after #406 merges
writes both signatures — the ratification loop; `Q-INTENTOS-LAUNCH-01` falsifier (b) itself was met when #391 landed at 01:01Z (blocker 2). The twelve
open PRs (#394–#405) carry 0.4.x PENDING blocks and ratify when merged, in any order. The board drops the echo:
`→ PR` (or `→ PR again` after a landing, which asks first), status line `DECIDED · <choice> · <PR> · hash … ·
merge the PR to ratify`. #388 (the ratify-recovery falsifier) is moot: there is no relay-side ratification to
recover.

**Z2 (2026-09-18, evening): "how do we make the board a webpage … I don't want any public, I want to have to
login to open the board."** Built inert and filed as d31 (`z1-inbox/2026-09-18/Q-BOARD-PUBLISH-01.md`; d17 stands
until it rules): `board/worker.mjs`, a Cloudflare Worker that serves two pages of `ui/` — the board and the test
dashboard; not the Z2 reviewer, which reads `../z1-inbox/` at runtime — only behind a verified Cloudflare Access
login (the token from Access's request header, the cookie unread; RS256 against the team's keys; shape, issuer,
audience, expiry, `nbf`, signature) and answers 401 to everything but `/healthz` until
`ACCESS_TEAM_DOMAIN`/`ACCESS_AUD`/`ACCESS_ALLOWED_EMAILS` are set; the Worker enforces the allow-list itself (a
valid login for an unlisted identity is 403 — authorization is the code's, not only the Access policy's); keys
cached in an immutable snapshot with a rate-limited refresh on an unknown kid and a 24 h last-known-good bound;
CSP / nosniff / frame-deny on every answer; `X-Board-Commit` on every authenticated one — 46-check self-test in
`board/worker.test.mjs` (after Copilot's two reviews and Z2's three red-team reviews on #409); `wrangler.jsonc`,
the Workers Builds configuration (assets `./ui`, `run_worker_first`, `keep_vars`); `package.json` + lockfile
pinning wrangler for the build. **Z2's ChatGPT review found a governance bypass** — `ratify.py --apply` still
signed board-ruling blocks by hand after the merge-is-ratification ruling, and d31 documented it: the tool now
refuses any block with a `## Ruling` section and a `choice:` line, d31 / runbook §4 drop the by-hand route,
and `z1-inbox/2026-09-18/IC-CAND-RATIFY-MANUAL-BYPASS.md` (Q-IC-RATIFY-BYPASS-01) is the registry entry the
Tier 2 rule asks for (`.z1-control/ratify.py` is a GATE path, so #409 measures Tier 2). No
secrets in the tree; nothing deploys until Z2 connects the repository in the dashboard; the steps are in runbook
§5. Z2 connected the Cloudflare connector to this session (docs search and account reads); the Cloudflare API
and docs site are denied by the sandbox egress policy, and no credentials are set here, so nothing was deployed
from this session — Workers Builds is the deploy path by design. The account already holds two Workers
(`humanaios`, `haios-personal-ops` — the latter a May 2026 password-cookie ops page reading from KV); neither is
touched.

## Next blockers

1. Z2: d23–d26 + KNOWN_RED (`Q-INTENTOS-REFRESH-01`); d27–d30 (`Q-INTENTOS-BUS-01`); d20–d22 choices (accepted, unrecorded); Ruling 6; d3, d5–d13, d15, d16 (d2 and d14 ruled 09-18 by merge). The two IC-candidates above (manifest `smoke_test`; a smoke test with side effects) to register, and `Q-IC-RATIFY-BYPASS-01` (the by-hand `ratify.py` bypass of merge-is-ratification, found by Z2's red team on #409 — the registry entry the Tier 2 rule asks for, since #409 changes `.z1-control/ratify.py`).
2. `Q-INTENTOS-LAUNCH-01` falsifier (b): **met 2026-09-18 01:00:59Z**, when #391 opened with a `RULING d14` block and a `hash:` line in its body — the condition as signed on 09-14 (`9a2a469b…`): *"no ruling has landed through the relay (no PR whose body carries a RULING block and a hash: line)"*. The "landed *and ratified*" reading this handoff carried from the first echo onward was criterion drift — a signed falsifier does not gain a condition after the fact (CLAUDE.md) — withdrawn on Z2's adversarial review of #408; a correction is appended to `z1-inbox/2026-09-18/Z2_RULING_MERGE_IS_RATIFICATION.md`, whose effect 5 repeated it. **Separately, the ratification loop closed 16:38Z:** #406 merged (d8775a7), the reconcile job's first live run opened #407 with d2 (#393) and d14 (#391) signed by Night over the merged bytes, Z2 approved and merged it (a23acb3); `validate.py`, `ratify.py --verify` and `render.py --check` pass on main; the job's second run found nothing awaiting reconciliation (the Z2 queue itself still holds 38 candidates). Relay 0.5.0 is live on Railway. **`later` semantics (Z2's review, finding 2):** terminal for the Q-ID — the signed block is closed, the row stays on the board marked ruled, and re-opening is a successor Q- block citing the original (runbook §7); nothing returns to the queue on its own, and the board's gauge now says "decisions recorded", not "resolved".
3. Z2: rule d31 on the board (tap → merge); on `serve behind login`, the four dashboard steps in runbook §5 — including the policy receipt after the Access step and the third Worker variable `ACCESS_ALLOWED_EMAILS`, then the three probes (the third, authorization, is NO_GATE until a second identity can be tested).
4. Z2: review and merge the twelve decided PRs #394–#405 (any order); each merge is a ruling; the reconcile job records them. GitHub holds the PR-triggered checks on a job-opened PR until a person clicks "Approve and run" — the job's own dispatch of the z2 gate is already green on the same commit.
5. Local copies: until d25, refresh a `~/Downloads` copy by replacing the file with the repository's after each merge — the filename is frozen (d19), so the browser's saved taps survive and the new `rev` loads on restore.
