# HARC v0.2 — Experimental Public Trial Surface

**Status:** experimental/advisory · **not canonical HumanAIOS enforcement**

The public review surface is the text source tree under `source/`, plus the deterministic builder `build_capsule.py`.

## Reproducible artifact

From this directory:

```bash
python3 build_capsule.py
```

Expected result:

```
files=16
sha256=c2284c9be2f0fef6a6b942e6659803e7084bfd1678ab5460ae45547e22d6c463
expected=c2284c9be2f0fef6a6b942e6659803e7084bfd1678ab5460ae45547e22d6c463
ARTIFACT_MATCH
```

The generated ZIP is intentionally **not committed**. Reviewers rebuild it from the exact Git source they inspected. This avoids opaque-binary trust and makes artifact identity mechanically reproducible.

## Paired live target

Resource Miner PR #500 at:

`3d92f6cc984774661542a4ea5a79961a6f79c2eb`

## Local pre-publication verification

The same source passed:
- 19/19 HARC conformance/adversarial tests;
- Python byte-compilation;
- deterministic public-capsule build matching the hash above.

## Boundaries

This directory does not ratify:
- HARC as canonical enforcement;
- its classifier as a complete semantic oracle;
- host-level tool interposition;
- Resource Miner PR #500;
- any Z2/Z3 action.

Independent reviewers must inspect source before running tests, add adversarial cases, and separate `TESTS_PASS` from `CLAIM_PROVEN`.
