# Ruling request Q-BOARD-PUBLISH-01 — board ruling d31

**Z1 Proposer:** Claude (Z1) — transcribing Z2's direction of 2026-09-18 on the board's surface
**Date Submitted:** 2026-09-18
**Source:** `ui/intent-os-humanaios-v3_3.html` · `rulings[d31]` · filed under Z2 ruling d18: every board ruling lives in the same queue as every other Z2 decision
**Status:** AWAITING Z2 RATIFICATION
**Amends:** d17 (`z1-inbox/2026-09-14/Z2_RULING_INTENTOS_LAUNCH.md`, local only) — a new ruling, not an edit of the signed one

## Question

Board surface — serve the board from a login-gated Cloudflare Worker (Cloudflare Access, allow-listed identities only; no public copy), replacing d17's local-only?

## Context carried on the board

Z2, 2026-09-18: *"I don't want any public, I want to have to login to open the board."* The mechanism is built
and inert on `main`: `board/worker.js` serves two pages of `ui/` — the board and the test dashboard — only after
verifying a Cloudflare Access login (RS256 token from the team's keys, issued for this application, unexpired);
with the two Access variables unset it answers 401 to everything but `/healthz`, so a deploy publishes nothing
until Access is in front of it. `wrangler.jsonc` at the root is the Workers Builds configuration and
`package.json` pins the deploy tool; Cloudflare deploys from this repository on each push to `main` once Z2
connects the repository in the dashboard. The relay is untouched. Runbook §5 has the steps.

## Options

- `serve behind login`
- `stay local`
- `later`

## How this gets ruled

1. **From the board:** tap the option under Decisions, then **→ PR**. `tools/decision_relay.py` writes the
   choice into the *Ruling* section below on a branch and opens a one-file pull request. **Merging that pull
   request is the ratification** (Z2, 2026-09-18): `.github/workflows/intent-os-reconcile.yml` then signs the
   merged bytes, records the signature in `z1-inbox/<date>/Z2_RULINGS_<date>.md`, marks this candidate
   `ratified` in `z1-inbox/INDEX.yaml` and regenerates `Z1_INBOX_INDEX.md` in a reconcile pull request.
2. **By hand:** write the chosen option on the `choice:` line below, then run
   `python3 .z1-control/ratify.py Q-BOARD-PUBLISH-01 --decision ACCEPT --by Night --apply`.

A choice of `later` is a ruling too: it closes this block (its bytes are signed); the question returns only
as a new block. `stay local` leaves d17 in force and the Worker unconnected.

## What `serve behind login` sets in motion (Z1 executes nothing of this; the dashboard steps are Z2's)

1. Workers & Pages → Create → connect `humanaios-ui/operations` (root `/`, no build command, deploy
   `npx wrangler deploy`, production branch `main`). Cloudflare builds and deploys `intent-os-board`.
2. Zero Trust → Access → Applications → Self-hosted → destination: the Worker `intent-os-board` → policy Allow
   emails: Z2's, and later each further member's. Note the application's **AUD** tag and the team domain.
3. Worker → Settings → Variables: `ACCESS_TEAM_DOMAIN=<team>.cloudflareaccess.com`, `ACCESS_AUD=<AUD tag>`.
   From that moment the Worker serves the board to a logged-in identity and 401 to everyone else.
4. Optional: a custom domain (`board.humanaios.ai`) on the Worker, if that zone is on Cloudflare.

## Ruling

choice:
by:
at:
status: OPEN

## Z2 Review Checklist

- [ ] Board surface — serve the board from a login-gated Cloudflare Worker, replacing d17's local-only? — options: serve behind login, stay local, later
- [ ] The allow-list is identities (email / GitHub login), one per member — no shared password
- [ ] The relay's own gate and HMAC stay as they are; the Worker adds a login in front of the page, not a new path into the relay

## Falsifier

Event-based, no clock. The claim is about requests that **reach the Worker**: once Access fronts the hostname,
an unauthenticated request is answered by Cloudflare's login redirect and never reaches the Worker — that is
compliant, not a failure. The block is falsified if either of these is ever observed after a Workers Builds
deploy has **completed** (a build in progress is not measured):

- (a) a request without a valid Access token that reaches the Worker is answered with `200` and the board's
  bytes — any path other than `/healthz`. Probe: an unauthenticated
  `curl -sS -o /dev/null -w '%{http_code}' https://<worker>/intent-os-humanaios-v3_3.html` must print `401`
  (or a `302` to the Access login when Access fronts the name), never `200`.
- (b) an **authenticated** `GET` of `/intent-os-humanaios-v3_3.html` returns bytes whose `sha256` differs from
  `ui/intent-os-humanaios-v3_3.html` at the commit that deploy built (the deploy's commit in the Workers
  Builds log), i.e. the surface serves something other than the ratified file.

On either: disconnect the repository from Workers Builds, and this block is withdrawn rather than carried.
`node board/worker.test.mjs` is the check against the code (every refusal path, and that only the board and the
test dashboard are served); the two probes above are the check against the deployment.
