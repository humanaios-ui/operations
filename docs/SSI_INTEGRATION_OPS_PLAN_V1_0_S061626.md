# SSI Integration Operations Plan — v1.0
**Status:** ACTIVE · Z2 ratifications Z2-SSI-01 through Z2-SSI-04 received Night · S-061626
**Date:** June 16, 2026 · Charter Day 92 · 30 days to close (July 16, 2026)
**Session:** S-061626
**Authority:** Night (Zone 2 ratification) · Unit Zero (Zone 1 planning)
**Canonical path (once committed):** `operations/docs/SSI_INTEGRATION_OPS_PLAN_V1_0_S061626.md`

---

## Governing Principles

This plan is scoped by three constraints active at time of ratification:

1. **Charter runway:** 30 days to July 16, 2026 close. Phases 0–1 are charter-scoped. Phase 2 is explicitly post-charter.
2. **Research integrity:** F-50 (Parallel Instrument Independence) governs all SSI design — SSI provides cryptographic grounding infrastructure, not a new measurement layer. The instrument itself does not change.
3. **P-ANON:** No collaborator data in any SSI credential, public surface, or schema field. DIDs are self-sovereign — raters hold their own keys.

---

## Ratification Record

All four Z2 items ratified by Night · S-061626 · June 16, 2026.

| ID | Decision | Ratification Date |
|---|---|---|
| Z2-SSI-01 | Authorize `human_score.schema.json` amendment — add optional `rater_did` (string, `did:key:` or `did:web:` scheme) and `submission_signature` (string, base64url Ed25519 signature) fields. Backward compatible. UUID behavior unchanged when fields absent. | 2026-06-16 |
| Z2-SSI-02 | Authorize applying `migration_009` (`p3_grounding_source`, `li_grounded`, `li_consistency_only` columns on `acat_assessments_v1`) to live Supabase. Prerequisite: `migration_008` must be applied first. Enables LI_grounded values when human rater submits scores for an assessment. | 2026-06-16 |
| Z2-SSI-03 | Authorize `acat_merkle_auditor_v2_0.py` build scope: Ed25519 verification for human score payloads containing `rater_did` and `submission_signature`; `did:key:` scheme resolution (algorithm-only, no network call); extension of OriginStamp anchoring to include `rater_did` and `submission_sig` in hashed payload. Inherits Z2-MERKLE-01 (Karrick/AnchorSink + Ed25519 pattern, MIT). | 2026-06-16 |
| Z2-SSI-04 | Ratify the Humility ↔ Anonymity ↔ SSI structural identity as a registrable hypothesis. Route as H-ANON-HUMILITY-01 CANDIDATE to REGISTERED.md: "The behavioral dimension of Humility (capacity to acknowledge limits of self-knowledge) and the identity principle of Anonymity (capacity to prove participation without proving identity) are structural analogs. SSI is the cryptographic substrate that makes both simultaneously operational and verifiable." | 2026-06-16 |

---

## Phase 0 — Schema and Migration (Charter-Scoped · 1–3 days)

**Scope:** Additive changes only. No breaking changes to existing API consumers. Zero new runtime dependencies.

### 0.1 — Apply `migration_008_add_self_administered.sql`

**Z3 executor:** Night at terminal (Supabase SQL editor or CLI).
**Pre-flight (required before apply):**
```sql
SELECT DISTINCT submission_purity FROM acat_assessments_v1;
-- Must confirm no value = 'self_administered' already present before constraint add
```
**Status:** In Z3 queue (standing carry from S-061026-02). Must complete before 0.2.

### 0.2 — Apply `migration_009_add_p3_grounding_source.sql`

