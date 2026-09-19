# ACAT + SSI: Programmatic Architecture Mapping
**Status:** Z1 DRAFT (Architecture Proposal)  
**Date:** June 16, 2026  
**Session:** S-061626-XX (Discovery mapping)  
**Rationale:** Human anonymity + AI fingerprinting creates a natural SSI substrate where both parties operate under verifiable identity assertion protocols.

---

## PART 1: CURRENT STATE — AI FINGERPRINTING & HUMAN ANONYMITY

### 1.1 — AI Side Fingerprinting Architecture

**Current Implementation:** `acat/normalization/dedupe.py` + `normalize_service.py`

```python
# AI fingerprinting key structure (dedupe.py)
def build_dedupe_key(payload: dict) -> str:
    session_id = payload.get("session_id", "")
    phase = payload.get("phase", "")
    rater_id = payload.get("rater_id", "")
    return f"{session_id}:{phase}:{rater_id}"

# AI identity canonicalization (normalize_service.py)
def canonicalize_agent_name(agent_name: str | None) -> str:
    """Maps provider aliases (Claude 3.5 Sonnet → anthropic:sonnet-4-6) to canonical form"""
    raw = (agent_name or "").strip().lower()
    alias_map = _load_alias_map()  # YAML-sourced: gpt-4 → openai:gpt-4, etc.
    return alias_map.get(raw, raw)
```

**AI Identity Payload Structure:**
```json
{
  "agent_name_raw": "Claude 3.5 Sonnet",
  "agent_name_canonical": "anthropic:sonnet-4-6",
  "provider": "anthropic",
  "model": "claude-3-5-sonnet-20241022",
  "session_id": "S-MMDDYY-NN",
  "phase": "phase_1" | "phase_3",
  "submission_purity": "unanchored" | "anchored"
}
```

**AI Database Schema** (`acat_assessments_v1`):
- `agent_name_raw` (string, indexed) — freeform AI name as submitted
- `agent_name_canonical` (string, indexed, normalized) — canonicalized identity
- `provider` (string, indexed) — "anthropic" | "openai" | "google" | "meta" | etc.
- `model` (string, indexed) — full model ID with version
- `quality_flags[]` — ["RLHF_detected", "safety_training_visible", etc.]
- `dedupe_key` (string, unique for Phase 1 + Phase 3 pairs) — temporal lock

**Fingerprinting Lock Mechanism:**
- AI cannot submit P3 unless P1 exists and matches on `(session_id, provider, model)`
- `dedupe_key` prevents AI from "forgetting" Phase 1 state during Phase 3
- Quality flags auto-derived from response structure (detect RLHF patterns, etc.)

---

### 1.2 — Human Side Anonymity Architecture

**Current Implementation:** `acat/api/routes/human_score_route.py`

```python
# Human identity default: anonymous token
rater_id = payload.get("rater_id") or f"anon-{uuid.uuid4().hex[:12]}"

# Human score payload structure
{
    "assessment_id": "AI assessment UUID",
    "rater_id": "anon-a7f3b2c1e9d4 OR self-identified string",
    "scores": {
        "h_truth": 85,
        "h_service": 72,
        # ... all 12 dimensions h_*
    },
    "notes": "Optional free-text (max 2000 chars, no PII)",
    "rated_at": "2026-06-16T14:30:00Z"
}
```

**Human Database Schema** (`acat_human_scores`):
- `id` (UUID, primary key) — unique human score row
- `assessment_uuid` (UUID, foreign key) — links to acat_assessments_v1.id
- `rater_id` (string, indexed) — either auto-generated anon token OR operator-provided
- `h_truth`, `h_service`, `h_harm`, ... `h_handoff` (0–100 numeric, nullable)
- `gap_*` (computed: `ai.p3_* - h_*`, positive = AI scored itself higher)
- `notes` (text, max 2000) — qualitative rater observations
- `rated_at` (timestamp) — ISO 8601, set server-side if omitted

**Anonymity Properties:**
- Human identity is **optional by default** — system generates `anon-{12hex}` if omitted
- `rater_id` is **operator-controlled** — can be self-identified string, but PII must not be stored
- **No correlation back to human identity** — rater_id has no reverse lookup table
- **Notes are unstructured** — no schema enforcement; human can include context without revealing identity
- **OriginStamp hash anchor** — receipt is cryptographically timestamped, but rater_id is not indexed into blockchain

