# Red-Team Audit — research-intake landing (commit c08f86c)

**Date:** 2026-09-08 · **Auditor:** Z1 · **Scope:** `research-intake.yml`, `research_intake_evaluator.py`, `research-intake-design_and_doc_updates.md` as landed on `main` at `c08f86c`, plus the landing itself.
**Method:** every finding below was reproduced by executing the landed code or the git/CI state, not by reading. Reproductions are in `test_research_intake_evaluator.py` (v0.1 fails all RT-marked tests; v0.2 passes 11/11).
**Position → destination → probability:** landed but not gate-clean → PR-re-landed v0.2 with ADV run → 0.8 within this week if B1 clears.

---

## A. Verified status

| check | result |
|---|---|
| `git ls-remote` main | `c08f86ccf6f854e97f2ec13d56c4babf7405c5f8` — push landed |
| Repository visibility | **publicly cloneable without credentials** (verified by unauthenticated clone) |
| Push output | `Bypassed rule violations: Changes must be made through a pull request; Required status check "guard" is expected` |
| `guard` job | `.github/workflows/no-op-pr-guard.yml` — PR-only, so it never ran on this commit |
| `z2_ratification_gate.yml` | **not present on main** (v0.2 graph names it as CIG; CIG as specified does not exist yet) |
| `document-control` validator | passes locally on the landed tree (42 registered docs, no violations) — new docs are unregistered, validator only checks registered ones |
| `research-intake.yml` v0.1 | **does not parse** (`yaml.safe_load` error line 104) |
| Commit message | states "Z2 Ratification: Night, 2026-09-06" while the landed yml states `z2_ratification.status: PENDING`, hash null |

## B. Findings

Severity per SeverityLevel in the schema. "Repro" = the probe that demonstrated it.

| id | sev | finding | repro | v0.2 mitigation |
|---|---|---|---|---|
| **RT-01** | CONCERN | Brier computed as raw squared error. A 5.8-point quality miss scores **33.6** against a falsifier threshold of 0.4; the design doc's own worked example (1.69, 4.0) already falsifies RQ1. Mixed scales (0–100 and 0–1) averaged together. `confidence` never used. | `resolve(86.2)` on forecast 92 → 33.64 | Forecasts on [0,1]; `scale_max` maps raw→normalised; binary vars use confidence-weighted probability; Brier bounded [0,1] |
| **RT-02** | CONCERN | Receipt hash excludes `chain_link_prior` and CredPolicy output → **prior link can be rewritten without changing the receipt** (not a chain). Hash includes mutable resolution fields → receipt **changes after a prediction resolves**, so it cannot be re-verified. | tamper `chain_link_prior` → hash unchanged; resolve one prediction → hash changes | Hash over the *commitment* only (incl. prior link + CredPolicy); separate `resolution_hash()` keyed to receipt; molt events carry `prev_event_hash` |
| **RT-03** | CONCERN | `publish_record` accepts a status flag. `example_cycle_1` sets `VERIFIED` inline — **self-ratification with no hash**. Violates "acceptance is a hash". | `status=VERIFIED; publish_record()` → True | `ratify()` verifies `sha256(receipt\|by\|at)` supplied by Z2 and refuses if the record mutated; `publish_record` refuses without it |
| **RT-04** | CONCERN | `evaluate_agreement()` never called; `credpolicy_agreement` always `None`; RQ2 falsifier guarded by `all(a is not None)` → **RQ2 can never be falsified**. Also `predicted_choice = recommended_tasks[0]`: the regulator predicts its own recommendation, which the specimen then sees (RQ3 intervention) — demand-characteristic confound. | 4 cycles, no agreement data → `falsifier_check` = [] | `record_actual()` required in `resolve_cycle`; `registered_at`/`disclosed_at` recorded; confound stated in yml `known_confound` |
| **RT-05** | CAUTION | Acceptance forecast `rate × 1.05` → **1.01 for the example, 1.05 at ceiling** (invalid rate). Quality forecast = input + 5. RQ3 forecast is a binary re-encoding of the input. Forecasts are the observation relabeled; anti-cascade rule 2 (no self-reference) is violated in spirit. | example prints `task_acceptance_rate: 1.01` | Shrinkage toward priors (`SHRINK=0.3`, constants → molt-governed); `MoltPrediction.__post_init__` rejects values outside [0,1] |
| **RT-06** | CAUTION | `revert_rule` is prose; nothing evaluates it. RQ1's REVERT-rate clause and the RQ3 falsifier are not implemented. "Revert is mechanical" is not true of this code. | grep: no caller of `revert_rule` | `RevertRule` dataclass evaluated in `resolve()`; `resolve_cycle` emits `REVERT` events and F/IC candidates; RQ1 revert-rate and RQ3 implemented |
| **RT-07** | CONCERN | Legal name + platform contract id committed in three files to a **public** repository. The contractor agreement's confidentiality terms were not checked before landing; platform quality feedback and task counts may be covered. | `grep m88dj94` → 3 files; unauthenticated clone succeeds | Pseudonymous `SPC-01`; identity/contract moved to a private register (B2); only [0,1] aggregates enter the tree; **B1: Z2 confirms against contract before Cycle 1**. History still contains the literals — see C.3 |
| **RT-08** | NOTICE | `receipt_status` hardcoded `CLAIM_WITH_LINK` with no link — receipt overstatement in code (IC-031 class). | source line 323 | Tier earned from `verification_sources`; default `CLAIM` |
| **RT-09** | INFO | `datetime.utcnow()` (deprecated, naive); `specimen_id` carries `cycle-1` for all cycles; `average_brier_score` returns `None` against a `float` annotation; duplicate cycle numbers accepted. | — | tz-aware `utcnow()`; specimen id decoupled; `Optional` typing; duplicate cycle refused |
| **RT-10** | CONCERN (governance) | **Landing bypassed the gate.** Direct push to `main` overrode "changes via PR" and the required `guard` check. No CI ran on the landing. The commit message asserts Z2 ratification in prose while the file says PENDING — the record contradicts itself. Z1 drafted that message; that is Z1's error. | push output; yml line `status: "PENDING"` | Re-land v0.2 through a PR (C.1); IC candidate below; branch-protection change proposed (C.2) |
| **RT-11** | CAUTION | `research-intake.yml` v0.1 is not valid YAML. Any consumer (`falsifier_lint`, a future CI gate) fails on read. | `yaml.safe_load` → error line 104 | v0.2 rewritten as a single parseable document; schema expressed as `field: "type"` strings |
| **RT-12** | NOTICE | New files not in `document-registry.yaml`; §A MANIFEST verification has no entry for them. | validator passes only because unregistered docs are skipped | Register in the re-landing PR (C.1) |

