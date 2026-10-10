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

## Live GitHub API witness bridge (candidate, not active until trusted-main merge)

The read-only `trusted_witness.py` binds the pilot to **GitHub's own REST records**, using a token scoped to `actions:read`, `contents:read`, and `pull-requests:read` from `.github/workflows/scvc-milestone-witness.yml`. It does not accept a caller-supplied JSON attestation to issue a live completion result.

The workflow checks out **main only**; it does not execute PR #794 code or consume untrusted artifacts. GitHub events `workflow_run` (quality-baseline/security-gates), `push`, `workflow_dispatch`, and a daily schedule trigger **read-only** re-evaluation after the workflow is reviewed and installed on main. Before that merge, there is no active trusted scheduled witness.

The collector corroborates, independently of candidate self-reports:

- Witness run ID, run attempt, trusted-main checkout SHA and workflow path against GitHub REST.
- Predecessor PR #788 merge commit ancestry and blob-verified source files from the exact default-branch SHA.
- Current PR #794 head SHA; exact-head quality/security workflow run ID, attempt, event, issuer workflow path and completed successful job results.
- No candidate edits to the two CI-issuer workflow files.
- **Positive** branch trust-root verification: an active ruleset applying to main must require both a PR approving review and a quality-related required status check. Missing permissions, unknown rules, non-fast-forward restrictions alone, or unavailable rulesets yield `BLOCKED_TRUST_ROOT`.

The resulting evidence object stays ephemeral and is emitted to GitHub Actions step summary and a 30-day artifact. An artifact hash or copied JSON is **not** a cryptographic attestation, a durable issuer signature or a human acceptance receipt.

When the positive trust-root condition and all M0 predicates and exact-head CI succeed, the derived observer reports `SCVC-M0=OBSERVATIONAL_MILESTONE_ACHIEVED` and unlocks `SCVC-M1=ELIGIBLE_FOR_AUTHORIZED_WORK`. These are **observation-only statuses**, not an authorized coordinator ledger mutation or final Z2 disposition. M1–M4 still require separately verified evidence and human review where indicated.

If branch protections cannot be verified, the observer retains `BLOCKED_TRUST_ROOT` even when CI succeeds. At review time, GitHub's visible repository-wide ruleset enforced deletion/non-fast-forward protection but did not demonstrate required reviews and required CI, so **no protected trust-root claim is made**.

### Verify locally (synthetic; no GitHub authentication)

```bash
python3 -m pytest tests/test_scvc_v02_milestone_pilot.py tests/test_scvc_v02_trusted_witness.py -q
```

To inspect future live witness evidence, use the GitHub Actions run for `scvc-milestone-witness`; never treat self-described `CLAIMED_VERIFIED` metadata, user-controlled commit statuses, or JSON copies as verified proof.

### Governance conditions

The new workflow is a **proposed control** on this PR. It is not an independent trust anchor until installed on and executed from a suitably protected default branch. The runtime does not modify GitHub permissions, repository rulesets, admission state, issue comments, workflow dispatch, PR readiness, or merge status. The real-world transition into protected independent CI still requires repository-owner review and verified rule configuration. No automatic promotion of M1–M4 is permitted without a separately approved scope expansion.
