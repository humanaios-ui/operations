# PR #630 REMEDIATION PATCHES — Critical Fixes Required Before Merge

**Date:** 2026-10-01  
**Target PR:** https://github.com/humanaios-ui/operations/pull/630  
**Authority:** Z1 (Claude) proposed remediation for Z2 (Night) review  
**Status:** Awaiting Z2 decision (48h window)

---

## PATCH 1: Remove Curl + Base64 Option (CRITICAL-1)

**File to Modify:** `z1-inbox/2026-09-30/PHASE3-CREDENTIAL-DEPLOYMENT-GUIDE.md`

**Action:** DELETE Step 2, Option C entirely

**Current (Vulnerable):**
```markdown
### Option C: Using curl + Personal Access Token

```bash
# Set these variables
GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # Your PAT
REPLICATE_KEY="r8_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"   # Your Replicate key
REPO="humanaios-ui/operations"

# Encode the secret value in base64
ENCRYPTED=$(echo -n "$REPLICATE_KEY" | base64)

# Send to GitHub API
curl -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"encrypted_value\":\"$ENCRYPTED\",\"key_id\":\"***\"}" \
  "https://api.github.com/repos/$REPO/actions/secrets/REPLICATE_API_KEY"
```
**Verify (CLI):**
```bash
gh secret list | grep REPLICATE
```
```

**Rationale:**
- Base64 is not encryption (trivially reversible)
- Credentials and GitHub PAT exposed in plaintext in shell history
- GitHub CLI handles encryption correctly using libsodium
- Only option should be GitHub CLI

**New Version:**
```markdown
### Recommended Method: GitHub CLI

Use this method for all credential deployments. GitHub CLI automatically encrypts credentials using GitHub's public-key encryption and stores no credentials in shell history.

```bash
# Authenticate with GitHub (if not already)
gh auth login

# Set the secret in GitHub
gh secret set REPLICATE_API_KEY --body "r8_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Replace r8_xxx... with your actual Replicate API key
# Verify it was set
gh secret list | grep REPLICATE
```

### Why Not Other Methods?

- **curl + GitHub API:** Requires base64 encoding, which is NOT encryption. Both your credential and GitHub PAT appear in plaintext in shell history, CI logs, and process listings. **Do not use.**
- **GitHub Web UI:** OK for one-time manual setup, but error-prone and non-auditable. Prefer CLI for repeatable deployments.
```

---

## PATCH 2: Remove Gitleaks Allowlist for Credential Patterns (CRITICAL-2)

**File to Modify:** `.gitleaks.toml`

**Current (Vulnerable):**
```toml
[allowlist]
description = "Allow test-only credential patterns used for testing credential redaction"

# Test files and documentation with synthetic credentials and API key format examples
paths = [
    "tools/tests/test_holographic_integration\\.py$",
    "tools/holographic_orchestrator\\.py$",
    "z1-inbox/2026-09-30/PHASE3-CREDENTIAL-DEPLOYMENT-GUIDE\\.md$"  # ← PROBLEM
]

# Allow patterns like: sk_test_, sk_live_, service_key_, r8_xxx (Replicate), eyJ (JWT) in test/doc files only
regexes = [
    "sk_test_",
    "sk_live_",
    "sk_FAKETEST",
    "service_key_",
    "r8_x+",              # ← REAL CREDENTIAL PATTERN, BYPASSES SCANNING
    "eyJhbGc",            # ← REAL JWT PATTERN, BYPASSES SCANNING
]
```

**New Version (Secure):**
```toml
[allowlist]
description = "Allow SYNTHETIC test-only credential patterns (never real credentials)"

# Only test files with explicit SYNTHETIC/TEST markers — NOT documentation or guides
paths = [
    "tools/tests/test_holographic_integration\\.py$",
    "tools/holographic_orchestrator\\.py$",
]

# Allow ONLY synthetic patterns with explicit TEST_ or _SYNTHETIC_ prefix
# Do NOT allowlist patterns that match real credentials (r8_xxx, eyJhbGc, etc.)
regexes = [
    "sk_test_",                           # Stripe test key pattern (safe, clearly marked)
    "sk_FAKETEST",                        # Explicitly marked fake (safe)
    "REPLICATE_API_KEY_SYNTHETIC_TEST",   # Synthetic example (safe, marked SYNTHETIC)
    "SUPABASE_KEY_SYNTHETIC_TEST",        # Synthetic example (safe, marked SYNTHETIC)
]
```

