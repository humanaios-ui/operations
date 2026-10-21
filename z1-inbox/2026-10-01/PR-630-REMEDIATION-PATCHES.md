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
- Earlier literal credential assignments may remain in shell history; expanded curl arguments can expose the PAT through process listings
- GitHub CLI handles encryption correctly using libsodium
- Only option should be GitHub CLI

**New Version:**
```markdown
### Recommended Method: GitHub CLI

Use this method for all credential deployments. GitHub CLI encrypts the secret for GitHub using its public key. Enter the value at the hidden prompt (or provide it on stdin from a secure source); encryption does not prevent shell-history or process-argument exposure when values are passed on the command line. Disable shell tracing while handling credentials.

```bash
# Authenticate with GitHub (if not already)
gh auth login

# Set the repository secret; paste the value at the hidden prompt
gh secret set REPLICATE_API_KEY  # Paste the approved value at the hidden prompt
# Verify it was set
gh secret list | grep REPLICATE
```

### Why Not Other Methods?

- **The removed curl example:** Base64 is not encryption, and GitHub requires public-key encryption for secret uploads. Shell history records literal variable references in the curl command, but earlier literal credential assignments may remain in history, and expanded arguments can expose the PAT through process listings. Use the CLI prompt instead.
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
[extend]
useDefault = true

# No global credential-pattern exceptions. sk_test_ keys can be real credentials.
# Only if a fixture needs an exception: use its exact synthetic value AND
# exact test path, scoped to the detecting rule (Gitleaks 8.25+ syntax).
[[rules]]
id = "stripe-access-token"
[[rules.allowlists]]
description = "Exact synthetic credential-redaction fixture"
condition = "AND"
paths = ['^tools/tests/test_holographic_integration\.py$']
regexTarget = "secret"
regexes = ['^sk_test_SYNTHETICONLY0123456789ABC$']
```

**Rationale:**
- Remove credential patterns (sk_test_, r8_xxx, eyJhbGc) from global allowlists entirely
- Never allowlist real credential patterns, even in documentation
- A synthetic marker alone is insufficient: any required exception must match the exact synthetic value AND its test path
- This prevents real credentials from bypassing gitleaks

---

## PATCH 3: Add Z2 Authorization Gate for Credentials (CRITICAL-3)

**Files to Modify:**
1. `.github/workflows/ci-predict-pin.yml` (add credential validation)
2. `tools-manifest.yaml` (document credential authority)
3. `CLAUDE.md` (extend Z2 ratification requirement to credentials)

### Change 3a: Add Credential Validation Step to CI

**File:** `.github/workflows/ci-predict-pin.yml`

**Add a job under `jobs`:** The authorization must already be recorded on the trusted base. A PR cannot authorize itself by editing its own index or registry. The signed proposal must list the SHA-256 of each approved file's complete bytes in the `credential_files` JSON block below (`null` authorizes deletion). Register the accepted signature as an exact line in `REGISTERED.md`: `RATIFY <Q-ID> sha256:<digest> decision:ACCEPT`. This proposed gate checks that registration, the indexed Z2 ruling, and the content signature; Git provenance of the trusted base supplies operator identity, since a SHA-256 digest alone does not authenticate a signer.

```yaml
  credential_authorization:
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v7
        with:
          ref: ${{ github.event.pull_request.head.sha }}
          path: proposed
          fetch-depth: 0
          persist-credentials: false
      - uses: actions/checkout@v7
        with:
          ref: ${{ github.event.pull_request.base.sha }}
          path: trusted
          persist-credentials: false
      - uses: actions/setup-python@v7
        with:
          python-version: '3.x'
      - run: python3 -m pip install pyyaml
      - name: Verify Z2 authorization for credential changes
        env:
          BASE_SHA: ${{ github.event.pull_request.base.sha }}
          HEAD_SHA: ${{ github.event.pull_request.head.sha }}
        run: |
          set -euo pipefail
          # Run diff separately: a missing ref or any diff error fails the job.
          git -C proposed diff --name-only "$BASE_SHA" "$HEAD_SHA" > changed-paths.txt
          python3 - <<'PY'
          import hashlib
          from pathlib import Path
          import re
          import sys

          trusted = Path('trusted').resolve()
          sys.path.insert(0, str(trusted / '.z1-control'))
          from ratify import signature
          from validate import INDEX, StrictLoader, load_index
          import yaml

          changed = {
              p for p in Path('changed-paths.txt').read_text().splitlines()
              if re.search(r'PHASE3.*DEPLOYMENT|\.gitleaks\.toml', p)
          }
          if not changed:
              sys.exit(0)
          index = load_index(INDEX)
          registered = (trusted / 'REGISTERED.md').read_text().splitlines()
          records = {r['path'] for r in index.get('records', [])}
          approved = set()
          for c in index.get('candidates', []):
              digest = str(c.get('z2_hash', ''))
              if (c.get('status') != 'ratified'
                      or c.get('ratified_by') not in index['ratifiers']
                      or not re.fullmatch(r'[0-9a-f]{64}', digest)
                      or c.get('z2_ruling') not in records):
                  continue
              if f"RATIFY {c['q_id']} sha256:{digest} decision:ACCEPT" not in registered:
                  continue
              proposal = (trusted / c['path']).read_bytes()
              if signature(proposal, c['ratified_by'], str(c['ratified_at']), 'ACCEPT') != digest:
                  continue
              if digest not in (trusted / c['z2_ruling']).read_text():
                  continue
              block = re.search(rb'```json\n(.*?)\n```', proposal, re.S)
              if not block:
                  continue
              allowed = yaml.load(block[1], Loader=StrictLoader).get('credential_files', {})
              for p in changed:
                  target = Path('proposed') / p
                  if target.is_symlink():
                      sys.exit('Credential paths must be regular files: ' + p)
                  actual = hashlib.sha256(target.read_bytes()).hexdigest() if target.exists() else None
                  if p in allowed and allowed[p] == actual:
                      approved.add(p)
          missing = changed - approved
          if missing:
              sys.exit('Missing or invalid registered Z2 RATIFY authorization: ' + ', '.join(sorted(missing)))
          print('Registered Z2 authorization verified for every credential path')
          PY
```

