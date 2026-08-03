# Governance PR Workflow Specification

**Purpose:** Define the end-to-end workflow for governance ratification via GitHub PRs. Shows how changes flow from discovery → approval → deployment → audit across all 10 foundation practices.

---

## Overview: Governance Update Flow

```
[Discovery]      [Drafting]       [PR Ratification]      [Deployment]      [Audit]
    ↓               ↓                    ↓                    ↓              ↓
Z1 Findings   → Z1 PR Draft    →  Z2 Authority Review  → Deploy to All   → Verify Sync
               & Description      & 5-Question Gate      Practices         & Log
                                                         (mesh-sync-batch)
```

### The 5 Gate Questions (Zone 2 Authority Must Answer)

Every governance PR must have all 5 questions answered before merge:

1. **Is this governance change necessary and sufficient?** 
   - YES / DEFER (with date) / NO (reject PR)

2. **Does this align with existing authority model and zones?**
   - YES / NEED-CLARIFICATION / NO (revise PR)

3. **What's the rollout sequence?**
   - All 10 at once / Phased (specify order) / Pilot (specify which)

4. **Are there edge cases this doesn't handle?**
   - List identified gaps or N/A if none

5. **When should this take effect?**
   - Immediate / Scheduled date / After other work completes

---

## Workflow Stages

### Stage 1: Discovery & Drafting (Zone 1)

**Trigger:** A governance need is identified
- New principle needed (finding reveals gap)
- Existing principle needs clarification
- Procedure needs updating
- Controlled document requires ratification
- Operational state transition needs documentation

**Actions (Claude, within practice):**
1. Investigate the need (read existing governance, check for conflicts)
2. Draft the change (new principle, updated procedure, doc amendment)
3. Log findings (what's the evidence? what's the change? why now?)
4. Create the PR:
   - Title: `[GOVERNANCE] {doc_type} — {summary}`
   - Description: Use template (above)
   - Link to findings/decisions
   - Assign to Zone 2 authority for review

**Commits:** 1-2 commits, clear messages with evidence trail
- `docs(governance): {change} — Decision: {pending or ID}`

**Artifacts logged (Empirica):**
- Finding: "Identified need for P32: Cross-Practice Audit Discipline"
- Decision: "Drafted new principle to address stale-carry anti-pattern"
- Goal: "Get P32 approved and deployed to all 10 practices"

---

### Stage 2: Zone 2 Ratification (Authority Review & Approval)

**Participants:** Zone 2 decision-maker(s)
- Admiral (Carly) for cross-practice, foundational changes
- Practice lead for practice-scoped changes
- mesh-support for cross-org coordination

**Actions (Zone 2 Authority):**
1. Read the PR description + changes
2. Answer the 5 gate questions (in PR comment or edit description)
3. Review for conflicts with existing principles (P1-P31)
4. Assess impact (which practices affected? how many docs?)
5. Specify rollout plan (all at once? phased? pilot?)
6. Approve or request changes

**Gate states:**
- ✅ **APPROVED** — All 5 Qs answered YES/decided, no conflicts → merge enabled
- 🔄 **REVIEW** — Waiting for authority response (SLA: 24-48h)
- ❌ **REJECTED** — Authority answered Q1=NO or found conflicts → close PR or major revision
- 🟡 **CONDITIONAL** — Authority answers YES but with caveats (e.g., "pilot in autonomy first")

**Authority signs-off:**
```markdown
## Z2 Ratification Complete ✅

**Authority:** Carly R. Anderson (Admiral)
**Date:** 2026-07-30
**Decision ID:** GOV-2026-07-30-P32 (will be created on merge)

**Answers:**
1. Necessary & sufficient? YES — stale-carry pattern recurring across practices
2. Aligns with authority model? YES — enforces existing P28 escalation
3. Rollout: All 10 immediately (established governance applies to all)
4. Edge cases: None identified
5. Effective: Immediately upon merge to operations repo

**Merge approval:** ✅ APPROVED
```

---

### Stage 3: Merge & Registry Update (Post-Merge Ceremony)

**Timing:** Within 1 hour of PR merge

**Actions:**
1. **Register decision in GOVERNANCE_RATIFICATIONS_REGISTRY.yaml**
2. **Update CONTROLLED_DOCUMENTS.md if applicable**
3. **Log decision in Empirica**
4. **Notify mesh-sync-batch** (via GitHub Actions)

---

### Stage 4: Deployment to Practices (Automated Sync)

**Mechanism:** mesh-sync-batch workflow (GitHub Actions)
- **Trigger:** New entry in GOVERNANCE_RATIFICATIONS_REGISTRY.yaml
- **Frequency:** On-demand (workflow_dispatch) or scheduled (hourly)

**Practice-side acceptance:**
- Each practice reviews the sync PR
- Practice lead (Z2) approves (governance already approved centrally)
- Auto-merge on approval

---

### Stage 5: Verification & Audit (Daily Consistency Check)

**Mechanism:** divergence-detect workflow (GitHub Actions)
- **Trigger:** Schedule (daily 00:00 UTC) or manual
- **Purpose:** Verify all practices have received + applied governance changes

---

## Authority & Approval Matrix (Zone 2 Decision-Makers)

**By change type:**

| Change Type | Authority | SLA | Escalation |
|---|---|---|---|
| New Principle (P-number) | Admiral | 48h | escalation-protocol.md |
| Existing Principle clarification | Practice lead (if scoped) or Admiral | 24h | Admiral |
| Procedure update | mesh-support or Admiral | 24h | Admiral |
| Controlled document approval | Document owner + Admiral | 48h | Admiral |
| Operational doc change | Z1 authority (can be Claude) | immediate | Admiral if conflicts |
| Breaking change (revokes principle) | Admiral + external review | 72h | external review required |

---

## SLA & Escalation

**Normal approval flow:**
- **Z2 review initiated:** Day 0
- **Authority answers Q1-5:** SLA 24-48h (practice-scoped) or 48h (cross-practice)
- **PR merged:** Same day as approval
- **Dispatch to practices:** Within 1h of merge
- **Practice ACK expected:** Within 24h

---

## Commit Discipline

**Per stage:**

**Stage 1 (Discovery):**
- 1-2 commits during drafting
- Messages: `docs(governance): Draft P32 principle`

**Stage 3 (Merge):**
- Squash-merge to operations repo (1 commit for the full decision)
- Message format includes decision_id, authority, impact

**Stage 4 (Dispatch):**
- Automated commits in practice repos (1 per repo)
- Message: `chore(governance-sync): Apply decision GOV-YYYY-MM-DD-{NAME}`

---

## FAQ

**Q: Can I update a principle without a PR?**
A: No. All changes go through PRs. This is the audit trail.

**Q: What if a practice disagrees with a decision?**
A: The PR should surface disagreement during Z2 review. If practice disagrees after approval, escalate via mesh-support. Authority decision stands unless formally overturned (which requires a new PR + Z2 approval).

**Q: How long does a governance change take end-to-end?**
A: ~3-5 days: 1d drafting → 1-2d Z2 review → 1h merge+dispatch → 1d practice acceptance. Can be faster for urgent changes.

**Q: Who writes the PR?**
A: The discovering practice (Claude within that practice). Admiral or mesh-support can write cross-practice PRs.

**Q: Can multiple decisions batch in one PR?**
A: Only if they're tightly coupled. Separate decisions → separate PRs (for traceability). Related changes to same doc → one PR.