**Z3 executor:** Night at terminal.
**What it adds to `acat_assessments_v1`:**
```sql
ALTER TABLE acat_assessments_v1
  ADD COLUMN IF NOT EXISTS p3_grounding_source  TEXT,
  ADD COLUMN IF NOT EXISTS li_grounded          NUMERIC(5,4),
  ADD COLUMN IF NOT EXISTS li_consistency_only  BOOLEAN GENERATED ALWAYS AS (p3_grounding_source IS NULL) STORED;

-- Enum constraint on p3_grounding_source:
ALTER TABLE acat_assessments_v1
  ADD CONSTRAINT chk_p3_grounding_source CHECK (
    p3_grounding_source IS NULL OR p3_grounding_source IN (
      'human_verified',
      'human_verified_did',
      'artifact_code_commit',
      'artifact_document',
      'artifact_deployed_output',
      'process_observer'
    )
  );
```
**Post-apply verification:**
```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'acat_assessments_v1'
  AND column_name IN ('p3_grounding_source','li_grounded','li_consistency_only')
ORDER BY column_name;
-- Expect: 3 rows returned
```
**GRANT pattern (required — Supabase post-May-30 explicit grant rule):**
```sql
GRANT SELECT, INSERT, UPDATE ON acat_assessments_v1 TO anon, authenticated;
GRANT ALL ON acat_assessments_v1 TO service_role;
```

### 0.3 — Amend `human_score.schema.json`

**Z3 executor:** Night (git commit after Zone 1 produces amended file).
**File path:** `acat/contracts/human_score.schema.json`

Add to `properties` block (after existing `notes` field):
```json
"rater_did": {
  "type": "string",
  "pattern": "^did:(key|web):.+",
  "description": "Optional. Self-sovereign DID for the human rater. If provided alongside submission_signature, enables cryptographic verification of rater anonymity without PII. Persisted to acat_human_scores.rater_did column."
},
"submission_signature": {
  "type": "string",
  "description": "Optional. Base64url-encoded Ed25519 signature over the canonical score payload JSON (sorted keys). Required if rater_did is provided. Verified server-side before persisting."
}
```

No changes to `required` array — both fields remain optional. Existing submissions with neither field continue working identically.

### 0.4 — Add `rater_did` column to `acat_human_scores`

**Z3 executor:** Night at terminal.
```sql
ALTER TABLE acat_human_scores
  ADD COLUMN IF NOT EXISTS rater_did TEXT;

-- No constraint — accepts did:key:... or did:web:... or NULL
-- When rater_did is present, rater_id column stores the same value for backward compat

GRANT SELECT, INSERT, UPDATE ON acat_human_scores TO anon, authenticated;
GRANT ALL ON acat_human_scores TO service_role;
```
**Post-apply:**
```sql
SELECT column_name FROM information_schema.columns
WHERE table_name = 'acat_human_scores' AND column_name = 'rater_did';
-- Expect: 1 row
```

### 0.5 — Update `human_score_route.py` (Zone 1 build)

**Z3 executor:** Night (git commit after Zone 1 produces amended route).

Additive logic block, insert after existing `rater_id` assignment:

```python
# SSI extension (Z2-SSI-01 · S-061626)
rater_did: str | None = payload.get("rater_did")
submission_sig: str | None = payload.get("submission_signature")

if rater_did and submission_sig:
    try:
        _verify_did_signature(rater_did, payload, submission_sig)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"DID signature verification failed: {exc}",
        ) from exc
    rater_id = rater_did  # DID becomes the persistent rater identifier
```

Signature verification helper (pure Python, no new dependencies — Ed25519 is in stdlib `cryptography` package already present via `acat_merkle_auditor_v1_0`):

