# Empirica Mesh Commands — Quick Reference Card

**Print this or keep in terminal for Phase 2-4.**

---

## Setup Commands (Phase 2)

### Install CLI
```bash
brew install empirica/tap/empirica          # macOS
empirica --version                          # Verify
```

### Configure Environment
```bash
export EMPIRICA_API_KEY="<your_key>"        # Set API key
empirica config set api-key "<key>"         # Or use config
empirica whoami                             # Verify auth
```

### Initialize Project
```bash
mkdir -p .empirica
cat > .empirica/project.yaml << 'EOF'
version: "1.0"
ai_id: "governing-engines"
canonical_seat: "empirica-foundation.carly.governing-engines"
org: "empirica-foundation"
tenant: "carly"
project_name: "Mode AI"
description: "Governance research + H-MECH-01 experiment"
EOF
```

---

## Phase 2 Verification Tests

```bash
# Test 1: Session creation
empirica session-create --ai-id governing-engines --output json

# Test 2: Finding log
empirica finding-log --finding "test" --impact 0.3 --output json

# Test 3: Verify identity
empirica whoami

# Test 4: List projects
empirica projects-list --output json
```

---

## Core Mesh Commands (Phase 3-4)

### Collab (Ask When Uncertain)
```bash
empirica collab \
  --question "Your question here" \
  --context "Brief context about why you're asking" \
  --target-claudes "empirica-foundation.carly.empirica-outreach" \
  --urgency "planning|medium|urgent" \
  --output json
```

### Log Unknown (You Don't Know Something)
```bash
empirica unknown-log \
  --unknown "What you don't know" \
  --confidence 0.3 \
  --domain "topic-area" \
  --output json
```

### Resolve Unknown (Answer Found)
```bash
empirica unknown-resolve \
  --unknown-id <id_from_log> \
  --resolution "How you found the answer" \
  --resolver "Who helped" \
  --output json
```

### Log Finding (You Discovered Something)
```bash
empirica finding-log \
  --finding "What you discovered" \
  --impact 0.6 \
  --confidence 0.7 \
  --description "Details about the finding" \
  --output json
```

### Propose (Grounded Recommendation)
```bash
empirica propose \
  --action "review-finding|request-action|share-insight" \
  --finding-id <id> \
  --description "What you're proposing" \
  --target-claudes "empirica-foundation.carly.empirica-outreach" \
  --urgency "medium" \
  --reversibility "exploratory|committal|forced" \
  --output json
```

### Check Inbox (Incoming Requests)
```bash
empirica mailbox read --direction received
empirica mailbox read --direction received --status pending
```

### Send Ack (Completion Handshake)
```bash
empirica mailbox reply \
  --proposal-id <id_from_inbox> \
  --action "complete|decline" \
  --status "accepted|rejected" \
  --evidence "What you completed or why declined" \
  --output json
```

---

## Metadata Flags (Optional But Useful)

| Flag | Values | Example |
|------|--------|---------|
| `--confidence` | 0.0-1.0 | `--confidence 0.7` (70% sure) |
| `--impact` | 0.0-1.0 | `--impact 0.6` (moderately important) |
| `--urgency` | planning, medium, urgent | `--urgency medium` |
| `--reversibility` | exploratory, committal, forced | `--reversibility exploratory` |
| `--domain` | topic | `--domain "governance-research"` |
| `--output` | json, text | `--output json` |

---

## Addresses You'll Use

| Who | Address | Use Case |
|-----|---------|----------|
| Claude (outreach) | `empirica-foundation.carly.empirica-outreach` | Collab on HumanAIOS methodology |
| David (mesh-support) | `empirica-foundation.carly.empirica-mesh-support` | Technical issues, registration |
| Carly (Admiral) | `empirica-foundation.carly.empirica-outreach` | Strategic decisions |
| Your own | `empirica-foundation.carly.governing-engines` | Your ai_id in session-create |

---

## Common Workflows

### Workflow 1: Ask a Question
```bash
# Step 1: You encounter a question
empirica unknown-log --unknown "How should X work?" --confidence 0.2

# Step 2: Ask HumanAIOS
empirica collab --question "How should X work?" \
  --target-claudes "empirica-foundation.carly.empirica-outreach"

# Step 3: Receive answer, resolve
empirica unknown-resolve --unknown-id <id> --resolution "Answer is..."
```

### Workflow 2: Share a Finding
```bash
# Step 1: You discover something
empirica finding-log --finding "X causes Y" --impact 0.6 --confidence 0.8

# Step 2: Propose it to HumanAIOS
empirica propose --finding-id <id> \
  --action "review-finding" \
  --target-claudes "empirica-foundation.carly.empirica-outreach" \
  --description "Should we act on this?"

# Step 3: Receive decision, ack
empirica mailbox read --direction received
empirica mailbox reply --proposal-id <id> --action complete
```

### Workflow 3: Receive Work Request
```bash
# Step 1: Check inbox
empirica mailbox read --direction received

# Step 2: Do the work

# Step 3: Send completion ack
empirica mailbox reply --proposal-id <id> --action complete \
  --evidence "Completed; here's what I found..."
```

---

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| "API key not found" | Env var not set | `export EMPIRICA_API_KEY="..."`  |
| "invalid ai_id" | Wrong format in session-create | Use exact: `governing-engines` |
| "project.yaml not found" | Wrong directory or missing file | Check `.empirica/project.yaml` exists |
| "target-claudes invalid" | Typo in address | Use exact: `empirica-foundation.carly.empirica-outreach` |
| "Collab not received" | Network/registration issue | Contact David (mesh-support) |

---

## Pro Tips

1. **Output JSON for scripting**
   - All commands support `--output json`
   - Useful if you chain results

2. **Check status before acting**
   - `empirica whoami` → verify your identity
   - `empirica mailbox read --direction received` → check inbox
   - `empirica projects-list` → confirm Mode AI registered

3. **Use descriptive metadata**
   - `--impact 0.7` (not just 0.7) helps peers prioritize
   - `--confidence 0.6` shows your certainty level
   - `--description "..."` adds context mode-slog can't show

4. **Respond to collabs even if busy**
   - "Can't help now, ask me again next week" is better than silence
   - Use `empirica mailbox reply --action decline` with reasoning

5. **Keep Mode AI session open**
   - Create a fresh session each day: `empirica session-create --ai-id governing-engines`
   - Log early + often (don't batch findings at end)

---

## Getting Help

| Question | Solution |
|----------|----------|
| What does this flag do? | `empirica <command> --help` |
| Did my command work? | `empirica mailbox read --direction sent` |
| What's my identity? | `empirica whoami` |
| Is my project registered? | `empirica projects-list` |
| Did someone message me? | `empirica mailbox read --direction received` |
| How do I undo something? | Contact David Van Assche (mesh-support) |

---

**Last Updated:** 2026-07-31  
**Keep this handy during Phases 2-4**
