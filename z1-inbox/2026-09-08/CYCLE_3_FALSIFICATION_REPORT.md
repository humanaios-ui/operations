# ADVERSARIAL REPORT
## Governance & Process Graph v0.2
### HumanAIOS / Z1-Z2-Z3 Registry Architecture

---

**Report ID:** ADV-2026-0908-001  
**Target:** `governance_graph_v0.2.json` (registered_md_sha: `40391062966c6d6f9e29819a56ba1b87a035146e9d962a331d33de0aa8069029`)  
**Date:** 2026-09-08  
**Classification:** FULL DISCLOSURE — Adversarial Review  
**Methodology:** Static graph analysis, invariant falsification, deadlock detection, trust-boundary probing, semantic contradiction mining  
**Assumption:** The graph is the authoritative specification. Any behavior not encoded in nodes/edges/metadata is **undefined** and therefore **untrusted**.

---

## 1. EXECUTIVE SUMMARY

This report presents **17 verified findings** across **4 severity tiers**, **6 compound attack chains**, and **8 concrete falsification tests** that can break claimed invariants.

**Bottom line:** The architecture is **governance-fragile**. It delegates absolute authority to Z2 (an un-audited, self-referential actor), places a policy engine (MOLT) in a mechanical zone, acknowledges only 2 of 16 dependency cycles, and leaves enforcement paths undefined for 5 critical subsystems. A single Z2 error, a MOLT misconfiguration, or an MK consistency failure can cascade into a full registry freeze or silent policy corruption.

**Verdict:** **DO NOT RATIFY** in current form. Minimum 7 structural changes required before Tier-1 molt.

---

## 2. SCOPE & METHODOLOGY

### 2.1 In-Scope
- 19 nodes, 44 edges, metadata block
- Validation claims (`dangling_nodes`, `dangling_edges`, `cycles`, `state_mutators`)
- Enforcement clauses per node
- Zone/Tier assignments
- Ratification references

### 2.2 Methodology
1. **Graph Invariant Analysis:** Cycle detection, sink/source analysis, edge coverage
2. **Trust Boundary Probing:** Every node that writes state was checked for (a) who operates it, (b) who reviews its output, (c) who can revert it
3. **Semantic Contradiction Mining:** Cross-referencing node metadata against edges, metadata against metadata
4. **Falsification Design:** For each claimed invariant, constructing a minimal input that should trigger it but may not
5. **Deadlock Detection:** Analyzing feedback loops for liveness guarantees

### 2.3 Tools
- Python `networkx` equivalent (custom DFS)
- JSON schema validation (manual)
- Invariant injection (simulated)

---

## 3. THREAT MODEL

The adversary is assumed to have one or more of:
- **A1:** Z2 compromise (insider threat, coercion, model drift)
- **A2:** MOLT manipulation (bug, malicious revert, stale constant)
- **A3:** Q priority manipulation (wrong weights, stale pins)
- **A4:** CIG/MK deadlock trigger (DoS via inconsistency injection)
- **A5:** ADV suppression (silent gate rot)
- **A6:** Ghost Z1 exploitation (unaccountable proposals)

The system claims to resist A1-A6. This report tests those claims.

---

## 4. FINDINGS

### 4.1 CRITICAL

---

#### ADV-001: Z2 is an Unaudited Absolute Monarch
**Severity:** CRITICAL  
**Category:** Trust Architecture / Single Point of Failure  
**CVSS-equivalent:** 10.0 (Complete system compromise with no mitigation path)

**Description:**  
Z2 ratifies hashes for Q, FS, OM, PRS, MOLT, REG, and indirectly CONST. Z2's operator field says "Z2 (Night)" — **self-referential**. No node reviews Z2's decisions. No edge shows Z2 being overridden, audited, or adversarially tested. The metadata claims "Z2 ratifies by hash" but never specifies **who ratifies Z2**.

**Evidence:**
```
"id": "Z2",
"operator": "Z2 (Night)",
"enforcement": "hash, not prose"
```
Z2 receives candidates from FS, OM, PRS, MOLT. Z2 sends ratification to CIG, MOLT. No incoming edge from ADV, no audit loop, no Z3 mechanical check on Z2 output.

