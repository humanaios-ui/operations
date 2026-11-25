# ACAT-R v0.1 — First Real, Owned Machine-Runtime Pilot

**Machine runtimes exercised:** actual host CPython interpreter in isolated child processes, native SQLite extension via `sqlite3`, SQLite in-memory database operations. These are **real processes**, not synthetic output fixtures. We intentionally plant three bugs in the **owned application wrapper**, then correct that wrapper. This does **not** mean Python or SQLite is defective, and does not test DASE.

## What a pass proves

ACAT-R's offline evaluator accepts genuine child-process data and: (1) commits the original baseline before challenges; (2) measures source-backed reference violations; (3) distinguishes bad success from explicit refusal; (4) reports observed correction and preserved controls; (5) refuses to claim independent evidence or admission.

## What a pass does not prove

It does not show general runtime calibration accuracy, hardware-specific performance, proof of an independent observer, chronological proof by an external witness, independent reference validation, root-cause certainty for a real-world incident, DASE source correctness, or metrological traceability. The same operator controls scripts, references, and capture. P1 hash commit is local-only. **EVIDENCE STATE = UNVERIFIED_RUNTIME_OBSERVATIONS.**

## Bounded and explicit run

From repository root, only on a machine you control:

```sh
python3 -m unittest discover -s tests -p 'test_acat_r_v01.py' -v
python3 -m unittest discover -s tests -p 'test_acat_r_live.py' -v
python3 experiments/acat_r_v01/live_pilot/collect_live.py --run-owned --output-dir /tmp/acat-r-owned-capture-01
python3 experiments/acat_r_v01/live_pilot/verify_live.py --replay-owned --evidence-dir /tmp/acat-r-owned-capture-01
```

The collection script accepts **no arbitrary executable, command or external inputs**. It runs two fixed repository-owned sources via `[sys.executable, '-I', '-S', script]`, 6-second child timeouts, no shell, no network calls, no disk SQLite database, no credentials, no remote service. The process is not confined by an OS-level sandbox; use a disposable local runner. Never use this tool on third-party binaries without new approval, sandbox controls and permission.

## Pre-registered cases and references

| Case | P1 real input | P2 real challenge | Expected P3 correction |
|---|---|---|---|
| `sqlite-atomicity` | Transfer 10 from account A to B; total invariant 100 | Inject missing-table error between updates | Explicit `BEGIN`/`ROLLBACK` restores total=100 |
| `numeric-string` | JSON numeric `2.5` accepted | String `"2.5"` must be refused | Strict type gate refuses |
| `nan-string` | JSON numeric `5.0` accepted | String `"NaN"` must be refused | Strict finite gate refuses |
| `sqlite-unique` | Insert unique `B`; count 2 | Duplicate `A` must be refused | Remains refused in both versions |

P1 and P2 use the **same source+runtime fingerprint**. P3 changes the **owned wrapper source only**, retaining the interpreter and SQLite library. Reference conservation and schema rules are defined before collecting P1. Every real invocation records stdin and stdout hashes, exit code, raw stdout and the pinned source fingerprint. Local replay launches another 12 actual child processes and checks raw receipts against newly captured results. No cryptographic signature or remote witness.

**Falsifiers:** uncommitted P1 change, altered source or raw stdout, missing per-case receipts, empty refusal reason, nonfinite output represented as success, numeric string coercion, SQLite balance loss, regression of the accepted UNIQUE refusal, contradictory artifact hashes, or outcome authorization escalation.

**Expected controlled outcome, not a discovered defect:** P1 4/4, P2 1/4, P3 4/4; three planted wrapper failures corrected; zero regressions. This is a demonstration of test sensitivity **under constructed defects**, not a population performance estimate or false-positive rate.

**Evidence distribution limit:** The detailed raw JSON receipts live in a **separate downloadable conversation evidence package**, not under this GitHub source tree. The in-repo `PROOF_RECEIPT_LOCAL.json` is a provisional summary; no current in-tree GitHub CI check authenticates its `evidence_sha256`, and the `verify_live.py` checker needs the separately provided evidence directory to check raw receipt digests. A bare summary without that directory cannot establish original observation authenticity.

**Replay portability limit:** `verify_live.py` compares the evidence's source, CPython interpreter, and native SQLite extension hashes against the **current host** through `runtime_manifest(...)`. A different Python interpreter build, SQLite extension build, or operating system will normally reject the original evidence **before replay**. On a different host, run `collect_live.py --run-owned` to create *new* separately labeled receipts on that host rather than rebranding them as a byte-for-byte historical replay. Its fresh outputs can still be compared against the four-case reference results. A separately authenticated independent reviewer and independently held raw evidence are needed before admission.
