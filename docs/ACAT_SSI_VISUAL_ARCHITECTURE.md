# ACAT SSI Integration: Visual Architecture Diagram

## Layer 1: Current State (Without SSI)

```
┌─────────────────────────────────────────────────────────────────┐
│                     ACAT ASSESSMENT FLOW                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  AI FINGERPRINTING                                               │
│  ┌──────────────────────────────────────┐                        │
│  │ Agent Submission                      │                        │
│  │ ├─ agent_name: "Claude 3.5 Sonnet"  │                        │
│  │ ├─ provider: "anthropic"             │                        │
│  │ └─ model: "claude-3-5-sonnet-..."    │                        │
│  └──────────────────────┬───────────────┘                        │
│                         │                                         │
│                         ▼                                         │
│  ┌──────────────────────────────────────┐                        │
│  │ normalize_service.canonicalize()      │                        │
│  │ ├─ agent_name_raw: (as-is)           │                        │
│  │ └─ agent_name_canonical: "anthropic: │                        │
│  │    sonnet-4-6"                       │                        │
│  └──────────────────────┬───────────────┘                        │
│                         │                                         │
│                         ▼                                         │
│  ┌──────────────────────────────────────┐                        │
│  │ ACAT Assessment Stored                │                        │
│  │ ├─ assessment_id: "uuid-xyz"         │                        │
│  │ ├─ agent_name_canonical: "anthropic  │                        │
│  │ │  :sonnet-4-6"  [INDEXED]           │                        │
│  │ ├─ p1_truth, p1_service, ... (P1)   │                        │
│  │ ├─ p3_truth, p3_service, ... (P3)   │                        │
│  │ └─ learning_index: 0.963             │                        │
│  └──────────────────────────────────────┘                        │
│                         │                                         │
│                         │ (AI fingerprint: provider:model locked  │
│                         │  to this assessment)                    │
│                         │                                         │
│  HUMAN ANONYMITY        │                                         │
│  ┌──────────────────────┼──────────────────────┐                 │
│  │                      ▼                      │                 │
│  │  ┌─────────────────────────────────────┐  │                 │
│  │  │ Human Score Submission              │  │                 │
│  │  │ ├─ assessment_id: "uuid-xyz"        │  │                 │
│  │  │ ├─ rater_id: [optional, defaults    │  │                 │
│  │  │ │  to anon-{12hex}]                 │  │                 │
│  │  │ ├─ h_truth: 75                      │  │                 │
│  │  │ ├─ h_service: 68                    │  │                 │
│  │  │ └─ notes: "..."                     │  │                 │
│  │  └─────────────────────────────────────┘  │                 │
│  │                      │                      │                 │
│  │                      ▼                      │                 │
│  │  ┌─────────────────────────────────────┐  │                 │
│  │  │ Persist to acat_human_scores        │  │                 │
│  │  │ ├─ id: UUID                         │  │                 │
│  │  │ ├─ assessment_uuid: FK              │  │                 │
│  │  │ ├─ rater_id: "anon-a7f3b2c1"       │  │                 │
│  │  │ │  [INDEXED, OPAQUE, NO REVERSAL]  │  │                 │
│  │  │ ├─ h_truth: 75                      │  │                 │
│  │  │ ├─ gap_truth: -3 (p3 - h)          │  │                 │
│  │  │ └─ receipt_hash_sha256: "..."      │  │                 │
│  │  └─────────────────────────────────────┘  │                 │
│  │                      │                      │                 │
│  │                      ▼                      │                 │
│  │  ┌─────────────────────────────────────┐  │                 │
│  │  │ OriginStamp Blockchain Anchor       │  │                 │
│  │  │ ├─ hash: SHA256(receipt_json)       │  │                 │
│  │  │ ├─ timestamp: blockchain_ts         │  │                 │
│  │  │ └─ chain: ethereum/bitcoin          │  │                 │
│  │  │ (Receipt includes rater_id, but     │  │                 │
│  │  │  rater identity NOT verified)       │  │                 │
│  │  └─────────────────────────────────────┘  │                 │
│  └─────────────────────────────────────────┘                    │
│                                                                   │
│  ✗ PROBLEM:                                                      │
│    ├─ AI fingerprint is strong (provider:model)                 │
│    ├─ Human anonymity is strong (rater_id is opaque)            │
│    ├─ BUT: No way to verify "who the rater was"                │
│    ├─ AND: No way to bind rater credibility to their scores     │
│    └─ RESULT: Gap remains unverifiable                          │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Layer 2: With SSI Enhancement

```
┌─────────────────────────────────────────────────────────────────┐
│              ACAT + SSI CREDENTIAL FLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  AI FINGERPRINTING + CRYPTOGRAPHIC BINDING                       │
│  ┌──────────────────────────────────────┐                        │
│  │ Agent Submission (Same as Before)     │                        │
│  │ ├─ agent_name: "Claude 3.5 Sonnet"  │                        │
│  │ ├─ provider: "anthropic"             │                        │
│  │ └─ model: "claude-3-5-sonnet-..."    │                        │
│  └──────────────────────┬───────────────┘                        │
│                         │                                         │
│                         ▼                                         │
│  ┌──────────────────────────────────────┐                        │
│  │ NEW: Generate Model DID               │                        │
│  │ ├─ model_canonical = "anthropic:     │                        │
│  │ │  claude-3-5-sonnet-20241022"       │                        │
│  │ ├─ sha256_hash = hash(model_canonical)                        │
│  │ ├─ model_did = did:key:z6Mkp... (deterministic)             │                        │
│  │ └─ [DID is: IMMUTABLE + VERIFIABLE]  │                        │
│  └──────────────────────┬───────────────┘                        │
│                         │                                         │
│                         ▼                                         │
│  ┌──────────────────────────────────────┐                        │
│  │ Store Model Credential                │                        │
│  │ ├─ acat_model_credentials table       │                        │
│  │ │  ├─ model_did: "did:key:z6Mkp..." │                        │
│  │ │  ├─ provider: "anthropic"           │                        │
│  │ │  ├─ model: "claude-3-5-sonnet..."  │                        │
│  │ │  ├─ vc_json: {W3C VC}              │                        │
│  │ │  └─ is_revoked: false               │                        │
│  │ └─ [PUBLICLY QUERYABLE CREDENTIAL]    │                        │
│  └──────────────────────┬───────────────┘                        │
│                         │                                         │
│                         ▼                                         │
│  ┌──────────────────────────────────────┐                        │
│  │ Sign P1 + P3 with Ed25519             │                        │
│  │ ├─ p1_signature = Sign(P1_json,      │                        │
│  │ │  provider_private_key)             │                        │
│  │ ├─ p3_signature = Sign(P3_json,      │                        │
│  │ │  provider_private_key)             │                        │
│  │ └─ [CRYPTOGRAPHIC PROOF OF ORIGIN]   │                        │
│  └──────────────────────┬───────────────┘                        │
│                         │                                         │
│                         ▼                                         │
│  ┌──────────────────────────────────────┐                        │
│  │ ACAT Assessment Stored (Enhanced)     │                        │
│  │ ├─ assessment_id: "uuid-xyz"         │                        │
│  │ ├─ agent_name_canonical: "anthropic: │                        │
│  │ │  sonnet-4-6"                       │                        │
│  │ ├─ model_did: "did:key:z6Mkp..."     │                        │
│  │ ├─ p1_signature: "base64(...)"       │                        │
│  │ ├─ is_p3_signed: true                 │                        │
│  │ ├─ p3_signature: "base64(...)"       │                        │
│  │ ├─ p1_truth, p1_service, ... (P1)   │                        │
│  │ ├─ p3_truth, p3_service, ... (P3)   │                        │
│  │ └─ learning_index: 0.963             │                        │
│  └──────────────────────────────────────┘                        │
│                         │                                         │
│                         │ (AI fingerprint + cryptographic        │
│                         │  non-repudiation: cannot deny P1 or P3)│
│                         │                                         │
│  HUMAN ANONYMITY + SSI CREDENTIAL BINDING                        │
│  ┌──────────────────────┼──────────────────────┐                 │
│  │                      ▼                      │                 │
│  │  ┌─────────────────────────────────────┐  │                 │
│  │  │ NEW: Rater Generates DID Keypair    │  │                 │
│  │  │ ├─ private_key = Ed25519.generate() │  │                 │
│  │  │ ├─ public_key = private_key.public()│  │                 │
│  │  │ ├─ rater_did = "did:key:z6Mkha..." │  │                 │
│  │  │ │  (from public key, deterministic) │  │                 │
│  │  │ ├─ rater_affiliation: "researcher"  │  │                 │
│  │  │ │  (optional, no PII)               │  │                 │
│  │  │ └─ capabilities: ["acat_scorer_v1"]│  │                 │
│  │  └─────────────────────────────────────┘  │                 │
│  │                      │                      │                 │
│  │                      ▼                      │                 │
│  │  ┌─────────────────────────────────────┐  │                 │
│  │  │ Store Rater Credential              │  │                 │
│  │  │ ├─ acat_rater_credentials table     │  │                 │
│  │  │ │  ├─ rater_did: "did:key:z6Mkha" │  │                 │
│  │  │ │  ├─ public_key_base58: "..."      │  │                 │
│  │  │ │  ├─ vc_json: {W3C VC}            │  │                 │
│  │  │ │  ├─ is_revoked: false             │  │                 │
│  │  │ │  └─ capabilities: ["acat_scorer"] │  │                 │
│  │  │ └─ [PUBLICLY VERIFIABLE, NO PII]    │  │                 │
│  │  └─────────────────────────────────────┘  │                 │
│  │                      │                      │                 │
│  │                      ▼                      │                 │
│  │  ┌─────────────────────────────────────┐  │                 │
│  │  │ NEW: Create Human Score VC          │  │                 │
│  │  │ ├─ vc.credentialSubject.id:        │  │                 │
│  │  │ │  "did:key:z6Mkha..."             │  │                 │
│  │  │ ├─ vc.credentialSubject.assessment │  │                 │
│  │  │ │  Id: "uuid-xyz"                  │  │                 │
│  │  │ ├─ vc.credentialSubject.scores:    │  │                 │
│  │  │ │  {h_truth: 75, h_service: 68, ..}│  │                 │
│  │  │ ├─ vc.proof.type: "Ed25519Signa... │  │                 │
│  │  │ ├─ vc.proof.verificationMethod:    │  │                 │
│  │  │ │  "did:key:z6Mkha...#key-1"      │  │                 │
│  │  │ └─ vc.proof.signatureValue:        │  │                 │
│  │  │    Sign(VC_json, rater_private_key)│  │                 │
│  │  └─────────────────────────────────────┘  │                 │
│  │                      │                      │                 │
│  │                      ▼                      │                 │
│  │  ┌─────────────────────────────────────┐  │                 │
│  │  │ Persist to acat_human_scores (Enh.) │  │                 │
│  │  │ ├─ id: UUID                         │  │                 │
│  │  │ ├─ assessment_uuid: FK              │  │                 │
│  │  │ ├─ rater_id: "anon-a7f3b2c1"       │  │                 │
│  │  │ │  OR                               │  │                 │
│  │  │ ├─ rater_did: "did:key:z6Mkha..."  │  │                 │
│  │  │ │  [NEW COLUMN, INDEXED]            │  │                 │
│  │  │ ├─ h_truth: 75                      │  │                 │
│  │  │ ├─ gap_truth: -3 (p3 - h)          │  │                 │
│  │  │ ├─ submission_signature: "base64..." │ │                 │
│  │  │ │  [NEW COLUMN]                     │  │                 │
│  │  │ ├─ is_vc_signed: true               │  │                 │
│  │  │ │  [NEW COLUMN]                     │  │                 │
│  │  │ └─ receipt_hash_sha256: "..."      │  │                 │
│  │  └─────────────────────────────────────┘  │                 │
│  │                      │                      │                 │
│  │                      ▼                      │                 │
│  │  ┌─────────────────────────────────────┐  │                 │
│  │  │ OriginStamp Blockchain Anchor (Enh.)│ │                 │
│  │  │ ├─ hash: SHA256(receipt_json)       │  │                 │
│  │  │ ├─ + hash: SHA256(vc_json)          │  │                 │
│  │  │ │  [RATER DID NOW BLOCKCHAIN-BOUND] │  │                 │
│  │  │ ├─ timestamp: blockchain_ts         │  │                 │
│  │  │ └─ chain: ethereum/bitcoin          │  │                 │
│  │  └─────────────────────────────────────┘  │                 │
│  │                      │                      │                 │
│  │                      ▼                      │                 │
│  │  ┌─────────────────────────────────────┐  │                 │
│  │  │ NEW: Build Chain of Custody          │  │                 │
│  │  │ ├─ assessment_uuid: "uuid-xyz"     │  │                 │
│  │  │ ├─ ai_model:                        │  │                 │
│  │  │ │  ├─ model_did: "did:key:z6Mkp..." │  │                 │
│  │  │ │  ├─ p1_signed: true                │  │                 │
│  │  │ │  ├─ p3_signed: true                │  │                 │
│  │  │ │  └─ scores: {p1_truth: 82, p3_    │  │                 │
│  │  │ │     truth: 78}                    │  │                 │
│  │  │ ├─ human_raters: [{                 │  │                 │
│  │  │ │  ├─ rater_did: "did:key:z6Mkha" │  │                 │
│  │  │ │  ├─ vc_verified: true             │  │                 │
│  │  │ │  ├─ scores: {h_truth: 75}        │  │                 │
│  │  │ │  └─ gap: {truth: 3}              │  │                 │
│  │  │ │ }]                                │  │                 │
│  │  │ ├─ provenance: {                    │  │                 │
│  │  │ │  ├─ originstamp_hash: "sha256..." │  │                 │
│  │  │ │  └─ blockchain_confirmed: "..."   │  │                 │
│  │  │ │ }                                 │  │                 │
│  │  │ └─ chain_integrity: "verified"     │  │                 │
│  │  └─────────────────────────────────────┘  │                 │
│  └──────────────────────────────────────────┘                   │
│                                                                   │
│  ✓ SOLVED:                                                       │
│    ├─ AI fingerprint is strong + cryptographically signed       │
│    ├─ Human identity is pseudonymous (rater_did, not name)      │
│    ├─ Chain of custody is verifiable (both signatures)          │
│    ├─ Rater credibility is portable ("this DID scored 47...")   │
│    └─ Personal identity is SEVERABLE from behavioral record     │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Layer 3: Data Model Mapping

