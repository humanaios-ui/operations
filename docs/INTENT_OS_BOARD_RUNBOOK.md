---
title: Intent-OS board — runbook (open, read, rule, land, re-check)
status: draft
lifecycle: consumed
consumer: tools/intent_os_board_check_v1_0.py   # the checker enforces the seal rule this runbook describes
board: ui/intent-os-humanaios-v3_3.html
relay: tools/decision_relay.py
policy: tools/relay_policy.yml
written: 2026-09-14
authority: Z1 draft; the launch decisions (d17–d19) are in z1-inbox/2026-09-14/Q-INTENTOS-LAUNCH-01.md and are Z2's
---

# Intent-OS board — runbook

The board is one HTML file. It renders a project as pipeline steps, metrics, owner rulings,
deadlines, pre-registered predictions and a table of verified records ("seals"). Its one rule:
**a step turns green when it is verified by a fetch, not when someone says it is done.** This
runbook is how a Z2 session opens it, rules on it, lands a ruling, and re-checks it.

## 1. Files

| file | role | zone |
|---|---|---|
| `ui/intent-os-humanaios-v3_3.html` | the board; the `HUMANAIOS` block inside it is the live dataset | Z2's hand |
| `tools/intent_os_board_check_v1_0.py` | re-hashes every seal against the tree; exit 0 HOLDS, exit 2 STALE | Z1 (execute) |
| `tools/decision_relay.py` | lands a tapped ruling into its candidate block as a one-file pull request marked DECIDED; signs nothing (0.5.0 — the merge is the ratification); the block's `by` is the ratifier configured on its own machine (`RELAY_RATIFIER`), never a request string; `/assist` is Z1 navigator grammar; `/task` is the agent bus | Z3 (lands) |
| `tools/intent_os_reconcile_v1_0.py` | after a decided candidate merges: signs the merged bytes with the merger and the merge date, writes the day's ruling file, the INDEX entry and the rendered index; `--check` exit 1 = something waiting, 2 = refused | Z1 (records a Z2 act) |
| `.github/workflows/intent-os-reconcile.yml` | runs the reconcile tool on every push to `main` that touches `z1-inbox/`, verifies with the z2 gate's own tools, opens one PR `intent-os: reconcile ratifications` | Z1 job |
| `tools/relay_policy.yml` | ngrok traffic policy in front of the relay (basic-auth; OPTIONS exempt) | Z3 |
| `docs/INTENT_OS_GENERAL_USER_SPEC.md` | the general-user variant (lexicon, connectors, data line) — unratified | Z1 draft |
| `z1-inbox/2026-09-14/Q-INTENTOS-LAUNCH-01.md` | the launch candidate block: what Z2 is asked to decide | Z1 → Z2 |

The path `ui/intent-os-humanaios-v3_3.html` is the stable consumer target
(`docs/ACAT_BENCHMARK_MAP_20260908.md` points at it). A re-read changes the data inside the
file, not the filename, unless d19 rules otherwise.

## 2. Open the board (any session)

1. Open the HTML file in a browser (double-click works; no server needed).
2. The board saves checkbox and ruling state to `localStorage` on that device. The note under
   the buttons says which store is in use, or "export before closing" if none is available.
3. **Export board** writes a JSON file with the project data and every tap; **Import board**
   restores it on another device. Nothing else leaves the page.

## 3. Read it honestly (Z1, before citing anything on it)

```
git fetch origin && git rev-parse HEAD
python3 tools/intent_os_board_check_v1_0.py
```

- `verdict: HOLDS` → every seal with a path still matches the tree; the board may be cited.
- `verdict: STALE` → at least one seal is DRIFT / MISSING / NOT-IN-HISTORY. Do not cite the
  board. Do a re-read: refresh the `HUMANAIOS` block (facts, hashes, `read.against`), rerun the
  checker until it HOLDS, and land the change through a PR. The checker never edits the board.
- Rows without a path (ratification slugs, RECEIPT-GAP notes) are listed as UNCHECKED and are
  never counted green.

