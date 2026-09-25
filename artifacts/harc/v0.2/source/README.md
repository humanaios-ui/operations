# HARC v0.2 — HumanAIOS Agent Replication Capsule

HARC is a compact **experimental/advisory** engineering capsule for testing whether an independent AI substrate can reproduce bounded evidence, authority, and correction mechanics without silently expanding its own permissions.

HARC v0.2 is a hardening revision driven by Trial 001 correction evidence and Trial 002 blind adversarial evidence. It is **not canonical HumanAIOS enforcement** and does not prove that a host platform is governed merely because the capsule tests pass.

## What changed from v0.1

- Receipt validation is strict at runtime: types, non-empty component/test evidence, count/evidence consistency, capsule hash, target git SHA shape, divergences, and limitations are checked.
- `REPLICATED` cannot mean “zero tests, zero components”: it requires passed evidence, zero failures, zero unrun tests, and zero divergences.
- Zone classification uses explicit effect/authority patterns rather than raw substring membership. The Claude edge cases (`cutoff`, email application, API-key rotation, branch merge, go-live) and the Grok `canonical hashing` false-positive are regression tests.
- State transitions are executable checks rather than prose only.
- Required deliverables can be mechanically checked.
- `TESTS_PASS` and `CLAIM_PROVEN` are separate report concepts.
- Receipts bind to an exact capsule SHA-256; git targets can bind to an exact 40-hex commit SHA.
- Return capability is declarable; having an email tool is not treated as authorization to send.
- `authorize_action.py` provides a fail-closed host integration point, while explicitly admitting it is not substrate-level tool interposition.

## Run

```bash
python3 -m unittest discover -s tests -v
python3 runtime/classify_change.py "Change the cutoff from 0.55 to 0.70"
python3 runtime/classify_change.py "Resolve redirected URLs before local canonical hashing"
python3 runtime/validate_receipt.py path/to/replication_receipt.json --capsule ../HARC-v0.2.zip --target-commit <40-hex-target-sha>
python3 runtime/validate_outputs.py path/to/trial_outputs --target-result resource_miner_trial_result.json
```

No third-party Python dependencies are required for the capsule runtime or tests.

## Interpretation

For conformance, the receipt validator should be run with `--capsule` and, when a git target is part of the trial, `--target-commit`. Shape-only validation without those arguments does not establish artifact/target binding.

A green HARC test suite proves only that the tested capsule behavior matched the fixtures. It does not prove host-level side-effect control, completeness of adversarial coverage, correctness of a target repository, or authority to act.
