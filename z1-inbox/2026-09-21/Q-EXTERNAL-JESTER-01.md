# Q-EXTERNAL-JESTER-01 — the ratified Jester's independence rule is the wrong rule, and we can now measure that

**Type:** IC · **Author:** Z1 (Claude) · **Status:** awaiting_z2
**Amends:** `Q-JESTER-CHECK-01` (ratified by Night, 2026-09-08, hash
`h-cand-batch-ratified-20260908`) — design rule 2, *substrate independence*.
**Bears on:** `Q-WITCH-CASCADE-01` (ratified same batch), H-CAND-CASCADE-01.
**Origin:** Night, 2026-09-21 — *"having Copilot is still having a contaminated
agent providing red team, because Copilot lives inside the vault."*

---

## Correction owed before the finding

Z1 drafted this candidate as a new proposal for an external adversarial witness,
and it was not new. `z1-inbox/2026-09-07/JESTER_EXTERNAL_CHECK_BLOCK.md` was
ratified two weeks ago and already contains the role, a Nemeth-grounded
mitigation against ceremonial dissent, six design rules, a falsifier and five
GAPs. Proposing it again would have been the third instance this session of a
claim written about a source without being executed against it.

The finding below is what survives after reading the ratified block: not a new
role, but **a measurement that falsifies one of its ratified design rules.**

## The ratified rule

From `JESTER_EXTERNAL_CHECK_BLOCK.md` §2, design rule 2:

> **Substrate independence.** Critic ≠ author substrate. Already practice
> (Copilot/Grok/ChatGPT); make it a CI check on adv_eval:
> `critic_substrate != author_substrate` or NO_GATE.

That rule is satisfied today. Copilot reviews Claude's pull requests; the
substrates differ; the check would pass.

## What the measurement shows

`tools/graph_convergence_v1_0.py`, run against Copilot's `EVIDENCE_GRAPH.json`
and Claude's `INTENT_GRAPH.yaml` (`GRAPH_CONVERGENCE.md`):

```
6 aligned pairs · 0 graded INDEPENDENT · total corroboration weight 0.0
```

Three pairs share a source, two have unrecorded provenance, one is a declared
false friend. Two agents on different substrates, kept from reading each other's
output, produced **zero** independent agreement — because they read the same
tree.

So substrate independence and source independence are different properties, and
the ratified rule tests the one that does not matter. A critic on a different
substrate reading the same repository is a second reading. It will find what a
careful second reading finds — which is real and not nothing, and is exactly what
Copilot has delivered across three review rounds this session — and it cannot
corroborate, because corroboration requires a source the author did not have.

There is a second overlap that no CI check can reach: Copilot and Claude are both
language models with overlapping training corpora. A shared prior has no path in
this repository, so it cannot be declared as a source and cannot be graded. It is
named here rather than omitted because it means **no rule applied to an in-vault
agent produces disjointness**, and because the ratified block's own evidence tier
discipline requires unverifiable confounds to be labelled rather than dropped.

## Why this is more serious than a rule correction

`Q-WITCH-CASCADE-01`, ratified in the same batch, registers H-CAND-CASCADE-01:

> Feedback read + staged procedure + blame, *without* an external check, is
> self-amplifying, not self-regulating. … **the external check is what keeps the
> other three from running away.** The jester is not decorative.

This project has the feedback read (the ledgers and audits), the staged procedure
(the ratification path), and blame attribution (the findings registry). Under its
own ratified hypothesis, the external check is the component that stops that
combination amplifying. The measurement above says the external check we believe
we have is not external.

That is not an argument that anything has gone wrong. It is an argument that the
guard registered as load-bearing has not been tested for the property it is
load-bearing on.

## Proposed amendment to design rule 2

Replace substrate independence with source disjointness, keeping substrate
independence as a necessary-but-insufficient sub-clause:

> **2. Source disjointness.** Critic ≠ author substrate **and** the critic's
> declared source set is disjoint from the author's under
> `tools/graph_convergence_v1_0.py`. A critic reading the repository is a second
> reading, not a check. Gate: an adversarial finding that grades SHARED_SOURCE,
> UNSOURCED or CONTAMINATED does not count toward catch-rate.

The single load-bearing constraint on an external Jester follows from that: **it
reads only what the project publishes, never the tree.** Dataset, papers, site,
public claims — which is also what an actual hostile reviewer has, so the
restriction buys realism as well as disjointness. Its brief:

1. Take a published HumanAIOS claim.
2. Find its stated falsifier. If there is none, that is the finding.
3. Attempt to trip it using public artifacts only.
4. Publish the attempt and its outcome, **including failed attempts.**

Step 4 is not decoration and the ratified block already implies it: rule 3
("the critic's standing is its catch-rate, never its agreement rate") is a
selection rule, and a critic publishing only successes is selecting on outcome —
the same failure `audits/ROI_RUBRICS_S-092126.md` Rubric B prices for HA-000.

