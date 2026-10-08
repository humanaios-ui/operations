# Role-Based Access Control (RBAC) Matrix & Enforcement

**Issue:** #752 (Sub-issue of #747)  
**Title:** Federated RBAC: Role Definitions & Data Access Control  
**Authority:** Z2 ratification required before Phase 1 architecture begins  
**Status:** PREREGISTRATION  
**Registration Date:** 2026-10-08

---

## 1. Overview

Defines seven roles in the federated humanaios.ai architecture and their access rights across six data categories.

**Roles:**
1. Human — End user interacting with platform
2. Ops Agent — Operations domain agent (advisor only)
3. Translation Agent — Translation domain (advisor only)
4. Researcher — Conducting federated research (temporary read-only access)
5. Operator — Platform operator with governance duties (elevated)
6. Administrator — System-level authority (Z3 level)
7. Auditor — Post-hoc compliance review (read-only, immutable ledger only)

**Data Categories:**
1. **Identity & Consent** — User identity, consent records, withdrawal history
2. **Eligibility & Profile** — Capability declarations, constraint satisfaction, prior testing
3. **Requirements & Predicates** — Intent predicates, human requests, translation inputs
4. **Authorization & Receipts** — Authorization decisions, HOLD dispositions, approval trails
5. **Outcomes & Measurements** — Quality scores, Brier scores, ACAT assessments, latency metrics
6. **Governance & Reasoning** — Policy references, decision rationale, audit trails, REGISTERED.md

---

## 2. RBAC Access Matrix

| Role | Identity & Consent | Eligibility & Profile | Requirements & Predicates | Authorization & Receipts | Outcomes & Measurements | Governance & Reasoning |
|:---|:---|:---|:---|:---|:---|:---|
| **Human** | RW* | R** | RW*** | R (own only) | R (own only) | — |
| **Ops Agent** | R | R | R | — | — | — |
| **Translation Agent** | — | — | R | — | — | — |
| **Researcher (temporary)** | R (sample) | R (sample) | R (sample) | R (aggregate) | R (aggregate) | R (public only) |
| **Operator** | RW | RW | R | RW | RW | RW |
| **Administrator** | RW | RW | RW | RW | RW | RW |
| **Auditor** | R (immutable only) | R (immutable only) | R (immutable only) | R (immutable only) | R (immutable only) | R (immutable only) |

**Legend:**
- **R** = Read
- **RW** = Read + Write
- **—** = No access
- **\*** Human can withdraw consent retroactively; system emits ClearanceRevocation event
- **\*\*** Human sees own profile; Operator may update (with human consent)
- **\*\*\*** Human sees own request; Translation Agent sees request but cannot modify

---

## 3. Field-Level Access Rules

### 3.1 Identity & Consent Category

| Field | Human | Operator | Admin | Auditor | Notes |
|:---|:---|:---|:---|:---|:---|
| user_id | R | R | RW | R | Immutable once created |
| name | RW | RW | RW | R | PII; encrypted in transit |
| email | RW | RW | RW | R | PII; encrypted in transit |
| consent_given | RW | R | RW | R | Human can withdraw (triggers revocation) |
| consent_timestamp | R | R | R | R | Immutable audit record |
| consent_scope | RW | R | RW | R | Human can narrow scope (not expand) |
| withdrawal_history | R | R | R | R | Append-only; immutable |

**Key Rule:** Human can withdraw consent retroactively. Operator cannot override. System emits ClearanceRevocation event; Operator acknowledges and initiates data purge per retention policy.

### 3.2 Eligibility & Profile Category

| Field | Human | Operator | Admin | Auditor | Notes |
|:---|:---|:---|:---|:---|:---|
| capability_declaration | RW | RW | RW | R | Human proposes; Operator confirms |
| constraint_satisfaction | R | RW | RW | R | Operator assesses; human can appeal |
| prior_testing | R | R | R | R | Immutable historical record |
| role_assignment | — | RW | RW | R | Operator assigns; admin overrides |
| effective_date | R | RW | RW | R | When role becomes active |