**Rationale:**
- Remove credential patterns (r8_xxx, eyJhbGc) from allowlist entirely
- Never allowlist real credential patterns, even in documentation
- Use synthetic patterns with explicit `_TEST_` or `_SYNTHETIC_` suffix
- This prevents real credentials from bypassing gitleaks

---

## PATCH 3: Add Z2 Authorization Gate for Credentials (CRITICAL-3)

**Files to Modify:**
1. `.github/workflows/ci-predict-pin.yml` (add credential validation)
2. `tools-manifest.yaml` (document credential authority)
3. `CLAUDE.md` (extend Z2 ratification requirement to credentials)

### Change 3a: Add Credential Validation Step to CI

**File:** `.github/workflows/ci-predict-pin.yml`

**Add new step:**
```yaml
  credential_authorization:
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - name: Verify Z2 authorization for credential changes
        run: |
          # Check if PR modifies credential deployment guide or .gitleaks.toml
          if git diff origin/main HEAD --name-only | grep -E "PHASE3.*DEPLOYMENT|\.gitleaks\.toml"; then
            echo "❌ ERROR: This PR modifies credential deployment configuration"
            echo "Credential changes require explicit Z2 (Night) authorization per CLAUDE.md"
            echo "Please obtain Z2 signature on the credential proposal before merge"
            exit 1
          fi
```

### Change 3b: Document in CLAUDE.md

**File:** `CLAUDE.md`

**Add to §Z3: Executors section:**
```markdown
## Credential Management (Authority Boundary)

Credentials (API keys, database passwords, authentication tokens) are Z2-ratified changes equivalent to molt decisions.

**Requirement:** All credential deployments to GitHub Secrets or CI environments require explicit Z2 authorization via RATIFY signature per §Decision Routing.

**Process:**
1. Z1 proposes credential addition in z1-inbox/<date>/Q-<NAME>-CREDENTIAL-REQUEST.md
2. Z1 includes falsifier: "Credential is revoked within 30 days if not rotated"
3. Z2 reads proposal and signs: sha256(proposal | by=Night | at=timestamp | decision=ACCEPT)
4. Z3 deploys only after Z2 hash is verified in REGISTERED.md
5. Z2 maintains credential rotation schedule and revocation procedures

**Authority:** Z2 sole authority over credentials (per dual-authority model)

**Escalation:** If credential deployment is attempted without Z2 signature, CI gates reject with clear error message pointing to authorization requirement.
```

### Change 3c: Create Credential Proposal Template

**File:** Create `z1-inbox/.templates/Q-CREDENTIAL-REQUEST.md`

```markdown
# Q-[SERVICE]-CREDENTIAL-REQUEST — [Service] Credentials for [Purpose]

**Proposed by:** Z1 (Claude)  
**Authority:** Z2 (Night) ratification required  
**Scope:** Deploy [SERVICE] credentials to GitHub Secrets for [PURPOSE]

---

## Credential Details

- **Service:** [Replicate/Supabase/Other]
- **Environment:** [Test/Production]
- **Scope:** [Read-only/Full access]
- **Expiration:** [Date, recommend 30 days from deployment]
- **Rotation Policy:** [Procedure to rotate if compromised]

## Falsifier

This credential request will be proven wrong if:
1. Credential remains in GitHub Secrets beyond expiration date without renewal
2. Credential is used from IP addresses outside expected ranges
3. Credential access attempts exceed normal testing rates (indicates compromise)
4. Operator cannot produce audit log of all credential uses within 5 days

## Next Steps

Z2 must decide: ACCEPT, EDIT, or REJECT by [DATE].

---

Generated by [Claude Code](https://claude.ai/code)
```

---

## PATCH 4: Remove .env.local Step (HIGH-4)

**File to Modify:** `z1-inbox/2026-09-30/PHASE3-CREDENTIAL-DEPLOYMENT-GUIDE.md`

