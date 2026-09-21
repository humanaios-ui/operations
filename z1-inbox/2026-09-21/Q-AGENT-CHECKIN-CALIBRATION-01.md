# Q-AGENT-CHECKIN-CALIBRATION-01 — calibration at check-in, and what two agents' graphs say about how to review

**Type:** IC · **Author:** Z1 (Claude) · **Status:** awaiting_z2
**Builds on:** PR #431 (Copilot, merged) — `PARTICIPATION_CONTRACT_V0_1.schema.json`, `EVIDENCE_GRAPH.json`
**Analysis:** `AGENT_GRAPH_COMPARISON.md`
**Requested by:** Night, 2026-09-21

---

## 1. The experiment already ran

Night proposed asking Copilot to build a graph of the repository and comparing it
to ours. That comparison is available without staging anything: **PR #431 was
authored by `copilot-swe-agent` and merged `EVIDENCE_GRAPH.json` — a typed graph of
this repository — hours before `INTENT_GRAPH.yaml` was written in PR #436.**

Two agents, same tree, no coordination, both reached for a typed graph with
claims, controls, tests and falsifiers as first-class nodes.

Staging a fresh run now would be *worse* evidence: Z1 has read Copilot's ontology
and cannot un-read it. The natural pair is the only uncontaminated sample this
repository will get, which is why `AGENT_GRAPH_COMPARISON.md` was written before
any merge of the two designs.

## 2. The result that matters

Copilot grades the **edge** — `CLAIMED → SPECIFIED → IMPLEMENTED → TESTED →
OBSERVED`. Claude grades the **node** — `LIVE / PROPOSED / CONFLICTED /
CITED_NOT_IMPLEMENTED`.

Edge-state answers *how well established is this relationship*. Node-status
structurally cannot.

The test case is already on record. In PR #436 the node `G-Z2-RATIFY` claimed its
workflow "refuses a merge without a Z2 hash, a falsifier, and anti-cascade
compliance." It does not — the signature step is `continue-on-error: true` and
anti-cascade is not evaluated there at all. Claude's validator passed it (E3 only
checks that the `source` path resolves, and it does). A human reviewer caught it.

Under Copilot's ontology that edge carries `state: CLAIMED`, and the gap is
**data**. An ontology built by one agent would have mechanically caught a defect
the other committed and shipped.

**Z1 recommends adopting edge-state grading into `INTENT_GRAPH.yaml` v0.2**, along
with Copilot's `failure` / `defeats_if_unmitigated` vocabulary; and keeping
Claude's `conflicts_with` and E3 source-resolution, which `EVIDENCE_GRAPH.json`
has no equivalent for. Full convergence/divergence table in the analysis file.

## 3. How the two reviewers differ — measured, not asserted

From the three review rounds on PR #436:

| | Copilot (reviewer) | Claude (author) |
|---|---|---|
| Findings raised | 20 | — |
| Survived verification | 20 of 20 | — |
| Strength | **local invariants against a stated contract** — duplicate YAML keys, path escape, `q_ref` truthiness, unchecked statuses, unchecked edge endpoints, resolved-conflict rendering | **cross-file contradiction and provenance** — the molt window, the broken `INDEX.yaml`, the `falsifier_lint` gap, the stale-`main` tier error |
| Blind spot | not one cross-artifact contradiction; every finding lived inside a single file | six single-file contract violations shipped, caught immediately by a contract-checking reader |

**Claude finds artifacts that disagree with each other; Copilot finds an artifact
that disagrees with itself.** Neither review covers the other's class.

Two process consequences:

- A governance change wants both reviewers. Today it gets both by accident.
- **Copilot's summary-table findings do not arrive as events.** Nine real findings
  on PR #436 appeared only in the review body's file table, never as inline
  comments; they were nearly missed. Any capture mechanism must read the summary
  table, not just the comment stream.

## 4. The check-in gap — H-ACAT

Night asked whether the check-in process includes H-ACAT. **It does not, for
humans or for agents.**

