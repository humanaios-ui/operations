# PRIORITY_QUEUE.md

Priority Queue for HumanAIOS v0.2 Intake Cycle. **Z1 proposes, Z2 ratifies by hash, only READY top-score rows may begin.**

## Queue Metadata

| field | value |
|---|---|
| **version** | z2_queue v1_1 |
| **issued** | 2026-09-05 |
| **ratification_hash** | — (pending Z2 signature) |
| **score_formula** | `impact + Σ impact(unblocks)` |
| **status_gate** | READY |

---

## Queue Items

### Q-ORCA-01 ◆ READY

**Title:** Evaluate stablyai/orca as the multi-substrate audit runner

| field | value |
|---|---|
| **status** | READY |
| **score** | 8 |
| **impact** | 3 |
| **unblock_impact_sum** | 5 |
| **session_type** | desktop |
| **tool_zone** | 1 (execute) |

**Unblocks:**
- OPT second-substrate audit step
- DELUSION-GUARD independence check

**Provenance:**
- repo: https://github.com/stablyai/orca
- stars (live read 2026-09-04): 61,815
- license: MIT
- tier: VERIFIED-LIVE (metadata only; code not yet read)

**Acceptance Criteria:**
1. Same packet run through Claude Code + Codex + one third agent, each in its own worktree
2. Each run's output hashed and appended to optimizer_events.jsonl
3. Disagreements between substrates surface as DISPUTED callouts, not averaged away

**Falsifier:** If orca cannot isolate worktrees per substrate or cannot expose per-run outputs for hashing, it does not serve the audit step and is dropped.

**Status After First Run:** LAID until first real packet runs through it; 0/40 unchanged.

---

## Blocked / In Review

(None currently)

---

## Landing Order

Per `z1-inbox/2026-09-06/registry_block_and_manifest_090626_v2.md` §Landing order (extended):
1. CODEOWNERS ×9 + 12 teams
2. Registry candidate block
3. research-intake.yml (Tier 2, ADV)
4. TLA spec as dataset row 1
5. Design docs
6. **← Queue patch (this file)**
7. Repo program C1 per practice
8. Intake post (after IC-SCOPE-05)

---

## Blockers to Queue Advancement

1. **GitHub PAT** — unblocks all work
2. **IC-030 live read** — drift vs REGISTERED.md pinned state
3. **IC-SCOPE-05 in code** — before intake post
4. **TLA_TOOLS_SHA256** — Z2 repository variable
5. **z2_budget_p2** — Phase 2 envelope constant (nothing ordered until it exists)

---

**Generated from z2_queue v1_1 patch:** 2026-09-06 (UTC)  
**Registry pin:** REGISTERED.md blob `c0899b9b4f8825d154274b176bb880f233c45995` at commit d1fb5f0d2dd9