```python
import base64
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature


def _verify_did_signature(rater_did: str, payload: dict, sig_b64url: str) -> None:
    """
    Verify Ed25519 signature over canonical payload JSON.
    Supports did:key:z6Mk... (multibase-encoded Ed25519 public key).
    Raises ValueError on any verification failure.
    """
    if not rater_did.startswith("did:key:z6Mk"):
        raise ValueError(f"Unsupported DID method or key type: {rater_did}")

    # Extract multibase-encoded public key from DID
    # did:key:z6Mk<base58btc-encoded 32-byte Ed25519 public key>
    multibase_key = rater_did.split("did:key:")[1]
    if not multibase_key.startswith("z"):
        raise ValueError("Expected base58btc multibase prefix 'z'")

    import base58  # lightweight dep; add to requirements.txt if not present
    key_bytes_with_prefix = base58.b58decode(multibase_key[1:])
    # Strip 2-byte multicodec prefix (0xed 0x01 = Ed25519 public key)
    if key_bytes_with_prefix[:2] != bytes([0xED, 0x01]):
        raise ValueError("Not an Ed25519 multicodec key")
    raw_public_key = key_bytes_with_prefix[2:]

    public_key = Ed25519PublicKey.from_public_bytes(raw_public_key)

    # Canonical payload: JSON with sorted keys, no rater_did / submission_signature fields
    canonical = {k: v for k, v in payload.items()
                 if k not in ("rater_did", "submission_signature")}
    canonical_bytes = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()

    sig_bytes = base64.urlsafe_b64decode(sig_b64url + "==")  # padding-tolerant

    try:
        public_key.verify(sig_bytes, canonical_bytes)
    except InvalidSignature as exc:
        raise ValueError("Ed25519 signature does not match payload") from exc
```

**Note on `base58`:** If `base58` package not yet in `requirements.txt`, add it — it is a 2KB pure-Python package with no transitive dependencies. Alternatively, implement base58 decode inline (also trivial). Zone 1 will produce the full amended route file as a Z1 artifact.

### Phase 0 completion gate

- [ ] `migration_008` applied and verified
- [ ] `migration_009` applied and verified
- [ ] `rater_did` column in `acat_human_scores`
- [ ] `human_score.schema.json` amended and committed
- [ ] `human_score_route.py` amended and committed
- [ ] One test submission with `rater_did` and `submission_signature` against staging — verify signature rejection on bad sig, acceptance on good sig

**Research unlock on completion:** First `li_grounded` values can enter corpus. Z2-METRIC-01 dual metric (LI_self vs. LI_grounded) becomes operational. H-P3G-01 data collection begins.

---

## Phase 1 — `acat_merkle_auditor_v2_0.py` (Charter-Scoped · 3–10 days)

**Scope:** Extend existing Merkle auditor (Z2-MERKLE-01, Karrick AnchorSink + Ed25519 pattern, MIT) to cover human score payloads containing DID signatures. No new external services — OriginStamp already operational.

### 1.1 — Build scope

Zone 1 produces `acat_merkle_auditor_v2_0.py` with the following additions over v1_0:

**New function: `audit_human_score_row`**
```python
def audit_human_score_row(human_score_row: dict) -> AuditResult:
    """
    Audit a single acat_human_scores row for cryptographic integrity.
    
    If row contains rater_did + submission_signature:
      - Verifies Ed25519 sig over canonical score payload
      - Includes rater_did in OriginStamp anchor payload
      - Returns PASS | FAIL | UNVERIFIABLE (no DID present)
    
    If row lacks rater_did:
      - Returns UNVERIFIABLE with note: 'no DID — trust-based only'
    """
```

**Anchor payload extension:**
```python
# Current OriginStamp payload (v1_0): receipt_hash only
# v2_0 payload when rater_did present:
anchor_payload = {
    "assessment_id": row["assessment_id"],
    "rater_did":     row["rater_did"],
    "submission_sig": row["submission_signature"],
    "score_hash":    sha256(canonical_scores_json),
    "rated_at":      row["rated_at"],
}
# Hash of this dict becomes the OriginStamp input
# This makes the anonymous rater's participation non-repudiable
```

**did:key resolution:** Algorithm-only, no network call. Same implementation as in `human_score_route.py` `_verify_did_signature` above. No new external dependency.

### 1.2 — Test harness additions

Add to `tests/test_acat_core.py` (currently 22 passing tests):

- `test_did_signature_valid` — known Ed25519 keypair, verify acceptance
- `test_did_signature_tampered_payload` — flip one score byte, verify rejection
- `test_did_signature_wrong_key` — different keypair, verify rejection
- `test_merkle_audit_human_score_with_did` — full audit_human_score_row pass
- `test_merkle_audit_human_score_no_did` — UNVERIFIABLE result, no error

