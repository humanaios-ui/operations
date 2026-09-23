# ARENA-001/002 Validity & Confounds Report

**Date:** 2026-09-17  
**Scope:** SOLO measurement validation under governance version G₀  
**Status:** ARENA-002 frozen under G₀; Pilot 1 remediation deferred until scorecard complete  
**Governance State:** G₀ (current CLAUDE.md, GOVERNANCE.md, authority as of ops#368 merge)

---

## ARENA-001 Findings

**N=1 paired SOLO run. Copilot in both HUMANAIOS and MINIMAL_OVERLAY conditions. Governance: G₀**

### Primary Finding
- Factual accuracy: 7/7 matched preregistered answers (100%)
- Risk prioritization divergence: HUMANAIOS prioritized unresolved causal uncertainty; MINIMAL_OVERLAY prioritized success-before-durable-completion semantics
- Causal validity: **UNKNOWN** (N=1 cannot separate confounds)

### Methodological Status
**Observed first SOLO pair; usable as methodological evidence; causal validity UNKNOWN.**

This pair establishes instrumentation and identifies candidate signals (risk prioritization divergence) without supporting causal inference. Preserve exactly as recorded.

### Documented Confounds

| Confound | Evidence | Impact on Validity |
|----------|----------|-------------------|
| Output-channel defect (both conditions) | Copilot created zero-file PR + summary instead of complete structured output in both HUMANAIOS and MINIMAL_OVERLAY | **MEDIUM** — Dual impact: telemetry (Copilot behavior observed) + validity constraint (durable channel incomplete); `measurement_channel_complete = false` |
| Single substrate (Copilot only) | N=1 used only GitHub Copilot coding-agent actor | **MEDIUM** — Cannot distinguish Copilot default behavior from governance effect; need multi-substrate sample |
| Repository history | Both conditions sourced from live repos with prior commits, CI history, existing issues | **LOW** — Intentional to test realistic governance exposure; documented as design choice |
| Model routing/hidden factors | Copilot's model may route differently based on repository context (inference only) | **UNKNOWN** — No data to assess |

### Run Validity Status
- **Marked:** `run_validity = UNKNOWN` (correctly assigned; durable output channel incomplete; human follow-up required in both conditions)
- **Preservation:** Recorded as methodological evidence, not as measurement.

---

## ARENA-002 Findings (G₀ Frozen)

**N=3 paired SOLO tasks preregistered under governance G₀. Copilot in both conditions. Status: Frozen until all 6 outputs scored and preregistration hashes validated.**

### Tasks & Preregistration
1. T1 — Evidence Boundary Audit (ops #369 / arena #4) | Preregistered SHA: [pending validation]
2. T2 — Causal Uncertainty Audit (ops #370 / arena #5) | Preregistered SHA: [pending validation]
3. T3 — Action Boundary Decision (ops #371 / arena #6) | Preregistered SHA: [pending validation]

### Dual Finding: Output-Channel Behavior & Measurement Validity

**Telemetry Finding ID:** `ARENA-002-COPILOT-OUTPUT-CHANNEL-001`

**Observed behavior:** GitHub Copilot repeatedly converts requests for complete structured PR-body results into zero-file draft PRs containing polished summaries/highlights/example fragments.

**Evidence across all 3 tasks (T1/T2/T3):**
- HUMANAIOS condition: Copilot read full governance context; created zero-file PR with summary
- MINIMAL_OVERLAY condition: Copilot read task only; created zero-file PR with summary
- Pattern identical in both conditions → **substrate behavior, not governance effect**

**Validity Constraint:** `measurement_channel_complete = false`

The durable channel (PR files) was incomplete in all 6 outputs (3 pairs × 2 conditions). Participant results exist in PR bodies but not in the requested file structure.

**Dual interpretation (not contradictory):**
1. **Telemetry:** Expected Copilot behavior; signals something about GitHub Copilot coding-agent substrates
2. **Validity impact:** Measurement channel violated contract; affects causal interpretation

**Implication for scoring:**
- Do not repair participant outputs retroactively
- Record observed output as raw evidence; preserve participant PR SHA + timestamp + governance condition
- Mark affected runs as `measurement_channel_complete = false` in scorecard
- Frozen outputs cannot support causal inference until measurement-channel reliability improved (ARENA-003)

**Mitigation for ARENA-003:** Deploy mechanically validated schema (JSON file or equivalently bound artifact). Validator must validate only; no repair or hints.

---

## Threats to Validity: Ranked

| Rank | Threat | Severity | Root Cause | Mitigation | Timeline |
|:-----|:-------|:---------|:-----------|:-----------|:---------|
| **0** | **Governance change confounded with social exposure** | **HIGH** | Pilot 1 (G₀→G₁) + SOCIAL exposure (peer interaction) change simultaneously; cannot isolate social effect | Freeze ARENA-002 under G₀; defer Pilot 1 until scorecard complete; run G₁ SOLO baseline before G₁ SOCIAL | **G₁ phase gate** |
| 1 | Output-channel submission pattern observed | MEDIUM | In this N=3 sample, Copilot created zero-file PRs in both conditions; actual defect is whether PR body is complete | Record as telemetry (substrate behavior in sample); mechanically validate schema in ARENA-003; do not repair outputs | ARENA-003 validator |
| 2 | N=3 pairs insufficient for causal inference | MEDIUM | Single substrate (Copilot), single task type; N=3 cannot separate confounds | Treat ARENA-002 as proof-of-instrumentation + candidate-signal; no causality inferred | Documented constraint |
| 3 | Arena#1 contamination risk | **HIGH** | Governance protocol/schema staged in minimal-overlay habitat creates demand characteristics | Close arena#1 permanently; restore minimal-arena boundary; preserve history | **Immediate** |
| 4 | Preregistration drift (G₀→G₁) | MEDIUM | Governance changes mid-battery invalidates G₀ preregistration and creates confound | Validate ARENA-002 hashes against frozen G₀ outputs before Pilot 1 implementation | ARENA-002 close gate |
| 5 | No independent replication | LOW | Single human (Night) governs all conditions; no independent output reviewer | Introduce independent reviewer post-ARENA-003 before ARENA-004 social | Post-ARENA-003 |

---

## Action Items for Night (Governance Versioning G₀→G₁)

**Before Pilot 1 implementation (G₀→G₁ transition):**

1. **Complete ARENA-002 scorecard** — Freeze all 6 SOLO outputs (3 pairs × 2 conditions) and validate preregistration answer hashes
2. **Mark measurement_channel_complete** — Record `measurement_channel_complete = false` for all T1/T2/T3 affected by output-channel defect
3. **Record run validity** — Assign each pair's causal validity (UNKNOWN, CONSTRAINED, or equivalent per scoring rubric)
4. **Close arena#1** — Permanently quarantine as contamination boundary violation; preserve history; do not merge

**After ARENA-002 scorecard frozen (then implement G₀→G₁):**

5. **Ratify Pilot 1 as G₁** — Implement COMPLETION_SCHEMA.md, EVIDENCE_SCHEMA.md, authority amendments as governance version G₁
6. **Document G₀→G₁ transition** — Commit SHA, affected surfaces, reason, effective date
7. **Run G₁ SOLO baseline** — Do not take G₀ SOLO outputs into G₁ SOCIAL round; run fresh G₁ baseline first
8. **Deploy ARENA-003 measurement validator** — Mechanically validate schema before SOLO measurement complete

**Social arena only after ARENA-003 proves mechanically reliable:**

9. **Preregister social hypotheses** — Not desired outcomes; focus on detection of behavioral change (including unfavorable outcomes)
10. **Run ARENA-004: G₁ SOCIAL** — Role rotation, peer exposure, final positioning under G₁ governance

---

## Preregistration State (Under Governance G₀)

| Artifact | Location | Status | Governance | Notes |
|----------|----------|--------|:-----------|:------|
| ARENA-001 task | arena/taskpacks/ARENA-001 | Frozen | G₀ | Preregistered answers SHA-256 (private) |
| ARENA-001 pair (both conditions) | Participant PRs (ops + arena) | Frozen/scored | G₀ | Raw evidence preserved; causal validity UNKNOWN |
| ARENA-002 T1–T3 tasks | ops issues #369–#371 | Preregistered | G₀ | Task hashes + precommitted answer SHAs in issues |
| ARENA-002 T1 pair (both conditions) | Participant PRs #7 (arena), (ops) | Frozen/awaiting score | G₀ | Awaiting preregistration hash validation |
| ARENA-002 T2 pair (both conditions) | Participant PRs #8 (arena), (ops) | Frozen/awaiting score | G₀ | Awaiting preregistration hash validation |
| ARENA-002 T3 pair (both conditions) | Participant PRs #9 (arena), (ops) | Frozen/awaiting score | G₀ | Awaiting preregistration hash validation |
| G₀ governance snapshot | ops commit SHA | Anchor | ops#368 + prior | CLAUDE.md, GOVERNANCE.md, authority state when ARENA-002 preregistered |
| G₁ governance (Pilot 1) | (draft, pending Z2) | Blocked | G₀→G₁ gate | Not implemented until ARENA-002 scorecard complete |
| ARENA-003 template | (draft, in prep) | Pending | G₁ | Measurement-channel validator (not yet governance gate) |

---

## Experimental Sequence Gates (Governance Versioning)

**G₀ Phase (SOLO validation under current governance):**
- [ ] All 6 ARENA-002 SOLO outputs frozen (3 pairs × 2 conditions)
- [ ] Preregistration hashes validated against observed participant outputs
- [ ] Measurement completeness recorded (`measurement_channel_complete = false/true` per pair)
- [ ] Run validity assigned (UNKNOWN, CONSTRAINED, or equivalent per rubric)
- [ ] Output-channel telemetry documented (Copilot substrate behavior)
- [ ] Arena#1 permanently closed (contamination boundary restored)
- [ ] No causality inferred; treated as proof-of-instrumentation + candidate signals

**G₀→G₁ Gate (before Pilot 1 implementation):**
- [ ] ARENA-002 scorecard complete and signed off
- [ ] Governance versioning document prepared (G₀→G₁ commit SHA + surfaces + reason)
- [ ] Z2 approval to proceed with Pilot 1 governance changes

**G₁ Phase (SOLO baseline + later social under revised governance):**
- [ ] Pilot 1 (G₁ governance) merged to main
- [ ] Fresh G₁ SOLO baseline run (ARENA-003 measurement-channel validation)
- [ ] ARENA-003 validator deployed (mechanically validates schema; does not repair)
- [ ] Independent reviewer onboarded for output audit
- [ ] Only then: G₁ SOCIAL exposure (ARENA-004) with preregistered hypotheses (not desired outcomes)

---

*Report generated by Claude Haiku 4.5 per Night's execution approval.*