PR #431 already shipped the check-in mechanism.
`PARTICIPATION_CONTRACT_V0_1.schema.json` requires `subject_ref`,
`observation_level` (O0–O3), `research_role` (R0–R3), `governance_role_claim`
(G0–G5), `continuity_mode` (`EPHEMERAL` / `STANDING_SIGIL` /
`QUALIFICATION_PROOF` / `REGULATED_EXTERNAL_IDENTITY`), `purposes`,
`modality_permissions`, `retention_policy`, `authority_resolution_ref` — and
blocks `effective_authority`, `authority_granted` and `ratifier_signature` so no
participant can self-grant. `EPHEMERAL` is precisely a session-scoped agent.

It carries **no calibration field at all.** A participant can check in claiming
`G3_PROPOSER` with no statement of how calibrated that claim is. `PARTICIPATE.md`
invites any AI system to self-report on the 12 ACAT dimensions, and
`WITNESS_SERVICE_CONTRACT.md` is ACAT-mapped — but the thing a participant
actually signs references neither.

For humans it is worse: H-ACAT is the layer that would measure the operator, it
sits at TRL 1–2, and **`HA-000` has not been run** (`ACAT_MARKETPLACE_ROADMAP.md`:
"H-ACAT HA-000 not yet run"). The instrument that would calibrate the operator has
never been executed on the operator.

### Proposed `v0.2` addition

```yaml
calibration:
  instrument: ACAT | H-ACAT | NONE_DECLARED
  self_report_ref: <phase-1 submission id, or null>
  demonstrated_ref: <phase-3 resolution id, or null>
  learning_index: <number, or null>        # demonstrated ÷ self-reported
  resolution_source: <corpus/ledger reference>
```

Two properties keep it honest:

1. **A declared calibration is not a calibration.** `learning_index` follows the
   rule the schema already applies to authority: referenced from an independent
   record, never asserted by the subject. Otherwise check-in becomes a place to
   claim being well-calibrated, which is the exact behaviour ACAT exists to detect.
2. **`NONE_DECLARED` is legal.** Gating the commons on a TRL 1–2 instrument that
   has not run its own founding execution would be the overstatement this
   repository is built to refuse. Recording the absence is the honest state.

## 5. What Z2 is asked to decide

1. **Adopt edge-state grading** into `INTENT_GRAPH.yaml` v0.2 (Z1 recommends yes —
   it catches a defect class Z1 has already demonstrated shipping).
2. **Adopt `failure` / `defeats_if_unmitigated`** so adversarial-review output has
   somewhere to land other than prose.
3. **`calibration` block in `PARTICIPATION_CONTRACT` v0.2** — and whether
   `NONE_DECLARED` stays legal. Schema change to a merged Phase 0 contract, so
   Z2's call, not Z1's.
4. **HA-000.** The founding H-ACAT run does not exist. If operator calibration is
   to mean anything at check-in, something has to execute it. Z1 cannot: H-ACAT
   measures the human operator.
5. **Whether review-agent findings get a ledger.** The repo already has the
   pattern (`audits/molt_tier_gap_ledger.jsonl`, SMAG self-accuracy). One row per
   finding — agent, file, class (`single-file-contract` vs `cross-artifact`),
   verdict on verification — would turn §3's table from a one-PR observation into
   a measured series. Z1 recommends deferring until §1–4 are ruled on rather than
   building instrumentation for an unratified taxonomy.

## Falsifier

This candidate is FALSE if:

1. The two graphs were not independently authored — i.e. PR #436's ontology was
   designed after reading `EVIDENCE_GRAPH.json`. *Stated weakness: the file
   appeared in a directory listing during PR #436's session before the ontology
   was written, though it was not opened. Directory-listing exposure is not zero
   exposure, and this is the weakest link in the independence claim.*
2. Edge-state grading would not have flagged `G-Z2-RATIFY` — i.e. an author
   inclined to overstate would simply have written `state: IMPLEMENTED`. Edge-state
   only helps if grading is harder to fake than prose, and that is untested.
3. The reviewer division in §3 does not hold on the next governance PR reviewed by
   both: Copilot raises a cross-artifact contradiction, or Claude's diff carries no
   single-file contract violations. Measurable from the next PR, no new
   instrumentation required.

```yaml
z2_decision: {status: awaiting_ratification, ratified_at: null, ratification_hash: null, z2_notes: ""}
```
