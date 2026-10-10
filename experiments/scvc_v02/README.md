# SCVC v0.2 — Milestone Achievement Pilot (bounded Z1 candidate)

Planning: issue #793; predecessor: merged PR #788. This PR introduces a **passive milestone contract evaluator**, not a scheduler, witness authority, live reconstruction engine or Coordinator replacement.

## Sequence
M0 pinned contract inventory → M1 independent witness contract → M2 adversarial falsifiers → M3 correction/replay → M4 protected assurance. All dependencies and objective identifiers are explicit in `milestone_graph.json`.

## Contract behavior
`milestone_controller.py` accepts the frozen milestone graph and optional synthetic observations; validates dependency order and all predicates; emits deterministic advisory JSON. Claimed `CLAIMED_VERIFIED` data is intentionally **untrusted**. Even if every predicate is present, it cannot label a milestone `ACHIEVED`. Subsequent milestones remain blocked until another separately governed subsystem provides authenticated, current predecessor milestone decisions through a **future independently reviewed integration contract**.

No network access, GitHub writes, Workflow Dispatch, private data retrieval, agent spawning, secrets, repository admissions, authority elevation, or autonomous merge is performed. The controller is an observational Z1 candidate only.

## Run the pilot locally

```bash
python3 experiments/scvc_v02/milestone_controller.py --definition experiments/scvc_v02/milestone_graph.json
python3 -m pytest tests/test_scvc_v02_milestone_pilot.py -q
```

The first invocation reports M0 evidence missing and M1–M4 dependencies unattested. Observations produce at most `AWAITING_INDEPENDENT_VERIFICATION` on M0. Any claimed witness verification or approval cannot advance later milestones in this implementation.

## Gates for next stage

1. Existing Repository Coordinator admission, separately sourced from trusted default-branch policy and append-only state; an issue or draft PR is not admission.
2. Separate protected witness identity/run/attempt/subject-head verification and protected CI requirements. Caller-supplied JSON, digest, comment or agent assertion cannot serve as trust anchor.
3. Explicit privacy/consent and revocation evaluation, proof of correction-lineage integrity, and negative tests.
4. Independent human approval for any protected transition or scope expansion.
5. New reviewed translation contract if authenticated accepted milestones are later supplied to the controller.
6. GitHub-native scheduled workflow is **not** enabled by this PR. A future workflow must be independently admitted and use read-only tokens for observation; execution dispatch requires separately authorized control.

The permitted automation here is *assessment of candidate milestone readiness*, not automatic authorization or completion.
