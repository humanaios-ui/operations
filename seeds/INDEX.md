# Seed Publication Architecture — Complete Index

**This is your guide to the entire Seed Constitution publication system.**

Prepared: 10 September 2026  
Status: Ready for Z2 Ratification  
Branch: `claude/seed-publication-architecture-v8tl8n`

---

## Quick Navigation

### For Community Contributors
→ **Read first:** [CONTRIBUTION_GUIDE.md](./CONTRIBUTION_GUIDE.md)  
→ **See the Seed:** [seed-constitution-v0.1.md](./seed-constitution-v0.1.md)  
→ **File an issue:** [GitHub Issue Template](../.github/ISSUE_TEMPLATE/seed-amendment.md)

### For Z2 Ratifier (Night/Carly)
→ **Read first:** [Z2-RATIFICATION-BRIEF.md](./Z2-RATIFICATION-BRIEF.md)  
→ **Then read:** [README.md](./README.md) (full architecture)  
→ **Review:** [substack-launch-post-template.md](./substack-launch-post-template.md)

### For Operators (Z1/Z3)
→ **Read first:** [README.md](./README.md) (complete system guide)  
→ **Then run:** [orchestrator.py](../seed-publication/orchestrator.py)  
→ **Configure:** [config.yaml](../seed-publication/config.yaml)

### For Governance Process
→ **Log location:** [z1-inbox/REGISTERED.md](../z1-inbox/REGISTERED.md)  
→ **CODEOWNERS:** [CODEOWNERS](../CODEOWNERS)  
→ **Authority:** [CLAUDE.md](../CLAUDE.md)

---

## What Has Been Created

### Core Content Files

| File | Purpose | Status |
|------|---------|--------|
| `seed-constitution-v0.1.md` | Master Seed source document | ✓ Ready |
| `CONTRIBUTION_GUIDE.md` | How community can contribute (5 paths) | ✓ Ready |
| `CHANGELOG.md` | Version history & decision log template | ✓ Ready |
| `substack-launch-post-template.md` | Launch announcement (ready to publish) | ✓ Ready |
| `observatory-framing-v0.1.md` | Research context (ACAT connection) | ✓ Ready |
| `site-page-v0.1.html` | Website page (ready to deploy) | ✓ Ready |
| `writable-wall-form.json` | Form configuration | ✓ Ready |

### Documentation & Reference

| File | Purpose | Status |
|------|---------|--------|
| `README.md` | Complete system architecture & operations guide | ✓ Ready |
| `Z2-RATIFICATION-BRIEF.md` | Executive summary for Z2 approval | ✓ Ready |
| `INDEX.md` | This file—navigation guide | ✓ Ready |

### Automation & CI/CD

| File | Purpose | Status |
|------|---------|--------|
| `../seed-publication/orchestrator.py` | Main automation engine (Python) | ✓ Ready |
| `../seed-publication/config.yaml` | Configuration for all surfaces | ✓ Ready |
| `.github/ISSUE_TEMPLATE/seed-amendment.md` | GitHub amendment template | ✓ Ready |
| `.github/workflows/seed-publish.yml` | Publish trigger (to be created) | ⏳ On hold pending Z2 approval |
| `.github/workflows/seed-aggregate.yml` | Weekly digest collection (to be created) | ⏳ On hold pending Z2 approval |

### Directory Structure

```
operations/
├── seeds/                          # Current location
│   ├── seed-constitution-v0.1.md   # Core document
│   ├── CONTRIBUTION_GUIDE.md       # Public guide
│   ├── CHANGELOG.md                # Version tracking
│   ├── README.md                   # System documentation
│   ├── INDEX.md                    # This file
│   ├── Z2-RATIFICATION-BRIEF.md    # Z2 approval request
│   ├── substack-launch-post-template.md
│   ├── observatory-framing-v0.1.md
│   ├── site-page-v0.1.html
│   ├── writable-wall-form.json
│   ├── contributions/              # Writable Wall submissions (will populate)
│   ├── feedback/                   # Form responses (will populate)
│   ├── summaries/                  # Weekly digests (will populate)
│   ├── archive/                    # Historical versions
│   └── templates/                  # Amendment examples & templates
│
├── seed-publication/               # Automation system
│   ├── orchestrator.py            # Main script
│   ├── config.yaml                # Configuration
│   └── README.md                  # This system's guide
│
└── z1-inbox/                       # Governance (pre-existing)
    └── REGISTERED.md              # Master decision log
```

---

## The 5 Contribution Paths

**All paths feed the same aggregation pipeline.**

