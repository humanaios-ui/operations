# HumanAIOS Operations Observatory — E0 read-only telemetry and kinetics

**State:** Z1 WORKBENCH / DRAFT FOR HUMAN REVIEW. Not admitted, merged, published, hosted or deployed by this change. **Authority effect:** NONE. **Execution:** DISABLED. **Merge authority:** false.

- Human request and session/admission record: [issue #1088](https://github.com/humanaios-ui/operations/issues/1088).
- Existing foundation, untouched except one navigation link: [Living Operations Canvas](../ui/living-operations-canvas.html), [original contract](LIVING_OPERATIONS_CANVAS.md).
- Companion page: [Operations Observatory E0](../ui/operations-observatory-e0.html).
- Pure browser projection/collector: [operations-observatory-e0.js](../ui/operations-observatory-e0.js).
- Canonical topology: [system_graph.json](../system_graph.json), unchanged. Existing [graph timeline](../graph_timeline/system_graph_timeline.html), unchanged.
- Separate **unmerged** draft observability experiments: PR #1040 (structural convergence) and PR #1042 (exact-head review attestations); E0 does not borrow, claim to replace, or join their evidence or authority.

## Purpose

Make three public GitHub repositories understandable from one read-only surface, with source-linked metrics and a clearly proposed human-attention list:

1. \`humanaios-ui/humanaios\` — platform and bridge.
2. \`humanaios-ui/operations\` — governance, INTENT-OS and Resource Miner.
3. \`humanaios-ui/lasting-light-ai\` — research, ACAT, Witness and public website.

This is a **live-on-request GitHub evidence view**, not a promise of continuously streaming telemetry. It makes no assertion of healthy runtime, generated value, AI identity, independently validated research, approved PRs, or real-world recovery benefit.

## Source contract and definitions

The browser reads **only** public GitHub REST issue collections, using unauthenticated GET requests, via these allowlisted URI patterns:

\`https://api.github.com/repos/humanaios-ui/{humanaios|operations|lasting-light-ai}/issues?state=all&sort=updated&direction=desc&per_page=100&page=N\`

GitHub's issue endpoint also returns pull requests. Distinguish PRs by the \`pull_request\` member, but do **not** infer merge status from \`state: closed\`. Every item must contain a canonical GitHub HTML URL for its exact repository, kind and issue number. The UI constructs the known URL rather than trusting unknown targets from response data.

The **28-day** observation interval is \`[fetch_time - 28*24h, fetch_time]\` in UTC milliseconds, calculated at each refresh. Each item is counted **at most once** in the interval according to its latest \`updated_at\`. Not every edit, commit, review, comment or state transition is represented. This is *last-touch distribution*, not event throughput.

- \`PRs last updated\` and \`Issues last updated\`: unique items whose latest update is in the rolling window.
- \`PRs created\` and \`Issues created\`: those touched items whose creation timestamp is also in the interval. This is a subset of updated items, not a separate stream of creation events.
- \`Open PRs/issues in window\`: current \`state: open\` among recently touched items; not a complete pending backlog.
- \`28 buckets\`: 28 rolling 24-hour slices of each item's **last update**, from oldest to newest. Latest observation time falls in the final slice.
- \`Last 7d / prior 7d\`: counts of unique items by last update within two adjacent week slices. These are *not* commit counts, user interactions, or work-completion velocity.
- \`Human Attention\`: open recently touched items, with explicit source-label matches prioritized; all others are clearly candidates. Neither ranking nor any label grants human authority.

### Completeness / source trust

At most **four 100-item pages per repository** are read. Stop at a short last page or when a descending page reaches older-than-cutoff activity. If the cap is reached, timestamps are unsorted, HTTP fails (including API rate limits), JSON is invalid, or records are malformed, display PARTIAL / UNAVAILABLE with an explicit reason; incomplete counts use lower-bound markers. The source itself is public GitHub; data is not independent confirmation of participant identity, runtime state or project outcomes.

A previous fully fetched result may remain visible **in memory** after failed refresh, marked \`STALE_LAST_SUCCESS\`. It is never called live or current. No browser persistence, cookies, credentials, tokens, private Gmail, profile data, write operations or outbound analytic calls.

## Preview — step by step

From a checked-out branch of \`humanaios-ui/operations\`:

\`\`\`sh
python3 -m http.server 8000
\`\`\`

Open \`http://localhost:8000/ui/living-operations-canvas.html\`. Click **Operations Observatory E0**. Alternatively open \`http://localhost:8000/ui/operations-observatory-e0.html\`.

1. Confirm all three allowlisted repository headings appear (not two).
2. Select **Refresh public evidence**. Verify a real GitHub source link in each displayed row.
3. Confirm every source count is labeled COMPLETE WINDOW or PARTIAL / UNAVAILABLE, with as-of/window timestamps.
4. Confirm no numeric total before the API responds; a failure must not generate demo data.
5. Check the 28-bucket chart and 7-day comparison; they describe last updates, not transitions.
6. Click Human Attention items; they must open the exact public GitHub issue/PR. Nothing must auto-submit, auto-approve or enqueue Project Desk work.
7. Disable networking or hit an API rate limit: see stale/error status, never a green health claim.
8. Confirm the original canvas graph/embedded image, filters, source validation warning and timeline still work.

## Offline verification

\`\`\`sh
python3 -m unittest tools.tests.test_living_operations_canvas tools.tests.test_operations_observatory_e0 -v
node --test tools/tests/operations_observatory_e0.test.cjs
node --check ui/operations-observatory-e0.js
\`\`\`

Tests cover exact allowlist, canonical URL, 28-day boundary, duplicate records, issue/PR distinction, closed≠merged, label-based advisory classification, rate-limit failure and page-cap coverage, no write paths, no browser storage, and preservation of the original Living Canvas.

**Evidence not yet established by offline checks:** independent browser acceptance, successful live GitHub readback at a pinned revision, repository-wide CI success, actual human task outcomes and deployed-host security. Request these before approval.

## Admission, limits and rollback

This patch intentionally **does not** change \`system_graph.json\`, graph timeline, auth, Coordinator, Z2 policy, scheduled jobs, PR merge state, CI workflows or deployment. The canonical graph's previously reported cycle-validation error remains visible in the original canvas. An \`OPERATED\` node is a source declaration, not a health check.

**Project Desk and INTENT-OS:** *not connected*. A separate read-only projection proposal, identity/replay check, independent review, and human gate are required before any cross-system integration. Do not portray a proposed attention item as an authorized task.

**CI/review:** Use the existing protected checks at the exact PR head; request independent code and browser review. Keep the PR **draft**, Z1, and human-admission HOLD. Do not auto-merge or deploy.

**Rollback:** remove the companion HTML, JS, tests and this document and undo the single canvas link in a separately reviewed change. No data migration is required.