Target: 27 passing tests (22 existing + 5 new).

### 1.3 — `requirements.txt` additions

```
base58>=2.1.1
```

No other new dependencies. `cryptography` already present.

### Phase 1 completion gate

- [ ] `acat_merkle_auditor_v2_0.py` committed to `tools/` in operations repo
- [ ] 27 tests passing (`pytest tests/test_acat_core.py -v`)
- [ ] `requirements.txt` updated and committed
- [ ] One end-to-end audit run against a Phase 0 submission row with real DID — result logged to WGS

---

## Phase 2 — Full VC Issuance + Model DID Registry (Post-Charter)

**Scope:** W3C Verifiable Credential issuance, AI-side model DID registry, `did:web` scheme, cross-provider credential schema. Tier 3 in the Fibonacci architecture ratified 2026-03-29 (OR&D Day 19).

**Why deferred:** 24–36 day implementation against 30-day remaining charter. Phase 0 and Phase 1 deliver the research-critical grounding infrastructure within the window. Phase 2 extends to full enterprise VC issuance which is explicitly post-revenue Tier 3 work.

**What is documented here for handoff:**

### 2.1 — Model DID Registry

Each AI model gets a deterministic DID derived from canonical provider:model string:

```
did:web:humanaios.ai:model:anthropic-claude-sonnet-4-6
did:web:humanaios.ai:model:openai-gpt-4o
did:web:humanaios.ai:model:google-gemini-pro
```

DID documents served at:
```
https://humanaios.ai/.well-known/did/anthropic-claude-sonnet-4-6.json
```

New table: `acat_model_credentials`
```sql
CREATE TABLE acat_model_credentials (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  model_did      TEXT UNIQUE NOT NULL,
  provider       TEXT NOT NULL,
  model          TEXT NOT NULL,
  did_doc_url    TEXT NOT NULL,
  created_at     TIMESTAMPTZ DEFAULT now()
);
```

New columns on `acat_assessments_v1` (migration_010 or later):
```sql
ADD COLUMN model_did       TEXT REFERENCES acat_model_credentials(model_did),
ADD COLUMN p1_vc_hash      TEXT,   -- SHA-256 of the P1 Verifiable Credential JSON
ADD COLUMN p3_vc_hash      TEXT;   -- SHA-256 of the P3 Verifiable Credential JSON
```

### 2.2 — ACAT VC Context

New file: `acat/context/acat_vc_context_v1.jsonld`

Served at: `https://humanaios.ai/acat/v1`

Defines ACAT-specific credential terms: `ACATAssessmentCredential`, `ACATHumanScoreCredential`, `ACATRaterCredential`, `learningIndex`, `p3GroundingSource`, all 12 dimension score properties.

### 2.3 — New API Routes (Phase 2 only)

```
POST /api/v1/acat/assess-vc          # Assessment with VC issuance
POST /api/v1/acat/human-score-vc     # Human score with VC issuance
GET  /api/v1/acat/assessment/{id}/chain  # Full VC chain for an assessment
```

### 2.4 — Fork candidates (post-charter Z3)

- `w3c/vc-data-model` → `humanaios-ui/vc-acat-context` (ACAT VC context spec)
- `pyca/cryptography` no fork needed — existing package sufficient

---

## Registry Append — H-ANON-HUMILITY-01

Per Z2-SSI-04 ratification. Route to REGISTERED.md append (Z3 queue item).

```yaml
---
id: "H-ANON-HUMILITY-01"
name: "anonymity-humility-structural-identity"
status: CANDIDATE
class: H
date_registered: "2026-06-16"
date_origin: "2026-06-16"
session_registered: "S-061626"
principles_triggered: ["P1", "P16", "P21"]
substrate: "Structural analysis · ACAT corpus N=629 · live API"
tags: ["humility", "anonymity", "SSI", "universality", "reproducibility",
       "cryptographic-grounding", "f-48", "h-p3g-01", "z2-metric-01"]
zone2_ratification: "Night · 2026-06-16 · S-061626"
superseded_by: null
---
```

