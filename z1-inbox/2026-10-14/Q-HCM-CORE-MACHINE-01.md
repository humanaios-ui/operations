# Candidate Block: Q-HCM-CORE-MACHINE-01 — HumanAIOS Core Machine v0.1 (PR #812), staged for the controlled ratification path

**Z1 Proposer:** Claude (AI agent)
**Date Submitted:** 2026-10-14
**Status:** AWAITING Z2 RATIFICATION (controlled path: `.z1-control/ratify.py`)

```yaml
candidate_id: "Q-HCM-CORE-MACHINE-01"
title: "HumanAIOS Core Machine v0.1: the Operations contract compiled to deterministic bytecode (issue #810, PR #812)"
author: "Z1 (Claude)"
proposed_at: "2026-10-14T00:00:00Z"
scope:
  - "tools/humanaios_core_machine_v0_1.py (HAIOS-TOOL-223: compiler, integrity-checking decoder, pure replay VM, JSON CLI)"
  - "tools/tests/test_humanaios_core_machine_v0_1.py (protected baseline coverage, registered in .tool-control/baseline_tests.yaml)"
  - "tools/verified_receipts.py + tests/test_verified_receipts.py (consumed/unconsumed receipt requirements, atomic consumption)"
  - "schemas/humanaios_core_machine_v0_1.schema.json (strict program/receipt schema)"
  - "docs/design/HUMANAIOS_CORE_MACHINE_V0_1.md (binary format and design specification)"
  - "tools-manifest.yaml / TOOLS_MANIFEST.md (tool registration)"
pinned_subject:
  pull_request: 812
  branch: "feat/810-humanaios-core-machine"
  head: "c49eabe14864a5209c70aa6b1d63032c86331189"
  tree: "c3e51373f730f4a7ce8f12b5b6e25aa4e2c0869c"
  prior_ratified_head: "7fc8211761cc6db7d304184bd9f4f9d6bc798760"
registered_record:
  file: "REGISTERED.md"
  entry: "Q-HCM-CORE-MACHINE-01"
  landed_on_main_by: "merge of PR #815 (merge commit 0c70f2022925ce03dcce3c337fc37de8487831ab, authored under a Z2 identity)"
  original_hash: "cb622b71c8a4b8e9b06d97b0b9e6bc1a588a423fe016349277192dbaabc6bd7f"
  repin_hash: "c0b9cc3566c61d8b54721474c8621302bb4d386f563dd9793a351be99603c77c"
resource_cost:
  cost:
    RAT-min: 5
    Z1-ktok: 10
    CI-min: 0
  dependencies: ["Q-CORE-CONCEPT-MAPPING-01", "Q-Z2-DUAL-AUTHORITY-GOVERNANCE-01", "Q-INTENT-OS-WITNESS-LEDGER-01"]
  blocking_on: []
impact_prediction:
  resource_impact: 0
  areas_affected: ["z1-inbox/INDEX.yaml", "Z1_INBOX_INDEX.md", "z1-inbox/2026-10-14/Z2_RULINGS_2026-10-14.md (written by ratify.py --apply)"]
  positive_outcomes:
    - "The HCM ratification gains a signature that .z1-control/validate.py enforces (indexed ruling file carrying the hash, ratifier drawn from KNOWN_RATIFIERS, ratified_at not before submission), on top of the convention-bound record already on main."
    - "ratify.py --verify will re-check this signature on every gate run, so a later edit to this candidate reads as a mismatch rather than passing silently."
  risk_factors:
    - "This block is a second record of one decision. It must not be read as a second decision: the governance decision was taken on 2026-10-12 and is recorded in REGISTERED.md. This path only authenticates it."
    - "ratify.py refuses a candidate that is not awaiting_z2, so the index entry for this block carries no signature fields. Z1 has not pre-filled any of them."
```

## Claim

