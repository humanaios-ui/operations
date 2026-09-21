# Q-EXTERNAL-JESTER-01 — an adversarial witness outside the vault, and a way to tell whether it is really outside

**Type:** H (hypothesis) · **Author:** Z1 (Claude) · **Status:** awaiting_z2
**Origin:** Night, 2026-09-21 — *"having Copilot is still having a contaminated
agent providing red team, because Copilot lives inside the vault. Is there a way
to mitigate this? We have the Witness navigator proposal — could we have a
similar but external adversarial witness? Perhaps the Witness and the Jester? Use
this as a prototype, then introduce the Witch."*

---

## The finding that makes this necessary

Night's objection was an intuition. It is now a measurement.

`tools/graph_convergence_v1_0.py`, run against Copilot's `EVIDENCE_GRAPH.json` and
Claude's `INTENT_GRAPH.yaml`:

```
6 aligned pairs · 0 graded INDEPENDENT · total corroboration weight 0.0
```

Three pairs share a source, two have unrecorded provenance, one is a declared
false friend. `AGENT_GRAPH_COMPARISON.md` previously called these two graphs
independently authored; that claim is corrected in the same file. The two agents
were kept from reading each other's output and it did not matter, because they
read the same tree.

There is a second overlap the tool cannot even score: both agents are language
models with overlapping training corpora. A shared prior has no path in this
repository, so it cannot be declared as a source and cannot be graded. It is the
decisive fact, because it means **no amount of procedural care applied to an
in-vault agent produces disjointness.** Copilot is not a poor red team. It is a
second reading, and a second reading is structurally incapable of being a
witness.

## What the Witness already is, and what it is not

`WITNESS_SERVICE_CONTRACT.md` defines a Witness that "can explain, request, and
route" and "cannot self-ratify, self-authorize, widen consent, or convert
participation metadata into effective governance authority." That is a
*custodial* role: it observes and it is constrained from acting.

It has no adversary. Nothing in the contract is charged with trying to make the
Witness's account false. A custodian with no adversary records whatever it is
given, faithfully, including a false account faithfully recorded.

## Proposal: the Jester

A second external role, defined by what it may attack rather than what it may do.

| | Witness (exists) | **Jester (proposed)** |
|---|---|---|
| Posture | custodial — records | adversarial — attempts to falsify the record |
| Position | inside, constrained | **outside the vault** |
| Reads | the tree | **only published outputs**, never the tree |
| Authority | none; routes | none; publishes findings |
| Success condition | the record is complete | **a published claim fails against its own falsifier** |
| Relation to Z2 | supplies the record | supplies contested findings; Z2 still rules |

The single load-bearing constraint is the third row. **A Jester that reads the
repository becomes Copilot** — another reader of one source, corroboration weight
zero, and the whole exercise repeats. The Jester's value comes entirely from
having a different source set, which means it must work from what the project
publishes: the dataset, the papers, the site, the public claims. That is also
exactly what an actual hostile reviewer has, which is the point.

The Jester's brief is narrow enough to be checkable:

1. Take a published HumanAIOS claim.
2. Find its stated falsifier. If there is none, that is the finding.
3. Attempt to trip it using only public artifacts.
4. Publish the attempt and its outcome, including failed attempts.

Step 4 is not decoration. A Jester that publishes only successes is selecting on
outcome, which is the failure `audits/ROI_RUBRICS_S-092126.md` Rubric B prices at
length. Its own record has to be complete or it inherits the defect it exists to
find.

## How we will know whether the Jester is actually external

This is the part that distinguishes the proposal from hiring a second opinion,
and it is already built.

Every Jester finding enters `GRAPH_ALIGNMENT.yaml` as an alignment row with a
declared source set. `tools/graph_convergence_v1_0.py` grades it. The grading
cannot be talked around: a Jester whose sources intersect ours grades
SHARED_SOURCE at weight 0 no matter how adversarial its prose, and a Jester
working from public artifacts alone grades INDEPENDENT at 1.0.

So the hypothesis is measurable in the instrument's own terms:

> **H:** an external Jester produces alignment rows that grade INDEPENDENT.
> Corroboration weight rises above 0.0 for the first time in this repository.

