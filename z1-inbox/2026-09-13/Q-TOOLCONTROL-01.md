# Candidate Block: Q-TOOLCONTROL-01 — Tool Manifest & Document-Control Registry

**Z1 Proposer:** Claude (AI agent)
**Date Submitted:** 2026-09-13
**Pinned SHA:** `b1767c5ceb372e1e2f338d761dd6b1d8df7f3f89`
**Branch:** `claude/tool-manifest-doc-registry-344ako`
**Phase:** 0/1 (control infrastructure)
**Status:** AWAITING Z2 RATIFICATION

---

## §A Position · Destination · Probability

**Position:** `operations` pinned at `b1767c5`. Two control surfaces exist on paper. One
(`document-registry.yaml` + `.doc-control/validate.py` + `document-control.yml`) is real but has
a hole in it. The other (`TOOLS_MANIFEST.md`) is a hand-written snapshot with no mechanism
behind it at all.

**Destination:** give tools the SSOT → validator → renderer → CI shape that doc-control already
proves out, and close the drift holes in doc-control itself, so that both registries fail a PR
when they stop describing reality rather than quietly becoming historical documents.

**Probability:** **80%** that both gates stay green on `main` for 30 days without an exception
being carved for them. Held below 90% because the coverage rule is strict by design: any tool
added without running `scan.py` fails the PR, and that friction is exactly where a new gate
usually gets disabled instead of obeyed.

---

## The finding that motivated the work

`TOOLS_MANIFEST.md` was written 2026-07-14 and describes **6 tools**. The repo contains **136** tools
across `tools/`, `scripts/` and `bin/`. That is a **96% coverage gap**, and it went unnoticed for
two months because nothing compared the document to the disk.

The same failure mode had already started in doc-control, one step less far along:
`CONTROLLED_DOCUMENTS.md` carries the header *"Rendered from `document-registry.yaml` (SSOT).
Do not hand-edit — edit the registry"* — but **no renderer existed**. It was maintained by hand
and had frozen at the 34 documents present at seeding, against a registry that had since grown to
46. The document asserted a mechanism that was not implemented.

Both are the same class: a registry nothing verifies degrades into a claim about the past. The
structural fix is that each index is **generated**, and CI blocks when the generated output and
the committed file disagree.

---

## What was built

### Tool control — new, modelled on `.doc-control/`

| file | role |
|---|---|
| `tools-manifest.yaml` | SSOT. 136 tools + 2 MCP servers. `HAIOS-TOOL-<nnn>` / `HAIOS-MCP-<nnn>`. |
| `.tool-control/scan.py` | Refreshes mechanical fields from the working tree. |
| `.tool-control/validate.py` | The merge gate — 8 structural rules. |
| `.tool-control/render.py` | `tools-manifest.yaml` → `TOOLS_MANIFEST.md`. |
| `.tool-control/README.md` | Lifecycle, field classes, phasing. |
| `.github/workflows/tool-manifest.yml` | Runs all three on every PR touching tools. |

Fields split into **DERIVED** (re-read every scan — version, interface, smoke test, builder
markers) and **CURATED** (preserved across scans — status, owner, purpose, category, zone,
notes). A tool's own `TOOL_CATEGORY`/`TOOL_ZONE` constant always wins over a curated value, and a
mismatch between file and manifest **blocks the merge**. This is what keeps the manifest from
becoming a second, divergent description of the same tools.

`approved` is the owner's act and is never set by a scan — the same no-self-grant rule
`document-registry.yaml` already states for documents.

**The load-bearing rule is coverage** (rule 4): every tool file on disk is registered or
explicitly listed under `excluded:`. This is precisely the rule whose absence produced the 6-of-136
gap.

### Doc control — holes closed

- `.doc-control/render.py` — makes the "do not hand-edit" header true. CI `--check` blocks drift.
- `validate.py` rule 6 — a document canonical to *this* repo must resolve on disk.
- `validate.py` rule 7 — `review_due` must parse; overdue is advisory.
- `validate.py` rule 8 — the registry's own `counts:` block must match reality.

