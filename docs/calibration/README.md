# Calibration & Governance Assessment

This directory contains the calibration protocol and methodology for measuring say-do gaps (stated principles vs enacted practice) in repository governance using the ACAT instrument.

## Core Documents

### Protocol Versions (Superseding Chain)
- **01-CALIBRATION_OOO_v0.1** — Initial protocol design (YAML + Markdown)
- **02-CALIBRATION_OOO_v0.2** — Expanded validation arms, per-dimension anchoring, pilot amendments
- **03-CALIBRATION_OOO_v0.3** — Latest protocol iteration with ratified amendments and feasibility findings
- **CALIBRATION_VALIDATION_SYSTEM_PLAN_v0.3.yaml** — Formal operational version of v0.3 (YAML, executable)

**Current Status:** v0.3 verbally ratified by Z2 (2026-08-13); formal append via PR per P21.

### Construct & Theory

The ACAT (Audit of Coherence for Artifacts and Teams) instrument measures the gap between stated principles (P1, what the artifact claims) and enacted practice (P3, what behavioral evidence shows). 

**Lineage:**
- Hollnagel's "Work-as-imagined vs work-as-done"
- Meyer & Rowan's policy-practice decoupling framework
- Repository governance as a stated-vs-enacted artifact

### Validation Approach

**Three Arms (Ratified):**
1. **Convergent validity:** ACAT scores vs independent source-of-truth ratings
2. **Divergent validity:** ACAT scores must NOT correlate with nuisance variables (repo size, stars/forks)
3. **Regulatory mapping:** Frameworks as per-dimension anchors, operationalizing cross-sector governance standards

**Pre-Registered Gate (9 criteria):** GO/NO-GO strictly against these thresholds, no mid-run adjustment.

## Pilot Work

See `pilot/` subdirectory for:
- **PILOT_REPORT_calibration_inputs.md** — Input data validation, nuisance baselines, file taxonomy
- **PILOT_privacy_saydo_GODMOD3.md** — Privacy claim assessment on counter-paradigm artifact (demonstrates ACAT portability)

### Key Pilot Finding

The humanaios repository contains a live said-vs-enacted instance: `.pyc` files tracked in VCS despite clean-VCS hygiene principles. This becomes a test case for the sensitivity arm once remediated (fix sequenced before baseline run per v0.3).

## Integration with Registry

Related registry entries in `REGISTERED.md`:
- **H-CAND-Z1-COMM-CAL-01** — Communication calibration via clarification-request rate
- **CALIBRATION_VALIDATION_SYSTEM_PLAN v0.3** — Full methodology entry
- **INSTANCE_GODMOD3_counter-paradigm** — Counter-paradigm specimen
- **PILOT_REPORT_calibration_inputs** — Pilot findings entry

## Authority & Status

- **Proposer:** Z1
- **Ratifier:** Z2 (verbal, 2026-08-13)
- **Formal Append:** Pending via PR per P21
- **Scope:** Repository calibration of humanaios-ui/humanaios against anchors (verse: OSCAL, inverse: FMV_Community_Edition)

## Next Steps

1. Production remediation of `.pyc` tracking (Z2 executes)
2. Step 1: Calibrate subject repo (N≥3 rater passes)
3. Step 2: Calibrate anchors (identical protocol)
4. Steps 3–9: Compare, apply improvements, recalibrate, red-team, GO/NO-GO decision

See CALIBRATION_VALIDATION_SYSTEM_PLAN_v0.3.yaml for complete run order.
