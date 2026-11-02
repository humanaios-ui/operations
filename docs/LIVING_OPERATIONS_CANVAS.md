# Living Operations Canvas — draft integration

**Status:** Z1 proposal / draft PR; not admitted, ratified, published, or deployed.
**Source:** `system_graph.json` is the only canonical topology input.
**Entry point:** `ui/living-operations-canvas.html`.
**Existing timeline:** `graph_timeline/system_graph_timeline.html` (retained without changes).

## What the canvas does

- Keeps the user-created operations artwork as an **illustrative navigation surface**, with six clickable conceptual hotspots.
- Renders nodes, directional edges, statuses, zones, recorded tests, and implementation references from the committed `system_graph.json`.
- Reads the **public** `main/system_graph.json` endpoint at opening, on manual refresh, and every five minutes while the page is visible. It makes a read-only GET; never POST, PATCH, PUT, or DELETE.
- Embeds a clearly labeled 2026-09-13 v0.2 **offline snapshot**. If GitHub fails, it shows the snapshot or marks the last successful fetch as **stale**, not as fresh data.
- Links to the pre-existing graph timeline for history. Does not replace or regenerate that timeline.
- Displays the graph's own validation result instead of silently treating declared feedback cycles as a clean DAG.

**Status warning:** `OPERATED` and `LAID` are recorded statuses in the source, not independent production health checks. Graph links are declared relationships, not proof a running workflow executed. The artwork may use illustrative labels not present in the canonical graph.

## Local preview

From the repository root:

```sh
python3 -m http.server 8000
# Open http://localhost:8000/ui/living-operations-canvas.html
```

For a self-contained offline preview, the same file may be opened locally; cross-file timeline navigation works when the repository tree is available. Live GitHub fetching requires an allowed connection to `raw.githubusercontent.com`. No tokens are used or stored.

## Verification

```sh
python3 -m unittest tools.tests.test_living_operations_canvas -v
```

Review the rendered page on desktop and mobile. Test initial offline display, successful and failed refresh, status/zone filters, source links, node keyboard selection, art hotspots, and the history link. Browser behavior and any deployment must be verified independently before admission.

## Z2 review / existing controls

This proposal **does not** edit `system_graph.json`, `system_graph_generator.py`, `REGISTERED.md`, `CLAUDE.md`, CODEOWNERS, `.github/workflows/`, the graph timeline, or any ratification artifacts. It adds an **advisory read-only view**, not a new authority path. Merge, publication, hosting, wider connector access, or future write-capable Witness interactions remain subject to existing human/Z2 admission and repository CI gates. Opening a PR or running a test is not a ratification.

**Known source warning:** canonical v0.2 reports `validation_status.valid=false` with a cycle detection error. The separate `Q-SYSTEM-GRAPH-TEMPORAL-01` v0.3 proposal remains pending; this UI neither resolves nor ratifies it.

**Release decision for Z2:** whether to expose this public-source view only within an authenticated operator surface, which host (if any) may serve it, and what independent review and tests are needed. Do not add production telemetry, credentials, or private user data to this version.

## Scope and limits

This view does **not** claim that INTENT-OS, Resource Miner, PR statuses, CI runs, Witness, or recovery outcomes are connected. Those need separately verified adapters, source-linked receipts, access controls, and Z2 authorization. The static image is a guide; a live runtime state is a different instrument.

**Rollback:** remove only the newly added canvas and this integration documentation/test in a separately reviewed PR. The canonical graph and graph timeline remain untouched.
