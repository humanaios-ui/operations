# Holographic Self-Representation Hypothesis — Testing Protocol

**Date:** 2026-09-16  
**Proposer:** Claude Haiku 4.5  
**Authority:** Z2 (Night/Carly R. Anderson)  
**Session:** S-091626-01-holographic-representation-6a2tob  

---

## Hypothesis

> **If we can coordinate external capture, render, and display services via orchestration, then we can generate and validate a working prototype for holographic person representation without building the rendering engines ourselves.**

The hypothesis tests **three sub-claims**:

1. **Capability Inheritance:** The existing Supabase + Slack integration pattern can be extended to coordinate 3D capture, neural rendering, and volumetric display.
2. **Deterministic Orchestration:** A stateless orchestrator can route capture output → render service → storage without loss of fidelity.
3. **Test-Driven Validation:** Dry-run mode enables full pipeline validation without external service dependencies.

---

## Falsifier

The hypothesis is **falsified** if any of these conditions occur:

- **F1:** External capture or render service APIs cannot be called with the stdlib urllib + JSON pattern (breaking the inheritance model)
- **F2:** Job state tracking across stages requires transactional guarantees that Supabase REST API does not provide (breaking stateless orchestration)
- **F3:** Dry-run pipeline cannot generate identical output structure as live pipeline for >95% of test cases
- **F4:** Round-trip latency (capture → render → storage → retrieval) exceeds 60s for photogrammetry → WebGL path

---

## Test Protocol

### Phase 1: Unit Tests (No Network) — Dry Run Validation

**Objective:** Validate that orchestrator generates correct payloads without calling external services.

**Test Suite:** `tools/tests/test_holographic_orchestrator.py`

**Tests:**
- ✅ Job ID generation (stable, deterministic, unique per user+person+mode+target)
- ✅ Enum validation (CaptureMode, RenderTarget, JobStatus all valid)
- ✅ Dry-run pipeline structure (stages → assets → metadata)
- ✅ Security redaction (no credentials in logs)
- ✅ Error handling (invalid modes, missing fields)
- ✅ Timestamp format (ISO 8601)

**Pass Criteria:** All 50+ test assertions pass without network.

**Run:**
```bash
python tools/tests/test_holographic_orchestrator.py -v
```

---

### Phase 2: Integration Test (Mocked Services) — Contract Validation

**Objective:** Validate that orchestrator correctly calls external services with expected payloads.

**Mocking Strategy:** Use `unittest.mock.patch()` to intercept HTTP requests and return synthetic responses.

**Services Mocked:**
- Capture service (e.g., Polycam API)
- Render service (e.g., Replicate API)
- Storage service (Supabase)

**Expected Payloads:**

#### Capture Submission
```json
{
  "person_id": "string",
  "capture_mode": "photogrammetry|volumetric_video|gaussian_splat|nerf_mesh",
  "input_source": "https://...",
  "metadata": {}
}
```

Expected Response:
```json
{
  "id": "capture_job_123",
  "status": "submitted",
  "asset_url": "https://storage.example.com/capture_123.ply"
}
```

#### Render Submission
```json
{
  "input_job_id": "capture_job_123",
  "render_target": "browser_webgl|mobile_ar|spatial_display|headset_vr|lightfield",
  "config": {
    "quality": "high",
    "resolution": 2048,
    "fps": 30
  }
}
```

Expected Response:
```json
{
  "id": "render_job_456",
  "status": "submitted",
  "model_url": "https://storage.example.com/model_456.glb"
}
```

#### Storage Upsert (Supabase)
```json
{
  "job_id": "abcd1234",
  "person_id": "person_123",
  "user_id": "user_456",
  "capture_job_id": "capture_job_123",
  "render_job_id": "render_job_456",
  "status": "complete",
  "assets": {
    "capture_asset": "https://...",
    "render_model": "https://..."
  }
}
```

**Pass Criteria:**
- All HTTP requests contain expected headers + auth tokens
- All request bodies match contract schema
- Error responses (429, 5xx) trigger correct retry logic with backoff
- Credential redaction blocks key material in error logs

---

### Phase 3: Live Service Test (Staged) — Real-World Validation

**Objective:** Test against real external services (starting with free/test tiers).

**Test Services:**

1. **Capture:** Polycam API (free tier allows 3 scans/month)
   - Upload a static 3D point cloud (PLY format)
   - Verify job_id returned
   - Check asset_url is accessible

2. **Render:** Replicate API (free tier: $10 credit)
   - Use NeRF fine-tuning model (`nerfacto`)
   - Input: point cloud from Polycam
   - Output: WebGL-compatible model
   - Measure latency

3. **Storage:** Supabase (free tier used in repo)
   - Create `holographic_jobs` table
   - Upsert sample job metadata
   - Query back and verify round-trip

