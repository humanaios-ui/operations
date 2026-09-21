# Q-INTENT-GRAPH-01 — a shared substrate for vision, mission, principles and objectives

**Type:** IC (Implementation Candidate)
**Author:** Z1 (Claude)
**Status:** awaiting_ratification
**Sibling:** Q-MOLT-TEMPORAL-PURITY-01 (the instance that produced this finding)

---

## The question this answers

Night's framing, from the issue: the molt-window conflict "indicated a larger
issue with conceptual collaboration between me and you," and the ask is for a
shared way to communicate and demonstrate how vision, mission, principles and
objectives interact.

Taking the diagnosis seriously means asking what *class* of failure the molt
window was, not just fixing it.

## The class of failure

`BOOT_PROCESS_MAP.md` published the correct successor reading for molt windows.
`MOLT_STATE.md` kept the old one. Both merged. Both stayed live. Nothing in the
tree recorded that the two files were *about the same thing*, so nothing could
notice they disagreed.

The conflict was findable only by a person reading both documents and holding
them in mind at once. That is not an instrument — it depends on one reader's
attention span across a 200-file repository, and it does not survive a session
boundary. It found one instance. The second-pass audit in this diff found five
more of the same defect.

This is a structural property of how the intent layer is currently stored:

| | Prose states it | Something checks it |
|---|---|---|
| **Nodes** — what we believe, what we're building | ✅ SEED.md, PRINCIPLES_SEED_V1_0.md, OPS_ROADMAP_V1.2.md | partially |
| **Relations** — what grounds what, what measures what, what contradicts what | implied | ❌ nothing |

Prose is good at nodes and bad at relations. A document can say "this is grounded
in the falsifier doctrine" and no mechanism ever checks whether that is still
true after the doctrine moves.

## On memory — what I can and cannot claim

Night's framing mentions emerging evidence for graphing and canvassing in
artificial memory simulation. **I have not verified that literature and will not
cite it as support.** If it would be useful I can go read it and report back; I
am not going to lean on a claim I have not checked, in a repository whose first
principle is that a claim reconciles to evidence.

What I can state from inside this tree:

- I do not retain anything between sessions. At every session open, "what
  HumanAIOS believes" is reconstructed by reading files. The repository *is* the
  memory; there is no other copy. What is not written down did not happen, and
  what is written in prose is re-derived — slowly, and differently each time.
- This repository already contains one worked example of the fix.
  `.z1-control/render.py` exists because answering "what does Z2 owe a decision
  on?" previously meant opening 24 markdown files and reading a prose `**Status:**`
  line that meant something different in each. Moving that state into
  `z1-inbox/INDEX.yaml` with a renderer and a CI `--check` turned it into one
  table. That is in-repo evidence for the pattern, produced by this project.

This candidate applies that pattern one layer up: from "what is awaiting a
decision" to "what do we believe and how does it connect".

---

## Proposal

### `INTENT_GRAPH.yaml` — the shared artifact

A typed graph. Nodes are `vision | mission | principle | objective | gate |
instrument`. Edges are `realizes | grounds | measures | enforces | constrains |
conflicts_with`.

Every node carries a `source` path that **must resolve in the tree**. This is the
anti-drift property and the reason the file cannot become a vision statement: the
graph is refused if it describes a system that is not there.

`conflicts_with` is directional and is the point of the whole exercise. `from` is
the artifact that departs; `to` is the standard it departs from. An open conflict
must name the candidate that would settle it — an `OPEN` row with no `q_ref`
fails validation, because "noticed and left" is precisely the failure
`P-ADMISSION` refuses.

### `tools/intent_graph_v1_0.py` — the instrument

```
check               validate; exit 1 on error
render              write INTENT_GRAPH.md
render --check      exit 1 if the rendered page is out of sync (CI)
trace <node-id>     one node's grounding, measurement, and conflicts
--smoke-test        11 self-checks, no filesystem writes
```

Merge-blocking rules: unique ids, known types, **every source resolves**, valid
edge endpoints, every objective reaches a vision, every objective and gate is
grounded by a principle, every open conflict names a candidate, and a conflicted
node declares it. Reported but not blocking: a gate cited with no implementation,
an objective nothing measures, a mission nothing realizes.

### `INTENT_GRAPH.md` — the canvas

