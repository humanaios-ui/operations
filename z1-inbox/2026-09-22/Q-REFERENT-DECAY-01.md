# Q-REFERENT-DECAY-01 — five artifacts whose link to their referent died while the artifact stayed alive

**Type:** F (finding) · **Author:** Z1 (Claude) · **Status:** awaiting_z2
**Authorised by:** Night, 2026-09-22 — *"File the remaining two candidates."*
**Origin:** Night, 2026-09-22 — *"What does [these three things] teach us and what's our options?"*
**Supersedes nothing.** Reframes `Q-GRAPH-CONVERGENCE-01`, `Q-DEFERRAL-RULE-01`,
`Q-P19-GATE-INERT-01` and `Q-CORPUS-STATS-RECONCILE-01` as one class.

---

## The finding

Five instances, all from session S-092126–S-092226, all the same shape:

| # | The artifact | What it still asserts | The referent that moved | How it was caught |
|---|---|---|---|---|
| 1 | `A11` in `tools/graph_convergence_v1_0.py` | distinct `ordering` protects the grade | `A13` removed the dependency | reading the diff of a fix |
| 2 | Z1's claim that molt closure was "already solved" | the pattern is available to borrow | `MOLT_STATE.md:125` says PROPOSED, awaiting_z2 | Copilot review, PR #447 |
| 3 | `0.8632` ×38 tree-wide | the corpus mean LI | the corpus stopped reproducing it 2026-07-02 | a sweep, months late |
| 4 | `Check principles (P19)` | this code was inspected | the file list never split, so no file opened | accident — one PR had the rare shape |
| 5 | the stop hook's "1 unpushed commit" | work is unshipped | the PR squash-merged; the tree was identical | trying to push |

A sixth, from the same class and the same week, is worth listing separately
because the author is not this repository: `.z1-control/validate.py` emits
"N days past the 2d window" for 57 candidates. Night's ruling — *"deadlines are
of no concern with temporal dissolution in effect"* — makes that output
authoritative over nothing. It is not wrong; it has no referent.

## What unites them

Every one is an assertion that outlived the thing it was about. Not one was
false when written.

The repository has mechanisms that check **assertions** (does it parse, is it
present, does it lint) and mechanisms that check **sources** (E3: does the path
resolve). It has nothing that checks **the edge between them**.

That diagnosis is not new here. It is already written down twice — in
`AGENT_GRAPH_COMPARISON.md`, and as an `ONTOLOGY_DIVERGENCE` row in
`GRAPH_ALIGNMENT.yaml`:

> INTENT grades maturity on the **node**. EVIDENCE grades it on the **edge**.
> The edge is the better locus, and the reason is this session's own record:
> every Copilot finding across three review rounds was a statement about a
> source written without executing against the source.

Z1 wrote *"this is the strongest argument for adopting edge-state grading"* and
then produced four more instances of the gap, one of them inside the document
arguing against it.

## The asymmetry that makes #4 worst

Instances 1, 2, 3 and 5 are stale **assertions**. Instance 4 is a stale
**checker**, and it is categorically worse:

> Prose that is wrong is **neutral** evidence — a reader may or may not believe
> it. A green check is **positive** evidence. It actively tells every reader the
> property was checked. An inert gate does not fail to inform; it misinforms, on
> every pull request, in the direction of reassurance.

## What Z2 is asked to decide

Z1 recommends this order and does not recommend doing all of it.

### E — lint governance-status claims *(recommended first)*

All of instances 1, 2 and 3 involve a **governance-status fact**: is this
candidate ratified, is this rule in force, is this figure current. A check that
finds any sentence asserting a Q-ID's status and compares it to
`z1-inbox/INDEX.yaml` would have caught instance 2 mechanically, before the
commit. Narrow, cheap, and it closes the class with the worst blast radius —
instance 2 put a false status claim into a governance candidate.

### F — audit the gates for liveness *(recommended second)*

> **A gate that has never failed is either protecting a property nobody
> violates, or not running.** Those are distinguishable from CI history, and the
> observation that proves a gate is alive is a failure.

This is `Q-DEFERRAL-RULE-01`'s leg 3 pointed at our own instruments: an
assertion needs an ending observation, and *"this gate works"* is an assertion.
It is the only option that finds things **already** broken and silent, which is
the category all five instances fall into. Instance 4 was found by accident; F
is what finding it on purpose looks like.

