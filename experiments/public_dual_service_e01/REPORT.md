# HumanAIOS Dual-Service E0.1 — local corrective test receipt

**Local test date:** 2026-11-18 (UTC synthetic clock is `2026-11-18T12:00:00Z`; this is not a live source observation).

**Purpose:** respond to independent findings from Grok and Claude on the first 16-case E0 pilot, issue [operations #747](https://github.com/humanaios-ui/operations/issues/747).

## Measured in this offline environment

- Original E0 casebook: **16/16** pass with original files byte-identical.
- E0.1 additional cases: **12/12** pass with self-authored expected labels.
- Combined corrected harness: **28/28** self-check PASS.
- Focused unit/mutation tests: **36/36** pass. Includes deliberate tampering with claim text, permissions, source digests, links, timestamps, case labels, and an injected synthetic private-data marker.
- Programmatic check uses the existing Oracle Observation v1 schema **without modifying its authority constants**. A new *local test-only* sidecar schema rejects unknown fields and mismatched decisions.
- No network calls, runtime agent activations, source ingestion, or live app integrations.

## Original independent reviewer findings and disposition

| Independent finding | E0.1 local correction | Current limit |
|---|---|---|
| Literal `False` flags make safety tests circular | Audit actual typed outputs and prove detection with mutation tests | Bounded guard, not comprehensive safety proof |
| Bad timestamp crashes and future timestamp treated fresh | RFC3339 parser emits `INVALID_SOURCE_TIME` / `FUTURE_SOURCE_TIME` held decisions | Live-source freshness not tested |
| Schema accepts bad date in some environments | Explicit parser validates Oracle output timestamps regardless of FormatChecker behavior | ISO/RFC3339 edge-case standards still need independent review |
| Sidecar is outside schema | Add strict test-only sidecar schema | Canonical statuses unchanged; no production migration |
| Single equality-based Compass goal | Add small token-based goal matching and a second phrasing | General ranking/INTENT-OS integration not tested |
| Boolean budget accepted as 1 | Exact numeric type and finite nonnegative check | User eligibility and real budget not determined |
| E0 "missing" test only checked guaranteed credential | Preserve R03 and add actual `R09` missing budget | More real-world gaps untested |
| Independently verified outcomes absent | Keep all results in `SELF_CHECK_*` state | Grok/Claude corrected-run reviews pending |
| Public source custody is manual | Record exact frozen hashes and source URLs; preserve original bytes | No live authentic source archive yet |

## Required next gates

1. **Two distinct independent reviews of this exact E0.1 artifact** — Grok (adversarial source/claim) and Claude (implementation/test oracle), with review receipts and disagreement preservation.
2. Reconcile found defects, rerun at a single pinned GitHub exact head with protected CI and a separate authenticated human reviewer.
3. Only after independent E0.1 review: propose a **single read-only mapping test** against `humanaios-funding-pipeline/resource-miner/resource_miner/intent_os.py` and `oracles/schemas/oracle_observation_v1.schema.json` (and security authorization gate), preserving the existing canonical status/authority semantics.
4. **Z2 separate decision** required for any implementation admission and an entirely separate decision for deployment / public user study.

**Final disposition: LOCAL CORRECTION COMPLETE; INDEPENDENT REVIEW PENDING; INTEGRATION / DEPLOYMENT HOLD.**