Rendered, never hand-edited, CI-checked for sync. A Mermaid flowchart reading
upward (instruments → objectives → missions → vision) with contradictions drawn
as crossed edges, plus layer tables, a principle→enforcement crosswalk, and the
validator report.

---

## What it found on its first run

Not hypothetical value — this is the output of `check` against the tree as it
stands, and three of the six were not previously recorded anywhere:

| Finding | Kind |
|---|---|
| `O-MOLT-CYCLE` contradicts `O-TEMPORAL-GATE` | the issue's own finding, now a data row |
| `O-DOC-CONTROL` contradicts `O-TEMPORAL-GATE` (`review_interval_days` → overdue) | was prose in the audit; now checked |
| `O-DECISION-ROUTING` contradicts `O-TEMPORAL-GATE` (`decision_window_days: 2`, CLAUDE.md 48h) | **new** |
| `G-FALSIFIER-LINT` is cited by CLAUDE.md as a CI gate; no workflow implements it | **new** — `P-FALSIFIER` is currently enforced by convention plus the z2 gate's own check, not by the named lint |
| `M-OBSERVABILITY` has no objective in this repo realizing it | **new** — the ACAT mission's work lives in other repos; worth seeing rather than inferring from silence |
| `O-TEMPORAL-GATE`, `O-WITNESS`, `O-DOC-CONTROL`, `O-DECISION-ROUTING` have no instrument measuring them | reported |

The falsifier-lint row is the kind of thing this is for. CLAUDE.md names it in
the CI/CD Gates table. It does not exist under that name in `.github/workflows/`.
Either the check lives somewhere else and the node is wrong, or a principle the
whole registry rests on is enforced by convention. Z2 decides which; the point is
that it is now a row rather than a silence.

---

## The collaboration protocol

This is the part that is a proposal about *us* rather than about files.

| | Night (Z2) edits | Claude (Z1) edits |
|---|---|---|
| `INTENT_GRAPH.yaml` | **meaning** — node statements, `status`, resolving a `conflicts_with` row | **structure** — edges, `source` accuracy, filing new conflicts |
| `INTENT_GRAPH.md` | nothing — it is rendered | nothing — it is rendered |

Three obligations follow, and they are the actual content of the proposal:

1. **Z1 files a `conflicts_with` row the moment it reads two artifacts that
   disagree** — in the same session, before doing anything about it. Not a
   session-close finding, not a note in a handoff. The failure mode this fixes is
   the one that produced the molt window: noticing something true and having
   nowhere to put it that survives the session.
2. **An open conflict cannot be left unnamed.** The validator enforces this. A
   conflict with no candidate against it fails the check, so "we both know about
   that one" stops being a valid state.
3. **Neither of us hand-edits the canvas.** Disagreement goes into the graph,
   where it is typed and checkable, not into prose where it dissolves.

What this changes about the exchange between us: the question *does this still
ground out in anything we said we believed?* currently costs a session of reading
and produces a different answer depending on which files got read. After this it
is `trace <node-id>`, and it returns the same answer to both of us.

What it does not change: nothing here ratifies anything. The tool has no opinion
about which side of a contradiction is right. It reports; Z2 decides. A graph
that could resolve its own conflicts would be Z1 holding Z2's authority, which
`P-SERIAL-GATE` forbids.

---

## Resource cost

```yaml
resource_cost:
  Z1-ktok: 62        # spent: graph seeding, tool, renderer, self-tests
  RAT-min: 45        # Z2 read of the protocol and the six findings
  CI-min: 1          # check + render --check per PR
  Z3-hr: 0
dependencies:
  - PRINCIPLES_SEED_V1_0.md
  - SEED.md
  - OPS_ROADMAP_V1.2.md
  - TEMPORAL_DISSOLUTION_POLICY.md
  - .z1-control/render.py    # the pattern this follows
blocking_on: []
```

The ongoing cost is honest and worth stating: **the graph is a thing to keep
true.** A stale intent graph is worse than none, because it would be checked and
believed. The `source`-must-resolve rule is what makes staleness loud rather than
quiet — a node whose file moves fails CI on the next run.

---

## Impact prediction

**resource_impact: 6** — it changes no behavior and gates no merge on its own. It
changes what is *findable*, which is upstream of most of the governance cost in
this repo.

**Positive:**
- Contradictions between governance surfaces become data, found by a check rather
  than by a reader.
- Orphan work is visible: an objective with no principle grounding it is either
  ungrounded or the grounding was never written down.