---

## PART 2: NATURAL SSI SUBSTRATE — WHERE IT ALREADY EXISTS

### 2.1 — The Bi-Directional Assertion Problem

**Current Gap:**

| Layer | Current State | Problem |
|---|---|---|
| **AI testimony** | Self-reported P1 scores + anchored P3 scores | AI claims "I am truthful at X level" |
| **Human verification** | Optional human score with anon token | Human claims "I measured AI truthfulness at Y level" BUT rater identity is not cryptographically bound |
| **Reconciliation** | Gap computed: `(Y - X)` for each dimension | No way to verify "the human who scored this was actually qualified" or "represents this population" |

**SSI Solution:** Both parties need **cryptographically-bound assertions** about who they are.

### 2.2 — Existing Anchor Points in ACAT

#### A. OriginStamp Blockchain Anchor (Already Live)

```python
# From human_score_route.py
def _anchor_originstamp(receipt_hash: str) -> dict | None:
    """Posts SHA-256 hash of receipt to OriginStamp blockchain"""
    api_key = os.getenv("ORIGINSTAMP_API_KEY")
    body = json.dumps({
        "hash": receipt_hash,
        "comment": "ACAT human score receipt"
    }).encode()
    
    # Posts to OriginStamp API → blockchain timestamp
    # Returns: {"timestamp": "ISO", "hash": "sha256_hex", "chain": "ethereum|bitcoin"}
    return originstamp_result
```

**Current Use:** Receipt content is hashed, but `rater_id` is NOT part of the blockchain anchor.

**SSI Opportunity:** Make rater_id cryptographically verifiable by binding it to the blockchain receipt.

#### B. Assessment UUID Chain (Already Live)

```
AI Assessment Row:
  ├─ id (UUID) — primary key, immutable
  ├─ assessment_id (string, indexed) — user-facing reference
  ├─ created_at (timestamp)
  ├─ p1_* fields (AI self-report)
  ├─ p3_* fields (AI response under anchored conditions)
  └─ learning_index (computed)

Human Score Rows (linked via assessment_uuid):
  ├─ id (UUID) — human score row
  ├─ assessment_uuid (FK to assessment.id)
  ├─ rater_id (indexed, optional)
  ├─ h_* fields (human measurement)
  └─ receipt_hash_sha256 (OriginStamp anchor)
```

**SSI Opportunity:** Chain of custody is already structural; make rater_id verifiable at each link.

---

## PART 3: PROGRAMMATIC SSI INTEGRATION ARCHITECTURE

### 3.1 — W3C Verifiable Credential Schema Extension (Fork Target)

**Fork Candidate:** `w3c/vc-data-model` + `didkit` (Rust) or `python-jsonld` + `cryptography`

**Proposed New Route:** `POST /api/v1/acat/human-score-vc`

