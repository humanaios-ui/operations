# Site Generation — Operator Runbook

**Tool:** `tools/registry_site_generator_v1_0.py`  
**Version:** 1.0.0  
**Status:** LIVE  
**Builder pattern:** v1.7

-----

## Purpose

Converts `REGISTERED.md` into a browseable static HTML research site.  
Each registry entry (F-class finding, IC-class correction, H-class hypothesis)
gets an individual HTML page.  An index page links to all findings and supports
client-side filtering by class.

This does **not** modify `REGISTERED.md` — the tool is read-only with respect
to the registry (append-only semantics are preserved).

-----

## Running the generator

### Prerequisite

Python 3.9+ and `PyYAML` (already in `requirements.txt`):

```bash
pip install -r requirements.txt
```

### Default run (repo root → site/)

```bash
python tools/registry_site_generator_v1_0.py
```

Outputs:

```
site/
  index.html          # landing / browsing page
  assets/
    style.css         # shared stylesheet
  findings/
    F-18.html
    F-19.html
    ...
    IC-018.html
    ...
    H-TRINITY-001.html
    ...
```

### Smoke test (no file writes)

```bash
python tools/registry_site_generator_v1_0.py --smoke
```

Verifies that the parser finds all three entry classes and at least 20 entries.
Exit 0 on pass, 1 on failure.

### Custom paths

```bash
python tools/registry_site_generator_v1_0.py \
  --registry /path/to/REGISTERED.md \
  --out /path/to/output/site
```

### JSON report

Every run writes a machine-readable report to `reports/registry_site_generator.json`
(override with `--report`).  The report contains `status`, timestamps, and counts.

-----

## Inputs and outputs

| Item | Path | Notes |
|------|------|-------|
| Source registry | `REGISTERED.md` | Append-only; never modified by this tool |
| Generator script | `tools/registry_site_generator_v1_0.py` | Builder v1.7, CLI + optional MCP |
| Site root | `site/` | Committed to the repo; browseable locally as static HTML |
| Index page | `site/index.html` | Links to all findings; client-side class filter |
| Finding pages | `site/findings/<ID>.html` | One per entry; `<ID>` is the entry's `id:` field |
| Stylesheet | `site/assets/style.css` | Dark-theme design; no external runtime deps |
| JSON report | `reports/registry_site_generator.json` | Run metadata; not committed |

-----

## Architecture and parsing

### Entry detection

The generator scans `REGISTERED.md` for level-3 Markdown headings that match the
registry entry pattern:

```
### <ID> — <title>
```

The separator must be an em-dash (`—`) or en-dash (`–`).
Plain hyphens are excluded so that non-entry section headers
(e.g. `### F-number registry quick index`) are never matched.

### YAML front-matter

Each entry is expected to open with a YAML front-matter block:

```
---
id: "F-18"
name: "force-power-behavioral-taxonomy"
status: ACTIVE
class: F
date_registered: "2026-02"
...
---
```

Fields extracted and displayed: `id`, `name`, `class`, `status`,
`date_registered`, `date_origin`, `session_registered`, `substrate`,
`principles_triggered`, `tags`, `superseded_by`.

Entries without YAML blocks (older minimal entries like `H-1`) are still
rendered using the heading ID and title; metadata fields are omitted.

### Body rendering

The body text (after the YAML block) is converted from Markdown to HTML using
a lightweight inline converter that handles the patterns used in `REGISTERED.md`:

- `**bold**`, `*italic*`, `` `code` ``
- `[text](url)` links
- Unordered (`-`) and ordered (`1.`) lists
- Fenced code blocks (` ``` `)
- Horizontal rules (`---`)

No external Markdown library is required.

### Honest-gap entries

F-32 and F-33 are "honest gap" placeholders.  They are included in the output
to preserve numerical completeness of the F-number sequence.  Their status is
shown as `GAP` in the badge.

-----

## Design and styling

The site uses the same dark-theme design palette as the existing HTML files in
the repository (IBM Plex Mono, Fraunces, DM Sans; CSS custom properties for
gold, teal, slate, etc.).  No JavaScript framework or build tool is required —
the only runtime JavaScript is a ~20-line filter snippet on the index page.

Google Fonts are loaded over CDN.  For fully offline use, remove the
`<link rel="stylesheet" href="https://fonts.googleapis.com/...">` tag;
the pages will fall back to Georgia / system-ui / monospace.

-----

## Workflow integration

This tool is intended to run as a Zone 1 operation (no external writes,
no Supabase, no registry modification).  Recommended cadence:

1. After appending new entries to `REGISTERED.md`, run the generator.
2. Commit the updated `site/` directory alongside the registry append.
3. The updated pages are immediately browseable from the GitHub repository
   (open `site/index.html` locally, or link from the README).

The `site/` directory is **committed to the repository** (not a
`.gitignore`d build artifact) so the generated HTML is always available
without a build step.

-----

## Assumptions and limitations

- **Boundary correctness is required:** Generated pages must preserve canonical
  entry boundaries — no cross-entry bleed and no major-section spillover
  (e.g. H/IC/NM/changelog content appearing in the wrong entry page).

- **Entry ID uniqueness:** The generator uses the `id:` YAML field as the HTML
  filename.  If two entries share an `id:` value, the second will overwrite the
  first.  The registry schema requires unique IDs, so this should not occur.

- **Incomplete YAML:** Entries without YAML front-matter still render, but
  metadata fields (dates, substrate, tags) are omitted from the detail page.

- **Markdown fidelity:** The inline converter handles headings (`##`, `###`,
  `####`), blockquotes, lists, links, emphasis, fenced code blocks, and rules.
  More advanced constructs (such as tables or deeply nested lists) are rendered
  in a simplified form.

- **No server required:** The output is pure static HTML.  Open
  `site/index.html` in any browser.  All relative paths (`../assets/style.css`,
  `../index.html`) are constructed assuming the standard `site/findings/` layout.

-----

## Related files

| File | Role |
|------|------|
| `REGISTERED.md` | Source of truth — append-only registry |
| `tools/tool_template.py` | Builder v1.7 reference template |
| `PRINCIPLES_SEED.md` | Principles this tool aligns to (P2, P3, structural traceability) |
| `INTEGRATION_MAP_V1_S-051126-01.md` | Document flow context |
