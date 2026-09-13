# Instructions for GitHub Copilot in this repository

This file is read automatically by Copilot (chat and coding-agent) on every task in
this repo. It does not replace [`CONTRIBUTING.md`](../CONTRIBUTING.md),
[`GOVERNANCE.md`](../GOVERNANCE.md), or [`CLAUDE.md`](../CLAUDE.md) — read those for
the full rules. This is the short list of things that have already gone wrong on
Copilot PRs here, so you don't repeat them.

## What this repo is

`operations` is the canonical operating record for HumanAIOS — findings, governance,
and tools that other humans and agents treat as settled fact. A claim here is
expected to match what actually happened. If you are not sure whether something is
true, say so in the PR rather than asserting it.

## 1. You operate in Zone 1 — everything else stops and asks

Per `GOVERNANCE.md`'s zone system:

- **Zone 1 (you execute):** code, docs, analysis, non-credentialed tool changes.
- **Zone 2 (operator decides):** editing canonical records, registering findings,
  governance changes, anything an issue marks `z2-ratified` or that names Night/the
  Admiral as approver.
- **Zone 3 (operator only):** credentials, deploys, billing, git operations outside
  a normal PR.

If a task assigned to you asks for a Zone 2/3 action, or an issue and a repo file
disagree about what to do, **stop and comment on the issue** instead of resolving
the conflict yourself. Guessing is the failure mode this rule exists to prevent.

You never merge your own PRs. Every PR here requires human review
(`.github/CODEOWNERS` names a reviewer for every path, `*` included) — your job ends
at opening a mergeable, green PR.

## 2. Base branch: `copilot/*` heads target the default branch, never another `copilot/*` branch

