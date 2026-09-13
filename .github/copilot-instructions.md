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
- **Zone 2 (operator decides):** document tier changes, public-facing content,
  financial decisions, strategic choices, finding registrations, governance
  amendments — `GOVERNANCE.md`'s own list — plus anything an issue marks
  `z2-ratified` or that names Night/the Admiral as approver.
- **Zone 3 (operator only):** terminal commands, git pushes, revenue collection,
  grant submissions, API key rotation, relationship actions, and deploying to
  production — `GOVERNANCE.md`'s own list. You only ever act through a pull
  request here, so most of this won't come up directly, but don't take a Zone 3
  action (rotating a key, pushing outside review) even if a task asks you to.

If a task assigned to you asks for a Zone 2/3 action, or an issue and a repo file
disagree about what to do, **stop and comment on the issue** instead of resolving
the conflict yourself. Guessing is the failure mode this rule exists to prevent.

§7's validation commands, `sha256sum` in §4, and §5's registration commands
(`scan.py`, `render.py`) are terminal commands too, which can look like a
contradiction of the Zone 3 line above. It isn't, for two separate reasons:
a read-only command that only reports (every validation command, `sha256sum`)
never leaves Zone 1 regardless of what it inspects; and the only *writes*
this involves are `scan.py`/`render.py` regenerating the specific generated
files §5/§6 name (`tools-manifest.yaml`, `TOOLS_MANIFEST.md`,
`CONTROLLED_DOCUMENTS.md`), hand-editing `document-registry.yaml` as its own
curated source exactly as §6 describes (never generated, always hand-edited),
and the file your task actually asked you to create or edit — that's the
ordinary mechanism of writing a PR, which
`GOVERNANCE.md`'s Zone 1 already covers ("file operations, data writes,
code"). This carve-out is narrow: it does not extend to `REGISTERED.md` or
any other file §4/§6 name as Zone 2, and it does not make "editing a tracked
file" a general Zone 1 license. What stays Zone 3 regardless is anything on
the list above — a git push outside review, rotating a key, and so on —
whether or not it happens to run through a terminal.

You never merge your own PRs, and never push directly to `main` or force-push,
delete, or rewrite history on any branch. Every PR here requires human review
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
- **Any file an issue marks `[FROZEN]`** must land byte-exact, no exceptions.
  Hash it after placement (`sha256sum <file>`) and compare; if it doesn't
  match, stop and comment rather than trying to fix it forward.
- **A file an issue gives a SHA256 for, without `[FROZEN]`,** is verified the
  same way — but check the issue for an explicitly authorized edit first
  (issue #197's own manifest table gave `GRBS-REGISTERED.md` a SHA256 with no
  `[FROZEN]` tag, alongside a task explicitly permitting one specific line
  edit to it). Apply only the edit the issue names, then hash-verify the rest
  of the file is otherwise unchanged — don't read a bare SHA256 as license to
  reject every edit an unfrozen file's task explicitly asks for.
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
executable extensionless tools too (a non-executable extensionless file is
skipped), but only into the manifest — not this checklist.

A new Python tool file needs, at minimum: two markers the Builder scanner
itself checks for (below) plus what `tools/README.md`'s own "Adding a new
tool" section separately requires of every tool —