**Impact:**  
If Z2 is compromised (A1), the adversary can:
- Ratify arbitrary MOLT candidates → poison CONST
- Approve broken PRS verdicts → deploy unsafe code
- Accept fraudulent FS findings → register false invariants
- Merge arbitrary REG updates → corrupt the public record

**Falsification Test:**  
Construct a ledger where Z2 ratifies a MOLT candidate that changes `J03_agree_max` from 0.90 to 1.00 (eliminating the sycophancy gate). The graph has no mechanism to reject this. Run `jester_invariants.py` — it will report PASS because the constant is now 1.00, but the **gate is gone**. Z2's ratification hash is the only check, and it passed.

**Remediation:**
- **Option A:** Add Z2-AUDIT node. Z2 ratifications must pass ADV before CIG merge.
- **Option B:** Require multi-sig Z2 (quorum of independent operators, not "Z2 (Night)").
- **Option C:** Z2 decisions are themselves ratified by a Z3 mechanical check (e.g., Z2 output must satisfy a formal spec verified by CI).

---

#### ADV-002: CIG → REG → MK → CIG Deadlock Cycle (Unacknowledged)
**Severity:** CRITICAL  
**Category:** Liveness / Denial of Service  
**CVSS-equivalent:** 7.5 (Availability impact, no data loss)

**Description:**  
The validation section lists only 2 cycles. Static analysis reveals **16 cycles**. The most dangerous is `CIG → REG → MK → CIG`. If MK detects inconsistency, it blocks CIG. CIG blocks REG merge. REG never updates. MK has no new data to re-evaluate. **Permanent liveness failure.**

**Evidence:**
```
{"source": "CIG", "target": "REG", "type": "merge"}
{"source": "REG", "target": "MK", "type": "trigger"}
{"source": "MK", "target": "CIG", "type": "gate", "label": "consistency FAIL blocks merge"}
```
Validation claims only:
```
"cycles": [
  "MOLT → CONST → Q → MOLT (learning loop; tier-gated)",
  "EV → FS → Z2 → CIG → REG → EV (record chain; append-only)"
]
```
The CIG-REG-MK cycle is **absent** from this list.

**Impact:**  
An attacker (A4) can inject a single inconsistent hash into REG. MK fails. CIG blocks all future merges. The registry freezes. No new molts, no new constants, no new ratifications. The system is **operationally dead** but **appears secure** (CI is blocking bad merges).

**Falsification Test:**  
1. Submit a PR that appends a valid-looking but hash-mismatched entry to REGISTERED.md
2. MK detects inconsistency → signals FAIL to CIG
3. CIG blocks merge
4. Submit a **correct** fix PR
5. CIG still blocks because MK hasn't re-run on the new proposed state (it only runs on merged state)
6. System is frozen. No recovery path is defined.

**Remediation:**
- **Option A:** Add `MK → ST` trigger on consistency FAIL. ST stale-sweeps the blocked merge and reopens as GAP.
- **Option B:** Change MK → CIG from "blocks merge" to "queues retry with exponential backoff". After N retries, escalate to MOLT for mechanical revert.
- **Option C:** Separate MK into pre-merge (on PR) and post-merge (on main). Pre-merge MK runs on proposed state; post-merge MK runs on landed state. Pre-merge failure should not block future PRs.

---

#### ADV-003: MOLT is a Policy Engine Masquerading as a Mechanical Node
**Severity:** CRITICAL  
**Category:** Zone Violation / Privilege Escalation  
**CVSS-equivalent:** 9.8 (Arbitrary state modification with no review)

**Description:**  
MOLT is assigned to **Zone 3** ("lands; CI enforces") and **Tier 1** (highest impact). But MOLT:
- Reads Q gaps (operational state from Zone 1/2)
- Makes **revert decisions** ("code measures and reverts")
- Writes CONST values that affect the entire system
- Has operator "Z2 ratifies Tier 1/2; **code measures and reverts**"

Zone 3 nodes should be **pure functions** (MK, OTS). MOLT is a **policy interpreter**. Placing it in Zone 3 means its revert decisions are treated as "mechanical" and bypass the ratification layer.

**Evidence:**
```
"id": "MOLT",
"zone": 3,
"tier": 1,
"writes": ["MOLT_CANDIDATE", "molt_events.jsonl", "CONST writes (ratified) / reverts (mechanical)"],
"operator": "Z2 ratifies Tier 1/2; code measures and reverts",
"enforcement": "anti-cascade rules 1–5; freeze after 2 reverts; loop-level falsifier"
```
The "anti-cascade rules 1–5" and "loop-level falsifier" are **undefined** in this document.