---

## Gates verified to actually fail

A gate that cannot fail is decoration. Each was driven red and restored:

| test | result |
|---|---|
| Unregistered tool dropped into `tools/` | `::error::unregistered tool …`, exit 1 |
| Manifest version edited away from the file's `TOOL_VERSION` | caught by both `validate.py` and `scan.py --check` |
| `TOOLS_MANIFEST.md` hand-edited | `render.py --check` exit 1 |
| `document-registry.yaml` counts falsified (46 → 34) | `::error::counts.documents says 34 but the registry holds 46` |
| `counts:` block deleted outright | `::error::registry is missing a `counts:` mapping` |
| `canonical_path: /etc/passwd` | `::error::must be a relative path inside the repo` |
| `canonical_path` pointing at a directory | `::error::is a directory, not a document` |
| New Zone 2 tool setting `pending_ratification` | `::error::a tool cannot grant itself the Z2 waiver` |
| Registered tool deleted from the tree | entry preserved with its `tool_id`, flagged, and the gate fails until it is retired explicitly |

All four self-tests pass (`scan`, `validate`, `render` in `.tool-control/`, plus `.doc-control/render`).
Both gates are green on the branch head, under PyYAML 6.0.1 and 6.0.3.

---

## Registrable items surfaced (routed, not self-registered)

1. **`TOOLS_MANIFEST.md` described 6 of 136 tools.** A 96% coverage gap in a governance
   artifact, undetected for two months. **IC candidate** — same class as IC-031 (overstatement),
   but on a registry rather than a receipt.

2. **`CONTROLLED_DOCUMENTS.md` asserted a mechanism that did not exist.** Its header instructed
   readers not to hand-edit because it was "rendered from" the registry; no renderer existed and
   it was hand-edited. Frozen at 34 vs an actual 46. **IC candidate.**

3. **Root `CODEOWNERS` doc-control rules have never been in force.** `.github/CODEOWNERS` exists,
   and GitHub honours it over the root file. Every `@humanaios-ui/doc-control` assignment in the
   root `CODEOWNERS` — including `/document-registry.yaml` and `/.doc-control/` — is inert. The
   root file's own comment anticipates unknown *teams* being a no-op but not the file being
   shadowed entirely. `CLAUDE.md` reproduces the root excerpt as the governance CODEOWNERS.
   **IC candidate — the authority map documents an enforcement that is not running.** Mitigated
   here by adding the control-surface rules to `.github/CODEOWNERS` with owners that exist.

4. **`tools/message_calibration_v1_0.py` self-declares `TOOL_ZONE = 2`** (ratify) with no Z2
   ratification anywhere in the repo. Z1 cannot grant Zone 2 and will not silently downgrade the
   declaration, so it is recorded as `pending_ratification: true` — visible in `TOOLS_MANIFEST.md`
   and in every CI run — while the gate blocks any *new* unratified Zone 2/3 claim.
   **Z2 decision needed: ratify, or correct the declaration to Zone 1.**

5. **MCP servers were governed by nothing.** `.mcp.json` declares `supabase` (HTTP, carrying a
   live project ref) and `rentahuman` (stdio). Neither appeared in any registry; neither had a
   recorded scope or data classification. They are now registered as `HAIOS-MCP-001/002` at
   `status: draft`, and the gate refuses to let either reach `approved` while scope or data
   classification is still a placeholder. **F candidate — a network-boundary tool surface outside
   document and tool control.** Scope and classification are Z2/owner calls, not Z1's.

6. **39 of 46 controlled documents are past `review_due`** — 34 due 2026-08-01, 5 due 2026-08-15,
   including 5 at `status: approved`. Previously invisible because nothing read the field. This is
   the **STALE** callout condition in `CLAUDE.md`. Advisory in CI; the reviews are the owner's act.

