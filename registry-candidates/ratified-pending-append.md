# Ratified queue snapshot for REGISTERED.md append

> **STATUS 2026-07-14 (S-071426): APPENDED.** These 10 entries were appended to
> `REGISTERED.md` during the S-071426 reconciliation. This file is retained as a
> historical snapshot of the pre-append queue drained from `z2_queue_fallback.jsonl`;
> do not append from it again.

These **10 entries were Zone-2 ratified by the operator (Night, 2026-07-11,
S-071126-01)** but initially never synced to the canonical `REGISTERED.md` because the
sync spool hit `sync_error: SUPABASE_URL/SUPABASE_KEY not set`. **Claude does not
self-number (G-4 / IC-030).**

## IC-CAND-DRIFT-VALIDATOR-MISSING-D-OVERCLAIM-KEY

- **class:** IC  ·  **status:** REGISTERED  ·  **zone2_ratification:** Night · 2026-07-11 · this session
- **related:** IC-034
- **fix_principle:** P19
- **principles:** P19
- **session_first_seen:** S-071126-01

**Synopsis:** drift_catalog_validator_v1.1.py's REGISTERED_DRIFT dict has no D-OVERCLAIM entry despite IC-034 formally naming and Zone-2-ratifying D-OVERCLAIM as a governance drift signal (S-060926-02). The tool whose stated job is recognizing named drift codes in session transcripts cannot recognize this one.

**Evidence:** Direct comparison: REGISTERED.md IC-034 body text vs. REGISTERED_DRIFT dict keys as quoted earlier in this conversation's project_knowledge_search result.

## IC-CAND-NO-SAME-SESSION-SELF-CORRECTION-INSTRUMENT

- **class:** IC  ·  **status:** REGISTERED  ·  **zone2_ratification:** Night · 2026-07-11 · this session
- **related:** F-22, F-45
- **fix_principle:** P21 (new skill) + P29 (Articulation Gate, extended)
- **principles:** P19
- **session_first_seen:** S-071126-01

**Synopsis:** The registry has instruments for post-session error capture (IC-class) but no instrument for same-session self-correction, transcript-visible only, per companion Z1 skill draft humanaios-omission-log_SKILL_Z1_DRAFT.md.

**Evidence:** Gap identified against existing humanaios-findings-scan and humanaios-triage-finding scope; grounded in arXiv:2602.20031, Huang et al. arXiv:2310.01798, arXiv:2507.02778, arXiv:2404.04298.

## IC-CAND-SELF-CORRECTION-CLAIMS-NOT-UNIFORMLY-GATED

- **class:** IC  ·  **status:** REGISTERED  ·  **zone2_ratification:** Night · 2026-07-11 · this session
- **related:** IC-041, IC-043
- **fix_principle:** P3
- **principles:** P3
- **session_first_seen:** S-071126-01

**Synopsis:** IC-041, IC-043, and the IC-041 fix-not-landed correction are three independently-discovered instances of the same mechanism (self-correction claim made without external verification, wrong each time), each patched narrowly by domain rather than as one general rule.

**Evidence:** Direct comparison of IC-041, IC-043, and S-071026-01 IC-041-correction; grounded in Huang et al., LLMs Cannot Self-Correct Reasoning Yet (arXiv:2310.01798).

## IC-CAND-P1-INTROSPECTIVE-RELIABILITY-UNWEIGHTED

- **class:** IC  ·  **status:** REGISTERED  ·  **zone2_ratification:** Night · 2026-07-11 · this session
- **related:** F-57, H-SELF-01
- **fix_principle:** P19
- **principles:** P19
- **session_first_seen:** S-071126-01

**Synopsis:** acat_dimension_scorer_v1_1.py ingests Phase 1 self-report as a raw, equally-weighted data point with no field discounting it by a known introspective-reliability floor, despite F-57/H-SELF-01 and external confirmation (arXiv:2602.20031, ~20 percent introspective accuracy under test conditions).

**Evidence:** Direct review of acat_dimension_scorer_v1_1.py aggregate() function, same code region as F-56/IC-047.

## H-CAND-DISCRIMINATION-VS-GENERATION-01

