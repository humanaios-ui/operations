# Phase 2: Technical Setup — Empirica CLI + Project Registration

**Timeline:** Aug 2-3 (1-2 hours)  
**Owner:** Demarius + David Van Assche (mesh-support)  
**Deliverable:** CLI verified working + project registered in empirica mesh

---

## Prerequisites
- Phase 1 orientation complete + mesh agreement signed
- macOS/Linux terminal access (Windows WSL2 supported)
- Git installed locally (`git --version` works)

---

## Step 1: Install Empirica CLI (15-20 min)

### Option A: Homebrew (macOS/Linux)
```bash
brew install empirica/tap/empirica
empirica --version
```

### Option B: Direct Binary (Any OS)
```bash
# Download latest release
curl -LO https://github.com/empirica/empirica/releases/download/latest/empirica-darwin-arm64
chmod +x empirica-darwin-arm64
sudo mv empirica-darwin-arm64 /usr/local/bin/empirica
empirica --version
```

### Option C: From Source (if needed)
```bash
git clone https://github.com/empirica/empirica.git
cd empirica
go build -o empirica cmd/main.go
sudo mv empirica /usr/local/bin/
empirica --version
```

**Verify:** Should output `empirica version X.Y.Z`

---

## Step 2: Empirica Authentication (10-15 min)

You need an API key from the empirica account tied to Demarius.

```bash
# Set your API key
export EMPIRICA_API_KEY="<your_api_key_here>"

# Verify authentication
empirica whoami
```

**Expected output:**
```
Authenticated as:
  User: Demarius J. Lawson
  Org: empirica-foundation
  Tenant: carly
```

**If you don't have an API key:**
1. Contact David Van Assche (mesh-support): truuzee@gmail.com
2. Request an API key for `empirica-foundation.carly.governing-engines`
3. David will generate + send key
4. Add to your shell config (`.bashrc`, `.zshrc`):
   ```bash
   export EMPIRICA_API_KEY="<key>"
   ```

---

## Step 3: Initialize Project (10 min)

Create the `.empirica/project.yaml` file in your local Mode AI workspace:

```bash
cd ~/your-mode-ai-workspace  # or wherever Mode AI code lives locally

# Create .empirica directory
mkdir -p .empirica

# Create project.yaml (see template below)
cat > .empirica/project.yaml << 'EOF'
version: "1.0"
ai_id: "governing-engines"
canonical_seat: "empirica-foundation.carly.governing-engines"
org: "empirica-foundation"
tenant: "carly"
project_name: "Mode AI"
description: "Governance research + H-MECH-01 experiment coordination"
EOF

# Verify
cat .empirica/project.yaml
```

**Your canonical mesh identity is now:** `empirica-foundation.carly.governing-engines`

---

## Step 4: Verify CLI (10 min)

Run these tests to confirm setup:

### Test 1: Session Creation
```bash
empirica session-create --ai-id governing-engines --output json
```

**Expected:** JSON output with session_id, timestamp, ai_id.

### Test 2: Finding Log
```bash
empirica finding-log \
  --finding "Technical setup verified — empirica CLI working locally" \
  --impact 0.3 \
  --output json
```

**Expected:** JSON with finding_id, timestamp, logged successfully.

### Test 3: Whoami (Verify Identity)
```bash
empirica whoami
```

**Expected:**
```
Authenticated as:
  Org: empirica-foundation
  Tenant: carly
  Seat: governing-engines
```

### Test 4: List Projects (Optional)
```bash
empirica projects-list --output json
```

**Expected:** List includes your Mode AI project.

---

## If Tests Fail

### Error: "API key not found"
```
Solution: Set EMPIRICA_API_KEY env var or contact David for key
empirica config get api-key    # Check current key
empirica config set api-key "<new_key>"  # Update
```

### Error: "project.yaml not found"
```
Solution: Verify .empirica/project.yaml exists in your workspace
ls -la .empirica/project.yaml    # Should list file
cat .empirica/project.yaml       # Should show config
```

### Error: "invalid ai_id"
```
Solution: Use exact canonical form: empirica-foundation.carly.governing-engines
grep ai_id .empirica/project.yaml   # Verify format
```

### Error: "session-create failed"
```
Solution: Check authentication + project registration
empirica whoami                    # Verify auth
empirica projects-list --verbose   # Verify project registered
Contact David Van Assche if project not in list
```

---

## Step 5: Notify David Van Assche (10 min)

Once all tests pass, send David confirmation:

**Email to:** truuzee@gmail.com  
**Subject:** Phase 2 Complete — governing-engines CLI verified

**Message:**
```
David,

Phase 2 technical setup for Demarius (governing-engines) is complete.

✅ CLI installed + verified
✅ .empirica/project.yaml configured
✅ session-create test passed
✅ finding-log test passed
✅ whoami confirms: empirica-foundation.carly.governing-engines

Ready to proceed with Phase 3 coordination test (Aug 3-4).

—Demarius
```

---

## Phase 2 Deliverables Checklist

- [ ] empirica CLI installed (`empirica --version` works)
- [ ] EMPIRICA_API_KEY set in environment
- [ ] `.empirica/project.yaml` created with correct ai_id
- [ ] `empirica session-create --ai-id governing-engines` passes
- [ ] `empirica finding-log --finding "test"` passes
- [ ] `empirica whoami` shows correct org/tenant/seat
- [ ] David Van Assche notified + confirms project registration
- [ ] Ready to start Phase 3 (coordination test)

---

## Next Phase (Phase 3)

Once Phase 2 is complete:
1. Claude (outreach) reaches out to schedule Phase 3
2. Phase 3 is a live collab → propose → ack coordination test
3. ~30-60 min sync to execute one full mesh coordination cycle
4. Deliverable: Mesh agreement + one coordination cycle completed

---

**Phase 2 Owner:** Demarius + David Van Assche  
**Estimated Time:** 1-2 hours  
**Due:** Aug 3 EOD (so Phase 3 can start Aug 3-4)