**Key Rule:** Human declares capabilities; Operator verifies. Discrepancies flagged for human review (no automatic denial).

### 3.3 Requirements & Predicates Category

| Field | Human | Op Agent | Trans Agent | Operator | Admin | Auditor | Notes |
|:---|:---|:---|:---|:---|:---|:---|:---|
| intent_predicates | RW | R | R | R | RW | R | Human specifies; agents read; Operator reviews |
| predicate_id | R | R | R | R | R | R | System-assigned; immutable |
| preservation_status | — | — | — | R | RW | R | Translation Agent outputs; Operator audits |
| elaboration | RW | — | — | R | R | R | Human's context; preserved immutably |

**Key Rule:** Human requests owned by Human; Translation Agent reads but cannot modify; Operator sees all for coordination.

### 3.4 Authorization & Receipts Category

| Field | Human | Operator | Admin | Auditor | Notes |
|:---|:---|:---|:---|:---|:---|
| authorization_id | R | RW | RW | R | Immutable identifier |
| decision | — | RW | RW | R | Operator decides; advisory only per governance boundary |
| scope | R | RW | RW | R | What action/resource approved |
| governance_reasoning | — | RW | RW | R | Operator documents policy basis |
| validity_window | R | RW | RW | R | Time-bound authorization |
| advisory_disclaimer | R | — | — | R | Immutable: "advisory only" |