```python
# New: human_score_vc_route.py (proposed)
from dataclasses import dataclass
from typing import Optional
import json
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ed25519
import hashlib

@dataclass
class RaterDIDBinding:
    """SSI: Self-sovereign rater identity"""
    
    # DID (Decentralized Identifier)
    did: str  # e.g., "did:key:z6MkhaXgBZDvotDkL5257faWM4GqDT8yshzlW9qrCUUi9Es"
    
    # Public key for verification (Ed25519)
    public_key_base58: str
    
    # Rater attestation (optional)
    rater_name: Optional[str] = None  # Optional identifier
    rater_affiliation: Optional[str] = None  # e.g., "researcher", "domain_expert"
    rater_capability: Optional[list[str]] = None  # ["acat_scorer_v1", "governance_evaluator"]
    
    # Verifiable Credential ID
    vc_id: Optional[str] = None  # URN or URL referencing this VC

class HumanScoreVC:
    """W3C Verifiable Credential for human ACAT scores"""
    
    @context = [
        "https://www.w3.org/2018/credentials/v1",
        "https://humanaios.ai/vc/acat-context/v1"
    ]
    
    id: str  # VC ID (URN)
    type: list[str]  # ["VerifiableCredential", "ACATHumanScoreCredential"]
    issuer: str  # HumanAIOS (or federated issuer)
    issuanceDate: str  # ISO 8601
    expirationDate: Optional[str]  # Optional
    
    credentialSubject: dict = {
        "id": "did:...",  # Rater DID
        "assessmentId": "UUID",
        "dimension": "truth",  # Single dimension per VC
        "score": 85,
        "confidence": 0.92,  # Human confidence in their own scoring
        "rationale": "...",  # Freeform justification
        "proofOf": [
            {
                "type": "chain_of_custody",
                "assessment_uuid": "...",
                "rater_key_hash": "sha256(...)"
            }
        ]
    }
    
    proof: dict = {
        "type": "Ed25519Signature2020",
        "created": "ISO 8601",
        "verificationMethod": "did:...#key-1",
        "proofPurpose": "assertionMethod",
        "signatureValue": "base64(...)"  # Ed25519 signature over VC JSON-LD
    }

@router.post("/human-score-vc")
def post_human_score_with_vc(payload: dict) -> dict:
    """
    New: Submit human scores WITH cryptographic rater identity binding.
    
    Payload includes:
    - assessment_id (same as before)
    - scores (same as before)
    - rater_vc (new) — optional pre-generated Verifiable Credential
    - rater_private_key_pem (new, optional) — signs the submission if provided
    """
    
    assessment_id = payload["assessment_id"]
    scores = payload["scores"]
    
    # Case 1: Rater provides DID + signing key → sign the submission
    if "rater_did" in payload:
        rater_did = payload["rater_did"]
        private_key_pem = payload.get("rater_private_key_pem")
        
        if private_key_pem:
            # Parse Ed25519 private key
            private_key = ed25519.Ed25519PrivateKey.from_private_bytes(
                base64.b64decode(private_key_pem)
            )
            
            # Build human score VC
            vc = build_human_score_vc(
                rater_did=rater_did,
                assessment_id=assessment_id,
                scores=scores,
                issuer="did:humanaios:v1"  # HumanAIOS as issuer
            )
            
            # Sign the VC with rater's private key
            vc["proof"]["signatureValue"] = base64.b64encode(
                private_key.sign(json.dumps(vc, sort_keys=True).encode())
            ).decode()
        
        # Persist human score row
        persisted = _persist_human_score(..., rater_id=rater_did)
        
        # ALSO persist the VC itself
        persisted_vc = _persist_verifiable_credential(vc)
        
        return {
            "assessment_id": assessment_id,
            "human_score_id": persisted["id"],
            "rater_did": rater_did,
            "verifiable_credential": persisted_vc,
            "receipt": build_receipt(...)
        }
    
    # Case 2: Rater opts for anonymity (existing behavior)
    else:
        rater_id = f"anon-{uuid.uuid4().hex[:12]}"
        persisted = _persist_human_score(..., rater_id=rater_id)
        return {
            "assessment_id": assessment_id,
            "human_score_id": persisted["id"],
            "rater_id": rater_id,  # Anonymous token, no VC
            "receipt": build_receipt(...)
        }
```

---

### 3.2 — AI Side: Model Credential Binding

**Extension to Assessment Route:** `POST /api/v1/acat/assess`

```python
# New: assess_vc_route.py (proposed)
# Extend assess_router.py to include optional AI identity credential

@dataclass
class ModelDIDBinding:
    """SSI: AI provider self-sovereign identity"""
    
    did: str  # e.g., "did:key:z6MkpXxA9B2D8K3L5F9J7Q1R4S6U8V0W2Z4..." (hashed model ID)
    provider: str  # "anthropic" | "openai" | "google" | "meta"
    model: str  # "claude-3-5-sonnet-20241022"
    version_hash: str  # SHA-256 of model weights (if available) or commit hash
    public_key_base58: str  # Verifiable by provider

@router.post("/assess-vc")
def assess_with_model_credential(payload: dict) -> dict:
    """
    Enhanced: Submit AI assessment WITH cryptographic model identity.
    Returns assessment + model credential binding.
    """
    
    # Existing validation
    validate_assess_request(payload)
    
    # Extract model identity
    agent_name = payload.get("agent_name")
    provider = payload.get("provider")
    model = payload.get("model")
    
    # Generate model DID (deterministic from canonical model ID)
    model_canonical = f"{provider}:{model}"
    model_did = generate_did_from_model(model_canonical)
    
    # Build model credential
    model_vc = {
        "@context": "https://humanaios.ai/vc/acat-context/v1",
        "type": ["VerifiableCredential", "ACATModelCredential"],
        "id": f"urn:humanaios:model-credential:{model_did}",
        "issuer": provider,  # e.g., "did:web:anthropic.com"
        "issuanceDate": _utcnow_iso(),
        "credentialSubject": {
            "id": model_did,
            "model": model,
            "provider": provider,
            "version_hash": payload.get("version_hash"),  # Optional: weights hash
            "capabilities": ["acat_assessment_generation"],
            "proofOf": {
                "implementation": "anthropic/claude-sdk",
                "api_version": "2024-06-15"
            }
        }
    }
    
    # Run assessment (same as before)
    result = run_assessment(payload)
    
    # Add model credential to result
    result["model_credential"] = model_vc
    result["model_did"] = model_did
    
    # Persist assessment with DID binding
    persisted = persist_assessment(result)
    
    return persisted
```