- Cited-but-absent machinery surfaces (the falsifier-lint row).
- Session-boundary durability: reconstructing "how this all fits together" becomes
  reading one graph instead of re-deriving from five prose documents.

**Risks:**
- **The graph drifts and is trusted anyway.** The sharpest risk. Mitigated by
  E3 (source must resolve) and `render --check`, neither of which catches a node
  whose *statement* has gone stale while its path still exists.
- **Premature formalization.** Typing relations that are genuinely still fluid
  makes them harder to change than prose. Mitigated by keeping the vocabulary
  small (6 node types, 6 edge types) and by `status: PROPOSED` on nodes that are
  not settled.
- **It becomes a vision-statement artifact** — the failure mode of every
  strategy-map exercise. The `source`-must-resolve rule is the specific defense:
  a node that names no file in the tree is an error, not an aspiration.

---

## Falsifier

This candidate is FALSE if:

1. A governance contradiction of the class this issue found — two live artifacts
   in the tree giving conflicting answers on the same control question — exists
   while `python3 tools/intent_graph_v1_0.py check` reports zero errors and the
   contradiction is not present as a `conflicts_with` row.
2. `INTENT_GRAPH.yaml` contains a node whose `source` does not resolve in the
   tree and `check` exits 0.
3. Answering "what grounds this objective, and what measures it" still requires
   reading more than one file after ratification.
4. Over the next N ratified candidates (Z2 sets N), no `conflicts_with` row is
   filed by Z1 in-session while contradictions continue to be found by human
   reading — i.e. obligation 1 is not actually being followed, and the graph is
   documentation rather than practice.

Condition 4 is the one that matters. The first three test the tool; the fourth
tests whether the protocol changed anything about how we work. A graph that is
correct and unused has failed.

---

## Evidence

- `INTENT_GRAPH.yaml`, `tools/intent_graph_v1_0.py`, `INTENT_GRAPH.md` (this diff)
- `.z1-control/render.py` — the in-repo precedent, including its own statement of
  the problem it solved
- `TEMPORAL_CONTROL_AUDIT.md` § Second pass § Pattern — why the defect recurred
  after the fix was published
- `CLAUDE.md` § CI/CD Gates — names `falsifier_lint`; absent from
  `.github/workflows/` (52 workflows present; none matching)
- `FRAMEWORK_MAPPING.md` § 1 Graph Engineering — this repo already holds graph
  engineering as a governance concept; nothing had yet applied it to the intent
  layer

---

## What Z2 is being asked to decide

1. **Ratify or reject** the graph as the shared intent substrate.
2. **Correct the node statements.** Z1 seeded them from SEED.md,
   PRINCIPLES_SEED_V1_0.md, OPS_ROADMAP_V1.2.md and CLAUDE.md. They are Z1's
   reading of Night's meaning and should be read as a proposal about what Night
   meant, not a record of it. The vision and mission statements especially.
3. **Accept or amend the three obligations** in the collaboration protocol —
   particularly obligation 1, which is a commitment about Z1's behavior in
   session.
4. **Rule on `G-FALSIFIER-LINT`:** does the check exist under another name, or is
   `P-FALSIFIER` enforced by convention?
5. **Set N** for falsifier condition 4.
6. **Decide whether `check` becomes merge-blocking, and whether a workflow runs
   it at all.** Nothing in `.github/workflows/` currently runs `check` or
   `render --check`, so `INTENT_GRAPH.md` can drift from `INTENT_GRAPH.yaml`
   unnoticed — the exact failure this candidate exists to prevent, and a fair
   criticism of the diff as it stands.

   Z1 has **not** added that workflow, and the reason is this question. A gate
   enforcing the graph before Z2 has ratified the graph would be Z1 enforcing its
   own unreviewed reading of Night's intent — the thing point 3 above says this
   must not do. Z1's proposal, ready to land on ratification:

   - `render --check` **blocking** — purely mechanical ("did you regenerate the
     page"), same contract as `.z1-control/render.py --check` and
     `.tool-control/render.py --check`, which are already gated.
   - `check` **advisory** — its errors are judgements about grounding and
     contradiction, and those are Z2's to correct first.

   If Z2 prefers both blocking, or both advisory, that is a one-line difference
   in the workflow.

```yaml
z2_decision:
  status: awaiting_ratification
  ratified_at: null
  ratification_hash: null
  z2_notes: ""
```
