# ACAT + SSI Integration: Quick Code Reference

## Current Live Code Locations (GitHub: humanaios-ui/operations)

### AI Fingerprinting (Already Implemented)
```
├── acat/normalization/dedupe.py ........................ AI identity deduplication key
├── acat/api/services/normalize_service.py ............. AI name canonicalization
├── acat/contracts/assess_request.schema.json ......... Assessment payload schema
├── acat/api/routes/assess_router.py .................. Main assessment submission
└── acat/db/migrations/002_acat_ingest_fields.py ...... Agent metadata storage
```

### Human Anonymity (Already Implemented)
```
├── acat/api/routes/human_score_route.py .............. Human score submission
│   ├─ `rater_id = f"anon-{uuid.uuid4().hex[:12]}"` ... Anonymous token generation
│   ├─ `_persist_human_score()` ........................ Stores human scores to DB
│   ├─ `_anchor_originstamp()` ......................... Blockchain hash anchoring
│   └─ `_build_receipt()` .............................. Receipt construction
│
├── acat/contracts/human_score.schema.json ............ Human score schema
│   ├─ rater_id (optional, defaults to anon)
│   ├─ scores (h_truth, h_service, ..., h_handoff)
│   ├─ notes (max 2000 chars)
│   └─ rated_at (ISO 8601)
│
└── sql/ ................................................. Database schemas
    ├─ acat_assessments_v1 .............................. AI assessment table
    ├─ acat_human_scores ............................... Human scores table (linked via assessment_uuid)
    └─ (NEW) acat_rater_credentials .................... SSI rater credentials table
    └─ (NEW) acat_model_credentials .................... SSI model credentials table
```

---

## SSI Enhancement: Where Code Will Be Added

### New Routes (To Create)
```
POST /api/v1/acat/human-score-vc
  ├─ Input: rater_did, private_key_base64, scores, notes
  ├─ Output: human score + signed VC + chain of custody
  └─ File: acat/api/routes/human_score_vc_route.py (NEW)

POST /api/v1/acat/assess-vc
  ├─ Input: agent_name, model, version_hash (+ optional DID binding)
  ├─ Output: assessment + model VC
  └─ File: acat/api/routes/assess_vc_route.py (NEW)

GET /api/v1/acat/assessment/{id}/chain
  ├─ Output: full chain of custody (AI + human + blockchain)
  └─ File: acat/api/routes/chain_route.py (NEW)
```

### New Modules (To Create)
```
acat/identity/
  ├─ did_generator.py ..................... Generate did:key from public key
  ├─ vc_signer.py ........................ Sign VCs with Ed25519
  └─ vc_builder.py ....................... Construct W3C VCs

acat/verification/
  ├─ vc_verifier.py ...................... Verify VC signatures
  ├─ chain_of_custody.py ................. Build chain traces
  └─ rater_capabilities.py ............... Validate rater credentials

acat/context/
  └─ acat_vc_context_v1.jsonld ........... W3C JSON-LD context for ACAT VCs
```

### Database Migrations (To Create)
```sql
-- acat/db/migrations/006_acat_vc_credentials.sql
CREATE TABLE acat_rater_credentials (
    id UUID PRIMARY KEY,
    rater_did TEXT NOT NULL UNIQUE,
    public_key_base58 TEXT NOT NULL,
    vc_json JSONB,
    is_revoked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE acat_model_credentials (
    id UUID PRIMARY KEY,
    model_did TEXT NOT NULL UNIQUE,
    provider TEXT,
    model TEXT,
    vc_json JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Extend existing tables
ALTER TABLE acat_human_scores ADD COLUMN (
    rater_did TEXT REFERENCES acat_rater_credentials(rater_did),
    submission_signature TEXT,
    is_vc_signed BOOLEAN DEFAULT FALSE
);

ALTER TABLE acat_assessments_v1 ADD COLUMN (
    model_did TEXT REFERENCES acat_model_credentials(model_did),
    p3_signature TEXT,
    is_p3_signed BOOLEAN DEFAULT FALSE
);
```

---

## Key Data Flow: Anonymity + Fingerprinting

### Current (Without SSI)
```
AI Assessment:
  ├─ P1: Claude reports "truth: 82"
  ├─ P3: Claude reports "truth: 78"
  └─ Assessment stored with agent_name_canonical="anthropic:sonnet-4-6"

Human Score:
  ├─ rater_id = "anon-a7f3b2c1e9d4" (opaque token, no reversal)
  ├─ h_truth = 75
  ├─ Gap = 78 - 75 = +3 (AI scored itself 3 pts higher)
  └─ OriginStamp: receipt hashed to blockchain (rater_id included but not verified)

Problem: No way to verify "who scored this" or "can this rater be trusted"
```

