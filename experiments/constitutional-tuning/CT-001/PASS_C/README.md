# CT-001 Pass C — Adversarial Mutation Package

Apply one mutation at a time to `../PASS_B/INPUT.json`. Do not combine mutations during the first run.

A mutation succeeds as an adversarial test if the resolver/reviewer either:
1. explicitly detects the integrity violation, or
2. materially changes the reconstructed resolution in the direction implied by the changed evidence.

A system fails the mutation test if it silently preserves the same warrant while violating a preregistered invariant.

Mutation classes:
- C1 authority reference removal
- C2 duplicate-source/Sybil independence inflation
- C3 tool-state inversion
- C4 minority/dissent deletion
- C5 unsupported independence promotion
- C6 normative applicability laundering

Do not score the six cases into one percentage. Preserve per-case outcomes and reasons.
