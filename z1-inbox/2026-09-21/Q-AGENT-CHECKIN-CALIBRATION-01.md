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

### 3a. Is the mitigation bidirectional? No — and the missing half is the larger one

Night asked whether there is a bidirectional mitigation. There is not. Stating
both directions plainly:

| Direction | Channel today | Loss |
|---|---|---|
| **Copilot → Claude** | review comments arrive as events; **summary-table findings do not** | 9 of 20 findings on PR #436 were reachable only by fetching the review body and parsing its file table |
| **Claude → Copilot** | **nothing** | Copilot re-reviews the diff from scratch each round. It cannot read Z1's replies, does not know a finding was accepted, deferred with a reason, or judged wrong, and re-raises accordingly |

The second row is the worse one, and it is the asymmetry that costs most: Claude
accumulates context across rounds; Copilot re-derives from the diff every time. A
finding Z1 deferred *with a stated reason* looks identical to a finding Z1
ignored. The only channel back is the diff itself — which is why the reply
comments Z1 has been writing are, from Copilot's side, invisible.

**Proposed mitigation, both directions:**

1. **Copilot → Claude.** Whatever harvests review findings must read
   `pull_request_read(method="get_reviews")` and parse the summary table, not
   only the inline comment stream. This is a documentation/process rule, not code:
   Z1 nearly missed nine real findings by trusting the event stream.
2. **Claude → Copilot.** Findings that are *deferred rather than fixed* get a
   durable in-diff record — the reason lives in the candidate block or a code
   comment at the site, not only in a PR reply. Two of PR #436's deferrals (the
   CI workflow, source content hashing) were handled this way and did not
   re-appear in the next review; the ones answered only in replies are not
   testable either way, which is itself the point. A reviewer that re-derives
   from the diff can only see what the diff says.

Z1 does **not** propose automating a Claude→Copilot channel. There is no
supported mechanism to inject state into Copilot's review, and inventing one
would mean writing text into the diff aimed at steering a reviewer rather than
documenting the code — which is the manipulation pattern
`WITNESS_SERVICE_CONTRACT.md`'s anti-manipulation invariant exists to refuse.
The honest mitigation is that a deferral must be defensible in the artifact,
where any reviewer — bot, human, or a future session — can find it.

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

---

## Options

- `ratify 3`
- `ratify 1-2`
- `ratify 1-3`
- `edit`
- `reject`
- `later`

The numbers are the five asks in section 5 ("What Z2 is asked to decide") above. Asks 4 and 5 are not offered, because a ruling here cannot supply what each needs: ask 4 (HA-000) needs a named administrator who is not Z1, which Night names, and ask 5 (a review-finding ledger) is one the block itself recommends deferring until asks 1-4 are ruled on.

## What each sets in motion

- `ratify 3`: ask 3 only. A `calibration` block (`instrument` as `ACAT`, `H-ACAT` or `NONE_DECLARED`; references to the self-report and the demonstrated record; `learning_index` taken from an independent record, never asserted by the subject; `NONE_DECLARED` stays legal) is to be added to the participation contract as v0.2. It changes no file except this one. Z1 would then draft the v0.2 schema, its tests and the baseline entry as a later pull request, which Night rules on separately because it changes a merged Phase 0 contract. It does **not** run HA-000, and it declares no one calibrated.
- `ratify 1-2`: asks 1 and 2 only. Edge-state grading (`CLAIMED`, `SPECIFIED`, `IMPLEMENTED`, `TESTED`, `OBSERVED`) and the `failure` / `defeats_if_unmitigated` vocabulary are to be adopted into `INTENT_GRAPH.yaml` v0.2, keeping `conflicts_with` and the source-resolution check, as the block says. It changes no file except this one. Z1 would draft v0.2 as a later pull request. The block's claim that the two graphs were independently authored (section 1 and falsifier 1) was retracted elsewhere, and this option does not rely on it; see below.
- `ratify 1-3`: all three of the above, as separate later pull requests.
- None of these options adopts the two review-process rules in section 3a, which are not among the five asks.
- `edit`: Z1 revises the block and files it again.
- `reject`: the block closes with its bytes signed and the reason Night records. Nothing is entered in `REGISTERED.md`.
- `later`: this block closes with its bytes signed; the question returns only as a new block.

## Checked on 2026-11-16 (not carried from the block above)

- **Section 1 and falsifier 1 are superseded.** The block says the two graphs are the only uncontaminated sample and independently authored. `AGENT_GRAPH_COMPARISON.md` carries a "Correction, 2026-09-21" that retracts this: the test that mattered was source disjointness, not graph-to-graph exposure. As recorded there and in `Q-GRAPH-CONVERGENCE-01`, the graphs have 6 aligned pairs, 0 graded independent, total corroboration weight 0.0. Z1 did not re-run the tool today. The text above is left unchanged.
- **The case for edge-state grading survives that correction.** It rests on the `G-Z2-RATIFY` contradiction, where `Q-GRAPH-CONVERGENCE-01` records that "the tree agrees with EVIDENCE", the graph that grades the edge. Still true on main today: in `.github/workflows/z2_ratification_gate.yml` the `ratify.py --verify` step has `continue-on-error: true` (line 143), and a search of that file for "anti-cascade" or "anti_cascade" finds nothing.
- **The graph-convergence ruling did not adopt edge-state grading.** `Q-GRAPH-CONVERGENCE-01` was ruled `ratify 1-3` and reconciled. Its three asks were the alignment rows, `source_lineage` and `render --check` in CI. So asks 1 and 2 here are still open.
- **`INTENT_GRAPH.yaml` is unchanged in the relevant way.** It is `version: 1`, its edges carry `from`, `to` and `rel` only, and a search finds no edge `state`, `failure` or `defeats_if_unmitigated` field.
- **No v0.2 contract exists.** Only `PARTICIPATION_CONTRACT_V0_1.schema.json` is in the tree (added by #431), and it has no `calibration` field.
- **HA-000.** `ACAT_MARKETPLACE_ROADMAP.md` still says "HA-000 not yet executed" (line 96) and "HA-000 not yet run" (line 165). Z1 found nothing in the tree showing it ran, and did not look outside the tree.
- **A review-finding ledger does not exist.** The pattern does: `audits/molt_tier_gap_ledger.jsonl` and `audits/smag_pilot_ledger.jsonl`.
- **Not re-checked:** the section 3 counts from PR #436 (20 findings, 20 of 20 verified, the nine summary-table findings).

## Ruling

choice:
by:
at:
status: OPEN