If it does not — if the Jester's findings keep grading SHARED_SOURCE — then
either it is reading the tree, or the "public artifacts" and the tree are not as
disjoint as assumed. Both are findings, and both are visible without anyone
having to be trusted.

## Sequencing: Witness → Jester → Witch

Night proposed the Witch as a later stage. Z1 recommends holding it and states
why, because the reason is a constraint rather than a preference.

Witness and Jester are both **non-authoritative**: one records, one attacks, and
neither can change what the tree says. That is what makes them safe to add
without touching the Z2 serial gate. The Witch, as discussed, implies a
*transforming* role — something that acts on the system rather than observing it.
Any such role has to be reconciled with the serial gate before it exists, not
after, or it becomes a second authority by accident. `Q-Z2-DUAL-AUTHORITY-GOVERNANCE-01`
took a full ratification to formalise two Z2 identities; a third acting role is
at least that size.

Recommended order, with a gate between each:
1. **Witness** — exists. No change proposed here.
2. **Jester** — this candidate. Non-authoritative, external, measurable.
3. **Witch** — only after the Jester has produced at least one INDEPENDENT-graded
   finding, which proves the external channel works before anything is given
   power through it.

## The site as telemetry prototype

Night proposed the site as a prototype for human collaboration with multiple AI
agents, and it fits this proposal better than a separate build would.

The site is already the boundary between the vault and the public. It is where
published claims appear, which makes it exactly the surface a Jester is allowed
to read, and it is where a human interacts with the system without a repository
checkout. So the telemetry it should carry is not general analytics but the two
things this design needs:

- **Which published claim a visitor engaged with**, so the Jester's target set is
  driven by what is actually being read rather than by what we think matters.
- **The check-in record** — pseudonymous, per `audits/ROI_RUBRICS_S-092126.md`
  Rubric A: no recovery for EPHEMERAL and QUALIFICATION_PROOF, and no behavioural
  re-identification, which that rubric shows is a biometric wearing the costume of
  privacy.

A prototype that collects more than this is collecting for its own sake, and the
project has a standing objection to instruments that measure what is easy rather
than what the claim needs.

## What Z2 is asked to decide

1. **Whether the Jester role is created at all**, given it will produce findings
   against published work that the project then has to answer in public.
2. **Who or what plays it.** A person, a differently-hosted model with no
   repository access, or a standing open invitation. Z1 has no basis to choose and
   notes that a differently-hosted model still shares the training-corpus prior
   the tool cannot see — a human external reviewer is the only option that clears
   it, and costs correspondingly more.
3. **Whether failed attacks are published.** Z1 recommends yes, and the
   recommendation is load-bearing rather than decorative.
4. **The Witch's deferral**, per the sequencing above.

## What Z1 is not doing

Not engaging anyone, not building the role, not adding telemetry to the site, and
not writing Jester findings itself. Z1 writing the adversary's findings is the
contamination this candidate exists to remove, performed by the one agent least
able to notice it.

## Falsifier

FALSE if an in-vault agent can produce an alignment row grading INDEPENDENT under
`tools/graph_convergence_v1_0.py` — which would show the vault is not the
constraint and the Jester's externality is unnecessary. Mechanically checkable:
declare the row, run `grade`.

Also FALSE if the external Jester's findings, once graded, are *also* weight 0 —
which would mean the published artifacts and the tree are not disjoint, and the
externality is nominal. This is the outcome Z1 considers most likely to be
embarrassing and it is stated in advance for that reason.

## Evidence

- `GRAPH_CONVERGENCE.md` — 6 pairs, 0 INDEPENDENT, total weight 0.0
- `GRAPH_ALIGNMENT.yaml` — the source sets and access grades behind that number
- `AGENT_GRAPH_COMPARISON.md`, "Correction, 2026-09-21" — the overstatement retracted
- `WITNESS_SERVICE_CONTRACT.md` line 32 — the Witness's custodial constraint
- `audits/ROI_RUBRICS_S-092126.md` — Rubric A (pseudonymous check-in), Rubric B
  (external administration), both of which this candidate depends on

```yaml
z2_decision: {status: awaiting_ratification, ratified_at: null, ratification_hash: null, z2_notes: ""}
```