**Impact:**  
If MOLT's "code measures and reverts" has a bug (A2), it can:
- Revert safety-critical constants silently
- Freeze itself after 2 reverts (self-DoS)
- Write to CONST without Z2 ratification (the "mechanical" path)

**Falsification Test:**  
1. MOLT proposes a candidate that changes `J06_noise_catch` from 0.10 to 0.00
2. Z2 ratifies it (or MOLT applies it "mechanically" if the ratification path is bypassed)
3. `jester_invariants.py` now requires 0% catch rate — any critic passes
4. The adversarial review system is **functionally disabled**
5. No node detects this because ADV has no enforcement path (ADV-004)

**Remediation:**
- **Option A:** Demote MOLT to Zone 2. Split into MOLT-PROPOSE (Z2 candidate) and CONST-APPLY (Z3 mechanical). Only CONST-APPLY touches CONST, and only after Z2 ratification hash is present.
- **Option B:** Define "anti-cascade rules 1–5" as executable invariants (like JESTER-01..07) and run them in CI before any MOLT output is accepted.
- **Option C:** Remove "mechanical revert" from MOLT. All reverts must be Z2-ratified candidates.

---

### 4.2 HIGH

---

#### ADV-004: ADV (Adversarial Eval) Has No Enforcement Path
**Severity:** HIGH  
**Category:** Detection Gap / Silent Failure  
**CVSS-equivalent:** 8.0 (Gate rot undetected, no escalation)

**Description:**  
ADV is the system's immune system. It reads "gates under test" and writes "ATTACK/VERDICT events, catch rates". But its only outgoing edge is to EV (Event chains). There is **no path** from ADV to Z2, CIG, MOLT, or Q. If ADV finds a broken gate, the verdict sits in EV until FS happens to scan it.

**Evidence:**
```
"id": "ADV",
"writes": ["ATTACK/VERDICT events", "catch rates"],
"enforcement": "NO_GATE reported, never counted as caught"
```
Edges from ADV: only `ADV → EV` (event).

**Impact:**  
An attacker (A5) can:
- Break a gate (e.g., make J-05 always PASS by changing the imperative regex)
- ADV detects it, writes to EV
- FS may never prioritize this finding
- Z2 never sees it
- The broken gate remains in production indefinitely

**Falsification Test:**  
1. Modify the IMPERATIVE regex in `jester_invariants.py` to exclude "you must"
2. Run ADV — it detects the gap (imperatives now pass)
3. ADV writes ATTACK-VERDICT to EV
4. FS scans EV, but the finding is buried under 1000 other events
5. Z2 never ratifies a fix
6. The gate is broken for months

**Remediation:**
- **Option A:** Add `ADV → Z2` (type: callout, label: "BROKEN_GATE") for findings above a severity threshold.
- **Option B:** Add `ADV → Q` (type: callout, label: "EMERGENCY") to force the broken gate to top priority.
- **Option C:** ADV findings auto-trigger a MOLT candidate (mechanical) to revert the changed gate.

---

#### ADV-005: Z1 is a Ghost Actor
**Severity:** HIGH  
**Category:** Accountability / Undefined Actor  
**CVSS-equivalent:** 7.5 (Unaccountable actions, no audit trail)

**Description:**  
Metadata: "Z1 proposes; Z2 ratifies by hash". But there is **no Z1 node** in the 19-node graph. Z1 is referenced in TC ("every Z1 reply") and MOLT ("session open"), but Z1 has no defined:
- Interface (what does Z1 read/write?)
- Accountability edges (who reviews Z1?)
- Event logging (Z1 actions go to EV? No edge shown.)
- Identity (is Z1 a human? A model? A committee?)

**Evidence:**
```
"note": "All nodes are processes (code that runs). No document nodes. Z1 proposes; Z2 ratifies by hash; Z3 lands; CI enforces."
```
19 nodes listed. 0 named Z1.

**Impact:**  
If Z1 is a human operator (A6), they can:
- Propose arbitrary candidates to Z2 with no record
- Influence TC dials ("every Z1 reply") with no accountability
- Trigger MOLT sessions with no justification