- A module docstring containing the literal phrase `Builder v1.7 compliant` and the
  word `HumanAIOS` (the scanner's own markers, not in `tools/README.md`).
- `TOOL_NAME`, `TOOL_VERSION`, `TOOL_CATEGORY`, `TOOL_SESSION`, and `TOOL_ZONE`
  constants (`tools/README.md`).
- An `if __name__ == "__main__":` guard, with `--help` and `--input` support.
- A `--smoke-test` CLI flag, usually implemented by calling an internal
  `run_smoke_test()`. The flag itself must be present and callable — the
  scanner below only checks for the *text* `smoke.test` or `run_smoke_test`
  somewhere in the file (a regex, not a functional check), so a comment or
  docstring mentioning either string would satisfy the scanner without
  satisfying the actual contract; don't rely on the scanner to catch that gap.

`python3 tools/builder_compliance_scanner_v1.0.py --path <your file>` gates on
six **hard** checks (a failure blocks by default) plus three **soft** ones
(`write_report`, `argparse.ArgumentParser`, `SpecLoadFailed` — reported but
non-blocking unless the scanner is run with `--strict`, which `builder-lint.yml`
does not use). All nine are the same kind of check: a regex over the whole
source text, not a semantic check of real structure. A comment or string
literal containing the marker text (or `if __name__`) would satisfy the
docstring phrase, `TOOL_NAME`/`TOOL_VERSION`, the `HumanAIOS` tag, the
smoke-test check, or the main-guard check without the file actually having a
working guard, docstring, or smoke test — write the real thing; don't rely on
the scanner to catch a file that only mentions it. None of the nine check
`TOOL_CATEGORY`/`TOOL_SESSION`/`TOOL_ZONE` or `--help`/`--input` — a scanner
pass isn't full compliance with `tools/README.md`'s broader contract, so check
those by hand. The manifest gate (below) enforces the resulting `category`/
`zone` *fields in the manifest entry*, not the constants themselves —
`scan.py` falls back to a curated value, then the README catalog, then
`unclassified`/zone 1 if the file declares neither. Declaring the constants is
still the right way to set them (see the note on manifest edits below), but a
tool with no `TOOL_CATEGORY`/`TOOL_ZONE` at all can still pass if its curated
fields are already valid. `TOOL_SESSION` has no such fallback or gate at
all — `tools-manifest.yaml`'s own `REQUIRED` fields don't include it, so a
tool missing it passes every automated gate here while violating the README
contract; hand-check it too.

A **new** tool file under `tools/**/*.py` also needs
`python3 tools/behavioral_compliance_gate_v1_0.py --path <your file>` to pass
(`behavioral-compliance.yml`'s own 100%-required new-file gate) — an
AST-level structural check, separate from and in addition to the
marker-presence scanner above. That 100% requirement applies only to files
your PR *adds*; a *modified* existing tool isn't individually gated, only
counted into the whole `tools/` corpus's ≥70% pass-rate floor
(`builder-lint.yml`'s equivalent new-file gate, by contrast, covers added
*and* modified files — the two workflows don't scope identically). Run the
gate on a modified file anyway; a corpus-wide regression still blocks merge.
The new-file gate itself has a real gap worth knowing about, not relying on:
its CI step only fails on a result explicitly starting with `FAIL` — if the
scanner crashes and produces no report at all, the workflow's own parsing
treats that as `UNKNOWN` and passes it through as if it were fine. Don't read
"the new-file gate passed" as strong a guarantee as "the file is compliant";
confirm your own local run actually produced a real PASS, not a swallowed
crash.

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
...) unconditionally. `category` and `zone` are handled independently of each
other, and each is curated only when its own constant is absent from the tool
file — declaring one validly doesn't touch the other. "Validly" means
different things for the two: a `TOOL_CATEGORY` that merely *looks* like an
identifier (e.g. `made_up_thing`) is kept and passed straight through to
`validate.py`, which then rejects it as a real, visible merge-blocking error
(the vocabulary check below) — only a non-identifier placeholder (a leftover
template string like `{tool_type}`) is silently discarded before that point.
`TOOL_ZONE` is stricter: anything that isn't already a Python `int` in
`1`/`2`/`3` is discarded outright (note `TOOL_ZONE = True` is an `int` equal
to `1` and slips through as zone 1 uncaught; write a real int, never a bool).
Declare a real, valid value for whichever constant applies in code rather
than hand-editing that field in the manifest (a mismatch between two *valid*
declared-vs-curated values is a merge-blocking error); a field whose
constant you didn't declare is still yours to curate. What you must never
hand-edit is **`TOOLS_MANIFEST.md`** itself — change `tools-manifest.yaml` and
rerun `render.py` instead.

The **manifest's** `category` field must land on one of the 16 terms in
`.tool-control/README.md`'s category vocabulary table (`audit_tool`,
`calibration_tool`, `validation_tool`, ...) — both `unclassified` (an omitted
or invalid category) and any string outside it are now **merge-blocking**
errors, not advisory ones. Your `TOOL_CATEGORY` constant doesn't have to
already be one of those 16 literally: a handful of legacy labels
(`governance`, `discovery`, `dispatch`, `site`, `template`,
`meta_validator_tool`) are normalized to a real category by
`CATEGORY_ALIASES` before validation runs — but don't rely on that mapping for
a new tool; declare a real vocabulary term directly. Extending the vocabulary
itself means editing `CATEGORIES` in `scan.py` as its own reviewed change, not
inventing a new string on a tool PR.

A tool at `zone: 2` or `3` needs its manifest entry's own `ratified_by` field
naming a Z2 hash or ratification document — `.tool-control/validate.py` blocks
merge on any zone-2/3 entry with no `ratified_by` (one pre-existing legacy
exception aside). Naming the ratification in the issue or PR description is
not enough on its own; it has to land in the manifest. A tool cannot
self-declare its own waiver (see `.tool-control/README.md`).

## 6. Adding or changing a controlled document

Whether a document is "controlled" is decided by `document-registry.yaml`
itself, not by whether the file happens to carry `doc_id` frontmatter — check
the registry, not the file, before assuming something is free-form. Some
real controlled entries (`OPERATOR_RUNBOOK.md`, `CURRENT.md`) have no
frontmatter at all; the registry lists them by path regardless. Frontmatter
declaring a `doc_id` (format `HAIOS-<AREA>-<nnn>`) is only how
`.doc-control/validate.py` catches a *new* file that should have been
registered but wasn't — it fails the PR with "orphan doc_id" if the declared
`doc_id` isn't in the registry, but says nothing about files with no
frontmatter, controlled or not.

If you're editing a document already in `document-registry.yaml`, no
registration step is needed. If you're adding a genuinely new controlled
document, `document-registry.yaml` has no scan step of its own: it's a
curated YAML list you hand-edit directly, adding your `doc_id` entry with its
required fields — `doc_id`, `title`, `canonical_repo`, `canonical_path`, and
`status` at minimum (`.doc-control/validate.py` blocks merge on any missing).
You must also increment the registry's own top-level `counts:` mapping
(`documents`, `excluded`, `needs_reconcile`) to match reality by hand —
`render.py` doesn't touch it, and `validate.py` blocks merge if it's stale or
missing, the same class of check as the tool manifest's own counters. After
registering, run `python3 .doc-control/render.py` to regenerate
`CONTROLLED_DOCUMENTS.md` from it — like `TOOLS_MANIFEST.md`, that rendered
index is never hand-edited. Most new `.md` files you'll write (tool READMEs,
specs, this file itself) are genuinely free-form and need neither
registration nor frontmatter — but confirm that by checking the registry, not
by the file's subject matter.