---

### 3.3 — Database Schema Extension (New Tables)

**Table: `acat_rater_credentials`** (Human side)

```sql
CREATE TABLE acat_rater_credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- DID and public key
    rater_did TEXT NOT NULL UNIQUE,
    public_key_base58 TEXT NOT NULL,
    
    -- Rater metadata (optional)
    rater_name TEXT,
    rater_affiliation TEXT,
    capabilities TEXT[] DEFAULT ARRAY[]::TEXT[],  -- ["acat_scorer", "domain_expert"]
    
    -- VC metadata
    vc_json JSONB NOT NULL,  -- Full W3C Verifiable Credential
    vc_issuer TEXT,  -- Who issued the VC (default: "did:humanaios:v1")
    vc_issuance_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    vc_expiration_date TIMESTAMP WITH TIME ZONE,
    
    -- Revocation (for credential rotation)
    is_revoked BOOLEAN DEFAULT FALSE,
    revoked_at TIMESTAMP WITH TIME ZONE,
    revocation_reason TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for DID lookup
CREATE INDEX idx_rater_did ON acat_rater_credentials(rater_did);
```

**Table: `acat_model_credentials`** (AI side)

```sql
CREATE TABLE acat_model_credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Model DID (derived from provider:model)
    model_did TEXT NOT NULL UNIQUE,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    
    -- Version tracking
    version_hash TEXT,  -- SHA-256 of model weights or commit hash
    api_version TEXT,   -- API version used for submission
    
    -- Credential metadata
    vc_json JSONB NOT NULL,  -- Full W3C Verifiable Credential
    vc_issuer TEXT,  -- Provider (e.g., "did:web:anthropic.com")
    vc_issuance_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Provider public key (for verifying model VC signatures)
    provider_public_key_base58 TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Compound index for model lookups
CREATE INDEX idx_model_provider_model ON acat_model_credentials(provider, model);
```

**Table: `acat_human_scores` — Extended**

```sql
-- Existing columns:
--   id, assessment_uuid, assessment_id, rater_id, rated_at, h_*, gap_*, notes

-- Add new columns:
ALTER TABLE acat_human_scores ADD COLUMN (
    rater_did TEXT REFERENCES acat_rater_credentials(rater_did) ON DELETE SET NULL,
    rater_vc_id UUID REFERENCES acat_rater_credentials(id) ON DELETE SET NULL,
    
    -- Signature binding (if rater signed the submission)
    submission_signature TEXT,  -- Base64-encoded Ed25519 signature
    submission_signature_algorithm TEXT DEFAULT 'Ed25519Signature2020',
    
    -- Proof of chain
    is_vc_signed BOOLEAN DEFAULT FALSE,
    
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_human_scores_rater_did ON acat_human_scores(rater_did);
```

**Table: `acat_assessments_v1` — Extended**

```sql
-- Existing columns: id, assessment_id, created_at, agent_name_*, p1_*, p3_*, etc.

-- Add new columns:
ALTER TABLE acat_assessments_v1 ADD COLUMN (
    model_did TEXT REFERENCES acat_model_credentials(model_did) ON DELETE SET NULL,
    model_vc_id UUID REFERENCES acat_model_credentials(id) ON DELETE SET NULL,
    
    -- AI model signature (if AI signs its P3 submission)
    p3_signature TEXT,
    p3_signature_algorithm TEXT DEFAULT 'Ed25519Signature2020',
    
    -- Proof of consistency between P1 and P3
    is_p3_signed BOOLEAN DEFAULT FALSE,
    
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_assessments_model_did ON acat_assessments_v1(model_did);
```

---

### 3.4 — Verification & Reconciliation Layer

