# Candidate Block: Q-TOOLCONTROL-03 — Turning the Gate on Itself

**Z1 Proposer:** Claude (AI agent)
**Date Submitted:** 2026-09-13
**Pinned SHA:** `1e1b518` (main, after PR #306)
**Branch:** `claude/tool-manifest-doc-registry-344ako`
**Phase:** 1 (control infrastructure — third pass)
**Status:** AWAITING Z2 RATIFICATION
**Follows:** Q-TOOLCONTROL-01, Q-TOOLCONTROL-02 (both merged, both awaiting Z2)

---

## The question that produced this

After #306 merged, the operator asked: *the gates caught none of those; reviewers did — what does
that tell us about our gates in order to rectify this?*

It is the right question, and the answer was measurable rather than rhetorical.

---

## §A Position · Destination · Probability

**Position:** two control systems now gate the repo. Across three review rounds they caught
drift, staleness and structural violations in the corpus — and **zero** of the four defects in
their own implementation. Every one of those four was found by an external reviewer.

**Destination:** make the gates' own failure paths executable and verified, so a rule that stops
enforcing is a failing check rather than a discovery made by whoever happens to read the code.

**Probability:** **70%** that the coverage requirement is still in force, un-weakened, in 60 days.
Held well below the earlier blocks' 75–80% because this rule taxes the person adding a rule: the
cheapest way past a failing `selftest` is to delete the fixture requirement. The falsifier watches
for exactly that.

---

## Diagnosis — three gaps, one of them measured

### 1 · The gates validated data. Nothing validated the gates.

Every rule answered *"is this manifest entry well-formed?"* None answered *"does this gate do what
its documentation says?"* The corpus was under test; the instrument was not.

**Measured before changing anything:** `.tool-control/validate.py` contained **26 blocking
conditions. Its own smoke test exercised 10.** The other 16 had never been executed — including
`unregistered tool`, the coverage rule the entire system rests on.

That rule *was* tested. By hand, in a shell, during development, and the demonstration was thrown
away. Every negative test across both PRs was transient: run once, reported in prose, never
committed. **The evidence that the gates can fail existed in a transcript, not in the repository.**

### 2 · The control system was exempt from control.

`.tool-control/` and `.doc-control/` sat outside both registries — an exclusion I wrote myself,
in #304, reasoning that control-system internals are governed by CODEOWNERS. The effect was that
the only code gating the whole repository was the one part of it gated by nothing else.

### 3 · Prose claims had no executable counterpart — and this is institutional.

All four defects share one shape: **a rule the documentation asserted and the code did not
enforce.** That is not a new failure mode here. It is item 3 of Q-TOOLCONTROL-01 — `CLAUDE.md`
describes CI-enforced Z2-hash, Merkle and anti-cascade gates that are not wired — and item 2 —
`CONTROLLED_DOCUMENTS.md` instructing readers not to hand-edit it because it was "rendered from"
a registry by a renderer that did not exist. Counting precisely: **two pre-existing instances
plus the four defects above — six in total**, in five different places.

There is a fourth instance worth naming plainly: the repository's own research note is
`docs/REFLEXIVE_CALIBRATION_PAPER_V1_0.md` — *"The Instrument Turned Inward"* (HAIOS-RES-009).
The failure here is the one that paper's title describes.

---

## What was built

### `.tool-control/selftest.py` — every rule must be able to fail

One fixture per blocking condition, each constructing a violating manifest and asserting the gate
reports it. All 26 in `validate.py`, plus seven document-control conditions driven end to end as a
subprocess against a throwaway repo root (that validator is a script, not an importable module, so
it is exercised the way CI runs it rather than refactored under test).

**Coverage is enforced, not reported.** An `err()` site with no fixture fails the suite. That is
the part that makes this a ratchet instead of a snapshot, and it was verified in both directions:

| injected defect | result |
|---|---|
| New blocking rule added with no fixture | `undemonstrated blocking condition`, exit 1 |
| Existing rule silently disabled (`if False:`) | `expected an error containing 'requires approved_by + approved_date', got []`, exit 1 |

It also asserts the grandfathered Zone 2 path still **passes**. A rule that only ever rejects is
as broken as one that never does, and nothing was checking that direction either.

### The instruments are now inside the registry

`.tool-control/` and `.doc-control/` were added to `SCAN_ROOTS`. Six control files are now
registered tools (`HAIOS-TOOL-145`–`150`) subject to the same version, category and coverage rules
as everything else; `.doc-control/validate.py` gained the `TOOL_*` declarations it had always
demanded of others. If a control script is deleted or renamed, the coverage rule now notices.

### What was deliberately *not* built

Whether a category is **correct** is a judgment, not a mechanical property. A filename-echo lint
(flagging a tool whose category stem appears in its filename) was the obvious candidate, since it
would have caught both of my subject-over-role errors. It was measured against the corpus before
being written: **14 of 137 tools match, and on inspection all 14 are correct** —
`acat_merkle_auditor` really is an `audit_tool`, `supabase_corpus_connector` really is a
`connector_tool`. It would have produced 14 false positives and zero true positives.

A check that cries wolf trains people to ignore gates, which is worse than no check. Semantic
correctness is what independent review is for — and independent review is what actually caught it.

---

## The finding worth registering

**Self-authored tests are `agent_self_only` evidence about the author's own instrument.**

This repository already has the vocabulary for this. Its corpus distinguishes `agent_self_only`
from `two_stage_verified`, and 81 of 105 rows are the former. My smoke tests were written by the
same process that wrote the bugs, and they tested what I thought to test — which is precisely the
set of things I had not got wrong. They were confirmatory by construction.

The three review rounds are the two-stage half. Their score across this work: **22 findings, 22
correct, 0 false positives.** The gates' score on the same defects: 0.

`selftest.py` does not fix this. It converts one narrow class — *"the code no longer does what the
rule says"* — from undetectable into a failing check. It cannot detect *"the rule is the wrong
rule"*, which is what the category errors were and what review caught. **F candidate:** a
control's self-tests and its adversarial review are not substitutes; the repo should not count a
gate as verified on self-test alone.

---

## §Review round — Copilot, 7 findings, all correct

**The coverage enforcement itself had a bypass.** `blocking_conditions()` found `err()` sites with
a regex matching only `err("` and `err(f"`. A rule written `err('...')`, `err(message)`, or across
multiple lines was invisible to it — so the mechanism built to guarantee every rule has a
demonstration would not have demanded one. Verified by smuggling two such rules in: the regex saw
26 and passed; AST-based discovery sees 28 and fails. **That is the same defect class this block
is about, occurring inside the fix for it — the third consecutive round in which that has
happened.**

**The fixtures tested functions, not the command CI runs.** Every case called `validate_coverage()`
directly while CI invokes `validate.py`. Unwiring the coverage check from `main()` left all unit
fixtures green. An end-to-end subprocess case now builds a throwaway repo with an unregistered
tool and runs the actual command; with the call removed it reports *"validate.py exited 0 with an
unregistered tool on disk — the coverage check is not wired into main()"*.

**Widening the scan scope without widening the trigger.** Adding `.doc-control` to `SCAN_ROOTS`
made its files registered tools, but the workflow's `paths:` filters still listed only
`.tool-control/**`. A PR touching just `.doc-control/validate.py` would have skipped the manifest
and selftest gates entirely, and `document-control.yml` does not run them. This is the identical
hole fixed in #304 (workflows omitting themselves from their own filters), reopened by extending
coverage in one place and not the other.

**`interface: module` was a false promise.** `.doc-control/validate.py` executes at import and
calls `sys.exit()`; the scanner labelled it `module` because it is a `.py` file. Classification
now turns on import-safety — a `.py` without a `__main__` guard is a `script`. Two registered
files were mislabelled; both now read `script`.

Plus two documentation corrections: the workflow header still said "All three are ERROR gates"
after a fourth was added, and this block's own arithmetic said "three times ... twice and twice".

---

## Falsifier

**Claim:** requiring every blocking rule to carry an executable demonstration keeps the gates
enforcing what their documentation claims.

**FALSE if:**

- A blocking rule can be added to `validate.py` and merged with no fixture demonstrating it, OR
- A rule can be silently weakened (its condition made unreachable) while `selftest.py` passes, OR
- The coverage requirement is relaxed, skipped, or made `continue-on-error` to unblock a PR, OR
- A fixture is changed to assert a weaker message instead of the rule being fixed, OR
- Within 60 days another defect of the *same shape* — documentation asserting an enforcement the
  code does not perform — is found anywhere in `.tool-control/` or `.doc-control/` by a reviewer
  rather than by CI.

**Success criterion:** 60 days with the coverage requirement in force, no fixture deletions, and
any new blocking rule arriving with its demonstration in the same commit.

**Explicitly not claimed:** that this would have caught the category errors. It would not have.

---

## Honest limitations, named

- **This verifies that rules fire, not that they are the right rules.** Both category errors would
  pass every fixture here, because each tool's category was internally consistent — just wrong.
- **The fixtures were written by the same author as the rules**, so they inherit the same blind
  spots. The coverage requirement bounds this (every `err()` must be hit) but cannot bound whether
  the *assertion* is meaningful: a fixture asserting a weak substring would pass. The falsifier
  names that as a failure mode rather than solving it.
- **Document-control is covered end to end, not per-condition.** Its validator is a top-level
  script; seven conditions are exercised by subprocess, and coverage there is not mechanically
  enforced the way the tool gate's is. Making it so requires refactoring a working gate, which
  this pass declined to do in the same change. Named as follow-up.
- **`.doc-control/validate.py`'s version was set to 1.1.0** on registration — it had no declared
  version before, so this is an assertion about a file whose history predates the convention.
- **The 26-condition count is of `err()` call sites**, not of semantically distinct rules; several
  sites belong to one rule (three path-shape errors, for instance). The count is a coverage
  denominator, not a claim about rule granularity.

---

## Deliverables

| File | Change |
|---|---|
| `.tool-control/selftest.py` | New — 26 tool + 7 doc fixtures + an end-to-end CLI case; AST-based coverage |
| `.tool-control/scan.py` | `.tool-control` + `.doc-control` in `SCAN_ROOTS`; `interface` now turns on import-safety |
| `.doc-control/validate.py` | `TOOL_NAME`/`TOOL_VERSION`/`TOOL_CATEGORY`/`TOOL_ZONE` declared |
| `.tool-control/README.md` | "Who gates the gate", the measurement, the rejected lint |
| `.github/workflows/tool-manifest.yml` | `selftest.py` as a blocking step; `.doc-control/**` added to both triggers |
| `tools-manifest.yaml`, `TOOLS_MANIFEST.md` | Regenerated — 143 tools, 0 unclassified |
| `z1-inbox/2026-09-13/Q-TOOLCONTROL-03.md` | This block |

No tool's behaviour changed. No status, owner or approval was set.

---

## Z2 Review Checklist

- [ ] The coverage requirement is accepted as blocking: a blocking rule without a demonstration
      fails CI
- [ ] Bringing `.tool-control/` and `.doc-control/` inside the registry is accepted
- [ ] The decision **not** to ship the filename-echo lint is accepted, on the measured 14/14
      false-positive rate
- [ ] The `agent_self_only` finding is routed — a gate verified only by its author's own tests is
      not verified in this repo's own sense of the word
- [ ] Document-control's per-condition coverage is accepted as named follow-up, not silently owed
- [ ] The three open items from Q-TOOLCONTROL-01 (Zone 2 claim, MCP scope, overdue reviews) and
      the status/owner queue are unaffected by this pass

---

## Summary

The gates could not catch defects in themselves because nothing ever ran their failure paths: 10
of 26 blocking conditions had been executed, and the tests that did exist were written by the
author of the bugs, testing what he thought to test.

Every blocking condition now carries a fixture that proves it fires, and a rule without one fails
the suite. The instruments are inside the registry they enforce. The one class this cannot reach —
whether a rule is the *right* rule — is named rather than papered over, and the measurement that
proved a lint would not reach it either is recorded instead of the lint.

Reviewers: 22 findings, 22 correct. Gates, on those same defects: 0. That ratio is the argument
for keeping adversarial review in the loop, not for believing the gates now suffice.

**Ratification requested.**
