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
and inert on `main`: `board/worker.mjs` serves two pages of `ui/` — the board and the test dashboard — only
after verifying a Cloudflare Access login (the RS256 token Access injects in its request header, checked
against the team's keys, issued for this application, unexpired, not before its `nbf`); with the two Access
variables unset it answers 401 to everything but `/healthz`, so a deploy publishes nothing until Access is in
front of it. Every authenticated answer names the deployed commit (`X-Board-Commit`). `wrangler.jsonc` at the
root is the Workers Builds configuration and `package.json` pins the deploy tool; Cloudflare deploys from this
repository on each push to `main` once Z2 connects the repository in the dashboard. The relay is untouched.
Runbook §5 has the steps and the failure modes.

## Options

- `serve behind login`
- `stay local`
- `later`

## How this gets ruled

One act, and only one: tap the option under Decisions on the board, then **→ PR**. `tools/decision_relay.py`
writes the choice into the *Ruling* section below on a branch and opens a one-file pull request. **Merging
that pull request is the ratification** (Z2, 2026-09-18): `.github/workflows/intent-os-reconcile.yml` then
signs the merged bytes, records the signature in `z1-inbox/<date>/Z2_RULINGS_<date>.md`, marks this candidate
`ratified` in `z1-inbox/INDEX.yaml` and regenerates `Z1_INBOX_INDEX.md` in a reconcile pull request. Without
the relay, the same one-file pull request can be opened by hand (write the option on the `choice:` line,
`status: DECIDED`) — the merge is still the act. `.z1-control/ratify.py --apply` refuses a block of this shape,
so there is no second, unreviewed path to a signature.

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
- [ ] The allow-list is identities (email / GitHub login), one per member — no shared password — and it is
      enforced twice: by the Access policy in front, and by the Worker itself (`ACCESS_ALLOWED_EMAILS`), so a
      policy widened by mistake still gets `403` from the Worker
- [ ] The Access policy is receipted in the tree (`z1-inbox/<date>/ACCESS_POLICY_RECEIPT_<date>.md`, runbook
      §5): application, AUD, rule type, identity count and the hash of the list — so a later widening is
      detectable without publishing addresses
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
  `ui/intent-os-humanaios-v3_3.html` at the commit the answer's own `X-Board-Commit` header names (the Worker
  is stamped with the built commit at deploy time), i.e. the surface serves something other than the
  ratified file. If the header reads `unknown`, the deploy command lost its stamp: that is a failure of (b)
  too, since the served bytes can then not be tied to a commit.
- (c) **authorization, not only authentication:** a request carrying a *valid* Access token for an identity
  that is **not** on the allow-list is answered with the board (`200`) instead of `403`. A valid token proves
  only that the request passed Access for this application; the claim "allow-listed identities only" is the
  Worker's own list. Probes: positive — Z2's listed identity logs in and gets `200`; negative — an identity
  that can log in to the team but is not on `ACCESS_ALLOWED_EMAILS` (a second address Z2 controls, admitted
  by the Access policy for the test only) gets `403` from the Worker. If no such second identity is
  available, the deployment-level result for (c) is recorded as **NO_GATE — authorization unverified**, not
  as PASS; the code-level check (`node board/worker.test.mjs`: a valid token for an unlisted identity → 403)
  stands on its own but does not substitute.

On any of the three: disconnect the repository from Workers Builds, and this block is withdrawn rather than
carried. `node board/worker.test.mjs` is the check against the code (every refusal path, the allow-list, and
that only the board and the test dashboard are served); the probes above are the check against the
deployment, and the policy receipt (checklist) is what makes a later widening of the Access policy visible.
