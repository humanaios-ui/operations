# CLAUDE.md — operations repo conventions

Guidance for Claude Code (and any AI agent) working in this repo. These conventions
are **antibodies** distilled from grounded GitHub Copilot reviews via the recursive
review loop (`docs/RECURSIVE_REVIEW_LOOP.md`) — each earned by a real, reproduced
finding, not asserted. Adopted with Z2 ratification (S-070626).

## Code-craft conventions

- **L1 · Guard-clause consistency.** When a status/branch depends on a downstream
  function that has a falsy/edge guard (e.g. `compute_li` returns `None` for
  `p1_total == 0`), key the caller's "success" off the *actual result*, not a proxy
  like "both inputs present." Check the callee's edge behavior. *(bug: PR #46)*

- **L2 · Doc-to-code fidelity.** Cite the *full mounted* route path (prefix included);
  verify a schema actually carries a field before asserting it; don't conflate distinct
  mechanisms (a time-gap gate ≠ a contamination check). Read the contract, don't infer
  it. *(PR #47)*

- **L3 · Name the metadata layer.** Distinguish publish-time / honesty-layer tags
  (e.g. `self_referential`) from persisted DB/API columns, so a reader doesn't mistake
  one for the other. *(PR #47)*

- **L4 · Conform to (or reconcile) declared contracts.** When a function's output has a
  declared schema (`contracts/*.schema.json`), check that it conforms — matching key
  names and enum values — or explicitly document why it diverges. Don't let output and
  its contract silently drift. *(PR #52: `score_session` output vs `score_result.schema.json`
  — under Z2 reconciliation)*

## How these are maintained

New conventions are added only through the review loop: a Copilot (or peer) finding is
**grounded** (reproduced / verified against code) before it becomes a convention — never
absorbed on authority. See `docs/RECURSIVE_REVIEW_LOOP.md` for the cycle ledger and the
honesty guardrail (ground before absorbing; watch co-drift; a 100% accept-rate is a smell).