- **claim:** The HumanAIOS Core Machine v0.1 in PR #812 is the machine-encoding layer of the Operations contract (`PIN_CONTEXT → OBSERVE → CLAIM → CHALLENGE → WARRANT → IMPORT_AUTHORITY → RECORD_ACTION → RECORD_OUTCOME → CLOSE / HALT`), and its preserved authority boundary is a ratified invariant: every replay result fixes `authority_effect=NONE`, `can_authorize=false`, `can_execute=false`, `merge_authority=false`, `authenticated=false`, `trust_anchor_authentication=EXTERNAL_TO_VM`. The VM has no external-action handler; comments, claims, CI success, evaluator output and warrants are not authorization; a comment alone cannot satisfy `IMPORT_AUTHORITY`.
- **what this block is:** the same candidate that `REGISTERED.md` already carries as `Q-HCM-CORE-MACHINE-01` (ratified 2026-10-12 on direct Z2 instruction; re-pinned to PR #812 head `c49eabe1`; landed on `main` by Z2's merge of PR #815), re-staged as an indexed z1-inbox candidate so that Z2 can bind the decision through the controlled path that `.z1-control/validate.py` enforces. The REGISTERED.md record binds by governance convention and precedent (the Layer 4 and Layer 0 records were bound the same way). This path adds the stronger, mechanically checked binding. It changes nothing about what was ratified.
- **evidence_tier:** VERIFIED-LIVE at head `c49eabe1`, re-run by Z1 in a detached checkout: focused HCM suite 50 passed; receipt resolver suite 17 passed; Layer 0 tier-1 suite 40 passed; `ruff check --select E9,F63,F7,F82` clean; `TOOLS_MANIFEST.md` in sync; the six authority-boundary values present verbatim in the replay-result constructor. File digests at that tree: `tools/humanaios_core_machine_v0_1.py` `ee537d72e98b2e78e6c95a30947695db2df04821eb36fbc88b08152f3c5b31cd` · `tools/tests/test_humanaios_core_machine_v0_1.py` `3ff197d8` (prefix; full digest in the REGISTERED.md re-pin addendum) · `tools/verified_receipts.py` `c82d84ea6bbfcb6bc76fbf3b96a65e35edb9d564ae4486414118b8049b980ae1` · `docs/design/HUMANAIOS_CORE_MACHINE_V0_1.md` `1f92be767c95fc347ec4466b1237fd2d6cfe830ec7bb8aa0a92592f74761275c` · `schemas/humanaios_core_machine_v0_1.schema.json` `d0976b10bf9477c06697a83ec08ccc1f2db8573fc0a53f119f5310e79b4b6e13`. Repository Coordinator admission for PR #812 reads PASS / ACTIVE at that head (run 38632970018, admission routing only).
- **what Z2 signs here:** the bytes of this file, through

  ```text
  python3 .z1-control/ratify.py Q-HCM-CORE-MACHINE-01 --decision ACCEPT --by Night --apply
  python3 .z1-control/render.py
  python3 .z1-control/validate.py
  ```

  run by Z2 and committed by Z2. The tool computes `sha256(candidate | by=Night | at=<date> | decision=ACCEPT)` over this file, appends the ruling to `z1-inbox/<date>/Z2_RULINGS_<date>.md`, sets this index entry to `ratified` with `ratified_by`, `ratified_at`, `z2_ruling` and `z2_hash`, indexes the ruling file under `records:`, and recomputes `counts:`. Z1 does none of those steps. The commit author is the signature's provenance.

## Falsifier

This candidate is FALSE if any of the following is observed:

1. Any of the PR's own falsifiers, adopted here as the candidate's: a protected test shows modified bytecode passing integrity verification; missing or disputed evidence or an open challenge forming a warrant; a stale, comment-based or non-exact-head authority import being accepted; altered evidence reusing an authorization; a one-time receipt consumed twice; action or outcome recording bypassing its receipt binding; the VM performing an external action; or any replay output gaining authorization, execution or merge authority (any of the six boundary values above drifting from the fixed ones).
2. The focused HCM suite or the receipt resolver suite failing at head `c49eabe1`, or any of the five file digests listed above failing to reproduce at that head.
3. `python3 .z1-control/ratify.py --verify` reporting a mismatch for `Q-HCM-CORE-MACHINE-01` after Z2 signs it, which would mean this file was edited after ratification.
4. The REGISTERED.md record of `Q-HCM-CORE-MACHINE-01` on `main` and this block disagreeing on the pinned head, the ratified decision, or the six authority-boundary values.

## Proposed Z2 actions (accept, edit, or reject individually)

1. Sign this candidate through the controlled path (the three commands above) and commit the result under a Z2 identity. This is authentication path (b) named in PR #815's record; path (a), the Z2 merge of PR #815, is already done.
2. Nothing else. The authenticated `APPROVED` review on PR #812's exact head `c49eabe1` and the merge of #812 are separate Z2 acts that this block does not request and cannot perform.

## Z2 Decision Gate

- [ ] ACCEPT — run `ratify.py … --decision ACCEPT --by Night --apply`, render, validate, commit
- [ ] EDIT — propose changes (reply in thread); EDIT through the same tool records `edit_requested`
- [ ] REJECT — reason (reply in thread); REJECT through the same tool records `rejected`

**Awaiting Z2 ratification by:** 2026-10-16 (48h window)

---

*Generated by Claude (Z1) for Z2 (Night) ratification*