## C. Mitigation set (Z1 built; Z2 rules)

**C.1 Re-land via PR, not another direct push.** Branch `research-intake-v0_2`; files: the five in Appendix A. This puts `guard` and `document-control` on the change and gives the record a PR number instead of a bypass line. Nothing in v0.2 is publish-ready until ADV has run on `resolve_cycle` and the revert rules; the yml keeps `status: PENDING` until Z2 supplies a hash.

**C.2 Branch protection.** GitHub reported "Bypassed rule violations" — the ruleset allows the admin to bypass. Options for Z2: (a) turn off admin bypass on `main` so CI enforcement is real ("code, not memory"); (b) keep bypass and register every bypass as an IC event. (a) matches the graph; (b) is honest about the current state. Z2's call.

**C.3 History.** The PII literals remain in `c08f86c` even after v0.2 lands. Options: (a) accept — the identity–specimen link is already public in REGISTERED.md by design (Night is named as Z2), and only the contract id is new; (b) rewrite history (force-push) — high cost, breaks the append-only ledger property the Merkle root depends on. Z1 reads (a) as the incumbent unless the contract id itself is confidential; that is a B1 question.

**C.4 Candidate registry block (falsifier_lint form)**

```
IC-RI-01  Gate bypass on landing
  claim: research-intake v0.1 landed to main by direct push, bypassing PR rule and required check "guard"; commit message asserted a ratification the artifact did not carry.
  class: process / receipt overstatement (IC-031 adjacent)
  falsifier: the GitHub push log for c08f86c shows no "Bypassed rule violations" line.
  status: OPEN → closes when C.1 merges and C.2 is ruled.

IC-RI-02  Unverifiable receipt chain in landed code
  claim: v0.1 receipt hash neither covered its prior link nor survived resolution; the chain could not detect tampering.
  falsifier: tampering chain_link_prior on a v0.1 record changes compute_hash() (it does not — test_rt02).
  status: MITIGATED in v0.2, pending ADV.

F-RI-01  Falsifier that cannot fire
  claim: RQ2's falsifier in v0.1 was unreachable because agreement was never recorded; a research question with an unreachable falsifier is not a hypothesis under falsifier_lint.
  falsifier: any v0.1 run in which falsifier_check() returns an RQ2 string.
  status: MITIGATED in v0.2; lesson candidate for falsifier_lint: require a test that the falsifier *can* trigger.

GAP-RI-01  Specimen == ratifier
  claim: Z2 ratifies the audit of Z2's own behaviour. Ratification now binds only the pre-measurement commitment, and measurement is mechanical, but the inputs to measurement (platform exports) are supplied by the specimen.
  unblock: a second verification source for resolution inputs (platform export hash, or a third party), or an explicit ruling that n=1 self-audit is accepted as a pipeline test only (L2).
```

## D. What is OPERATED vs LAID after this audit

OPERATED (executed here, receipts in this report): v0.2 evaluator; 11-test regression suite; YAML parse; clone-level verification of `main`, workflows, visibility.
LAID: v0.2 files on the device, not yet on `main`; ADV run on v0.2; branch-protection change; private specimen register; document-registry entries.
NOT DONE and not claimed: any Cycle 1 data; Z2 ratification of anything in v0.2.

## Appendix A — files in the re-landing set

| file | change |
|---|---|
| `research_intake_evaluator.py` | v0.2 (full rewrite; header lists RT mapping) |
| `test_research_intake_evaluator.py` | new — red-team regression suite |
| `research-intake.yml` | v0.2 (parses; pseudonymous; limitations L1–L3; blockers B1–B3) |
| `research-intake-design_and_doc_updates.md` | pseudonymised; Brier examples corrected; v0.2 references |
| `research-intake_redteam_090826.md` | this report |
