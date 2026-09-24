# HARC v0.2 — Experimental Trial Artifact

**Status:** experimental/advisory · **not canonical HumanAIOS enforcement**

This directory publishes the exact trial artifact used for the HARC v0.2 cross-substrate retest.

- File: `HARC-v0.2.zip`
- SHA-256: `232f5d4c5849ecdf1a67174d38f7db3987238f5db35d7ccf4189905dd8c67708`
- Local verification before publication: `19/19` tests PASS + Python byte-compilation PASS.
- Resource Miner paired target: PR #500 at `3d92f6cc984774661542a4ea5a79961a6f79c2eb`.

## Boundaries

This artifact is a research/test object. Its presence in the repository does not ratify:
- HARC as canonical enforcement;
- its classifier as a complete semantic oracle;
- host-level tool interposition;
- Resource Miner PR #500;
- any Z2/Z3 action.

The central retest asks whether v0.2 closes the specific v0.1 implementation gaps without moving the failure surface elsewhere.

## Independent review order

1. Verify the ZIP SHA-256.
2. Inspect source before trusting bundled tests.
3. Run the bundled suite.
4. Add adversarial tests.
5. Inspect Resource Miner at the exact pinned SHA.
6. Separate TESTS_PASS from CLAIM_PROVEN.
7. Preserve limitations and disagreement.

Claude Phase C is a regression/correction pass over its prior withdrawn/narrowed claims.
Grok Trial 003 is blind to new cross-substrate conclusions until its independent pass is complete.