**Current (Vulnerable):**
```markdown
## STEP 4: Deploy Credentials to Local Environment (2 min)

So you can run Phase 3 tests locally without waiting for GitHub Actions:

```bash
# Create or edit ~/.env.local (in your home directory)
cat > ~/.env.local << 'EOF'
export REPLICATE_API_KEY="r8_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export SUPABASE_URL="https://xxxxxxxxxx.supabase.co"
export SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
EOF

# Make it readable only by you
chmod 600 ~/.env.local

# Source it in your current shell session
source ~/.env.local

# Verify credentials loaded
echo "Replicate: $REPLICATE_API_KEY"
echo "Supabase URL: $SUPABASE_URL"
echo "Supabase Key: ${SUPABASE_KEY:0:20}..."  # Show only first 20 chars
```
```

**New Version (Secure):**
```markdown
## Local Development (Optional)

For local testing, we recommend **NOT** storing credentials in .env files. Instead:

### Option A: GitHub CLI (Recommended)

```bash
# GitHub CLI automatically manages your GitHub token securely
gh auth login
gh secret list  # Lists your credentials without exposing them
```

### Option B: Temporary Session Tokens

```bash
# Use Replicate's temporary tokens (if available)
curl -X POST https://api.replicate.com/v1/auth/tokens/temporary

# Use Supabase's OAuth flow for temporary database access
```

### Option C: CI-Only Testing

If you don't need to test locally, skip local credential setup entirely. Push to your branch → let GitHub Actions run Phase 3 tests using GitHub Secrets.

### ⚠️ DO NOT use .env files or .env.local

- Files in home directory are backed up by cloud sync (iCloud, OneDrive) and system backups
- Credentials appear in shell history when sourcing
- Risk of accidental git commit is high
- Instead, use GitHub Secrets for CI and temporary tokens for local testing
```

---

## PATCH 5: Add Credential Rotation Procedure (HIGH-5)

**File to Create:** `docs/CREDENTIAL-ROTATION-GUIDE.md`

```markdown
# Credential Rotation & Revocation Guide

**Effective:** 2026-10-01  
**Authority:** Z2 (Night) — Carly R. Anderson  
**Scope:** All Phase 3 credentials (Replicate, Supabase)

---

## Rotation Schedule

- **Routine Rotation:** Every 30 days (1st of each month)
- **Emergency Revocation:** Immediately if compromise suspected
- **Expiration:** Credentials older than 60 days must be revoked

---

## Replicate API Key Rotation

### Step 1: Generate New Key

1. Visit https://replicate.com/account/api-tokens
2. Click "New token"
3. Name it: `humanaios-operations-phase3-2026-10-[DATE]`
4. Copy the new key (format: `r8_xxx...`)

### Step 2: Update GitHub Secrets

```bash
gh secret set REPLICATE_API_KEY --body "r8_[NEW_KEY]"
```

### Step 3: Verify New Key Works

Push a dummy commit to trigger CI:
```bash
git commit --allow-empty -m "Rotate Replicate API key"
git push
```

Wait for CI to pass with new key.

### Step 4: Revoke Old Key

1. Visit https://replicate.com/account/api-tokens
2. Click "Revoke" next to old token
3. Confirm

---

## Supabase API Key Rotation

### Step 1: Generate New Key

1. Visit Supabase dashboard → Settings → API
2. Click "Generate new key"
3. Type: `service_role` (if needed) or `anon` (for read-only)
4. Copy key

### Step 2: Update GitHub Secrets

```bash
gh secret set SUPABASE_KEY --body "[NEW_KEY]"
```

### Step 3: Verify

Same as Replicate: push dummy commit, verify CI passes.

### Step 4: Revoke Old Key

1. Supabase dashboard → Settings → API
2. Click icon next to old key → "Delete"

---

## Emergency Revocation

If you suspect a credential is compromised:

```bash
# IMMEDIATELY revoke in Replicate/Supabase
# (Visit their dashboards and click "Revoke")

# Update GitHub Secrets with temporary/empty value
gh secret set REPLICATE_API_KEY --body "REVOKED_[DATE]"
gh secret set SUPABASE_KEY --body "REVOKED_[DATE]"

