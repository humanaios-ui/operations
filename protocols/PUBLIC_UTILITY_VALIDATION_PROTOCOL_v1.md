# Public Utility + Market Validation Protocol v1.0

**Status:** DRAFT — no external utility or differentiation claim that relies on issue #499 results may be promoted until the maturity gate in §10 is passed.  
**Authority:** Zone-2 ratification required for changes to stakeholder success criteria, comparator-selection rules, or the maturity gate.  
**Purpose:** Prevent confirmation bias, moving goalposts, terminological relabeling, and premature product claims while HumanAIOS tests whether it provides external value beyond its own governance environment.  
**Scope boundary:** This protocol governs issue #499 only. Market demand can generate amendment candidates, but it cannot automatically change the governance authority, evidence standards, or safety boundaries tracked by issue #497.

---

## 1. Strongest-Comparator Rule

1. Every differentiation hypothesis must name the strongest currently available comparator that plausibly solves the same user problem.
2. “Strongest” is determined by market presence, published technical depth, or independent evaluation — never by ease of beating the comparator.
3. A differentiation claim is invalid unless the strongest comparator has been evaluated against the same criteria.
4. Comparator inclusion, exclusion, and replacement decisions must be pre-registered in `market/comparator_registry.yaml` before evaluation begins.
5. If a stronger comparator appears mid-study, reopen the comparison rather than preserving a stale win.

## 2. Locked stakeholder classes

The primary stakeholder classes for this track are fixed unless Z2 ratifies a change:

- developers / operators
- enterprises
- auditors / compliance teams
- insurers / risk assessors
- researchers
- regulators / policy teams
- open-source maintainers
- security teams
- biomedical / research institutions
- general public / civil-society observers

Results may be segmented by stakeholder class, but mixed results may not be reframed as universal success.

## 3. Pre-registered success and failure criteria

Before data collection, every benchmark or utility test must define:

1. the stakeholder class under test,
2. the exact workflow being improved,
3. at least one quantitative or binary success criterion,
4. a paired failure criterion,
5. the baseline system being compared,
6. the evidence labels that will be used in the final report.

Exploratory observations may be logged after the fact, but they may not replace the pre-registered pass/fail criteria.

## 4. Functional-equivalence requirement

Differentiation must be tested on observable behavior, not naming differences.

Questions to answer for each comparator:

- Can a user reconstruct what happened?
- Can a user see why the action was allowed?
- Can a user inspect the evidence chain supporting the action?
- Can a user identify what remained unknown or disputed?
- Can a user tell what authority or role allowed execution?
- Can a user inspect the execution receipt and downstream consequence?

If a comparator solves the same user job through a different representation, HumanAIOS must count that as competition.

## 5. Evidence labels

Every market-facing claim in this track must be labeled with one of the following classes:

- `VENDOR_CLAIM`
- `PUBLIC_DOCUMENTATION`
- `CUSTOMER_REPORT`
- `INDEPENDENT_REVIEW`
- `OBSERVED_PRODUCT_BEHAVIOR`
- `HUMANAIOS_EXPERIMENT`
- `INFERENCE`
- `UNKNOWN`

Vendor marketing is admissible only as `VENDOR_CLAIM` or `PUBLIC_DOCUMENTATION`; it is never independent validation by itself.

## 6. Differentiation hypotheses are two-part tests

Each differentiation hypothesis must be split into both of the following questions:

1. **Feature-presence question:** does an existing system already expose the capability?
2. **External-value question:** does the capability improve a real stakeholder workflow enough to matter?

A differentiation hypothesis fails if either:

- the strongest comparator already solves the job at adequate quality, or
- the capability exists only as a distinction without measurable user value.

## 7. Required benchmark ladder

The minimum benchmark ladder for consequential-action analysis is:

```text
BASE AGENT
        vs
OBSERVABILITY-INSTRUMENTED AGENT
        vs
HUMANAIOS-GOVERNED AGENT
```

Each run must measure whether an independent observer can determine:

1. what happened,
2. why it happened,
3. what evidence supported the action,
4. whether the evidence was independent,
5. what authority allowed it,
6. whether scope was respected,
7. what remained unknown or challenged,
8. what was executed,
9. what consequence occurred,
10. whether the warrant changed after the consequence.

The first completed run may be a desk benchmark over public product documentation, but all utility claims require task-based experiments with real users.

## 8. Public commons vs institutional product split

Every artifact in this track must be classified as one of:

- **public commons candidate** — reusable schema, method, public viewer, educational or research output,
- **institutional / commercial candidate** — private telemetry, retained evidence graph, enterprise controls, integrations, deployment support,
- **shared dependency** — used by both layers.

The split is a hypothesis, not an axiom. If the same artifact cannot serve both layers without conflict, record that explicitly.

## 9. Governance boundary with issues #497 and #498

- Issue #497 remains the authority source for governance architecture and execution boundaries.
- Issue #498 may inform historical framing or experimental controls, but historical analogy does not count as market validation.
- Customer demand, comparator pressure, or adoption signals may create amendment candidates, but they do not ratify constitutional or safety changes.

## 10. Maturity gate

No external differentiation or public-utility claim from this track may be promoted unless all of the following are true:

1. comparator selection is published and current,
2. at least one comparative benchmark run is logged,
3. at least one external-user utility test is logged,
4. the result log records any failed differentiation claims,
5. the public-commons / institutional split has been evaluated,
6. the “Show Me Why” demonstrator has been tested on a non-sensitive fixture,
7. unresolved unknowns are named instead of collapsed into success language.

If any gate is not met, the correct status is **UNPROVEN** rather than “emerging,” “category-defining,” or equivalent marketing language.

## 11. Stage-specific falsifiers

### Stage 0 — Problem validation
Fails if the target actors do not describe the problem as costly, confusing, or currently underserved.

### Stage 1 — Category validation
Fails if there is no evidence that organizations already buy or adopt adjacent observability, governance, evaluation, audit, or control-plane tools.

### Stage 2 — Gap validation
Fails if strongest comparators already provide the same evidence → warrant → authority → receipt loop at adequate quality.

### Stage 3 — Utility validation
Fails if HumanAIOS does not improve reconstruction quality, decision quality, trust calibration, or authority-boundary compliance for the tested user.

### Stage 4 — Outcome validation
Fails if the added provenance and warrant layers increase governance burden without improving understanding or correction.

### Stage 5 — Adoption / willingness to pay
Fails if users value only conventional observability or compliance outputs and will not adopt the additional HumanAIOS layer.

## 12. Required outputs for this track

The initial repository-backed outputs are:

- `market/actor_map.yaml`
- `market/comparator_registry.yaml`
- `market/capability_matrix.json`
- `market/gap_hypotheses.yaml`
- `market/public_utility_hypotheses.yaml`
- `market/benchmark_protocol.md`
- `market/show_me_why_demo/`
- `market/validation_results.jsonl`
- `market/product_molt_log.md`

These files may record negative or null results. Failure to differentiate is a valid outcome and must be preserved.