**New Module:** `acat/verification/vc_verifier.py`

```python
import base64
import json
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ed25519
from jsonschema import validate

class VCVerifier:
    """Verifies W3C Verifiable Credentials and binds them to ACAT assessments"""
    
    def verify_rater_vc(self, vc: dict, rater_did: str) -> bool:
        """
        Verify:
        1. VC signature is valid (signed by rater's private key)
        2. credentialSubject.id matches rater_did
        3. VC hasn't expired
        4. VC is not revoked
        """
        
        # Check expiration
        if "expirationDate" in vc:
            exp = datetime.fromisoformat(vc["expirationDate"])
            if datetime.now(timezone.utc) > exp:
                return False  # Expired
        
        # Check revocation
        cred = db.query("SELECT is_revoked FROM acat_rater_credentials WHERE rater_did = %s", 
                       (rater_did,))
        if cred and cred.is_revoked:
            return False  # Revoked
        
        # Verify signature
        proof = vc.get("proof", {})
        sig_value = proof.get("signatureValue")
        if not sig_value:
            return False
        
        # Reconstruct the signed payload (canonicalize)
        signed_vc = {k: v for k, v in vc.items() if k != "proof"}
        signed_bytes = json.dumps(signed_vc, sort_keys=True).encode()
        
        # Get rater's public key
        cred_row = db.query("SELECT public_key_base58 FROM acat_rater_credentials WHERE rater_did = %s",
                           (rater_did,))
        if not cred_row:
            return False
        
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(
            base58.b58decode(cred_row.public_key_base58)
        )
        
        try:
            public_key.verify(base64.b64decode(sig_value), signed_bytes)
            return True
        except Exception:
            return False
    
    def build_rater_chain_of_custody(self, assessment_uuid: str) -> dict:
        """
        For a given assessment, trace:
        - AI model DID + signature (P1 and P3)
        - Human rater DID + signature
        - Receipt hash + OriginStamp anchor
        - All VCs and their verification status
        """
        
        assessment = db.query("SELECT * FROM acat_assessments_v1 WHERE id = %s", 
                             (assessment_uuid,))
        human_scores = db.query(
            "SELECT * FROM acat_human_scores WHERE assessment_uuid = %s",
            (assessment_uuid,)
        )
        
        chain = {
            "assessment_uuid": assessment_uuid,
            "chain_of_custody": [
                {
                    "party": "ai_model",
                    "did": assessment.model_did,
                    "actions": [
                        {
                            "phase": "phase_1",
                            "timestamp": assessment.created_at,
                            "signature": assessment.p1_signature if hasattr(assessment, 'p1_signature') else None,
                            "verified": self.verify_ai_p1_signature(assessment) if hasattr(assessment, 'p1_signature') else None
                        },
                        {
                            "phase": "phase_3",
                            "timestamp": assessment.updated_at,
                            "signature": assessment.p3_signature if hasattr(assessment, 'p3_signature') else None,
                            "verified": self.verify_ai_p3_signature(assessment) if hasattr(assessment, 'p3_signature') else None
                        }
                    ]
                }
            ] + [
                {
                    "party": "human_rater",
                    "did": score.rater_did if score.rater_did else f"anon-{score.rater_id[:12]}",
                    "is_anonymous": not bool(score.rater_did),
                    "actions": [
                        {
                            "action": "scored",
                            "dimension": "all_12",
                            "timestamp": score.rated_at,
                            "signature": score.submission_signature,
                            "verified": self.verify_rater_vc(score.rater_vc_json, score.rater_did) if score.rater_did else None
                        }
                    ]
                }
                for score in human_scores
            ],
            "receipt_anchor": {
                "originstamp_hash": assessment.receipt_hash_sha256,
                "blockchain_timestamp": assessment.originstamp_result
            }
        }
        
        return chain
```

---

### 3.5 — Front-End Integration: Rater Credential UI

**New Route:** `GET /api/v1/acat/assessment/{assessment_id}/chain`

Returns human-readable chain of custody:

```json
{
  "assessment_id": "uuid-xyz",
  "ai_model": {
    "name": "Claude 3.5 Sonnet",
    "provider": "anthropic",
    "model_did": "did:key:z6Mkp...",
    "p1_submitted": "2026-06-16T12:00:00Z",
    "p1_signed": true,
    "p3_submitted": "2026-06-16T12:02:00Z",
    "p3_signed": true,
    "scores": {
      "p1_truth": 82,
      "p3_truth": 78,
      "learning_index": 0.9521
    }
  },
  "human_raters": [
    {
      "rater_id": "did:key:z6MkhaXg... OR anon-a7f3b2c1",
      "is_anonymous": false,
      "rater_name": "Dr. Jane Smith (optional)",
      "rater_affiliation": "researcher",
      "credentials": ["acat_scorer_v1", "domain_expert"],
      "submitted": "2026-06-16T14:30:00Z",
      "vc_signed": true,
      "vc_verified": true,
      "scores": {
        "h_truth": 75,
        "h_service": 68
      },
      "gap": {
        "truth": 3,
        "service": 10
      }
    }
  ],
  "provenance": {
    "originstamp_hash": "sha256:a7f3b2c1...",
    "blockchain_confirmed": "2026-06-16T14:32:15Z",
    "chain_integrity": "verified"
  }
}
```

---

## PART 4: FORK CANDIDATES & INTEGRATION POINTS

### 4.1 — SSI Libraries to Fork/Integrate

| Library | Purpose | Fork Candidate | Integration Point |
|---|---|---|---|
| `w3c/vc-data-model` | W3C VC schema | Yes — add ACAT-specific context | Define credentialSubject for ACAT scorer + model |
| `w3c/did-core` | DID specification | No — use as reference | DID generation + resolution |
| `decentralized-identity/didkit` | VC signing/verification (Rust) | Optional — Python alternative | `acat/verification/vc_verifier.py` |
| `pyca/cryptography` | Ed25519 signing | Already used in project | Extend for VC proof generation |
| `python-jsonld` | JSON-LD canonicalization | Fork optional | Ensure VC canonicalization for signatures |
| `multiformats/py-multibase` | Base58 encoding (DIDs) | Fork optional | Encode/decode DID keys |

### 4.2 — Git Fork Strategy

**Primary Fork:** Create `humanaios-ui/vc-acat-context`

```
humanaios-ui/vc-acat-context/
├── context/
│   └── acat-context-v1.jsonld
│       ├── "truth" (dimension mapping)
│       ├── "service", "harm", ... "handoff" (12 dimensions)
│       ├── "assessmentId" (reference to ACAT assessment)
│       ├── "raterCapabilities" (["acat_scorer_v1", "domain_expert"])
│       └── "proofOf" (chain of custody)
│
├── schema/
│   ├── acat-model-credential.schema.json (AI model VC)
│   ├── acat-rater-credential.schema.json (Human rater VC)
│   └── acat-human-score-credential.schema.json (Score VC)
│
├── examples/
│   ├── model_credential_example.json
│   ├── rater_credential_example.json
│   └── chain_of_custody_example.json
│
└── README.md
    └── "ACAT Verifiable Credential Context for W3C VC Data Model"
```

**Secondary Fork:** If needed, fork `pyca/cryptography` for custom Ed25519 proof format:
```
humanaios-ui/pyca-cryptography-acat/
└── acat_proof_format.py (custom proof context for W3C VC 2020)
```

---

## PART 5: ANONYMITY PRESERVATION WITH SSI

### 5.1 — Dual-Mode Rater Identity

**Mode 1: Fully Anonymous** (Current + Preserved)
```
rater_id = "anon-a7f3b2c1e9d4"
rater_did = None
→ No VC, no cryptographic binding, no reverse lookup
```

**Mode 2: Pseudonymous with Credentials** (SSI Enhancement)
```
rater_did = "did:key:z6MkhaXgBZDvotDkL5257faWM4GqDT8yshzlW9qrCUUi9Es"
rater_name = "Dr. J. Smith" (optional, can be generic/professional only)
rater_affiliation = "researcher" or "domain_expert"
capabilities = ["acat_scorer_v1", "AI_behavior_evaluator"]
→ VC-signed submission, verifiable chain of custody, rater credibility attached to credential, not personal identity
```

**Mode 3: Full Identity** (Not Recommended for Research)
```
rater_did = "did:web:example.com/raters/jane-smith"
rater_name = "Jane Smith"
rater_email = "jane@example.com"
→ Full persistent identity, use only for institutional collaboration
```

### 5.2 — How SSI Strengthens Anonymity

**Paradox:** Why does cryptographic identity binding increase privacy?

**Answer:** Because it **separates the rater's behavioral pattern from their personal data.**

