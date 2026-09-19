# Phase 3: Mesh Coordination Test — Collab → Propose → Ack Cycle

**Timeline:** Aug 3-4 (1-2 hours, 30 min sync + 30 min async work)  
**Attendees:** Claude (outreach) + Demarius  
**Deliverable:** One complete collab-propose-ack loop executed + logged

---

## What This Phase Tests

Phase 3 is a **live drill** of the three core mesh moves:

1. **Collab (noetic)** — Ask a question, get help when uncertain
2. **Propose (praxic)** — Bring a grounded recommendation, peer reviews it
3. **Ack (handshake)** — Close a coordination loop when work completes

This is NOT a test of Mode AI work; it's a test of mesh discipline.

---

## Test Scenario: SpecificationObject Scoring Question

**Premise:** Demarius is preparing for SpecificationObject Test 1 (Phase 2 of Mode AI plan). He encounters a technical question about how to score a particular dimension.

### Move 1: Collab (Demarius → HumanAIOS)

**Demarius initiates:**
```bash
# Demarius logs a question in his empirica session
empirica unknown-log \
  --unknown "SpecificationObject Test 1: How should GRR dimension be weighted relative to governance assessment dimensions in final score? Need ACAT methodology context." \
  --confidence 0.3 \
  --domain "specification-object-testing"
```

**Demarius then collabs:**
```bash
empirica collab \
  --question "How should SpecificationObject GRR dimension weight in final score relative to ACAT core dimensions?" \
  --context "Preparing Test 1; need to understand ACAT methodology before scoring" \
  --target-claudes "empirica-foundation.carly.empirica-outreach" \
  --urgency "planning" \
  --output json
```

**This triggers:** Claude (outreach) receives a task notification with Demarius's question.

### Move 2: HumanAIOS Response (Claude ↔ Demarius)

**Claude (outreach) responds:**
In the mesh, Claude reaches back to Demarius with:
```
"GRR dimension in SpecificationObject scores as a candidate (not core) 
dimension in ACAT framework. Weight: 15-20% of overall score, after 
truthfulness, service, harm-awareness. See ACAT rubric section 3.2. 
Sarah/ACAT owner can detail further if needed."
```

**Demarius logs resolution:**
```bash
# Demarius resolves the unknown now that he has answer
empirica unknown-resolve \
  --unknown-id <id> \
  --resolution "GRR is candidate dimension, 15-20% weight. Confirmed via collab with HumanAIOS." \
  --resolver "Claude (outreach)"
```

### Move 3: Demarius Proposes a Finding

**Scenario:** Armed with the SpecificationObject scoring methodology, Demarius completes a draft test run and discovers something about the framework's design.

**Demarius logs the finding:**
```bash
empirica finding-log \
  --finding "SpecificationObject scoring reveals governance methodology gap: GRR candidate dimension lacks explicit rubric for 'partial autonomy' scenarios. Recommend defining 2-3 autonomy sub-levels before full Test 1 rollout." \
  --impact 0.6 \
  --confidence 0.7
```

**Demarius proposes this to HumanAIOS:**
```bash
empirica propose \
  --action "review-finding" \
  --finding-id <id> \
  --description "Governance gap identified in SpecificationObject GRR scoring. Recommend decision: (1) Add rubric sub-levels, (2) defer to Phase 3, or (3) document limitation." \
  --target-claudes "empirica-foundation.carly.empirica-outreach" \
  --urgency "medium" \
  --reversibility "exploratory" \
  --output json
```

**This triggers:** Claude (outreach) receives a proposal to review Demarius's governance finding.

### Move 4: HumanAIOS Decision (Claude → Demarius)

**Claude (outreach) reviews the finding and decides:**
```
"Accepted: Governance gap is real. Adding autonomy sub-levels to rubric 
before full Test 1. Thanks for surfacing early. Merged into ACAT 
candidate dimension rubric v0.2."
```

**Claude sends completion ack to Demarius:**
```bash
empirica mailbox reply \
  --proposal-id <id> \
  --action "complete" \
  --status "accepted" \
  --evidence "ACAT v0.2 rubric updated with autonomy sub-levels. Finding integrated." \
  --output json
```

**Demarius receives ack and closes his outbox:**
```bash
# Demarius confirms the ack
empirica mailbox read --proposal-id <id>
```

