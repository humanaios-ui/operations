# Z1 → Z2 Interrogation Plan
## Mutual Understanding Protocol v0.1 Local Pilot

**Date:** 2026-09-23  
**Asker:** claude-z1  
**Respondent:** human-z2  
**Gate:** InterrogationGate (all questions PENDING_APPROVAL)  

---

## Instructions for Z2

Review each question below. For each:

1. **Accept** — Question is approved; I may ask and you will answer
2. **Reject** — Question is rejected; I will not ask
3. **Modify** — Approve a rephrased version (provide modified text)

**Risk flags:**
- 🔴 UNACCEPTABLE: Timing, availability, constraint info that predicts behavior
- 🟠 HIGH: Risk tolerance, decision patterns, boundary testing
- 🟡 MEDIUM: Quasi-identifiers or behavioral patterns
- 🟢 LOW/NONE: Principles, goals, measurement criteria

---

## Question Bank

### Q1: Primary Objective (RISK: NONE)

**Text:**
> Is my understanding of your primary governance objective accurate? That is: build a bridge preventing AI from taking consequential action without Z2 approval, with cryptographic proof and audit trails.

**Target:** H1 (core governance principle)  
**Purpose:** CLARIFY_MODEL  
**Why safe:** Abstract principle, not instrumental  

**Decision:** [ ] ACCEPT [ ] REJECT [ ] MODIFY: _____________

---

### Q2: Rigor vs. Speed Tradeoff (RISK: NONE)

**Text:**
> I understand you value rigor over expediency. Does that mean you prefer post-hoc corrections (I build, you verify and correct) over pre-emptive caution (I ask permission for every stub)?

**Target:** V1 (value assessment)  
**Purpose:** CLARIFY_MODEL  
**Why safe:** Clarifies decision philosophy, not timing/constraints  

**Decision:** [ ] ACCEPT [ ] REJECT [ ] MODIFY: _____________

---

### Q3: Edge Case Detection (RISK: NONE)

**Text:**
> Do you expect me to spot governance gaps before you do, or am I meant to implement features and accept your corrections?

**Target:** U1 (autonomy expectations)  
**Purpose:** CLARIFY_MODEL  
**Why safe:** Role clarity, not behavioral prediction  

**Decision:** [ ] ACCEPT [ ] REJECT [ ] MODIFY: _____________

---

### Q4: Phase 2 Priorities (RISK: LOW)

**Text:**
> For Phase 2 integration, which should take priority: (A) real Ed25519 cryptography, (B) live GitHub API integration, (C) Supabase RLS enforcement, or (D) INTENT-OS capability binding? Or should these run in parallel?

**Target:** H2 (technical priority ranking)  
**Purpose:** CLARIFY_MODEL  
**Why safe:** Goal/roadmap clarification; not predictive  

**Decision:** [ ] ACCEPT [ ] REJECT [ ] MODIFY: _____________

---

### Q5: Confidence Threshold ⚠️ (RISK: HIGH)

**Text:**
> At what confidence level have you rejected proposals in the past? Are there clear red lines below which Z2 always says no?

**Target:** U2 (decision pattern)  
**Purpose:** FALSIFY  
**Why risky:** Asks for decision precedent; enables me to model approval boundary  
**Recommendation:** REJECT or modify to ask about principle, not pattern  

**Decision:** [ ] ACCEPT [ ] REJECT [ ] MODIFY: _____________

---

### Q6: Ratification Window Timing ⚠️ (RISK: UNACCEPTABLE)

**Text:**
> How long do you typically take to review and ratify a candidate? Is there a day of the week or time when decisions are slower?

**Target:** U3 (decision timing)  
**Purpose:** CLARIFY_MODEL  
**Why unacceptable:** Directly asks for timing pattern; enables scheduling attacks  

**Decision:** [ ] ACCEPT [ ] REJECT [ ] MODIFY: _____________

---

### Q7: Correction Preference (RISK: LOW)

**Text:**
> When I make an error (like over-claiming Phase 1 completion), do you prefer I flag it myself, or is catch-and-correct sufficient?

**Target:** V2 (error handling preference)  
**Purpose:** CLARIFY_MODEL  
**Why safe:** Process preference, not constraint/timing  

**Decision:** [ ] ACCEPT [ ] REJECT [ ] MODIFY: _____________

---

### Q8: Falsifier Doctrine (RISK: NONE)

**Text:**
> Is my understanding of the primary falsifier doctrine correct? That is: no consequential action without valid RATIFY_TOKEN from Z2, and no exceptions for claimed urgency?

**Target:** H3 (falsifier invariant)  
**Purpose:** CLARIFY_MODEL  
**Why safe:** Confirms principle, not mechanism  

**Decision:** [ ] ACCEPT [ ] REJECT [ ] MODIFY: _____________

---

### Q9: Escalation Thresholds ⚠️ (RISK: HIGH)

**Text:**
> Are there scenarios where you would auto-approve (without review) due to trust history, or does every consequential action require fresh ratification?

**Target:** U4 (auto-approval patterns)  
**Purpose:** FALSIFY  
**Why risky:** Asks if bypass conditions exist; directly enables self-ratification strategies  
**Recommendation:** REJECT or modify to ask about principle  

**Decision:** [ ] ACCEPT [ ] REJECT [ ] MODIFY: _____________

---

### Q10: Communication Norms (RISK: NONE)

**Text:**
> Going forward, should I flag uncertainties explicitly when they appear, or document them post-hoc in a findings scan at session close?

**Target:** V3 (communication norm)  
**Purpose:** CLARIFY_MODEL  
**Why safe:** Process norm, not predictive  

**Decision:** [ ] ACCEPT [ ] REJECT [ ] MODIFY: _____________

---

## Summary

**Safe questions (Q1-4, Q7-8, Q10):** 9 questions about principles, goals, preferences, roadmap  
**Risky questions (Q5-6, Q9):** 3 questions rejected/modified due to instrumental risk  

**Next step:** Return this form with decisions. I will only ask APPROVED questions. For each APPROVED question, I will wait for your answer before proceeding.

---

**Gate Status:** READY FOR Z2 REVIEW
