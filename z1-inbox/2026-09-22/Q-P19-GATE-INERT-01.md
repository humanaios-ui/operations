# Q-P19-GATE-INERT-01 — the principle-compliance gate reported green without opening a file

**Type:** IC · Tier 2 (edits `.github/workflows/` and `tools/agents/`) · **Author:** Z1 (Claude) · **Status:** awaiting_z2
**Authorised by:** Night, 2026-09-22 — *"Safe to fix P19 gate defect."*
**Found on:** PR #446, which happened to be the rare shape that made the gate run.

---

## The finding

`Check principles (P19)` failed on PR #446 with `P-HUMILITY: Absolute language in
tools/graph_convergence_v1_0.py`. Investigating why it had *not* failed on #442,
which added that same file containing the same words, produced the real finding:

`.github/workflows/agent-principle-compliance-check.yml` built its file list with

```bash
CHANGED_FILES=$(git diff --name-only HEAD~1 HEAD)
```

which emits **one path per line**. The bot split it on **commas**:

```python
files = [f.strip() for f in args.files.split(",")]
```

So every multi-file change arrived as a single blob of newline-joined paths. That
blob does not end in `.py`, `check_code_file` was never called, and the gate
printed `✓ All checks passed` having inspected nothing.

**P19 only inspected code when a change touched exactly one `.py` file and
nothing else.** Verified by running the bot both ways:

```
two files in, newline-joined (as the workflow passed them)
  Files changed: 1        <- one "file" seen
  ✓ All checks passed

one .py file in
  ⚠ 1 violation(s) detected
```

Measured on the real #442 file list: **0 Python files opened** where 1 should
have been.

## Why this is the worst of the four

This session recorded three artifacts whose link to their referent went dead
while the artifact stayed alive — `A11` enforcing distinctness that `A13` made
irrelevant, a claim about `MOLT_STATE.md` written without reading it, and
`0.8632` copied 38 times from a corpus that stopped reproducing it. This is the
same family and it is worse, because of an asymmetry worth stating plainly:

> Prose that is wrong is **neutral** evidence — a reader may or may not believe
> it. **A green check is positive evidence.** It actively tells every reader the
> property was checked. An inert gate does not fail to inform; it misinforms, on
> every pull request, in the direction of reassurance.

## The second defect, and why both had to be fixed at once

`check_code_file` read the **whole file** and matched a bare substring. Measured
on this tree: **113 of 373 `.py` files** contain `always`, `never` or
`impossible` somewhere — **30%**.

Repairing only the plumbing would therefore have switched on a gate that fails
roughly a third of Python files for words the change did not write. That is the
"push that turns CI red" failure at repository scale, and it is why this
candidate fixes both or neither.

## What changed

| Defect | Fix |
|---|---|
| Newline list, comma split | `split_file_list()` splits on either; the workflow comma-joins so the contract is explicit rather than incidental |
| Whole-file scan | `added_lines()` diffs against the PR base; only lines the change **adds** are scanned |
| Bare substring | word-boundary regex — `nevertheless` no longer matches `never` |
| Unreadable diff passed silently | a failed `git diff` now exits non-zero: **a gate that cannot see its input must not report green** |
| The bot would flag itself | `SELF_EXEMPT`, with the same reason `tests/test_temporal_dissolution_gate.py` carries — a detector must contain the pattern it detects |

The workflow also now diffs against `github.event.pull_request.base.sha` rather
than `HEAD~1`, which on a PR's synthetic merge commit is only accidentally the
base.

### Proved, not asserted

Against the real #442 file list:

```
old: files parsed 1 · python files opened 0
new: files parsed 3 · python files opened 1
```

Against the real #446 diff:

```
whole-file matches (old scan would blame all on this PR):  8
lines this change adds:                                    52
added lines flagged (new scan):                             1
  -> "any declared exposure may only lower a grade, never raise it."
```

The smoke test went from 1 check (construct the bot) to **12**, every one a
regression test for a way this gate reported green while inspecting nothing. The
old smoke test is itself part of the finding: **the thing that was broken was
never the thing being tested**, which is why the defect survived.

## What Z2 is asked to decide

1. **Ratify the fix.** Tier 2, measured — the classifier returns 2 against this
   diff and Z1 claimed 2.
2. **Calibrate P-HUMILITY, which Z1 deliberately did not touch.** The now-working
   gate flags exactly one added line on #446: *"any declared exposure may only
   lower a grade, never raise it."* That is absolute language **and** it is a
   correctly-stated invariant. The rule as written cannot tell those apart, and
   softening a governance principle is not Z1's to do. Options Z2 may want:
   leave it strict and let authors reword or justify; narrow the rule to prose
   outside code contracts; or accept invariant statements explicitly.
3. **Whether the gate should block.** It is currently non-required — #446 merged
   `unstable` with it red. A gate nobody must satisfy is a weaker version of the
   one this candidate just repaired.
4. **Whether other gates are inert.** This one was green for an unknown period
   while checking nothing, and it was found by accident. The general form is
   below.

## The generalisation worth more than the fix

> **A gate that has never failed is either protecting a property nobody
> violates, or not running.** Those are distinguishable from CI history, and the
> observation that proves a gate is alive is a failure.

That is `Q-DEFERRAL-RULE-01`'s leg 3 pointed at our own instruments: an
assertion needs an ending observation, and "this gate works" is an assertion.
Z1 recommends a liveness audit across the ~52 workflows before adding any new
gate, and has not run one — it is a separate candidate and Night has approved
filings individually.

## Falsifier

FALSE if the old code path did in fact open files on multi-file changes — i.e.
if `"a\nb".split(",")` yields two entries. Mechanically checkable, and checked:
it yields one.

FALSE if scanning added lines rather than whole files misses a violation the old
scan would have caught **in the change under review**. It cannot: added lines are
a subset of the file, and every line the old scan blamed on a PR that the new one
does not was already in the tree before that PR.

Also FALSE if the 113/373 measurement is wrong, which would change whether both
defects had to be fixed together. Re-runnable:
`grep -rlE "\b(always|never|impossible)\b" --include="*.py" .`

## Evidence

- `.github/workflows/agent-principle-compliance-check.yml` — the newline list
- `tools/agents/principle_compliance_bot_v1.py` — the comma split, the whole-file scan
- PR #446 comment — the diagnosis, posted before this fix
- PR #442 check run — `Check principles (P19)` reporting success on 12 changed files
- `tools/molting_protocol_diff_v1_0.py` — `.github/workflows/` as a `GATE_PATHS` entry

```yaml
z2_decision: {status: awaiting_ratification, ratified_at: null, ratification_hash: null, z2_notes: ""}
```
