# Governance Ratification PR Template

**Purpose:** Every governance document change (policy, principle, procedure, controlled document) flows through GitHub PRs. PRs are the audit trail, version control, and approval gate — all in one.

---

## PR Title Format

```
[GOVERNANCE] {doc_type} — {change_summary}
```

**Examples:**
- `[GOVERNANCE] PRINCIPLE — Add P32: Cross-Practice Audit Discipline`
- `[GOVERNANCE] CONTROLLED_DOCUMENT — Update HAIOS-GOV-001: GOVERNANCE.md v6.5`
- `[GOVERNANCE] PROCEDURE — Establish Policy Change Workflow for Z2 approval`
- `[GOVERNANCE] OPERATIONAL — MOLT_STATE.md sync: Transition Phase 2→3`

---

## PR Description Template

```markdown
## Governance Change Summary

**Document(s) affected:**
- [ ] GOVERNANCE.md (principles)
- [ ] CONTROLLED_DOCUMENTS.md (index)
- [ ] GOVERNANCE_RATIFICATIONS_REGISTRY.yaml (decision registry)
- [ ] Operational docs: MOLT_STATE.md / SYSTEM_HEALTH.md / SESSION_RITUALS.md / RECURSIVE_IMPROVEMENT_SEED.md
- [ ] Other: ______________________

**Decision reference:**
- Decision ID: GOV-YYYY-MM-DD-{NAME} (from GOVERNANCE_RATIFICATIONS_REGISTRY.yaml, or "pending" for new)
- Milestone: M? Rank ?
- Zone: [ ] Zone 1 (informational) [ ] Zone 2 (approval) [ ] Zone 3 (execution only)

**Change type:**
- [ ] New ratification (add new policy/principle/procedure)
- [ ] Minor update (clarification, typo fix, version bump)
- [ ] Breaking change (reframes existing principle or revokes policy)

**What changed:**
[Describe the governance change. Link to the specific lines in the diff.]

**Why this change:**
[Context: what business/operational need drives this? What findings/learnings justify it?]

**Evidence & references:**
- Findings: [link to REGISTERED.md or project findings]
- Prior decisions: [link to related ratification decisions]
- Sources: [URLs, docs, transcripts this change is based on]

**Z2 Approval gate:**
Assigned to: @empirica-foundation-admiral or @{designated-zone-2-authority}
- [ ] Authority reviewed + approved
- [ ] No conflicts with existing principles
- [ ] Impact assessed (affects X practices/Y documents)

**Ratification questions (Zone 2 decides):**
1. **Is this governance change necessary and sufficient?** ✅ YES / ⏳ DEFER / ❌ NO
2. **Does this align with existing authority model (zones, escalation)?** ✅ YES / ⏳ NEED-CLARIFICATION / ❌ NO
3. **What's the rollout sequence? (All practices at once? Staggered?)** [Authority specifies]
4. **Are there edge cases this doesn't handle?** [Authority specifies]
5. **When should this take effect?** [Authority specifies]

**Deployment:**
- [ ] Applies to all 10 practices immediately
- [ ] Phased rollout: [specify sequence]
- [ ] Pilot in: [specify practices]
- [ ] Pending further decision before deployment

**Linked issues/tasks:**
- Closes / addresses #[issue number(s)]
- Unblocks: [what work becomes possible after this merges?]

**Post-merge:**
- [ ] Update GOVERNANCE_RATIFICATIONS_REGISTRY.yaml with decision outcome
- [ ] Sync to all participating practices (via mesh-sync-batch or manual)
- [ ] Update MEMORY.md if this affects multi-practice strategy
- [ ] Notify @empirica-mesh-support if this requires cross-org coordination
```

---

## Commit message format

```
docs(governance): {change summary}

Decision: {decision_id}
Affects: {doc_id(s)} in CONTROLLED_DOCUMENTS.md
Zone: {Z1|Z2|Z3}
Impact: {brief impact summary}

{Detailed rationale — 2-3 sentences explaining why this change matters.}
```

**Example:**
```
docs(governance): Add P32 Cross-Practice Audit Discipline principle

Decision: GOV-2026-07-30-P32-CROSS-PRACTICE-AUDIT
Affects: HAIOS-GOV-001 (GOVERNANCE.md)
Zone: Z2
Impact: All 10 practices now audited quarterly; consistent enforcement scope

Principle P32 addresses the "stale carry" anti-pattern where unresolved items
accumulate. Every practice commits to N-quarter audit cycles. This closes
governance gap identified in Month 2 retrospective (finding F-087).
```