Scope note, from instance 4's review: the audit should also ask **which
workflows re-derive logic another already has**. `z2_ratification_gate.yml`
had solved push-range handling, with a comment giving the reasoning, and
`agent-principle-compliance-check.yml` re-derived it badly.

### D — generate the facts that get restated *(recommended third)*

Already proven three times in this tree. `INTENT_GRAPH.md`, `TOOLS_MANIFEST.md`
and `Z1_INBOX_INDEX.md` are generated and gated by `--check`, and none has ever
drifted. The ratified TRL direction points the same way: `SEED.md` should carry
a **derivation reference**, not a copied constant. The open question is scope —
which facts get promoted — not whether the mechanism works.

Limit: structured facts only. Useless against an argumentative claim like
instance 2.

### C — edge-state grading *(recommended as standing discipline)*

Adopt `CLAIMED → SPECIFIED → IMPLEMENTED → TESTED → OBSERVED` on claim→source
links. The only option that touches argumentative prose. A discipline rather
than an automation — the author still grades their own edge, so it is gameable —
but *"already solved"* written as a `CLAIMED` edge is visibly a promise, where
in prose it reads as fact.

### B — source content hashing *(recommended to stay deferred)*

Record each source's hash at claim time, report drift. Would catch instance 3.
Deferred twice already for a real reason: file-level hashing invalidates every
claim citing `CLAUDE.md` on any edit to it, producing noise nobody clears —
the 50.8% dead-suppression failure from `audits/DEFERRAL_RULE_RESEARCH_S-092126.md`
in a new costume. Needs section-level anchoring first.

**Under `Q-DEFERRAL-RULE-01`'s proposed leg 3, this deferral now carries an
ending observation: section-level anchoring exists.** The previous two deferrals
of B did not, which is leg 3 applied to itself and the reason it is recommended.

## What Z1 is not doing

Not building E, F, D, C or B. Not recalibrating any rule. Not treating the
ordering above as a decision. Night asked for the candidates filed; filing is
the Z1 act.

## Falsifier

FALSE if the five instances are not one class — specifically, if a mechanism
that would have caught instance 2 (a status claim) would have had no purchase on
instance 4 (an inert gate) and vice versa, such that "referent decay" is a
label over unrelated bugs rather than a shared structure.

Z1 judges this **partly true and says so**: option E catches 1–3 and not 4;
option F catches 4 and not 2. No single option catches all five. The claim is
that they share a *diagnosis* — no check on the assertion-to-referent edge — not
that they share a *fix*. If Z2 reads that as the class being too loose to act
on, that is a defensible ruling and this candidate should be split.

Also FALSE if any instance is misreported. Each is checkable:
`grep -n "ordering" tools/graph_convergence_v1_0.py` (1); `MOLT_STATE.md:125`
plus the index status of `Q-MOLT-TEMPORAL-PURITY-01` (2);
`grep -rc "0.8632"` against `audits/CORPUS_RECONCILIATION_S-070226.md` (3);
running the P19 bot on a newline-joined two-file list (4); `git diff` between
the branch tip and `main` at the moment the hook fired (5).

## Evidence

- `z1-inbox/2026-09-22/Q-P19-GATE-INERT-01.md` — instance 4, with its measurements
- `z1-inbox/2026-09-21/Q-GRAPH-CONVERGENCE-01.md` — the edge/node divergence
- `z1-inbox/2026-09-21/Q-DEFERRAL-RULE-01.md` — leg 3, the ending-observation form
- `z1-inbox/2026-09-21/Q-CORPUS-STATS-RECONCILE-01.md` — instance 3
- `z1-inbox/2026-09-22/Q-A11-ORDERING-INERT-01.md` — instance 1, filed separately
- `AGENT_GRAPH_COMPARISON.md` · `GRAPH_ALIGNMENT.yaml` — the diagnosis, written before the instances
- `audits/DEFERRAL_RULE_RESEARCH_S-092126.md` — why option B stays deferred

```yaml
z2_decision: {status: awaiting_ratification, ratified_at: null, ratification_hash: null, z2_notes: ""}
```