If Z1 is a model, it has no caps, no gate, no ADV review.

**Falsification Test:**  
1. A "Z1" actor submits a proposal to Z2
2. The graph has no node to validate that this actor is authorized
3. Z2 ratifies it
4. The action is logged... somewhere? But no Z1 → EV edge exists
5. Post-hoc audit cannot determine **who** proposed it or **why**

**Remediation:**
- **Option A:** Add Z1 node: Zone 1, Tier 0, reads operator_events, writes proposals to Z2, logs all actions to EV.
- **Option B:** If Z1 is a human, define it as an OM (Operator Model) instance with explicit read/write boundaries.
- **Option C:** Remove all Z1 references from the graph and replace with explicit human-in-the-loop nodes (e.g., HUMAN-REVIEWER-1).

---

#### ADV-006: Q (Priority Queue) is Self-Operating in Zone 2 with No Review
**Severity:** HIGH  
**Category:** Privilege Escalation / Manipulation  
**CVSS-equivalent:** 7.8 (Priority manipulation, wrong work executed)

**Description:**  
Q is in Zone 2 (ratification) but has no ratification of its own. It writes PRIORITY_QUEUE.md, which PRS, AG, OM, and ADV read as work orders. But:
- No ADV edge to Q (no one tests if Q's priorities are correct)
- No Z2 edge to Q (Z2 "ratifies hash and impact pins" but does not review Q's logic)
- Q reads CONST weights — if CONST is poisoned, Q's priorities are poisoned

**Evidence:**
```
"id": "Q",
"zone": 2,
"operator": "Z2 ratifies hash and impact pins",
"enforcement": "only READY top-score rows may start"
```
Who defines "READY"? Q does. Who defines "top-score"? Q does, using CONST weights.

**Impact:**  
An attacker (A3) who poisons CONST weights can:
- Deprioritize security fixes
- Prioritize low-value work
- Starve ADV of resources (ADV is work-ordered by Q)

**Falsification Test:**  
1. MOLT changes Q's weight for "security" from 10 to 0
2. Q now never prioritizes security reviews
3. ADV findings sit at the bottom of the queue
4. The system appears to function (work is being done) but is **insecure by starvation**

**Remediation:**
- **Option A:** Add `ADV → Q` (type: adversarial review) to test Q's priority logic.
- **Option B:** Q's weights must be ratified separately from other CONST values (higher bar).
- **Option C:** Add a Z3 mechanical check that verifies Q's output against a formal priority spec.

---

### 4.3 MEDIUM

---

#### ADV-007: CONST Rollback Has No Propagation Path
**Severity:** MEDIUM  
**Category:** State Consistency / Silent Corruption  
**CVSS-equivalent:** 6.5 (Downstream nodes use stale values)

**Description:**  
MOLT can "revert (mechanical)" CONST values. But CONST → TC, Q, PRS, AG are all **unidirectional read edges**. If CONST reverts a cap from 100 to 50, AG may not know until it tries to exceed 50 and halts. TC may continue scoring with the old dial. Q may keep using the old weight.

**Evidence:**
```
{"source": "MOLT", "target": "CONST", "type": "apply", "label": "apply (ratified) / revert (mechanical)"}
{"source": "CONST", "target": "TC", "type": "read", "label": "dials"}
{"source": "CONST", "target": "Q", "type": "read", "label": "weights"}
```
No `CONST → TC/Q/PRS/AG` of type `notify`, `invalidate`, or `version`.

**Impact:**  
Transient inconsistency. Nodes operate with different versions of CONST until they happen to re-read. In a distributed system, this is a **split-brain** condition.

**Remediation:**
- **Option A:** Version CONST values. All reads must specify version. MOLT revert forces version bump.
- **Option B:** Add `CONST → *` notify edges. Consumers must acknowledge receipt before MOLT completes revert.
- **Option C:** Make CONST reads pull-based with TTL. Consumers re-read every N seconds.

---

#### ADV-008: REG "Append-Only" Contradicts "Merge"
**Severity:** MEDIUM  
**Category:** Semantic Contradiction / Data Integrity  
**CVSS-equivalent:** 6.0 (Ambiguous consistency model)

**Description:**  
REG claims "public record (append-only)". But CIG → REG is a "merge". Merging is mutation. MK checks "consistency FAIL blocks merge" — but append-only logs don't need merge consistency; they need hash-chain validity.

**Evidence:**
```
"id": "REG",
"writes": "public record (append-only)"
```
```
{"source": "CIG", "target": "REG", "type": "merge"}
```

**Impact:**  
The append-only claim is **unenforceable** if merge is the transport mechanism. Git merge can rewrite history (rebase, squash). An append-only log must be strictly sequential with cryptographic chaining.

**Remediation:**
- **Option A:** Make REG a true append-only log (e.g., Merkle tree of signed blocks). CIG "appends" ratified blocks, not merges.
- **Option B:** If Git merge is required for workflow, make REG a **mirror**. The canonical REG is the append-only log; the Git file is a read-only view.

---

#### ADV-009: ST (Stale Sweep) Has No Incoming Data Edges
**Severity:** MEDIUM  
**Category:** Undefined Trigger / Ghost Process  
**CVSS-equivalent:** 5.5 (May never run, or run with stale data)

**Description:**  
ST is a **pure source node** (no incoming edges). It claims to wake on "nightly / on read" and reads "last_read + half-life (CONST)". But:
- No edge shows what ST reads
- ST's `reads` field is `null`
- If CONST half-life changes, ST has no notification path

**Evidence:**
```
"id": "ST",
"reads": null,
"wakes_on": "nightly / on read"
```

**Impact:**  
ST may never trigger, or may trigger with wrong parameters. Stale gaps are never reopened. The system accumulates technical debt.

**Remediation:**
- **Option A:** Add explicit edges: `CONST → ST` (read: half-life), `EV → ST` (trigger: nightly cron event).
- **Option B:** Make ST a scheduled job with explicit input file (e.g., `stale_config.json`).

---

#### ADV-010: NF → Q Edge is Unacknowledged by Q
**Severity:** MEDIUM  
**Category:** Interface Mismatch / Silent Data Loss  
**CVSS-equivalent:** 5.0 (Signal ignored, Brier trends unused)

**Description:**  
NF sends "Brier trend" signal to Q. But Q's `reads` list does not include NF or Brier trends. The edge exists in the graph but is not reflected in the node's interface contract.

**Evidence:**
```
{"source": "NF", "target": "Q", "type": "signal", "label": "Brier trend"}
```
```
"id": "Q",
"reads": ["queue_items.json", "ledgers", "callouts", "CONST weights"]
```

**Impact:**  
NF's signal is **orphaned**. Calibration data does not influence priorities. The system does not learn from its own accuracy metrics.

**Remediation:**
- **Option A:** Add "NF Brier trends" to Q's `reads`.
- **Option B:** Remove the NF → Q edge if it is not used.

---

#### ADV-011: 14 Cycles Are Unacknowledged in Validation
**Severity:** MEDIUM  
**Category:** Documentation / Trust Erosion  
**CVSS-equivalent:** 5.5 (Undocumented feedback loops)

**Description:**  
Validation claims only 2 cycles. Static analysis finds **16 cycles**. The unacknowledged 14 include paths through Z2, CIG, MOLT, and CONST. Each cycle is a potential infinite loop or race condition.

**Evidence:**
Full cycle list:
1. `CIG → REG → MK → CIG` (deadlock — ADV-002)
2. `EV → FS → Z2 → CIG → REG → PRS → EV`
3. `PRS → NF → Q → PRS`
4. `EV → FS → Z2 → CIG → REG → PRS → NF → Q → AG → EV`
5. `NF → Q → OM → NF`
6. `Z2 → CIG → REG → PRS → NF → Q → OM → Z2`
7. `EV → FS → Z2 → CIG → REG → PRS → NF → Q → ADV → EV`
8. `Z2 → CIG → REG → PRS → NF → Q → MOLT → Z2`
9. `TC → EV → FS → Z2 → CIG → REG → PRS → NF → Q → MOLT → CONST → TC`
10. `Q → MOLT → CONST → Q` (acknowledged)
11. `PRS → NF → Q → MOLT → CONST → PRS`
12. `EV → FS → Z2 → CIG → REG → PRS → NF → Q → MOLT → ML → EV`
13. `NF → Q → MOLT → NF`
14. `FS → Z2 → CIG → REG → PRS → NF → Q → MOLT → FS`
15. `Z2 → CIG → REG → PRS → Z2`
16. `FS → Z2 → CIG → REG → FS`

**Impact:**  
Undocumented cycles are **untrusted**. If a cycle causes a race condition or resource exhaustion, operators will not know to look for it.

**Remediation:**
- **Option A:** Catalog all 16 cycles with safety proofs or guard descriptions.
- **Option B:** Add CI lint that fails if graph acquires a new uncatalogued cycle.

---

### 4.4 LOW

---

#### ADV-012: Metadata Claims "No Document Nodes" but REG and Q Write Documents
**Severity:** LOW  
**Category:** Metadata Contradiction  
**CVSS-equivalent:** 3.0 (Documentation error, minor confusion)

**Description:**  
Metadata: "All nodes are processes (code that runs). No document nodes." But REG is "REGISTERED.md" and Q writes "PRIORITY_QUEUE.md". These are documents.

**Evidence:**
```
"note": "All nodes are processes (code that runs). No document nodes."
```
```
"id": "REG", "file": "REGISTERED.md"
"id": "Q", "writes": ["PRIORITY_QUEUE.md", "hash"]
```

**Remediation:**  
Update metadata: "All nodes are processes or process outputs. Document nodes are process artifacts, not static files."

---

#### ADV-013: Ratifications Reference Undefined External Molts
**Severity:** LOW  
**Category:** Dangling Pointer / Stale Reference  
**CVSS-equivalent:** 3.5 (References may dangle)

**Description:**  
The `ratifications` field cites three molts that are not defined in this document:
- `molt-tiers-anticascade-K3-N10-20260906`
- `pq-formula-impact-unblocks-20260906`
- `zone-integer-extend-zone3-20260906`

**Evidence:**
```
"ratifications": {
  "OI-G1": "molt-tiers-anticascade-K3-N10-20260906",
  "OI-G2": "pq-formula-impact-unblocks-20260906",
  "OI-G3": "zone-integer-extend-zone3-20260906"
}
```

**Remediation:**  
Include hashes of the ratified documents, or inline the ratified content, or add `ratified_doc_sha` fields.

---

#### ADV-014: Undefined Terms Break Falsifiability
**Severity:** LOW  
**Category:** Specification Gap  
**CVSS-equivalent:** 4.0 (Cannot verify claims)

**Description:**  
The following terms are used in enforcement clauses but **undefined** in this document:
- "H" (FS: "no H without disproof line")
- "D10" (OM: "D10 predictions resolved")
- "impact pins" (Q operator)
- "anti-cascade rules 1–5" (MOLT enforcement)
- "loop-level falsifier" (MOLT enforcement)
- "IC-030", "IC-031" (edge labels, RC enforcement)
- "B.6" (RC: "session close (B.6)")

**Impact:**  
These terms are **unfalsifiable**. No one can verify whether the system satisfies its own enforcement rules because the rules are not specified.

**Remediation:**  
Define each term in a glossary, or replace with executable invariants (like JESTER-01..07).

---

#### ADV-015: `molt_id` is Null in Metadata
**Severity:** LOW  
**Category:** Self-Reference / Bootstrap Problem  
**CVSS-equivalent:** 2.0 (Document not self-ratified)

**Description:**  
The metadata `molt_id` is `null`. This document describes a ratification system but is **not itself ratified**. The `registered_md_sha` proves the document exists, but does not prove it was approved by the system it describes.

**Evidence:**
```
"molt_id": null
```

**Remediation:**  
This document should be ratified by Z2 and its `molt_id` recorded. Or, add a bootstrap note: "This document is self-ratifying by Z2 hash [SHA]."

---

#### ADV-016: Q Sends Work Orders to Zone 1 from Zone 2
**Severity:** LOW  
**Category:** Zone Hierarchy Violation  
**CVSS-equivalent:** 3.0 (Directional confusion)

**Description:**  
Metadata: "Z1 proposes; Z2 ratifies by hash; Z3 lands; CI enforces." This implies a flow: Z1 → Z2 → Z3. But Q (Zone 2) sends work orders to PRS, AG, OM, ADV (all Zone 1). This is **backwards** — Zone 2 should not command Zone 1.

**Evidence:**
```
{"source": "Q", "target": "PRS", "type": "work_order"}
{"source": "Q", "target": "AG", "type": "work_order"}
```

**Remediation:**  
Either:
- Q is actually Zone 1 (operational), not Zone 2
- Or work orders flow Z1 → Z2, and Z2 ratifies them before Z1 executes
- Or redefine zones to allow operational control from Z2

---

#### ADV-017: No Recovery Procedure Defined for REVERT Events
**Severity:** LOW  
**Category:** Operational Gap  
**CVSS-equivalent:** 3.5 (Manual recovery required)

**Description:**  
MOLT can emit REVERT events. FS can emit REVERT. But no node defines:
- How to recover from a revert
- Who decides when to re-attempt a reverted change
- What happens to downstream nodes that already consumed the reverted state

**Evidence:**
```
"id": "MOLT",
"writes": ["... CONST writes (ratified) / reverts (mechanical)"]
```
```
"id": "FS",
"wakes_on": "end of session; before close; on REVERT"
```

**Remediation:**  
Add a RECOVERY node or define recovery as part of MOLT's mechanical revert path.

---

## 5. ATTACK CHAINS (Compound Exploits)

### Chain 1: Z2 Takeover → Full System Compromise
**Prerequisites:** A1 (Z2 compromise)  
**Steps:**
1. Z2 ratifies a malicious MOLT candidate
2. MOLT applies poisoned CONST values (mechanical revert path)
3. Q uses poisoned weights → deprioritizes security work
4. ADV detects nothing (or detects but has no enforcement path)
5. CIG merges poisoned REG updates
6. MK and OTS seal the corruption
**Result:** System appears healthy but is permanently compromised. **Detection time: indefinite.**

### Chain 2: MOLT Bug → CONST Poisoning → Silent Gate Removal
**Prerequisites:** A2 (MOLT bug)  
**Steps:**
1. MOLT's "code measures and reverts" has an off-by-one error
2. Reverts `J04_window` from 5 to 0
3. `jester_invariants.py`: J-04 window is 0 → `len(win) >= W` is always false → J-04 always NO_GATE
4. Ritual dissent is never detected
5. Critics restate authors indefinitely
**Result:** Quality collapse. **Detection time: until manual audit.**

### Chain 3: CIG-REG-MK Deadlock → Registry Freeze
**Prerequisites:** A4 (DoS)  
**Steps:**
1. Attacker submits PR with hash-mismatched entry
2. MK detects inconsistency → signals FAIL to CIG
3. CIG blocks merge
4. All future PRs blocked (MK only runs on merged state, not proposed state)
5. No new molts, no new constants, no new ratifications
**Result:** System is secure but dead. **Recovery: manual CI override (bypasses all gates).**

### Chain 4: ADV Suppression + Q Starvation → Gate Rot
**Prerequisites:** A3 + A5  
**Steps:**
1. Attacker changes CONST weights to deprioritize ADV
2. ADV runs quarterly but findings sit at bottom of Q
3. ADV detects broken gate, writes to EV
4. FS never scans it (too low priority)
5. Z2 never sees it
6. Gate remains broken for months
**Result:** Gradual security degradation. **Detection time: next external audit (if any).**

### Chain 5: Ghost Z1 → Unaccountable Proposal Flood
**Prerequisites:** A6  
**Steps:**
1. Unknown actor claims to be "Z1"
2. Submits proposals to Z2 with no logging
3. Z2 ratifies (hash looks valid)
4. No audit trail of who proposed or why
5. Post-hoc investigation impossible
**Result:** Accountability collapse. **Detection time: never (no data).**

### Chain 6: ST Failure → Stale Accumulation → Cascade Revert
**Prerequisites:** ADV-009 (ST never triggers)  
**Steps:**
1. ST fails to trigger (no incoming edges)
2. Constants and gaps go stale
3. MOLT eventually detects stale accumulation
4. MOLT triggers "anti-cascade rule 3" (undefined)
5. Mechanical revert cascades through CONST
6. Downstream nodes (TC, Q, PRS, AG) operate with inconsistent state
**Result:** Cascade failure. **Detection time: when AG halts on cap violation.**

---

## 6. FALSIFICATION TESTS

These are concrete tests that would break claimed invariants. They can be run against the system or its simulation.

| Test ID | Target Invariant | Injection | Expected | If Broken |
|---------|------------------|-----------|----------|-----------|
| F-001 | Z2 ratification integrity | Z2 ratifies MOLT candidate that sets `J03_agree_max = 1.0` | CIG should block (no molt_id?) | Sycophancy gate disabled |
| F-002 | MOLT mechanical revert safety | MOLT reverts `J06_window` to 0 | J-06 should detect noise | J-06 always NO_GATE |
| F-003 | CIG-REG-MK liveness | Submit PR with bad hash, then good PR | Good PR should merge | Registry frozen |
| F-004 | ADV enforcement | Break J-05 regex, run ADV | Z2 should receive callout | Gate broken, no action |
| F-005 | Q priority integrity | Change CONST weight for ADV to 0 | ADV should still run | ADV starved |
| F-006 | Z1 accountability | Submit proposal with no Z1 node logging | Should be rejected | Accepted, no audit trail |
| F-007 | CONST propagation | Revert AG cap from 100→50 | AG should know immediately | AG halts later |
| F-008 | REG append-only | Git rebase on REG branch | MK should detect history rewrite | Append-only claim violated |

---

## 7. RECOMMENDATIONS

### Immediate (Block Ratification)
1. **Fix ADV-001:** Add Z2 oversight mechanism. Z2 ratifications must pass ADV review before CIG merge.
2. **Fix ADV-002:** Break CIG-REG-MK deadlock. Add retry queue or ST trigger on MK failure.
3. **Fix ADV-003:** Demote MOLT to Zone 2. Split MOLT-PROPOSE / CONST-APPLY.

### Short-Term (Before Production)
4. **Fix ADV-004:** Give ADV enforcement teeth. Add ADV → Z2 callout for broken gates.
5. **Fix ADV-005:** Define Z1 as a real node with explicit edges and logging.
6. **Fix ADV-006:** Add ADV review of Q priority logic.
7. **Fix ADV-007:** Version CONST values and add propagation notifications.

### Medium-Term (Next Molt Cycle)
8. **Fix ADV-008:** Make REG a true append-only log or clarify the merge model.
9. **Fix ADV-009:** Add explicit trigger edges to ST.
10. **Fix ADV-011:** Catalog all 16 cycles with safety proofs.
11. **Fix ADV-014:** Define all undefined terms as executable invariants.
12. **Fix ADV-015:** Ratify this document (record molt_id).

---

## 8. APPENDICES

### A. Graph Statistics
- Nodes: 19
- Edges: 44
- Cycles: 16 (2 acknowledged, 14 unacknowledged)
- Sink nodes: 1 (OTS)
- Source nodes: 2 (ST, RC)
- Zone 1: 11 nodes, Zone 2: 3 nodes, Zone 3: 5 nodes
- Tier 0: 12 nodes, Tier 1: 2 nodes, Tier null: 5 nodes

### B. Severity Distribution
- CRITICAL: 3 (ADV-001, ADV-002, ADV-003)
- HIGH: 3 (ADV-004, ADV-005, ADV-006)
- MEDIUM: 5 (ADV-007, ADV-008, ADV-009, ADV-010, ADV-011)
- LOW: 6 (ADV-012, ADV-013, ADV-014, ADV-015, ADV-016, ADV-017)

### C. Trust Boundary Map
```
[Z1] --(ghost)--> [Z2] --(unaudited)--> [CIG] --(merge)--> [REG]
                                      |
                                      v
                              [MOLT] --(mechanical)--> [CONST]
                                      |
                                      v
                              [Q] --(work orders)--> [PRS, AG, OM, ADV]
```
The critical path Z2 → CIG → REG → MK → CIG has no external audit. Z2 is the root of trust with no root of trust for Z2.

### D. Glossary of Undefined Terms (from this document)
- **H:** Hypothesis? Claim? Used in FS enforcement.
- **D10:** Time horizon? Metric? Used in OM.
- **Impact pins:** Priority locking mechanism? Used in Q.
- **Anti-cascade rules 1–5:** MOLT safety rules. Undefined.
- **Loop-level falsifier:** MOLT self-test. Undefined.
- **IC-030, IC-031:** Invariant codes. Undefined.
- **B.6:** Document section reference. Undefined.

---

**End of Report**

*This report was generated by adversarial review. All findings are falsifiable. The reviewer does not claim the system is malicious; only that its invariants are insufficiently enforced and its trust boundaries are inadequately guarded.*