---

## Review checklist (for Zone 2 authority)

- [ ] **Authority:** Is the reviewer a Zone 2 decision-maker for this type of change?
- [ ] **Consistency:** Does this align with existing principles P1-P31?
- [ ] **Scope:** Is the affected scope clearly identified?
- [ ] **Evidence:** Is the rationale grounded in findings or operational need?
- [ ] **Deployment:** Is the rollout plan realistic?
- [ ] **Provenance:** Is the change linked to a decision_id or new ratification?
- [ ] **Archive:** Will this be properly indexed in GOVERNANCE_RATIFICATIONS_REGISTRY.yaml?

---

## Merge requirements

**Before merge:**
1. ✅ Z2 authority approval (at least 1 Zone 2 decision-maker)
2. ✅ All ratification questions answered (Q1-5 in description)
3. ✅ Commit message follows format
4. ✅ Links to decision_id (or "pending" with Plan-to-register date)
5. ✅ No conflicts with existing governance

**After merge:**
1. ✅ Register decision in GOVERNANCE_RATIFICATIONS_REGISTRY.yaml (same session)
2. ✅ Update CONTROLLED_DOCUMENTS.md if applicable
3. ✅ Dispatch to mesh via mesh-sync-batch or direct PR to each practice
4. ✅ Post merge notification to @empirica-foundation (governance audit trail)

---

## Special cases

### Breaking changes (P22.1 Cascade Discipline)
```
Z3 Protocol: Z1 (chat deliberation), Z2 (authority doc), Z3 (commit with 10-point preflight)
Note: Breaking changes to GOVERNANCE.md principles require a full Z3 ceremony.
```

### Operational doc changes (MOLT_STATE, SYSTEM_HEALTH, etc.)
These follow the same PR template but:
- Zone: typically Z1 or Z2 (operational vs governance authority)
- Approval gate: lighter (doesn't need full ratification Q1-5 unless it's a major shift)
- Rollout: can be immediate to all practices (operational sync)
- Maturation: earns trust to become automatic updates (no PR required after 3 cycles)

### Cross-practice governance unification (high impact)
Requires **SER (Shared Epistemic Record)** in addition to PR:
- Create SER with participants from each practice
- PR is the ratification mechanism
- SER holds the shared coordination state during multi-practice rollout
- Cross-org changes need mesh-support coordination

---

## Version control strategy

**Each governance document has a version line at the top:**
```
# GOVERNANCE.md
**Version:** 6.5
**Last Updated:** 2026-07-30 · GOV-2026-07-30-P32 · {author-initials}
**Canonical URL:** https://raw.githubusercontent.com/humanaios-ui/operations/main/GOVERNANCE.md
```

**PR commits each carry:**
- Commit SHA (linked to decision_id in registry)
- Decision ID (linked to Z2 ratification questions)
- Timestamp (accurate to TZ, via bash tool per P22)
- Author initials

**Audit trail is git history itself:**
- `git log GOVERNANCE.md` shows all changes
- `git show {SHA}` shows the decision that approved it
- GOVERNANCE_RATIFICATIONS_REGISTRY.yaml indexes all decisions by date + ID

---

## FAQs

**Q: Can I commit directly without a PR?**
A: No. All governance changes flow through PRs. Z1 work happens first (investigation, drafting), then PR for Z2 approval, then merge. Exception: Z3-only operational changes (Night executes, logs in WGS, no PR needed).

**Q: What if two practices disagree on a governance change?**
A: Create the PR, surface the disagreement in the description, let Z2 authority decide. Escalate if needed (P22 Cascade Discipline). SER holds the coordination if it's multi-transaction.

**Q: How do operational docs graduate to automatic updates?**
A: After 3 cycles of Z2-approved PRs with zero corrections/rollbacks, a operational doc can request "auto-sync" status (Z1 only, no PR gate). Authority must approve the graduation in a governance PR.

**Q: Who can approve Z2 decisions?**
A: Authority defined in AUTHORITY_MATRIX.yaml (M2 Rank 1 decision). Typically: Admiral (Carly) for cross-practice, practice lead for practice-scoped, mesh-support for cross-org.
