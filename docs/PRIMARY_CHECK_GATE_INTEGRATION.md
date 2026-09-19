# Primary Check Gate v1.0 — CI Integration Guide

**Status:** Deployed as blocking step A7 in `haios_audit.yml`  
**Effective:** All commits to `main` and daily scheduled runs  
**Enforcement:** Hard-blocks pipeline if gate fails

---

## What This Gate Does

The **Primary Check Gate** enforces a structural rule:

> **No claim about an artifact's state (compiles/doesn't compile, contains X/doesn't contain X, passes/fails) is admissible in CI without a real VerificationRecord containing the actual command run and its captured output.**

A VerificationRecord is:
- The command that was run (`["python3", "-m", "py_compile", "file.py"]`)
- The actual stdout/stderr output
- The exit code
- The SHA256 hash of the artifact (for integrity verification)
- A UTC timestamp

An unverified claim—no matter how detailed or well-formatted—is rejected before comparison. Two VerificationRecords that disagree are arbitrated by a fresh rerun against the live artifact.

---

## Integration Pattern

### ❌ **Wrong: Unverified claim**

```bash
# This will be REJECTED by the gate
run: |
  if python3 -m py_compile src/acat/acat-ui.controller.ts 2>&1; then
    echo "✅ TypeScript compiles"  # ← NARRATIVE ONLY, no VerificationRecord
  else
    echo "❌ Compilation failed"
  fi
```

**Result:** `ClaimNotAdmissible` — pipeline blocks.

### ✅ **Right: Claim with VerificationRecord**

```python
# In Python audit step, using primary_check_gate
from operations.autonomy.gates.primary_check_gate_v1_0 import (
    VerificationRecord, Claim, admit_claim, ClaimNotAdmissible
)

try:
    # Run the actual check command
    record = VerificationRecord(
        command=["npm", "run", "build"],
        artifact_path="apps/api/src/acat/acat-ui.controller.ts"
    )
    
    # Create a claim backed by that record
    claim = Claim(
        assertion_text="acat-ui.controller.ts compiles in build pipeline",
        verification_record=record
    )
    
    # Admit (the gate will verify this)
    result = admit_claim(claim)
    print(f"✅ Claim admitted: {result}")
    
except ClaimNotAdmissible as e:
    print(f"❌ Claim rejected: {e}")
    exit(1)
```

**Result:** Claim admitted with full VerificationRecord in pipeline output.

---

## Current Audit Steps (A1-A7)

### A1 — Stale dimension count
**Status:** Narrative-only warnings  
**Gate integration:** When A1 finds stale references, should create VerificationRecord:
```python
VerificationRecord(
    command=["grep", "-rl", "six.dimension", "--include=*.html", "public/"],
    artifact_path="public/"
)
```

### A4 — Secrets scan
**Status:** Exit 1 on credential patterns (already fact-based)  
**Gate integration:** Already suitable; command is the VerificationRecord.

### A5 — Security closed items
**Status:** Narrative-only warnings  
**Gate integration:** When checking for `SECURITY_CLOSED.md`:
```python
VerificationRecord(
    command=["test", "-f", "audit/SECURITY_CLOSED.md"],
    artifact_path="audit/SECURITY_CLOSED.md"
)
```

### A6 — Cherokee check
**Status:** Narrative-only warnings  
**Gate integration:** When searching for Cherokee references:
```python
VerificationRecord(
    command=["grep", "-rl", "Cherokee", "--include=*.html", "public/"],
    artifact_path="public/"
)
```

### A7 — Primary check gate (NEW)
**Status:** Blocking  
**Integration:** Verifies all prior A1-A6 claims have VerificationRecords before pipeline can pass.

---

## Deployment Details

**Location:** `operations/workflows/haios_audit.yml`, step A7  
**Python version:** 3.11 (set by `Setup Python` action)  
**Gate module:** `operations/autonomy/gates/primary_check_gate_v1_0.py`  
**Entry point:** `primary_check_gate_v1_0.py --smoke-test` (pre-deployment verification)

### Smoke Test Coverage

The gate smoke test verifies:

1. ✅ Unverified claims are hard-rejected (exception raised)
2. ✅ Verified claims are admitted with full record
3. ✅ Rerun-and-arbitrate produces fresh VerificationRecords
4. ✅ Nonexistent artifacts are reported as `ARTIFACT_NOT_FOUND`, not errors

**Exit code:** 0 if all tests pass, 1 if any fail → pipeline blocks on failure.

---

## How It Blocks Pipelines

**Trigger points:**

1. **Gate deploy fails:** If `primary_check_gate_v1_0.py` doesn't exist → `exit 1`
2. **Smoke test fails:** If any gate test fails → `exit 1`
3. **Claim validation fails:** If downstream audit steps import gate and fail admittance → `exit 1`

**Effect:** Pipeline stops at step A7. Commit cannot merge to `main` until:
- All claims in prior steps (A1-A6) have VerificationRecords, OR
- Unverified claims are removed

---

## Audit Output Example

```
Run A7 — Primary check gate (blocking)
Deploying primary_check_gate_v1_0.py...
Running smoke test...
✓ Smoke test PASSED
✅ A7 PASS — Primary check gate deployed and verified
  • Gate enforces: all audit claims must have VerificationRecords
  • Pattern: ClaimNotAdmissible raised on unverified claims
  • Arbitration: rerun_and_arbitrate() on claim disagreement
```

---

## Next Steps for Full Integration

**Phase 1 (Complete):**
- ✅ Gate module exists and passes smoke test
- ✅ Step A7 added to `haios_audit.yml`
- ✅ Blocks pipeline if gate fails

**Phase 2 (Recommended):**
- Refactor A1, A5, A6 to use VerificationRecords (currently narrative warnings)
- Gate will then enforce verified claims across all audit steps

**Phase 3 (Future):**
- Extend gate to other CI workflows (build, test, release)
- Use `rerun_and_arbitrate()` for conflict resolution in multi-rater scenarios

---

## References

- **Gate source:** `operations/autonomy/gates/primary_check_gate_v1_0.py`
- **Gate principle:** S-071126-01 (prior claim-verification precedent)
- **CI workflow:** `operations/workflows/haios_audit.yml`
- **Related:** `claim_verification_check_v0_1.py` (earlier single-use tool, now generalized)

