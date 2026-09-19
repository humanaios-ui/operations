# BOOT_PROCESS_MAP.md — Session Rituals → Resource States

**Purpose:** Map session open (§A) and close (§B) rituals to resource capacity states  
**Authority:** Z2 ratifies design; Z1 executes rituals per this map  
**Model:** Resource-based; halt conditions defined by resource depletion, not time  
**Updated:** 2026-09-14T00:00:00Z

---

## Session Lifecycle (Resource-Based Model)

```
┌─ SESSION START (§A) ────────────────────────────────────┐
│                                                          │
│ A.1: Pin SHA (REGISTERED.md live-fetch, IC-030)         │ ← Resource: Network I/O
│      HALT if: fetch fails → no valid proposal log       │
│                                                          │
│ A.2: Read ZONE_REGISTRY.md (verify repo is active)      │ ← Resource: Context (1 file)
│      HALT if: repo not listed → unknown authority       │
│                                                          │
│ A.3: Read REGISTERED.md at pinned SHA                   │ ← Resource: Context (cached)
│      HALT if: SHA mismatch → stale context              │
│                                                          │
│ A.4: Read PRIORITY_QUEUE.md (ranked by resource_impact) │ ← Resource: Context (1 file)
│      HALT if: queue empty or inaccessible → no work     │
│                                                          │
│ A.5: Read MOLT_STATE.md (open molts, state machine)     │ ← Resource: Context (1 file)
│      HALT if: state inconsistent → measurement broken   │
│                                                          │
│ A.6: Read BOOT_PROCESS_MAP.md (this file; reference)    │ ← Resource: Context (1 file)
│      HALT if: boot steps changed → unclear ritual       │
│                                                          │
│ → Session resources: 5 files cached; authority context  │
│   established; ready for work                           │
│                                                          │
└─ BOOT COMPLETE (All halts cleared) ────────────────────┘
                    ↓
        ┌─ WORK PHASE ─────────────────────┐
        │ (Z1 proposes, Z2 ratifies,       │
        │  Z3 executes; emit VERDICT,      │
        │  CYCLE, MEASURE events)          │
        │                                  │
        │ Resource budget tracked per:     │
        │ - Z1 proposal effort (units)     │
        │ - Z2 ratification (per cycle)    │
        │ - Z3 agent caps (behavior_spec)  │
        │                                  │
        │ Deplete budget → work halts;     │
        │ no time deadline                 │
        └──────────────────────────────────┘
                    ↓
┌─ SESSION CLOSE (§B) ────────────────────────────────────┐
│                                                          │
│ B.1: Walk claim vs. ledgers/NF_LEDGER.jsonl (receipt reconcile) │ ← Resource: Ledger I/O
│      HALT if: ledger inaccessible → no measurement data │
│                                                          │
│ B.2: Generate receipt (claim → ledger entry)            │ ← Resource: Analysis (audit)
│      HALT if: RECEIPT-GAP exists → verify or file IC    │
│                                                          │
│ B.3: Harvest F/IC/H candidates from events              │ ← Resource: Analysis
│      (molt ledger, RECEIPT-GAP callouts, observations)  │
│                                                          │
│ B.4: Write z1-inbox/<date>/HANDOFF.md                   │ ← Resource: Storage
│      (SHA pinned, findings, receipt walk-back, blockers)│
│                                                          │
│ B.5: Z2 ratifies handoff (signs findings + next priority)│ ← Resource: Z2 review
│      (moves candidates to PRIORITY_QUEUE.md)            │
│                                                          │
│ → Session artifacts: handoff file saved; findings       │
│   queued; ledger consistent; ready to close             │
│                                                          │
└─ SESSION CLOSE COMPLETE ──────────────────────────────┘
```

---

## Halt Conditions (Resource-Based)

| Halt Condition | Stage | Reason | Recovery |
|:---|:---|:---|:---|
| Network I/O fails (A.1) | Boot | Cannot fetch live REGISTERED.md | Retry network; check proxy status (/root/.ccr/README.md) |
| Repo not in ZONE_REGISTRY.md (A.2) | Boot | Authority unclear; unknown zone | Z2 adds repo to ZONE_REGISTRY.md, re-pin |
| SHA mismatch on REGISTERED.md (A.3) | Boot | Stale context; IC-030 violated | Live-fetch again; verify cache cleared |
| PRIORITY_QUEUE.md empty (A.4) | Boot | No work defined; queue inaccessible | Z2 populates queue from findings or creates new work |
| MOLT_STATE.md inconsistent (A.5) | Boot | State machine corrupted; molts undefined | Z2 verifies state consistency; regenerate if needed |
| ledgers/NF_LEDGER.jsonl inaccessible (B.1) | Close | Cannot verify measurements; audit fails | Check ledger hash-chain; recover from backup if needed |
| RECEIPT-GAP exists (B.2) | Close | Claim not found in ledger; audit fails | Verify claim is real; file IC-RECONCILIATION candidate if needed |