## 7. Before you open or update a PR, run what CI runs

(§1's Zone 1/3 carve-out covers exactly the commands below — read it first if
you haven't.) CI on this repo is unforgiving of stale generated files; the
fastest path to a green PR is running the same commands locally first:

```bash
python3 tools/repo_health.py --strict                 # repo vitality gate
python3 .doc-control/render.py --smoke-test            # renderer self-test (document-control.yml runs this first)
python3 .doc-control/validate.py                       # document-control gate
python3 .doc-control/render.py --check                 # CONTROLLED_DOCUMENTS.md in sync
python3 .tool-control/scan.py --smoke-test             # control-script self-tests (tool-manifest.yml runs these first)
python3 .tool-control/validate.py --smoke-test
python3 .tool-control/render.py --smoke-test
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

The commands above cover every PR. If your PR also touches `tools/**/*.py`,
two more path-scoped gates apply and aren't in the list above: `builder-lint.yml`
(§5's Builder scanner, 2 CI steps: a corpus gate and a per-file gate) and
`behavioral-compliance.yml` (§5's AST-level gate, 4 CI steps: the same two
gates plus its own pytest and smoke-test self-tests). They don't scope
identically (§5 covers this in full): `builder-lint.yml`'s per-file gate
covers your PR's added *and* modified files; `behavioral-compliance.yml`'s
per-file gate covers only *added* files, with a modified tool checked solely
through the corpus floor.

Both also gate the whole `tools/` corpus, but reproduce that locally with the
CI thresholds, not the CLI defaults (both scripts default `--min-pass-rate`
to `1.0`, which the current corpus does not meet):

```bash
python3 tools/builder_compliance_scanner_v1.0.py --path tools/ --min-pass-rate 0.90
python3 tools/behavioral_compliance_gate_v1_0.py --path tools/ --min-pass-rate 0.70
```

The Builder corpus run has a blind spot worth knowing: it only scans files
that already contain the `Builder v1.7 compliant` marker
(`_is_builder_corpus_member()`), so an unmarked or non-compliant *new* tool
never shows up in this corpus run at all — the per-file added/modified gate
above is what actually catches that for your PR, not this command.

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
- When in doubt about any of the above under task pressure — "just make CI
  green" is not a reason to guess — comment and stop, per §1.
