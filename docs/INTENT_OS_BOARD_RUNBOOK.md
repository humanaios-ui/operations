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
| `tools/decision_relay.py` | lands a tapped ruling into its candidate block as a PENDING PR; on hash echo signs it as ratify.py does; signs as the ratifier configured on its own machine (`RELAY_RATIFIER`), never as a request string; `/assist` is Z1 navigator grammar | Z3 (lands) |
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
   candidate block (`z1-inbox/2026-09-14/Q-BOARD-RULING-<nn>.md`, section *Ruling*) on a branch and
   opens a PR marked **PENDING** with the block's sha256.
4. Tap **→ PR** again and paste the hash back. The relay refuses a hash that does not match the
   landed block. On a match it signs the candidate exactly as `.z1-control/ratify.py` does
   (`sha256(candidate | by=Night | at=<date> | decision=ACCEPT)`), appends the signature to
   `z1-inbox/<date>/Z2_RULINGS_<date>.md`, marks the candidate `ratified` in
   `z1-inbox/INDEX.yaml`, regenerates `Z1_INBOX_INDEX.md`, comments `RATIFY <id> <hash>` and
   labels the PR `z2-ratified`. Every check the z2 gate runs is satisfied on the branch, so the
   PR is green or the relay is wrong.
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
  candidate's INDEX.yaml entry (d18; `z2-rulings/` is retired).

## 7. What is ruled, and what is not

Ruled 2026-09-14 (`z1-inbox/2026-09-14/Z2_RULING_INTENTOS_LAUNCH.md`; ACCEPT signed in
`z1-inbox/2026-09-14/Z2_RULINGS_2026-09-14.md`): **d17 local only · d18 z1-inbox + INDEX.yaml ·
d19 freeze path**; the temporary GitHub tokens are revoked (Z2's statement is the receipt).

Not ruled: the fourteen board rulings d2, d3, d5–d16, now each a candidate block
(`z1-inbox/2026-09-14/Q-BOARD-RULING-<nn>.md`) in the same queue as everything else Z2 owes.