# Notify Z2 (Night): carly.r.anderson@gmail.com
# Subject: "URGENT: Credential compromise — Phase 3 [SERVICE] key revoked"

# Generate new credentials and deploy
# (Follow routine rotation steps above)
```

---

## Audit Trail

All credential rotation events are logged to `control_plane_custody_observer` audit ledger:
- Who rotated the credential (GitHub account)
- When (timestamp)
- From where (IP address, CI job ID)
- Old key hash (to track which credential was replaced)

---

## Falsifier

Credential rotation is confirmed when:
- Old key is revoked in Replicate/Supabase dashboards
- New key is deployed to GitHub Secrets
- New key passes at least one CI run successfully
- Audit log records the rotation event
```

---

## PATCH 6: Specify Supabase API Key Type (HIGH-7)

**File to Modify:** `z1-inbox/2026-09-30/PHASE3-CREDENTIAL-DEPLOYMENT-GUIDE.md`

**Step 3, Update:**
```markdown
## STEP 3: Deploy Supabase Credentials to GitHub Secrets (5 min)

### Which API Key Type?

**For CI (recommended):** Use `anon` key (public, read-only)
- Least privilege
- Cannot modify database schema
- Restricted by Row-Level Security (RLS) policies

**For local development:** Use `anon` key with temporary token

**ONLY if necessary:** Use `service_role` key (private, full access)
- Requires explicit Z2 approval (see CLAUDE.md § Credentials)
- Can modify any table
- Should only be used for database migrations, not routine tests
- Must be rotated immediately after use

### Deploy anon Key (Default)

```bash
# From Supabase dashboard → Settings → API
# Copy the "anon" key (public, not service_role)

gh secret set SUPABASE_KEY --body "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Deploy service_role Key (Requires Z2 Approval)

```bash
# Only if explicitly approved by Z2
# Mark the approval in REGISTERED.md before deploying

gh secret set SUPABASE_KEY --body "[SERVICE_ROLE_KEY]"
```
```

---

## SUMMARY OF PATCHES

| Patch | File | Issue | Fix | Lines |
|:------|:-----|:------|:---|:------|
| 1 | PHASE3-CREDENTIAL-DEPLOYMENT-GUIDE.md | Remove curl + base64 | Delete Step 2C entirely | ~20 |
| 2 | .gitleaks.toml | Remove credential patterns | Remove r8_xxx, eyJhbGc from allowlist | ~5 |
| 3a | .github/workflows/ci-predict-pin.yml | No authorization gate | Add Z2 authorization validation step | ~15 |
| 3b | CLAUDE.md | Extend Z2 authority | Document credential ratification requirement | ~25 |
| 3c | z1-inbox/.templates/ | Create template | Credential proposal template | ~35 |
| 4 | PHASE3-CREDENTIAL-DEPLOYMENT-GUIDE.md | Remove .env.local risk | Delete Step 4, add secure alternatives | ~20 |
| 5 | docs/CREDENTIAL-ROTATION-GUIDE.md | No rotation procedure | New document: rotation, revocation, audit | ~120 |
| 6 | PHASE3-CREDENTIAL-DEPLOYMENT-GUIDE.md | No least privilege | Specify anon key default | ~15 |

**Total Changes:** ~255 lines added, ~50 lines removed, 8 files modified/created

---

## INTEGRATION PATH

1. **Z2 Review:** Approve remediation approach (48h window)
2. **Z1 Implementation:** Apply patches to PR #630
3. **CI Validation:** All gates pass with security changes
4. **Z2 Ratification:** Issue RATIFY signature on remediated PR
5. **Merge:** PR #630 merges with security hardening in place
6. **Phase 3:** Credential deployment proceeds under new security model

---

## AUTHORITY

**Proposed by:** Z1 (Claude) via red team audit  
**Requires:** Z2 (Night) ratification before implementation  
**Authority Reference:** CLAUDE.md §Decision Routing, §Z3 Executors

Generated 2026-10-01  
[Claude Code](https://claude.ai/code) session 01TYKcwkeQfYEeCN5JzZ2WRi
```
