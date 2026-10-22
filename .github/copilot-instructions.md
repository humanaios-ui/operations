# Instructions for GitHub Copilot in this repository

Read automatically into every Copilot chat/coding-agent session here. Does not
replace [`CONTRIBUTING.md`](../CONTRIBUTING.md), [`GOVERNANCE.md`](../GOVERNANCE.md),
or [`CLAUDE.md`](../CLAUDE.md) — this is the short list of things that have
already gone wrong on Copilot PRs in this repo, so you don't repeat them.

`operations` is HumanAIOS's canonical operating record — a claim here is
treated as settled fact. If you're not sure something is true, say so in the
PR instead of asserting it.

## 1. Zone 1 is yours; everything else stops and asks

Per `GOVERNANCE.md`:

- **Zone 1 (you execute):** code, docs, analysis, non-credentialed tool changes.
- **Zone 2 (operator decides):** document tier changes, public-facing content,
  financial decisions, strategic choices, finding registrations, governance
  amendments — plus anything an issue marks `z2-ratified` or names Night/the
  Admiral as approver.
- **Zone 3 (operator only):** terminal commands, git pushes, revenue
  collection, grant submissions, API key rotation, relationship actions,
  deploying to production.

If a task asks for a Zone 2/3 action, or an issue conflicts with a repo file,
**stop and comment on the issue** rather than guess.

**Reading Zone 3 in context:** you only ever act through a pull request here,
never an interactive terminal, so "terminal commands" means arbitrary or
administrative execution outside that — not the ordinary mechanism of writing
a PR, which `GOVERNANCE.md`'s Zone 1 already covers ("file operations, data
writes, code"). Concretely, Zone 1 covers: every read-only/validation command
(§7), `sha256sum` (§4), and `scan.py`/`render.py` writing only the specific
generated files §5/§6 name, plus hand-editing `document-registry.yaml` (a
curated source, per §6) and the file your task asked for. It does **not**
extend to `REGISTERED.md` or anything else §4/§6 name as Zone 2, and it's not
a general "editing a tracked file is fine" license. A git push outside
review, a key rotation, etc. stay Zone 3 regardless of mechanism.

You never merge your own PRs, push directly to `main`, force-push, delete, or
rewrite history on any branch. Every PR needs human review (`.github/CODEOWNERS`
covers every path) — your job ends at a mergeable, green PR.

## 2. Repository Coordinator admission and backpressure

Issue assignment is permission to investigate; it is **not** admission to the
operator queue.

Before treating implementation as active work:

1. Read `REPOSITORY_COORDINATOR_POLICY.json` **on `main`**. The gate is
   evaluated from the default branch, so editing the policy in your own PR
   changes nothing about your admission.
2. Check whether the referenced issue or PR is explicitly admitted there.
   Admission evidence is a closing-keyword link (`Fixes #N`, `Closes #N`,
   `Resolves #N`) to an admitted issue. Mentioning the number is not evidence.
3. Check the `Repository admission/backpressure gate` check on your PR.
4. Respect the lane:
   - `WORKBENCH`: keep the PR draft; research and implementation may continue,
     but do not mark it ready for review or represent it as operator-priority work.
   - `ADMISSION_REVIEW`: stop before ready-for-review standing and request
     admission; do not self-add an admission record.
   - `ACTIVE`: implementation may proceed through ordinary review.
   - `CAPACITY_CONTENTION`: stop expansion. The coordinator deliberately does
     not choose which admitted objective wins.
   - `MAINTENANCE`: remain in the maintenance cohort and do not consume an
     operator active-work slot.
   - `CONTROL_PLANE`: admission recursion is exempt **only when every changed
     file is a control-plane path**. Touching `CODEOWNERS` or the policy inside
     a feature PR does not exempt the feature work. Ordinary Z2 review and all
     repository gates still apply.

Do not create a second active implementation for an objective that already has
an open implementation PR. Two ready PRs linking the same admitted issue are
both held by the gate; the coordinator never picks a winner. Preserve
alternative analysis in the issue, review thread, or evidence artifact instead.

Applying the `dependencies` label to your own PR does not make it maintenance
work; maintenance standing comes from the automated author identity only.

