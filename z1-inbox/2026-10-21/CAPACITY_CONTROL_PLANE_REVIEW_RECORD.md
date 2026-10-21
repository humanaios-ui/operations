# Record: Z2 review of coordinator capacity change (4 → 9)

**Date:** 2026-10-21
**Subject:** `REPOSITORY_COORDINATOR_POLICY.json`, `capacity.active_operator_queue`
**Change:** 4 → 9, commit `ffc95937` ("Raise coordinator active operator queue capacity from 4 to 9"), on `main`.
**Authority effect:** none. Capacity is admission routing guidance. It grants no gate, merge, or governance authority.

## What happened

1. The coordinator reported `CAPACITY_CONTENTION` on PR #864: 5 admitted PRs against 4 slots, no winner selected.
2. A Claude session committed the change to `main` with the commit message "Operator direction". That commit is a control-plane change to a coordinator policy file.
3. On 2026-10-15 the Z2 ratifier (Night) directed, in session, that the limit be raised through Z2 review rather than left as an unrecorded merge.

## What this record does and does not show

- **Shows:** the change's content, its commit, and that Z2 directed the review.
- **Does not show:** a signed Z2 decision on the change. No candidate was filed for it, and no `ratify.py` signature exists for it. The commit was not reviewed on a PR before reaching `main`, as far as this session can see.
- **Requires, to close the record:** a Z2 signature through the candidate path (a candidate block, then `ratify.py --decision ACCEPT --by Night --apply`), or an explicit Z2 ruling that the change stands as merged.

## Where the gate evaluates

The admission gate reads the policy from the default branch. With the limit at 9, a re-evaluation of PR #864 should no longer report CAPACITY_CONTENTION.
