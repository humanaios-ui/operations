# Intent: [name]
Author: [name or did:key:z6Mk...]. Status: draft.
Submitted: [ISO timestamp]. Signature: [optional base64 Ed25519 signature over body]

## Problem
What can't be done today, and who is affected.
_Restate as a symptom, not a solution. Anti-drift check: Z1 asks "so the real problem is...?" - confirm or correct._

## Proposed Outcome
What "better" looks like when this ships.

## Affected Users and Systems
Who interacts with it, what code it touches.

## Constraints
What must not change or be introduced.

## Open Questions
What still needs a decision before design can start.

---

## Falsifier
A specific, observable condition that would prove this intent wrong.
Example: "If the API response time stays above 4s after this ships, this failed."

## Success Probability
A forecast `smag_p: <0..1>` for this intent reaching the proposed outcome as stated.
Example: `smag_p: 0.72 # Z1`

## Calibration Check
Has the originator re-read this intent after scenario pressure and still endorse it?
- [ ] Re-read and endorse (signature updated)
- [ ] Re-read and revise (submit revised version, not a flag)
- [ ] Skipped (mark as AMBIGUITY callout)

_Optional for feature-level intents; required for architectural changes._
