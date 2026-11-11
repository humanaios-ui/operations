# Codebase Atlas — internal visual map (v0.1)

**Status:** Z1 proposal. **Authority:** `NONE`. **Merge / admission effect:** `NONE`.

GitDiagram inspired the goal: turn a repository inventory into a clickable diagram. This implementation is independently written using Python standard library; it does not import or copy GitDiagram source. GitDiagram is MIT-licensed (Ahmed Khaleel). Source: https://github.com/ahmedkhaleel2004/gitdiagram.

## Use it

From a checkout of `humanaios-ui/operations`:

```bash
python3 architecture/codebase_atlas.py --out /tmp/humanaios-atlas
open /tmp/humanaios-atlas/index.html  # macOS; or open the file in a browser
```

Outputs:

- `index.html` — self-contained offline interactive SVG, clickable commit-pinned GitHub links, search, evidence pane, JSON/Mermaid download.
- `atlas.json` — deterministic schema, component assignments and traceable edge observations.
- `atlas.mmd` — GitHub-compatible Mermaid flowchart.
- `atlas.md` — agent-readable map with evidence paths and coverage counts.

The GitHub Actions `codebase-atlas` workflow runs the regression tests and generates the four files as a **short-lived build artifact**, using only `contents: read`. It does not commit generated files or mutate the Coordinator.

## Observation method

The analyzer runs `git ls-files` to inventory tracked paths, groups them by **ordered**, reviewable patterns in `architecture/codebase_atlas.components.json`, and reads only bounded UTF-8 sources (200 kB per file). It records cross-group edges **only** when supported by a Python AST import, a relative Markdown link, or a concrete Python script invocation in a workflow. The proof records include file, target and line number; no edge is guessed by AI.

URL paths are pinned to `git rev-parse HEAD`. When the worktree differs from HEAD, the output says `UNVERIFIED_WORKTREE`; it must not be used as an exact-head receipt. Generated HTML is entirely local and has no CDN or remote code, although clicking a GitHub source link opens GitHub.

**Known limits:** AST imports are not full dynamic call graphs; docs references do not establish runtime behavior; shell calls and JS import graphs are not fully analyzed; unmapped files are counted rather than claimed as covered. Static edges **cannot** prove workflow order, actual execution, SCVC continuity, or authority. The map is an observability aid and cannot grant admission, approval, or merge standing.

## Falsifiers

Tests reject forged path traversal patterns, wrong repositories, untracked paths, unsupported/fictional links, and script calls in comments. They verify parser-backed Python import evidence, exact commit links, repeatable rendering, safe HTML text emission, and truthful dirty-worktree flags. Any extension that introduces a model must preserve source-path validation and treat model output as untrusted.

## Upgrade path

A later milestone may include scope and process selection, JS/TS imports, architecture diff against a second commit, and graph projections from the existing Session/Evidence Graph. Such joins must preserve origin and authority domains, never promote observational connectivity to a governance fact.
