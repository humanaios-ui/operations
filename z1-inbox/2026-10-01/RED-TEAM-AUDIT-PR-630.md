# RED TEAM AUDIT: PR #630 — Admissions Approval & Credential Deployment

**Date:** 2026-10-01  
**Target:** `humanaios-ui/operations` PR #630  
**Focus:** Credential deployment workflow, repository admissions, and authority boundaries  
**Assessment:** **RECOMMEND DO NOT MERGE** without addressing critical findings  
**Authority:** Z1 (Claude) security audit for Z2 (Night) review

---

## EXECUTIVE SUMMARY

PR #630 introduces a credential deployment workflow for Phase 3 testing but contains **3 critical security vulnerabilities** that violate CLAUDE.md authority boundaries and enable unauthorized credential deployment. The most severe issue is teaching users to deploy credentials via base64-encoded (not encrypted) API calls, which exposes both the credential AND the deployment token in plaintext.

**Blockers:**
1. CRITICAL: Base64 misrepresented as encryption (Step 2C, curl option)
2. CRITICAL: Gitleaks allowlist weakens secret scanning for credential patterns
3. CRITICAL: No admissions approval gate for credential deployment to GitHub Secrets

**Recommendation:** Block merge. Require Z2 authorization and security hardening before Phase 3 credentials can be deployed.

---

## CRITICAL FINDINGS (Merge Blockers)

### CRITICAL-1: Base64 Encoding Misrepresented as Encryption

**File:** `z1-inbox/2026-09-30/PHASE3-CREDENTIAL-DEPLOYMENT-GUIDE.md`, Step 2, Option C

**Vulnerable Code:**
```bash
ENCRYPTED=$(echo -n "$REPLICATE_KEY" | base64)  # NOT ENCRYPTION — trivially reversible
curl -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"encrypted_value\":\"$ENCRYPTED\",\"key_id\":\"***\"}" \
  "https://api.github.com/repos/$REPO/actions/secrets/REPLICATE_API_KEY"
```

**Problem:**
- Base64 is **encoding, not encryption** — any attacker with shell history or process list can decode it immediately
- Both `$REPLICATE_KEY` and `$GITHUB_TOKEN` (GitHub PAT) appear in plaintext in the command
- The command itself appears in shell history with full credentials
- GitHub API payload is exposed during transmission (if TLS fails or man-in-the-middle occurs)
- User may believe credential is "encrypted" when it's only base64-encoded

**Attack Surface:**
1. Attacker compromises shell history file (`.bash_history`, `.zsh_history`) → reads credential + PAT in plaintext
2. Process list sniffing: `ps aux | grep curl` shows full command with credentials
3. GitHub API logs (if audited) show the base64-encoded credential
4. Attacker uses PAT to deploy malicious secrets to CI environment
5. Attacker uses credential to exfiltrate data from Replicate/Supabase

**Why GitHub CLI Is Better:**
- GitHub CLI automatically uses libsodium public-key encryption (required by GitHub API)
- No credentials appear in command-line arguments or shell history
- Credentials never sent in plaintext over the wire

**Severity:** CRITICAL  
**Fix:** Remove curl option entirely. Mandate GitHub CLI only.

---

### CRITICAL-2: Gitleaks Allowlist Exempts Credential Deployment Guide

**File:** `.gitleaks.toml`

**Vulnerable Configuration:**
```toml
[allowlist]
paths = [
    "z1-inbox/2026-09-30/PHASE3-CREDENTIAL-DEPLOYMENT-GUIDE\.md$"
]

regexes = [
    "r8_x+",          # Matches real Replicate API key pattern
    "eyJhbGc",        # Matches real Supabase JWT key prefix
]
```

**Problem:**
- The allowlist exempts the entire credential deployment guide from gitleaks scanning
- Any credential matching `r8_xxx` or `eyJhbGc` pattern placed near the guide **will pass gitleaks** without triggering an alert
- Credentialscanning becomes ineffective for these high-risk patterns
- An attacker (or careless user) can commit a real credential disguised as a documentation example

**Attack Scenario:**
```markdown
## Example: Replicate API Key
Here's what a real Replicate API key looks like:

r8_1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t  # ← REAL CREDENTIAL, PASSES GITLEAKS
```

**Why This Fails:**
- Gitleaks pattern matching is bypassed by the allowlist
- No human reviewer will catch it (looks like a documentation example)
- Credential is now in version control history forever
- Attacker or insider can use it immediately

