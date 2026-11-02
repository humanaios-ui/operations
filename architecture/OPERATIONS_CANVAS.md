# Operations Canvas

**Status:** Z1 proposal, draft. **Authority:** `NONE`. **Ratified:** no. Z2 review pending.

A read-only picture of this repository. It has two parts:

1. **Code graph.** Components and evidenced links from the codebase atlas (`architecture/codebase_atlas.py`).
2. **Repo map.** The ecosystem by status, from `ZONE_REGISTRY.md` and `PLANNED_REPOS.md`.

## Build

```bash
python3 architecture/operations_canvas.py --out /tmp/operations-canvas
# or reuse an atlas you already built:
python3 architecture/operations_canvas.py --out /tmp/operations-canvas --atlas /tmp/atlas/atlas.json
```

Outputs:

- `index.html`: self-contained page. No external scripts. Data is embedded as JSON.
- `canvas.json`: the same data, with `authority_effect: "NONE"` and `ratified: false`.

## Provenance

- An atlas this run generates can be verified. It is verified only when the worktree is clean and the snapshot is `HEAD_WORKTREE`.
- An atlas file passed with `--atlas` is always unverified. Its fields are self-reported.
- The repo map comes from `ZONE_REGISTRY.md` and `PLANNED_REPOS.md`. Their SHA-256 hashes are printed on the page. The atlas provenance does not cover them.

## Living, not committed

The codebase-atlas workflow rebuilds the canvas on push and on pull request. It uploads the result as a short-lived build artifact. Generated files are not committed.

## What it does not do

- It does not change `REGISTERED.md`, `ZONE_REGISTRY.md`, `PLANNED_REPOS.md`, `CODEOWNERS`, or any Z2 gate workflow.
- It does not replace `graph_timeline/system_graph_timeline.html`. That timeline stays as it is.
- It does not ratify, merge, admit, or sign. A rendered page is evidence, not approval.

## Known limits

- Static source links do not prove runtime execution.
- The repo map reports a count check. `ZONE_REGISTRY.md` headers claim a total that can differ from the rows. The page shows the mismatch. It does not hide it.

## Tests

```bash
python3 -m unittest tests.test_operations_canvas -v
```

The tests check the parsers, the authority fields, the count check, and that embedded JSON cannot close its own script tag.
