# Registry Candidate Block — for Z2 review and PR append
# Drafted by Z1 per P21; verbally ratified by Z2 in-session 2026-08-13; never self-registered.
# Numbering per live REGISTERED.md convention (clone @ this session), pending collision check at append.

### H-CAND-Z1-COMM-CAL-01 — Z1 Communication Calibration Is Measurable by Clarification-Request Rate

```yaml
id: "H-CAND-Z1-COMM-CAL-01"
class: "H-candidate"
status: "verbally ratified; formal append via PR pending"
session: "S-081326"
statement: >
  Zone 1 communication calibration is measurable as a say-do gap: each Z2
  clarification request marks a delta between what Z1 assumed was transmitted
  and what actually arrived. The rate is trackable per session and classifiable
  by upstream cause, making downstream clarification load a leading indicator
  of upstream Z1 assumption errors.
construct_mapping: >
  Structurally identical to ACAT Phase-1/Phase-3: Z1's transmitted output =
  claim (P1); Z2's comprehension state, evidenced by clarification requests =
  external grounding (P3); the request itself = the gap event. Compatible with
  existing calibration math (rate analog of LI/SAG) without new instrumentation.
cause_taxonomy_v1:
  C1_unverified_referent: "memory/concept treated as verifiable artifact (mitigation: live-verify all identifiers before artifact entry — IC-030 generalized)"
  C2_register_ambiguity: "intent-layer language crossing into measurement vocabulary (mitigation: F-RESONANCE-NEUTRALITY applied at first use — every resonant term gets a recorded neutral twin)"
  C3_decision_interface_mismatch: "output packaged for the system, not the decision-maker (mitigation: every Z2-routed item must be decision-ready — plain definition, options, cost of each)"
first_data_point_AUDITED: >
  S-081326, transcript audit (Z2-directed): 7 events total. Composition:
  C3 = 5 (E3 yaml-unreadable, E4 threshold clarify, E5 rubric-variant,
  E6 production-execution, E7 repeat of E6 — escalation marker),
  C1 = 1 (E2 referent confirmation; healthy-verification subtype),
  C2 = 0 in the Z2→Z1 direction, correction events = 1 (E1 construct fix,
  reverse direction). [V against transcript]
audit_finding: >
  Prior Z1 self-inventory (C1=3, C2=3, C3=2) was miscalibrated: it
  undercounted the dominant failure mode (C3) and counted two Z1-initiated
  disambiguations as Z2 events (direction error). Establishes: (a) the [M]
  audit requirement is load-bearing, not ceremonial; (b) F33 instance —
  instrument truthful about its own data quality on first measurement.
taxonomy_amendments_from_audit:
  - "Add event-direction field: Z2→Z1 clarification request vs Z1→Z2 disambiguation vs Z2 correction event — only the first counts toward the hypothesis rate"
  - "Add repeat-referent escalation marker (E6→E7 pattern): same-topic re-ask after an answer = answer did not land; weight above first asks"
  - "Add healthy-verification subtype under C1: referent confirmations are positive-control behavior, not failures"
falsifiable_prediction: >
  If the taxonomy captures real causes, applying the three mitigations should
  reduce per-class clarification rates across subsequent sessions, with C3
  declining after decision-ready packaging is enforced. If rates do not move,
  the taxonomy is wrong or the mitigation is not the binding constraint.
threshold_note: >
  Target is calibrated reduction, not zero: a zero-clarification session more
  likely indicates Z2 under-challenge or Z1 over-explanation than perfect
  transmission. Floor behavior itself is informative.
relations:
  - "Complements IC-031 (receipt overstatement): IC-031 measures claim inflation; this measures transmission fidelity."
  - "Distinct from H-VERIF-02 lineage (external correction loops); this is the internal Z1→Z2 channel."
```