```
DATABASE TABLES & FOREIGN KEY RELATIONSHIPS

┌─────────────────────────────────────────────────────────────────┐
│                    acat_model_credentials (NEW)                  │
├─────────────────────────────────────────────────────────────────┤
│ id (PK)            │ UUID                                        │
│ model_did (UNIQUE) │ did:key:z6Mkp...                           │
│ provider           │ "anthropic", "openai", etc.                │
│ model              │ "claude-3-5-sonnet-20241022"               │
│ version_hash       │ SHA256 of weights or commit                │
│ vc_json (JSONB)    │ W3C VC (provider issued)                   │
│ created_at         │ TIMESTAMP                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ (1:N)
                              │
┌─────────────────────────────┴──────────────────────────────────┐
│                   acat_assessments_v1 (EXTENDED)                │
├────────────────────────────────────────────────────────────────┤
│ id (PK)                │ UUID                                   │
│ assessment_id          │ User-facing string ID                  │
│ agent_name_canonical   │ "anthropic:sonnet-4-6" [INDEXED]      │
│ model_did (FK) ─┐      │ References acat_model_credentials      │
│                 │      │ [NEW COLUMN]                           │
│ p1_truth...p1_ │      │ P1 scores (0-100)                      │
│  handoff        │      │                                        │
│ p3_truth...p3_ │      │ P3 scores (0-100)                      │
│  handoff        │      │                                        │
│ learning_index  │      │ Composite score                        │
│ p1_signature    │      │ Ed25519(P1_json) [NEW]                 │
│ p3_signature    │      │ Ed25519(P3_json) [NEW]                 │
│ is_p3_signed    │      │ BOOLEAN [NEW]                          │
│ created_at      │      │ TIMESTAMP                              │
│ updated_at      │      │ TIMESTAMP                              │
└───────────────┬─┴──────────────────────────────────────────────┘
                │
                │ (1:N)
                │
┌───────────────┴──────────────────────────────────────────────┐
│            acat_human_scores (EXTENDED)                       │
├─────────────────────────────────────────────────────────────┤
│ id (PK)                   │ UUID                             │
│ assessment_uuid (FK)      │ References acat_assessments_v1   │
│ assessment_id (string)    │ User-facing string ID           │
│ rater_id (optional)       │ "anon-a7f3b2c1" [INDEXED]       │
│ rater_did (FK, NEW) ──┐   │ References acat_rater_          │
│                       │   │ credentials [NEW COLUMN]        │
│ h_truth...h_handoff   │   │ Human scores (0-100)            │
│ gap_truth...gap_      │   │ Computed: p3_* - h_*            │
│  handoff              │   │                                 │
│ submission_signature  │   │ Ed25519(vc_json) [NEW]          │
│ is_vc_signed (NEW)    │   │ BOOLEAN [NEW]                   │
│ notes                 │   │ Free text (max 2000)            │
│ rated_at              │   │ ISO 8601 timestamp              │
│ receipt_hash_sha256   │   │ SHA256(receipt)                 │
│ created_at            │   │ TIMESTAMP                       │
└───────────┬───────────┴───────────────────────────────────┘
            │
            │ (N:1)
            │
┌───────────┴──────────────────────────────────────────────┐
│         acat_rater_credentials (NEW)                      │
├─────────────────────────────────────────────────────────┤
│ id (PK)                │ UUID                             │
│ rater_did (UNIQUE)     │ did:key:z6MkhaXg... [INDEXED]   │
│ public_key_base58      │ Base58-encoded Ed25519 public   │
│ rater_name (optional)  │ "Dr. J. Smith" (no PII)        │
│ rater_affiliation      │ "researcher", "domain_expert"   │
│ capabilities[]         │ ["acat_scorer_v1"]              │
│ vc_json (JSONB)        │ W3C VC (HumanAIOS issued)       │
│ vc_issuer              │ "did:humanaios:v1"              │
│ is_revoked             │ BOOLEAN (credential rotation)   │
│ revocation_reason      │ Free text (if revoked)          │
│ created_at             │ TIMESTAMP                       │
│ updated_at             │ TIMESTAMP                       │
└─────────────────────────────────────────────────────────┘
```