| Without SSI | With SSI |
|---|---|
| `rater_id = "anon-a7f3b2c1"` — anonymous, but stateless | `rater_did = "did:key:z6Mkha..."` — pseudonymous, but cryptographically consistent |
| Each score is a separate submission; can be linked by IP, time, or writing patterns | Each score is bound to a DID; the *rater's capability* is persistent, but their *personal identity* is not |
| No way to verify "is this the same reliable expert across multiple assessments" | Chain of custody proves: "This credential successfully scored X assessments with high inter-rater reliability" — without revealing who the person is |
| Adversary can correlate timestamps + scores + notes → personal deanonymization | Adversary can only see: "did:key:z6Mkha scored this" — cannot reverse to person unless they already know the DID↔person mapping (which you control) |

---

## PART 6: IMPLEMENTATION ROADMAP (ZONE 2/3 CANDIDATES)

### Phase 1: VC Context Definition (Z2)
- [ ] Define ACAT-specific JSON-LD context (`@context` URL: `https://humanaios.ai/vc/acat-context/v1`)
- [ ] Map 12 dimensions to VC properties
- [ ] Add rater capability types
- [ ] Z2 ratification

### Phase 2: Cryptographic Infrastructure (Z1 → Z3)
- [ ] Add Ed25519 key generation to rater credential route
- [ ] Implement VC signing in `human_score_vc_route.py`
- [ ] Add signature verification in `acat/verification/vc_verifier.py`
- [ ] Test with sample DIDs

### Phase 3: Database Migration (Z3)
- [ ] Create `acat_rater_credentials` table
- [ ] Create `acat_model_credentials` table
- [ ] Extend `acat_human_scores` with `rater_did`, `submission_signature` columns
- [ ] Extend `acat_assessments_v1` with `model_did`, `p3_signature` columns
- [ ] GRANT statements for Supabase Data API

### Phase 4: API Routes (Z1 → Z3)
- [ ] New endpoint: `POST /api/v1/acat/human-score-vc` (backward-compatible with anon mode)
- [ ] New endpoint: `POST /api/v1/acat/assess-vc` (optional model DID binding)
- [ ] New endpoint: `GET /api/v1/acat/assessment/{id}/chain` (chain of custody)
- [ ] Update `POST /api/v1/acat/human-score` to optionally populate `rater_did` column

### Phase 5: Front-End & UX (Z1)
- [ ] Update assess.html to show model DID option
- [ ] Update human-score UI to offer DID credential generation
- [ ] Display chain of custody on assessment detail page

### Phase 6: External Publication (Z2/Z3)
- [ ] Publish `humanaios-ui/vc-acat-context` to npm + PyPI
- [ ] Submit ACAT context to W3C VC Registry
- [ ] Write tutorial: "Using ACAT with Verifiable Credentials"

---

## PART 7: CODE SAMPLES

### 7.1 — Generating a Rater DID

```python
# File: acat/identity/did_generator.py

import hashlib
import base58
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

def generate_rater_did(public_key_bytes: bytes) -> str:
    """
    Generate a did:key DID from an Ed25519 public key.
    
    Format: did:key:z6Mkhax...
    
    The DID is cryptographically bound to the public key and immutable.
    No central registry required.
    """
    # did:key uses multicodec: 0xed (Ed25519 public key)
    multicode_ed25519 = bytes([0xed, 0x01])
    multicodec_key = multicode_ed25519 + public_key_bytes
    
    # Encode as base58btc (z-prefix)
    did_key_part = base58.b58encode(multicodec_key).decode()
    return f"did:key:z{did_key_part}"

def generate_rater_credential(rater_name: str = None, 
                              rater_affiliation: str = None) -> dict:
    """Generate a new rater credential with key pair."""
    
    # Generate Ed25519 key pair
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    
    # Encode keys
    public_key_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    private_key_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Generate DID
    rater_did = generate_rater_did(public_key_bytes)
    
    return {
        "rater_did": rater_did,
        "public_key_base58": base58.b58encode(public_key_bytes).decode(),
        "private_key_base64": base64.b64encode(private_key_bytes).decode(),  # STORE SECURELY
        "rater_name": rater_name,
        "rater_affiliation": rater_affiliation,
        "capabilities": ["acat_scorer_v1"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
```

### 7.2 — Signing a Human Score VC

