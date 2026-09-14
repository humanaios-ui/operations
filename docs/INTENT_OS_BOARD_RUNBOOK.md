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
| `tools/decision_relay.py` | lands a tapped ruling as a PENDING PR; ratifies on hash echo; `/assist` is Z1 navigator grammar | Z3 (lands) |
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
   export GITHUB_TOKEN=…        # scoped PAT: repo write on humanaios-ui/operations only
   python3 tools/decision_relay.py 8787
   ngrok http 8787 --traffic-policy-file tools/relay_policy.yml --url <endpoint>
   ```

   `DRY_RUN=1 python3 tools/decision_relay.py --self-test` proves the logic without a token.
2. Put the ngrok URL in the board's project data as `relay.url` (https only) and apply.
3. Tap **→ PR** on the ruling. The board prompts for the relay secret and the basic-auth
   password (kept in memory, never written). The relay lands
   `z2-rulings/<date>/<id>.md` on a branch and opens a PR marked **PENDING** with the block's
   sha256.
4. Tap **→ PR** again and paste the hash back. The relay refuses a hash that does not match the
   landed block; on a match it comments `RATIFY <id> <hash>` and labels the PR `z2-ratified`.
5. **ask Z1** returns navigator grammar only (position · readings · probability · what would
   prove the favoured reading wrong). Imperatives are stripped and logged as DRIFT. It writes
   nothing.

Where the relay lands rulings is d18's question. Today it is `z2-rulings/`, which the z2 gate
(`.github/workflows/z2_ratification_gate.yml`) and `.z1-control/validate.py` do not cover. The
candidate block proposes `z1-inbox/<date>/` + `INDEX.yaml` so the same gate that covers every
other Z2 decision covers these.

## 5. Publish (only after d17)

`.github/workflows/pages.yml` deploys `site/` to GitHub Pages on every push to `main` that
touches `site/**`. `site/` is generated by `tools/registry_site_generator_v1_0.py`, which writes
`index.html`, `assets/`, `findings/` and leaves other subdirectories alone. So publishing is:

```
mkdir -p site/board && cp ui/intent-os-humanaios-v3_3.html site/board/index.html
# link it from site/index.html; open a PR; the Pages job runs on merge
```

Do not do this before d17 rules **pages (public)**: the board lists every open ruling, the
token-exposure note (step 3) and the history/PII question (d8). A public copy is a disclosure.
Whether Pages is enabled on the repository is a settings-page fact that cannot be verified from
the tree; the first deploy run is the receipt.

## 6. Re-read cadence

- **Before any session cites the board:** §3.
- **After any merge to `main` that touches a sealed file:** the checker goes STALE by design.
  Re-read within the session that merged it, or file the drift as a RECEIPT-GAP in the handoff.
- **Every Z2 ruling:** the ruling's `s` line on the board changes from the question to
  `RULED: … · <hash>`; the hash must appear in a file under `z1-inbox/` (or `z2-rulings/` until
  d18 rules).

## 7. What this runbook does not decide

d17 (publish surface), d18 (relay landing path), d19 (path freeze vs. version bump per read),
and every ruling d2–d16 carried on the board. Those are in the candidate block and are Z2's.