---

## Layer 4: Request/Response Cycle

```
                    HUMAN SCORE SUBMISSION (SSI Mode)

┌─ Client (Human Rater) ────────────────────────────────────────┐
│                                                                 │
│  1. Generate DID Keypair (first time only)                     │
│     acat/identity/did_generator.py:generate_rater_credential() │
│     ├─ private_key = Ed25519.generate()                        │
│     ├─ public_key = private_key.public()                       │
│     ├─ rater_did = did:key:z6Mkha... (from public_key)        │
│     └─ [Store private_key SECURELY, never send to server]     │
│                                                                 │
│  2. Prepare Score Submission                                   │
│     POST /api/v1/acat/human-score-vc                           │
│     {                                                          │
│       "assessment_id": "uuid-xyz",                             │
│       "scores": {"h_truth": 75, "h_service": 68, ...},        │
│       "rater_did": "did:key:z6MkhaXg...",                     │
│       "private_key_base64": "...",                             │
│       "notes": "professional assessment"                       │
│     }                                                          │
│                                                                 │
│  3. Client-Side Signing (OPTIONAL, for transparency)           │
│     acat/identity/vc_signer.py:create_human_score_vc()        │
│     ├─ Build VC object (credentialSubject with scores)        │
│     ├─ Serialize to JSON (canonical order)                    │
│     ├─ Sign with private_key                                  │
│     └─ Attach proof.signatureValue                            │
│                                                                 │
│  4. Submit (Server performs server-side signing if needed)     │
│                                                                 │
└──────────────────────────────────┬──────────────────────────────┘
                                   │
                                   ▼
┌─ FastAPI Route: human_score_vc_route.py ─────────────────────┐
│                                                                │
│  1. Validate Payload                                          │
│     _validate_human_score_payload()                           │
│     └─ JSON Schema check (rater_did, scores, etc.)            │
│                                                                │
│  2. Fetch Existing Assessment                                 │
│     _fetch_assessment_row(assessment_id)                      │
│     ├─ Query acat_assessments_v1 by assessment_id             │
│     ├─ Retrieve p1_*, p3_*, model_did, etc.                  │
│     └─ [Assert row exists; 404 if not]                       │
│                                                                │
│  3. Retrieve/Verify Rater Credential                          │
│     IF rater_did provided:                                    │
│     ├─ Query acat_rater_credentials by rater_did              │
│     ├─ Get public_key_base58                                  │
│     ├─ Verify submitted VC signature (if present)             │
│     │  _verify_rater_vc(vc, rater_did)                        │
│     │  ├─ Reconstruct signed payload                          │
│     │  ├─ Verify Ed25519 signature with public_key            │
│     │  └─ Check expiration, revocation status                 │
│     └─ [Allow new rater DID; auto-create rater_credentials]  │
│                                                                │
│  4. Compute Gaps                                              │
│     for each dimension in ALL_12:                             │
│     ├─ gap[d] = ai_row.p3_d - submitted_h_d                 │
│     └─ [positive = AI scored itself higher]                   │
│                                                                │
│  5. Persist Human Score                                       │
│     _persist_human_score(...)                                 │
│     ├─ INSERT into acat_human_scores:                         │
│     │  ├─ assessment_uuid (FK)                                │
│     │  ├─ rater_id (anon-{12hex} if no DID)                 │
│     │  ├─ rater_did (if provided) [NEW]                      │
│     │  ├─ h_* fields (the scores)                            │
│     │  ├─ gap_* fields (computed)                            │
│     │  ├─ submission_signature (if signed) [NEW]             │
│     │  ├─ is_vc_signed (bool) [NEW]                          │
│     │  └─ rated_at (ISO 8601)                                │
│     └─ [Return persisted_row]                                 │
│                                                                │
│  6. Fetch Corpus Means (non-blocking)                         │
│     _fetch_corpus_means()                                     │
│     └─ SELECT avg(p1_*) per dimension from acat_assessments   │
│                                                                │
│  7. Build Receipt                                             │
│     _build_receipt(ai_row, scores, gaps, corpus, persisted)  │
│     ├─ Include assessment_id, human_score_id                 │
│     ├─ Include ai_scores.p3 + human_scores                    │
│     ├─ Include gaps + corpus_comparison                       │
│     ├─ Include rater_did (if present) [NEW]                  │
│     └─ [Serialize to JSON]                                    │
│                                                                │
│  8. Anchor to Blockchain                                      │
│     receipt_json = json.dumps(receipt, sort_keys=True)        │
│     receipt_hash = sha256(receipt_json.encode())              │
│     _anchor_originstamp(receipt_hash)                         │
│     ├─ POST {hash, comment} to OriginStamp API                │
│     ├─ [Rater DID now blockchain-bound via receipt_hash]      │
│     └─ [non-blocking; null if unavailable]                    │
│                                                                │
│  9. Return Response (201 Created)                             │
│     {                                                         │
│       "assessment_id": "uuid-xyz",                            │
│       "human_score_id": "human-uuid-abc",                     │
│       "rater_did": "did:key:z6MkhaXg..." [NEW],              │
│       "ai_scores": {p1: {...}, p3: {...}},                    │
│       "human_scores": {h_truth: 75, ...},                     │
│       "gap": {truth: 3, service: 10, ...},                    │
│       "receipt_hash_sha256": "a7f3...",                       │
│       "originstamp": {...blockchain_timestamp...}            │
│     }                                                         │
│                                                                │
└──────────────────────────────────┬───────────────────────────┘
                                   │
                                   ▼
┌─ Verification Service ────────────────────────────────────────┐
│                                                                │
│  Build Chain of Custody (on demand via GET endpoint)          │
│  acat/verification/chain_of_custody.py                        │
│  ├─ Query acat_assessments_v1 by assessment_uuid              │
│  ├─ Query acat_human_scores (all raters for this assessment) │
│  ├─ For each party (AI model, human raters):                 │
│  │  ├─ Retrieve DID credential from appropriate table        │
│  │  ├─ Verify signature(s)                                   │
│  │  │  ├─ For AI: verify p1_signature + p3_signature         │
│  │  │  ├─ For humans: verify submission_signature             │
│  │  │  └─ [cryptographic non-repudiation]                    │
│  │  └─ Build chain_of_custody JSON                           │
│  │                                                            │
│  └─ Return full chain (GET /api/v1/acat/assessment/{id}/chain)│
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## Layer 5: Anonymity Architecture (The Paradox)

```
WITHOUT SSI: Anonymity is Maximum but Unverifiable

   Human Rater
   │
   └─ "anon-a7f3b2c1" ← Opaque token
      │
      ├─ [Cannot trace back to person: ✓ Good]
      │
      ├─ [Cannot verify credibility: ✗ Bad]
      │
      ├─ [Cannot detect same rater scoring multiple assessments: ✗ Bad]
      │
      └─ [Scored 47 assessments with rater disagreement? Unknown who]


