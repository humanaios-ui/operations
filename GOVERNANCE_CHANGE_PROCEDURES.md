# Governance Change Procedures

**Purpose:** Define the specific workflows for 4 types of governance changes. Each follows the core PR workflow but with different SLAs, authority levels, and approval gates.

---

## Procedure 1: New Ratification (Principles, Policies, Procedures)

**When to use:** Adding a new governance principle (P-number), policy, or procedure that didn't exist before.

### SLA:
- Z2 review: 48h (cross-practice) or 24h (practice-scoped)
- Total time: 3-5 days

### Authority:
- **Cross-practice principle:** Admiral (Carly)
- **Practice-scoped principle:** Practice lead + Admiral veto

---

## Procedure 2: Minor Update (Clarifications, Typo Fixes, Version Bumps)

**When to use:** Fixing grammar, clarifying existing principle, bumping version, no semantic change.

### SLA:
- Z2 review: 24h
- Total time: 1-2 days

### Authority:
- Admiral (final authority on all GOVERNANCE.md content)
- Can be delegated to practice leads for practice-scoped minor updates

---

## Procedure 3: Breaking Change (Revokes, Reframes, High-Impact Updates)

**When to use:** Revokes an existing principle, reframes how a zone works, changes escalation logic, or changes fundamental authority model.

### SLA:
- Z2 review: 72h
- External review: 72h
- Phased deployment: varies by migration plan (1-4 weeks typical)
- Total time: 1-2 weeks minimum for significant changes

### Authority:
- **Admiral** (final authority, must approve breaking changes)
- **External review** (if cross-org impact, request mesh-support + collaborator)
- **Practice leads** (must ACK breaking changes affecting their practices)

---

## Procedure 4: Operational Doc Update (MOLT_STATE, SYSTEM_HEALTH, etc.)

**When to use:** Updating state docs that reflect current system status or operational procedures.

### SLA:
- Review: 12h (fast)
- Deploy: 1-2h after merge
- Total time: Same day to next day

### Authority:
- **Z1 (Claude)** — can merge operational docs directly after self-review
- **Practice lead** — optional review for accuracy
- **Admiral** — veto if change conflicts with governance

### Maturation Rules:
After 3 cycles of successful Z2-approved PRs with zero corrections:
- Request "auto-sync" status in governance PR
- Admiral approves → operational doc marked "auto-update-ready"
- Thereafter: Claude updates doc directly (no PR), practices auto-sync

---

## Summary Table: Which Procedure?

| Change Type | Example | Procedure | Authority | SLA | Approval Gate |
|---|---|---|---|---|---|
| New Principle | "Add P32" | New Ratification | Admiral | 48-72h | 5 Q-gate |
| Principle Clarification | "Fix typo in P22" | Minor Update | Admiral | 24h | Lightweight (Q1-2) |
| Breaking Change | "Revoke P14" | Breaking Change | Admiral + external | 72h-2w | Heavyweight + rollback plan |
| Operational State | "Update MOLT_STATE" | Operational Doc | Z1 + optional practice lead review | 12-24h | Optional lightweight |
| Matured Operational | "Auto-update MOLT_STATE" | (No PR) | Z1 only | immediate | None (auto-sync) |
