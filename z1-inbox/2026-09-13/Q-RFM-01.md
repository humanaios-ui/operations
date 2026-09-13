# Candidate Block: Q-RFM-01 — REGISTERED.md Failure-Mode Map & Scanner

**Z1 Proposer:** Claude (AI agent)
**Date Submitted:** 2026-09-13
**Pinned SHA:** `1e1b5189f6ae657c3b1a666eb5b52194327e0b63`
**Branch:** `claude/registered-failure-modes-tm16ge`
**Phase:** 0/1 (control infrastructure)
**Status:** AWAITING Z2 RATIFICATION

---

## §A Position · Destination · Probability

**Position:** `REGISTERED.md` pinned at `1e1b518` — 3,948 lines, 131 entries, append-only, `Status: LIVE`. `grep -rIn "FMEA"` returns zero repo-wide. The registry catalogues failure modes of substrates and sessions; it has never been turned on itself.

**Destination:** A ratified failure-mode vocabulary for the registry (`RFM-01` … `RFM-19`), the standing orders derived from it, their mapping to industrial reliability terms, and an executable scanner that measures the registry against the taxonomy.

**Probability: 70%** that the taxonomy survives the falsifier window without needing a new RFM class. Reasoning: 11 of 19 modes were derived *from* measured defects rather than imagined, which biases toward completeness on the STRUCTURE and RECONCILE axes. The READ and GOVERN axes are the exposure — those modes are `UNMEASURED`, and a session-behaviour failure mode not yet observed could require a new class. 70% rather than higher because the taxonomy has been tested against exactly one file at one SHA.

---

## The finding that motivated the work

`SESSION_RITUALS.md:57` asks each session to *"predict 3-8 failure modes you may exhibit."* `RECURSIVE_IMPROVEMENT_SEED.md:128` already records why that does not work: *"there is no gate that checks whether the catalog was comprehensive or whether materialized drifts were missed. The catalog is generated to justify a humility score, not to actually measure drift."*

The registry asks every session to predict its own failure modes, and has never enumerated its own.

---

## What was built

1. **`REGISTERED_FAILURE_MODES.md`** — the three-column map. 19 registry failure modes, 14 standing orders derived from them, industrial classification for each. All counts tool-generated.
2. **`tools/registered_failure_mode_scan_v0_1.py`** — 11 checks, `collect()`/`evaluate()` split, self-test against synthetic fixtures. Advisory by default.

---

## §Live result — this candidate was measured by its own mechanism

Entry-level, 131 entries × 4 checks:

| Check | RFM | Defects | Conformance |
|:---|:---|:---|:---|
| Ordering | RFM-09 | 29/131 | 77.9% |
| Required fields | RFM-06 | 8/131 | 93.9% |
| Fence form | RFM-07 | 4/131 | 96.9% |
| Quote hygiene | RFM-08 | 3/131 | 97.7% |

**44 defects / 524 opportunities → 91.6% FPY → 83,969 DPMO → ~2.9σ**, same methodology as `audits/T1_DEFECT_BASELINE_S070726.md`, which designated `operations` the *"clean reference bar (0/7)."* At entry level it is not clean.

File-level: 10/45 F-entries absent from the quick index · 25 entries past the `## Changelog` · 1 orphan roll-up row (IC-036) · 3 of 6 ratified classes empty · 2 cross-artifact ratification contradictions.

---

## Gates verified to actually fail

Each evaluator was run against a synthetic known-bad fixture and asserted to detect it — 22 assertions, `self-test` passes. This is the gauge R&R step, and it is not decorative: **the scanner's first version was wrong.** It scored ordering at 28/131 by silently skipping non-F/IC/H entries, where `REGISTRY_SPEC.md:114` declares *"F-class, then IC-class, then H-class, then other classes"* — making `Z2-ASSESS-01` inside the H block a violation, not an exemption. Reconciliation against an independent count caught it; corrected to 29.

Two assertions specifically guard against false positives: the F-32/F-33 honest-gap whitelist must suppress them, **and** a non-whitelisted phantom must still be caught. `audits/T2_ANALYZE_S070726.md` records a regex bug that manufactured five false defects (IC-037 + IC-034); an instrument that only over-reports is not safer than one that under-reports.

---

## Registrable items surfaced (routed, not self-registered)

Z1 proposes; Z2 numbers and appends, per G-4 / IC-030.

| Candidate | Claim | Evidence |
|:---|:---|:---|
| **IC-CAND-A** | Ratification hash is a git commit SHA where a decision signature is specified | `REGISTERED.md:3925` = `e8a501f` (7 hex); `CLAUDE.md` routing step 6 and `NF_LEDGER_SCHEMA_v1.md` specify `sha256(candidate \| by \| at \| decision)` = 64 hex. Proves when code landed, not what was approved |
| **IC-CAND-B** | `PRIORITY_QUEUE.md` contradicts itself on its own ratification state | `:11` reads *"pending Z2 signature"*; its own `## Appended Events` reads *"PRIORITY_QUEUE.md v1_1 ratified"* |
| **IC-CAND-C** | IC roll-up cites IC-036, which has no body entry — IC-041 *audit-false-pass* genus | `REGISTERED.md:118` |
| **IC-CAND-D** | IC-052 and IC-053 number the same defect twice, defeating the Pareto's frequency signal | both "drift validator missing D-OVERCLAIM" |

