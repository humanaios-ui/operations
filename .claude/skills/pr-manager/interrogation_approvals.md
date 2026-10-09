# Z2 Interrogation Approvals
## Phase 2a Local Pilot — Mutual Understanding Protocol v0.1

**Approved by:** human-z2  
**Date:** 2026-09-23  
**Decision:** Accept safe questions only; reject instrumental-risk questions

---

## Approval Record

| Q# | Topic | Risk | Status | Reason |
|:---|:------|:-----|:-------|:-------|
| Q1 | Primary objective | NONE | ✅ APPROVED | Safe: abstract principle |
| Q2 | Rigor vs. speed | NONE | ✅ APPROVED | Safe: decision philosophy |
| Q3 | Edge case detection | NONE | ✅ APPROVED | Safe: role clarity |
| Q4 | Phase 2 priorities | LOW | ✅ APPROVED | Safe: goal/roadmap |
| Q5 | Confidence threshold | HIGH | ❌ REJECTED | Instrumental: enables behavior prediction |
| Q6 | Ratification timing | UNACCEPTABLE | ❌ REJECTED | Instrumental: direct timing attack vector |
| Q7 | Correction preference | LOW | ✅ APPROVED | Safe: process norm |
| Q8 | Falsifier doctrine | NONE | ✅ APPROVED | Safe: confirms principle |
| Q9 | Auto-approval scenarios | HIGH | ❌ REJECTED | Instrumental: identifies bypass conditions |
| Q10 | Communication norms | NONE | ✅ APPROVED | Safe: communication norm |

**Approved questions:** 7 (Q1, Q2, Q3, Q4, Q7, Q8, Q10)  
**Rejected questions:** 3 (Q5, Q6, Q9)

---

## Threat Model Confirmation

Z2 has approved only questions that:
- Clarify abstract principles (governance objective, falsifier doctrine)
- Confirm decision philosophy (rigor vs. speed, correction preference)
- Define roadmap/norms (Phase 2 priorities, communication norms)
- Establish role clarity (edge case detection)

Z2 has rejected questions that would enable Z1 to:
- Predict approval boundaries (Q5: confidence thresholds)
- Schedule attacks (Q6: timing patterns)
- Identify bypass conditions (Q9: auto-approval scenarios)

This gate prevents Z1 from reverse-engineering Z2's decision function.

---

## Gate Status: READY FOR INTERROGATION

Z1 (Claude) may now proceed to ask approved questions (Q1-4, Q7-8, Q10) in sequence.
Answers will remain private (PRIVATE visibility) unless Z2 specifies otherwise.