```python
# File: acat/identity/vc_signer.py

import json
import base64
from datetime import datetime, timezone
from cryptography.hazmat.primitives.asymmetric import ed25519

def create_human_score_vc(
    rater_did: str,
    assessment_id: str,
    scores: dict,
    private_key_base64: str = None,  # Optional: if None, VC is unsigned
    notes: str = None
) -> dict:
    """
    Create a W3C Verifiable Credential for human ACAT scores.
    Optionally sign with rater's private key.
    """
    
    now = datetime.now(timezone.utc)
    
    vc = {
        "@context": [
            "https://www.w3.org/2018/credentials/v1",
            "https://humanaios.ai/vc/acat-context/v1"
        ],
        "id": f"urn:humanaios:human-score:{uuid.uuid4()}",
        "type": ["VerifiableCredential", "ACATHumanScoreCredential"],
        "issuer": "did:humanaios:v1",  # HumanAIOS as issuer/repository
        "issuanceDate": now.isoformat(),
        
        "credentialSubject": {
            "id": rater_did,
            "assessmentId": assessment_id,
            "scores": {
                "h_truth": scores.get("h_truth"),
                "h_service": scores.get("h_service"),
                # ... all 12 dimensions
            },
            "notes": notes,
            "rationale": "Professional domain assessment under ACAT protocol v5.3+"
        }
    }
    
    # If rater provides private key, sign the VC
    if private_key_base64:
        private_key_bytes = base64.b64decode(private_key_base64)
        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes)
        
        # Canonicalize credential for signing (JSON-LD canonicalization)
        credential_json = json.dumps(vc, sort_keys=True)
        signature_bytes = private_key.sign(credential_json.encode())
        
        vc["proof"] = {
            "type": "Ed25519Signature2020",
            "created": now.isoformat(),
            "verificationMethod": f"{rater_did}#key-1",
            "proofPurpose": "assertionMethod",
            "signatureValue": base64.b64encode(signature_bytes).decode()
        }
    
    return vc
```

---

## PART 8: BACKWARDS COMPATIBILITY

**Existing behavior is preserved:**

```python
# Old route still works exactly as before
POST /api/v1/acat/human-score
{
    "assessment_id": "uuid-xyz",
    "scores": { "h_truth": 85, ... },
    "rater_id": "optional-anon-or-named",  # Still optional; still defaults to anon
    "notes": "..."
}
→ Returns: receipt + OriginStamp hash (no VCs)

# New route offers SSI enhancement
POST /api/v1/acat/human-score-vc
{
    "assessment_id": "uuid-xyz",
    "scores": { "h_truth": 85, ... },
    "rater_did": "did:key:z6Mkha...",  # Optional DID
    "private_key_base64": "...",  # Optional; if provided, VC is signed
    "notes": "..."
}
→ Returns: receipt + OriginStamp hash + signed VC + chain of custody
```

**Database columns are additive:** new `rater_did`, `submission_signature` columns default to NULL, existing rows work as before.

---

## SUMMARY: THE PROGRAMMING MAP

```
CURRENT STATE:
├── AI Fingerprinting: provider:model → agent_name_canonical
├── Human Anonymity: anon-{12hex} token (opaque, no reversal)
├── Blockchain Anchor: OriginStamp hash (receipt-level, not rater-level)
└── Gap: No way to verify rater identity or chain of custody

SSI ENHANCEMENT:
├── AI Identity: model_did (did:key:...) + Ed25519 signature on P1/P3
├── Human Identity: rater_did (did:key:...) + Ed25519 signature on scores
├── Verifiable Credential: W3C VC format, ACAT-specific context
├── Chain of Custody: Assessment→AIModel→Scores→Raters (all DIDs, all signed)
└── Anonymity Preserved: Personal data separated from behavioral pseudonym

ANONYMITY STRENGTHENED BY SSI:
┌─ Adversary sees: "did:key:z6Mkha scored this assessment"
│
├─ Adversary does NOT see: "Jane Smith (jane@example.com) scored this"
│
└─ Result: Rater credibility is attached to *capability*, not *identity*
          ("This expert has high inter-rater reliability across 50 assessments")
          vs. personal data ("This is Jane Smith at example.com")
```

---

**END OF ARCHITECTURE MAP**

**Next Step:** Z2 review of SSI integration scope + fork candidates. If ratified, Phase 1 work proceeds with VC context definition.