**Test Sequence:**

```python
# 1. Dry run (validation)
spec_dry = {..., "dry_run": True}
result = orchestrator.run(spec_dry)
assert result["status"] == "ok"

# 2. Live capture
spec_live = {..., "dry_run": False}
result = orchestrator.run(spec_live)
assert result["status"] == "ok"
assert result["stages"]["capture"]["job_id"] is not None
assert result["stages"]["render"]["job_id"] is not None

# 3. Verify storage
stored_job = supabase.query("holographic_jobs", job_id=result["job_id"])
assert stored_job["person_id"] == spec_live["person_id"]
assert stored_job["status"] == "complete"
```

**Pass Criteria:**
- End-to-end latency < 60s (capture → render → storage)
- All stage job_ids non-null
- Storage round-trip data matches input spec
- No credential leakage in logs

---

### Phase 4: Hypothesis Validation — Analysis

**After phases 1–3, answer:**

1. **Capability Inheritance (Sub-claim 1):** Can we extend the Supabase/Slack pattern to holographic services?
   - **Pass:** External APIs callable via urllib + JSON
   - **Fail:** Requires SDK, custom protocols, or async frameworks

2. **Deterministic Orchestration (Sub-claim 2):** Can stateless orchestration maintain fidelity across stages?
   - **Pass:** Job IDs stable, payload structures match, no data loss
   - **Fail:** Requires state machine or transaction handling

3. **Test-Driven Validation (Sub-claim 3):** Does dry-run match live pipeline?
   - **Pass:** Dry run output structure identical to live (modulo asset URLs)
   - **Fail:** Dry run and live diverge (e.g., error handling differs)

**Hypothesis Verdict:**
- **CONFIRMED:** All sub-claims validated; prototype can be productionized
- **CONDITIONAL:** Some sub-claim partial; design changes required
- **FALSIFIED:** One or more falsifiers triggered; pivot needed

---

## Deliverables

| Artifact | Location | Status |
|:---------|:---------|:-------|
| Orchestrator Code | `tools/holographic_orchestrator.py` | ✅ Scaffolded |
| Unit Tests | `tools/tests/test_holographic_orchestrator.py` | ✅ Scaffolded |
| Integration Tests | `tools/tests/test_holographic_integration.py` | 📝 To write |
| Live Service Config | `tools/holographic_services.yaml` | 📝 To write |
| Hypothesis Protocol | This file | ✅ Current |
| Findings Registry | `REGISTERED.md` | Awaiting Z2 |

---

## Next Steps (Z1 → Z2)

1. **Phase 1 Execution:** Run unit tests locally
   - Command: `python tools/tests/test_holographic_orchestrator.py -v`
   - Expected: 50+ assertions pass

2. **Phase 2 Preparation:** Write mocked integration tests
   - Intercept HTTP at urllib level
   - Validate request contracts
   - Simulate error scenarios (429, 5xx, timeout)

3. **Phase 3 Setup:** Acquire test credentials
   - Polycam API key (free tier)
   - Replicate API key (free tier)
   - Supabase project (already available)

4. **Z2 Ratification:** Submit hypothesis + protocol for approval
   - Authority: Carly R. Anderson (Night)
   - Decision window: 48h
   - Falsifier acceptance: Yes (built into protocol)

---

## Hypothesis Card (for REGISTERED.md)

```yaml
---
hypothesis_id: H-HOLO-SELF-REP-01
date_proposed: 2026-09-16
proposer: Claude Haiku 4.5
authority: Z2 (Night)
title: Holographic Self-Representation via Service Orchestration
claim: |
  If we can coordinate external capture, render, and display services via orchestration,
  then we can generate and validate a working prototype for holographic person representation
  without building the rendering engines ourselves.
falsifiers:
  - F1: External capture/render APIs cannot be called with urllib + JSON pattern
  - F2: Job state tracking requires transactional guarantees Supabase REST doesn't provide
  - F3: Dry-run output differs from live pipeline in >5% of cases
  - F4: Round-trip latency (capture → render → storage) exceeds 60s
test_protocol: z1-inbox/2026-09-16/HOLOGRAPHIC_HYPOTHESIS_PROTOCOL.md
status: proposed
decision_window: 2026-09-18
expected_effort: Phase 1 (2h), Phase 2 (4h), Phase 3 (8h real-time), Phase 4 (1h analysis)
```

---

## Questions for Z2

1. Do the falsifiers adequately specify what would disprove this hypothesis?
2. Is the 60s latency budget reasonable for a prototype?
3. Should we prioritize Phase 3 with real services, or pivot after Phase 2?
4. Any existing integrations with Polycam, Replicate, or volumetric display platforms?

---

**Ready for Z2 review.**