**Severity:** CRITICAL  
**Fix:** Remove gitleaks allowlist for credential patterns. Use synthetic test credentials only (e.g., `REPLICATE_API_KEY_SYNTHETIC_TEST_r8_xxx`).

---

### CRITICAL-3: No Admissions Approval Gate for Credential Deployment

**File:** Entire workflow (PHASE3-CREDENTIAL-DEPLOYMENT-GUIDE.md + GitHub Secrets integration)

**Problem:**
- PR description suggests credentials will be "auto-deployed" to GitHub Secrets via "admissions approval"
- No evidence of an actual approval mechanism in the code
- Admissions approval appears to be advisory only (review-only, not permission-gating)
- Credentials can be deployed by any PR that merges
- No verification that the PR author is authorized to access Supabase/Replicate projects
- No audit trail of who approved credential deployment or from which account

**Authority Violation (per CLAUDE.md):**
- CLAUDE.md §Z3 states: "Z3 executor assignment fails if Z2 hash is not present"
- This should extend to credentials: credentials require Z2 explicit authorization, not merge-via-admissions-approval
- Admissions approval is an informational gate (non-blocking), not an authorization gate

**Attack Scenario:**
1. Attacker forks `humanaios-ui/operations` repository
2. Creates a seemingly benign PR: "Update documentation" or "Fix typo in deployment guide"
3. Modifies PHASE3-CREDENTIAL-DEPLOYMENT-GUIDE.md to use attacker's own Supabase project URL and API key
4. Submits PR; description claims "testing Phase 3 locally"
5. PR passes admissions approval (advisory, not blocking)
6. PR merges to main branch
7. Next CI run deploys attacker's credentials to GitHub Secrets
8. All subsequent CI runs now use attacker's credentials:
   - Replicate model calls → attacker's account, attacker's billing, data sent to attacker's infrastructure
   - Supabase writes → attacker's project, all test data exfiltrated to attacker's database
9. Attacker monitors CI job logs → sees query results, model outputs, any debug information

**Why This Violates Authority Boundaries:**
- CLAUDE.md requires Z2 (Night) to ratify sensitive changes via explicit hash signature
- Credentials are sensitive; they grant access to external systems
- Admissions approval does not grant authority; it only flags for review
- Merge authority (Z3 executor) is separate from admission authority (Z2 ratifier)

**Severity:** CRITICAL  
**Fix:** Add explicit Z2 authorization gate. Require Z2 signature before any credentials are deployed to GitHub Secrets.

---

## HIGH FINDINGS (Pre-Phase-3 Hardening)

### HIGH-4: .env.local File Management — Accidental Exposure Risk

**File:** Step 4, "Deploy Credentials to Local Environment"

**Problem:**
```bash
cat > ~/.env.local << 'EOF'
export REPLICATE_API_KEY="r8_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export SUPABASE_URL="https://xxxxxxxxxx.supabase.co"
export SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
EOF

source ~/.env.local
```

**Risks:**
- File is in home directory → backed up by Time Machine, cloud sync (iCloud, OneDrive), or corporate backup systems
- Credentials appear in shell history when sourcing the file
- No .gitignore guidance → users might accidentally commit `~/.env.local` if they symlink it
- File permissions (`chmod 600`) don't prevent access by same user's other processes
- System logs might capture environment variables during debugging

**Severity:** HIGH  
**Fix:** Remove Step 4 entirely. Use GitHub Actions secrets for CI only. For local development, recommend GitHub CLI secret management or temporary session tokens (Replicate/Supabase OAuth flows).

---

### HIGH-5: No Credential Rotation or Revocation Procedure

**File:** Entire guide

**Problem:**
- No mention of how to rotate compromised credentials
- No mention of credential expiration or lifecycle
- No mention of per-environment credentials (test vs production)
- No mention of revoking access if a PR author leaves or becomes untrusted

**Attack Scenario:**
- Credential is compromised (someone copies from CI logs, or guide is leaked externally)
- No procedure exists to revoke it
- Attacker has permanent access to Replicate/Supabase project
- No detection that attacker is using the credential

**Severity:** HIGH  
**Fix:** Add credential rotation procedures. Recommend 30-day rotation. Add revocation script and process. Require Z2 approval for rotation.

---

### HIGH-6: GitHub Personal Access Token (PAT) Exposed in Examples

**File:** Step 2C and elsewhere