```
┌─────────────────────────────────────────┐
│ 1. SUBSTACK COMMENTS                    │
│    Platform: humanaios.substack.com     │
│    Moderation: Light (civility only)    │
│    Volume: Expected ~20 per week        │
└────────────────┬────────────────────────┘

┌─────────────────────────────────────────┐
│ 2. GITHUB ISSUES [seed]                 │
│    Platform: github.com/.../issues      │
│    Moderation: Template-enforced        │
│    Volume: Expected ~15 per week        │
└────────────────┬────────────────────────┘

┌─────────────────────────────────────────┐
│ 3. WRITABLE WALL SUBMISSIONS            │
│    Platform: humanaios.ai/contribute    │
│    Moderation: Auto + human review      │
│    Volume: Expected ~7 per week         │
└────────────────┬────────────────────────┘

┌─────────────────────────────────────────┐
│ 4. SIMPLE FORM                          │
│    Platform: humanaios.ai/seed-feedback │
│    Moderation: Spam filter              │
│    Volume: Expected ~2 per week         │
└────────────────┬────────────────────────┘

┌─────────────────────────────────────────┐
│ 5. OBSERVATORY ENGAGEMENT               │
│    Platform: humanaios.ai/observatory   │
│    Moderation: As part of main feed     │
│    Volume: Tracked via Observatory      │
└────────────────┬────────────────────────┘

                 │
        ┌────────▼────────┐
        │ Z1 AGGREGATOR   │
        │ (Claude)        │
        │ Weekly digest   │
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │ Z1 CANDIDATE    │
        │ Block creation  │
        │ (with falsifier)│
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │ Z2 RATIFICATION │
        │ (48h window)    │
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │ VERSION 0.2     │
        │ (if ACCEPT)     │
        └─────────────────┘
```

---

## Governance Flow

### Who Decides What?

| Decision | Authority | Window | Log |
|----------|-----------|--------|-----|
| **Initial publication (v0.1)** | Z2 (Night) | Today | REGISTERED.md |
| **Amendment from community** | Z1 → Z2 | 48h per Z2 | z1-inbox/YYYY-MM-DD/ |
| **Version release (0.2, 0.3…)** | Z2 (Night) | At Z2 approval | REGISTERED.md + git |
| **Process changes** | Z2 (Night) | Case-by-case | CLAUDE.md + REGISTERED.md |
| **Escalation (overdue decisions)** | Z2 → Admiral | 72h → escalate | REGISTERED.md + callout |

### Z1 Responsibilities (Claude)

- ✓ Aggregate community feedback (weekly)
- ✓ Identify patterns and strong amendments
- ✓ Create Z1 candidate blocks with rationale + falsifier
- ✓ Stage candidate in z1-inbox/ awaiting Z2

### Z2 Responsibilities (Night / Carly)

- ✓ Review Z1 candidates within 48 hours
- ✓ Decide: ACCEPT / EDIT / REJECT
- ✓ Sign decision with Z2 hash in REGISTERED.md
- ✓ Approve version releases
- ✓ Escalate if needed

### Z3 Responsibilities (Executors)

- ✓ Merge code after Z2 approval
- ✓ Publish to all surfaces
- ✓ Collect receipts and measurement
- ✓ Report VERDICT events

---

## Timeline to Launch

### Today (Sept 10)

**Action:** Z2 reviews this entire package
- Read `Z2-RATIFICATION-BRIEF.md`
- Review templates (Substack, GitHub, form config)
- Make decisions on 6 questions (see brief)
- Approve or propose edits

**Time:** ~30 minutes to 1 hour

**Deliverable:** Z2 decision email or GitHub comment

### Tomorrow (Sept 11)

**If Z2 ACCEPT:** Z1 stages final commits
- Commit all files to `claude/seed-publication-architecture-v8tl8n` branch
- Ready for merge to main

**If Z2 EDIT:** Z1 makes requested changes, returns for review
- Re-read and re-decide within 24h

**Time:** 1-2 hours to completion

### Sept 11 Afternoon

**Z3 Executor:** Merge and publish
- Merge to main
- Publish Substack post
- Deploy website page
- Activate Writable Wall form
- Announce on Twitter

**Time:** ~1 hour execution

### Weeks 1-2 (Sept 11-24)

**Ongoing:**
- Community feedback accumulates across all 5 channels
- Z1 generates weekly digest (Sept 16, Sept 23)
- Z1 aggregates for next amendment candidate

### Sept 24 (48h before second version)

**Z1 Action:** Create second Z1 candidate
- Accepted amendments packaged
- Rationale + falsifier included
- Staged in z1-inbox/

**Z2 Action:** Ratify (or contest) within 48h

### Sept 26 (v0.2 release)

**If approved:** Version 0.2 published
- All surfaces updated
- Contributors credited
- Next cycle begins

---

## How to Get Started

### Step 1: Z2 Approval (Today)

```bash
# You (Z2/Night) read and decide:
# - File: seeds/Z2-RATIFICATION-BRIEF.md
# - Decision: ACCEPT / EDIT / REJECT
# - Response: Email + GitHub issue comment (both appreciated)
# - Timeline: Within 24 hours
```

