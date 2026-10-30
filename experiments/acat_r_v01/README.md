# ACAT-R v0.1 — General Runtime Calibration (Z1 research)

**Status:** research prototype; **authority effect: NONE**. ACAT-R is a new experimental extension of the three-phase ACAT method, **not** an administration of the original AI self-report instrument. No original ACAT Learning Index (LI), SAG, corpus row, or score is produced. No DASE software was tested.

## What this does

The **core evaluator** accepts a **declared reference protocol** and three sets of **pre-collected, exact-input-linked runtime observations**. Its job is to measure agreement with bounded reference oracles, structured refusal under challenge, and replay results after an attempted correction. It never launches a target binary, contacts a network endpoint, changes machine settings, or authorizes a deployment.

- **P1 — Baseline:** assess the original runtime on a valid input. First `commit` the *exact bytes* of the P1 observation file and protocol.
- **P2 — Challenge:** assess the *same pinned artifact* on a specified invalid/stress input. The phase must reference the challenge input hash.
- **P3 — Challenge replay:** assess the same challenge input after proposed correction or environmental recovery; P3's artifact hash records whether the binary reportedly changed.

Checks include schema strictness, duplicate JSON keys, nonfinite numeric tokens or nonfinite strings in successful results, numeric strings in numeric output paths, boolean-as-numeric confusion, contradictory status flags, negative controls that must return an explicit reason, missing cases, input hashes, and P1 protocol/byte commitment mismatches.

## Safe command line demo

From repository root:

```sh
python3 -m unittest discover -s tests -p 'test_acat_r_v01.py' -v
python3 experiments/acat_r_v01/calibrate.py commit \
  --protocol experiments/acat_r_v01/examples/protocol.json \
  --p1 experiments/acat_r_v01/examples/p1.json \
  --output /tmp/acat-r-demo-commit.json
python3 experiments/acat_r_v01/calibrate.py evaluate \
  --protocol experiments/acat_r_v01/examples/protocol.json \
  --p1 experiments/acat_r_v01/examples/p1.json \
  --p2 experiments/acat_r_v01/examples/p2.json \
  --p3 experiments/acat_r_v01/examples/p3.json \
  --commit /tmp/acat-r-demo-commit.json \
  --output /tmp/acat-r-demo-report.json
```

The example is **fully synthetic**: two cases (queue overload; declared sphere versus cylinder mesh). Scripted P1 passes 2/2, P2 passes 1/2, P3 passes 2/2; challenge-replay gain is +0.5. These are *constructed fixtures*, not runtime measurements. `commit` / `evaluate` refuse to overwrite existing files; use a fresh destination each time.

## Protocol and observation contract

`protocol.json` has `schema`, `system_id`, `provenance`, and 1–100 `cases`. Each case has a unique `id`, `baseline_input`, `challenge_input`, `reference_id`, `baseline_oracle`, and `challenge_oracle`. Oracles are `numeric` (dot-path, finite expected number, nonnegative `atol` and `rtol`), `exact` (type-sensitive scalar), or `refusal` (requires `ok: false` and nonempty `reason`). Reference identifiers are **declarations**, not source authentication.

Each phase observation document must carry `schema`, `phase`, `system_id`, `artifact_sha256`, `capture_class`, and exactly one `observations` element per case. Each element binds `case_id`, `input_sha256`, `response`, and a nonempty `evidence_ref`. `P1` binds the baseline input; both `P2` and `P3` bind the exact same challenge input. `P1` and `P2` must declare the same artifact SHA; `P3` may name a changed artifact.

Allowed capture classes are `SYNTHETIC`, `SELF_REPORTED`, and `INDEPENDENT_CAPTURE_CLAIM`. **All are unverified** within this evaluator. To claim authenticated source truth, an external independent capture/witness protocol is required. Local SHA-256 receipts prove byte equality **only against a previously trusted independent copy**; the tool alone cannot prove capture order, authorship, causality, or immutable history.

## Measures (not original ACAT metrics)

`passes.P1`, `passes.P2`, and `passes.P3` count oracle agreements in each phase. `recovered_cases` counts cases failing P2 but passing P3; `regressed_cases` counts the inverse. `challenge_replay_gain = (P3 passes - P2 passes) / number_of_cases` is a **new experimental descriptive statistic**. A positive number does not prove the patch caused recovery, because there is no independent randomization, control, or repeated-runtime trial here. It is **not** LI or a validated calibration score.

## Safety and integration gates

- Core evaluator: input data **only**; no subprocess, shell, privileged operations, automatic patches, vendor scraping, or network calls.
- **Separate opt-in, owned-only pilot** at `live_pilot/collect_live.py` launches 12 controlled local CPython/SQLite child processes with no shell or network calls. It never accepts an arbitrary command, external binary, or target URL. This is executable research and is not an OS-level sandbox.
- Do **not** put synthetic observations in ACAT behavioral corpus tables or use them as external certification.
- Remain distinct from DASE AEC issue #803 and capability-R2 verification issue #1067. Those remain blocked until authorized code and real evidence exist.
- PR review should check the oracle's independence, version-pinned real input adapters, false-positive and false-negative rates, host isolation, CI exact-head checks, and an independent reviewer.
- **No admission, merge, deployment, external executable execution, or third-party calibration is authorized by this prototype.** Human approval and the repository's existing Coordinator gate remain separate requirements.

## Falsification criteria

1. Any missing/duplicate phase observation, uncommitted P1, or changed challenge input is accepted.
2. A numeric string, nonfinite result, contradictory status, or crash is counted as valid numerical output or valid refusal.
3. Synthetic observations or self-reported output cause a `VERIFIED`, `ADMITTED`, or `can_authorize: true` status.
4. Repeating the same evaluation over identical files changes report bytes.
5. A corrected artifact produces a worse P3 result without being reported as a regression.

These are contract-level acceptance criteria, **not** a general calibration accuracy claim.

## Observed owned-runtime pilot

See [`live_pilot/README.md`](live_pilot/README.md) and the locally captured, self-reported evidence bundle. We actually ran CPython child processes executing in-memory SQLite through deliberately flawed and repaired **owned application code**: baseline P1=4/4, challenge P2=1/4, corrected replay P3=4/4; three injected wrapper faults detected and resolved, zero regressions. Another 12 live child processes reproduced the recorded responses. The original ACAT-R CLI does not launch them; the separate opt-in collector does. This is **not** a demonstration of faults in SQLite or CPython, and it is **not** an independent witness. The original ACAT-R corpus remains unchanged, and the system keeps the evidence state `UNVERIFIED_RUNTIME_OBSERVATIONS` and admission HOLD.

Local test matrix: 30 offline evaluator tests and 8 live-process tests. Future work: capture an operator-controlled non-injected workload through an independent witness and compare incremental defect detection against ordinary unit tests at equal false-positive rates.