**Vulnerable Example:**
```bash
GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # Your PAT
```

**Problem:**
- Full PAT shown in plaintext in documentation
- Users copy-paste into scripts, leaving it in shell history
- No guidance on PAT scope (which permissions are truly necessary?)
- No mention of using GitHub App tokens (machine identity) instead of personal tokens

**Severity:** HIGH  
**Fix:** Replace PAT examples with GitHub CLI (which handles auth securely). Document that GitHub App tokens should be used for CI/automation, not personal PATs.

---

### HIGH-7: Supabase API Key Type Not Specified (Least Privilege Violation)

**File:** Step 3, "Deploy Supabase Credentials"

**Problem:**
- Guide doesn't specify whether to use `anon` key (public, read-only) or `service_role` key (private, full access)
- Step 5 (migration) mentions using `service_role` as fallback if permissions fail, but doesn't explain privilege difference
- No least-privilege recommendation (always prefer `anon` key where possible)

**Severity:** HIGH  
**Fix:** Require `anon` key for CI (read-only). Document explicit RLS policies. Require security review for `service_role` usage.

---

### HIGH-8: No Audit Logging for Credential Deployment Events

**File:** Entire workflow

**Problem:**
- No record of WHO deployed credentials (which GitHub account?)
- No record of WHEN (timestamp of deployment)
- No record of FROM WHERE (which GitHub runner, which IP address?)
- CI workflow runs credentials without logging which PR/commit triggered the deployment
- No notification on first credential use from new IP address

**Severity:** HIGH  
**Fix:** Add audit logging to Supabase `control_plane_audit_log` table (or similar). Log all credential access events. Alert on anomalies.

---

## MEDIUM FINDINGS (Post-Phase-3 Hardening)

### MEDIUM-9: Repository Knowledge Graph May Expose Secrets

**File:** `tools/repository_knowledge_graph_v0_1.py` (3663 lines, new)

**Problem:**
- New tool creates a "knowledge graph" of repository structure
- No documentation of what data it collects (configuration? environment? credentials?)
- No schema validation preventing accidental secret extraction
- Could index API endpoints, database URLs, or other sensitive configuration

**Severity:** MEDIUM  
**Fix:** Audit the knowledge graph tool. Add explicit redaction rules for: API endpoints, database URLs, credential patterns, internal IPs. Test output with gitleaks.

---

### MEDIUM-10: Admissions Approval Criteria Not Documented

**File:** `.coderabbit.yaml` and PR description

