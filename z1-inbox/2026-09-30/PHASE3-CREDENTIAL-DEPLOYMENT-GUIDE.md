# Phase 3 Credential Deployment — Step-by-Step Guide

**Date:** 2026-09-30  
**Target:** Deploy Replicate API key + Supabase credentials to unblock Phase 3 live testing  
**Expected Duration:** 15–20 minutes  
**Risk Level:** LOW (credentials only; no code changes)

---

## Pre-Deployment Checklist

Before you start, verify you have:

- [ ] GitHub repository access to `humanaios-ui/operations`
- [ ] GitHub personal access token (PAT) with `repo:write` + `admin:repo_hook` scopes, OR GitHub CLI (`gh`) installed with auth
- [ ] Replicate API key (format: `r8_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx`) — [get it](https://replicate.com/account/api-tokens)
- [ ] Supabase project URL (format: `https://xxxxxxxxxx.supabase.co`)
- [ ] Supabase API key (format: `eyJhbGc...` — get from Supabase dashboard → Settings → API Keys → `anon` or `service_role`)
- [ ] Terminal access to this repository directory

---

## STEP 1: Verify Current CI Test Status (2 min)

Confirm Phase 3 tests are currently skipped (no credentials yet):

```bash
cd /home/user/operations

# Check if test file exists
ls -la tools/tests/test_holographic_phase3_live.py

# Try running tests locally (they will SKIP without credentials)
python3 -m pytest tools/tests/test_holographic_phase3_live.py -v --tb=short 2>&1 | head -30
```

**Expected output:**
```
test_synthetic_mesh_available PASS
test_replicate_connectivity SKIP (no REPLICATE_API_KEY in environment)
test_dry_run_vs_live_schema PASS
test_latency_budget SKIP (no SUPABASE credentials)
```

If you see PASS/SKIP, you're good. If you see FAIL, note it and continue (credentials will fix it).

---

## STEP 2: Deploy Replicate API Key to GitHub Secrets (5 min)

### Option A: Using GitHub CLI (Recommended)

```bash
# Authenticate with GitHub (if not already)
gh auth login

# Set the secret in GitHub
gh secret set REPLICATE_API_KEY --body "r8_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Replace r8_xxx... with your actual Replicate API key
# Verify it was set
gh secret list
```

### Option B: Using GitHub Web UI

1. Open your browser → `https://github.com/humanaios-ui/operations`
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. **Name:** `REPLICATE_API_KEY`
5. **Value:** `r8_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx` (paste your actual key)
6. Click **Add secret**

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

---

## STEP 3: Deploy Supabase Credentials to GitHub Secrets (5 min)

Repeat Step 2 for Supabase URL and key.

### Using GitHub CLI (Recommended)

```bash
# Set Supabase URL
gh secret set SUPABASE_URL --body "https://xxxxxxxxxx.supabase.co"

# Set Supabase API key
gh secret set SUPABASE_KEY --body "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Verify
gh secret list | grep SUPABASE
```

**Expected output:**
```
REPLICATE_API_KEY  Updated 2026-09-30
SUPABASE_URL       Updated 2026-09-30
SUPABASE_KEY       Updated 2026-09-30
```

---

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

---

## STEP 5: Verify Supabase Project Configuration (3 min)

Before running tests, make sure your Supabase project is ready:

1. **Open Supabase dashboard:** https://supabase.com/dashboard
2. **Select your project** (the one you got credentials from)
3. **Go to:** Settings → API
4. **Verify:**
   - Project URL matches `SUPABASE_URL` ✓
   - API key (anon or service_role) matches `SUPABASE_KEY` ✓
5. **Go to:** SQL Editor
   - You'll apply the migration here in the next step

---

## STEP 6: Apply Supabase Migration (3 min)

Create the `holographic_jobs` table that Phase 3 tests will write results to.

### Option A: Using Supabase Web UI (Easiest)

1. **Open Supabase dashboard** → **SQL Editor**
2. **Click "New Query"**
3. **Copy & paste the entire migration from:**
   ```bash
   cat supabase/migrations/20260916_holographic_jobs.sql
   ```
4. **Paste into the SQL Editor**
5. **Click "Run"** (or Cmd+Enter)
6. **Verify output:** "Success. No rows returned."

### Option B: Using Supabase CLI (If Installed)

```bash
# Make sure you're logged into Supabase CLI
supabase login

# Apply the migration to your project
supabase db push --file supabase/migrations/20260916_holographic_jobs.sql
```

### Verification

After applying migration, verify the table was created:

```bash
# In Supabase SQL Editor, run:
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name = 'holographic_jobs';
```

**Expected output:**
```
table_name
-----------
holographic_jobs
```

---

## STEP 7: Run Phase 3 Tests Locally (5 min)

With credentials deployed to your environment:

```bash
cd /home/user/operations

# Source credentials again (in case new terminal session)
source ~/.env.local

# Run Phase 3 tests
python3 -m pytest tools/tests/test_holographic_phase3_live.py -v

# OR run just one test
python3 -m pytest tools/tests/test_holographic_phase3_live.py::test_replicate_connectivity -v
```

**Expected output (all tests PASS):**
```
test_synthetic_mesh_available PASS
test_replicate_connectivity PASS
test_dry_run_vs_live_schema PASS
test_latency_budget PASS

=========== 4 passed in 3.42s ===========
🔬 Hypothesis Verdict: CONFIRMED
```

---

## STEP 8: Trigger GitHub Actions to Run Phase 3 Tests (1 min)

Now that credentials are in GitHub Secrets, CI will run Phase 3 tests automatically on the next push.

### Option A: Create a Dummy Commit (Simplest)

```bash
# Add a comment to trigger CI
echo "# Trigger Phase 3 CI tests" >> /tmp/trigger.txt

# Commit and push
git add z1-inbox/2026-09-30/PHASE3-CREDENTIAL-DEPLOYMENT-GUIDE.md
git commit -m "Deploy Phase 3 credentials to GitHub Secrets

REPLICATE_API_KEY: deployed to GitHub Actions secrets
SUPABASE_URL: deployed to GitHub Actions secrets
SUPABASE_KEY: deployed to GitHub Actions secrets

Migration applied: 20260916_holographic_jobs.sql
Local tests verified: 4/4 PASS, Hypothesis CONFIRMED
"

git push -u origin claude/issues-prs-review-nkoj4l
```

### Option B: Push an Existing Branch

```bash
# If you already have commits staged
git push origin claude/issues-prs-review-nkoj4l
```

### Monitor GitHub Actions

1. **Open:** https://github.com/humanaios-ui/operations/actions
2. **Look for:** Latest workflow run (should be `tool-manifest` or your CI workflow)
3. **Check Phase 3 test step:**
   - Should show `test_holographic_phase3_live.py` passing
   - Results logged to Supabase `holographic_jobs` table

---

## STEP 9: Verify Results in Supabase (2 min)

After CI runs (or after your local test), check that results were written to the database:

```bash
# In Supabase SQL Editor, run:
SELECT id, job_id, person_id, status, latency_ms, schema_equivalence, created_at 
FROM holographic_jobs 
ORDER BY created_at DESC 
LIMIT 5;
```

**Expected output:**
```
id | job_id | person_id | status | latency_ms | schema_equivalence | created_at
---|--------|-----------|--------|------------|-------------------|---
 1 | phase3-test-001 | ...    | complete | 42 | 0.97 | 2026-09-30T15:23:45Z
```

---

## Troubleshooting

### Tests Still Skip After Credentials Deployed

**Cause:** Environment variables not picked up by Python/pytest

**Fix:**
```bash
# Explicitly pass credentials to pytest
REPLICATE_API_KEY="r8_..." SUPABASE_URL="https://..." SUPABASE_KEY="..." \
  python3 -m pytest tools/tests/test_holographic_phase3_live.py -v
```

### `REPLICATE_API_KEY` Invalid / Rejected by Replicate API

**Cause:** Incorrect API key format or revoked key

**Fix:**
1. Check format: must start with `r8_` followed by 32+ hex chars
2. Verify at https://replicate.com/account/api-tokens (re-generate if needed)
3. Re-deploy to GitHub Secrets and local .env.local

### Supabase Migration Fails with "Permission Denied"

**Cause:** API key lacks `table_create` permission

**Fix:**
1. Use `service_role` key instead of `anon` key
2. Or run migration in Supabase Web UI (auto-uses admin role)

### GitHub Actions Still Show "SKIP" After Deploying Secrets

**Cause:** Secrets cache not refreshed, or workflow not re-triggered

**Fix:**
```bash
# Force a workflow run
gh workflow run quality-baseline.yml --repo humanaios-ui/operations

# Or push an empty commit
git commit --allow-empty -m "Trigger Phase 3 CI"
git push
```

---

## Success Criteria

You've successfully deployed Phase 3 credentials when:

- [ ] `gh secret list` shows `REPLICATE_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`
- [ ] Local test run: `python3 tools/tests/test_holographic_phase3_live.py` → 4/4 PASS
- [ ] Supabase `holographic_jobs` table exists and has rows
- [ ] GitHub Actions workflow shows Phase 3 tests passing (not skipped)
- [ ] Hypothesis Verdict: `CONFIRMED`

---

## Next Steps

Once Phase 3 is unblocked:

1. **Z2 Ratification Decision:** Tier assignments for all 92 untiered candidates (Q-TIER-ASSIGNMENT-BATCH-01)
2. **Intent-OS Activation:** Ratify Q-INTENTOS-PAGES-GATE-01, Q-INTENTOS-REFRESH-01, Q-INTENTOS-BUS-01
3. **Resource System Launch:** Commit Issue #588 Resource System as new project
4. **Portfolio Replay:** Run RBE-OPS priority queue engine to schedule execution

---

**Estimated Total Time:** 15–20 minutes  
**Difficulty:** Beginner (copy-paste credentials, click buttons)  
**Prerequisites:** None (all tools/APIs are ready)

Good luck! 🚀
