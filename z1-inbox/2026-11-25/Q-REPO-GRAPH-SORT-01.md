# Q-REPO-GRAPH-SORT-01 — One file-level list of the repository's graphs (5S Sort)

**Z1 Proposer:** Claude (Z1)
**Date Submitted:** 2026-11-25
**Status:** AWAITING Z2 RATIFICATION
**AUTHORITY_EFFECT:** NONE. No graph, tool, gate or workflow is changed. No model, network or external agent is called.
**Filed because:** Night asked on 2026-11-25 for one page listing each repository graph, the question it answers and its owner, with clashes flagged, and then said to file it as a draft PR that replaces the old graph inventory rows.

## What changes

`docs/graph_integration/INVENTORY.md` gains a file-level section, pinned to main `4abc5da3`: 16 graphs on main and 3 off main, one row each with path, git blob, the question it answers, who built it and its size. A short clash list and a "not graphs" note follow. The original design-level table from PR #896 stays below it, unchanged, under "Design surfaces (PR #896)", so no trust-boundary text is lost.

No other file changes except this candidate and the Z1 inbox index.

## What Z2 is asked to decide

Make this section the one place that lists the repository's graphs, keyed by path plus blob. A new graph, or a count or label quoted in a crosswalk, should cite a row here rather than start another list.

## Options

- `accept`
- `edit`
- `reject`
- `later`

## Falsifier

The list fails if any of these is observed at the pinned commit:

1. A file on main that holds a node-and-edge structure (a graph) is missing from the tables, and is not one of the helpers, tests, workflows or schemas named under "Not graphs".
2. A node or edge count in the tables does not match the file it names.
3. A blob in the tables does not match `git rev-parse 4abc5da3:<path>`.

## Open, not decided here

- Whether `PROGRAM_GRAPH_MAPPING.md` and the canonical set in `tools/graph_capture_lint_v1_0.py` should point at this list.
- Whether the stale timeline and the stale counts in `AGENT_GRAPH_COMPARISON.md` and `docs/WORKFLOW_DEPENDENCY_GRAPH.md` are rebuilt or marked superseded.
- Open or merged state of PRs #630 and #1310 was not read; their branch heads were.