7. **86 of 136 tools are uncategorized and 24 carry no Builder v1.7 markers.** Advisory at
   adoption, not blocking. See the honest-limitations note below before reading the second number.

---

## §Live result — this candidate was measured by its own mechanism

| Round | Source | Findings | Outcome |
|---|---|---|---|
| r1 → r2 | own CI (the new gate) | 1 | The first thing the tool-manifest gate caught was a defect in the scanner behind it: docstring extraction via `ast.parse` made the manifest depend on the interpreter version (PEP 701 f-strings parse on 3.12+, not 3.11), so CI and a developer machine produced different manifests from one commit. Fixed by extracting textually. |
| r2 → r3 | Copilot | 7 posted + 3 suppressed | All 10 verified correct and fixed. |

**r2 → r3 corrections, two of which contradicted this document's own claims:**

| Finding | Verified reality |
|---|---|
| `pending_ratification` is user-controlled | Any new Zone 2/3 tool could set it and take the warning branch. The README claimed new claims block; the code did not enforce that. **The exemption was itself a self-grant.** Now gated on `LEGACY_ZONE_EXCEPTIONS` in CODEOWNER-protected code. |
| scan drops deleted/renamed entries | A deleted tool silently lost its `tool_id` and audit record, though the README said retirement is an explicit act. Entries are now preserved and flagged, failing the gate until retired deliberately. |
| discovery counts non-tools | `__init__.py`, `test_*` modules and `_shared/` helpers were registered as tools, overstating coverage. Now mirrors `_skip_reason` in `builder_compliance_scanner_v1.0.py`: **143 → 136**. |
| path fields are unvalidated | `canonical_path: /etc/passwd` (and a directory) satisfied both existence gates. Both validators now require a repo-contained regular file. |
| `counts:` check is bypassable | Deleting the block skipped the drift check entirely. The mapping and its three keys are now required. |
| MCP approval lacks attribution | A server could reach `approved` with no `approved_by`/`approved_date`, and with `scope: unscoped` once the "set before approval" suffix was deleted. Both now rejected. |
| workflows omit themselves from path filters | A PR changing only a gate would not run that gate. Both now self-test. |

Two of these — the self-grantable waiver and the silent deletion — were places where
this document asserted a protection the code did not implement. That is the same failure
class the whole change exists to fix, reproduced inside the fix.

---

## Falsifier

**Claim:** generating each index from its registry and gating on coverage prevents the registries
from drifting out of correspondence with the repo.

**FALSE if:**

- A tool can be added to `tools/`, `scripts/` or `bin/` and merged to `main` without appearing in
  `tools-manifest.yaml`, OR
- `TOOLS_MANIFEST.md` or `CONTROLLED_DOCUMENTS.md` can be merged in a state their renderer would
  not reproduce, OR
- A manifest entry can claim a `version` its file does not declare, OR
- A tool can reach `zone: 2` or `zone: 3` in the manifest without a `ratified_by` reference, OR
- An MCP server can reach `status: approved` with a placeholder scope or data classification, OR
- The gates require an exception or `continue-on-error` within 30 days to keep `main` merging.

**Success criterion:** both gates green on `main` for 30 days with no exception carved, and the
`unclassified` count strictly decreasing over that window.

---

## Honest limitations, named

- **`builder_markers` is not a compliance verdict.** It is a presence heuristic (header,
  `TOOL_NAME`, `TOOL_VERSION`, main guard, smoke test). The authoritative check remains
  `tools/builder_compliance_scanner_v1.0.py` via `builder-lint.yml`, which reports **111 of 112
  (99.1%)** over a corpus that excludes tests, archived and private modules and never sees
  `scripts/`, `bin/`, `.js` or `.sh`. My 24-of-136 and its 1-of-112 are **not in
  conflict** — different corpora, different definitions. The field was renamed from `builder_v17`
  specifically so the repo does not end up with two competing numbers both called "Builder v1.7
  compliant". Where they disagree, the scanner is right.