A `copilot/*` PR must target `main`. A PR that targets another `copilot/*` branch is
a fix stacked on a fix — this exact pattern produced a five-deep, zero-diff merge
chain (PR #250) that had to be untangled by hand. `copilot-base-guard.yml` will
retarget a misdirected PR to `main` automatically (its explanatory comment is
best-effort and can silently fail to post), but treat retargeting as a safety net
you should never need — open against `main` yourself.

## 3. Any file payload goes on a pushed branch — never in an issue or PR body

An issue may describe *what* to do, but if it hands you file contents to land
verbatim, that content must exist as commits on a real, pushed branch, referenced by
name — not pasted into the issue/PR body as a fenced code block. Issue #197 is the
worked example of why: the payload branch (`session/S-082026-grbs`) was never
pushed, and the pasted file contents were corrupted by markdown rendering by the
time they reached the issue. The PR that tried to execute it stalled and closed as
a blocker. If an issue asks you to land specific file contents but the source branch
doesn't exist or doesn't fetch, say so on the issue and stop — do not reconstruct
the files from the corrupted paste.

## 4. Some files are append-only or byte-frozen — check before you touch them

- **`REGISTERED.md`** is append-only. Never edit or delete an existing entry, only
  add new ones at the section end an issue specifies. Follow the entry schema
  already at the top of the file.
- **Any file an issue marks `[FROZEN]` or gives a SHA256 for** must land byte-exact.
  Hash it after placement (`sha256sum <file>`) and compare; if it doesn't match,
  stop and comment rather than trying to fix it forward.
- **`CONTROLLED_DOCUMENTS.md`** and **`TOOLS_MANIFEST.md`** are pure rendered
  output — never hand-edit either one. `document-registry.yaml` and
  `tools-manifest.yaml` are their sources and are meant to be edited directly
  for the fields that aren't mechanically derived — see §5 and §6.

## 5. Adding or changing a tool in `tools/`, `scripts/`, or `bin/`

The Builder v1.7 marker checklist below is Python-specific, and CI enforces it
(`builder_compliance_scanner_v1.0.py` via `builder-lint.yml`) only for
`tools/**/*.py` — not `scripts/`/`bin/`, and not other languages. Run the
scanner manually for a Python tool outside `tools/`; for another language,
match the same intent (a name, a version, a stated purpose, a smoke test) in
that language's own idiom. `.tool-control/scan.py` registers `.js`, `.sh`, and
extensionless tools too, but only into the manifest — not this checklist.

A new Python tool file needs, at minimum (per `tools/README.md`'s own "Adding a
new tool" section):

- A module docstring containing the literal phrase `Builder v1.7 compliant` and the
  word `HumanAIOS`.
- `TOOL_NAME`, `TOOL_VERSION`, `TOOL_CATEGORY`, `TOOL_SESSION`, and `TOOL_ZONE`
  constants.
- An `if __name__ == "__main__":` guard, with `--help` and `--input` support.
- A smoke test reachable via `--smoke-test` (or a `run_smoke_test()` function).

Verify with `python3 tools/builder_compliance_scanner_v1.0.py --path <your file>`.

Then register the file — a tool on disk that isn't in the manifest fails CI
(`tool-manifest.yml`, check name **"Tool manifest integrity"**):

```bash
python3 .tool-control/scan.py       # refreshes DERIVED fields from the tree, adds new files
# now hand-edit tools-manifest.yaml: fill in owner, purpose, and — only if your
# tool file does NOT already declare TOOL_CATEGORY/TOOL_ZONE — category/zone
python3 .tool-control/render.py     # regenerates TOOLS_MANIFEST.md to match
python3 .tool-control/validate.py   # the merge gate itself, run it yourself first
```

`scan.py` preserves **CURATED** fields (`owner`, `purpose`, `status`, `notes`,
...) unconditionally, but `category`/`zone` are curated *only* when the tool
file declares neither `TOOL_CATEGORY` nor `TOOL_ZONE` — if it declares either,
that constant is treated as DERIVED and overwrites the manifest on every scan,
so declare it in code rather than hand-editing the manifest entry (a mismatch
between the two is a merge-blocking error). What you must never hand-edit is
**`TOOLS_MANIFEST.md`** itself — change `tools-manifest.yaml` and rerun
`render.py` instead.

A tool at `zone: 2` or `3` needs its manifest entry's own `ratified_by` field
naming a Z2 hash or ratification document — `.tool-control/validate.py` blocks
merge on any zone-2/3 entry with no `ratified_by` (one pre-existing legacy
exception aside). Naming the ratification in the issue or PR description is
not enough on its own; it has to land in the manifest. A tool cannot
self-declare its own waiver (see `.tool-control/README.md`).

## 6. Adding or changing a controlled document

Most `.md` files in this repo are free-form. A **controlled** document is one whose
frontmatter declares a `doc_id` (format `HAIOS-<AREA>-<nnn>`) — those must be
registered in `document-registry.yaml` first, or `.doc-control/validate.py` fails
the PR with "orphan doc_id". Unlike the tool manifest, `document-registry.yaml`
has no scan step: it's a curated YAML list you hand-edit directly, adding your
`doc_id` entry with its required fields — `title`, `canonical_repo`,
`canonical_path`, and `status` at minimum (`.doc-control/validate.py` blocks
merge on any missing). After registering, run `python3 .doc-control/render.py`
to regenerate
`CONTROLLED_DOCUMENTS.md` from it — like `TOOLS_MANIFEST.md`, that rendered
index is never hand-edited. If you're not adding a governance/research-of-record
document, you almost certainly don't need frontmatter at all — most tool READMEs,
specs, and this file itself carry none.

## 7. Before you open or update a PR, run what CI runs

CI on this repo is unforgiving of stale generated files; the fastest path to a green
PR is running the same commands locally first:

```bash
python3 tools/repo_health.py --strict                 # repo vitality gate
python3 .doc-control/validate.py                       # document-control gate
python3 .doc-control/render.py --check                 # CONTROLLED_DOCUMENTS.md in sync
python3 .tool-control/scan.py --check                  # manifest matches the tree
python3 .tool-control/validate.py                      # tool-control structural gate
python3 .tool-control/render.py --check                # TOOLS_MANIFEST.md in sync
python3 -m ruff check --select=E9,F63,F7,F82 \
  src/humanaios_operations acat/api/services tools/tests tests
python3 -m mypy src/humanaios_operations --ignore-missing-imports
```

Then run the blocking pytest suite exactly as `quality-baseline.yml`'s "Pytest
baseline suites" step defines it — copy that step's file list verbatim rather
than running a bare `pytest -q`: blanket discovery both picks up tests CI
doesn't gate on and can pass locally while missing a suite CI does gate on, if
your environment lacks that suite's fixtures.

If a check fails because a generated file (manifest, rendered index) is stale, the
fix is almost always re-running the tool that generates it — see §5/§6 — not
editing the generated file by hand.

## 8. Commit and PR hygiene

- Small, coherent commits; conventional prefixes (`feat:`, `fix:`, `docs:`, `ci:`,
  `chore:`) are welcome.
- Fill in the PR template's Zone checkbox honestly — mislabeling a Zone 2/3 action
  as Zone 1 is itself a finding worth registering.
- If your change fixes or reveals a failure mode, say so in the PR and let a human
  register it in `REGISTERED.md` rather than registering it yourself (§4).
- Don't skip, disable, or narrow a test to make CI pass. If a check is failing for
  a reason your diff didn't cause, say that in the PR instead of routing around it.