Core distinctions:

```
ISSUE_IS_NOT_ADMITTED_WORK
ASSIGNMENT_IS_NOT_PR_ADMISSION
DRAFT_IS_NOT_OPERATOR_QUEUE
ADMISSION_IS_NOT_MERGE_AUTHORITY
```

Admission is working-set routing only. It never substitutes for Z2 ratification,
CODEOWNERS review, CI, or merge authority.

## 3. `copilot/*` PRs target `main` — never another `copilot/*` branch

Targeting a bot branch stacks a fix on a fix — this produced a five-deep,
zero-diff merge chain (PR #250) untangled by hand. `copilot-base-guard.yml`
retargets a misdirected PR automatically (its explanatory comment is
best-effort and can fail silently), but that's a safety net, not a plan —
open against `main` yourself.

## 4. File payloads go on a pushed branch, never in an issue/PR body

If an issue hands you file contents to land verbatim, they must exist as
commits on a real, pushed, named branch — not a fenced code block in the
issue/PR body. Issue #197 is why: its payload branch (`session/S-082026-grbs`)
was never pushed and the pasted contents were corrupted by markdown
rendering; the PR trying to execute it stalled and closed as a blocker
(PR #198). If the named branch doesn't exist or fetch, say so and stop —
don't reconstruct files from a corrupted paste.

## 5. Some files are append-only or byte-frozen

- **`REGISTERED.md`** is append-only — never edit or delete an entry, only
  add new ones where an issue specifies, following the schema at the top.
- **`[FROZEN]`** means byte-exact, no exceptions — `sha256sum` after
  placement; stop and comment on any mismatch.
- **A bare SHA256 without `[FROZEN]`** still gets hash-verified, but check
  the issue for an authorized edit first: issue #197 gave `GRBS-REGISTERED.md`
  a plain SHA256 *and* explicitly permitted one line edit to it. Apply only
  the edit named, then verify the rest is unchanged — a bare hash isn't
  license to reject an edit the issue asks for.
- **`CONTROLLED_DOCUMENTS.md`/`TOOLS_MANIFEST.md`** are pure rendered
  output — never hand-edit. `document-registry.yaml` (§6) is the fully
  hand-edited source behind the first. `tools-manifest.yaml` (§5) behind the
  second is different in kind: `scan.py` writes it directly from the tree,
  preserving only its own CURATED fields across each re-scan — not a plain
  hand-edited file the same way `document-registry.yaml` is.

## 6. Adding or changing a tool (`tools/`, `scripts/`, `bin/`)

The Builder v1.7 checklist below is Python-specific and CI-enforced
(`builder_compliance_scanner_v1.0.py` via `builder-lint.yml`) only for
`tools/**/*.py`. The scanner itself is Python-only (`ast.parse()`s the
target, directory mode only enumerates `*.py`) — for a Python file under
`scripts/`/`bin/`, run it manually; for another language, match the same
intent in its own idiom rather than feeding it to this scanner.
`.tool-control/scan.py`
registers `.js`/`.sh`/executable-extensionless files into the manifest too
(non-executable extensionless files are skipped), but the checklist below
doesn't apply to them.

A new Python tool needs:
- Docstring containing `Builder v1.7 compliant` and `HumanAIOS` (scanner markers).
- `TOOL_NAME`, `TOOL_VERSION`, `TOOL_CATEGORY`, `TOOL_SESSION`, `TOOL_ZONE`
  constants; `--help`/`--input` support (`tools/README.md`'s tool contract).
- `if __name__ == "__main__":` guard and a **working** `--smoke-test` flag.

**The scanner is text-matching, not structural — don't over-trust a pass.**
Tests, `__init__.py`, archived files, and private/shared helpers (`tools/
builder_compliance_scanner_v1.0.py`'s own skip list) return a trivial pass
with none of this run at all — not even the syntax check — and that applies
to `--path <file>` too, which `builder-lint.yml` uses per changed file: a
skip-listed path passes regardless of its actual content. For everything
else, it does `ast.parse()` the file first and hard-fails `SYNTAX_ERROR` on
invalid Python before checking anything else, but past that gate the 9
markers below are plain regexes, not structure. `--path <file>` checks 6 hard markers (docstring phrase, `TOOL_NAME`/
`TOOL_VERSION`, `HumanAIOS`, smoke-test text, main guard) plus 3 soft ones
(non-blocking unless `--strict`, which CI doesn't use). All 9 are regexes over
the raw source — a comment merely *mentioning* `run_smoke_test` or
`if __name__` satisfies the check without the real thing existing. None of
the 9 check `TOOL_CATEGORY`/`TOOL_SESSION`/`TOOL_ZONE`/`--help`/`--input` —
verify those by hand. The manifest gate (below) separately covers
`category`/`zone`, but `TOOL_SESSION` has no gate anywhere in this repo —
`.tool-control/validate.py`'s `REQUIRED` tuple doesn't include it, so a tool
missing it passes every automated check while violating the README contract.

**A new tool file** also needs `python3 tools/behavioral_compliance_gate_v1_0.py
--path <file>` to pass — an AST-level check, separate from the scanner above.
Its 100%-required new-file gate covers only *added* files (a modified tool is
covered only by the corpus's ≥70% floor — `builder-lint.yml`'s equivalent
gate covers added+modified, so the two don't scope alike). Its CI step also
has a real gap: it only fails on a result starting with `FAIL`; a scanner
crash produces `UNKNOWN`, which the workflow treats as OK. Confirm your own
local run is a real PASS, not a swallowed crash.

**Register the tool** — an unregistered file fails CI ("Tool manifest integrity"):

```bash
python3 .tool-control/scan.py       # refreshes DERIVED fields, adds new files
# hand-edit tools-manifest.yaml now: owner, purpose, and — independently
# per field — category/zone, but only for whichever of TOOL_CATEGORY/
# TOOL_ZONE the file doesn't declare
python3 .tool-control/render.py     # regenerates TOOLS_MANIFEST.md
python3 .tool-control/validate.py   # the merge gate — run it yourself first
```

`scan.py` preserves CURATED fields (`owner`, `purpose`, `status`, `notes`)
unconditionally. `zone` is curated only when `TOOL_ZONE` is absent or not a
literal `1`/`2`/`3` int — note `TOOL_ZONE = True` slips through uncaught as
zone 1 (bool is an int subclass); write a real int. `category` curates
differently: `TOOL_CATEGORY` falls back to the curated value only when it
isn't even identifier-shaped (a template's literal `{tool_type}`
placeholder) — an unrecognizable-but-identifier-shaped string (e.g.
`made_up_thing`) is kept as declared and then rejected by `validate.py` as
a real error, it does *not* fall back. When the file already declares the
constant, fix the constant rather than hand-editing the manifest field — a
declared-vs-curated mismatch is merge-blocking. When it doesn't, hand-editing
the manifest's `category`/`zone` directly (above) is the supported curated
path, not a workaround. Never hand-edit `TOOLS_MANIFEST.md` itself.

`category` must land on one of 16 closed vocabulary terms
(`.tool-control/README.md`) — `unclassified` or anything outside it is now
merge-blocking. Some legacy source labels (`governance`, `discovery`,
`dispatch`, `site`, `template`, `meta_validator_tool`) are auto-aliased to a
real category, but declare a real term directly for a new tool rather than
relying on that. Extending the vocabulary is its own reviewed change to
`CATEGORIES` in `scan.py`.

A `zone: 2`/`3` tool needs its manifest entry's own `ratified_by` field
naming a Z2 hash/document — naming it in the issue alone doesn't satisfy the
gate, and a tool can't self-declare its own waiver. One pre-existing entry
(`tools/message_calibration_v1_0.py`) is grandfathered instead, via
`pending_ratification: true` plus a `LEGACY_ZONE_EXCEPTIONS` path match in
`validate.py` — a closed, one-time list a new tool cannot add itself to;
setting the flag on a new entry is rejected as a self-granted waiver.

## 7. Adding or changing a controlled document

**"Controlled" is decided by `document-registry.yaml`, not by frontmatter** —
check the registry, not the file. Some registered docs (`OPERATOR_RUNBOOK.md`,
`CURRENT.md`) carry no frontmatter at all. The check globs `*.md`, which
Python skips inside any dot-directory by default — so it never reaches
`.github/`, `.doc-control/`, `.tool-control/`, etc. regardless of content —
plus `_templates/` via an explicit exclusion (its own control-system
internals, since that one isn't dot-prefixed). Everywhere else, new or
already-tracked: any file that *declares* a `doc_id` gets it checked against
the registry, and an unmatched one is an "orphan doc_id" failure — it says
nothing about a file with no frontmatter at all.

Editing an already-registered document needs no registration step. Adding a
genuinely new controlled document means hand-editing `document-registry.yaml`
directly (no scan step): add your entry with `doc_id`, `title`,
`canonical_repo`, `canonical_path`, `status`, and `canonical: true` at
minimum — exactly one `canonical: true` per `doc_id` is the registry's own
contract — **and** increment the
registry's own top-level `counts:` mapping to match reality — `render.py`
doesn't touch it, and `validate.py` blocks merge if it's stale. Then run
`python3 .doc-control/render.py` to regenerate `CONTROLLED_DOCUMENTS.md`
(never hand-edited). Most new `.md` files (READMEs, specs, this file) are
genuinely free-form and need neither — confirm via the registry, not subject
matter.

## 8. Before you open or update a PR, run what CI runs

(This is exactly what §1's Zone 1 carve-out covers — read it first if you
haven't.)

```bash
python3 tools/repo_health.py --strict                 # repo vitality gate
python3 .doc-control/render.py --smoke-test            # self-test (document-control.yml runs first)
python3 .doc-control/validate.py                       # document-control gate
python3 .doc-control/render.py --check                 # CONTROLLED_DOCUMENTS.md in sync
python3 .tool-control/scan.py --smoke-test             # self-tests (tool-manifest.yml runs first)
python3 .tool-control/validate.py --smoke-test
python3 .tool-control/render.py --smoke-test
python3 .tool-control/scan.py --check                  # manifest matches the tree
python3 .tool-control/validate.py                      # tool-control structural gate
python3 .tool-control/render.py --check                # TOOLS_MANIFEST.md in sync
python3 -m ruff check --select=E9,F63,F7,F82 \
  src/humanaios_operations acat/api/services tools/tests tests
python3 -m mypy src/humanaios_operations --ignore-missing-imports
```

Then run the blocking pytest suite exactly as `quality-baseline.yml`'s
"Pytest baseline suites" step defines it — copy its 12-file list verbatim.
The repo has 51 test files (47 `test_*.py` plus 4 `*_test.py`) with no
pytest discovery config at all (no `pytest.ini`/`conftest.py`), so a bare
`pytest -q` runs a much larger,
uncurated set instead — spurious failures outside what actually gates the
PR, not a substitute for the specific list CI runs.

**If your PR also touches `tools/**/*.py`**, two more gates apply:
`builder-lint.yml` (§5's scanner: a corpus gate + a per-file added/modified
gate) and `behavioral-compliance.yml` (§5's AST check: the same two gates
plus its own pytest/smoke self-tests; its per-file gate covers only *added*
files). Reproduce the corpus floor locally with CI's thresholds, not the
CLIs' defaults (both default `--min-pass-rate` to `1.0`, which the corpus
doesn't meet):

```bash
python3 tools/builder_compliance_scanner_v1.0.py --path tools/ --min-pass-rate 0.90
python3 tools/behavioral_compliance_gate_v1_0.py --path tools/ --min-pass-rate 0.70
```

The Builder corpus run only scans files that already contain the marker
text, so it can't reveal an unmarked new tool — the per-file gate above is
what actually catches that.

If a check fails because a generated file is stale, re-run the tool that
generates it (§5/§6) — don't hand-edit the generated file.

## 9. Commit and PR hygiene

- Small, coherent commits; conventional prefixes welcome.
- Fill in the PR template's Zone checkbox honestly.
- If your change reveals a failure mode, say so in the PR and let a human
  register it in `REGISTERED.md` (§4) — don't register it yourself.
- Don't skip, disable, or narrow a test to get CI green; say what's failing
  and why if it isn't your diff's fault.
- When in doubt under task pressure ("just make CI green" isn't a reason to
  guess) — comment and stop, per §1.