A re-read is a Z1 act. It touches no governance file, so it needs no Z2 hash — but every number
it writes must come from a command run in that session, and the `read.against` commit must be
the fetched HEAD.

## 4. Rule on something (Z2)

Tap an option under **Decisions**. The tap is saved locally. **A tap is not a ratification;
the hash is.** To make it one:

1. Run the relay on the machine that holds the GitHub token (never in the browser):

   ```
   export RELAY_SECRET=…        # set at intake; the board asks for it once per session
   export RELAY_BASIC_PASS=…    # the ngrok basic-auth password (relay_policy.yml)
   export RELAY_RATIFIER=Night  # who this relay signs as — set here, never taken from the board
   export GITHUB_TOKEN=…        # scoped PAT: repo write on humanaios-ui/operations only
   python3 tools/decision_relay.py 8787
   ngrok http 8787 --traffic-policy-file tools/relay_policy.yml --url <endpoint>
   ```

   `DRY_RUN=1 python3 tools/decision_relay.py --self-test` proves the logic without a token.
2. Put the ngrok URL in the board's project data as `relay.url` (https only) and apply.
3. Tap **→ PR** on the ruling. The board prompts for the relay secret and the basic-auth
   password (kept in memory, never written). The relay writes the choice into the ruling's own
   candidate block (`z1-inbox/2026-09-14/Q-BOARD-RULING-<nn>.md`, section *Ruling*, `status: DECIDED`)
   on a branch `z2/<id>-<date>` and opens a pull request titled
   `Z2 ruling <id>: <question> → <choice> (<Q-id>)`. The PR changes **one file** — the candidate — so
   any number of taps can land and merge in any order. The status line under the ruling reads
   `DECIDED · <choice> · <PR> · hash … · merge the PR to ratify`. A second tap re-sends (the board
   asks first): the branch is refreshed from main and the same section rewritten, so a changed choice
   updates the open PR.
4. **Review the pull request and merge it. The merge is the ratification** (Z2, 2026-09-18,
   `z1-inbox/2026-09-18/Z2_RULING_MERGE_IS_RATIFICATION.md`). The relay signs nothing and the board
   has no second step: whoever merges, and the day they do, are the signature's `by` and `at`.
   `.github/workflows/intent-os-reconcile.yml` then runs on `main`, finds every awaiting candidate whose
   file carries a relay block behind a merged PR, computes `sha256(candidate | by=Night | at=<merge
   date> | decision=ACCEPT)` over the merged bytes (what `.z1-control/ratify.py --verify` recomputes),
   appends it to `z1-inbox/<date>/Z2_RULINGS_<date>.md`, marks the candidate `ratified` in
   `z1-inbox/INDEX.yaml`, regenerates `Z1_INBOX_INDEX.md`, checks the result with the z2 gate's own
   tools and opens one PR **`intent-os: reconcile ratifications`** listing id, question, choice, who
   merged, which PR, and the signature. Merge that too (it is derived files only; nothing in it
   decides). Until it merges the index still says `awaiting_z2` — the ruling is made, not yet recorded.
   *Who may merge:* with one member, Z2 reviews and merges their own PR — that is d7's bypass and the
   ruling section says so (`single-member override`). Once there is a second member, the repository's
   required review makes the approver and the merger two people; the board is then not a ratifier at
   all, only the hand that opens the PR, and a person cannot both rule on the board and merge their own
   ruling. The reconcile job records the approvers it finds either way.
5. **ask Z1** returns navigator grammar only (position · readings · probability · what would
   prove the favoured reading wrong). Imperatives are stripped and logged as DRIFT. It writes
   nothing.

**Ruled (d18, 2026-09-14):** rulings land in `z1-inbox/` + `INDEX.yaml`. `z2-rulings/` was never
used and is retired. Every open board ruling has its own candidate block (`Q-BOARD-RULING-02` …
`Q-BOARD-RULING-16`), so "what does Z2 owe a decision on" has one answer: `Z1_INBOX_INDEX.md`. The same
ruling can also be recorded by hand — write the choice on the block's `choice:` line and run
`python3 .z1-control/ratify.py Q-BOARD-RULING-<nn> --decision ACCEPT --by Night --apply`.

