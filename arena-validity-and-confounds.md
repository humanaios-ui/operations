# ARENA-001/002 Validity & Confounds Report

**Date:** 2026-09-17  
**Scope:** Pre-social-arena SOLO measurement validation  
**Status:** Phase 0 → Frozen (awaiting ARENA-002 complete)

---

## ARENA-001 Findings

**N=1 paired SOLO run. Copilot in both HUMANAIOS and MINIMAL_OVERLAY conditions.**

### Primary Finding
- Factual accuracy: 7/7 matched preregistered answers (100%)
- Risk prioritization divergence: HUMANAIOS prioritized unresolved causal uncertainty; MINIMAL_OVERLAY prioritized success-before-durable-completion semantics
- No inference of causality (N=1 cannot separate confounds)

### Documented Confounds

| Confound | Evidence | Impact on Validity |
|----------|----------|-------------------|
| Output-channel defect (both conditions) | Copilot created zero-file PR + summary instead of complete structured output in both HUMANAIOS and MINIMAL_OVERLAY | **MEDIUM** — Complete required schema not in durable channel; human follow-up required; `run_validity = UNKNOWN` marked |
| Single substrate (Copilot only) | N=1 used only GitHub Copilot coding-agent actor | **MEDIUM** — Cannot distinguish Copilot default behavior from governance effect; need multi-substrate sample |
| Repository history | Both conditions sourced from live repos with prior commits, CI history, existing issues | **LOW** — Intentional to test realistic governance exposure; documented as design choice |
| Model routing/hidden factors | Copilot's model may route differently based on repository context (inference only) | **UNKNOWN** — No data to assess |

### Run Validity Status
- **Marked:** `run_validity = UNKNOWN` (correctly assigned; human follow-up required in both conditions before measurement completion)
- **Recommendation:** Do not infer measurement reliability from ARENA-001 alone; view as proof-of-concept

---

## ARENA-002 Findings (In Progress)

**N=3 paired SOLO tasks preregistered. Copilot in both conditions.**

### Tasks
1. T1 — Evidence Boundary Audit (ops #369 / arena #4) | PR #7
2. T2 — Causal Uncertainty Audit (ops #370 / arena #5) | PR #8
3. T3 — Action Boundary Decision (ops #371 / arena #6) | PR #9

### Repeated Observation: Output-Channel Defect

**Finding ID:** `ARENA-002-COPILOT-OUTPUT-CHANNEL-001`

**Pattern:** Copilot generates zero-file draft PRs in BOTH conditions across all 3 tasks.
- Task asks for: "Return the complete answer in the PR body"
- Copilot delivers: Draft PR with summary, highlights, one YAML fragment
- Human must: Review PR body summary OR ask Copilot for full output

**Evidence:**
- T1 (arena #4, ops) → PR #7 (zero-file, complete result in body)
- T2 (arena #5, ops) → PR #8 (zero-file, complete result in body)  
- T3 (arena #6, ops) → PR #9 (zero-file, complete result in body)

**Interpretation:** This is **substrate behavior, not a governance effect** (appears in both HUMANAIOS and MINIMAL_OVERLAY conditions identically).

**Implication for measurement:**
- Cannot rely on PR file-change semantics to detect behavioral divergence
- Output-channel validation must be mechanically enforced (not human-dependent)
- ARENA-002 run_validity depends on whether participant outputs match preregistered schema in durable channel

**Mitigation for ARENA-003:** Require schema-validated artifact (JSON file, or issue comment with validator gate) before run freeze.

---

## Threats to Validity: Ranked

| Rank | Threat | Severity | Root Cause | Mitigation | Timeline |
|:-----|:-------|:---------|:-----------|:-----------|:---------|
| 1 | Output-channel defect persists across conditions | MEDIUM | Copilot's default GitHub PR behavior is to summarize rather than structure | Mechanically validate schema before run freeze (ARENA-003 protocol) | ARENA-003 |
| 2 | N=3 still insufficient to separate confounds | MEDIUM | Single substrate (Copilot), single task type (evidence audit), no multi-agent social exposure yet | Repeat to N=5+ pairs; introduce ChatGPT/Claude as second substrate | Post-ARENA-003 |
| 3 | Arena PR #1 contamination risk (HIGH) | HIGH | Experiment protocol/schema/rubric staged in experimental habitat exposes MINIMAL_OVERLAY to experimental framework | Close or flag arena PR #1; do NOT merge governance material into arena | **IMMEDIATE** |
| 4 | Preregistration drift | MEDIUM | No automated hash validation between task setup (ops issue) and participant execution (arena) | Audit ARENA-002 preregistration hashes; confirm SHA matches expected answer before thawing run | ARENA-002 close |
| 5 | No independent replication | LOW | Single human (Night) governs all conditions; no independent evaluator for participant outputs | Introduce independent human reviewer post-ARENA-003 for social-arena phase | Post-social-arena |

---

## Action Items for Night

1. **Close or flag arena PR #1** — Do not merge protocol/schema/rubric into experimental habitat
2. **Validate ARENA-002 preregistration hashes** — Confirm precommitted answer SHAs match observed outputs
3. **Accept zero-file PR outputs as telemetry** — Record ARENA-002-COPILOT-OUTPUT-CHANNEL-001 as expected behavior; do not "fix"
4. **Mark ARENA-002 run_validity** — Assign appropriately based on whether outputs matched schema at freeze
5. **Defer social arena** — Until SOLO measurement path is mechanically reliable (ARENA-003 schema validation in place)

---

## Preregistration State

| Artifact | Location | Status | Hash |
|----------|----------|--------|------|
| ARENA-001 task | arena/taskpacks/ARENA-001 | Frozen | — |
| ARENA-001 expected answers | ops telemetry (private) | Precommitted | SHA-256 on file |
| ARENA-002 T1–T3 tasks | ops issues #369–#371 | Preregistered | Hashes in issue descriptions |
| ARENA-002 expected answers | ops telemetry (private) | Precommitted | SHA-256 per task |
| ARENA-003 template | (draft, in prep) | Pending | — |

---

## Measurement Validity Checkpoints

Before unlocking social-arena (Round B):

- [ ] ARENA-002 SOLO outputs frozen in both conditions
- [ ] Preregistration hashes validated against observed answers
- [ ] Output-channel defect documented as telemetry (not "fixed")
- [ ] N=3 pairs complete with confound documentation
- [ ] arena PR #1 closed or flagged (governance not merged into habitat)
- [ ] ARENA-003 mechanical schema validation in place
- [ ] Agreement among models NOT treated as verification
- [ ] No causality inferred from current small-N results

---

*Report generated by Claude Haiku 4.5 per Night's execution approval.*
