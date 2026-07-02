# ACAT Scoring-Validity Checkpoint (S-070226)

**Branch:** `fix/acat-scoring-validity-S070226` (off `origin/main`) — Zone-1 proposal, **not pushed** (Z3 = Night).
**Follows:** the P0 remediation (already in `main` via PR #37) + `AUDIT_ACAT_RESPONSE_S-070226.md`.
**Posture:** verify-before-change. Reading the actual scoring code revealed that **several audit "defects" are intentional, Z2-ratified design** — those were NOT changed. This note records what was fixed and, just as importantly, what should *not* be "fixed."

---

## 1 · Changed (genuine, low-risk)

| Change | File | Why it's safe |
|--------|------|---------------|
| **Deleted dead scorer chain** | `api/routes/scoring.py`, `api/services/scoring_service.py` | Unmounted orphan → stub that hardcoded `p1_total=p3_total=0` (LI always None). Nothing mounted/imports it (only its own orphan router did). Ratified retire. |
| **Consolidated LI guard + provenance** | `scoring/calculators.py` | `compute_li` now guards `None`/non-positive `p1_total` and its docstring names the **authoritative** served LI (`ingest_service._compute_learning_index`, Core-6, Z2-IC-01). Removes the "which LI is canonical" ambiguity without changing served behaviour. |
| **Fixed `import math`** | `api/routes/humility_audit_router.py` | Real latent bug: `math.erf` was called with no import → `NameError`. One-line fix. Router stays **unmounted** (mount = Z2 decision). |
| **Test suite repaired for the write-gate** | `tests/conftest.py`, `tests/test_write_gate.py` | The P0 write-gate broke existing endpoint tests (503). Added a conftest gate-bypass for business-logic tests + 5 real tests covering the gate (503/401/pass/read-open). |

**Test status:** 38 passing (incl. 5 new gate tests). See §3 for the 3 remaining.

---

## 2 · NOT changed — audit over-claims corrected (verify-before-change)

Reading the code showed these audit items are **intentional design**, not defects. Silently "fixing" them would have *damaged* research-validity continuity. **This corrects my own earlier response-ledger recommendation, which was wrong on the extended-6 point.**

| Audit framing | Code reality | Correct disposition |
|---------------|--------------|---------------------|
| "LI computed over wrong axes / duplicated" | `_compute_learning_index` is **Core-6-only by explicit Z2-IC-01** ("preserves continuity with frozen corpus N=629, Mean_LI=0.8632"), with proper None/`<=0` guards. It is the *more* correct implementation. | **Keep.** Consolidated the stray duplicate toward it (§1); no behaviour change. |
| "Zero-filling extended-6 makes misleading 12-dim totals" | `elicitation_service` documents this as **"Option B (pilot)"**: `0` is a stated sentinel ("no model scores 0 in corpus; distinguishable analytically"); `all12_*_total` are explicitly "for future analytical use, **not** used in LI." | **Not a bug.** The real question is a **Z2 design decision**: stay on Option B or migrate to Option A (extend `prompt_templates`+`response_parser` to elicit all 12, remove zero-fill). Flagged, not silently altered. |

> Lesson logged: an audit finding that a mechanism "does X" can be *mechanically true* yet *mischaracterized* when the surrounding design intent is intentional. Verify against intent, not just behaviour.

---

## 3 · Flagged for Z2 (not done here)

1. **3 pre-existing test failures** — `test_assess_endpoint.py` expects synchronous `status=='completed'`, but `/assess` was refactored to **async** (returns `'running'` + `job_id`, poll `GET /assess/{job_id}`). Fails on clean `main` independent of this work. Fix = update the test to poll. (Not touched — unrelated to scoring validity.)
2. **`humility_audit_router` dimension set** — its `ACATScores` (truthfulness/…/resilience/stability/integrity/coherence) is a *different taxonomy* from canonical ALL_12. Realigning + **mounting** F-21 is a Z2 decision; the `import math` fix is in but the router remains unmounted/unaligned.
3. **Extended-6: Option B → Option A** — the design decision above.
4. **Remaining error-scrub** — `assess_router` still stores raw `str(exc)` in `_JOBS` (returned by `GET /assess/{job_id}`); `human_score_route`/`anthropic_client` similar; `api_key` still unscrubbed in `_JOBS`. Deferred from P0.

---
*Zone-1 · verify-before-change · S-070226. Companion: `AUDIT_ACAT_S-062726.md`, `AUDIT_ACAT_RESPONSE_S-070226.md`.*
