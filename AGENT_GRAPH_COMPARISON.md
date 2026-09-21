# AGENT_GRAPH_COMPARISON.md — two agents, two graphs, one repository

**Candidate:** Q-AGENT-CHECKIN-CALIBRATION-01
**Status:** PROPOSED — Z1 analysis; no ratification claimed
**Subjects:** `EVIDENCE_GRAPH.json` (Copilot, PR #431, merged 2026-09-21) · `INTENT_GRAPH.yaml` (Claude, PR #436, open)

---

## Why this is not a staged experiment

Night proposed asking Copilot to generate a graph of the repository so the two
could be compared. That experiment has already run, unprompted, and its result is
merged: **PR #431 was authored by `copilot-swe-agent` and shipped
`EVIDENCE_GRAPH.json` — a typed graph of this repository — hours before
`INTENT_GRAPH.yaml` was written in PR #436.**

Neither agent saw the other's graph. Neither was told to build a graph in a
particular shape. Both were given a governance problem in the same tree and both
independently reached for a typed graph with claims, controls, tests and
falsifiers as first-class node types.

Staging the experiment now would be worse evidence than reading the one that
already happened, because a staged run would be contaminated: Z1 has now read
Copilot's ontology and cannot un-read it. **The naturally occurring pair is the
only uncontaminated sample this repository will ever get.** It is written up here
before any merge of the two designs, so the independent priors are on record.

---

## The two ontologies

| | `EVIDENCE_GRAPH.json` (Copilot) | `INTENT_GRAPH.yaml` (Claude) |
|---|---|---|
| **Question asked** | Is this claim *established*? | Is this objective *grounded*, and does anything contradict it? |
| **Scope** | One initiative (Phase 0 Witness), 15 nodes | Repository intent layer, 26 nodes |
| **Node types** | artifact, claim, control, test, evidence, failure, falsifier, decision, standard, readiness_domain (10) | vision, mission, principle, objective, gate, instrument (6) |
| **Edge types** | constrained_by, implements, verifies, supports, defeats_if_unmitigated, narrows_scope, crosswalk_for, gates (8) | realizes, grounds, measures, enforces, constrains, conflicts_with (6) |
| **Where maturity lives** | **on the edge** — `state: CLAIMED → SPECIFIED → IMPLEMENTED → TESTED → OBSERVED` | **on the node** — `status: LIVE / PROPOSED / CONFLICTED / CITED_NOT_IMPLEMENTED` |
| **Anti-drift** | conformance test asserts required files exist and edge states are legal | E3: every node `source` must resolve inside the tree, or `check` fails |
| **Contradiction** | not expressible | `conflicts_with`, directional, must name a resolving candidate |
| **Threat model** | `failure` nodes, `defeats_if_unmitigated` edges | not expressible |
| **External frame** | `standard` node, NIST AI RMF crosswalk | not expressible |
| **Enforcement** | 5 unit tests (98 lines) | 30 self-tests, `check` + `render --check` sync |

---

## Convergence

Four things both agents did without coordination. Convergence across independent
designs is weak evidence that the choice is forced by the domain rather than by
either agent's habits — the closest thing to a control this comparison has.

1. **A typed graph, not prose.** Both concluded the relations were the thing
   worth making machine-readable.
2. **Falsifier as a first-class node type.** Both lifted it out of prose into the
   ontology. This one is plausibly repo-induced — the falsifier doctrine is
   everywhere in CLAUDE.md — but neither was told to model it as a *node*.
3. **Separation of claim / control / verification.** Copilot: claim → control →
   test. Claude: objective → gate → instrument. Different vocabulary, identical
   three-layer shape, with the verifying layer pointing back at the constraining
   layer (`verifies` / `enforces`).
4. **Explicit non-authority.** Copilot: `WITNESS_IS_NOT_THE_AUTHORITY`, contract
   cannot self-grant. Claude: the validator "has no opinion about which side of a
   conflict is right," ratification stays a Z2 act. Both agents independently
   built the constraint that the instrument must not become the ratifier.

---

## Divergence, and which side is right

### 1. Edge-state grading — Copilot is right, and it would have caught Claude's own defect

Copilot puts `CLAIMED → SPECIFIED → IMPLEMENTED → TESTED → OBSERVED` on the
**edge**. Claude puts status on the **node**. These are not stylistic variants:
edge-state answers *how well established is this relationship*, which node-status
structurally cannot.

The test case is already on record. In PR #436 the node `G-Z2-RATIFY` asserted its
workflow "refuses a merge without a Z2 hash, a falsifier, and anti-cascade
compliance." It does not — the signature check is `continue-on-error: true` and
anti-cascade is not evaluated there at all. Claude's validator passed it, because
E3 only checks that the node's `source` *resolves*, and the file is right there.
A human reviewer caught it.

In Copilot's ontology that edge would have carried `state: CLAIMED`, and the gap
between claimed and implemented would have been **visible as data**. This is the
strongest single result in the comparison: an ontology built by one agent would
have mechanically caught a defect the other agent committed and shipped.

**Verdict: adopt.** Edge-state grading belongs in `INTENT_GRAPH.yaml`.

### 2. Contradiction — Claude is right

`EVIDENCE_GRAPH.json` has no way to say *these two live artifacts disagree*. Its
edges all assert construction (implements, verifies, supports); none assert
conflict. A repository where `MOLT_STATE.md` and `BOOT_PROCESS_MAP.md` give
opposite answers cannot be described in it.

**Verdict: keep.** `conflicts_with` has already surfaced five contradictions.

### 3. Threat modelling — Copilot is right

`failure` nodes and `defeats_if_unmitigated` edges express "this known attack
would invalidate that claim." Claude's graph has no vocabulary for a failure mode
that has not yet happened; `conflicts_with` only describes disagreements that
already exist in the tree.

**Verdict: adopt.** The repo runs adversarial review and red-team audits whose
outputs currently land only in prose.

### 4. Source resolution — Claude is right

Copilot's nodes are free-text labels. `{"id": "A1", "label":
"PARTICIPATION_CONTRACT_V0_1.schema.json"}` happens to name a real file, but
nothing in the graph requires it to; the conformance test checks a separate
hardcoded list. Rename the file and the graph still validates while describing a
tree that no longer exists.

**Verdict: keep.** E3 is what stops a graph becoming a wish list.

### 5. External standards — Copilot is right

A `standard` node with a `crosswalk_for` edge (NIST AI RMF) anchors internal
structure to an external frame. Claude's graph is entirely self-referential, which
is comfortable and unfalsifiable from outside.

**Verdict: adopt, low priority.** Real for funder and regulator audiences.

---

## Synergy: what a merged ontology looks like

Not a union of both — that would be 16 node types nobody can hold in mind. The
merge that earns its complexity:

```yaml
# from Copilot — maturity moves to the edge
edges:
  - from: G-Z2-RATIFY
    to: P-SERIAL-GATE
    rel: enforces
    state: CLAIMED          # CLAIMED | SPECIFIED | IMPLEMENTED | TESTED | OBSERVED
    state_evidence: ".github/workflows/z2_ratification_gate.yml: continue-on-error: true"

