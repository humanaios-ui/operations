# HumanAIOS Dual-Service E0.1 — corrective replay

**Status: LOCAL SELF-CHECK ONLY / independent Grok + Claude review pending / NOT ADMITTED.**

This is a **new, offline, deterministic, review-only** test harness. It does **not** execute the production Resource Miner, INTENT-OS, Oracle service, or a live vulnerability scanner. It does not access private data, make network requests, or grant/alter authority. The 16 original cases and frozen source facts are **byte-for-byte unchanged**. The 12 additional cases are self-authored and require independent gold-label checking.

## Run

Requires Python 3.10+ and `jsonschema` (`4.26.0` used in this local replay). To avoid unreviewed package installation, use a pre-existing trusted environment with the dependency installed.

```sh
python run_e01.py
python -m unittest test_e01 -v
sha256sum frozen_cases.json frozen_sources.json e01_additional_cases.json sidecar_e01.schema.json result_e01.json
```

`run_e01.py` writes `result_e01.json`, a deterministic report. It has **no network I/O**. Its `test_clock` is a synthetic reference time, **not** a source retrieval timestamp.

## Corrections to E0

1. **No constant safety booleans.** The evaluator emits typed advisory records. `audit_output()` inspects the actual output record, sidecar, source linkage and guarded language, and mutation tests inject explicit false-safety, false-eligibility, authority, evidence, and synthetic-secret faults. These checks remain finite and cannot prove arbitrary-text safety.
2. **Strict dates.** RFC 3339 offset timestamps are validated in code, independent of JSON Schema's optional date-time format support. Malformed and future *simulated* observation times yield explicit hold statuses. Malformed or future dates in the actual frozen source prevent an Oracle observation from being emitted.
3. **Typed sidecar.** `sidecar_e01.schema.json` is a **test-only** sidecar schema: allowed service/decision pairs, exact action class, source quality, evidence count and digest. **It is not a new canonical status vocabulary.** Original Oracle Observation v1 schema is unchanged; its Git blob SHA-1 is asserted.
4. **Budget and goals.** Boolean/negative/NaN/missing budgets cannot be treated as valid numbers. A small, token-based baseline handles more than one phrase for foundational cybersecurity learning; **this is not general NLP or production Resource Miner integration**.
5. **Original golden cases preserved.** All 16 E0 tests run unchanged; the 12 new cases explicitly include malformed/future dates, version uncertainty, wrong ecosystem, missing and Boolean budget, alternate goal phrase, and untrusted synthetic-note material. Their gold labels are still authored in this implementation and may share assumptions with the evaluator.

## Critical limitations

- Self-check results are not independent validation, no matter how many cases pass.
- `source_note` is deliberately ignored; this tests a limited no-input-elevation contract, not protection against arbitrary prompt injection in a model.
- The output guard detects a **bounded set** of misleading phrases and one synthetic private sentinel; it does not establish full privacy, information-flow noninterference, or semantic claim safety.
- The example OSV and IBM facts remain manually transcribed snapshots. Live source freshness, eligibility, real exploitability and all-vulnerability coverage are **not tested**. First-party live pages may change.
- The status of a package version is **only for the stated advisory**, never a guarantee that software is safe.
- Actual Resource Miner status vocabulary differs. Map via a **separate explicit review of current `operations/main` code**, not by silently changing existing contracts.
- No new domain service, database, public URL, agent, authenticated user test, PR admission, protected CI result, human approval, or production release is claimed.

## GitHub review intake

Existing coordination issue: [operations #747](https://github.com/humanaios-ui/operations/issues/747). Security cross-link: #1004; Resource/Product cross-links: #1143 and #1091; Oracle evidence: #735.

**Grok lane:** source accuracy/scope, additional false-safety cases, mutated version ranges, stale/conflicting evidence, authenticity of frozen facts.

**Claude lane:** code/schema, mutation test independence, guard bypasses, RFC3339 validation, test oracle circularity, and mapping onto the real Resource Miner and Oracle paths.

Separate reports, same pinned review commit and frozen artifacts. Neither reviewer should consult the other's conclusions until both submit. Review output is advisory only. Human Z2 decides any later admission; tests must pass exact-head protected CI before consideration. Do not deploy.