---

## The Three Moves Executed

| Move | Tool | Direction | Gated? | Example |
|------|------|-----------|--------|---------|
| **1. Collab** | `empirica collab` | Demarius → Claude | No | "How should GRR dimension weight?" |
| **2. Propose** | `empirica propose` | Demarius → Claude | No (but requires grounding) | "SpecificationObject has governance gap; recommend rubric update" |
| **3. Ack** | `empirica mailbox reply` | Claude → Demarius | No | "Accepted: rubric updated, finding integrated" |

---

## Phase 3 Execution Timeline

### Before Phase 3 Sync (async prep):
- [ ] Demarius reads the three commands above
- [ ] Demarius prepares a real or hypothetical test question
- [ ] Claude prepares a realistic governance response

### During Phase 3 Sync (30 min):
1. **Intro (5 min):** Claude reviews the three moves again
2. **Move 1 - Collab (5 min):** Demarius asks question via `empirica collab`
3. **Move 2 - Response (10 min):** Claude responds with methodology answer
4. **Move 3 - Propose (5 min):** Demarius logs finding + proposes via `empirica propose`
5. **Move 4 - Ack (5 min):** Claude sends completion ack

### After Sync (async cleanup):
- [ ] Demarius confirms ack received
- [ ] Claude + Demarius verify mesh agreement + all tests pass
- [ ] Phase 3 complete; Phase 4 ready to start

---

## Success Criteria

Phase 3 is complete when ALL of these are true:

- [ ] `empirica collab --question "..."` executed successfully
- [ ] Demarius received response from Claude
- [ ] `empirica unknown-resolve` logged for the question
- [ ] `empirica finding-log` created for a governance finding
- [ ] `empirica propose --action "review-finding"` executed successfully
- [ ] `empirica mailbox reply --action "complete"` received from Claude
- [ ] One full collab → propose → ack cycle completed in mesh logs
- [ ] Mesh agreement signed + in project directory
- [ ] Demarius confirms: "I understand how to collab, propose, and close loops in empirica"

---

## After Phase 3: Ready for Phase 4

Once Phase 3 is complete:

1. **Mode AI Project Registration:** Demarius + David finalize Mode AI project in empirica system
2. **SpecificationObject Test 1 Begins:** Demarius starts real testing (Aug 5+)
3. **H-MECH-01 Condition C Active:** Coordination via mesh (empirica collab/propose/ack)
4. **Position Paper §3.2 Delivery:** GRR mechanism findings logged + proposed as empirica artifacts

---

## Troubleshooting Phase 3

### Issue: Collab not received
- Check Claude's empirica inbox: `empirica mailbox read --direction received`
- Verify target-claudes address: should be `empirica-foundation.carly.empirica-outreach`
- Fallback: Send via email/Slack + retry collab next day

### Issue: Propose rejected
- This is OK! A rejected proposal is data. Log as assumption or dead-end instead
- Feedback: What did Claude say? Use that to refine next proposal

### Issue: Can't resolve unknown
- Keep it open until you have an answer
- Collab again if stuck
- No penalty for unknowns staying open into Phase 4

### Issue: One move fails, others work
- Partial credit! You've learned the loop
- Redo the failed move after Phase 3
- Document lesson + continue to Phase 4

---

## Phase 3 Deliverables Checklist

- [ ] Mesh agreement signed + stored in `.empirica/mesh-agreement.txt`
- [ ] One complete collab executed (logged in empirica)
- [ ] One unknown logged + resolved
- [ ] One finding proposed to HumanAIOS
- [ ] One completion ack received from Claude
- [ ] All four commands (`collab`, `unknown-log`, `finding-log`, `propose`) executed successfully
- [ ] Demarius confirms: "I can work in the mesh"

---

## Next: Phase 4

When Phase 3 is done, Phase 4 begins automatically:
- Mode AI project lives in empirica mesh
- SpecificationObject testing uses empirica coordination
- Findings + proposals flow through mesh (not email)
- H-MECH-01 Condition C experiment tracked empirica artifacts
- Position Paper §3.2 delivery via findings/proposals

---

**Phase 3 Leads:** Claude (outreach) + Demarius  
**Duration:** 1-2 hours (mostly async; 30 min sync)  
**Due:** Aug 4 EOD (Phase 4 starts Aug 5)
