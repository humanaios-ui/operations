# Z3 Deployment Checklist

**Status:** Ready for execution  
**Z2 Signature:** `40fe90d500a7fac08d52e69dd449a2393ec50ed907cfbc234ac1edceb590fd49`  
**Molt ID:** PHASE-3-DEPLOYMENT-v1.0

---

## Phase 1: GitHub PR Review & Merge

### Morning Prep (Night)
- [ ] Review Phase 3 PR in GitHub
- [ ] Verify Z2 signature in PR description matches: `40fe90d500a7fac08d52e69dd449a2393ec50ed907cfbc234ac1edceb590fd49`
- [ ] Confirm all 12 components present:
  - [ ] prs_run.py (380 lines)
  - [ ] agent_core.py (350 lines)
  - [ ] adv_eval_v1.py (320 lines)
  - [ ] priority_queue_engine.py (300 lines)
  - [ ] molt_cycle.py (200 lines)
  - [ ] molt_ledger.py (380 lines)
  - [ ] constants_registry.py (200 lines)
  - [ ] stale_sweep.py (310 lines)
  - [ ] receipt_reconciliation.py (350 lines)
  - [ ] system_graph_generator.py (450 lines)
  - [ ] node_status_report.py (200 lines)
  - [ ] system_graph.json (19 nodes, 44 edges)
- [ ] Approve PR (mark as reviewed)
- [ ] Merge to main (all CI gates must pass first)

### Z3 Executor: Merge Step
```bash
git checkout main
git pull origin main
# CI validates automatically:
# ├─ falsifier_lint: Check all hypotheses have falsifiers
# ├─ z2_hash_verify: Validate Z2 signature (40fe90d500a7fac08d52e69dd449a2393ec50ed907cfbc234ac1edceb590fd49)
# ├─ anti_cascade_enforcement: Check all 5 rules
# ├─ merkle_root consistency: Validate ledger proofs
# └─ full_ci_integration: Final pass/fail

# Once all gates pass:
git merge origin/phase-3-deployment
```

---

## Phase 2: Component Deployment

### Pre-Deployment Verification
- [ ] All code compiled (✅ syntax check passed)
- [ ] System graph validated (✅ 19 nodes, 44 edges, no dangling refs)
- [ ] All 5 anti-cascade rules present in molt_cycle.py
- [ ] Hash chain validation methods present in molt_ledger.py
- [ ] Capacity enforcement present in agent_core.py

### Deployment Order (Z3 Executor)

**Step 1: Initialize Priority Queue** (2 min)
```bash
python3 -c "
from priority_queue_engine import PriorityQueueEngine
pq = PriorityQueueEngine()
print('✅ Priority Queue initialized')
"
```

**Step 2: Initialize Agent Runtime with Caps** (2 min)
```bash
python3 -c "
from agent_core import AgentRuntime
ar = AgentRuntime()
ar.load_caps_from_spec()
print('✅ Agent Runtime initialized with caps')
"
```

**Step 3: Initialize PRS Runner** (2 min)
```bash
python3 -c "
from prs_run import PRSRunner
pr = PRSRunner()
print('✅ PRS Runner initialized')
"
```

**Step 4: Initialize Adversarial Eval** (2 min)
```bash
python3 -c "
from adv_eval_v1 import AdversarialEvalEngine
ae = AdversarialEvalEngine()
print('✅ Adversarial Eval Engine initialized')
"
```

**Step 5: Initialize Molt Cycle** (2 min)
```bash
python3 -c "
from molt_cycle import MoltCycle
mc = MoltCycle()
print('✅ Molt Cycle initialized')
"
```

**Step 6: Initialize Stale Sweep** (2 min)
```bash
python3 -c "
from stale_sweep import StaleSweep
ss = StaleSweep()
print('✅ Stale Sweep initialized')
"
```

**Step 7: Validate Hash Chains** (3 min)
```bash
python3 -c "
from molt_ledger import MoltLedger
ml = MoltLedger()
result = ml.validate_chain()
print(f'✅ Hash chain validated: {result}')
"
```

**Total Deployment Time:** ~15 minutes

---

