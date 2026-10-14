# Q-ISSUE-TRIAGE-CONVENTION-01 — Labels, assignees, and triage for repository issues

**Proposal ID:** Q-ISSUE-TRIAGE-CONVENTION-01
**Date:** 2026-10-14
**Authority:** Z1 (Claude) proposes; Z2 (Night) ratifies
**Tier:** Tier 1 (repository convention; no change to CODEOWNERS, branch protection, or any Z2-signed file)
**Trigger:** Issue #824 (Pre-Phase 2 audit) was filed without labels or assignees because no convention exists in this repository.
**Status:** Awaiting Z2 ratification

---

## Executive Summary

`operations` has no written convention for issue labels, assignees, or triage.
The closest artifacts are `.github/CODEOWNERS` (a self-review placeholder with a
single collaborator), two issue templates, and label rules that apply only to
external-repo engagements in `GITHUB_COLLABORATION_GOVERNANCE.md`. Issues are
therefore filed with inconsistent or no metadata, and nothing connects an issue to
its Priority Queue item or its Z2 decision.

This proposal sets a small, fixed label vocabulary, a single assignee rule, and one
linking rule. It deliberately does not create a triage role, because the repository
has one collaborator.

---

## Proposed convention

### 1. Labels (three axes, 10 labels maximum)

Every issue carries **exactly one** label from each axis it applies to.

| Axis | Label | Meaning |
|:---|:---|:---|
| **kind** | `kind:governance` | Changes or audits governance, registry, or authority artifacts |
| | `kind:defect` | Something is broken or drifted from its stated spec |
| | `kind:research` | Hypothesis, experiment, or measurement work |
| | `kind:ops` | Deployment, CI, tooling, or infrastructure |
| **state** | `state:needs-triage` | Filed; not yet read against the Priority Queue |
| | `state:ready` | Triaged; has an owner and a Priority Queue ID |
| | `state:awaiting-z2` | Blocked on a Z2 ratification or decision |
| | `state:blocked` | Blocked on something other than Z2 (name it in a comment) |
| **authority** | `zone:z1-proposal` | Z1 is proposing; no execution authority implied |

Closing an issue needs no label; use GitHub's close reason (`completed` or
`not planned`) as CLAUDE.md's issue hygiene already requires.

`state:needs-triage` is removed when the issue reaches `state:ready`. Issues are
never left in `needs-triage` past the next Z1 session-open (§A) without a comment
explaining why.

### 2. Assignees

- **Z2 decision holder:** the repository owner (`@humanaios-ui`) is assigned to any
  issue whose resolution requires a Z2 ratification. This is the only assignee the
  current access model supports.
- **Z1 author:** Z1 does not assign itself. The issue body names the proposal ID
  instead.
- **Z3 executor:** assigned only when a Z3 assignment exists in `ZONE_REGISTRY.md`
  for that repository. Until then, unassigned.

Assignees are not reviewers. Review requirements remain governed by `CODEOWNERS`
and are out of scope for this proposal.

### 3. Linking

Every issue that proposes or tracks work names:

- its Priority Queue ID if one exists (`PRIORITY_QUEUE.md`), and
- its Z1 proposal ID if one exists (`Q-…`), with the `z1-inbox/<date>/` path.

Issues that have neither are allowed only for `kind:ops` and `kind:defect`.

### 4. Who may change the convention

- Z1 may propose label additions or removals through a new Q-block.
- Labels are created or deleted in GitHub only after Z2 ratifies the proposal.
- The label set is capped at 10 labels. Adding an eleventh requires removing one.

---

## Retroactive application

Issue #824 would be labeled `kind:governance`, `state:awaiting-z2`, and linked to
the Priority Queue item for its five items once one exists. No other open issues
are relabeled by this proposal. A separate pass over open issues is a follow-up if
Z2 ratifies.

---

## Falsifier

This convention fails if, on any measurement taken **30 days after ratification**:

1. **Label coverage:** fewer than 80% of issues opened after ratification carry a
   `kind:` label **and** a `state:` label. Measured by listing issues created after
   the ratification date and counting labels via the GitHub API.
2. **Linking:** more than 20% of issues labeled `kind:governance` or `kind:research`
   name neither a Priority Queue ID nor a `Q-` proposal ID.
3. **Drift:** any `state:needs-triage` issue is older than 14 days without a comment.

If any condition holds, the convention is revised or retired by a new Z1 proposal.
The falsifier is a count, not an impression.

---

## Explicit non-goals

- No change to `.github/CODEOWNERS`. That file is Z2-owned and its placeholder
  status is recorded there.
- No change to branch protection or required reviews.
- No triage rota. With one collaborator, a rota would be fiction.
- No new issue templates in this proposal.
- No edit to `REGISTERED.md` or `z1-inbox/INDEX.yaml`. Registry writes are Z2-only;
  this block is filed as a candidate and does not register itself.

---

## Decision requested from Z2 (Night)

- [ ] **ACCEPT** the three label axes, the assignee rule, and the linking rule as written
- [ ] **EDIT** — specify changes
- [ ] **REJECT** — specify reason; Z1 may re-propose within 48h

Z2 may also instruct the retroactive labeling of #824 directly.

---

## Open questions for Z2

1. Should the `zone:z1-proposal` label be replaced with a Z2-maintained `zone:` set
   that mirrors `ZONE_REGISTRY.md`? Z1 recommends not, to keep the set at 10.
2. Should `kind:ops` issues be exempt from the Priority Queue link rule? Z1
   recommends yes, as drafted.