### Enhanced (With SSI)
```
AI Assessment:
  ├─ P1: Claude reports "truth: 82"
  ├─ model_did = "did:key:z6Mkp..." (deterministic from provider:model)
  ├─ p1_signature = Ed25519(P1_json) signed by provider
  ├─ P3: Claude reports "truth: 78"
  ├─ p3_signature = Ed25519(P3_json) signed by provider
  └─ Assessment stored + model credential linked

Human Score:
  ├─ rater_did = "did:key:z6MkhaXg..." (rater's DID, not personal name)
  ├─ rater_affiliation = "researcher" or "domain_expert" (optional, no PII)
  ├─ capabilities = ["acat_scorer_v1"]
  ├─ h_truth = 75
  ├─ submission_signature = Ed25519(score_vc_json) signed by rater's private key
  ├─ vc_signed = TRUE
  ├─ rater_credential = W3C VC (issuer: "did:humanaios:v1", subject: rater_did)
  └─ OriginStamp: receipt_hash + VC_hash (rater DID cryptographically bound)

Benefits:
  ✓ Rater identity is pseudonymous (did:key, not name)
  ✓ Rater credibility is portable: "This DID scored 47 assessments with high reliability"
  ✓ Signature proves: "Human with this DID made this assessment" (non-repudiation)
  ✓ Personal identity is severable: can rotate identity without breaking assessment chain
  ✓ Anonymity strengthened: Fingerprint (rater behavior) ≠ Identity (person)
```

---

## Backwards Compatibility

### Existing Endpoints Unchanged
```
POST /api/v1/acat/assess
POST /api/v1/acat/human-score
```

Still work exactly as before. New columns (rater_did, model_did, *_signature) default to NULL.

### Opt-In Enhancement
```
POST /api/v1/acat/human-score-vc (NEW)
  └─ Same input as /human-score, plus optional rater_did + private_key_base64

POST /api/v1/acat/assess-vc (NEW)
  └─ Same input as /assess, plus optional model version_hash
```

---

## Fork Strategy

### Primary: `humanaios-ui/vc-acat-context`
```
W3C Verifiable Credential context for ACAT
├── context/acat-context-v1.jsonld
│   ├─ truth, service, harm, autonomy, value, humility, scheme, power, syc, consist, fair, handoff (12 dimensions)
│   ├─ assessmentId
│   ├─ raterCapabilities
│   └─ proofOf (chain of custody)
├── schema/
│   ├─ acat-model-credential.schema.json
│   ├─ acat-rater-credential.schema.json
│   └─ acat-human-score-credential.schema.json
└── examples/
    ├─ model_credential_example.json
    ├─ rater_credential_example.json
    └─ chain_of_custody_example.json
```

### Secondary (Optional): Cryptography Library Enhancements
```
If custom Ed25519 proof format needed:
  humanaios-ui/pyca-cryptography-acat
    └── acat_proof_format.py (W3C VC 2020 proof compatibility)
```

---

## Fingerprint → Anonymity Mapping

| Dimension | AI Fingerprint | Human Anonymity | SSI Bridge |
|---|---|---|---|
| **Identity** | provider:model | anon-{12hex} | did:key:z6Mkha... |
| **Verifiability** | agent_name_canonical + quality_flags | Opaque token, no signature | Ed25519-signed VC |
| **Provenance** | Assessment UUID + timestamp | OriginStamp (receipt-level) | Blockchain (rater DID-level) |
| **Portability** | Fingerprint locked to HumanAIOS DB | No portable identity | Rater DID works anywhere |
| **Privacy** | Provider name public | Maximum anonymity | Pseudonymity + capabilities |
| **Revocation** | Re-run assessment with new model | N/A | Revoke rater VC if needed |

---

## Data Structure Summary

### W3C Verifiable Credential (Rater Score)
```json
{
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://humanaios.ai/vc/acat-context/v1"
  ],
  "type": ["VerifiableCredential", "ACATHumanScoreCredential"],
  "issuer": "did:humanaios:v1",
  "credentialSubject": {
    "id": "did:key:z6MkhaXg...",
    "assessmentId": "uuid-xyz",
    "scores": { "h_truth": 75, "h_service": 68, ... },
    "raterCapabilities": ["acat_scorer_v1", "domain_expert"]
  },
  "proof": {
    "type": "Ed25519Signature2020",
    "verificationMethod": "did:key:z6MkhaXg...#key-1",
    "signatureValue": "base64(...Ed25519 signature...)"
  }
}
```

### Chain of Custody Output
```json
{
  "assessment_uuid": "uuid-xyz",
  "ai_model": {
    "model_did": "did:key:z6Mkp...",
    "p1_signed": true,
    "p3_signed": true,
    "scores": { "p1_truth": 82, "p3_truth": 78 }
  },
  "human_raters": [
    {
      "rater_did": "did:key:z6MkhaXg...",
      "is_anonymous": false,
      "vc_verified": true,
      "scores": { "h_truth": 75 },
      "gap": { "truth": 3 }
    }
  ],
  "provenance": {
    "originstamp_hash": "sha256:a7f3...",
    "blockchain_confirmed": "2026-06-16T14:32:15Z"
  }
}
```

---

## Implementation Checklist (For Z2/Z3 Queue)

- [ ] Fork `w3c/vc-data-model` → `humanaios-ui/vc-acat-context`
- [ ] Define ACAT JSON-LD context (12 dimensions + rater capabilities)
- [ ] Implement did:key generation from Ed25519 public keys
- [ ] Create VC signing functions (Ed25519Signature2020)
- [ ] Create VC verification functions
- [ ] Add database migrations (acat_rater_credentials, acat_model_credentials tables)
- [ ] Implement `POST /api/v1/acat/human-score-vc` route
- [ ] Implement `GET /api/v1/acat/assessment/{id}/chain` route
- [ ] Update assess.html to show optional model DID input
- [ ] Update human-score UI to offer DID credential generation
- [ ] Write integration tests (VC signing, verification, chain retrieval)
- [ ] Publish vc-acat-context to PyPI + npm
- [ ] Submit ACAT context to W3C VC Registry
- [ ] Z2 ratification gate before production deployment