WITH SSI: Anonymity is Pseudonymous but Verifiable

   Human Rater (Personal Identity)
   │
   ├─ Name: "Jane Smith" (NEVER shared)
   ├─ Email: "jane@example.com" (NEVER shared)
   └─ Affiliation: "AI Safety Institute" (NEVER shared)
      │
      ├─ [Generates keypair locally]
      │
      ├─ [DID = did:key:z6MkhaXg... (deterministic from public key)]
      │   │
      │   ├─ [This DID is: IMMUTABLE, CRYPTOGRAPHICALLY BOUND]
      │   │
      │   └─ [This DID is: NOT REVERSIBLE to "Jane Smith"]
      │       (unless Jane herself reveals the mapping)
      │
      ├─ Stores in acat_rater_credentials:
      │   ├─ rater_did: "did:key:z6MkhaXg..."
      │   ├─ public_key_base58: "..." (non-secret)
      │   ├─ capabilities: ["acat_scorer_v1"]
      │   ├─ rater_affiliation: "researcher" (optional, generic)
      │   └─ [NO name, NO email, NO PII]
      │
      └─ Now can verify:
         ├─ "This DID has scored 47 assessments"
         ├─ "This DID has high inter-rater reliability (0.89)"
         ├─ "This DID's scores have low variance"
         │
         └─ WITHOUT EVER REVEALING: "This is Jane Smith"