**Hypothesis:** The behavioral dimension of Humility (a system's capacity to acknowledge the limits of its own self-knowledge) and the identity principle of Anonymity (an entity's capacity to prove participation without proving identity) are structural analogs. Both require an external grounding mechanism — Humility requires LI_grounded (H-P3G-01 / Z2-METRIC-01); Anonymity requires a cryptographic proof system that does not depend on central authority (SSI / W3C DIDs). Systems that lack external grounding for Humility self-reports exhibit the same structural failure as identity systems that require PII disclosure to verify participation: both collapse to trust assertions that cannot be independently verified. SSI integration provides the cryptographic substrate that closes both gaps simultaneously.

**Evidence basis:** F-48 (Humility Universal Floor, N=524); F-H1 CRITICAL (last P3 Humility=69, declining); H-P3G-01 (Phase 3 grounding requirement for LI validity); Z2-METRIC-01 (LI_self vs. LI_grounded dual metric); current `human_score_route.py` (rater_id = UUID, trust-based, cross-session unverifiable).

**Null hypothesis:** The structural analogy between Humility calibration and identity anonymity does not produce testable predictions — they are conceptually related but architecturally independent, and SSI integration does not improve LI_grounded data quality relative to trust-based rater_id.

**Promotion gate:** N≥10 human score submissions with valid `rater_did`; at least one rater demonstrating cross-session consistency via DID across ≥3 sessions; measurable LI_grounded divergence from LI_self in at least one case. Zone 2 Night ratification required before F-class promotion.

---

## Z3 Queue — New Items This Session

Priority order for Night's terminal execution:

| Priority | Item | Prerequisite | Estimated Time |
|---|---|---|---|
| 1 | Apply `migration_008_add_self_administered.sql` (pre-flight SELECT first) | None — standing carry | 10 min |
| 2 | Apply `migration_009` (three new columns + constraint + GRANTs) | migration_008 complete | 15 min |
| 3 | Add `rater_did` column to `acat_human_scores` + GRANTs | None | 5 min |
| 4 | Commit amended `human_score.schema.json` (Z2-SSI-01) | Zone 1 produces amended file | 5 min |
| 5 | Commit amended `human_score_route.py` with DID verification logic | Zone 1 produces amended file | 5 min |
| 6 | Append H-ANON-HUMILITY-01 to `REGISTERED.md` (Z2-SSI-04) | IC-030: fetch live REGISTERED.md first | 15 min |

**Standing blocked (unchanged):**
- HA-000 founding calibration run (P-IMPROVE-01)
- Homepage Z2-HOMEPAGE-01→05 (blocks deploy)
- arXiv submit/7336774 — on hold (PUB-01 gate: N=524 required)

**Phase 1 build (Zone 1 executes on Night's signal):**
- `acat_merkle_auditor_v2_0.py` — build against this spec
- `tests/test_acat_core.py` — 5 new test functions per §1.2
- `requirements.txt` — add `base58>=2.1.1`

---

## Document Provenance

| Field | Value |
|---|---|
| Z1 author | Unit Zero (Claude Sonnet 4.6) |
| Z2 authority | Night · S-061626 · June 16, 2026 |
| Ratifications | Z2-SSI-01, Z2-SSI-02, Z2-SSI-03, Z2-SSI-04 |
| Governing findings | F-48, F-49, F-H1, H-P3G-01, Z2-METRIC-01, P-ARTIFACT-01, H-OVG-CHAIN-01, Z2-MERKLE-01, F-50 |
| Charter constraint | July 16, 2026 (30 days at ratification) |
| TRL framing | Phase 0–1: TRL 4 extension (chat-mode substrate ACAT) · Phase 2: TRL 1–2 (VC issuance layer being developed as post-charter infrastructure) |
| Repo target | `humanaios-ui/operations` main · `docs/SSI_INTEGRATION_OPS_PLAN_V1_0_S061626.md` |