## How this composes with the ratified ritual-dissent detector

Design rule 4 already measures whether dissent is authentic: novelty ratio
(objections not present in the author's text) below 0.30 over five reviews fires
`DRIFT:RITUAL`. The convergence grader measures something different and the two
should both run:

| | measures | fails when |
|---|---|---|
| Novelty ratio (ratified, rule 4) | did the critic **say** something the author had not? | the critic bolsters the author's position |
| Corroboration weight (new) | **could** the critic have known it any other way? | the critic and author read one source |

A critic can score high novelty and zero corroboration weight at the same time —
which is precisely Copilot's position, and precisely why its findings have been
valuable while its agreement has been worthless. Neither instrument alone would
have shown that.

## What this candidate does NOT propose

- **Not a new role.** The Jester is ratified. This amends how its independence is
  tested.
- **Not reopening the Witch.** `Q-WITCH-CASCADE-01` is ratified as *hypotheses*
  with falsifiers, which is a different thing from a Witch with authority to act
  on the system. Only the latter would need reconciling with the Z2 serial gate
  before it exists, and nothing here proposes it. Z1 notes only that H-CAND-CASCADE-01
  makes the order matter: the external check should be shown working before
  anything else in that family is given power through it.
- **Not engaging anyone**, not adding site telemetry, and not writing Jester
  findings itself. Z1 writing the adversary's findings is the contamination this
  candidate exists to remove, performed by the agent least able to notice it.

## The site as telemetry prototype

Night proposed the site as a prototype for human collaboration with multiple AI
agents. It fits this amendment better than a separate build, because the site is
already the boundary between the vault and the public — it is the surface a
source-disjoint Jester is *allowed* to read. Two telemetry items follow from the
design and nothing else does:

- **Which published claim a visitor engaged with**, so the Jester's target set is
  driven by what is read rather than by what we think matters.
- **The check-in record** — pseudonymous, per `audits/ROI_RUBRICS_S-092126.md`
  Rubric A: no recovery for EPHEMERAL and QUALIFICATION_PROOF, and no behavioural
  re-identification, which that rubric shows is a biometric in the costume of
  privacy.

Anything beyond these two is collecting for its own sake.

## What Z2 is asked to decide

1. **Amend design rule 2** as above. It edits a ratified block, so it is a Z2 act
   and Z1 has written the replacement text rather than applying it.
2. **Whether the gate clause binds**: does a SHARED_SOURCE finding stop counting
   toward catch-rate, or is that advisory? Binding it would mean Copilot's
   catch-rate falls to zero overnight while its findings stay valuable, which is
   a defensible outcome but a confusing one, and Z1 does not recommend guessing.
3. **Who plays the external Jester.** A person, a differently-hosted model with
   no repository access, or a standing open invitation. Z1 notes a
   differently-hosted model still shares the training-corpus prior; a human
   external reviewer is the only option that clears it, and costs accordingly.
4. **Whether failed attacks are published.** Z1 recommends yes; it is load-bearing.

## Falsifier

FALSE if an in-vault agent can produce an alignment row grading INDEPENDENT under
`tools/graph_convergence_v1_0.py` — which would show the vault is not the
constraint and substrate independence was sufficient after all. Mechanically
checkable: declare the row, run `grade`.

Also FALSE if the external Jester's findings, once graded, are *also* weight 0 —
meaning the published artifacts and the tree are not disjoint and the externality
is nominal. Z1 considers this the most likely embarrassing outcome and states it
in advance for that reason.

Also FALSE if `JESTER_EXTERNAL_CHECK_BLOCK.md` design rule 2 already carries a
source-disjointness clause Z1 failed to find. Checkable: the block's §2 is nine
lines and rule 2 is quoted above in full.

## Evidence

- `z1-inbox/2026-09-07/JESTER_EXTERNAL_CHECK_BLOCK.md` §2 rule 2 — the rule amended
- `z1-inbox/2026-09-07/WITCH_SPELL_CASCADE_BLOCK.md` §2 — H-CAND-CASCADE-01
- `z1-inbox/2026-09-08/Z2_RULINGS_2026-09-08.md` — the ratification of both
- `GRAPH_CONVERGENCE.md` — 6 pairs, 0 INDEPENDENT, total weight 0.0
- `GRAPH_ALIGNMENT.yaml` — the source sets and access grades behind that number
- `AGENT_GRAPH_COMPARISON.md`, "Correction, 2026-09-21" — the independence claim retracted
- `audits/ROI_RUBRICS_S-092126.md` — Rubrics A and B, which this depends on

```yaml
z2_decision: {status: awaiting_ratification, ratified_at: null, ratification_hash: null, z2_notes: ""}
```