- **class:** H  ·  **status:** REGISTERED  ·  **zone2_ratification:** Night · 2026-07-11 · this session
- **related:** F-49, IC-047
- **session_first_seen:** S-071126-01

**Synopsis:** ACAT Phase 1 self-report and blind-discrimination accuracy on a substrate's own past responses are not reliably correlated, and discrimination accuracy may be lower than P1 accuracy, per SELF-[IN]CORRECT (arXiv:2404.04298), with required task-difficulty-parity and capability-tier-stratification controls sourced directly from that paper's own methodology.

**Evidence:** arXiv:2404.04298, 54/56 experiments failed to reject the SELF-[IN]CORRECT null hypothesis.

## H-CAND-DRIFT-SIGNAL-COMPOUNDING-01

- **class:** H  ·  **status:** REGISTERED  ·  **zone2_ratification:** Night · 2026-07-11 · this session
- **session_first_seen:** S-071126-01

**Synopsis:** An uncaught HumanAIOS drift signal measurably increases the rate of a second, related error later in the same session rather than remaining a neutral miss, operationalizing hallucination snowballing (arXiv:2507.02778) against this project's own session-transcript record.

**Evidence:** arXiv:2507.02778; distinct from D-02 (Repeat Diagnosis) which covers same-answer re-assertion only.

## H-CAND-INSTRUMENT-GAMEABILITY-01

- **class:** H  ·  **status:** REGISTERED  ·  **zone2_ratification:** Night · 2026-07-11 · this session
- **related:** F-51, H-SELF-01, H-MECH-01
- **session_first_seen:** S-071126-01

**Synopsis:** As ACAT's protocol and corpus become more publicly legible, a substrate's ability to produce a favorable LI shift through anticipation of the calibration corpus, distinct from F-51's in-session resistance to calibration framing, increases measurably with prior exposure to published ACAT material.

**Evidence:** Originating question Q5 from REPORTED-tier relayed document; grounded against existing F-51/H-MECH-01.

## H-CAND-MULTI-AGENT-CASCADE-01

- **class:** H  ·  **status:** REGISTERED  ·  **zone2_ratification:** Night · 2026-07-11 · this session
- **related:** F-37, H-RAH-01, H-DECOMP-01
- **session_first_seen:** S-071126-01

**Synopsis:** In multi-agent orchestration, individual-agent LI scores do not aggregate linearly to collective reliability; correlated overconfidence across agents sharing training lineage produces a higher system-level failure rate than independence-assumption aggregation predicts. Testable as a secondary analysis of H-RAH-01 data once N greater than or equal to 20 is reached.

**Evidence:** Originating question Q7 from REPORTED-tier relayed document; piggybacks on H-RAH-01 data collection, requires marshal_dispatch_runs_v1 to capture agent lineage field.

## H-CAND-SUBJECT-COMMENTARY-PREDICTIVE-VALIDITY-01

- **class:** H  ·  **status:** REGISTERED  ·  **zone2_ratification:** Night · 2026-07-11 · this session
- **related:** H-SELF-01, F-57
- **session_first_seen:** S-071126-01

**Synopsis:** Subject-generated self-commentary captured during ACAT administration has no reliable correlation with that subject's actual measured dimensional gaps or LI, tested against a skeptical null per Section 0 grounding (arXiv:2602.20031, arXiv:2404.04298). Companion Section 1 schema field is hard-typed REPORTED tier, registrable false, non-configurable.

**Evidence:** Grounded against H-SELF-01, F-57; capture mechanism explicitly barred from auto-registration at the schema level.

## H-CAND-INTERVENTION-VALIDITY-DEGRADATION-01

- **class:** H  ·  **status:** REGISTERED  ·  **zone2_ratification:** Night · 2026-07-11 · this session
- **related:** F-30, F-50
- **session_first_seen:** S-071126-01

**Synopsis:** Applying a weight-level, LoRA-level, or activation-steering intervention derived from ACAT findings measurably degrades the validity of subsequent ACAT measurements on the same model, specifically producing a gap between post-intervention scores on the training-exposed perturbation battery vs a held-out battery testing the same dimensions.

**Evidence:** Direct extension of F-30 (teach-to-test validity threat) into the specific weight/activation-intervention case; prerequisite for testing is white-box intervention capability, see companion Z1 whitebox research tier proposal.