No matching credential paths requires no authorization. Matching paths pass only when their exact proposed contents have valid registered authorization. Missing or invalid authorization fails the job. This is a proposed gate, pending implementation and Z2 review.

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
4. Register the signature and indexed ruling on the trusted base; Z3 deploys only after the signature and approved file hashes verify
5. Z2 maintains credential rotation schedule and revocation procedures

**Authority:** Z2 sole authority over credentials (per dual-authority model)

**Escalation:** If credential deployment is attempted without Z2 signature, CI gates reject with clear error message pointing to authorization requirement.
```

### Change 3c: Create Credential Proposal Template

**File:** Create `z1-inbox/.templates/Q-CREDENTIAL-REQUEST.md`

````markdown
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

## Approved File Contents

Include each changed credential path and the SHA-256 of its proposed complete bytes. Use `null` for an approved deletion. Z2 signs these values as part of the proposal before the credential-change PR is evaluated.

```json
{
  "credential_files": {
    "z1-inbox/2026-09-30/PHASE3-CREDENTIAL-DEPLOYMENT-GUIDE.md": "<64-character SHA-256>",
    ".gitleaks.toml": "<64-character SHA-256>"
  }
}
```

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
````

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

### Repository-Secret Management (CI)

```bash
# Authenticate to manage GitHub repository secrets
gh auth login
gh secret list  # Lists secret names and metadata, never their values
```

This manages repository secrets for GitHub Actions. It does not download provider credentials or make them available to local tests. Workflows must explicitly pass the needed secrets to their test processes.

### Local Testing: Provider Authentication

Follow the documented authentication flow for each provider:
- **Replicate:** Use the [API token guide](https://replicate.com/docs/topics/security/api-tokens) to create and manage an authorized token.
- **Supabase:** Follow the [API key guide](https://supabase.com/docs/guides/api/api-keys) and, for user sessions, the [Auth guide](https://supabase.com/docs/guides/auth).

Supply the resulting credentials to the local test process through a secure credential manager or a hidden prompt with shell tracing disabled. Follow provider documentation for token lifetimes and revocation; do not assume an unauthenticated endpoint can mint temporary credentials.

### Option C: CI-Only Testing

If you don't need to test locally, skip local credential setup entirely. Push to your branch → let GitHub Actions run Phase 3 tests using GitHub Secrets.

### ⚠️ DO NOT use .env files or .env.local

- Files in home directory are backed up by cloud sync (iCloud, OneDrive) and system backups
- Literal credential assignments typed into a shell may remain in history; shell tracing can expose values when sourcing a file
- Risk of accidental git commit is high
- Use GitHub Secrets for CI; authenticate local tests through the documented provider flows above
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
gh secret set REPLICATE_API_KEY  # Paste the approved value at the hidden prompt
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
3. Type: `anon` (subject to grants and RLS policies); use `service_role` only with explicit Z2 approval
4. Copy key

### Step 2: Update GitHub Secrets

```bash
gh secret set SUPABASE_KEY  # Paste the approved value at the hidden prompt
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

# Remove revoked repository secrets so CI cannot keep using them
gh secret delete REPLICATE_API_KEY
gh secret delete SUPABASE_KEY

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

**For CI (recommended):** Use the public `anon` key with grants and Row-Level Security (RLS) policies limited to the operations the tests need.
- The key is read-only only when the project's grants and RLS policies enforce read-only access
- Public does not mean read-only: permitted writes are possible when grants and RLS allow them
- Verify the effective permissions before running CI

**For local development:** Follow the documented Supabase authentication flow and apply the same grants and RLS restrictions

**ONLY if necessary:** Use `service_role` key (private, full access)
- Requires explicit Z2 approval (see CLAUDE.md § Credentials)
- Can modify any table
- Should only be used for database migrations, not routine tests
- Must be rotated immediately after use

### Deploy anon Key (Default)

```bash
# From Supabase dashboard → Settings → API
# Copy the "anon" key (public, not service_role)

gh secret set SUPABASE_KEY  # Paste the approved value at the hidden prompt
```

### Deploy service_role Key (Requires Z2 Approval)

```bash
# Only if explicitly approved by Z2
# Mark the approval in REGISTERED.md before deploying

gh secret set SUPABASE_KEY  # Paste the approved value at the hidden prompt
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