## 4b. Ask an agent for work (the bus — relay v0.4)

A request is not a ruling and not a candidate: it asks Z2 for nothing. `POST /task` on the relay
(signed like every other call) lands it as a **record**:

```
z1-inbox/<day>/REQ-<yyyymmdd>-<nn>.md     the ask, a hashed request block, an empty ## Fulfilment
z1-inbox/INDEX.yaml  records:             one entry, note "OPEN · wants pr|answer|ruling · lane …"
Z1_INBOX_INDEX.md                         regenerated
branch req/<id> → PR "REQ-…: <title>"     merging it records the request; it decides nothing
```

Fields: `title` (one line), `ask`, `wants` (`pr` · `answer` · `ruling`), `lane` (optional), `tagline`
(recorded **as sent and marked unverified** — the HMAC proves the caller knew the secret, not who
they are). Any worker takes a request — a Claude Code session, a local model behind the relay, a
person — by filling `## Fulfilment` (`taken_by`, `pr`, `merged`, `at`) in its own PR and citing the
`REQ-` id in that PR's body. Governance is unchanged: anything the work needs ratified goes through a
candidate block as always. Without the relay, the same record can be written by hand and indexed; the
validator's coverage rule will insist on the index entry.

`DRY_RUN=1 python3 tools/decision_relay.py --input req.json` with `{"path": "/task", "title": …,
"ask": …, "wants": "pr"}` lands one request on a local copy under `relay_out/` for inspection.

**Seeing the bus.** `python3 tools/intent_os_requests_v1_0.py` lists every `REQ-` record with its stage —
`requested` (Fulfilment empty) → `taken` (`taken_by`) → `pr` → `merged` — derived from the Fulfilment
fields alone, never from time; `--check` exits 2 if any record's hash, ask, id or Fulfilment order does
not verify, or the index does not carry it. The test dashboard § 5 shows the same snapshot from the
last harness run, and its **Fetch live from main** button re-reads the records over HTTPS on click and
re-hashes each one in the browser before lighting a row (no network on open; a failed fetch lights nothing).

## 4c. The relay, live (Z2's direction, 2026-09-17: "wire it live to the internet")

The board stays a local file (d17 is untouched); what goes online is its only exit, the relay. It runs
as the service `intent-os-relay` at `https://intent-os-relay-production.up.railway.app` in the existing
Railway project beside the ACAT API, from this repository, with the start command
`python3 tools/decision_relay.py` (it listens on the host's `$PORT`). Nothing in the
tree carries a secret. The service's variables, set at intake in Railway and nowhere else:

| variable | what | who sets it |
|---|---|---|
| `RELAY_SECRET` | the HMAC key; the board asks for it once per session and keeps it in memory | Z1 generated it at intake; read it from the service's variables, never from the tree |
| `RELAY_BASIC_USER` / `RELAY_BASIC_PASS` | the basic-auth gate the ngrok policy used to provide, now inside the relay (every request but the CORS preflight); the board asks for the password once per session | as above |
| `GITHUB_TOKEN` | a fine-grained token scoped to this repository: contents, pull requests and issues read/write — what `/decide`, `/ratify` and `/task` need to land branches, files and PRs | **Z2 only.** Until it is set, `GET /` reports `github_token: false` and every landing answers `ERROR`; signing and the gate still work, so the wiring is testable without it |
| `RELAY_RATIFIER` | the name the relay signs as (`Night`) | set |

The board's project data names the live URL (`relay.url`) and the basic-auth user; both secrets are
typed into the browser prompts and never written to the file. `GET /healthz` is the host's liveness
probe and says nothing but `ok`; `GET /` (behind the gate) reports version, repo, whether the gate and
the token are set. Every POST is still HMAC-signed and replay-checked inside the relay — the gate only
stops an unauthenticated caller from probing. The ngrok path (`tools/relay_policy.yml`) still works
for a relay run on a laptop; set `RELAY_BASIC_PASS` empty there and let ngrok's policy be the gate.

**Reading a refusal.** The relay writes one line per request to the host's log (Railway → the service →
Deploy logs): `<addr> <METHOD> <path> <status> [<reason>]`, never a body or a credential. The two
refusals a board tap can meet look different there and on the board's status line:

| host log line | the board shows | what it means |
|---|---|---|
| `POST /assist 401 basic-auth required` | `REFUSED · basic-auth rejected … password cleared` | the password typed at the prompt is not `RELAY_BASIC_PASS`; the board asks again on the next tap |
| `POST /assist 401 bad signature` | `REFUSED · bad signature … secret cleared` | the secret typed at the prompt is not `RELAY_SECRET`; the board asks again on the next tap |
| `POST /decide 401 stale timestamp` | `REFUSED · stale timestamp` | the machine's clock is more than 300 s from the host's |
| `POST /decide 200` | `DECIDED · <choice> · <PR> · hash … · merge the PR to ratify` | landed; review and merge the PR — the merge is the ratification |
| `POST /ratify 404 unknown path` | `REFUSED · unknown path` | a board older than 2026-09-18 tried the retired hash echo; load the current board from the repository |
| `POST /decide 500 error` | `ERROR · could not create branch z2/… : GITHUB_TOKEN cannot do this … (GitHub POST …/git/refs: HTTP 403 — Resource not accessible by personal access token)` | GitHub refused the relay's write. The token can read but not write: give it **Contents**, **Pull requests** and **Issues** read & write on this repository, and — because the repository is organisation-owned — approve the fine-grained token for the organisation (Settings → Third-party access → Personal access tokens). A 403 without "access token" in GitHub's message may be a ruleset or branch protection blocking the `z2/` or `req/` branch, or a permission the token lacks — the status alone does not say which; read GitHub's message on the board |

| `POST /decide 200` with a **warning** on the board (`DECIDED · … · landed on z2/… but no pull request: …`) | the choice is on the branch (durable) but the pull request could not be opened — GitHub's message follows, usually Pull requests: write missing. Re-send after fixing the token: the branch is reused and a PR opened |
| `POST /decide 500 error` with `z2/… conflicts with main` | a re-sent tap on a branch whose candidate changed on main since the earlier tap (its PR merged and the file was edited after). Close that PR and delete the branch on GitHub, then tap again |
| `POST /decide 500 error` with `could not write … — written before the refusal: nothing; the branch is unchanged` | GitHub refused the first write; nothing landed. `… written before the refusal: <files>; the branch is partially changed` names what did land before a later write was refused — Z2 completes or reverts the branch by hand |

An answer's status always agrees with what is on the branch: refused before the first write means
nothing changed; a warning on DECIDED / OPEN means the write to the branch happened and only the
pull request could not be opened.