# from Copilot — threats are nodes
  - {id: F-SELF-RATIFY, type: failure, name: Z1 signs its own candidate}
  - {from: F-SELF-RATIFY, to: P-SERIAL-GATE, rel: defeats_if_unmitigated}

# from Claude — kept
  - {from: O-MOLT-CYCLE, to: O-TEMPORAL-GATE, rel: conflicts_with, status: OPEN, q_ref: ...}
```

The single highest-value change is `state` on `enforces` and `measures` edges.
Every node in `INTENT_GRAPH.yaml` that names a gate currently asserts that gate
works. Grading those edges would convert the graph from *what we believe is
connected* into *what we have evidence is connected* — and would have caught
`G-Z2-RATIFY` without a reviewer.

---

## What this says about the two reviewers

Night asked how we capture the difference between Copilot's feedback and Claude's.
The graphs are one sample; the PR #436 review rounds are another, and they point
the same way.

| | Copilot (as reviewer on PR #436) | Claude (as author) |
|---|---|---|
| Findings raised | 20 across 3 rounds | — |
| Held up on verification | 20 of 20 | — |
| Characteristic strength | **local invariants against a stated contract** — `safe_load` duplicate keys, path escape, `q_ref` truthiness, statuses unchecked, edge endpoints unchecked, resolved-conflict rendering | **cross-file contradiction and provenance** — the molt-window conflict, the broken `INDEX.yaml`, the `falsifier_lint` gap, the stale-`main` tier error |
| Characteristic blind spot | did not surface a single cross-artifact contradiction; every finding was inside one file | shipped six single-file defects that a contract-checking reader caught immediately |

The division is clean enough to be worth acting on rather than admiring: **Claude
finds disagreements between artifacts; Copilot finds an artifact disagreeing with
itself.** Those are different failure classes, and neither agent's review covers
the other's.

The practical consequence is that a governance change wants both, and the current
process gets both only by accident — Copilot reviews because a workflow requests
it, and its summary-table findings were nearly missed because only the inline
comments arrive as events.

---

## Proposed: calibration at check-in

PR #431 already shipped the mechanism. `PARTICIPATION_CONTRACT_V0_1.schema.json`
requires `subject_ref`, `observation_level` (O0–O3), `research_role` (R0–R3),
`governance_role_claim` (G0–G5), `continuity_mode` (`EPHEMERAL`,
`STANDING_SIGIL`, `QUALIFICATION_PROOF`, `REGULATED_EXTERNAL_IDENTITY`),
`purposes`, `modality_permissions`, `retention_policy` and
`authority_resolution_ref` — and blocks `effective_authority`,
`authority_granted` and `ratifier_signature` so a participant cannot self-grant.

`EPHEMERAL` is exactly what a session-scoped agent is. The check-in contract Night
wants for agents entering the system is already specified.

**The gap: it carries no calibration field, for agent or human.**

`PARTICIPATE.md` invites any AI system reading the repository to self-report on
the 12 ACAT dimensions, and `WITNESS_SERVICE_CONTRACT.md` is ACAT-mapped. But
`PARTICIPATION_CONTRACT_V0_1` — the thing an entering participant actually signs —
has no ACAT reference, no H-ACAT reference, and no field where a self-report or
its resolution could be recorded. A participant can check in with a declared
`governance_role_claim` of `G3_PROPOSER` and no statement of how well calibrated
that claim is.

For human participants the same hole is worse, because H-ACAT is the layer that
measures it and **`HA-000` has not been run** (`ACAT_MARKETPLACE_ROADMAP.md`: H-ACAT
at TRL 1–2, "HA-000 not yet executed"). The instrument that would calibrate the
operator has never been executed on the operator.

Proposed `v0.2` addition, deliberately minimal and non-self-granting:

```yaml
calibration:
  instrument: ACAT | H-ACAT | NONE_DECLARED
  self_report_ref: <phase-1 submission id, or null>
  demonstrated_ref: <phase-3 resolution id, or null>
  learning_index: <number, or null>       # demonstrated ÷ self-reported
  # LI is recorded, never asserted by the subject: like effective_authority,
  # it is resolved from an independent record, not supplied at check-in.
  resolution_source: <corpus/ledger reference>
