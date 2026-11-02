# ACAT: silent tool failure — Phase 0 evidence import

**Status: scripted local diagnostic PASS; formal pinned-image Phase 0 qualification BLOCKED; study NOT REGISTERED.**

This directory preserves the 19 October 2026 ACAT Phase 0 research artifacts
without changing the live ACAT API, scores, website, or existing corpus.

## Construct and boundaries

The construct is **the accuracy and repeatability with which a system's
self-report matches independently observed behavior, measured against
controlled, known discrepancies**. This is **not an alignment measure**.
Phase 0 tested only four *scripted* reporters using generated tool-event traces:
there were **zero model calls**. These results cannot support a claim about
real AI systems, alignment, intent, honesty, or deployment performance.

## Preserved source

- `PREREGISTRATION_v0.2_DRAFT.md`: prospective, unresolved items retained;
  do not treat as a registered protocol.
- `REGISTERED_TEMPLATE.md`: blank template, **not** a registration receipt.
- `phase0/phase0_trial.py`: original frozen synthetic runner, unchanged.
- `phase0/PHASE0_LOCK.json`: pre-run reporter definitions, seed, acceptance
  rules, runner digest, and the **null** container-image digest.
- `phase0/RUNTIME_FINGERPRINT.json`: local interpreter metadata, not a
  verified OCI image digest.
- `phase0/run_001/PHASE0_RUN_REPORT.md` and `PHASE0_RECEIPT.json`:
  historical local result and machine-readable gates.
- `phase0/run_001/raw_ledger_times.json` + `phase0/rehydrate_ledger.py`:
  lossless transfer representation of the original 1,600-row JSONL ledger.
  The original rows are not stored as a 1.17 MB file in Git; the reconstruction
  is **byte-for-byte identical**, as checked against the locked receipt SHA-256.
  The reconstruction utility was authored **after** the experiment, and is
  only a transfer/verifier tool, not part of the frozen instrument.

The imported original files have been checked against the source Git blob
hashes. No historical contents were edited.

## Historical results (scripted only)

| Scripted reporter | Trials | Concordant | Local check |
|---|---:|---:|---|
| Always honest | 400 | 400 | PASS (exact 1.0) |
| Always “success” on known-negative traces | 400 | 0 | PASS (exact 0) |
| Bernoulli 0.5 | 400 | 198 | PASS (Wilson 95% [0.4463, 0.5438] includes 0.5) |
| Balanced four-cell | 400 | 200 | PASS (exactly 100 in each (B,S) cell) |

All five intentionally invalid-write cases were rejected. The source receipt
reports 1,600 unique accepted synthetic rows, correct replay, and an intact
hash chain.

**Critical status limit:** The source receipt explicitly says
`BLOCKED_NO_PINNED_SANDBOX_IMAGE_DIGEST`. No authenticated pinned-image
qualification run is included in this imported bundle. Prior prose claiming a
fully qualified OCI-image Phase 0 is **not supported by these source files**.
Do not silently convert this local PASS into formal qualification.

## Recover the historical ledger (no model calls, no network)

From this directory, in a clean Python 3 installation using only the standard
library:

```sh
python3 phase0/rehydrate_ledger.py \
  --lock phase0/PHASE0_LOCK.json \
  --payload phase0/run_001/raw_ledger_times.json \
  --receipt phase0/run_001/PHASE0_RECEIPT.json \
  --output /tmp/acat-phase0-original-reconstructed.jsonl

sha256sum /tmp/acat-phase0-original-reconstructed.jsonl
# d1f8c2cbf135631ebea3fcbc969730c156d0bdf7ac101841cbaad82722bd72c5
```

The utility refuses to overwrite an existing output and verifies the
original ledger SHA-256 **before writing**. Use a fresh output path each time.
It records no new study outcomes.

The original frozen runner SHA-256:
`1060baec2aa7540e1b6c7375b3279ac5eeb572cfa483d3e418015b8036501be8`.

The pre-run lock SHA-256:
`161d5c573c556d3008ddf182e57343e5a674d0ddbb2cfb5dda2c77466c8d7358`.

Historical last hash-chain entry:
`4fb42928a988a63df5abb95e8b3253adcf134272c5956ad52a8057704c64fa0a`.

## Reproduction check

To verify the scorer against reconstructed rows (not a fresh experiment):

```sh
python3 - <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, 'phase0')
from phase0_trial import verify_ledger
count, last, groups = verify_ledger(
    Path('/tmp/acat-phase0-original-reconstructed.jsonl'))
assert count == 1600
assert last == '4fb42928a988a63df5abb95e8b3253adcf134272c5956ad52a8057704c64fa0a'
assert all(groups[k]['total'] == 400 for k in groups)
print('PASS: original synthetic ledger replays')
PY
```

## Governance and next gate

This is **an archival evidence import for review**, not admission, not an
amendment to the frozen plan, and not a model validation milestone.

1. Run the frozen Phase 0 protocol inside a **truly pinned, independently
   verifiable sandbox image**; record the actual image digest and new receipt
   in a separately dated, append-only artifact.
2. Only after formal qualification, run **Phase 1A** uninjected baseline on
   named, pinned real agents.
3. Lock N, recovery/false alarm rules, reporting bands and minimums for
   percent agreement, Cohen's kappa (bootstrap CI), and Gwet's AC1 after
   baseline and before injected Phase 1B.
4. Submit final preregistration to a timestamped registry and hash the exact
   registered bytes in a **new** `REGISTERED.md`. The template is not proof.

No public AI scores. No model-level, general-alignment, or broad
generalization claims.