---

## Resource Budget Tracking

**Session-level resources:**
- Network I/O: Fetch 5 governance files at start
- Cache: Keep 5 files in context for duration
- Storage: Write 1 handoff file at close
- Analysis: Receipt audit (time-bounded by ledger size, not deadline)

**Work-level resources:**
- Z1 proposal effort: Measured in units (1-10)
- Z2 ratification: Measured by queue score + capacity
- Z3 agent cycles: Capped per behavior_spec.json (token budget, tool budget)

**Depletion model:**
- When budget exhausted → work halts automatically
- No 48h deadline; no arbitrary window_end
- Refill on next session or when Z2 allocates more

---

## No Time-Based Gates

The following are **REMOVED** (resource-based model replaces them):
- ~~"Z2 responds within 48h"~~ → "Z2 ratifies when capacity permits"
- ~~"Molt window_end at timestamp"~~ → "Molt completes when measurement criteria met"
- ~~"Frozen after 2 reverts"~~ → "Frozen until root cause identified"
- ~~"Re-propose within 48h"~~ → "Re-propose when resource available (no deadline)"

Only regulatory/external deadlines override resource-impact ranking.

---

## Session Ritual Checklist (§A Open)

```
□ A.1 — Fetch REGISTERED.md from origin (live-fetch; pin SHA)
        ✓ SHA matches prior? YES → use pinned; NO → update pin
        
□ A.2 — Read ZONE_REGISTRY.md
        ✓ Repo in active list? YES → confirm authority; NO → ERROR
        
□ A.3 — Read REGISTERED.md at pinned SHA
        ✓ Candidates loaded? YES → proceed; NO → ERROR
        
□ A.4 — Read PRIORITY_QUEUE.md
        ✓ Queue has work? YES → rank by resource_impact; NO → error
        
□ A.5 — Read MOLT_STATE.md
        ✓ Molt state valid? YES → proceed; NO → verify consistency
        
□ A.6 — Read BOOT_PROCESS_MAP.md (reference)
        ✓ Boot steps current? YES → ready; NO → update map
        
□ READY — All halts cleared; begin work
```

---

## Session Close Checklist (§B Close)

```
□ B.1 — Fetch NF_LEDGER.jsonl (measurement log)
        ✓ Ledger accessible? YES → proceed; NO → ERROR
        
□ B.2 — Walk claim vs. ledger (receipt audit)
        ✓ All claims matched? YES → clean; NO → file RECEIPT-GAP
        
□ B.3 — Harvest F/IC/H candidates
        ✓ Any findings? → Candidates listed
        
□ B.4 — Write z1-inbox/<date>/HANDOFF.md
        ✓ Handoff saved? YES → ready for Z2
        
□ B.5 — Z2 ratifies handoff
        ✓ Z2 signed findings? → move to PRIORITY_QUEUE.md
        
□ CLOSED — Session artifacts persisted; Z2 signed; ready for next session
```

---

## Reference

- CLAUDE.md: Authority roles, Z-structure
- GOVERNANCE_FILES.md: Registry of all governance files
- REGISTERED.md: Live proposal log (fetch every session)
- PRIORITY_QUEUE.md: Ranked work queue
- MOLT_STATE.md: Molt lifecycle state machine
- NF_LEDGER.jsonl: Measurement log (append-only, hash-chained)
- behavior_spec.json: Z3 agent capability caps (resource budgets)

---

## Metadata

```yaml
metadata:
  model: "resource-based (no time deadlines)"
  halt_model: "resource depletion (not timeout)"
  boot_order: "A.1 → A.2 → A.3 → A.4 → A.5 → A.6 (sequential, halt-on-fail)"
  close_order: "B.1 → B.2 → B.3 → B.4 → B.5 (sequential)"
  authority: "Z2 (Night) ratifies this map"
  last_updated: "2026-09-14T00:00:00Z"
```