```

Two properties keep this honest:

1. **A declared calibration is not a calibration.** `learning_index` follows the
   same rule the schema already applies to authority — the subject may reference
   it, never assert it. Otherwise check-in becomes a place to claim being
   well-calibrated, which is the precise behaviour ACAT exists to detect.
2. **`NONE_DECLARED` is a legal value.** Requiring a calibration to participate
   would gate the commons on an instrument that is TRL 1–2 and has not run its
   own founding execution. Recording the absence is the honest state.

---

## Falsifier

This analysis is FALSE if:

1. `EVIDENCE_GRAPH.json` and `INTENT_GRAPH.yaml` were not independently authored —
   e.g. PR #436's author had read PR #431's graph before designing the ontology.
   *(Checkable: PR #431 merged 2026-09-21T07:21Z; the INTENT_GRAPH design commit
   landed 2026-09-21T12:4x. Session transcript shows `EVIDENCE_GRAPH.json` was
   listed in a directory listing but never opened before the ontology was written.
   This is the weakest link in the claim and is stated as such: directory-listing
   exposure is not zero exposure.)*
2. Edge-state grading would **not** have flagged `G-Z2-RATIFY` — i.e. an honest
   author would have written `state: IMPLEMENTED` on that edge anyway. This is the
   substantive risk: edge-state only helps if grading is harder to fake than prose.
3. The Copilot/Claude division of findings does not hold on the next governance PR
   reviewed by both — Copilot raises a cross-artifact contradiction, or Claude's
   diff contains no single-file contract violations.

Condition 3 is the one to watch, and it is measurable from the next PR onward
without any new instrumentation.
