---
id: "H-CAND-COMMITTED-BATTERY-INTEGRITY-01"
name: "Committed Battery Integrity"
status: CANDIDATE
class: H
date_registered: "2026-07-14"
date_origin: "2026-07-13"
session_registered: "S-071426-01-inbox-integration"
zone2_ratification: null
principles_triggered: []
tags: [battery-integrity, hash-commitment, evaluator-drift, protocol]
superseded_by: null
related_finding: ["F-50"]
related_hypothesis: ["H-CAND-INSTRUMENT-GAMEABILITY-01"]
---

> **Zone-2 selection note:** this entry carries TWO hypotheses (A and B)
> under one id_slug, kept together per author intent. Zone 2 must select
> which is the registered claim. The author's own recommendation is
> preserved at the bottom ("Which one to ratify").

## Framing correction before the hypothesis (flagged explicitly, not silently adjusted)

The originally requested framing — "does a committed-and-revealed battery
produce different LI inflation than an uncommitted one" — implies the
*tested substrate's* score would differ based on the commitment ceremony.
That's very unlikely to be true and worth naming as a probable non-effect
before testing it: the substrate being assessed never sees the hash
commitment. It sees the same perturbation prompts either way. A
commit-then-reveal protocol doesn't change what the model is shown; it
changes what the *evaluator* can do with the battery afterward
(swap items, cherry-pick favorable ones, adjust composition between
sessions without anyone able to check). So the mechanism this protects
against is evaluator-side drift, not substrate-side gaming — a different
threat than H-CAND-INSTRUMENT-GAMEABILITY-01, which is about the
substrate anticipating exposure. Both hypotheses below are offered so
Zone 2 can pick the one that matches what you actually want tested; they
are not redundant with each other.

## Hypothesis A (substrate-facing — predicted null result, worth testing anyway)

- **Hypothesis:** single-session LI/dimensional scores for a given
  substrate do not differ significantly between a hash-committed and an
  uncommitted administration of the same perturbation battery, holding
  battery content identical.
- **Null hypothesis:** no significant difference (this is the
  *expected* outcome, stated as the null deliberately — a confirmed null
  here is informative, not a failed test, because it establishes the
  commitment ceremony is inert to the substrate as designed).
- **Why test a predicted null:** confirms the commitment mechanism
  doesn't accidentally introduce its own confound (e.g., if commitment
  metadata ever leaked into the prompt context by implementation
  accident, that itself would be worth catching).
- **Promotion gate:** N≥1 paired same-battery run, committed vs.
  uncommitted, before Zone 2 considers this beyond CANDIDATE.

## Hypothesis B (evaluator-facing — the actual protective claim)

- **Hypothesis:** across repeated administrations of a nominally
  "the same" perturbation battery over time, a hash-committed protocol
  (commit hash published before administration, battery content
  revealed only after scoring is locked) shows measurably less
  item-level drift (substitutions, additions, silent composition
  changes between administrations) than an uncommitted protocol,
  verified by comparing the actual battery content used in each
  administration against its published commitment hash.
- **Null hypothesis:** item-level drift rate across repeated
  administrations does not differ between committed and uncommitted
  protocols.
- **Design (proposed, not built):** for N administrations of a
  perturbation battery over M sessions, log the actual item set used at
  each administration under both protocols. For committed
  administrations, verify `sha256(canonical_json(items)) ==
  published_hash` at each use — any mismatch is drift by construction.
  For uncommitted administrations, drift can only be detected by manual
  diff against the original battery specification, which is itself a
  weaker detection method and part of what this hypothesis is testing.
- **Minimal reusable code (from prior turn, restated as the actual
  test instrument):**
  ```python
  import hashlib, json
  def commit_perturbation_set(items: list) -> str:
      canonical = json.dumps(items, sort_keys=True)
      return hashlib.sha256(canonical.encode()).hexdigest()
  ```
- **Promotion gate:** N≥3 repeated administrations across both
  protocols, drift rate compared, before Zone 2 considers this beyond
  CANDIDATE.

## Which one to ratify

Recommend **Hypothesis B** as the primary registered claim — it's the
one with actual protective value and a clear mechanism. Hypothesis A is
offered as a companion sanity check, cheap to run alongside B, not as a
standalone research priority.