- **The 86 uncategorized tools are a backlog this change surfaces, not one it fixes.** Categories
  are a judgment call; auto-assigning them would have manufactured metadata. They are registered
  honestly as `unclassified` and left as visible work.
- **Every tool entered at `status: draft`.** Nothing was marked approved, reviewed, or owned.
  Assigning owners and approving are the owner's acts, and 136 of them is a real queue.
- **Purposes are inherited, not verified.** 43 came from the `tools/README.md` tables and the rest
  from module docstrings. Neither source was checked against what the code does.
- **Coverage is path-based.** The gate proves every file is registered; it does not prove an entry
  describes its tool correctly. A wrong `purpose` still passes.
- **Sibling-repo documents are unverifiable from here.** Doc-control rule 6 only checks the 18
  documents canonical to `operations`; the other 28 point at repos this checkout cannot see.
- **`tool_id` is bound to path.** A renamed tool gets a new id; the old entry must be retired by
  hand. Deliberate — silently re-pointing an id would break the audit trail — but it is manual work.

---

## Deliverables

| File | Status |
|---|---|
| `tools-manifest.yaml` | new — SSOT, 136 tools + 2 MCP servers |
| `TOOLS_MANIFEST.md` | **replaced** — now generated; the 2026-07-14 SORT-phase narrative is superseded (retained in git history) |
| `.tool-control/{scan,validate,render}.py`, `README.md` | new |
| `.github/workflows/tool-manifest.yml` | new |
| `.doc-control/render.py` | new |
| `.doc-control/validate.py` | rules 6–8 added; `.tool-control/` skipped as control-system internals |
| `.github/workflows/document-control.yml` | renderer self-test + `--check` step added |
| `CONTROLLED_DOCUMENTS.md` | **regenerated** — 34 → 46 documents, now accurate |
| `CODEOWNERS`, `.github/CODEOWNERS` | control-surface ownership; item 3 above mitigated |
| `tools/README.md` | header pointing at the manifest as registry of record |
| `z1-inbox/2026-09-13/Q-TOOLCONTROL-01.md` | this block |

No tool behaviour changed. No document content changed. No status was moved to `approved`.

---

## Z2 Review Checklist

- [ ] Item 3 (root `CODEOWNERS` shadowed by `.github/CODEOWNERS`) is routed with priority — it
      means the doc-control ownership ratified earlier has never actually been enforced, and
      `CLAUDE.md` reproduces the inert excerpt
- [ ] Item 4: `message_calibration_v1_0.py` Zone 2 — ratify with a hash, or direct Z3 to correct
      the declaration to Zone 1
- [ ] Item 5: scope and data classification for `HAIOS-MCP-001` (rentahuman) and `HAIOS-MCP-002`
      (supabase, live project ref) — owner call, blocking their approval
- [ ] Item 6: 39 overdue document reviews — set new `review_due` dates or accept the backlog
- [ ] The coverage rule is accepted as merge-blocking from day one (the 30-day falsifier tests
      exactly whether that friction holds)
- [ ] The `--strict` promotion path is accepted as the mechanism for the 86 uncategorized tools,
      with no date committed yet
- [ ] Replacing the 2026-07-14 `TOOLS_MANIFEST.md` narrative with a generated index is accepted
- [ ] `builder_markers` is accepted as explicitly subordinate to `builder_compliance_scanner_v1.0.py`

---

## Summary

One registry described 6 of 136 tools. The other instructed readers not to hand-edit it while
being hand-edited, and was 12 documents behind. Neither had a mechanism that could notice.

Both now generate from a registry and fail the PR that breaks the correspondence. The gates were
driven red four ways and restored. What the change does **not** do is clean the corpus it exposes:
86 uncategorized tools, 136 unowned entries, 39 overdue reviews and two unscoped MCP servers are
registered honestly and left visible, because categorizing, owning and approving are not Z1's to
do.

**Ratification requested.**