**Held pending census resolution:** `tools/registered_findings_validator_v1_0.py` returns `Verdict: WARN`, exit 0, `✓ F-class ✓ H-class ✓ IC-class` while 8 entries are missing required fields it nominally checks. Stating that as a finding first requires establishing that the two instruments are counting the same entries — see Honest limitations.

---

## Falsifier

**Claim:** The RFM taxonomy is complete enough at the structural level that registry defects found over the next 30 days classify into an existing RFM, and the scanner's counts are reproducible by independent means.

**FALSE if any of:**
- A structural defect (READ/WRITE/STRUCTURE/RECONCILE axes) is found in `REGISTERED.md` that requires a **new** RFM class, ≥2 times within the window
- The scanner's entry-level defect count diverges from an independent manual count of the same file at the same SHA by >2 defects
- Any known-bad fixture in `self-test` stops being detected after a change to the scanner
- The scanner flags F-32 or F-33 as index defects (the documented honest gaps), i.e. the whitelist regresses
- Two runs of `scan` against the same SHA produce different counts

**Success criterion:** Through **2026-10-13**, running `scan` at each session open reproduces `44/524` on the unchanged file, every new defect classifies into RFM-01…RFM-19, and `self-test` passes on every invocation.

**Note on falsifiability scope:** the GOVERN-axis modes (RFM-18, RFM-19) are *not* falsifiable by this scanner — they assert the absence of a definition, which the scanner cannot measure. They are excluded from the claim above and stand or fall on Z2's reading.

---

## Honest limitations, named

1. **The census is unresolved.** `registered_findings_validator_v1_0.py` reports 130 entries (F=47, H=47, IC=36); `repo_health.py` reports 126 immune entries; this scanner reports 131 (F=45, IC=43, H=42, other=1). Three instruments disagree about how many entries the registry contains and what class they are. **This document does not assert which is right.** Its own numbers are therefore conditional on its parser being the correct one, which is exactly the assumption IC-037 punishes. Resolving this should precede citing either census as authoritative.
2. **Occurrence data exists for 11 of 19 modes.** The rest read `UNMEASURED` and are not scored. They are not thereby rare — they are unobserved.
3. **Severity is unscored for 18 of 19 modes,** because `REGISTRY_SPEC.md:45` requires IC entries be cost-classified and only IC-031 is. No RPN is computed anywhere. The FMEA table is mostly empty by design; filling it would manufacture the false precision IC-034 names.
4. **The scanner is advisory.** Shipping `--enforce` on would fail CI on 44 pre-existing defects; shipping it off indefinitely reproduces IC-050, the repo's own evidence that a warn-only gate is a defeated gate. This is named rather than resolved, because the resolution is Z2's.
5. **Not wired into CI,** deliberately. `findings-registry.yml` already runs a blocking registry validator; a second gate on the same paths could return contradictory verdicts before Z2 has ruled — particularly given limitation 1.
6. **One file, one SHA.** The taxonomy has been tested against `REGISTERED.md` at `1e1b518` and nothing else. Generality to the other 30 repos is asserted, not demonstrated.
7. **`REGISTERED.md` was not modified.** This work describes the registry; it does not touch it. No entry was added, renumbered or corrected.

---

## Deliverables

| Path | Kind |
|:---|:---|
| `REGISTERED_FAILURE_MODES.md` | root mapping doc |
| `tools/registered_failure_mode_scan_v0_1.py` | scanner, 11 checks, self-testing |
| `z1-inbox/2026-09-13/Q-RFM-01.md` | this candidate block |
| `PRIORITY_QUEUE.md` | `Q-RFM-01` row + appended event |

---

## Z2 Review Checklist

- [ ] Is the RFM taxonomy the right vocabulary, and is 19 the right granularity?
- [ ] Should `--enforce` be turned on, and if so before or after remediating the 44 defects?
- [ ] Should the scanner be wired into CI, given `findings-registry.yml` already runs a blocking validator?
- [ ] Which instrument's census is authoritative — 126, 130 or 131?
- [ ] Accept / edit / reject IC-CAND-A through IC-CAND-D; assign numbers if accepted
- [ ] Commission `Q-RFM-02` (cost-class taxonomy)? It is the blocker on every `UNSCORED` FMEA cell
- [ ] Is naval command vocabulary in Column 2 acceptable, or should the map stay in existing terms?

---

## Summary

The registry asks every session to predict its own failure modes and had never enumerated its own. This enumerates them — 19 modes, 11 measured — derives the standing order each implies, classifies each in industrial reliability terms, and ships the instrument that measures them.

The most useful output is not the defect count. It is the watch census: **0 MANNED · 9 ADVISORY · 5 UNMANNED**. Before this work it was 0 · 2 · 12. The dominant failure mode of `REGISTERED.md` is not any single defect; it is that almost nothing would have caught any of them.

**Ratification requested.**