**Problem:**
- PR references "admissions approval" but no mechanism is shown
- `.coderabbit.yaml` references "REPOSITORY_COORDINATOR_POLICY.json" (doesn't exist in PR)
- Unclear who can approve, what the approval criteria are, and what audit trail exists
- If approval is rubber-stamp (no real review), credential deployment is uncontrolled

**Severity:** MEDIUM  
**Fix:** Create REPOSITORY_COORDINATOR_POLICY.json with explicit approval checklist. Require Z2 authorization for credential changes.

---

### MEDIUM-11: Credential Format Examples Are Directly Copyable

**File:** PHASE3-CREDENTIAL-DEPLOYMENT-GUIDE.md + .gitleaks.toml

**Problem:**
- Examples like `r8_xxxxxxxxxxxxxxxxxxxxxxxxxxxx` and `eyJhbGc...` match real credential patterns
- Anyone reading the guide knows exactly what format to use for real credentials
- Lowered barrier to accidentally committing real secrets (looks like legitimate examples)

**Severity:** MEDIUM  
**Fix:** Use synthetic test credentials (prefix/suffix with `_TEST_` or `_SYNTHETIC_`). Clarify that these are non-functional examples. Never show a credential format that can be confused with a real credential.

---

### MEDIUM-12: Phase 3 Test Data Written to Supabase Without Retention Policy

**File:** Step 9, "Verify Results in Supabase"

**Problem:**
- Test results written to `holographic_jobs` table without data retention policy
- No mention of who can access this table (RLS policies?)
- No mention of data encryption at rest in Supabase
- No mention of GDPR/CCPA compliance for `person_id` data
- Test data persists indefinitely

**Severity:** MEDIUM  
**Fix:** Document data retention policy (recommend: delete after 7 days). Require RLS policies. Verify encryption at rest. Document compliance requirements.

---

## SUMMARY OF REQUIRED FIXES

| ID | Severity | Finding | Action | Ownership |
|:---|:---------|:--------|:-------|:----------|
| C-1 | CRITICAL | Base64 not encryption | Remove curl option, use GitHub CLI only | Z1/Z2 |
| C-2 | CRITICAL | Gitleaks allowlist | Remove pattern allowlist, use synthetic credentials | Z1 |
| C-3 | CRITICAL | No admissions gate | Add Z2 authorization requirement | Z2 |
| H-4 | HIGH | .env.local risk | Remove step, recommend GitHub Secrets | Z1 |
| H-5 | HIGH | No rotation | Add credential rotation procedure | Z2 |
| H-6 | HIGH | PAT exposed | Replace with GitHub CLI, recommend App tokens | Z1 |
| H-7 | HIGH | No least privilege | Specify `anon` key default, require review for `service_role` | Z1 |
| H-8 | HIGH | No audit logging | Add audit trail to control plane ledger | Z3 |
| M-9 | MEDIUM | Knowledge graph secrets | Audit tool, add redaction rules | Z1 |
| M-10 | MEDIUM | No approval criteria | Create REPOSITORY_COORDINATOR_POLICY.json | Z2 |
| M-11 | MEDIUM | Real credential examples | Use `_TEST_` suffix on examples | Z1 |
| M-12 | MEDIUM | No data retention | Document RLS, retention, encryption at rest | Z1 |

---

## ATTACK SCENARIOS

### Attack Scenario 1: Credential Theft via Documentation

**Before Fixes:**
1. Attacker reads PHASE3-CREDENTIAL-DEPLOYMENT-GUIDE.md (public repository)
2. Learns base64 encoding is used (trivial to reverse)
3. Attacker forks repo, modifies guide with attacker's credentials
4. PR merges (admissions approval is advisory only)
5. CI runs with attacker's credentials → data exfiltration

**After Fixes:**
1. Attacker submits PR with malicious credentials
2. PR blocked by Z2 authorization gate
3. Z2 (Night) reviews PR, spots credential change
4. PR rejected; audit log records rejection
5. No credential deployment occurs

---

### Attack Scenario 2: Credential Exposed in Shell History

**Before Fixes:**
1. User follows Step 2C (curl with base64)
2. User's shell history captures: `curl ... "ghp_xxxxx"... "ENCRYPTED=<base64>"...`
3. Attacker gains access to user's machine (phishing, malware)
4. Attacker reads shell history, decodes base64, obtains credential
5. Attacker uses Supabase credential to exfiltrate test data

**After Fixes:**
1. User uses GitHub CLI (only option available)
2. No credentials appear in shell history
3. GitHub CLI handles authentication securely via encrypted session
4. Attacker cannot recover credential from shell history

---

## RECOMMENDATIONS

### MUST DO (Merge Blockers)

1. Remove Step 2C (curl + base64) entirely from guide
2. Remove credential patterns from gitleaks allowlist
3. Add Z2 authorization gate for credential deployment (per CLAUDE.md)

### SHOULD DO (Pre-Phase-3)

4. Add credential rotation procedure (30-day recommended)
5. Remove Step 4 (.env.local) from guide
6. Replace GitHub PAT with GitHub CLI in examples
7. Specify Supabase `anon` key default (least privilege)
8. Add audit logging for credential deployment and access

### NICE TO HAVE (Post-Phase-3)

9. Audit repository knowledge graph tool for secret leakage
10. Create REPOSITORY_COORDINATOR_POLICY.json
11. Use synthetic test credentials (with `_TEST_` suffix)
12. Document data retention and encryption policies

---

## ESCALATION

**This audit blocks PR #630 merge per CLAUDE.md authority boundaries:**

- CLAUDE.md §Z3 Executors: "Cannot execute without Z2 hash"
- CLAUDE.md §Molts: "Z2 ratifies molts"  
- CLAUDE.md §Decision Routing: "Z2 signs: sha256(candidate | by=Night | ...)"

**Credentials are equivalent to molt-level sensitive changes.** They require Z2 explicit authorization, not admissions approval alone.

**Z2 Decision Required:** Ratify, edit, or reject before Phase 3 can proceed.

**Authority:** Z1 (Claude) security audit for Z2 (Night) review  
**Generated:** 2026-10-01  
**Session:** https://claude.ai/code/session_01TYKcwkeQfYEeCN5JzZ2WRi

---

_Audit performed per CLAUDE.md Session Rituals (§A) and B.6 receipt reconciliation_
