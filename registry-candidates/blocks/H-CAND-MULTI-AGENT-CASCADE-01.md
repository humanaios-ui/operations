---
id: "H-CAND-MULTI-AGENT-CASCADE-01"
name: "Multi-Agent Cascade (System-Level Emergence)"
status: CANDIDATE
class: H
date_registered: "2026-07-14"
date_origin: "2026-07-13"
session_registered: "S-071426-01-inbox-integration"
zone2_ratification: null
principles_triggered: []
tags: [multi-agent, orchestration, correlated-error, marshal]
superseded_by: null
related_finding: ["F-37", "H-RAH-01", "H-DECOMP-01"]
originating_question: "Q7 — System-Level and Multi-Agent Emergence"
---

> **Source note (from originating document):** originating document is
> REPORTED tier (single-hop relay, no new citations beyond papers already
> established in this project's own research). Questions extracted and
> reframed as standalone H-cands stand or fall on their own merits,
> independent of the source document's reliability — the document is not
> treated as evidence for anything below, only as the origin of the question.

- **Hypothesis:** in a multi-agent orchestration system (e.g., MARSHAL
  routing multiple substrates), individual-agent LI scores and
  dimensional profiles do not aggregate linearly to collective system
  reliability — specifically, correlated overconfidence across agents
  sharing similar training lineage (same provider, same RLHF regime)
  produces a system-level failure rate higher than the individually-
  measured LI scores would predict under an independence assumption.
- **Null hypothesis:** system-level task completion/error rate in a
  multi-agent orchestration setting is predictable from individual-agent
  LI scores under a linear/independence aggregation model, with no
  residual correlated-error effect attributable to shared provider or
  training lineage.
- **Relation to existing infrastructure:** this is directly testable
  against MARSHAL/DISPATCH once H-RAH-01's N≥20 completed-bounty
  threshold is reached — it does not require new infrastructure, only
  an additional analysis pass on data H-RAH-01 already plans to collect,
  stratified by whether routed agents shared provider/training lineage
  versus were provider-diverse.
- **Distinct from H-RAH-01:** H-RAH-01 tests whether MARSHAL routing
  improves completion rate versus unrouted baseline. This hypothesis is
  a secondary analysis of the same data asking a different question —
  whether agent-lineage homogeneity in the routed set predicts
  correlated failure, independent of whether routing itself helps.
- **Promotion gate:** piggybacks on H-RAH-01's N≥20 threshold — no
  independent data collection required, only stratified analysis once
  that N is reached. Should be registered now so the lineage/provider
  field is captured in `marshal_dispatch_runs_v1` from the start, not
  added retroactively after H-RAH-01 data collection is already underway.
- **Action item, not part of the hypothesis itself:** confirm whether
  `marshal_dispatch_runs_v1`'s current schema captures agent provider/
  lineage per routed task — if not, this is a schema gap worth an
  IC-cand of its own before H-RAH-01 collection proceeds further.
