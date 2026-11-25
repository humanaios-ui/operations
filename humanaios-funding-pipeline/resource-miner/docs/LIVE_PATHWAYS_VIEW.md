# Resource Miner pathways — local live observation (v0.1)

**Authority:** NONE. **Execution:** DISABLED. **Eligibility:** NOT_ASSESSED.
**Status:** implementation under review, not a production deployment.

## Open the view

From the Resource Miner checkout:

```sh
python3 app.py --host 127.0.0.1 --port 8766
```

Visit `http://127.0.0.1:8766/pathways`, or follow the link from
`/my-opportunities`.

The route is available **only to a loopback client on a loopback-bound
server**, with same-host and same-origin checks, reusing the existing
`_local_opportunities_allowed()` gate. A public deployment returns 404.

## Actual wiring

- `GET /api/pathways?mode=stored` reads `data/resources.jsonl` when
  present, or else `data/resources.snapshot.jsonl`. It also reads
  `data/mines.seed.json`, `data/needs.seed.json`,
  `data/resource_requirements.seed.json`, and
  `data/resource_state.receipts.jsonl`.
- The page polls **this local file projection every 20 seconds** while
  visible. A poll does **not** run a scan, modify snapshots or contact
  an external provider.
- Clicking **Read public sources now** calls
  `GET /api/pathways?mode=public`, reusing the existing
  `_intent_scan()` public adapters (curated funding catalog and DEV
  Community). External observation may fail; a fallback is disclosed.
  This mode does not read or expose private state receipts.
- The graph renders real counts and candidate-to-need / requirement /
  state-receipt links from the selected observation. It shows up to
  200 deduplicated paths, with a count of unprojected source rows.
  The UI shows 10 at a time, with **Show more**, search and need filter.
- An explicit `mine_id` is required to bind a candidate to a
  configured Mine. A matching name alone never creates that edge.
  Safe source URLs are checked through the existing INTENT-OS
  `_public_https` guard before display.

## Epistemic limits

**OBSERVED:** candidate rows, recorded need/requirement matches, evidence
reference counts, local state receipts, registry entries, observation
timestamps and file-read timestamps.

**SUPPORTED:** graph links that carry explicit identifiers from the
same stored record (including explicit `mine_id`).

**UNVERIFIED:** current provider availability, eligibility, ownership
or resource acquisition, source authenticity, human beneficiary impact,
production deployment, and end-to-end runtime freshness.

A prior receipt with `to_status=ACTIVE` remains merely a dated note.
It must **not** override a later provider closure or an independent
contradiction. This view does not implement the cross-source
currentness reconciliation still under work elsewhere.

A `to_resource_state=ALREADY_ACQUIRED` receipt contributes only to
**recorded acquired · not verified**, never to independently verified
mission outcomes. No independent outcome ledger is connected here.
A dash means **not observed**, not **none exist**.

The backend strips free-form candidate descriptions, raw input,
subject identities and evidence bodies. The projection has no
application, claim, contact, payment, file-write or entitlement
execution methods.

## Manual checks

1. On loopback, `/api/pathways?mode=stored` returns a structured
   projection and the page shows its origin, sampling time and
   last candidate observation (these are different timestamps).
2. Refresh the JSONL source in a test checkout. The screen updates on
   its next local poll without a page reload.
3. Click a candidate. Verify the displayed Mine binding, source,
   linked needs, requirements and state receipts come only from that
   candidate's record.
4. Press **Read public sources now**. The source mode changes to
   `PUBLIC_REFRESH`. Any fallback source warning remains visible.
5. Bind the service to a non-loopback host; both `/pathways` and
   `/api/pathways` must return 404.
6. Verify that old ACTIVE notes cannot be mistaken for independent
   currentness. Check the known disputed job-listing reconciliation
   separately; do not infer the listing reopened.
7. Run `python3 -m unittest discover -s tests -p 'test_pathways_view.py' -v`
   from the Resource Miner directory, then the full repo's required CI.

## Admission

This is a read-only candidate PR. Human Z2 review, exact-head CI
checks, and independently observed runtime behavior remain required
before any merge, admission or deployment.
