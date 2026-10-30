# ACAT-R next milestone — existing, non-injected runtime workload

**Objective:** Test a real, *unchanged* HumanAIOS runtime against a separately implemented, publicly reviewable reference contract, using GitHub-sourced operational metadata and no artificially broken functions.

## What is actually measured

The system under test is **existing** `humanaios-funding-pipeline/resource-miner/resource_miner/on_track_reflex.py` at operations commit `52aa7c0ed70f6e24ec050d0d56788a791e5f78f7`. Its Git blob SHA-1 is pinned to `25bcb7d1be105d4e7869f9b918436eac430e2709`; the loader fails if the file has changed. It is launched as a fresh Python process each phase using its existing `--input` / `--json-out` CLI. The process runs real classification and aggregation code, not a mock or wrapper around a fake answer.

The workload is a convenience sample of **23 actual repository issues and one pull request** retrieved through the authenticated connected GitHub tools. It includes open and closed issues, anchor issues #822 and #928, an actual PR #1069, and two labeled issues. A *minimized* source projection stores issue title, issue state, labels, first nonempty body line, and all explicit `on_track_target:` lines found in the actual bodies. It does **not** copy full potentially sensitive issue bodies. Original live API snapshots are **not** preserved or cryptographically attested; provenance is weaker than an independently signed raw API receipt. The input is not an exhaustive issue inventory and must not be used to infer current outcomes or complete status.

A second program, `reference_oracle.py`, is an **independent implementation of a documented functional contract**, not a call to, or import of, the system under test. Its reference truth is deliberately narrow: only #822 and #928 are fixed product anchors; an explicit first-line target marker may establish a declaration, but never a verified result; labels may indicate risk; issue closure and PR creation do not prove deployed usability.

## ACAT-R protocol adaptation

- **P1:** Commit source Git blob, full snapshot SHA-256, and a subset of **8 real records**; execute unchanged On-Track CLI. Verify 8/8 against independently implemented per-record reference fields.
- **P2:** Challenge with a **larger, heterogeneous set of 24 actual records**, still with no code or record fault injection. Verify 24/24 against the reference; verify no fabricated `VERIFIED` state or admission/merge authority.
- **P3:** Re-execute exactly the same P2 input on exactly the same original code. Require identical output bytes and another 24/24 reference matches. **No correction is expected or claimed**; a nonzero gain would indicate protocol drift.

This is a **non-injected functional-conformance and reproducibility experiment**, not a metrological calibration of sensor outputs and not a certified calibration process. The reference does not come from an independent external testing laboratory; it is independent code written by the same investigator. Running on a GitHub runner also does not constitute independent third-party scientific review.

## Local reproduction, when whole operations tree is available

```sh
python -m unittest discover -s tests -p 'test_noninjected_oracle.py' -v
python experiments/acat_r_noninjected/run_real_workload.py \
  --source humanaios-funding-pipeline/resource-miner/resource_miner/on_track_reflex.py \
  --fixture experiments/acat_r_noninjected/pinned_issue_snapshot.json \
  --output /tmp/acat-r-existing-proof.json
```

The source fingerprint is mandatory. Do not replace it with a copied or rewritten version to make the experiment pass. The report must remain `authority_effect=NONE`, `can_authorize=false`, and `admission=HOLD`. For real source truth / generalization, conduct another pilot with independent human-reviewed references and different runtime families. No database write, deployment, human admission, or third-party proprietary software execution occurs here.