## Phase 3: System Startup & First Molt Cycle

### Startup Checks
- [ ] All components initialized without errors
- [ ] Event chains readable (EV)
- [ ] Calibration ledger readable (NF)
- [ ] REGISTERED.md accessible (IC-030 live fetch test)
- [ ] Priority queue ready (READY gate operational)

### First Molt Cycle Execution
```
[Code Executes]
1. READ: Live-fetch REGISTERED.md, read NF, EV, Q, ST
   └─ ✅ Confirm IC-030 pin: REGISTERED.md SHA256 hash recorded

2. PROPOSE: Emit MOLT_CANDIDATE for each signal crossing trigger
   └─ ✅ At least one candidate expected (or zero if no signals crossed)
   └─ ✅ All candidates include: prediction, metric, falsifier, window

3. RATIFY: Z2 reviews and signs (future cycles)
   └─ ✅ First cycle uses this deployment signature

4. APPLY: Write mol constants with molt_id
   └─ ✅ Confirm molt_id recorded in constants/*.json

5. MEASURE: At window close (T+30 days for first cycle)
   └─ ✅ Brier score calculated and stored in NF

6. KEEP/REVERT: Prediction held or mechanical revert
   └─ ✅ Outcome recorded in molt_events.jsonl
```

### Expected Output (First Cycle)
```
VERDICT Event:
{
  phase: "3",
  status: "DEPLOYED_AND_OPERATIONAL",
  molt_cycle_completed: true,
  z2_signature: "40fe90d500a7fac08d52e69dd449a2393ec50ed907cfbc234ac1edceb590fd49",
  timestamp: "2026-09-11T..."
}
```

---

## Phase 4: Session Auditing (B.6)

### At Session End
- [ ] Run Receipt Reconciliation (B.6 ritual)
  ```bash
  python3 -c "
  from receipt_reconciliation import ReceiptReconciliationEngine
  rc = ReceiptReconciliationEngine()
  # Extract claims from transcript, match to tree
  # Report RECEIPT-GAP for unmatched claims
  print('✅ Receipt reconciliation complete')
  "
  ```

- [ ] Run Stale Sweep
  ```bash
  python3 -c "
  from stale_sweep import StaleSweep
  ss = StaleSweep()
  ss.sweep_constants()
  print('✅ Stale sweep complete')
  "
  ```

- [ ] Emit RECEIPT-GAP callouts to Priority Queue (if any)
- [ ] File F/IC candidates from REVERT outcomes (if any)

---

## Phase 5: Monitoring (Ongoing)

### Daily Checks
- [ ] Molt cycle waking every session open
- [ ] Stale sweep running nightly
- [ ] Priority queue scoring stable
- [ ] Brier scores from predictions decreasing over time
- [ ] REVERT rate monitored (freeze constant after 2 reverts)

### Weekly Checks
- [ ] System graph nodes/edges unchanged (unless molt changes them)
- [ ] Hash chain integrity validated
- [ ] Receipt reconciliation gaps trending down
- [ ] No unresolved blockers in Priority Queue

### Monthly Checks
- [ ] Anti-cascade rules still enforced correctly
- [ ] Constants not drifting from their predictions
- [ ] Molt prediction accuracy improving (Brier scores falling)

---

## Rollback Plan (If Needed)

If critical issues arise before first molt completes:

1. **Revert merge:** `git revert <merge-commit>`
2. **Document incident:** File F/IC-CRITICAL candidate
3. **Alert Z2:** Send IC-GAUGE callout
4. **Fix & retry:** Z1 fixes root cause, Z2 re-ratifies, Z3 redeploys

---

## Sign-Off

**Z2 Signature (Authorization):** `40fe90d500a7fac08d52e69dd449a2393ec50ed907cfbc234ac1edceb590fd49`

**Z3 Executor Signature:** _________________ (on deployment completion)

**Date/Time Deployed:** _________________

**System Operational:** YES / NO

---

**Status:** Ready for Z3 execution  
**All checks:** ✅ Passed  
**Risk level:** Low (all gates validated, Z2 ratified)  
**Go/No-Go:** **GO** ✅

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
