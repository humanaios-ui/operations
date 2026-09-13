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
adoption the repo held **136**. Nothing checked, so nothing caught it. The same
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
`scripts/`/`bin/`. On the quality of an individual tool,
`tools/builder_compliance_scanner_v1.0.py` (gated by `builder-lint.yml`) is
authoritative and this field is not — where they disagree about a file, the
scanner wins.

They answer different questions, though, and the difference matters.
`_is_builder_corpus_member` admits a file to the scanner's corpus only if it
**already contains** the string "Builder v1.7 compliant". Its pass rate is
therefore computed over self-declared members: a tool that omits the header
entirely is not counted as failing, it is not counted at all. That is why
99.1% (111/112) coexisted with 24 registered tools carrying no markers. Adding a
header line to five agents moved it to 116/117: both numerator and denominator
rose by five, because those files were admitted to the corpus by opting in and
then passed. The rate barely moved; what changed is that five previously
invisible files became visible at all. This field covers the whole registry
instead, so it is the one that can see an omission. Neither number is wrong;
only one of them can notice a file that never opted in.

**CURATED** — set by a human, preserved across scans. This is where judgment
lives.

`status` · `owner` · `purpose` · `category` · `zone` · `review_due` · `notes` ·
`approved_by` · `approved_date` · `ratified_by` · `pending_ratification` ·
`supersedes` · `superseded_by`

`category` and `zone` are curated *only when the file declares neither* — a
tool's own `TOOL_CATEGORY` / `TOOL_ZONE` constant always wins, and a mismatch
between the file and the manifest is a merge-blocking error. Fix the file or
rerun the scan; do not "fix" the manifest by hand.

## Category vocabulary

A category says what a tool **does to the system**, not what subject it
concerns: "ACAT" is a subject, `audit_tool` is a role. The set is **closed** —
`validate.py` rejects a category outside it, and rejects `unclassified`
outright. Extending it means editing `CATEGORIES` in `scan.py`, which is a
reviewed change to the gate. That is deliberate: before the vocabulary existed
every tool invented its own label and 86 of 136 had none at all.

| category | meaning |
|---|---|
| `analytics_tool` | Statistical or psychometric computation over collected data. |
| `audit_tool` | Audits artifacts or state against rules and reports findings. |
| `calibration_tool` | Pins, resolves or scores predictions against outcomes. |
| `connector_tool` | Talks to an external service (Supabase, Slack, GitHub, LLM APIs). |
| `dependency` | Imported by other tools; not invoked directly. |
| `diagnostic_tool` | Measures and surfaces signals without gating anything. |
| `governance_tool` | Operates the governance machinery: registries, molts, routing. |
| `infrastructure_tool` | Internal plumbing: servers, routers, hooks, ingestion, scaffolding. |
| `monitoring_tool` | Watches a surface over time and raises alerts. |
| `orchestrator_tool` | Runs other tools or agents in sequence. |
| `pipeline_tool` | Multi-stage processing of a corpus or record set. |
| `reporting_tool` | Produces human-facing output: reports, sites, drafts. |
| `research_tool` | A research instrument: adversarial suites, elicitation, experiments. |
| `security_gate_tool` | Blocks an action (push, send, activation) on policy. |
| `template_tool` | A scaffold or template for producing new tools. |
| `validation_tool` | Validates the structure or content of an input; pass/fail. |

Five one-off `TOOL_CATEGORY` constants (`governance`, `discovery`, `dispatch`
×2, `site`, `template`) were normalized in their source files. A sixth label,
`meta_validator_tool`, appears only in the Builder header *prose* of
`tools/builder_compliance_scanner_v1.0.py` — it is a descriptor, not a declared
constant, so there was nothing to normalize and that tool is categorized
`validation_tool`. All six are mapped by `CATEGORY_ALIASES` anyway, so an
un-normalized file lands on a real category instead of failing the gate for a
name nobody chose deliberately.

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
open Z2 item in `TOOLS_MANIFEST.md` and in every CI run.

`pending_ratification` is a **grandfather clause, not a self-service waiver**.
The manifest field alone does nothing: the path must also appear in
`LEGACY_ZONE_EXCEPTIONS` in `validate.py`, which is code covered by CODEOWNERS.
A new Zone 2/3 tool that sets the flag is rejected with "a tool cannot grant
itself the Z2 waiver" — otherwise the exemption would be exactly the self-grant
this gate exists to prevent. And it never carries a tool to `approved`, even on
a grandfathered path.

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

Adding a tool: write it to the Builder v1.7 standard (`TOOLS_TEMPLATE.md`),
declaring a `TOOL_CATEGORY` from the vocabulary below, then run `scan.py`. A
tool with no category is registered as `unclassified`, which **fails the gate** —
that is how the backlog stays at zero. Run `render.py` and commit the manifest, the index and the tool
together.

## Scope

Scanned: `tools/`, `scripts/`, `bin/` — `.py`, `.js`, `.sh`, and extensionless
executables.

Not scanned, deliberately:

- `tools/skills/` — skills, governed by `SKILL_REGISTRY.md`.
- `tools/tests/`, and any `test_*` / `*_test` module — tests, not tools.
- `__init__.py` — package initializers.
- Any directory starting with `_` (e.g. `tools/agents/_shared/`) — private or
  shared helpers, imported rather than run.
- `__pycache__/`, `node_modules/`, `.git/`.

These classes mirror `_skip_reason` in
`tools/builder_compliance_scanner_v1.0.py`, so the repo keeps **one** definition
of "this file is a tool" instead of two that disagree. Archived tools are *not*
skipped — they are real tools that were retired, and stay registered at
`status: archived`.

To drop a file from control without deleting it, add it to `excluded:` in the
manifest with a reason — the same escape hatch `document-registry.yaml` uses.

## Retiring a tool

Deleting a tool does not delete its entry. The next scan keeps the entry,
preserves its `tool_id`, and flags it `missing_from_tree: true`; `validate.py`
then fails until someone either sets `status: archived` or removes the entry
deliberately. Retirement is a decision with an audit trail, not a side effect of
`rm`. (A file that stops being a tool *by rule* — renamed to `test_*.py`, say —
is dropped rather than flagged: it left the registry's scope, it was not
retired.)

## Phasing

Adopted errors-only, matching how `document-control.yml` was introduced, then
tightened as each backlog was cleared. **A finding is promoted to blocking only
once its count reaches zero** — that way the gate ratchets instead of shipping
a rule the corpus already violates.

| finding | at adoption | now | status |
|---|---|---|---|
| category `unclassified` | 86 of 136 | **0** | **blocking** |
| category outside the vocabulary | 6 of 136 | **0** | **blocking** |
| missing Builder v1.7 markers | 24 of 136 | 19 | warning |
| non-draft tool without owner / purpose | — | — | warning |
| `review_due` in the past | — | — | warning |

The gate blocks structural violations from day one; it does not demand the
existing corpus be clean before it can protect against getting worse. But once
a backlog *is* cleared, the corresponding rule is promoted so it cannot refill.