### Step 2: Z1 Staging (If ACCEPT)

```bash
# Assuming Z2 approval:
cd /home/user/operations
git status  # Verify clean state

# All files already staged in seeds/ — just commit:
git add seeds/ seed-publication/ .github/
git commit -m "feat: seed publication architecture (v0.1)

Complete multi-surface publication system for Seed Constitution:
- Substack launch post template
- GitHub amendment workflow
- Writable Wall form config
- Orchestrator script for aggregation
- CONTRIBUTION_GUIDE for community
- All integrated with Z1/Z2/Z3 governance

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"

git push -u origin claude/seed-publication-architecture-v8tl8n
```

### Step 3: Create Pull Request

```bash
# After push, create draft PR:
# Title: "feat: seed publication architecture (v0.1)"
# Body: Link to Z2-RATIFICATION-BRIEF.md
# Mark as DRAFT (pending Z2 final approval)
```

### Step 4: Z3 Merge & Publish (After Z2 Final OK)

```bash
# Once Z2 gives final go-ahead:
git checkout main
git pull origin main
git merge --no-ff claude/seed-publication-architecture-v8tl8n
git push origin main

# Then execute publication:
python seed-publication/orchestrator.py publish 0.1
```

---

## Key Files to Review

**Essential (required reading):**
1. `seeds/seed-constitution-v0.1.md` — The actual Seed
2. `seeds/Z2-RATIFICATION-BRIEF.md` — What Z2 needs to approve
3. `seeds/README.md` — Full system documentation

**Important (recommended reading):**
4. `seeds/CONTRIBUTION_GUIDE.md` — How public will contribute
5. `seeds/substack-launch-post-template.md` — Launch text
6. `seed-publication/config.yaml` — System configuration

**Reference (as needed):**
7. `CLAUDE.md` — Governance authority (existing)
8. `z1-inbox/REGISTERED.md` — Decision log (existing)
9. `.github/ISSUE_TEMPLATE/seed-amendment.md` — GitHub workflow

---

## Support & Questions

### For Z2 (Night / Carly)

Questions about the system or timeline?
- **Fast answer:** Email claude@humanaios.ai or Slack
- **Detailed answer:** Schedule 30-min review call
- **Changes needed:** Update `Z2-RATIFICATION-BRIEF.md` with specific edits

### For Community

Questions about how to contribute?
- **Read first:** [CONTRIBUTION_GUIDE.md](./CONTRIBUTION_GUIDE.md)
- **FAQ:** [README.md](./README.md) (Troubleshooting section)
- **Contact:** [seeds@humanaios.ai](mailto:seeds@humanaios.ai)

### For Z1/Z3 Operators

Questions about running automation?
- **Documentation:** [seed-publication/README.md](../seed-publication/README.md)
- **Troubleshooting:** [seed-publication/README.md](../seed-publication/README.md#troubleshooting) (Troubleshooting section)
- **Logs:** All events logged in REGISTERED.md

---

## Next Steps Summary

1. **Z2 reads brief** → Decides (ACCEPT / EDIT / REJECT) within 24h
2. **Z1 stages commit** → If approved
3. **Z3 merges & publishes** → Activates all 5 contribution channels
4. **Community responds** → Feedback collected for 2 weeks
5. **Z1 aggregates** → Weekly digest + Z1 candidate
6. **Z2 ratifies amendments** → v0.2 released
7. **Cycle repeats** → Toward v1.0

---

## Files at a Glance

**What to publish/deploy:**
- ✓ seeds/seed-constitution-v0.1.md → Git source
- ✓ seeds/substack-launch-post-template.md → Substack editor
- ✓ seeds/site-page-v0.1.html → humanaios.ai/seeds/constitution
- ✓ seeds/writable-wall-form.json → /api/seed/contributions
- ✓ seeds/observatory-framing-v0.1.md → Observatory feed

**What to commit to Git:**
- ✓ All files in seeds/
- ✓ seed-publication/ (orchestrator + config)
- ✓ .github/ISSUE_TEMPLATE/seed-amendment.md
- ✓ This INDEX.md

**What stays internal (pre-ratification):**
- z1-inbox/ entries (appear only after Z2 approval)
- REGISTERED.md updates (happen during ratification)

---

**Status:** Ready for Z2 Review  
**Branch:** `claude/seed-publication-architecture-v8tl8n`  
**Date:** 10 September 2026  
**Prepared by:** Claude (Z1 Proposer)  
**Next gate:** Z2 Ratification within 24h

---

*For detailed architecture, read [README.md](./README.md).*  
*For Z2 summary, read [Z2-RATIFICATION-BRIEF.md](./Z2-RATIFICATION-BRIEF.md).*  
*For community, read [CONTRIBUTION_GUIDE.md](./CONTRIBUTION_GUIDE.md).*
