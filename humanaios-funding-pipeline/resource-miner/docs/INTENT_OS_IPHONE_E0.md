# INTENT-OS iPhone E0 — mobile interface, private boundary, Desk import
Parent: #1084. Source baseline: operations main `52aa7c0ed70f6e24ec050d0d56788a791e5f78f7`.

**Review state:** Z1 candidate only. **Authority:** NONE. No live mobile release, no completed device installation, no private remote access, no automatic merge, and no approved Project Desk writes.

## First slice: phone interface
- Existing `/intent-os`, `/on-track`, and local-only `/my-opportunities` pages get iPhone viewport safe-area support, >=44px primary controls and bottom touch navigation.
- Public pages show **Private locked** rather than a link that bypasses security.
- `/app.webmanifest` is public app **identity only**. It has no service worker and no offline-private cache. The manifest is included in the container image.
- Safari Home Screen installation must be tested on an approved HTTPS origin; CSS responsiveness alone is not a verified iPhone usability result.

## Second slice: phone access — a mandatory HOLD
Existing `Handler._local_opportunities_allowed()` remains unchanged. Private routes require: server bound to loopback, loopback peer, permitted Host and permitted Origin. **Public container or a LAN phone does not pass.** Dedicated regression tests cover these negatives.

Before mobile private data can be enabled, choose and independently review an identity provider + server-side session design. Required controls:
1. A private HTTPS staging origin; authentication performed **server side**, with a user-bound identity and least privilege. Do not treat a phone's IP or Home Screen status as identity.
2. Session cookie: `Secure`, `HttpOnly`, `SameSite=Lax` or `Strict`; explicit expiry and logout. Authenticated mutation endpoints require CSRF protection and checked origins. Require transport security.
3. Authorize every private object and every file read for its actual user. Audit failed and successful access without retaining sensitive payloads.
4. Separate private gateway from the unchanged loopback service, or terminate into a specifically authorized private adapter. **Never** flip the current private route to `0.0.0.0`, disable the loopback check, put an admin token in web JS, add a permissive CORS header, or open an unauthenticated tunnel.
5. Preserve signed source provenance and user vs provider reports. Credential and personal data must not be embedded in a manifest, URL parameters, logs, public fixtures, analytics, or a service worker cache.
6. Perform independent authenticated/unauthenticated tests including cross-user denial, replay, CSRF, duplicate import, revoked session, and lost device scenarios. Deploy only after human authorization.

This branch **does not implement an IdP, mobile session, private gateway, or private sync**. The lock is intentional.

## Third slice: Project Desk source identity (proposal only)
`resource_miner/project_desk_bridge_e0.py::propose_sync(desk, workspace)` accepts only the real existing schema versions:
- `humanaios.workspace_view.v1` (`revision`, `records[].id`, `records[].tasks[].id`)
- `humanaios.project-desk.v1` (`projects[].origin`, `tasks[].source`, `imports[].data`)

Desk source mappings are exact `OPP-.../TASK-...` values and exact `INTENT-OS snapshot · <OPP ID> · revision <n>` origin values. Existing Desk item IDs, statuses, decisions, and evidence remain untouched. Unknown original source IDs become **proposals**, never accepted records. Source-reported `DONE` results in a `TODO` task *proposal*, with `source_reported_state: DONE` preserved for review. Duplicate identifiers, stale imports, and same-revision forks fail closed. Existing disagreements are reported as conflicts.

`source_sha256` measures JSON input integrity for local comparison; it **does not** authenticate a source.

The bridge does not handle persistence, credential access, remote transfer, project benefit claims, financial reconciliation, or bidirectional sync. The next gate is human approval of one source-pinned round trip before adding an explicit write adapter.

### Verification commands
From `humanaios-funding-pipeline/resource-miner`:

```sh
python3 -m unittest tests.test_project_desk_bridge_e0 tests.test_phone_private_boundary_e0 -v
python3 -m unittest discover -s tests -p 'test_*.py'
```

### Human device acceptance
1. Visit authorized HTTPS pilot in Safari, use Add to Home Screen, reopen, rotate and zoom.
2. Search for a real goal; review source status, links, and stale/closed feedback. Never call an unverified source a grant or vacancy.
3. Check On-Track labels, scrolling, touch target size, focus and assistive navigation.
4. Confirm `Private locked` on remotely reachable pages; direct `/my-opportunities` and its APIs must deny access.
5. Compare same workspace import twice; preserve source and Desk identities, show any conflict, and create no accepted completion.
6. Measure correct user understanding, task selection, errors, duplicate writes (target 0), and false verified or completed statuses (target 0).

**Admission gate:** exact-head CI + independent reviewer + private-security design review + explicit human signoff. No auto-deploy.
