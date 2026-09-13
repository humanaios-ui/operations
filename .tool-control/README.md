# Tool Control

Control system for executable tools, built to the same contract as
`.doc-control/` is for documents. One SSOT, a validator that gates merges, and a
rendered index that cannot drift from it.

| piece | role |
|---|---|
| `tools-manifest.yaml` | **SSOT.** Every tool in the repo + every MCP server the agent may call. |
| `TOOLS_MANIFEST.md` | Rendered index. A view — never hand-edit it. |
| `scan.py` | Refreshes the manifest's mechanical fields from the working tree. |
| `validate.py` | The merge gate. Structural rules only. |
| `render.py` | `tools-manifest.yaml` → `TOOLS_MANIFEST.md`. |
| `.github/workflows/tool-manifest.yml` | Runs all three on every PR touching tools. |

## Why this exists

`TOOLS_MANIFEST.md` was written by hand on 2026-07-14 describing 6 tools. By
adoption the repo held **143**. Nothing checked, so nothing caught it. The same
failure had started in doc-control: `CONTROLLED_DOCUMENTS.md` carried the header
"Do not hand-edit — edit the registry" while being maintained entirely by hand,
and had frozen at its seeded 34 entries against a registry of 46.

A registry that nothing verifies degrades into a historical document. So the
load-bearing rule here is **coverage**: every tool file on disk is either
registered or explicitly listed under `excluded:`, and CI blocks otherwise.
Drift becomes a failing check on the PR that causes it instead of a discovery
made months later.

## Two classes of field

**DERIVED** — re-read from the file on every scan. Never hand-edit; `scan.py`
overwrites them.

`version` · `interface` · `lang` · `smoke_test` · `builder_markers` · `session`

`builder_markers` is a **presence heuristic**, not a compliance verdict: it checks
that a file carries the Builder v1.7 header, `TOOL_NAME`, `TOOL_VERSION`, a main
guard and a smoke test, across every registered file including `.js`/`.sh` and
`scripts/`/`bin/`. The authoritative compliance check remains
`tools/builder_compliance_scanner_v1.0.py`, gated by `builder-lint.yml` over its
own (narrower) corpus. The two numbers differ legitimately — 30 of 143 here vs
1 of 112 there — because the corpora differ. Do not treat this field as a second
standard; where they disagree, the scanner wins.

**CURATED** — set by a human, preserved across scans. This is where judgment
lives.

`status` · `owner` · `purpose` · `category` · `zone` · `review_due` · `notes` ·
`approved_by` · `approved_date` · `ratified_by` · `pending_ratification` ·
`supersedes` · `superseded_by`

`category` and `zone` are curated *only when the file declares neither* — a
tool's own `TOOL_CATEGORY` / `TOOL_ZONE` constant always wins, and a mismatch
between the file and the manifest is a merge-blocking error. Fix the file or
rerun the scan; do not "fix" the manifest by hand.

## Status lifecycle

```
draft ──► review ──► approved
  │                     │
  └──► deprecated ──► archived
```

`approved` is the **owner's act** and is never set by a scan. This is the same
no-self-grant rule `document-registry.yaml` states for documents ("approval is
the OWNER's human act, never automated"). `validate.py` enforces that
`approved` carries `approved_by` + `approved_date`.

## Zones

Tools run in Zone 1 (Claude executes) unless ratified otherwise. Per `CLAUDE.md`,
Zone 2/3 authority is granted by Night — a tool cannot vote itself into it. So a
manifest entry with `zone: 2` or `zone: 3` must carry `ratified_by` naming the
Z2 hash or ratification document.

One pre-existing tool (`HAIOS-TOOL-088`, `tools/message_calibration_v1_0.py`)
self-declares `TOOL_ZONE = 2` with no ratification anywhere in the repo. Rather
than silently downgrade a declaration Z1 has no authority to change, or invent a
ratification, it carries `pending_ratification: true`: it stays visible as an
open Z2 item in `TOOLS_MANIFEST.md` and in every CI run, while the gate blocks
any *new* unratified Zone 2/3 claim. `pending_ratification` can never carry a
tool to `approved`.

## MCP servers

An MCP server is a tool with a network boundary, so the servers in `.mcp.json`
are registered here too, under `HAIOS-MCP-<nnn>`. Their `scope` and
`data_classification` are entirely curated — the config file says nothing about
what a server may touch — and both must be set to something real before a server
can reach `approved`. A server present in `.mcp.json` but absent from the
manifest is a merge-blocking error.

## Common tasks

```bash
# Register a newly added tool (and refresh mechanical fields)
python3 .tool-control/scan.py

# Re-render the index after editing curated fields
python3 .tool-control/render.py

# Run the gate exactly as CI does
python3 .tool-control/validate.py

# Preview the next phase: advisory findings become blocking
python3 .tool-control/validate.py --strict

# Self-tests (no repo writes)
python3 .tool-control/scan.py --smoke-test
python3 .tool-control/validate.py --smoke-test
python3 .tool-control/render.py --smoke-test
```

Adding a tool: write it to the Builder v1.7 standard (`TOOLS_TEMPLATE.md`), run
`scan.py`, then fill in its curated fields — at minimum `owner`, `purpose` and a
real `category`. Run `render.py` and commit the manifest, the index and the tool
together.

## Scope

Scanned: `tools/`, `scripts/`, `bin/` — `.py`, `.js`, `.sh`, and extensionless
executables.

Not scanned, deliberately:

- `tools/skills/` — skills, governed by `SKILL_REGISTRY.md`.
- `tools/tests/` — tests, not tools.
- `__pycache__/`, `node_modules/`, `.git/`.

To drop a file from control without deleting it, add it to `excluded:` in the
manifest with a reason — the same escape hatch `document-registry.yaml` uses.

## Phasing

Adopted errors-only, matching how `document-control.yml` was introduced. These
are **warnings** today and become blocking under `--strict` once the backlog is
worked down:

| finding | count at adoption |
|---|---|
| category `unclassified` | 93 of 143 |
| missing Builder v1.7 markers | 30 of 143 |
| non-draft tool without owner / purpose | — |
| `review_due` in the past | — |

The gate blocks structural violations from day one; it does not demand the
existing corpus be clean before it can protect against getting worse.
