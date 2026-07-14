# CLAUDE.md — operations repo conventions

Guidance for Claude Code (and any AI agent) working in this repo. These conventions are
**antibodies** distilled from grounded GitHub Copilot reviews via the recursive review loop
(`docs/RECURSIVE_REVIEW_LOOP.md`) — each earned by a real, reproduced finding, not asserted.
Z2-ratified (S-070626). *(Restored + extended in the Cycle-003 PR after the #52 merge silently
dropped this file — see L7.)*

## Code-craft conventions

- **L1 · Guard-clause consistency.** When a status/branch depends on a downstream function
  with a falsy/edge guard (e.g. `compute_li` returns `None` for `p1_total == 0`), key the
  caller's "success" off the *actual result*, not a proxy like "both inputs present." Check the
  callee's edge behavior. *(bug: PR #46)*

- **L2 · Doc-to-code fidelity.** Cite the *full mounted* route path (prefix included); verify a
  schema actually carries a field before asserting it; don't conflate distinct mechanisms (a
  time-gap gate ≠ a contamination check). Read the contract, don't infer it. *(PR #47)*

- **L3 · Name the metadata layer.** Distinguish publish-time / honesty-layer tags (e.g.
  `self_referential`) from persisted DB/API columns. *(PR #47)*

- **L4 · Conform to (or reconcile) declared contracts.** When output has a declared schema
  (`acat/contracts/*.schema.json`), check it conforms (keys + enum values) or document the divergence.
  *(PR #52: `score_session` vs `score_result.schema.json`)*

- **L5 · A peer's auto-fix is itself a Phase-1 claim.** When a reviewer AI auto-applies a fix,
  ground the *fix*, don't just accept the resulting consistency. Auto-fixing a **design**
  divergence can co-drift (Copilot aligned `score_result` schema→code, dropping the
  `validated`/`failed` lifecycle). *(PR #52, Cycle 002 — Z2 to confirm direction)*

- **L6 · Ground auto-corrections; reject no-ops.** An AI reviewer's auto-generated *fix PR* is a
  claim, not truth: verify it (a) changes something real — **empty/no-op PRs are noise, not work**
  — and (b) addresses a concern that wasn't already mitigated. A human/CI anchor gates merges.
  *(PR #55: an empty "fix" PR merged as noise → the `no-op-pr-guard` workflow now catches it.)*

- **L7 · Verify ratified content actually landed.** After a merge/rebase, confirm the files you
  intended are on `main` — churn can silently drop additions (this CLAUDE.md was dropped by the
  #52 merge). "Merged" is a claim; check the tree. *(Cycle 003)*

- **L8 · P-ANON gate before naming a collaborator.** Before a funding/public-facing doc names a
  collaborator or org, confirm they have self-attributed publicly; keep unconfirmed parties
  anonymized (e.g. "Governance-systems collaborator [PENDING P-ANON CHECK]"). Names are a
  claim about consent, not just a fact. *(Cycle 005)*

## How these are maintained

New conventions are added only through the review loop: a finding is **grounded** (reproduced /
verified) before it becomes a convention — never absorbed on authority. See
`docs/RECURSIVE_REVIEW_LOOP.md` for the ledger and the honesty guardrail (ground before
absorbing; watch co-drift; a 100% accept-rate is a smell; empty PRs are noise).