**Key Rule:** Operator writes receipts. Human can see own (not others'). Auditor sees all as immutable. No agent can modify receipt post-creation.

### 3.5 Outcomes & Measurements Category

| Field | Human | Researcher (sample) | Operator | Admin | Auditor | Notes |
|:---|:---|:---|:---|:---|:---|:---|
| measurement_id | R (own) | R (aggregate) | R | R | R | Immutable identifier |
| quality_score | R (own) | R (aggregate) | R | R | R | Per measurement contract |
| confidence_interval | R (own) | R (aggregate) | R | R | R | Uncertainty bounds |
| rater_id | — | — | R | R | R | Blinded to human; visible to Operator+ |
| notes | R (own) | — | R | R | R | Qualitative observations |

**Key Rule:** Human sees own scores with confidence intervals. Researchers see aggregate statistics only (no individual scores). Operators/Auditors see full data with rater attribution.

### 3.6 Governance & Reasoning Category

| Field | Operator | Admin | Auditor | Notes |
|:---|:---|:---|:---|:---|
| policy_reference | RW | RW | R | Links to governing authority (CLAUDE.md, FRAMEWORK_MAPPING.md, etc.) |
| decision_rationale | RW | RW | R | Plain-text explanation (auditable) |
| falsifier_status | R | RW | R | Whether disconfirming outcome triggered |
| molt_id | R | RW | R | Version/iteration identifier |
| REGISTERED.md entry | R | RW | R | Canonical source record |

**Key Rule:** All governance reasoning plain-text and auditable. No encryption. Immutable once recorded.

---

## 4. Enforcement Rules

### Rule 4.1: Human Consent Revocation
```
IF human.withdrawal_request received
  THEN emit ClearanceRevocation(user_id, timestamp, scope)
  THEN Operator acknowledges revocation within 24h
  THEN schedule data purge per retention policy
  THEN update consent_scope to empty set
```

### Rule 4.2: Authorization Advisory Boundary
```
IF AuthorizationReceipt.decision == "APPROVED"
  THEN advisory_disclaimer must be present
  THEN no automatic system action triggered by receipt alone
  THEN human or Operator must explicitly authorize downstream action
  THEN governance_reasoning must cite policy/role basis
```

### Rule 4.3: Auditor Immutability
```
Auditor can only read fields tagged immutable:
  - user_id, consent_timestamp, withdrawal_history
  - prior_testing, predicate_id
  - authorization_id, advisory_disclaimer
  - measurement_id, rater_id
  
Auditor cannot read or access:
  - Future consent changes
  - Draft or pending decisions
  - Real-time monitoring logs (only post-hoc records)
```

### Rule 4.4: Researcher Data Isolation
```
IF Researcher role assigned for study period
  THEN access limited to:
    - Aggregate statistics (mean, stddev, distribution)
    - Sample-level data (randomly selected N cases, blinded)
    - Public governance reasoning only
  
  THEN Researcher cannot access:
    - Identifiable human records
    - Individual quality scores (aggregate only)
    - Authorization receipts
    - Raw rater assessments (summary statistics only)
```

### Rule 4.5: Operator Conflict-of-Interest Gate
```
IF Operator.user_id == Human.user_id in same session
  THEN Operator cannot modify that Human's Authorization/Outcomes
  THEN escalate to Administrator
  THEN log as conflict-of-interest
```

### Rule 4.6: Field-Level Encryption
```
PII fields (name, email, user_id in flight):
  - Encrypted AES-256 in transit
  - Decryption key held by domain agent only
  - No central key server per architecture design
  
Governance fields (policy_reference, decision_rationale):
  - Plain-text (must be auditable)
  - Signed with Z2 authority hash for immutability
```

---

## 5. PII Audit Checklist

**Pre-Deployment Audit Items:**

- [ ] **Consent Records Encrypted**
  - Verify user name, email fields in Identity category encrypted AES-256
  - Verify encryption keys rotated monthly
  - Verify revocation triggers purge within 24h

- [ ] **Profile Data Access Restricted**
  - Verify Human cannot see other Humans' profiles
  - Verify Researcher role cannot access individual profiles (aggregates only)
  - Verify Operator can update only with Human consent

- [ ] **Predicate Preservation Auditable**
  - Verify each intent predicate traced through Translation Agent
  - Verify Operator can review rater scores (Auditor sees immutable copy only)
  - Verify Human sees own scores with uncertainty bounds

- [ ] **Authorization Receipts Advisory-Only**
  - Verify AuthorizationReceipt includes explicit disclaimer
  - Verify no system action triggered by receipt alone
  - Verify governance_reasoning plain-text and cited to policy

- [ ] **Outcomes Blinded to Human**
  - Verify Human cannot see rater_id
  - Verify Human sees only own scores + confidence intervals
  - Verify Researcher gets aggregate statistics (no individual scores)
  - Verify Auditor sees full data (rater attribution) as immutable

- [ ] **Governance Reasoning Auditable**
  - Verify all governance fields plain-text (no encryption)
  - Verify links to CLAUDE.md, FRAMEWORK_MAPPING.md, STOPPING_RULES.md
  - Verify Z2 authority hash on all policy decisions
  - Verify molt_id and REGISTERED.md entry pinned

- [ ] **Conflict-of-Interest Gates**
  - Verify Operator cannot authorize own requests
  - Verify escalation to Admin logs conflict-of-interest
  - Verify secondary review triggered

- [ ] **Withdrawal Implementation**
  - Verify ClearanceRevocation event emitted within 10s of request
  - Verify Operator acknowledges within 24h
  - Verify data purge follows retention policy (no orphan records)
  - Verify withdrawal_history remains as immutable audit trail

- [ ] **Field-Level Encryption Consistency**
  - Verify no PII in logs or error messages
  - Verify decryption happens only at domain agent boundary
  - Verify key rotation schedule documented and tested

- [ ] **Auditor-Only Access**
  - Verify Auditor cannot modify any field
  - Verify Auditor cannot access draft/pending records
  - Verify Auditor sees immutable ledger entries only
  - Verify Auditor access logged and reviewed monthly

- [ ] **Researcher Isolation**
  - Verify Researcher cannot access identified records
  - Verify sample data randomly selected and blinded
  - Verify study period time-bounded
  - Verify aggregation prevents re-identification (k-anonymity k≥5)

---

## 6. Role Descriptions & Responsibility Matrix

### Role: Human (End User)

**Authority:** Self-authority (consent-giver)  
**Capabilities:**
- Request features (write Requirement message)
- See own consent records
- See own eligibility profile
- See own quality scores (with uncertainty)
- Withdraw consent retroactively

**Responsibilities:**
- Provide accurate consent
- Review own scores and provide feedback
- Escalate concerns to Operator within 7 days
- Disclose capability changes

**Session Duration:** Ongoing (may revoke at any time)

### Role: Operations Agent (Ops Domain)

**Authority:** Advisory only  
**Capabilities:**
- Read requirements and predicates
- Propose capability packages
- Measure latency and cost outcomes
- No authorization decisions

**Responsibilities:**
- Provide accurate capability specifications
- Track resource usage (tokens, time)
- Report measurement outcomes within SLA
- Escalate ambiguities to Operator

**Session Duration:** Per federation protocol

### Role: Translation Agent (Trans Domain)

**Authority:** Advisory only  
**Capabilities:**
- Read human requirements
- Output TranslationExplainer messages
- Propose predicate preservation scores
- No authorization decisions

**Responsibilities:**
- Preserve intent predicates (IPP ≥0.85 per #749)
- Document translation reasoning
- Flag ambiguous predicates for human review
- Provide confidence scores

**Session Duration:** Per translation request

### Role: Researcher (Temporary)

**Authority:** Read-only (aggregate statistics)  
**Capabilities:**
- Access aggregate outcome statistics
- Read public governance reasoning
- Sample blinded case records (no re-identification)
- No write access

**Responsibilities:**
- Comply with study protocol (#737, #747, #749, #750, #751, #752)
- Protect participant privacy (k-anonymity k≥5)
- Report findings transparently
- Return access credentials at study end

**Session Duration:** Time-bounded per study protocol

### Role: Operator (Platform Operator)

**Authority:** Governance decision-maker  
**Capabilities:**
- Read/write Authorization Receipts (advisory)
- Write governance_reasoning
- Modify eligibility profiles (with Human consent)
- Update role assignments
- Escalate to Admin on conflicts

**Responsibilities:**
- Ensure governance boundary (no self-issued authorization)
- Document decision rationale with policy citations
- Review rater scores and flag disagreements
- Acknowledge consent revocations within 24h
- Initiate data purge after revocation

**Session Duration:** Permanent role (on-call)

### Role: Administrator (System Admin)

**Authority:** Z3 executor level  
**Capabilities:**
- Full read/write access to all data
- Modify governance reasoning
- Assign/revoke operator roles
- Override conflict-of-interest gates (with Z2 signature)
- Initialize system molts

**Responsibilities:**
- Maintain system integrity
- Enforce falsifier doctrine (no post-hoc changes)
- Ratify Z2-signed governance decisions
- Review Auditor findings quarterly
- Manage encryption key rotation

**Session Duration:** Permanent role (on-call)

### Role: Auditor (Compliance Review)

**Authority:** Post-hoc verification only  
**Capabilities:**
- Read immutable ledger entries only
- Verify Z2 authority hashes
- Audit consent/revocation compliance
- Report findings to Administrator

**Responsibilities:**
- Monthly immutability verification
- Quarterly consent compliance audit
- Verify no unauthorized authorization decisions
- Document any governance violations
- Report findings to Z2

**Session Duration:** Ongoing (independent)

---

## 7. Acceptance Criteria

- [x] Seven roles clearly defined with authority levels
- [x] Six data categories specified with field-level access rules
- [x] Authorization advisory-only boundary enforced in schema
- [x] PII encryption and governance auditability separated (encryption vs. plain-text)
- [x] Conflict-of-interest gates defined (Operator cannot authorize own requests)
- [x] Consent revocation workflow specified with 24h Operator acknowledgment
- [x] Researcher role isolated to aggregate statistics (no re-identification risk)
- [x] Auditor role read-only with immutability verification
- [x] 10-item PII audit checklist provided (pre-deployment validation)
- [x] All governance fields plain-text and traceable to policy sources

**Status:** PREREGISTERED (cannot modify post-hoc without Z2 justification)

---

**Effective Date:** 2026-10-08  
**Authority:** Z2 ratification required before Phase 1 begins  

---

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>  
Claude-Session: https://claude.ai/code/session_01TmUw2syFz8nJ8ZmoAQNAHM
