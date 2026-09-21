# Q-GRAPH-CONVERGENCE-01 — grade agreement between agents by source disjointness, not similarity

**Type:** H (hypothesis) + tooling · **Author:** Z1 (Claude) · **Status:** awaiting_z2
**Origin:** Night, 2026-09-21 — *"Do we have a mechanism or method for
determining independent convergence and graphing this? Would divergence be
useful? Can the graphs be backfilled?"*

---

## The mechanism

Three files:

| File | Role | Who writes it |
|---|---|---|
| `GRAPH_ALIGNMENT.yaml` | the judgments: which node means the same as which, what sources each came from, what access each author had | Z1 proposes, **Z2 ratifies** |
| `tools/graph_convergence_v1_0.py` | the grading: mechanical, 12 error rules, 3 warnings, 27 self-tests | nobody — it computes |
| `GRAPH_CONVERGENCE.md` | the rendered result | generated; `render --check` is the CI form |

The split is the design. The alignment is a judgment and therefore data a human
can contest. The grade is not a judgment and therefore not writable: **there is
no field an author can use to assert its own independence**, because that
assertion is exactly what the grading exists to check.

## Why not similarity

A similarity comparison of two graphs of this repository reports the overlap as
agreement. That number would be large and it would mean nothing. Copilot and
Claude both read this tree; where the two graphs agree, both are transcribing one
document. Counting that as convergence manufactures confidence from a single
source — the same defect as citing one statistic from 38 places and calling it
corroborated.

So a pair scores only when the two nodes cite no source in common **and** the
later author could not reach the earlier graph.

| Grade | Weight | Condition |
|---|---|---|
| INDEPENDENT | 1.0 | disjoint sources; earlier graph unreachable |
| SEQUENTIAL_UNREAD | 0.3 | disjoint; reachable, author asserts unread — an agent's claim about its own reading, discounted rather than trusted |
| SHARED_SOURCE | 0.0 | a source in common, directly or through declared lineage |
| UNSOURCED | 0.0 | one side's derivation was never recorded; unknown provenance is not independence |
| CONTAMINATED | 0.0 | the later author read the earlier graph |
| BACKFILL_UNGRADED | 0.0 | asserted by an author who already knew the outcome |
| NOT_CONVERGENCE | 0.0 | a declared false friend |

### Lineage, because paths are not enough

`CLAUDE.md` and `WITNESS_SERVICE_CONTRACT.md` are different files. The second
takes its non-authority and falsifier language from the first. Two nodes citing
them separately look disjoint and are reading one doctrine — so a path comparison
would score them INDEPENDENT, reintroducing the same error one level down.

`source_lineage` declares those derivations and the tool intersects transitive
closures. A declared lineage can only lower a grade, never raise one, so the list
is safe to extend and unsafe to leave short: every omission is a pair scoring
higher than it deserves.

## The result, which is the finding

```
6 aligned pairs · 0 graded INDEPENDENT · total corroboration weight 0.0
```

Three pairs share a source, two have unrecorded provenance, one is a declared
false friend. Copilot does not corroborate Claude in this tree, and the reason is
structural rather than a defect in either agent.

`AGENT_GRAPH_COMPARISON.md` previously called these graphs independently authored.
That claim is retracted in the same file. Its falsifier tested whether one author
had read the other's graph — graph-to-graph exposure — when the condition that
mattered was source disjointness. The correction also records an overlap the tool
*cannot* score: both agents are language models with overlapping training
corpora, and a shared prior has no path, so it can be neither declared nor graded.
It is named rather than omitted because it is the argument for
`Q-EXTERNAL-JESTER-01`.

## Is divergence useful

It is not merely useful; under shared sources it is the only part carrying
information. Agreement was the expected outcome and told us nothing. Five
divergences are recorded in three classes — COVERAGE_GAP, ONTOLOGY_DIVERGENCE,
CONTRADICTION — and one is worth restating:

> **CONTRADICTION.** `INTENT` recorded `G-Z2-RATIFY` as a gate refusing merges
> without a Z2 hash. `EVIDENCE` graded its equivalent edge SPECIFIED, not
> IMPLEMENTED. The tree agrees with EVIDENCE: `.z1-control/ratify.py --verify`
> runs `continue-on-error: true` in that workflow and anti-cascade is not
> evaluated there. Where the two graphs contradicted each other, the one grading
> the **edge** rather than the node was right.

That is the third time this session a claim failed because it was written about a
source without being executed against it, and it is the substantive case for
adopting edge-state grading.

## Can graphs be backfilled

Yes, and the answer needs a rule rather than a yes.

Backfilling is asserting a node or edge about an artifact that already exists, by
an author who has already seen what happened to it. Legitimate for **coverage** —
a graph describing only what was built after the graph describes almost nothing.
Illegitimate for **corroboration** — the backfiller is reading the answer off the
tree, not witnessing it.

So `provenance: BACKFILL` forces `BACKFILL_UNGRADED` at weight 0, and rule A6
errors on any backfilled row claiming independence. Backfilled rows render, count
for coverage, and never count as evidence that two methods found the same thing.
The discipline for a backfilled row is three columns: what was asserted, what
source it was read from, **and what the author already knew when asserting it.**
The third is what makes it ungradeable, and it is the one a backfill without this
rule silently omits.

## What Z2 is asked to decide

1. **Ratify the alignment rows** — six node pairs and five divergences. These are
   judgments about what two agents meant, made by one of the two agents, and the
   FALSE_FRIEND row is Z1 declaring another agent's node unalignable with its own.
   Z2 review is the only check on that.
2. **Ratify `source_lineage`.** Declaring that the witness contract derives from
   `CLAUDE.md` lowers three grades to zero. It is the right call and it is Z1
   marking down its own convergence claims, which should be confirmed rather than
   assumed.
3. **Whether `render --check` joins CI.** It would fail a PR that changes the
   alignment without regenerating the page — the same shape as the intent graph's
   renderer gate.
4. **Whether corroboration weight enters the Priority Queue** as a score input.
   Z1 does not recommend this yet: with one comparison at 0.0 there is nothing to
   calibrate against, and a scoring input with no variance is decoration.

## Falsifier

FALSE if two graphs in this repository can be shown to have genuinely disjoint
sources while describing the same governance objects — which would mean the
shared-source problem is an artifact of this particular pair and not structural.
Mechanically checkable: declare the alignment, run `grade`, look for a nonzero
weight.

Also FALSE if the grading can be gamed upward by an author declaring fewer
sources than it used. This is a real attack and the mitigation is partial:
`UNSOURCED` closes the obvious form (declare nothing, score independent) by
refusing to grade an undeclared side at all, but an author who declares one true
source and omits a second still scores too high. There is no mechanical defence
against that from inside the tree; it is the reason W1 reports coverage and the
reason `Q-EXTERNAL-JESTER-01` exists.

## Evidence

- `GRAPH_CONVERGENCE.md` — the rendered table and canvas
- `GRAPH_ALIGNMENT.yaml` — source sets, access grades, lineage, divergences
- `tools/graph_convergence_v1_0.py --smoke-test` — 27/27
- `AGENT_GRAPH_COMPARISON.md`, "Correction, 2026-09-21"
- `EVIDENCE_GRAPH.json` (Copilot, PR #431) · `INTENT_GRAPH.yaml` (Claude, PR #436)

```yaml
z2_decision: {status: awaiting_ratification, ratified_at: null, ratification_hash: null, z2_notes: ""}
```