**Any number at once; merge in any order.** A tap's branch touches only its candidate file, so the
fourteen that landed in one minute on 2026-09-18 (#391, #393–#405) never conflict with each other. The
files a ratification shares — `z1-inbox/INDEX.yaml`, the day's `Z2_RULINGS_<date>.md`, the rendered
index — are written by the reconcile job on `main`, once, after the merges, and land in one reconcile
PR. The 0.4.x protocol ("echo, merge, then the next echo") is retired with the echo.

**A merged PR is a ruling.** Before 2026-09-18 a PR marked PENDING was not; #391 (d14) and #393 (d2)
were merged so, with `awaiting_z2` still in the index. Under the ruling that retired the echo those
two merges *are* the ratifications of d14 and d2, and the reconcile job records them on its first run
(a `PENDING` block from relay 0.4.x is accepted exactly like a `DECIDED` one). The twelve PRs still open
(#394–#405) carry 0.4.x PENDING blocks too: merging any of them ratifies it.

The first live `/decide` (2026-09-17 22:52:30Z, d6 → `scrape`) was refused at exactly that step — no
`z2/d6-2026-09-17` branch exists on the remote — and relay 0.4.4 swallowed the refusal and reported
`INDEX.yaml not found`. From 0.4.5 the answer carries GitHub's own message and the meaning above.

The reason in the log is a closed set (the relay's own fixed refusals, or the status word); anything
that quotes the request — a tagline, an exception — stays in the board's answer and out of the host's log.

Copy each value from the service's Variables tab (the eye icon, then select-all) rather than the raw
editor: the board trims what it is given, but a value pasted with its quotes or its name is still wrong.
The first live taps (2026-09-17 21:34–21:37Z, three `POST /assist`) were all answered 401 by a relay
whose log did not yet say which; 0.4.3 and the board's re-prompting fix both.

## 5. Publish — ruled **local only** (d17, 2026-09-14)

The board is not published. Z2 opens `ui/intent-os-humanaios-v3_3.html` from the repository;
the relay is its only exit. Nothing is copied under `site/` and the Pages job is not involved.

If a later ruling reverses d17, the mechanics are one copy: `.github/workflows/pages.yml`
deploys `site/**` on push to `main`, and `tools/registry_site_generator_v1_0.py` leaves
subdirectories it does not write alone, so `site/board/index.html` plus a link from
`site/index.html` would ship it. Until then that is a description, not an instruction — the board
lists every open ruling and the history/PII question (d8), and a public copy is a disclosure.

## 6. Re-read cadence

- **Before any session cites the board:** §3.
- **After any merge to `main` that touches a sealed file:** the checker goes STALE by design.
  `.github/workflows/intent-os-refresh.yml` runs on every push to `main` (event-driven; no clock schedule — this
  project is resource-based and a merge is the event that drifts a seal), classifies the drift
  with `tools/intent_os_board_reseal_v1_0.py`, and publishes the receipt and the rendered pages as run
  artifacts. **MECHANICAL** drift (the inbox index, the registry, the ledgers, the rendered indexes —
  files whose bytes change by construction) is re-hashed, with each row's description saying so; the
  job opens a refresh PR once Z2 enables it (d23, `Q-INTENTOS-REFRESH-01`). **NEEDS-HUMAN** drift — a
  tool, a workflow, the graph, a ruling file — is never re-hashed by a job: the session that merged it
  re-reads it (say what the new bytes mean in the seal's description), or the job files a
  `intent-os-stale` issue and the next session does. Either way the same command decides:
  `python3 tools/intent_os_board_reseal_v1_0.py --check` (exit 0 HOLDS · 1 mechanical · 2 human).
- **Every Z2 ruling:** the ruling's `s` line on the board changes from the question to
  `RULED: … · <hash>`; the hash must appear in `z1-inbox/<date>/Z2_RULINGS_<date>.md` and the
  candidate's INDEX.yaml entry (d18; `z2-rulings/` is retired). From 2026-09-18 both are written by
  the reconcile job after the ruling's PR merges; the board is re-read once the reconcile PR is in.

## 7. What is ruled, and what is not

Ruled 2026-09-14 (`z1-inbox/2026-09-14/Z2_RULING_INTENTOS_LAUNCH.md`; ACCEPT signed in
`z1-inbox/2026-09-14/Z2_RULINGS_2026-09-14.md`): **d17 local only · d18 z1-inbox + INDEX.yaml ·
d19 freeze path**; the temporary GitHub tokens are revoked (Z2's statement is the receipt).

Ruled 2026-09-18 by merge (`z1-inbox/2026-09-18/Z2_RULINGS_2026-09-18.md`, written by the reconcile
job in #407): **d2 later · d14 later** — the first two rulings through the relay.

Not ruled: the twelve board rulings d3, d5–d13, d15, d16, each a candidate block
(`z1-inbox/2026-09-14/Q-BOARD-RULING-<nn>.md`) in the same queue as everything else Z2 owes, and each
with a decided pull request open (#394–#405) whose merge is the ruling.