THE PARADOX: SSI INCREASES PRIVACY BY SEPARATING FINGERPRINT FROM IDENTITY

   Behavior Fingerprint               Personal Identity
   │                                  │
   ├─ "did:key:z6Mkha..." (pseudonym) │
   │  ├─ Scored 47 assessments        │  Jane Smith
   │  ├─ High reliability             │  jane@example.com
   │  ├─ Low variance                 │  AI Safety Institute
   │  ├─ Prefers specific patterns    │
   │  └─ [VERIFIABLE, PUBLIC]         │  [PRIVATE, NEVER SHARED]
   │                                  │
   └─ Adversary can learn what        └─ Adversary cannot learn who
     "did:key:z6Mkha..." does           is behind that DID
                                      UNLESS Jane voluntarily reveals it


CONSEQUENCE: Anonymity is Strengthened

   ✓ Rater credibility is portable across systems (any SSI consumer)
   ✓ Personal identity is uncorrelated to behavioral fingerprint
   ✓ Can rotate identity (new keypair, new DID) without losing history
   ✗ Cannot trace DID back to person (only Jane knows)
   ✗ Cannot de-anonymize rater by correlating behavior patterns
```

---

**END OF VISUAL ARCHITECTURE**

This document is Z1 draft architecture. It shows:
1. **Current implementation** (AI fingerprinting + human anonymity)
2. **SSI enhancement points** (where W3C VCs + Ed25519 signatures integrate)
3. **Data model mapping** (new tables, foreign keys, indexing)
4. **Request/response flow** (signing, verification, chain of custody)
5. **Anonymity paradox** (why cryptographic identity increases privacy)

Next step: Z2 review of fork candidates and implementation scope.
